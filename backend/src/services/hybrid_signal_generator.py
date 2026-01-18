"""
하이브리드 신호 생성 서비스

AI 신호와 변동성 돌파 전략을 결합한 하이브리드 매매 신호를 생성합니다.

진입 규칙:
- BUY: AI BUY 신호 AND 변동성 돌파 조건 충족
- SELL: AI SELL 신호 (손절/익절은 AI 로직에 포함)
- HOLD: 그 외 모든 경우

K값 가이드:
- 횡보장: 0.6~0.7 (보수적)
- 상승장: 0.5~0.6 (공격적)
- 하락장: 0.7~0.8 (방어적)
"""

from dataclasses import dataclass

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import TradingSignal
from src.models.trading_signal import SignalType
from src.services.signal_generator import SignalGenerator, get_signal_generator
from src.services.volatility_breakout import (
    BreakoutCalculationError,
    BreakoutResult,
    VolatilityBreakoutStrategy,
    get_volatility_breakout_strategy,
)


@dataclass
class HybridSignalResult:
    """
    하이브리드 신호 생성 결과

    Attributes:
        final_signal: 최종 신호 (BUY/HOLD/SELL)
        ai_signal: AI 생성 신호 (TradingSignal 모델)
        breakout_result: 변동성 돌파 계산 결과 (없으면 None)
        hybrid_reasoning: 하이브리드 로직 적용 근거
        hybrid_mode_applied: 하이브리드 모드 적용 여부
    """

    final_signal: str
    ai_signal: TradingSignal
    breakout_result: BreakoutResult | None
    hybrid_reasoning: str
    hybrid_mode_applied: bool


