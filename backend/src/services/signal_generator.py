"""
AI 매매 신호 생성 서비스

이 모듈은 Gemini AI를 사용하여 암호화폐 매매 신호를 생성하는 서비스를 제공합니다.
- 시장 데이터 전처리 및 분석
- AI 프롬프트 템플릿 기반 신호 생성
- 신호 파싱 및 검증
"""

import json
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import MarketData, TradingSignal
from src.models.trading_signal import SignalType
from src.services.ai_client import AIClient, AIClientError, get_ai_client

# === 신호 생성 상수 ===
MIN_CONFIDENCE = 0.0  # 최소 신뢰도
MAX_CONFIDENCE = 1.0  # 최대 신뢰도
DEFAULT_CONFIDENCE = 0.5  # 기본 신뢰도 (파싱 실패 시)
MARKET_DATA_HOURS = 24  # 분석에 사용할 시장 데이터 기간 (시간)
COOLDOWN_MINUTES = 5  # 수동 신호 생성 쿨다운 (분)

# === 시스템 프롬프트 ===
SYSTEM_INSTRUCTION = """당신은 리플(XRP) 트레이딩 전문가 AI입니다.
주어진 시장 데이터를 분석하고 매매 신호를 생성합니다.

핵심 원칙:
1. 보수적 접근: 확실하지 않으면 HOLD를 권장
2. 리스크 관리: 변동성이 높으면 매수 신중, 손실 방지 우선
3. 근거 기반: 모든 결정에 명확한 기술적 근거 제시

출력 형식:
반드시 다음 JSON 형식으로만 응답하세요:
```json
{
  "signal": "BUY" | "HOLD" | "SELL",
  "confidence": 0.0 ~ 1.0 사이의 숫자,
  "reasoning": "분석 근거 설명 (한국어, 2-3문장)"
}
```

주의사항:
- JSON 외의 텍스트를 포함하지 마세요
- confidence는 신호의 확신도입니다 (0.7 이상: 강한 신호, 0.5 미만: 약한 신호)
- reasoning은 구체적인 기술적 지표나 패턴을 언급하세요
"""

# === 분석 프롬프트 템플릿 ===
ANALYSIS_PROMPT_TEMPLATE = """## 리플(XRP/KRW) 시장 분석 요청

### 현재 시장 상황
- 분석 시각: {timestamp}
- 현재가: {current_price:,.0f} KRW
- 24시간 고가: {high_price:,.0f} KRW
- 24시간 저가: {low_price:,.0f} KRW
- 24시간 거래량: {volume:,.2f} XRP
- 24시간 변동률: {price_change_pct:+.2f}%

### 가격 추이 (최근 {data_hours}시간)
{price_history}

### 분석 요청
위 시장 데이터를 기반으로 매매 신호를 생성해주세요.
가격 추세, 변동성, 거래량 패턴을 종합적으로 고려하세요.
"""


class SignalGeneratorError(Exception):
    """신호 생성 오류"""

    pass


