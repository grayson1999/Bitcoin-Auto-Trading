"""
시장 데이터 서비스 모듈

이 모듈은 시장 데이터 수집 및 조회 기능을 제공합니다.
- 실시간 시세 데이터 수집 (DataCollector 래핑)
- 시장 데이터 조회 (MarketRepository 사용)
- 통계 및 요약 정보 제공
"""

from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.upbit import (
    UpbitPublicAPI,
    UpbitPublicAPIError,
    get_upbit_public_api,
)
from src.config import settings
from src.entities import MarketData
from src.repositories.market_repository import MarketRepository
from src.services.data_collector import (
    DataCollector,
    DataCollectorError,
    get_data_collector,
)
from src.utils import UTC


class MarketServiceError(Exception):
    """시장 서비스 오류"""

    pass


class MarketService:
    """
    시장 데이터 서비스

    시장 데이터 수집, 조회, 통계 기능을 통합 제공합니다.
    DataCollector와 MarketRepository를 조합하여 사용합니다.

    사용 예시:
        service = MarketService(db_session)
        latest = await service.get_latest_data()
        history = await service.get_history(hours=24)
    """

    def __init__(
        self,
        db: AsyncSession,
        data_collector: DataCollector | None = None,
        upbit_client: UpbitPublicAPI | None = None,
    ):
        """
        시장 서비스 초기화

        Args:
            db: SQLAlchemy 비동기 세션
            data_collector: 데이터 수집기 (기본값: 싱글톤 사용)
            upbit_client: Upbit Public API 클라이언트 (기본값: 싱글톤 사용)
        """
        self.db = db
        self._collector = data_collector or get_data_collector()
        self._upbit_client = upbit_client or get_upbit_public_api()
        self._repository = MarketRepository(db)

        # 마켓 설정
        self.market = settings.trading_ticker

    # =========================================================================
    # 데이터 수집
    # =========================================================================

    async def collect_data(self) -> MarketData | None:
        """
        시장 데이터 1회 수집

        Upbit API에서 현재 시세를 수집하여 DB에 저장합니다.

        Returns:
            MarketData: 수집된 시장 데이터 (성공 시)
            None: 실패 시

        Raises:
            MarketServiceError: 수집 실패 시
        """
        try:
            market_data = await self._collector.collect_once(self.db)
            await self.db.commit()
            return market_data
        except DataCollectorError as e:
            logger.error(f"시장 데이터 수집 실패: {e}")
            raise MarketServiceError(f"데이터 수집 오류: {e}") from e

    async def collect_data_with_retry(
        self,
        max_attempts: int = 10,
    ) -> MarketData | None:
        """
        재시도 로직이 포함된 시장 데이터 수집

        Args:
            max_attempts: 최대 재시도 횟수

        Returns:
            MarketData: 수집된 시장 데이터 (성공 시)
            None: 모든 재시도 실패 시
        """
        market_data = await self._collector.collect_with_retry(self.db, max_attempts)
        if market_data:
            await self.db.commit()
        return market_data

    def get_collector_stats(self) -> dict[str, Any]:
        """
        데이터 수집기 통계 반환

        Returns:
            수집기 상태 및 통계 정보
        """
        return self._collector.stats

    # =========================================================================
    # 데이터 조회
    # =========================================================================

    async def get_latest_data(
        self,
        limit: int = 1,
        symbol: str | None = None,
    ) -> list[MarketData]:
        """
        최신 시장 데이터 조회

        Args:
            limit: 조회할 레코드 수
            symbol: 마켓 심볼 (기본: 현재 설정 마켓)

        Returns:
            최신 시장 데이터 목록 (최신순)
        """
        return await self._repository.get_latest(limit, symbol)

    async def get_latest_one(self, symbol: str | None = None) -> MarketData | None:
        """
        가장 최신 시장 데이터 1건 조회

        Args:
            symbol: 마켓 심볼 (기본: 현재 설정 마켓)

        Returns:
            최신 MarketData 또는 None
        """
        return await self._repository.get_latest_one(symbol)

    async def get_history(
        self,
        hours: int = 24,
        symbol: str | None = None,
    ) -> list[MarketData]:
        """
        시간 범위 내 히스토리 조회

        Args:
            hours: 조회할 시간 범위
            symbol: 마켓 심볼

        Returns:
            시간 범위 내 시장 데이터 목록 (오래된 순)
        """
        return await self._repository.get_history(hours, symbol)

    async def get_range(
        self,
        start_time: datetime,
        end_time: datetime | None = None,
        symbol: str | None = None,
    ) -> list[MarketData]:
        """
        시간 범위 내 시장 데이터 조회

        Args:
            start_time: 시작 시간
            end_time: 종료 시간 (기본: 현재 시간)
            symbol: 마켓 심볼

        Returns:
            시간 범위 내 시장 데이터 목록 (오래된 순)
        """
        return await self._repository.get_range(start_time, end_time, symbol)

    # =========================================================================
    # 통계 및 요약
    # =========================================================================

    async def get_hourly_summary(
        self,
        hours: int = 24,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        시간별 요약 통계 조회

        Args:
            hours: 통계 기간 (시간)
            symbol: 마켓 심볼

        Returns:
            요약 통계 딕셔너리
        """
        return await self._repository.get_hourly_summary(hours, symbol)

    async def get_current_price(self) -> dict[str, Any]:
        """
        현재 시세 조회 (Upbit API 직접 호출)

        Returns:
            현재 시세 정보 딕셔너리

        Raises:
            MarketServiceError: API 호출 실패 시
        """
        try:
            ticker = await self._upbit_client.get_ticker(self.market)

            # 24시간 변동률 계산
            change_24h_pct = None
            if ticker.prev_closing_price and ticker.prev_closing_price > 0:
                change_24h_pct = float(
                    (ticker.trade_price - ticker.prev_closing_price)
                    / ticker.prev_closing_price
                    * 100
                )

            return {
                "symbol": self.market,
                "price": float(ticker.trade_price),
                "high_price": float(ticker.high_price),
                "low_price": float(ticker.low_price),
                "volume_24h": float(ticker.acc_trade_volume_24h),
                "change_24h_pct": change_24h_pct,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        except UpbitPublicAPIError as e:
            logger.error(f"현재 시세 조회 실패: {e.message}")
            raise MarketServiceError(f"Upbit API 오류: {e.message}") from e

    async def get_data_count(self, symbol: str | None = None) -> int:
        """
        시장 데이터 레코드 개수 조회

        Args:
            symbol: 마켓 심볼

        Returns:
            레코드 개수
        """
        return await self._repository.get_count_by_symbol(symbol)

    # =========================================================================
    # 데이터 관리
    # =========================================================================

    async def cleanup_old_data(self, retention_days: int | None = None) -> int:
        """
        오래된 데이터 정리

        Args:
            retention_days: 보관 기간 (일)

        Returns:
            삭제된 레코드 수
        """
        deleted = await self._repository.cleanup_old_data(retention_days)
        await self.db.commit()

        if deleted > 0:
            logger.info(f"오래된 시장 데이터 {deleted}건 삭제 완료")

        return deleted


# === 팩토리 함수 ===
def get_market_service(db: AsyncSession) -> MarketService:
    """
    MarketService 인스턴스 생성

    Args:
        db: SQLAlchemy 비동기 세션

    Returns:
        MarketService 인스턴스
    """
    return MarketService(db)
