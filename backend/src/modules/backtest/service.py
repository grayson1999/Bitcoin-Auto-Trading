"""
백테스트 서비스 모듈

이 모듈은 과거 데이터로 AI 전략을 시뮬레이션하는 서비스를 제공합니다.
- 신호 시뮬레이션 (과거 데이터 기반)
- 성과 지표 계산 (수익률, MDD, 승률, 손익비, 샤프 비율)
- 거래 내역 기록
- Upbit 캔들 API 활용 (장기 백테스트 지원)
"""

from datetime import datetime
from decimal import Decimal

from loguru import logger
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.upbit import UpbitPublicAPI, get_upbit_public_api
from src.config import settings
from src.config.constants import (
    BACKTEST_CANDLE_FETCH_LIMIT,
    BACKTEST_DEFAULT_INITIAL_CAPITAL,
)
from src.entities import BacktestResult, BacktestStatus, TradingSignal
from src.modules.backtest.engine import BacktestEngine, BacktestState, CandlePriceData
from src.modules.backtest.reporter import BacktestReporter
from src.utils import UTC

# 상수를 Decimal로 변환
DEFAULT_INITIAL_CAPITAL = Decimal(str(BACKTEST_DEFAULT_INITIAL_CAPITAL))


class BacktestServiceError(Exception):
    """백테스트 서비스 오류"""

    pass


