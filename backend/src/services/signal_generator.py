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
from sqlalchemy import desc, select
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

# === 시스템 프롬프트 (개선 버전) ===
SYSTEM_INSTRUCTION = """당신은 리플(XRP) 트레이딩 전문가 AI입니다.
주어진 시장 데이터, 기술적 지표, 멀티 타임프레임 분석 결과를 종합하여 매매 신호를 생성합니다.

## 핵심 원칙
1. **사실과 해석 분리**: 객관적 데이터(Fact)와 주관적 판단(Interpretation)을 명확히 구분
2. **멀티 타임프레임 일치**: 여러 시간대에서 신호가 일치할 때 높은 신뢰도 부여
3. **보수적 접근**: 불확실하면 HOLD, 손실 방지 우선
4. **피드백 학습**: 과거 신호 성과를 반영한 개선된 판단

## 의사결정 프레임워크
1. 장기 추세(주봉, 일봉) 확인 → 방향성 결정
2. 중기 추세(4시간) 확인 → 진입 타이밍
3. 단기 모멘텀(1시간) 확인 → 실행 결정
4. 기술적 지표 종합 → 신뢰도 조정
5. 과거 성과 피드백 반영 → 최종 결정

## 출력 형식
반드시 다음 JSON 형식으로만 응답하세요:
```json
{
  "signal": "BUY" | "HOLD" | "SELL",
  "confidence": 0.0 ~ 1.0,
  "reasoning": {
    "facts": [
      "RSI(14): XX.X (과매수/과매도/중립)",
      "볼린저밴드: 현재가 밴드 내 XX% 위치",
      "타임프레임 합류점수: X.XX/1.00",
      "타임프레임별 추세: 1H=상승/하락/횡보, 4H=..., 1D=..., 1W=..."
    ],
    "interpretation": "종합 해석 및 판단 근거 (2-3문장)",
    "key_factors": ["핵심 판단 요소 1", "핵심 판단 요소 2"],
    "risks": ["위험 요소 1"],
    "action_levels": {
      "stop_loss": "손절가 (선택)",
      "take_profit": "익절가 (선택)"
    }
  }
}
```

## 응답 필수 포함 요소
facts에 반드시 다음 정보를 포함하세요:
1. RSI 수치와 상태 (예: "RSI(14): 28.5 과매도")
2. 볼린저밴드 위치 (예: "BB 위치: 15% (하단 접근)")
3. 타임프레임 합류점수 (예: "합류점수: 0.35/1.00 (불일치)")
4. 각 타임프레임 추세 요약 (예: "1H/4H/1W 하락, 1D 횡보")

## 신뢰도 기준
- 0.8 이상: 모든 타임프레임 일치, 기술적 지표 강한 신호, 과거 성과 양호
- 0.6~0.8: 대부분 타임프레임 일치, 일부 불확실
- 0.4~0.6: 혼재된 신호, HOLD 권장
- 0.4 미만: 반대 신호 우세, 신중한 접근 필요

주의: JSON 외의 텍스트를 포함하지 마세요.
"""

