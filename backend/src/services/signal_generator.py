"""
AI 매매 신호 생성 서비스 (개선 버전)

이 모듈은 Gemini AI를 사용하여 암호화폐 매매 신호를 생성하는 서비스를 제공합니다.
- 기술적 지표 분석 (RSI, MACD, 볼린저밴드, EMA, ATR)
- 멀티 타임프레임 분석 (1H, 4H, 1D, 1W)
- 과거 신호 성과 피드백 (Verbal Feedback)
- Fact/Interpretation 분리 분석
"""

import json
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import MarketData, TradingSignal
from src.models.trading_signal import SignalType
from src.services.ai_client import AIClient, AIClientError, get_ai_client
from src.services.multi_timeframe_analyzer import (
    MultiTimeframeAnalyzer,
    MultiTimeframeResult,
    get_multi_timeframe_analyzer,
)
from src.services.signal_performance_tracker import (
    PerformanceSummary,
    SignalPerformanceTracker,
)
from src.services.upbit_client import UpbitError, get_upbit_client

# === 신호 생성 상수 ===
MIN_CONFIDENCE = 0.0  # 최소 신뢰도
MAX_CONFIDENCE = 1.0  # 최대 신뢰도
DEFAULT_CONFIDENCE = 0.5  # 기본 신뢰도 (파싱 실패 시)
MARKET_DATA_HOURS = 168  # 분석에 사용할 시장 데이터 기간 (7일)
COOLDOWN_MINUTES = 5  # 수동 신호 생성 쿨다운 (분)

# === 손절/익절 비율 상수 ===
STOP_LOSS_PCT = 0.07  # 손절 비율 (7%)
TAKE_PROFIT_PCT = 0.10  # 익절 비율 (10%)
TRAILING_STOP_THRESHOLD_PCT = 0.07  # 트레일링 스탑 활성화 수익률 (7%)
BREAKEVEN_THRESHOLD_PCT = 0.03  # 본전 손절 활성화 수익률 (3%)

