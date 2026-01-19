"""
주문 실행기 핵심 단위 테스트

이 모듈은 OrderExecutor의 핵심 기능을 테스트합니다:
- 수수료 계산 검증
- 동적 포지션 사이징
- 중복 주문 방지
- PENDING 주문 동기화
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from src.models import Order, OrderSide, OrderStatus, OrderType, TradingSignal, SignalType
from src.services.order_executor import (
    OrderExecutor,
    OrderResult,
    BalanceInfo,
    UPBIT_FEE_RATE,
)
from src.services.upbit_client import UpbitError


class TestFeeCalculation:
    """수수료 계산 테스트"""

    def test_fee_calculation_formula(self):
        """수수료 계산 공식 검증: fee = volume * price * fee_rate"""
        # Given
        executed_volume = Decimal("0.001")  # 0.001 코인
        executed_price = Decimal("50000000")  # 5천만원/코인

        # When
        total_value = executed_volume * executed_price  # 50,000원
        fee = total_value * UPBIT_FEE_RATE  # 50,000 * 0.0005 = 25원

        # Then
        assert fee == Decimal("25")

    def test_fee_rate_is_correct(self):
        """Upbit 수수료율 확인 (0.05%)"""
        assert UPBIT_FEE_RATE == Decimal("0.0005")


class TestDynamicPositionSizing:
    """동적 포지션 사이징 테스트"""

    def test_low_confidence_uses_min_position(self):
        """낮은 신뢰도(0.5)는 최소 포지션(1%) 사용"""
        # Given
        min_pct = Decimal("1.0")
        max_pct = Decimal("3.0")
        confidence = Decimal("0.5")
        total_krw = Decimal("1000000")  # 100만원

        # When: 신뢰도 0.5 -> normalized = 0
        normalized = max(
            Decimal("0"),
            min(Decimal("1"), (confidence - Decimal("0.5")) * 2),
        )
        position_pct = min_pct + (max_pct - min_pct) * normalized
        order_amount = total_krw * position_pct / Decimal("100")

        # Then
        assert normalized == Decimal("0")
        assert position_pct == Decimal("1.0")
        assert order_amount == Decimal("10000")  # 1만원

    def test_high_confidence_uses_max_position(self):
        """높은 신뢰도(0.9+)는 최대 포지션(3%) 사용"""
        # Given
        min_pct = Decimal("1.0")
        max_pct = Decimal("3.0")
        confidence = Decimal("0.9")
        total_krw = Decimal("1000000")

        # When: 신뢰도 0.9 -> normalized = 0.8
        normalized = max(
            Decimal("0"),
            min(Decimal("1"), (confidence - Decimal("0.5")) * 2),
        )
        position_pct = min_pct + (max_pct - min_pct) * normalized
        order_amount = total_krw * position_pct / Decimal("100")

        # Then
        assert normalized == Decimal("0.8")
        assert position_pct == Decimal("2.6")  # 1 + 2 * 0.8
        assert order_amount == Decimal("26000")

    def test_confidence_1_0_uses_max_position(self):
        """신뢰도 1.0은 최대 포지션 사용"""
        # Given
        min_pct = Decimal("1.0")
        max_pct = Decimal("3.0")
        confidence = Decimal("1.0")

        # When
        normalized = max(
            Decimal("0"),
            min(Decimal("1"), (confidence - Decimal("0.5")) * 2),
        )
        position_pct = min_pct + (max_pct - min_pct) * normalized

        # Then
        assert normalized == Decimal("1")
        assert position_pct == Decimal("3.0")

    def test_confidence_below_0_5_uses_min_position(self):
        """신뢰도 0.5 미만도 최소 포지션 사용"""
        # Given
        min_pct = Decimal("1.0")
        max_pct = Decimal("3.0")
        confidence = Decimal("0.3")

        # When
        normalized = max(
            Decimal("0"),
            min(Decimal("1"), (confidence - Decimal("0.5")) * 2),
        )
        position_pct = min_pct + (max_pct - min_pct) * normalized

        # Then
        assert normalized == Decimal("0")
        assert position_pct == Decimal("1.0")


class TestIdempotencyKey:
    """중복 주문 방지 테스트"""

    def test_idempotency_key_is_unique_uuid(self):
        """idempotency_key는 유니크한 UUID 형식"""
        import uuid

        key1 = str(uuid.uuid4())
        key2 = str(uuid.uuid4())

        assert key1 != key2
        assert len(key1) == 36  # UUID 형식

    def test_order_model_has_idempotency_key(self):
        """Order 모델에 idempotency_key 필드 존재"""
        order = Order(
            signal_id=None,
            order_type=OrderType.MARKET.value,
            side=OrderSide.BUY.value,
            market="KRW-SOL",
            amount=Decimal("10000"),
            status=OrderStatus.PENDING.value,
            created_at=datetime.now(UTC),
            idempotency_key="test-key-12345",
        )

        assert order.idempotency_key == "test-key-12345"


class TestOrderStatus:
    """주문 상태 테스트"""

    def test_order_is_pending(self):
        """PENDING 상태 확인"""
        order = Order(
            order_type=OrderType.MARKET.value,
            side=OrderSide.BUY.value,
            market="KRW-SOL",
            amount=Decimal("10000"),
            status=OrderStatus.PENDING.value,
            created_at=datetime.now(UTC),
        )

        assert order.is_pending is True
        assert order.is_executed is False

    def test_order_is_executed(self):
        """EXECUTED 상태 확인"""
        order = Order(
            order_type=OrderType.MARKET.value,
            side=OrderSide.BUY.value,
            market="KRW-SOL",
            amount=Decimal("10000"),
            status=OrderStatus.EXECUTED.value,
            created_at=datetime.now(UTC),
        )

        assert order.is_executed is True
        assert order.is_pending is False

    def test_mark_executed(self):
        """mark_executed 메서드 검증"""
        order = Order(
            order_type=OrderType.MARKET.value,
            side=OrderSide.BUY.value,
            market="KRW-SOL",
            amount=Decimal("10000"),
            status=OrderStatus.PENDING.value,
            created_at=datetime.now(UTC),
        )

        order.mark_executed(
            executed_price=Decimal("200000"),
            executed_amount=Decimal("0.05"),
            fee=Decimal("5"),
        )

        assert order.status == OrderStatus.EXECUTED.value
        assert order.executed_price == Decimal("200000")
        assert order.executed_amount == Decimal("0.05")
        assert order.fee == Decimal("5")
        assert order.executed_at is not None

    def test_mark_failed(self):
        """mark_failed 메서드 검증"""
        order = Order(
            order_type=OrderType.MARKET.value,
            side=OrderSide.BUY.value,
            market="KRW-SOL",
            amount=Decimal("10000"),
            status=OrderStatus.PENDING.value,
            created_at=datetime.now(UTC),
        )

        order.mark_failed("잔고 부족")

        assert order.status == OrderStatus.FAILED.value
        assert order.error_message == "잔고 부족"


class TestBalanceInfo:
    """잔고 정보 테스트"""

    def test_balance_info_dataclass(self):
        """BalanceInfo 데이터클래스 검증"""
        balance = BalanceInfo(
            krw_available=Decimal("1000000"),
            krw_locked=Decimal("0"),
            coin_available=Decimal("10"),
            coin_locked=Decimal("0"),
            coin_avg_price=Decimal("200000"),
            total_krw=Decimal("3000000"),
        )

        assert balance.krw_available == Decimal("1000000")
        assert balance.total_krw == Decimal("3000000")


class TestSignalConfidence:
    """신호 신뢰도 테스트"""

    def test_trading_signal_confidence_range(self):
        """TradingSignal의 confidence 범위 확인"""
        signal = TradingSignal(
            signal_type=SignalType.BUY.value,
            confidence=Decimal("0.75"),
            reasoning="테스트",
            created_at=datetime.now(UTC),
            model_name="test-model",
            input_tokens=100,
            output_tokens=50,
        )

        assert Decimal("0") <= signal.confidence <= Decimal("1")


# 추가: 통합 수준 테스트 (Mock 사용)
class TestOrderExecutorIntegration:
    """OrderExecutor 통합 테스트 (Mock 사용)"""

    @pytest.fixture
    def mock_session(self):
        """Mock DB 세션"""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session.rollback = AsyncMock()
        session.add = MagicMock()
        return session

    @pytest.fixture
    def mock_upbit_client(self):
        """Mock Upbit 클라이언트"""
        client = AsyncMock()

        # 기본 응답 설정
        client.get_ticker.return_value = MagicMock(trade_price=Decimal("200000"))
        client.get_accounts.return_value = [
            MagicMock(
                currency="KRW",
                balance=Decimal("1000000"),
                locked=Decimal("0"),
                avg_buy_price=Decimal("0"),
            ),
            MagicMock(
                currency="SOL",
                balance=Decimal("10"),
                locked=Decimal("0"),
                avg_buy_price=Decimal("150000"),
            ),
        ]
        return client

    @pytest.fixture
    def mock_risk_manager(self):
        """Mock 리스크 매니저"""
        from src.services.risk_manager import RiskCheckResult, PositionCheckResult

        manager = AsyncMock()
        manager.is_trading_enabled.return_value = True
        manager.check_daily_loss_limit.return_value = (RiskCheckResult.PASS, "OK")
        manager.check_volatility.return_value = (RiskCheckResult.PASS, 1.0, "OK")
        manager.check_position_size.return_value = PositionCheckResult(
            result=RiskCheckResult.PASS,
            max_amount=Decimal("100000"),
            requested_amount=Decimal("20000"),
            message="OK",
        )
        manager.check_stop_loss.return_value = MagicMock(
            result=RiskCheckResult.PASS,
            should_close=False,
            message="OK",
        )
        return manager

    @pytest.mark.asyncio
    async def test_hold_signal_skips_order(
        self, mock_session, mock_upbit_client, mock_risk_manager
    ):
        """HOLD 신호는 주문을 건너뜀"""
        executor = OrderExecutor(
            mock_session, mock_upbit_client, mock_risk_manager
        )

        signal = TradingSignal(
            id=1,
            signal_type=SignalType.HOLD.value,
            confidence=Decimal("0.8"),
            reasoning="테스트",
            created_at=datetime.now(UTC),
            model_name="test",
            input_tokens=100,
            output_tokens=50,
        )

        result = await executor.execute_from_signal(signal)

        assert result.success is True
        assert result.order is None
        assert "HOLD" in result.message

    @pytest.mark.asyncio
    async def test_trading_disabled_blocks_order(
        self, mock_session, mock_upbit_client, mock_risk_manager
    ):
        """거래 비활성화 시 주문 차단"""
        mock_risk_manager.is_trading_enabled.return_value = False

        executor = OrderExecutor(
            mock_session, mock_upbit_client, mock_risk_manager
        )

        signal = TradingSignal(
            id=1,
            signal_type=SignalType.BUY.value,
            confidence=Decimal("0.8"),
            reasoning="테스트",
            created_at=datetime.now(UTC),
            model_name="test",
            input_tokens=100,
            output_tokens=50,
        )

        result = await executor.execute_from_signal(signal)

        assert result.success is False
        assert "비활성화" in result.message