class BacktestService:
    """
    백테스트 서비스

    과거 시장 데이터와 AI 신호를 기반으로 전략 성과를 시뮬레이션합니다.

    사용 예시:
        service = BacktestService(db_session)
        result = await service.run_backtest(
            name="6개월 테스트",
            start_date=datetime(2024, 7, 1),
            end_date=datetime(2025, 1, 1),
            initial_capital=Decimal("1000000"),
        )
        print(f"수익률: {result.total_return_pct}%")
    """

    def __init__(self, db: AsyncSession, upbit_client: UpbitPublicAPI | None = None):
        """
        백테스트 서비스 초기화

        Args:
            db: SQLAlchemy 비동기 세션
            upbit_client: Upbit Public API 클라이언트 (없으면 자동 생성)
        """
        self.db = db
        self.upbit_client = upbit_client or get_upbit_public_api()
        self._engine = BacktestEngine()
        self._reporter = BacktestReporter()

    async def run_backtest(
        self,
        name: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: Decimal = DEFAULT_INITIAL_CAPITAL,
    ) -> BacktestResult:
        """
        백테스트 실행

        지정된 기간의 과거 데이터로 전략을 시뮬레이션하고 결과를 저장합니다.

        Args:
            name: 백테스트 이름
            start_date: 시작 날짜
            end_date: 종료 날짜
            initial_capital: 초기 자본금

        Returns:
            BacktestResult: 백테스트 결과

        Raises:
            BacktestServiceError: 실행 실패 시
        """
        logger.info(f"백테스트 시작: {name} ({start_date.date()} ~ {end_date.date()})")

        # 1. 결과 레코드 생성 (RUNNING 상태)
        result = BacktestResult(
            name=name,
            status=BacktestStatus.RUNNING.value,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            created_at=datetime.now(UTC),
        )
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)

        try:
            # 2. 과거 신호 조회
            signals = await self._get_signals_in_range(start_date, end_date)
            if not signals:
                raise BacktestServiceError(
                    f"기간 내 신호가 없습니다: {start_date.date()} ~ {end_date.date()}"
                )

            logger.info(f"시뮬레이션 대상 신호: {len(signals)}개")

            # 3. 시장 데이터 조회 (신호 시점의 가격 확인용)
            market_data = await self._get_market_data_in_range(start_date, end_date)
            if not market_data:
                raise BacktestServiceError("기간 내 시장 데이터가 없습니다")

            # 4. 시뮬레이션 실행
            state = BacktestState(cash=initial_capital)
            state = await self._engine.simulate_trading(state, signals, market_data)

            # 5. 성과 지표 계산
            metrics = self._reporter.calculate_metrics(state, initial_capital)

            # 6. 결과 업데이트
            result.status = BacktestStatus.COMPLETED.value
            result.final_capital = metrics.final_capital
            result.total_return_pct = metrics.total_return_pct
            result.max_drawdown_pct = metrics.max_drawdown_pct
            result.win_rate_pct = metrics.win_rate_pct
            result.profit_factor = metrics.profit_factor
            result.sharpe_ratio = metrics.sharpe_ratio
            result.total_trades = metrics.total_trades
            result.winning_trades = metrics.winning_trades
            result.losing_trades = metrics.losing_trades
            result.avg_profit_pct = metrics.avg_profit_pct
            result.avg_loss_pct = metrics.avg_loss_pct
            result.trade_history = self._reporter.serialize_trades(state.trades)
            result.completed_at = datetime.now(UTC)

            await self.db.commit()
            await self.db.refresh(result)

            logger.info(
                f"백테스트 완료: {name} - "
                f"수익률 {metrics.total_return_pct:.2f}%, "
                f"MDD {metrics.max_drawdown_pct:.2f}%, "
                f"승률 {metrics.win_rate_pct:.2f}%"
            )

            return result

        except Exception as e:
            # 오류 발생 시 상태 업데이트
            result.status = BacktestStatus.FAILED.value
            result.error_message = str(e)
            result.completed_at = datetime.now(UTC)
            await self.db.commit()

            logger.error(f"백테스트 실패: {name} - {e}")
            raise BacktestServiceError(f"백테스트 실행 실패: {e}") from e

    async def _get_signals_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[TradingSignal]:
        """
        기간 내 신호 조회

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            list[TradingSignal]: 신호 목록 (시간순)
        """
        stmt = (
            select(TradingSignal)
            .where(
                TradingSignal.created_at >= start_date,
                TradingSignal.created_at <= end_date,
            )
            .order_by(TradingSignal.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_market_data_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[datetime, CandlePriceData]:
        """
        기간 내 시장 데이터 조회 (Upbit 캔들 API 사용)

        Upbit의 60분봉 캔들 API를 사용하여 과거 데이터를 조회합니다.
        7일 이상의 장기 백테스트도 지원합니다.

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            dict[datetime, CandlePriceData]: 시간대별 시장 데이터
        """
        indexed: dict[datetime, CandlePriceData] = {}

        # 필요한 시간 수 계산
        total_hours = int((end_date - start_date).total_seconds() / 3600) + 1
        logger.info(f"캔들 데이터 조회: {total_hours}시간 분량")

        # 페이지네이션으로 캔들 데이터 수집 (200개씩)
        remaining = total_hours

        while remaining > 0:
            fetch_count = min(remaining, BACKTEST_CANDLE_FETCH_LIMIT)

            try:
                # 60분봉 캔들 조회 (to 파라미터로 페이지네이션)
                candles = await self.upbit_client.get_minute_candles(
                    market=settings.trading_ticker,
                    unit=60,
                    count=fetch_count,
                )

                if not candles:
                    break

                for candle in candles:
                    # UTC 시간 파싱
                    candle_time = datetime.fromisoformat(
                        candle.candle_date_time_utc.replace("Z", "+00:00")
                    ).replace(tzinfo=UTC)

                    # 기간 내 데이터만 저장
                    if start_date <= candle_time <= end_date:
                        hour_key = candle_time.replace(
                            minute=0, second=0, microsecond=0
                        )
                        indexed[hour_key] = CandlePriceData(
                            timestamp=candle_time,
                            price=candle.trade_price or Decimal("0"),
                            high_price=candle.high_price,
                            low_price=candle.low_price,
                            volume=candle.candle_acc_trade_volume,
                        )

                # 다음 페이지를 위해 가장 오래된 캔들 시간으로 이동
                oldest_candle = candles[-1]
                oldest_time = datetime.fromisoformat(
                    oldest_candle.candle_date_time_utc.replace("Z", "+00:00")
                ).replace(tzinfo=UTC)

                if oldest_time <= start_date:
                    break

                remaining -= fetch_count

            except Exception as e:
                logger.warning(f"캔들 데이터 조회 실패: {e}")
                break

        logger.info(f"캔들 데이터 조회 완료: {len(indexed)}개 시간대")
        return indexed

    async def get_result(self, result_id: int) -> BacktestResult | None:
        """
        백테스트 결과 조회

        Args:
            result_id: 결과 ID

        Returns:
            BacktestResult | None: 결과 또는 None
        """
        stmt = select(BacktestResult).where(BacktestResult.id == result_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_results(
        self,
        limit: int = 20,
        status: str | None = None,
    ) -> list[BacktestResult]:
        """
        백테스트 결과 목록 조회

        Args:
            limit: 최대 조회 개수
            status: 상태 필터 (선택)

        Returns:
            list[BacktestResult]: 결과 목록 (최신순)
        """
        stmt = select(BacktestResult).order_by(desc(BacktestResult.created_at))

        if status:
            stmt = stmt.where(BacktestResult.status == status)

        stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())


# === 팩토리 함수 ===
def get_backtest_service(db: AsyncSession) -> BacktestService:
    """
    BacktestService 인스턴스 생성

    Args:
        db: SQLAlchemy 비동기 세션

    Returns:
        BacktestService: 백테스트 서비스 인스턴스
    """
    return BacktestService(db)