# === 시스템 프롬프트 (Risk First 버전) ===
SYSTEM_INSTRUCTION = """당신은 리플(XRP) 트레이딩 전문가 AI입니다.

## 최우선 원칙: 리스크 관리 (Risk First)

### 손절 강제 규칙 (MANDATORY - 기술적 분석보다 우선)
다음 조건 중 **하나라도** 충족되면 무조건 **SELL** 신호 (신뢰도 0.9):
1. 현재가 <= 평균매수가 × 0.93 (7% 손실)
2. 미실현 손실 >= 7%
3. 현재가 < 이전 설정 손절가

**중요**: 반등 가능성, 기술적 반전 신호가 있어도 손절 규칙 우선!

### 포지션 상태별 의사결정

#### 포지션 없음 (현금 100%)
| 조건 | 신호 | 신뢰도 |
|------|------|--------|
| Confluence >= 0.65 AND RSI < 65 AND 2개+ TF 상승 | BUY | 0.7-0.85 |
| Confluence >= 0.55 AND RSI < 50 | BUY (소량) | 0.55-0.7 |
| 그 외 | HOLD | 0.4-0.6 |

#### XRP 보유 중 - 수익 상태 (현재가 > 평균매수가)
| 수익률 | 조건 | 신호 |
|--------|------|------|
| +10% 이상 | 하락 추세 전환 신호 | SELL (익절) |
| +7% 이상 | Confluence <= 0.4 | SELL (익절) |
| +5% 이상 | 모든 TF 하락 전환 | SELL (익절) |
| +3~5% | 손절가를 평균매수가로 상향 | HOLD |
| 0~+3% | 상승 추세 유지 시 | HOLD |

#### XRP 보유 중 - 손실 상태 (현재가 < 평균매수가)
| 손실률 | 조건 | 신호 | 이유 |
|--------|------|------|------|
| -7% 이상 | 무조건 | **SELL** | 강제 손절 |
| -5~7% | 모든 TF 하락 | SELL | 손실 확대 방지 |
| -5~7% | 반등 신호 있음 | HOLD | 관망 |
| -3~5% | 관망 | HOLD | 노이즈 범위 |
| 0~-3% | 상승 신호 시 | BUY (물타기) | 평단가 낮춤 |

### 신호 결정 기준 (Confluence Score 기반)

**SELL 조건 (OR 연산 - 하나만 충족해도 SELL)**
- 손절 강제 규칙 해당
- 미실현 이익 >= 7% AND Confluence <= 0.45
- 모든 타임프레임(1H, 4H, 1D) 하락 추세
- RSI >= 75 AND 미실현 이익 > 3%

**BUY 조건 (AND 연산)**
- Confluence >= 0.60
- 미실현 손실 < 5% 또는 포지션 없음
- RSI < 65
- 최소 2개 타임프레임 상승 추세

**HOLD 조건**
- 위 조건 모두 미충족
- Confluence 0.45 ~ 0.55

### 손절/익절가 계산 (XRP 기준)

| 상황 | 손절가 | 익절가 |
|------|--------|--------|
| 신규 진입 | 평균매수가 × 0.93 (-7%) | 평균매수가 × 1.10 (+10%) |
| 수익 3%+ | 평균매수가 (본전) | 평균매수가 × 1.12 (+12%) |
| 수익 7%+ | 현재가 × 0.95 (트레일링) | 평균매수가 × 1.15 (+15%) |

### 신뢰도 기준

| 신뢰도 | 조건 |
|--------|------|
| 0.85-1.0 | 손절 강제 조건 OR 모든 TF 일치 + 강한 기술적 신호 |
| 0.70-0.85 | 3개 TF 일치 + 기술적 지표 지지 |
| 0.55-0.70 | 2개 TF 일치 또는 일부 지표 불일치 |
| 0.40-0.55 | 신호 혼재, HOLD 권장 |
| 0.40 미만 | 반대 신호 우세 |

## 출력 형식
```json
{
  "signal": "BUY" | "HOLD" | "SELL",
  "confidence": 0.0 ~ 1.0,
  "reasoning": {
    "risk_assessment": {
      "stop_loss_triggered": true/false,
      "trigger_reason": "손절 트리거 사유",
      "unrealized_pnl_pct": X.X,
      "position_status": "수익/손실/없음"
    },
    "technical_summary": {
      "confluence_score": 0.XX,
      "rsi_14": XX.X,
      "trend_1h": "상승/하락/횡보",
      "trend_4h": "상승/하락/횡보",
      "trend_1d": "상승/하락/횡보"
    },
    "decision_rationale": "결정 근거 (2-3문장)",
    "action_levels": {
      "stop_loss": "XXXX KRW",
      "take_profit": "XXXX KRW"
    }
  }
}
```

주의: JSON 외의 텍스트를 포함하지 마세요.
"""

# === 분석 프롬프트 템플릿 (Risk First 버전) ===
ANALYSIS_PROMPT_TEMPLATE = """## XRP/KRW 매매 신호 분석

### 1. 시장 현황
- 분석 시각: {timestamp}
- 현재가: {current_price:,.0f} KRW
- 24시간 변동: {price_change_pct:+.2f}%

### 2. 포지션 상태 (최우선 확인!)
{asset_status}

### 3. 리스크 체크 (손절 강제 규칙)
{risk_check}

**질문: 위 리스크 체크에서 손절 조건이 충족되었습니까?**
- 충족 → 즉시 SELL 신호 생성 (기술적 분석 무시)
- 미충족 → 아래 분석 진행

### 4. 기술적 지표
{technical_indicators}

### 5. 멀티 타임프레임 분석
{multi_timeframe_analysis}

### 6. 과거 성과 피드백
{performance_feedback}

### 7. 의사결정 체크리스트 (순서대로 진행)

**Step 1: 손절 체크 (최우선)**
- [ ] 미실현 손실 >= 7%? → SELL (신뢰도 0.9)
- [ ] 현재가 < 이전 손절가? → SELL (신뢰도 0.9)

**Step 2: 익절 체크**
- [ ] 미실현 이익 >= 10% AND 하락 신호? → SELL
- [ ] 미실현 이익 >= 7% AND Confluence <= 0.45? → SELL

**Step 3: 매수 체크**
- [ ] 포지션 없음 AND Confluence >= 0.60 AND RSI < 65? → BUY
- [ ] 손실 < 3% AND 상승 신호 AND 잔고 충분? → BUY (물타기)

**Step 4: 홀드**
- [ ] 위 조건 모두 미충족? → HOLD

### 8. 최종 분석 요청

위 체크리스트를 **순서대로** 검토하고 **첫 번째로 충족되는 조건**의 신호를 생성하세요.

**금지사항:**
- 손절 조건 충족 시 "반등 가능성"을 이유로 HOLD 금지
- "추가 하락 여력 제한"은 판단 근거가 될 수 없음
- 불확실하다는 이유만으로 HOLD 금지 (구체적 근거 필요)
"""