class HybridSignalGenerator:
    """
    하이브리드 신호 생성기

    AI 신호 분석과 변동성 돌파 전략을 결합합니다.

    규칙:
    - BUY: AI BUY AND 돌파 조건 충족 (강도 >= 최소값)
    - SELL: AI SELL (리스크 관리 우선)
    - HOLD: 그 외 모든 경우

    사용 예시:
        generator = HybridSignalGenerator(db_session)
        result = await generator.generate_hybrid_signal()
        print(f"최종 신호: {result.final_signal}")
        print(f"AI 신호: {result.ai_signal.signal_type}")
        br = result.breakout_result
        print(f"돌파 여부: {br.is_breakout if br else 'N/A'}")
    """

    def __init__(
        self,
        db: AsyncSession,
        signal_generator: SignalGenerator | None = None,
        breakout_strategy: VolatilityBreakoutStrategy | None = None,
    ):
        """
        하이브리드 신호 생성기 초기화

        Args:
            db: SQLAlchemy 비동기 세션
            signal_generator: AI 신호 생성기 (None이면 기본 생성)
            breakout_strategy: 변동성 돌파 전략 (None이면 기본 생성)
        """
        self.db = db
        self.signal_generator = signal_generator or get_signal_generator(db)
        self.breakout_strategy = breakout_strategy or get_volatility_breakout_strategy()
        self.hybrid_enabled = settings.hybrid_mode_enabled
        self.min_breakout_strength = settings.breakout_min_strength

    async def generate_hybrid_signal(
        self,
        force: bool = False,
    ) -> HybridSignalResult:
        """
        하이브리드 신호 생성

        1. AI 신호 생성 (기존 SignalGenerator 호출)
        2. 변동성 돌파 조건 계산
        3. 하이브리드 로직 적용
        4. 결과 반환

        Args:
            force: 쿨다운 무시 여부 (스케줄러에서 호출 시 True)

        Returns:
            HybridSignalResult: 하이브리드 신호 결과

        Raises:
            SignalGeneratorError: AI 신호 생성 실패 시
        """
        # 1. AI 신호 생성
        ai_signal = await self.signal_generator.generate_signal(force=force)

        # 하이브리드 모드가 비활성화된 경우, AI 신호만 반환
        if not self.hybrid_enabled:
            logger.info(
                f"하이브리드 모드 비활성화: AI 신호만 사용 ({ai_signal.signal_type})"
            )
            return HybridSignalResult(
                final_signal=ai_signal.signal_type,
                ai_signal=ai_signal,
                breakout_result=None,
                hybrid_reasoning="하이브리드 모드 비활성화, AI 신호만 사용",
                hybrid_mode_applied=False,
            )

        # 2. 변동성 돌파 계산
        breakout_result: BreakoutResult | None = None
        try:
            breakout_result = await self.breakout_strategy.calculate_breakout()
        except BreakoutCalculationError as e:
            logger.warning(f"변동성 돌파 계산 실패: {e}")
            # 돌파 계산 실패 시 AI 신호만 사용
            return HybridSignalResult(
                final_signal=ai_signal.signal_type,
                ai_signal=ai_signal,
                breakout_result=None,
                hybrid_reasoning=f"돌파 계산 실패 ({e}), AI 신호만 사용",
                hybrid_mode_applied=False,
            )

        # 3. 하이브리드 로직 적용
        final_signal, reasoning = self._apply_hybrid_logic(
            ai_signal=ai_signal,
            breakout_result=breakout_result,
        )

        # 4. 신호가 변경된 경우 DB 업데이트
        if final_signal != ai_signal.signal_type:
            original_signal = ai_signal.signal_type
            ai_signal.signal_type = final_signal
            ai_signal.reasoning = f"{ai_signal.reasoning} | [Hybrid] {reasoning}"
            await self.db.commit()

            logger.info(
                f"하이브리드 신호 변경: {original_signal} -> {final_signal} | "
                f"AI 신뢰도={ai_signal.confidence:.2f} | "
                f"돌파={'YES' if breakout_result.is_breakout else 'NO'} "
                f"(강도={breakout_result.breakout_strength:.2f}%)"
            )
        else:
            logger.info(
                f"하이브리드 신호 유지: {final_signal} | "
                f"돌파={'YES' if breakout_result.is_breakout else 'NO'} "
                f"(강도={breakout_result.breakout_strength:.2f}%)"
            )

        return HybridSignalResult(
            final_signal=final_signal,
            ai_signal=ai_signal,
            breakout_result=breakout_result,
            hybrid_reasoning=reasoning,
            hybrid_mode_applied=True,
        )

    def _apply_hybrid_logic(
        self,
        ai_signal: TradingSignal,
        breakout_result: BreakoutResult,
    ) -> tuple[str, str]:
        """
        하이브리드 로직 적용

        규칙:
        1. SELL은 항상 우선 (리스크 관리)
        2. BUY는 AI BUY AND 돌파 조건 충족 시
        3. 그 외는 HOLD

        Args:
            ai_signal: AI 생성 신호
            breakout_result: 변동성 돌파 계산 결과

        Returns:
            tuple[str, str]: (최종 신호, 근거 설명)
        """
        ai_type = ai_signal.signal_type

        # SELL은 항상 우선 (손절/익절 로직이 AI에 포함됨)
        if ai_type == SignalType.SELL.value:
            return (
                SignalType.SELL.value,
                f"AI SELL 신호 우선 적용 (신뢰도: {ai_signal.confidence:.2f})",
            )

        # BUY는 AI + 돌파 조건 모두 충족 필요
        if ai_type == SignalType.BUY.value:
            strength = breakout_result.breakout_strength
            min_str = self.min_breakout_strength
            cur_price = breakout_result.current_price
            tgt_price = breakout_result.target_price

            if breakout_result.is_breakout:
                if strength >= min_str:
                    return (
                        SignalType.BUY.value,
                        f"AI BUY + 돌파 확인 (강도: {strength:.2f}% >= {min_str}%)",
                    )
                else:
                    return (
                        SignalType.HOLD.value,
                        f"AI BUY but 돌파 강도 부족 ({strength:.2f}% < {min_str}%)",
                    )
            else:
                return (
                    SignalType.HOLD.value,
                    f"AI BUY but 돌파 미충족 (현재: {cur_price:,.0f} < "
                    f"목표: {tgt_price:,.0f})",
                )

        # HOLD는 그대로 유지
        return (
            SignalType.HOLD.value,
            f"AI HOLD 신호 유지 (신뢰도: {ai_signal.confidence:.2f})",
        )

    def get_status(self) -> dict:
        """
        하이브리드 생성기 상태 조회

        Returns:
            dict: 현재 설정 상태
        """
        return {
            "hybrid_mode_enabled": self.hybrid_enabled,
            "k_value": self.breakout_strategy.k_value,
            "min_breakout_strength": self.min_breakout_strength,
            "ticker": settings.trading_ticker,
            "currency": settings.trading_currency,
        }


def get_hybrid_signal_generator(
    db: AsyncSession,
    signal_generator: SignalGenerator | None = None,
    breakout_strategy: VolatilityBreakoutStrategy | None = None,
) -> HybridSignalGenerator:
    """
    HybridSignalGenerator 인스턴스 생성 헬퍼

    Args:
        db: SQLAlchemy 비동기 세션
        signal_generator: AI 신호 생성기
        breakout_strategy: 변동성 돌파 전략

    Returns:
        HybridSignalGenerator: 하이브리드 신호 생성기 인스턴스
    """
    return HybridSignalGenerator(
        db=db,
        signal_generator=signal_generator,
        breakout_strategy=breakout_strategy,
    )
