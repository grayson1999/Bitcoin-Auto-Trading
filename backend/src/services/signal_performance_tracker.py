"""
신호 성과 추적 서비스

과거 AI 매매 신호의 성과를 평가하고 피드백을 생성합니다.
Multi-Agent Bitcoin Trading System의 verbal feedback 메커니즘을 적용합니다.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import TradingSignal
from src.models.trading_signal import SignalType
from src.services.upbit_client import UpbitClient, get_upbit_client


@dataclass
class SignalOutcome:
    """
    개별 신호 성과 결과

    Attributes:
        signal_id: 신호 ID
        signal_type: 신호 타입
        confidence: 신뢰도
        price_at_signal: 신호 생성 시 가격
        price_after_4h: 4시간 후 가격
        price_after_24h: 24시간 후 가격
        pnl_percent_4h: 4시간 후 수익률 (%)
        pnl_percent_24h: 24시간 후 수익률 (%)
        was_correct: 신호 정확성 (방향 일치 여부)
        created_at: 신호 생성 시간
    """

    signal_id: int
    signal_type: str
    confidence: float
    price_at_signal: float
    price_after_4h: float | None
    price_after_24h: float | None
    pnl_percent_4h: float | None
    pnl_percent_24h: float | None
    was_correct: bool | None
    created_at: datetime


@dataclass
class PerformanceSummary:
    """
    성과 요약

    Attributes:
        total_signals: 총 신호 수
        buy_signals: 매수 신호 수
        sell_signals: 매도 신호 수
        hold_signals: 홀드 신호 수
        buy_accuracy: 매수 정확도 (%)
        sell_accuracy: 매도 정확도 (%)
        avg_confidence: 평균 신뢰도
        avg_pnl_4h: 평균 4시간 수익률 (%)
        avg_pnl_24h: 평균 24시간 수익률 (%)
        feedback_summary: 피드백 요약 (한국어)
        improvement_suggestions: 개선 제안 목록
        recent_patterns: 최근 패턴 목록
    """

    total_signals: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    hold_signals: int = 0
    buy_accuracy: float = 0.0
    sell_accuracy: float = 0.0
    avg_confidence: float = 0.0
    avg_pnl_4h: float = 0.0
    avg_pnl_24h: float = 0.0
    feedback_summary: str = ""
    improvement_suggestions: list[str] = field(default_factory=list)
    recent_patterns: list[str] = field(default_factory=list)


class SignalPerformanceTracker:
    """
    신호 성과 추적기

    과거 신호의 성과를 평가하고 학습 피드백을 생성합니다.

    사용 예시:
        tracker = SignalPerformanceTracker(db)
        await tracker.evaluate_pending_signals()
        summary = await tracker.generate_performance_summary()
    """

    def __init__(
        self,
        db: AsyncSession,
        upbit_client: UpbitClient | None = None,
    ):
        """
        신호 성과 추적기 초기화

        Args:
            db: 데이터베이스 세션
            upbit_client: Upbit API 클라이언트 (기본값: 싱글톤)
        """
        self.db = db
        self.upbit_client = upbit_client or get_upbit_client()

    async def evaluate_pending_signals(self, market: str | None = None) -> int:
        """
        미평가 신호들의 성과 평가

        4시간 이상 경과한 신호 중 아직 평가되지 않은 신호를 평가합니다.

        Args:
            market: 마켓 코드 (기본값: settings.trading_ticker)

        Returns:
            int: 평가된 신호 수
        """
        market = market or settings.trading_ticker

        # 현재 가격 조회
        try:
            ticker = await self.upbit_client.get_ticker(market)
            current_price = float(ticker.trade_price)
        except Exception as e:
            logger.error(f"현재가 조회 실패: {e}")
            return 0

        now = datetime.now(UTC)
        cutoff_4h = now - timedelta(hours=4)
        cutoff_24h = now - timedelta(hours=24)

        # 4시간 경과했지만 아직 4시간 가격이 없는 신호 업데이트
        stmt_4h = (
            select(TradingSignal)
            .where(
                and_(
                    TradingSignal.created_at < cutoff_4h,
                    TradingSignal.price_at_signal.isnot(None),
                    TradingSignal.price_after_4h.is_(None),
                )
            )
            .limit(100)
        )

        result_4h = await self.db.execute(stmt_4h)
        signals_4h = list(result_4h.scalars().all())

        for signal in signals_4h:
            signal.price_after_4h = Decimal(str(current_price))

        # 24시간 경과했지만 아직 평가 완료되지 않은 신호 평가
        stmt_24h = (
            select(TradingSignal)
            .where(
                and_(
                    TradingSignal.created_at < cutoff_24h,
                    TradingSignal.price_at_signal.isnot(None),
                    TradingSignal.outcome_evaluated.is_(False),
                )
            )
            .limit(100)
        )

        result_24h = await self.db.execute(stmt_24h)
        signals_24h = list(result_24h.scalars().all())

        evaluated_count = 0

        for signal in signals_24h:
            signal.price_after_24h = Decimal(str(current_price))

            # 정확성 평가
            if signal.price_at_signal and signal.price_after_24h:
                price_change = float(signal.price_after_24h) - float(
                    signal.price_at_signal
                )

                if signal.signal_type == SignalType.BUY.value:
                    signal.outcome_correct = price_change > 0
                elif signal.signal_type == SignalType.SELL.value:
                    signal.outcome_correct = price_change < 0
                else:  # HOLD
                    # HOLD는 가격 변동이 작을 때 정확
                    pct_change = abs(price_change / float(signal.price_at_signal) * 100)
                    signal.outcome_correct = pct_change < 3.0  # 3% 미만 변동

            signal.outcome_evaluated = True
            evaluated_count += 1

        await self.db.commit()

        logger.info(
            f"신호 성과 평가 완료: 4시간 가격 업데이트 {len(signals_4h)}건, "
            f"최종 평가 {evaluated_count}건"
        )

        return evaluated_count

    async def get_evaluated_signals(
        self,
        limit: int = 50,
        hours: int = 168,  # 1주일
    ) -> list[SignalOutcome]:
        """
        평가 완료된 신호 조회

        Args:
            limit: 최대 조회 수
            hours: 조회 기간 (시간)

        Returns:
            list[SignalOutcome]: 신호 성과 목록
        """
        since = datetime.now(UTC) - timedelta(hours=hours)

        stmt = (
            select(TradingSignal)
            .where(
                and_(
                    TradingSignal.outcome_evaluated.is_(True),
                    TradingSignal.created_at > since,
                )
            )
            .order_by(TradingSignal.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        signals = list(result.scalars().all())

        outcomes: list[SignalOutcome] = []

        for sig in signals:
            # 수익률 계산
            pnl_4h = None
            pnl_24h = None

            if sig.price_at_signal and sig.price_after_4h:
                pnl_4h = (
                    (float(sig.price_after_4h) - float(sig.price_at_signal))
                    / float(sig.price_at_signal)
                    * 100
                )

            if sig.price_at_signal and sig.price_after_24h:
                pnl_24h = (
                    (float(sig.price_after_24h) - float(sig.price_at_signal))
                    / float(sig.price_at_signal)
                    * 100
                )

            outcomes.append(
                SignalOutcome(
                    signal_id=sig.id,
                    signal_type=sig.signal_type,
                    confidence=float(sig.confidence),
                    price_at_signal=float(sig.price_at_signal)
                    if sig.price_at_signal
                    else 0,
                    price_after_4h=float(sig.price_after_4h)
                    if sig.price_after_4h
                    else None,
                    price_after_24h=float(sig.price_after_24h)
                    if sig.price_after_24h
                    else None,
                    pnl_percent_4h=round(pnl_4h, 2) if pnl_4h is not None else None,
                    pnl_percent_24h=round(pnl_24h, 2) if pnl_24h is not None else None,
                    was_correct=sig.outcome_correct,
                    created_at=sig.created_at,
                )
            )

        return outcomes

    def _calculate_accuracy(
        self,
        outcomes: list[SignalOutcome],
        signal_type: str,
    ) -> float:
        """
        특정 신호 타입의 정확도 계산

        Args:
            outcomes: 신호 성과 목록
            signal_type: 신호 타입

        Returns:
            float: 정확도 (%)
        """
        filtered = [o for o in outcomes if o.signal_type == signal_type]
        if not filtered:
            return 0.0

        correct = sum(1 for o in filtered if o.was_correct is True)
        return round((correct / len(filtered)) * 100, 1)

    def generate_verbal_feedback(
        self,
        outcomes: list[SignalOutcome],
    ) -> str:
        """
        Verbal Feedback 생성

        Multi-Agent Bitcoin Trading System의 verbal feedback 메커니즘 적용.
        과거 성과를 자연어로 요약하여 AI가 학습할 수 있도록 합니다.

        Args:
            outcomes: 신호 성과 목록

        Returns:
            str: 피드백 요약 (한국어)
        """
        if not outcomes:
            return "이전 신호 성과 데이터가 없습니다."

        feedback_parts: list[str] = []

        # 신호 타입별 분류
        buy_outcomes = [o for o in outcomes if o.signal_type == SignalType.BUY.value]
        sell_outcomes = [o for o in outcomes if o.signal_type == SignalType.SELL.value]

        # 매수 신호 피드백
        if buy_outcomes:
            correct_buys = [o for o in buy_outcomes if o.was_correct is True]
            wrong_buys = [o for o in buy_outcomes if o.was_correct is False]

            if correct_buys:
                avg_pnl = sum(
                    o.pnl_percent_24h for o in correct_buys if o.pnl_percent_24h
                ) / len(correct_buys)
                feedback_parts.append(
                    f"성공한 매수 신호 {len(correct_buys)}건 (평균 수익 {avg_pnl:.1f}%)"
                )

            if wrong_buys:
                avg_loss = sum(
                    o.pnl_percent_24h for o in wrong_buys if o.pnl_percent_24h
                ) / len(wrong_buys)
                feedback_parts.append(
                    f"실패한 매수 신호 {len(wrong_buys)}건 (평균 손실 {avg_loss:.1f}%)"
                )

        # 매도 신호 피드백
        if sell_outcomes:
            correct_sells = [o for o in sell_outcomes if o.was_correct is True]
            wrong_sells = [o for o in sell_outcomes if o.was_correct is False]

            if correct_sells:
                feedback_parts.append(f"성공한 매도 신호 {len(correct_sells)}건")

            if wrong_sells:
                feedback_parts.append(
                    f"실패한 매도 신호 {len(wrong_sells)}건 - 매도 타이밍 재검토 필요"
                )

        # 패턴 인식
        recent_5 = outcomes[:5]
        if len(recent_5) >= 5:
            recent_types = [o.signal_type for o in recent_5]
            if all(t == SignalType.HOLD.value for t in recent_types):
                feedback_parts.append(
                    "최근 5개 신호가 모두 HOLD - 명확한 추세 형성 시 적극적 신호 고려"
                )
            elif recent_types.count(SignalType.BUY.value) >= 4:
                feedback_parts.append("최근 매수 신호 빈발 - 과매수 가능성 고려 필요")
            elif recent_types.count(SignalType.SELL.value) >= 4:
                feedback_parts.append("최근 매도 신호 빈발 - 과매도 가능성 고려 필요")

        # 신뢰도 vs 정확도 상관관계
        high_conf_outcomes = [o for o in outcomes if o.confidence >= 0.7]
        if high_conf_outcomes:
            high_conf_correct = sum(
                1 for o in high_conf_outcomes if o.was_correct is True
            )
            high_conf_accuracy = (high_conf_correct / len(high_conf_outcomes)) * 100
            if high_conf_accuracy < 50:
                feedback_parts.append(
                    f"높은 신뢰도 신호 정확도 {high_conf_accuracy:.0f}% - 신뢰도 보정 필요"
                )

        return " | ".join(feedback_parts) if feedback_parts else "특이 패턴 없음"

    def generate_improvement_suggestions(
        self,
        outcomes: list[SignalOutcome],
    ) -> list[str]:
        """
        개선 제안 생성

        Args:
            outcomes: 신호 성과 목록

        Returns:
            list[str]: 개선 제안 목록
        """
        suggestions: list[str] = []

        if not outcomes:
            return ["충분한 성과 데이터가 없습니다. 더 많은 신호 생성 후 재평가하세요."]

        buy_outcomes = [o for o in outcomes if o.signal_type == SignalType.BUY.value]
        sell_outcomes = [o for o in outcomes if o.signal_type == SignalType.SELL.value]

        # 매수 정확도 분석
        if buy_outcomes:
            buy_accuracy = self._calculate_accuracy(outcomes, SignalType.BUY.value)
            if buy_accuracy < 50:
                suggestions.append(
                    f"매수 정확도 {buy_accuracy:.1f}%로 낮음. "
                    "RSI 과매도 + MACD 골든크로스 조건 강화 권장"
                )

        # 매도 정확도 분석
        if sell_outcomes:
            sell_accuracy = self._calculate_accuracy(outcomes, SignalType.SELL.value)
            if sell_accuracy < 50:
                suggestions.append(
                    f"매도 정확도 {sell_accuracy:.1f}%로 낮음. "
                    "RSI 과매수 + 볼린저밴드 상단 조건 강화 권장"
                )

        # 변동성 대응
        high_volatility_losses = [
            o
            for o in outcomes
            if o.was_correct is False
            and o.pnl_percent_24h
            and abs(o.pnl_percent_24h) > 5
        ]
        if len(high_volatility_losses) > 3:
            suggestions.append(
                "고변동성 구간에서 손실 빈발. ATR 기반 진입 시점 조정 권장"
            )

        # 연속 실패 패턴
        consecutive_fails = 0
        for o in outcomes[:10]:
            if o.was_correct is False:
                consecutive_fails += 1
            else:
                break

        if consecutive_fails >= 3:
            suggestions.append(
                f"최근 {consecutive_fails}회 연속 오류. 시장 환경 변화 가능성 - 보수적 접근 권장"
            )

        return suggestions if suggestions else ["현재 성과 양호. 기존 전략 유지"]

    async def generate_performance_summary(
        self,
        limit: int = 50,
        hours: int = 168,
    ) -> PerformanceSummary:
        """
        종합 성과 요약 생성

        Args:
            limit: 분석할 신호 수
            hours: 분석 기간 (시간)

        Returns:
            PerformanceSummary: 성과 요약
        """
        outcomes = await self.get_evaluated_signals(limit, hours)

        if not outcomes:
            return PerformanceSummary(
                feedback_summary="평가된 신호가 없습니다.",
                improvement_suggestions=["신호 생성 후 최소 24시간 대기 필요"],
            )

        # 기본 통계
        buy_count = sum(1 for o in outcomes if o.signal_type == SignalType.BUY.value)
        sell_count = sum(1 for o in outcomes if o.signal_type == SignalType.SELL.value)
        hold_count = sum(1 for o in outcomes if o.signal_type == SignalType.HOLD.value)

        # 정확도
        buy_accuracy = self._calculate_accuracy(outcomes, SignalType.BUY.value)
        sell_accuracy = self._calculate_accuracy(outcomes, SignalType.SELL.value)

        # 평균 신뢰도
        avg_confidence = sum(o.confidence for o in outcomes) / len(outcomes)

        # 평균 수익률
        pnl_4h_list = [
            o.pnl_percent_4h for o in outcomes if o.pnl_percent_4h is not None
        ]
        pnl_24h_list = [
            o.pnl_percent_24h for o in outcomes if o.pnl_percent_24h is not None
        ]

        avg_pnl_4h = sum(pnl_4h_list) / len(pnl_4h_list) if pnl_4h_list else 0.0
        avg_pnl_24h = sum(pnl_24h_list) / len(pnl_24h_list) if pnl_24h_list else 0.0

        # 피드백 및 제안
        feedback_summary = self.generate_verbal_feedback(outcomes)
        improvement_suggestions = self.generate_improvement_suggestions(outcomes)

        # 최근 패턴
        recent_patterns: list[str] = []
        recent_5 = outcomes[:5]
        if recent_5:
            types_count = {}
            for o in recent_5:
                types_count[o.signal_type] = types_count.get(o.signal_type, 0) + 1

            dominant_type = max(types_count.items(), key=lambda x: x[1])
            if dominant_type[1] >= 3:
                recent_patterns.append(
                    f"최근 {dominant_type[0]} 신호 우세 ({dominant_type[1]}/5)"
                )

        return PerformanceSummary(
            total_signals=len(outcomes),
            buy_signals=buy_count,
            sell_signals=sell_count,
            hold_signals=hold_count,
            buy_accuracy=buy_accuracy,
            sell_accuracy=sell_accuracy,
            avg_confidence=round(avg_confidence, 2),
            avg_pnl_4h=round(avg_pnl_4h, 2),
            avg_pnl_24h=round(avg_pnl_24h, 2),
            feedback_summary=feedback_summary,
            improvement_suggestions=improvement_suggestions,
            recent_patterns=recent_patterns,
        )