# === 분석 프롬프트 템플릿 (개선 버전) ===
ANALYSIS_PROMPT_TEMPLATE = """## XRP/KRW 종합 시장 분석

### 1. 현재 시장 상황
- 분석 시각: {timestamp}
- 현재가: {current_price:,.0f} KRW
- 24시간 변동: {price_change_pct:+.2f}%
- 24시간 고가: {high_price:,.0f} KRW
- 24시간 저가: {low_price:,.0f} KRW
- 24시간 거래량: {volume:,.2f} XRP

### 2. 기술적 지표 분석 (일봉 기준)
{technical_indicators}

### 3. 멀티 타임프레임 분석
{multi_timeframe_analysis}

### 4. 객관적 사실 vs 해석
**사실 (Facts):**
{facts}

**해석 (Interpretations):**
{interpretations}

### 5. 과거 신호 성과 피드백
{performance_feedback}

### 6. 현재 포지션 상태
{asset_status}

### 7. 분석 요청
위의 모든 데이터를 종합하여 매매 신호를 생성하세요.

**신호 결정 기준:**
- BUY: 타임프레임 합류 점수 높음 + 기술적 지표 매수 신호 + KRW 잔고 충분
- SELL: 타임프레임 합류 점수 높음 + 기술적 지표 매도 신호 + XRP 보유 중
- HOLD: 신호 혼재 또는 불확실 + 현재 포지션 유지가 적절

**중요 고려사항:**
- 멀티 타임프레임 일치도가 높을수록 높은 신뢰도
- 과거 피드백에서 지적된 패턴 주의
- 변동성이 높으면 보수적 접근
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

        # 7. 응답 파싱
        signal_type, confidence, reasoning = self._parse_response(response.text)

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

        # 기술적 지표 문자열 생성
        technical_indicators = self._format_technical_indicators(mtf_result)

        # 멀티 타임프레임 분석 문자열 생성
        multi_timeframe_analysis = self._format_multi_timeframe(mtf_result)

        # 사실/해석 분리
        facts = self._format_facts(mtf_result)
        interpretations = self._format_interpretations(mtf_result)

        # 성과 피드백 문자열 생성
        performance_feedback = self._format_performance_feedback(perf_summary)

        # 자산 상태 문자열 생성
        asset_status = self._format_asset_status(balance_info)

        return ANALYSIS_PROMPT_TEMPLATE.format(
            timestamp=latest.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
            current_price=float(latest.price),
            price_change_pct=price_change_pct,
            high_price=float(latest.high_price),
            low_price=float(latest.low_price),
            volume=float(latest.volume),
            technical_indicators=technical_indicators,
            multi_timeframe_analysis=multi_timeframe_analysis,
            facts=facts,
            interpretations=interpretations,
            performance_feedback=performance_feedback,
            asset_status=asset_status,
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

    def _format_facts(self, mtf_result: MultiTimeframeResult) -> str:
        """객관적 사실 포맷"""
        if not mtf_result.facts:
            return "- 데이터 없음"

        # 중요한 사실만 선별 (최대 10개)
        selected_facts = mtf_result.facts[:10]
        return "\n".join(f"- {fact}" for fact in selected_facts)

    def _format_interpretations(self, mtf_result: MultiTimeframeResult) -> str:
        """주관적 해석 포맷"""
        if not mtf_result.interpretations:
            return "- 특이 패턴 없음"

        return "\n".join(f"- {interp}" for interp in mtf_result.interpretations)

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
        AI 응답 파싱 (개선 버전)

        JSON 형식의 응답에서 신호, 신뢰도, 근거를 추출합니다.
        구조화된 reasoning 형식을 처리합니다.

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

                if "interpretation" in reasoning_raw:
                    reasoning_parts.append(reasoning_raw["interpretation"])

                if "facts" in reasoning_raw and reasoning_raw["facts"]:
                    # facts에서 핵심 지표만 추출 (RSI, BB, 합류점수)
                    key_facts = []
                    for fact in reasoning_raw["facts"][:5]:
                        if any(kw in fact for kw in ["RSI", "볼린저", "BB", "합류", "타임프레임"]):
                            key_facts.append(fact)
                    if key_facts:
                        reasoning_parts.append("지표: " + " / ".join(key_facts[:3]))
                    else:
                        reasoning_parts.append("근거: " + ", ".join(reasoning_raw["facts"][:3]))

                if "key_factors" in reasoning_raw and reasoning_raw["key_factors"]:
                    reasoning_parts.append(
                        "핵심: " + ", ".join(reasoning_raw["key_factors"])
                    )

                if "risks" in reasoning_raw and reasoning_raw["risks"]:
                    reasoning_parts.append(
                        "위험: " + ", ".join(reasoning_raw["risks"])
                    )

                # action_levels 처리 (손절/익절가)
                if "action_levels" in reasoning_raw:
                    levels = reasoning_raw["action_levels"]
                    level_parts = []
                    if levels.get("stop_loss"):
                        level_parts.append(f"손절: {levels['stop_loss']}")
                    if levels.get("take_profit"):
                        level_parts.append(f"익절: {levels['take_profit']}")
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
