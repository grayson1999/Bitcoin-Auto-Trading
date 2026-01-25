"""
주문 검증 모듈

이 모듈은 주문 실행 전 검증 로직을 담당합니다.
- 리스크 사전 체크
- 잔고 검증
- 포지션 크기 검증
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from loguru import logger

from src.clients.upbit import (
    UpbitPrivateAPI,
    UpbitPrivateAPIError,
    UpbitPublicAPI,
    UpbitPublicAPIError,
)
from src.config import settings
from src.config.constants import UPBIT_MIN_ORDER_KRW
from src.entities import Position, SignalType, TradingSignal
from src.modules.risk.service import RiskCheckResult, RiskService

# 상수를 Decimal로 변환
MIN_ORDER_AMOUNT_KRW = Decimal(str(UPBIT_MIN_ORDER_KRW))


class OrderBlockedReason(str, Enum):
    """주문 차단 사유"""

    TRADING_DISABLED = "TRADING_DISABLED"
    DAILY_LIMIT_REACHED = "DAILY_LIMIT_REACHED"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    POSITION_SIZE_EXCEEDED = "POSITION_SIZE_EXCEEDED"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"
    STOP_LOSS_TRIGGERED = "STOP_LOSS_TRIGGERED"
    RISK_CHECK_FAILED = "RISK_CHECK_FAILED"


@dataclass
class BalanceInfo:
    """잔고 정보 (동적 코인 지원)"""

    krw_available: Decimal
    krw_locked: Decimal
    coin_available: Decimal  # 보유 코인 수량
    coin_locked: Decimal  # 잠긴 코인 수량
    coin_avg_price: Decimal  # 평균 매수가
    total_krw: Decimal  # 총 평가금액


@dataclass
class ValidationResult:
    """주문 검증 결과"""

    is_valid: bool
    blocked_reason: OrderBlockedReason | None = None
    message: str = ""
    order_amount: Decimal | None = None  # 계산된 주문 금액


class OrderValidator:
    """
    주문 검증 서비스

    주문 실행 전 리스크 체크 및 잔고 검증을 수행합니다.
    """

    def __init__(
        self,
        private_api: UpbitPrivateAPI,
        public_api: UpbitPublicAPI,
        risk_service: RiskService,
    ) -> None:
        """
        OrderValidator 초기화

        Args:
            private_api: Upbit Private API 클라이언트
            public_api: Upbit Public API 클라이언트
            risk_service: 리스크 관리 서비스
        """
        self._private_api = private_api
        self._public_api = public_api
        self._risk_service = risk_service

    async def validate_signal(
        self,
        signal: TradingSignal,
    ) -> tuple[ValidationResult, BalanceInfo | None]:
        """
        신호 기반 주문 검증

        Args:
            signal: AI 매매 신호

        Returns:
            tuple[ValidationResult, BalanceInfo | None]: (검증 결과, 잔고 정보)
        """
        # HOLD 신호는 주문 실행하지 않음
        if signal.signal_type == SignalType.HOLD.value:
            logger.info("HOLD 신호 - 주문 실행 건너뜀")
            return (
                ValidationResult(
                    is_valid=True,
                    message="HOLD 신호 - 주문 없음",
                ),
                None,
            )

        # 1. 거래 활성화 상태 확인
        if not await self._risk_service.is_trading_enabled():
            logger.warning("거래 비활성화 상태 - 주문 실행 불가")
            return (
                ValidationResult(
                    is_valid=False,
                    blocked_reason=OrderBlockedReason.TRADING_DISABLED,
                    message="거래가 비활성화되어 있습니다",
                ),
                None,
            )

        # 2. 일일 손실 한도 체크
        daily_result, daily_msg = await self._risk_service.check_daily_loss_limit()
        if daily_result == RiskCheckResult.BLOCKED:
            logger.warning(f"일일 손실 한도 도달: {daily_msg}")
            return (
                ValidationResult(
                    is_valid=False,
                    blocked_reason=OrderBlockedReason.DAILY_LIMIT_REACHED,
                    message=daily_msg,
                ),
                None,
            )

        # 3. 변동성 체크
        vol_result, _vol_pct, vol_msg = await self._risk_service.check_volatility()
        if vol_result == RiskCheckResult.BLOCKED:
            logger.warning(f"고변동성 감지: {vol_msg}")
            return (
                ValidationResult(
                    is_valid=False,
                    blocked_reason=OrderBlockedReason.HIGH_VOLATILITY,
                    message=vol_msg,
                ),
                None,
            )

        # 4. 잔고 조회
        try:
            balance_info = await self._get_balance_info()
        except (UpbitPrivateAPIError, UpbitPublicAPIError) as e:
            logger.error(f"잔고 조회 실패: {e.message}")
            return (
                ValidationResult(
                    is_valid=False,
                    message=f"잔고 조회 실패: {e.message}",
                ),
                None,
            )

        return (
            ValidationResult(is_valid=True, message="검증 통과"),
            balance_info,
        )

    async def validate_buy_order(
        self,
        signal: TradingSignal,
        balance_info: BalanceInfo,
    ) -> ValidationResult:
        """
        매수 주문 검증

        Args:
            signal: AI 매매 신호
            balance_info: 잔고 정보

        Returns:
            ValidationResult: 검증 결과
        """
        # 동적 포지션 사이징: AI 신뢰도에 따라 min~max 범위에서 계산
        min_pct = Decimal(str(settings.position_size_min_pct))
        max_pct = Decimal(str(settings.position_size_max_pct))

        # 신뢰도 0.5 -> min_pct, 신뢰도 0.9+ -> max_pct
        confidence = signal.confidence
        # 0.5~1.0 범위를 0~1로 정규화
        normalized = max(
            Decimal("0"),
            min(Decimal("1"), (confidence - Decimal("0.5")) * 2),
        )

        position_pct = min_pct + (max_pct - min_pct) * normalized
        order_amount = balance_info.krw_available * position_pct / Decimal("100")

        logger.info(
            f"동적 포지션: confidence={confidence}, "
            f"pct={position_pct:.2f}%, krw_available={balance_info.krw_available:,.0f}원, "
            f"amount={order_amount:,.0f}원"
        )

        # 최소 주문 금액 확인
        if order_amount < MIN_ORDER_AMOUNT_KRW:
            logger.warning(
                f"주문 금액 부족: {order_amount:,.0f}원 < {MIN_ORDER_AMOUNT_KRW:,.0f}원"
            )
            return ValidationResult(
                is_valid=False,
                blocked_reason=OrderBlockedReason.INSUFFICIENT_BALANCE,
                message=f"주문 금액 부족: {order_amount:,.0f}원",
            )

        # 가용 잔고 확인
        if order_amount > balance_info.krw_available:
            order_amount = balance_info.krw_available
            logger.info(f"가용 잔고로 주문 금액 조정: {order_amount:,.0f}원")

        if order_amount < MIN_ORDER_AMOUNT_KRW:
            logger.warning(f"가용 잔고 부족: {balance_info.krw_available:,.0f}원")
            return ValidationResult(
                is_valid=False,
                blocked_reason=OrderBlockedReason.INSUFFICIENT_BALANCE,
                message=f"가용 잔고 부족: {balance_info.krw_available:,.0f}원",
            )
        # 포지션 크기 검증
        pos_result = await self._risk_service.check_position_size(
            order_amount, balance_info.total_krw
        )
        if pos_result.result == RiskCheckResult.BLOCKED:
            logger.warning(f"포지션 크기 초과: {pos_result.message}")
            return ValidationResult(
                is_valid=False,
                blocked_reason=OrderBlockedReason.POSITION_SIZE_EXCEEDED,
                message=pos_result.message,
            )

        return ValidationResult(
            is_valid=True,
            message="매수 주문 검증 통과",
            order_amount=order_amount,
        )

    async def validate_sell_order(
        self,
        signal: TradingSignal,
        balance_info: BalanceInfo,
        position: Position | None,
    ) -> ValidationResult:
        """
        매도 주문 검증

        Args:
            signal: AI 매매 신호
            balance_info: 잔고 정보
            position: 현재 포지션

        Returns:
            ValidationResult: 검증 결과
        """
        # 보유 코인 확인
        if balance_info.coin_available <= 0:
            logger.warning(f"보유 {settings.trading_currency} 없음 - 매도 불가")
            return ValidationResult(
                is_valid=False,
                blocked_reason=OrderBlockedReason.INSUFFICIENT_BALANCE,
                message=f"보유 {settings.trading_currency}가 없습니다",
            )

        # 포지션 정보 확인
        if position is None:
            logger.warning("포지션 정보 없음")
            return ValidationResult(
                is_valid=False,
                message="포지션 정보가 없습니다",
            )

        # 현재가 조회
        try:
            ticker = await self._public_api.get_ticker(settings.trading_ticker)
            current_price = ticker.trade_price
        except UpbitPublicAPIError as e:
            logger.error(f"현재가 조회 실패: {e.message}")
            return ValidationResult(
                is_valid=False,
                message=f"현재가 조회 실패: {e.message}",
            )

        # 손절 체크
        stop_loss_result = await self._risk_service.check_stop_loss(
            position, current_price
        )
        if stop_loss_result.result == RiskCheckResult.BLOCKED:
            logger.warning(f"손절 발동: {stop_loss_result.message}")
            # 손절 시에도 매도 진행 (should_close=True인 경우)
            if not stop_loss_result.should_close:
                return ValidationResult(
                    is_valid=False,
                    blocked_reason=OrderBlockedReason.STOP_LOSS_TRIGGERED,
                    message=stop_loss_result.message,
                )

        return ValidationResult(
            is_valid=True,
            message="매도 주문 검증 통과",
            order_amount=balance_info.coin_available,
        )

    async def get_balance_info(self) -> BalanceInfo:
        """
        Upbit 계좌 잔고 조회 (public 접근용)

        Returns:
            BalanceInfo: 잔고 정보
        """
        return await self._get_balance_info()

    async def _get_balance_info(self) -> BalanceInfo:
        """
        Upbit 계좌 잔고 조회

        Returns:
            BalanceInfo: 잔고 정보
        """
        accounts = await self._private_api.get_accounts()

        krw_available = Decimal("0")
        krw_locked = Decimal("0")
        coin_available = Decimal("0")
        coin_locked = Decimal("0")
        coin_avg_price = Decimal("0")

        for acc in accounts:
            if acc.currency == "KRW":
                krw_available = acc.balance
                krw_locked = acc.locked
            elif acc.currency == settings.trading_currency:
                coin_available = acc.balance
                coin_locked = acc.locked
                coin_avg_price = acc.avg_buy_price

        # 현재가 조회
        try:
            ticker = await self._public_api.get_ticker(settings.trading_ticker)
            current_price = ticker.trade_price
        except UpbitPublicAPIError:
            current_price = coin_avg_price  # 조회 실패 시 평균 매수가 사용

        # 총 평가금액 계산
        coin_value = (coin_available + coin_locked) * current_price
        total_krw = krw_available + krw_locked + coin_value

        return BalanceInfo(
            krw_available=krw_available,
            krw_locked=krw_locked,
            coin_available=coin_available,
            coin_locked=coin_locked,
            coin_avg_price=coin_avg_price,
            total_krw=total_krw,
        )