class SignalGenerator:
    """
    AI 매매 신호 생성 서비스

    Gemini AI를 사용하여 XRP 시장 데이터를 분석하고
    Buy/Hold/Sell 신호를 생성합니다.

    사용 예시:
        generator = SignalGenerator(db_session)
        signal = await generator.generate_signal()
        print(f"신호: {signal.signal_type}, 신뢰도: {signal.confidence}")
    """

    def __init__(
        self,
        db: AsyncSession,
        ai_client: AIClient | None = None,
    ):
        """
        신호 생성기 초기화

        Args:
            db: SQLAlchemy 비동기 세션
            ai_client: AI 클라이언트 (기본값: 싱글톤 사용)
        """
        self.db = db
        self.ai_client = ai_client or get_ai_client()

    async def generate_signal(
        self,
        force: bool = False,
    ) -> TradingSignal:
        """
        매매 신호 생성

        시장 데이터를 수집하고 AI에게 분석을 요청하여
        매매 신호를 생성합니다.

        Args:
            force: 쿨다운 무시 여부 (스케줄러에서는 True)

        Returns:
            TradingSignal: 생성된 신호 (DB에 저장됨)

        Raises:
            SignalGeneratorError: 신호 생성 실패 시
        """
        # 쿨다운 체크 (수동 호출 시)
        if not force:
            await self._check_cooldown()

        # 시장 데이터 수집
        market_data_list = await self._get_recent_market_data()
        if not market_data_list:
            raise SignalGeneratorError("분석할 시장 데이터가 없습니다")

        latest_data = market_data_list[0]  # 가장 최근 데이터

        # 프롬프트 생성
        prompt = self._build_prompt(market_data_list)

        # AI 호출
        try:
            response = await self.ai_client.generate(
                prompt=prompt,
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,  # 일관성 위해 낮은 온도
                max_output_tokens=512,
            )
        except AIClientError as e:
            logger.error(f"AI 신호 생성 실패: {e}")
            raise SignalGeneratorError(f"AI API 오류: {e}") from e

        # 응답 파싱
        signal_type, confidence, reasoning = self._parse_response(response.text)

        # DB에 저장
        signal = TradingSignal(
            market_data_id=latest_data.id,
            signal_type=signal_type,
            confidence=Decimal(str(confidence)),
            reasoning=reasoning,
            created_at=datetime.now(UTC),
            model_name=response.model_name,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
        )
        self.db.add(signal)
        await self.db.commit()
        await self.db.refresh(signal)

        logger.info(f"신호 생성 완료: {signal_type} (신뢰도: {confidence:.2f})")

        return signal

    async def _check_cooldown(self) -> None:
        """
        쿨다운 체크

        마지막 신호 생성 후 일정 시간이 지나지 않았으면 오류 발생.

        Raises:
            SignalGeneratorError: 쿨다운 기간 내 재요청 시
        """
        cooldown_threshold = datetime.now(UTC) - timedelta(minutes=COOLDOWN_MINUTES)

        stmt = select(TradingSignal).where(
            TradingSignal.created_at > cooldown_threshold
        )
        result = await self.db.execute(stmt)
        recent_signal = result.scalar_one_or_none()

        if recent_signal:
            raise SignalGeneratorError(
                f"신호 생성 쿨다운 중입니다. {COOLDOWN_MINUTES}분 후에 다시 시도하세요."
            )

    async def _get_recent_market_data(
        self,
        hours: int = MARKET_DATA_HOURS,
    ) -> list[MarketData]:
        """
        최근 시장 데이터 조회

        Args:
            hours: 조회할 시간 범위

        Returns:
            list[MarketData]: 최근 시장 데이터 목록 (최신순)
        """
        since = datetime.now(UTC) - timedelta(hours=hours)

        stmt = (
            select(MarketData)
            .where(MarketData.timestamp > since)
            .order_by(desc(MarketData.timestamp))
            .limit(1000)  # 충분한 데이터 확보
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _build_prompt(self, market_data_list: list[MarketData]) -> str:
        """
        분석 프롬프트 생성

        시장 데이터를 기반으로 AI 분석 프롬프트를 구성합니다.

        Args:
            market_data_list: 시장 데이터 목록 (최신순)

        Returns:
            str: 구성된 프롬프트
        """
        latest = market_data_list[0]

        # 24시간 변동률 계산
        if len(market_data_list) > 1:
            oldest = market_data_list[-1]
            price_change_pct = (
                (float(latest.price) - float(oldest.price)) / float(oldest.price) * 100
            )
        else:
            price_change_pct = 0.0

        # 가격 추이 요약 (1시간 간격으로 샘플링)
        price_history = self._summarize_price_history(market_data_list)

        return ANALYSIS_PROMPT_TEMPLATE.format(
            timestamp=latest.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
            current_price=float(latest.price),
            high_price=float(latest.high_price),
            low_price=float(latest.low_price),
            volume=float(latest.volume),
            price_change_pct=price_change_pct,
            data_hours=MARKET_DATA_HOURS,
            price_history=price_history,
        )

    def _summarize_price_history(
        self,
        market_data_list: list[MarketData],
        interval_hours: int = 1,
    ) -> str:
        """
        가격 추이 요약

        시간별 가격 변화를 요약합니다.

        Args:
            market_data_list: 시장 데이터 목록
            interval_hours: 샘플링 간격 (시간)

        Returns:
            str: 가격 추이 요약 문자열
        """
        if not market_data_list:
            return "데이터 없음"

        # 시간대별로 그룹화
        hourly_prices: dict[str, float] = {}
        for data in market_data_list:
            hour_key = data.timestamp.strftime("%m/%d %H:00")
            if hour_key not in hourly_prices:
                hourly_prices[hour_key] = float(data.price)

        # 최근 6개 시간대만 표시
        recent_hours = list(hourly_prices.items())[:6]
        if not recent_hours:
            return "데이터 없음"

        lines = []
        for time_str, price in reversed(recent_hours):
            lines.append(f"- {time_str}: {price:,.0f} KRW")

        return "\n".join(lines)

    def _parse_response(self, text: str) -> tuple[str, float, str]:
        """
        AI 응답 파싱

        JSON 형식의 응답에서 신호, 신뢰도, 근거를 추출합니다.

        Args:
            text: AI 응답 텍스트

        Returns:
            tuple[str, float, str]: (signal_type, confidence, reasoning)
        """
        # JSON 블록 추출 시도
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # JSON 블록 없으면 전체 텍스트에서 시도
            json_str = text

        try:
            data = json.loads(json_str)
            signal = data.get("signal", "HOLD").upper()
            confidence = float(data.get("confidence", DEFAULT_CONFIDENCE))
            reasoning = data.get("reasoning", "분석 근거 없음")

            # 신호 타입 검증
            if signal not in [s.value for s in SignalType]:
                signal = SignalType.HOLD.value

            # 신뢰도 범위 검증
            confidence = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, confidence))

            return signal, confidence, reasoning

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"AI 응답 파싱 실패: {e}, 원본: {text[:200]}")

            # 기본값 반환
            return (
                SignalType.HOLD.value,
                DEFAULT_CONFIDENCE,
                f"파싱 실패로 기본 HOLD 신호 생성. 원본: {text[:100]}",
            )

    async def get_latest_signal(self) -> TradingSignal | None:
        """
        최신 신호 조회

        Returns:
            TradingSignal | None: 가장 최근 신호 또는 None
        """
        stmt = select(TradingSignal).order_by(desc(TradingSignal.created_at)).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_signals(
        self,
        limit: int = 50,
        signal_type: str | None = None,
    ) -> list[TradingSignal]:
        """
        신호 목록 조회

        Args:
            limit: 최대 조회 개수
            signal_type: 필터링할 신호 타입 (선택)

        Returns:
            list[TradingSignal]: 신호 목록 (최신순)
        """
        stmt = select(TradingSignal).order_by(desc(TradingSignal.created_at))

        if signal_type and signal_type != "all":
            stmt = stmt.where(TradingSignal.signal_type == signal_type.upper())

        stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())


# === 싱글톤 팩토리 ===
def get_signal_generator(db: AsyncSession) -> SignalGenerator:
    """
    SignalGenerator 인스턴스 생성

    Args:
        db: SQLAlchemy 비동기 세션

    Returns:
        SignalGenerator: 신호 생성기 인스턴스
    """
    return SignalGenerator(db)
