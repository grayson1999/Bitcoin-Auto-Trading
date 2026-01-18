"""
변동성 돌파 전략 서비스

래리 윌리엄스의 변동성 돌파 전략을 구현합니다:
- 돌파 가격 = 당일 시가 + (전일 고가 - 전일 저가) × K
- 현재가 > 돌파 가격일 때 매수 신호

K값 가이드:
- 횡보장: 0.6~0.7 (보수적)
- 상승장: 0.5~0.6 (공격적)
- 하락장: 0.7~0.8 (방어적)
"""

from dataclasses import dataclass
from decimal import Decimal

from loguru import logger

from src.config import settings
from src.services.upbit_client import UpbitClient, get_upbit_client

# === 상수 ===
MIN_CANDLES_REQUIRED = 2  # 변동성 돌파 계산에 필요한 최소 캔들 수 (오늘 + 어제)


@dataclass
class BreakoutResult:
    """
    변동성 돌파 계산 결과

    Attributes:
        is_breakout: 돌파 조건 충족 여부
        target_price: 돌파 목표가
        current_price: 현재가
        opening_price: 당일 시가
        prev_high: 전일 고가
        prev_low: 전일 저가
        prev_range: 전일 변동폭 (고가 - 저가)
        k_value: 사용된 K 계수
        breakout_strength: 돌파 강도 (%) - (현재가 - 목표가) / 목표가 × 100
    """

    is_breakout: bool
    target_price: Decimal
    current_price: Decimal
    opening_price: Decimal
    prev_high: Decimal
    prev_low: Decimal
    prev_range: Decimal
    k_value: float
    breakout_strength: float


class BreakoutCalculationError(Exception):
    """변동성 돌파 계산 오류"""

    pass


class VolatilityBreakoutStrategy:
    """
    변동성 돌파 전략 계산기

    래리 윌리엄스의 변동성 돌파 전략을 기반으로 매수 신호를 생성합니다.

    Args:
        upbit_client: Upbit API 클라이언트 (None이면 기본 클라이언트 사용)
        k_value: K 계수 (None이면 설정값 사용, 기본 0.6)
    """

    def __init__(
        self,
        upbit_client: UpbitClient | None = None,
        k_value: float | None = None,
    ):
        self.upbit_client = upbit_client or get_upbit_client()
        self.k_value = k_value if k_value is not None else settings.volatility_k_value

    async def calculate_breakout(
        self,
        market: str | None = None,
    ) -> BreakoutResult:
        """
        변동성 돌파 조건 계산

        1. 전일 일봉에서 고가/저가 조회
        2. 당일 시가 조회
        3. 현재가 조회
        4. 돌파가격 = 시가 + (전일고가 - 전일저가) × K
        5. 현재가 > 돌파가격 → is_breakout = True

        Args:
            market: 마켓 코드 (예: KRW-SOL). None이면 설정값 사용

        Returns:
            BreakoutResult: 돌파 계산 결과

        Raises:
            BreakoutCalculationError: 계산에 필요한 데이터가 부족할 때
        """
        market = market or settings.trading_ticker

        try:
            # 일봉 캔들 조회 (최소 2개 필요: 오늘 + 어제)
            candles = await self.upbit_client.get_day_candles(
                market, count=MIN_CANDLES_REQUIRED
            )

            if len(candles) < MIN_CANDLES_REQUIRED:
                raise BreakoutCalculationError(
                    f"캔들 데이터 부족: {len(candles)}개 "
                    f"(최소 {MIN_CANDLES_REQUIRED}개 필요)"
                )

            # candles[0] = 오늘, candles[1] = 어제
            today_candle = candles[0]
            yesterday_candle = candles[1]

            # 전일 고가/저가
            prev_high = yesterday_candle.high_price
            prev_low = yesterday_candle.low_price
            prev_range = prev_high - prev_low

            # 당일 시가
            opening_price = today_candle.opening_price

            # 현재가 조회 (실시간 정확도를 위해 ticker 사용)
            ticker = await self.upbit_client.get_ticker(market)
            current_price = ticker.trade_price

            # 돌파 목표가 계산
            k_decimal = Decimal(str(self.k_value))
            target_price = opening_price + (prev_range * k_decimal)

            # 돌파 여부 판단
            is_breakout = current_price > target_price

            # 돌파 강도 계산 (%)
            if target_price > 0:
                breakout_strength = float(
                    (current_price - target_price) / target_price * 100
                )
            else:
                breakout_strength = 0.0

            result = BreakoutResult(
                is_breakout=is_breakout,
                target_price=target_price,
                current_price=current_price,
                opening_price=opening_price,
                prev_high=prev_high,
                prev_low=prev_low,
                prev_range=prev_range,
                k_value=self.k_value,
                breakout_strength=breakout_strength,
            )

            logger.debug(
                f"변동성 돌파 계산: {market} | "
                f"목표가={target_price:,.0f} | 현재가={current_price:,.0f} | "
                f"돌파={'YES' if is_breakout else 'NO'} | 강도={breakout_strength:.2f}%"
            )

            return result

        except BreakoutCalculationError:
            raise
        except Exception as e:
            logger.error(f"변동성 돌파 계산 오류: {e}")
            raise BreakoutCalculationError(f"계산 실패: {e}") from e

    def update_k_value(self, new_k: float) -> None:
        """
        K 계수 동적 업데이트

        Args:
            new_k: 새로운 K 계수 (0.1 ~ 1.0)

        Raises:
            ValueError: K 값이 유효 범위를 벗어날 때
        """
        if 0.1 <= new_k <= 1.0:
            old_k = self.k_value
            self.k_value = new_k
            logger.info(f"K 계수 업데이트: {old_k} -> {new_k}")
        else:
            raise ValueError(f"K 값은 0.1 ~ 1.0 범위여야 합니다: {new_k}")


def get_volatility_breakout_strategy(
    upbit_client: UpbitClient | None = None,
    k_value: float | None = None,
) -> VolatilityBreakoutStrategy:
    """
    VolatilityBreakoutStrategy 인스턴스 생성 헬퍼

    Args:
        upbit_client: Upbit API 클라이언트
        k_value: K 계수

    Returns:
        VolatilityBreakoutStrategy: 전략 인스턴스
    """
    return VolatilityBreakoutStrategy(
        upbit_client=upbit_client,
        k_value=k_value,
    )