class SignalGeneratorError(Exception):
    """신호 생성 오류"""

    pass


class SignalGenerator:
    """
    AI 매매 신호 생성 서비스 (개선 버전)

    Gemini AI를 사용하여 XRP 시장 데이터를 분석하고
    Buy/Hold/Sell 신호를 생성합니다.

    개선 사항:
    - 기술적 지표 분석 (RSI, MACD, 볼린저밴드, EMA, ATR)
    - 멀티 타임프레임 분석 (1H, 4H, 1D, 1W)
    - 과거 신호 성과 피드백
    - Fact/Interpretation 분리

    사용 예시:
        generator = SignalGenerator(db_session)
        signal = await generator.generate_signal()
        print(f"신호: {signal.signal_type}, 신뢰도: {signal.confidence}")
    """

    def __init__(
        self,
        db: AsyncSession,
        ai_client: AIClient | None = None,
        mtf_analyzer: MultiTimeframeAnalyzer | None = None,
    ):
        """
        신호 생성기 초기화

        Args:
            db: SQLAlchemy 비동기 세션
            ai_client: AI 클라이언트 (기본값: 싱글톤 사용)
            mtf_analyzer: 멀티 타임프레임 분석기 (기본값: 싱글톤 사용)
        """
        self.db = db
        self.ai_client = ai_client or get_ai_client()
        self.mtf_analyzer = mtf_analyzer or get_multi_timeframe_analyzer()

    async def generate_signal(
        self,
        force: bool = False,
    ) -> TradingSignal:
        """
        매매 신호 생성 (개선 버전)

        기술적 지표, 멀티 타임프레임 분석, 과거 성과 피드백을 종합하여
        AI에게 분석을 요청하고 매매 신호를 생성합니다.

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

        # 1. 시장 데이터 수집 (기존)
        market_data_list = await self._get_recent_market_data()
        if not market_data_list:
            raise SignalGeneratorError("분석할 시장 데이터가 없습니다")

        latest_data = market_data_list[0]  # 가장 최근 데이터
        current_price = float(latest_data.price)

        # 2. 멀티 타임프레임 분석 (신규)
        try:
            mtf_result = await self.mtf_analyzer.analyze("KRW-XRP")
        except Exception as e:
            logger.warning(f"멀티 타임프레임 분석 실패: {e}")
            mtf_result = MultiTimeframeResult()

        # 3. 과거 신호 성과 피드백 (신규)
        try:
            perf_tracker = SignalPerformanceTracker(self.db)
            perf_summary = await perf_tracker.generate_performance_summary(limit=30)
        except Exception as e:
            logger.warning(f"성과 피드백 생성 실패: {e}")
            perf_summary = PerformanceSummary()

        # 4. 잔고 정보 조회
        balance_info = await self._get_balance_info()

        # 5. 개선된 프롬프트 생성
        prompt = self._build_enhanced_prompt(
            market_data_list=market_data_list,
            mtf_result=mtf_result,
            perf_summary=perf_summary,
            balance_info=balance_info,
        )

        # 디버그: 생성된 프롬프트 로깅
        logger.info(f"AI 프롬프트 생성 완료 (길이: {len(prompt)}자)")
        logger.debug(f"프롬프트:\n{prompt}")

        # 6. AI 호출
        try:
            response = await self.ai_client.generate(
                prompt=prompt,
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.3,  # 일관성 위해 낮은 온도
                max_output_tokens=1024,  # 구조화된 응답을 위해 증가
            )
        except AIClientError as e:
            logger.error(f"AI 신호 생성 실패: {e}")
            raise SignalGeneratorError(f"AI API 오류: {e}") from e

        # 7. 응답 파싱 (포지션 정보 전달하여 익절/손절가 검증)
        signal_type, confidence, reasoning = self._parse_response(
            response.text,
            balance_info=balance_info,
        )

        # 8. 기술적 지표 스냅샷 생성
        technical_snapshot = self._create_technical_snapshot(mtf_result)

        # 9. DB에 저장 (성과 추적 필드 포함)
        signal = TradingSignal(
            market_data_id=latest_data.id,
            signal_type=signal_type,
            confidence=Decimal(str(confidence)),
            reasoning=reasoning,
            created_at=datetime.now(UTC),
            model_name=response.model_name,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            # 성과 추적 필드 (신규)
            price_at_signal=Decimal(str(current_price)),
            technical_snapshot=technical_snapshot,
        )
        self.db.add(signal)
        await self.db.commit()
        await self.db.refresh(signal)

        logger.info(
            f"신호 생성 완료: {signal_type} (신뢰도: {confidence:.2f}, "
            f"합류점수: {mtf_result.confluence_score:.2f})"
        )

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

    async def _get_balance_info(self) -> dict | None:
        """
        Upbit 잔고 정보 조회

        Returns:
            dict | None: 잔고 정보 딕셔너리 또는 None (조회 실패 시)
        """
        try:
            client = get_upbit_client()
            accounts = await client.get_accounts()

            krw_available = Decimal("0")
            xrp_available = Decimal("0")
            xrp_avg_price = Decimal("0")

            for acc in accounts:
                if acc.currency == "KRW":
                    krw_available = acc.balance
                elif acc.currency == "XRP":
                    xrp_available = acc.balance
                    xrp_avg_price = acc.avg_buy_price

            # 현재가 조회
            try:
                ticker = await client.get_ticker("KRW-XRP")
                current_price = ticker.trade_price
            except UpbitError:
                current_price = xrp_avg_price

            # 미실현 손익 계산
            xrp_value = xrp_available * current_price
            total_krw = krw_available + xrp_value
            unrealized_pnl = Decimal("0")
            unrealized_pnl_pct = 0.0

            if xrp_available > 0 and xrp_avg_price > 0:
                unrealized_pnl = (current_price - xrp_avg_price) * xrp_available
                unrealized_pnl_pct = float(
                    (current_price - xrp_avg_price) / xrp_avg_price * 100
                )

            return {
                "krw_available": krw_available,
                "xrp_available": xrp_available,
                "xrp_avg_price": xrp_avg_price,
                "current_price": current_price,
                "total_krw": total_krw,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
            }

        except UpbitError as e:
            logger.warning(f"잔고 조회 실패: {e.message}")
            return None
        except Exception as e:
            logger.warning(f"잔고 조회 중 오류: {e}")
            return None

    def _format_asset_status(self, balance_info: dict | None) -> str:
        """
        자산 상태 문자열 생성

        Args:
            balance_info: 잔고 정보

        Returns:
            str: 자산 상태 문자열
        """
        if balance_info is None:
            return "- 자산 정보 조회 불가 (API 키 미설정 또는 오류)"

        lines = []
        lines.append(f"- KRW 가용 잔고: {float(balance_info['krw_available']):,.0f} KRW")
        lines.append(f"- XRP 보유량: {float(balance_info['xrp_available']):.4f} XRP")

        if balance_info["xrp_available"] > 0:
            lines.append(
                f"- XRP 평균 매수가: {float(balance_info['xrp_avg_price']):,.0f} KRW"
            )
            lines.append(
                f"- 미실현 손익: {float(balance_info['unrealized_pnl']):+,.0f} KRW "
                f"({balance_info['unrealized_pnl_pct']:+.2f}%)"
            )

        lines.append(f"- 총 평가금액: {float(balance_info['total_krw']):,.0f} KRW")

        return "\n".join(lines)

    def _format_risk_check(self, balance_info: dict | None) -> str:
        """
        손절 조건 체크 결과 포맷

        손절 강제 규칙을 적용하여 현재 포지션의 리스크 상태를 명시적으로 표시.
        AI가 손절 조건 충족 여부를 명확히 인지하도록 함.

        Args:
            balance_info: 잔고 정보

        Returns:
            str: 리스크 체크 결과 문자열
        """
        if not balance_info or float(balance_info.get("xrp_available", 0)) <= 0:
            return "- 포지션 없음: 손절 체크 해당 없음"

        pnl_pct = balance_info["unrealized_pnl_pct"]
        current = float(balance_info["current_price"])
        avg = float(balance_info["xrp_avg_price"])
        stop_loss = avg * 0.93  # 7% 손절

        lines = [f"- 미실현 손익률: {pnl_pct:+.2f}%"]
        lines.append(f"- 손절 기준가: {stop_loss:,.0f} KRW (평균매수가 -7%)")
        lines.append(f"- 현재가와 손절가 차이: {((current - stop_loss) / stop_loss * 100):+.2f}%")

        # 손절 조건 판단
        if pnl_pct <= -7:
            lines.append("")
            lines.append("=" * 50)
            lines.append("**[손절 조건 충족] 미실현 손실 7% 초과!**")
            lines.append("→ 즉시 SELL 신호 생성 필수 (신뢰도 0.9)")
            lines.append("=" * 50)
        elif current <= stop_loss:
            lines.append("")
            lines.append("=" * 50)
            lines.append("**[손절 조건 충족] 현재가 < 손절가!**")
            lines.append("→ 즉시 SELL 신호 생성 필수 (신뢰도 0.9)")
            lines.append("=" * 50)
        elif pnl_pct <= -5:
            lines.append("")
            lines.append("**[경고] 미실현 손실 5% 초과 - 추세 확인 후 손절 검토**")

        return "\n".join(lines)

    def _build_enhanced_prompt(
        self,
        market_data_list: list[MarketData],
        mtf_result: MultiTimeframeResult,
        perf_summary: PerformanceSummary,
        balance_info: dict | None = None,
    ) -> str:
        """
        개선된 분석 프롬프트 생성

        기술적 지표, 멀티 타임프레임 분석, 성과 피드백을 포함한 프롬프트 생성.

        Args:
            market_data_list: 시장 데이터 목록 (최신순)
            mtf_result: 멀티 타임프레임 분석 결과
            perf_summary: 과거 성과 요약
            balance_info: 잔고 정보 (선택)

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

        # 자산 상태 문자열 생성
        asset_status = self._format_asset_status(balance_info)

        # 리스크 체크 문자열 생성 (손절 강제 규칙)
        risk_check = self._format_risk_check(balance_info)

        # 기술적 지표 문자열 생성
        technical_indicators = self._format_technical_indicators(mtf_result)

        # 멀티 타임프레임 분석 문자열 생성
        multi_timeframe_analysis = self._format_multi_timeframe(mtf_result)

        # 성과 피드백 문자열 생성
        performance_feedback = self._format_performance_feedback(perf_summary)

        return ANALYSIS_PROMPT_TEMPLATE.format(
            timestamp=latest.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
            current_price=float(latest.price),
            price_change_pct=price_change_pct,
            asset_status=asset_status,
            risk_check=risk_check,
            technical_indicators=technical_indicators,
            multi_timeframe_analysis=multi_timeframe_analysis,
            performance_feedback=performance_feedback,
        )

    def _format_technical_indicators(self, mtf_result: MultiTimeframeResult) -> str:
        """기술적 지표 문자열 포맷"""
        if "1d" not in mtf_result.analyses:
            return "- 기술적 지표 데이터 없음"

        daily = mtf_result.analyses["1d"]
        ind = daily.indicators

        lines = []

        # RSI
        rsi_status = {"oversold": "과매도", "overbought": "과매수", "neutral": "중립"}
        lines.append(f"**RSI (14일):** {ind.rsi_14:.1f} ({rsi_status.get(ind.rsi_signal, ind.rsi_signal)})")

        # MACD
        macd_status = {"bullish": "매수 신호", "bearish": "매도 신호", "neutral": "중립"}
        lines.append(
            f"**MACD (12-26-9):** Line={ind.macd_line:.4f}, Signal={ind.signal_line:.4f}, "
            f"Histogram={ind.macd_histogram:.4f} ({macd_status.get(ind.macd_signal, ind.macd_signal)})"
        )

        # 볼린저 밴드
        bb_status = {
            "overbought": "상단 돌파",
            "oversold": "하단 돌파",
            "upper_zone": "상단 접근",
            "lower_zone": "하단 접근",
            "neutral": "중립",
        }
        lines.append(
            f"**볼린저 밴드 (20일, 2σ):** 상단={ind.bb_upper:,.0f}, 중단={ind.bb_middle:,.0f}, "
            f"하단={ind.bb_lower:,.0f}, 위치={ind.bb_percent:.1f}% ({bb_status.get(ind.bb_signal, ind.bb_signal)})"
        )

        # EMA
        ema_status = {"bullish": "정배열", "bearish": "역배열", "mixed": "혼조"}
        lines.append(
            f"**EMA:** 9일={ind.ema_9:,.0f}, 21일={ind.ema_21:,.0f}, 50일={ind.ema_50:,.0f} "
            f"({ema_status.get(ind.ema_alignment, ind.ema_alignment)})"
        )

        # 변동성
        vol_status = {"low": "낮음", "medium": "보통", "high": "높음"}
        lines.append(
            f"**변동성:** ATR(14)={ind.atr_14:.2f}, 수준={vol_status.get(ind.volatility_level, ind.volatility_level)}"
        )

        return "\n".join(lines)

    def _format_multi_timeframe(self, mtf_result: MultiTimeframeResult) -> str:
        """멀티 타임프레임 분석 문자열 포맷"""
        lines = []

        tf_names = {"1h": "1시간봉", "4h": "4시간봉", "1d": "일봉", "1w": "주봉"}
        trend_kr = {"bullish": "상승", "bearish": "하락", "sideways": "횡보"}

        for tf in ["1h", "4h", "1d", "1w"]:
            if tf in mtf_result.analyses:
                analysis = mtf_result.analyses[tf]
                trend_text = trend_kr.get(analysis.trend, analysis.trend)
                lines.append(
                    f"- **{tf_names[tf]}:** {trend_text} 추세 (강도 {analysis.strength:.0%})"
                )
                lines.append(f"  - {analysis.key_observation}")
            else:
                lines.append(f"- **{tf_names[tf]}:** 데이터 없음")

        # 합류 점수
        bias_kr = {
            "strong_buy": "강한 매수",
            "buy": "매수",
            "neutral": "중립",
            "sell": "매도",
            "strong_sell": "강한 매도",
        }
        lines.append("")
        lines.append(f"**타임프레임 합류 점수:** {mtf_result.confluence_score:.2f}/1.00")
        lines.append(f"**종합 편향:** {bias_kr.get(mtf_result.overall_bias, mtf_result.overall_bias)}")

        return "\n".join(lines)

    def _format_performance_feedback(self, perf_summary: PerformanceSummary) -> str:
        """성과 피드백 포맷"""
        lines = []

        if perf_summary.total_signals == 0:
            return "- 평가된 신호가 없습니다. 첫 분석입니다."

        # 기본 통계
        lines.append(f"**분석 대상:** 최근 {perf_summary.total_signals}개 신호")
        lines.append(
            f"**신호 분포:** 매수 {perf_summary.buy_signals}건, "
            f"매도 {perf_summary.sell_signals}건, 홀드 {perf_summary.hold_signals}건"
        )
        lines.append(f"**매수 정확도:** {perf_summary.buy_accuracy:.1f}%")
        lines.append(f"**매도 정확도:** {perf_summary.sell_accuracy:.1f}%")
        lines.append(f"**평균 24시간 수익률:** {perf_summary.avg_pnl_24h:+.2f}%")

        # Verbal Feedback
        if perf_summary.feedback_summary:
            lines.append("")
            lines.append(f"**피드백:** {perf_summary.feedback_summary}")

        # 개선 제안
        if perf_summary.improvement_suggestions:
            lines.append("")
            lines.append("**개선 제안:**")
            for suggestion in perf_summary.improvement_suggestions[:3]:
                lines.append(f"- {suggestion}")

        return "\n".join(lines)

    def _create_technical_snapshot(self, mtf_result: MultiTimeframeResult) -> str:
        """기술적 지표 스냅샷 생성 (JSON)"""
        snapshot = {
            "timestamp": datetime.now(UTC).isoformat(),
            "confluence_score": mtf_result.confluence_score,
            "overall_bias": mtf_result.overall_bias,
            "timeframes": {},
        }

        for tf, analysis in mtf_result.analyses.items():
            snapshot["timeframes"][tf] = {
                "trend": analysis.trend,
                "strength": analysis.strength,
                "indicators": {
                    "rsi_14": analysis.indicators.rsi_14,
                    "macd_signal": analysis.indicators.macd_signal,
                    "bb_percent": analysis.indicators.bb_percent,
                    "ema_alignment": analysis.indicators.ema_alignment,
                    "volatility_level": analysis.indicators.volatility_level,
                },
            }

        return json.dumps(snapshot, ensure_ascii=False)

    def _parse_response(
        self,
        text: str,
        balance_info: dict | None = None,
    ) -> tuple[str, float, str]:
        """
        AI 응답 파싱 (개선 버전)

        JSON 형식의 응답에서 신호, 신뢰도, 근거를 추출합니다.
        구조화된 reasoning 형식을 처리합니다.
        포지션 정보가 있으면 익절/손절가 유효성도 검증합니다.

        Args:
            text: AI 응답 텍스트
            balance_info: 잔고 정보 (익절/손절가 검증용)

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
            reasoning_raw = data.get("reasoning", "분석 근거 없음")

            # 신호 타입 검증
            if signal not in [s.value for s in SignalType]:
                signal = SignalType.HOLD.value

            # 신뢰도 범위 검증
            confidence = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, confidence))

            # reasoning 처리 (구조화된 형식 또는 단순 문자열)
            if isinstance(reasoning_raw, dict):
                # 구조화된 reasoning을 읽기 쉬운 형식으로 변환
                reasoning_parts = []

                # 새 형식: risk_assessment 처리
                if "risk_assessment" in reasoning_raw:
                    risk = reasoning_raw["risk_assessment"]
                    if risk.get("stop_loss_triggered"):
                        reasoning_parts.append(
                            f"[손절 트리거] {risk.get('trigger_reason', '손절 조건 충족')}"
                        )
                    pnl_pct = risk.get("unrealized_pnl_pct")
                    if pnl_pct is not None:
                        reasoning_parts.append(f"손익률: {pnl_pct:+.1f}%")

                # 새 형식: decision_rationale 처리
                if "decision_rationale" in reasoning_raw:
                    reasoning_parts.append(reasoning_raw["decision_rationale"])
                # 구 형식: interpretation 처리 (하위 호환)
                elif "interpretation" in reasoning_raw:
                    reasoning_parts.append(reasoning_raw["interpretation"])

                # 새 형식: technical_summary 처리
                if "technical_summary" in reasoning_raw:
                    tech = reasoning_raw["technical_summary"]
                    tech_parts = []
                    if tech.get("confluence_score") is not None:
                        tech_parts.append(f"합류: {tech['confluence_score']:.2f}")
                    if tech.get("rsi_14") is not None:
                        tech_parts.append(f"RSI: {tech['rsi_14']:.1f}")
                    trends = []
                    for tf in ["1h", "4h", "1d"]:
                        trend_key = f"trend_{tf}"
                        if tech.get(trend_key):
                            trends.append(f"{tf.upper()}={tech[trend_key]}")
                    if trends:
                        tech_parts.append(" ".join(trends))
                    if tech_parts:
                        reasoning_parts.append("지표: " + " / ".join(tech_parts))
                # 구 형식: facts 처리 (하위 호환)
                elif "facts" in reasoning_raw and reasoning_raw["facts"]:
                    key_facts = []
                    for fact in reasoning_raw["facts"][:5]:
                        if any(kw in fact for kw in ["RSI", "볼린저", "BB", "합류", "타임프레임"]):
                            key_facts.append(fact)
                    if key_facts:
                        reasoning_parts.append("지표: " + " / ".join(key_facts[:3]))
                    else:
                        reasoning_parts.append("근거: " + ", ".join(reasoning_raw["facts"][:3]))

                # 구 형식: key_factors 처리 (하위 호환)
                if "key_factors" in reasoning_raw and reasoning_raw["key_factors"]:
                    reasoning_parts.append(
                        "핵심: " + ", ".join(reasoning_raw["key_factors"])
                    )

                # 구 형식: risks 처리 (하위 호환)
                if "risks" in reasoning_raw and reasoning_raw["risks"]:
                    reasoning_parts.append(
                        "위험: " + ", ".join(reasoning_raw["risks"])
                    )

                # action_levels 처리 (손절/익절가)
                if "action_levels" in reasoning_raw:
                    levels = reasoning_raw["action_levels"]
                    # 포지션 기반 익절/손절가 검증
                    validated_levels = self._validate_action_levels(levels, balance_info)
                    level_parts = []
                    if validated_levels.get("stop_loss"):
                        level_parts.append(f"손절: {validated_levels['stop_loss']}")
                    if validated_levels.get("take_profit"):
                        level_parts.append(f"익절: {validated_levels['take_profit']}")
                    if level_parts:
                        reasoning_parts.append(" / ".join(level_parts))

                reasoning = " | ".join(reasoning_parts) if reasoning_parts else "분석 근거 없음"
            else:
                reasoning = str(reasoning_raw)

            return signal, confidence, reasoning

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"AI 응답 파싱 실패: {e}, 원본: {text[:200]}")

            # 기본값 반환
            return (
                SignalType.HOLD.value,
                DEFAULT_CONFIDENCE,
                f"파싱 실패로 기본 HOLD 신호 생성. 원본: {text[:100]}",
            )

    def _parse_price(self, price_str: str | None) -> float | None:
        """
        가격 문자열 파싱

        "3,200", "3200원", "3,200 KRW" 등의 형식을 float로 변환.

        Args:
            price_str: 가격 문자열

        Returns:
            float | None: 파싱된 가격 또는 None
        """
        if not price_str:
            return None

        try:
            # 숫자와 소수점만 추출
            cleaned = re.sub(r"[^\d.]", "", str(price_str))
            if cleaned:
                return float(cleaned)
            return None
        except (ValueError, TypeError):
            return None

    def _validate_action_levels(
        self,
        levels: dict,
        balance_info: dict | None,
    ) -> dict:
        """
        익절/손절가가 포지션 평균 매수가 기준으로 유효한지 검증

        - 익절(이익 실현): 매도가 > 평균 매수가 (수익 상태에서 매도)
        - 손절(손실 확정): 매도가 < 평균 매수가 (손실을 감수하고 매도)

        잘못된 가격은 제거하고 경고 로그 남김.

        Args:
            levels: {"take_profit": ..., "stop_loss": ...}
            balance_info: 잔고 정보 딕셔너리

        Returns:
            dict: 검증된 action_levels
        """
        if not balance_info or float(balance_info.get("xrp_available", 0)) <= 0:
            return levels  # 포지션 없으면 검증 스킵

        avg_price = float(balance_info["xrp_avg_price"])
        if avg_price <= 0:
            return levels  # 평균 매수가 없으면 스킵

        validated = dict(levels)

        # 익절가 검증: 평균 매수가보다 낮으면 익절이 아님 (제거)
        if levels.get("take_profit"):
            tp = self._parse_price(levels["take_profit"])
            if tp and tp <= avg_price:
                logger.warning(
                    f"익절가({tp:,.0f}원)가 평균매수가({avg_price:,.0f}원)보다 낮음 - "
                    f"이 가격에 매도하면 손실이므로 익절가에서 제거"
                )
                validated["take_profit"] = None

        # 손절가 검증: 평균 매수가보다 높으면 손절이 아님 (제거)
        if levels.get("stop_loss"):
            sl = self._parse_price(levels["stop_loss"])
            if sl and sl >= avg_price:
                logger.warning(
                    f"손절가({sl:,.0f}원)가 평균매수가({avg_price:,.0f}원)보다 높음 - "
                    f"이 가격에 매도하면 이익이므로 손절가에서 제거"
                )
                validated["stop_loss"] = None

        return validated

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
        offset: int = 0,
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

        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_signals_count(self, signal_type: str | None = None) -> int:
        """
        신호 총 개수 조회

        Args:
            signal_type: 필터링할 신호 타입 (선택)

        Returns:
            int: 총 신호 개수
        """
        stmt = select(func.count()).select_from(TradingSignal)

        if signal_type and signal_type != "all":
            stmt = stmt.where(TradingSignal.signal_type == signal_type.upper())

        result = await self.db.execute(stmt)
        return result.scalar() or 0


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
