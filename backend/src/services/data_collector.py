"""
시장 데이터 수집 서비스 모듈

이 모듈은 Upbit에서 실시간 시장 데이터를 수집하고 관리하는 서비스를 제공합니다.
- 실시간 시세 데이터 수집 및 DB 저장
- 네트워크 장애 시 자동 재연결
- 수집 통계 및 상태 관리
- 오래된 데이터 자동 정리
"""

import asyncio
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.market_data import MarketData
from src.services.upbit_client import UpbitClient, UpbitError, get_upbit_client

# === 수집 관련 상수 ===
DEFAULT_MARKET = "KRW-XRP"  # 기본 수집 마켓
RECONNECT_BASE_DELAY = 1.0  # 재연결 기본 대기 시간 (초)
RECONNECT_MAX_DELAY = 60.0  # 재연결 최대 대기 시간 (초)
RECONNECT_MAX_ATTEMPTS = 10  # 최대 재시도 횟수
MS_TO_SECONDS = 1000  # 밀리초 → 초 변환 상수


class DataCollectorError(Exception):
    """
    데이터 수집 오류 예외

    시장 데이터 수집 중 발생하는 오류를 나타냅니다.
    """

    pass


class DataCollector:
    """
    시장 데이터 수집기

    Upbit API에서 XRP/KRW 시세를 수집하여 데이터베이스에 저장합니다.
    네트워크 장애 시 지수 백오프를 사용한 자동 재시도를 지원합니다.

    Attributes:
        _client: Upbit API 클라이언트
        _market: 수집 대상 마켓 코드
        _is_running: 실행 상태 플래그
        _consecutive_failures: 연속 실패 횟수
        _last_success: 마지막 성공 시간
        _total_collected: 총 수집 건수

    사용 예시:
        collector = DataCollector()
        async with async_session_factory() as session:
            data = await collector.collect_once(session)
            await session.commit()
    """

    def __init__(
        self,
        upbit_client: UpbitClient | None = None,
        market: str = DEFAULT_MARKET,
    ):
        """
        데이터 수집기 초기화

        Args:
            upbit_client: Upbit API 클라이언트 (기본값: 싱글톤 사용)
            market: 수집할 마켓 코드 (기본값: KRW-XRP)
        """
        self._client = upbit_client or get_upbit_client()
        self._market = market
        self._is_running = False
        self._consecutive_failures = 0
        self._last_success: datetime | None = None
        self._total_collected = 0

    @property
    def is_running(self) -> bool:
        """
        실행 상태 확인

        Returns:
            bool: 수집기 실행 중 여부
        """
        return self._is_running

    @property
    def stats(self) -> dict[str, Any]:
        """
        수집 통계 반환

        Returns:
            dict: 수집기 상태 및 통계 정보
                - is_running: 실행 중 여부
                - consecutive_failures: 연속 실패 횟수
                - last_success: 마지막 성공 시간 (ISO 형식)
                - total_collected: 총 수집 건수
                - market: 수집 마켓
        """
        return {
            "is_running": self._is_running,
            "consecutive_failures": self._consecutive_failures,
            "last_success": self._last_success.isoformat()
            if self._last_success
            else None,
            "total_collected": self._total_collected,
            "market": self._market,
        }

    async def collect_once(self, session: AsyncSession) -> MarketData | None:
        """
        시장 데이터 1회 수집 및 저장

        Upbit API에서 현재 시세를 조회하여 DB에 저장합니다.

        Args:
            session: 데이터베이스 세션

        Returns:
            MarketData: 저장된 시장 데이터 (성공 시)
            None: 실패 시

        Raises:
            DataCollectorError: 수집 또는 저장 실패 시
        """
        try:
            # Upbit API에서 시세 조회
            ticker = await self._client.get_ticker(self._market)

            # 시장 데이터 객체 생성
            market_data = MarketData(
                timestamp=datetime.fromtimestamp(
                    ticker.timestamp / MS_TO_SECONDS, tz=UTC
                ),
                price=ticker.trade_price,
                volume=ticker.acc_trade_volume_24h,
                high_price=ticker.high_price,
                low_price=ticker.low_price,
                trade_count=0,  # Upbit API에서 거래 건수 미제공
            )

            # DB에 추가 및 플러시 (ID 할당)
            session.add(market_data)
            await session.flush()

            # 성공 통계 업데이트
            self._consecutive_failures = 0
            self._last_success = datetime.now(UTC)
            self._total_collected += 1

            logger.debug(
                f"시장 데이터 수집: 가격={ticker.trade_price}, "
                f"거래량={ticker.acc_trade_volume_24h}"
            )

            return market_data

        except UpbitError as e:
            # API 오류 처리
            self._consecutive_failures += 1
            logger.error(
                f"시장 데이터 수집 실패: {e.message} "
                f"(시도 {self._consecutive_failures})"
            )
            raise DataCollectorError(f"Upbit API 오류: {e.message}") from e

        except Exception as e:
            # 기타 예외 처리
            self._consecutive_failures += 1
            logger.exception(
                f"시장 데이터 수집 중 예외 발생 (시도 {self._consecutive_failures})"
            )
            raise DataCollectorError(f"수집 오류: {e}") from e

    async def collect_with_retry(
        self,
        session: AsyncSession,
        max_attempts: int = RECONNECT_MAX_ATTEMPTS,
    ) -> MarketData | None:
        """
        재시도 로직이 포함된 시장 데이터 수집

        네트워크 오류 시 지수 백오프(exponential backoff)를 사용하여
        자동으로 재시도합니다. 지터(jitter)를 추가하여 thundering herd 방지.

        Args:
            session: 데이터베이스 세션
            max_attempts: 최대 재시도 횟수

        Returns:
            MarketData: 수집된 시장 데이터 (성공 시)
            None: 모든 재시도 실패 시
        """
        delay = RECONNECT_BASE_DELAY

        for attempt in range(max_attempts):
            try:
                return await self.collect_once(session)

            except DataCollectorError as e:
                # 마지막 시도면 None 반환
                if attempt == max_attempts - 1:
                    logger.error(f"{max_attempts}회 시도 후 데이터 수집 실패: {e}")
                    return None

                # 지수 백오프 + 지터 계산
                jitter = random.uniform(0, delay * 0.1)
                wait_time = min(delay + jitter, RECONNECT_MAX_DELAY)

                logger.warning(
                    f"{wait_time:.1f}초 후 재시도 (시도 {attempt + 1}/{max_attempts})"
                )

                await asyncio.sleep(wait_time)
                delay = min(delay * 2, RECONNECT_MAX_DELAY)  # 대기 시간 2배 증가

        return None

    async def get_latest(
        self,
        session: AsyncSession,
        limit: int = 1,
    ) -> list[MarketData]:
        """
        최신 시장 데이터 조회

        가장 최근에 수집된 데이터를 조회합니다.

        Args:
            session: 데이터베이스 세션
            limit: 조회할 레코드 수

        Returns:
            list[MarketData]: 최신 시장 데이터 목록 (최신순)
        """
        result = await session.execute(
            select(MarketData).order_by(MarketData.timestamp.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_data_range(
        self,
        session: AsyncSession,
        start_time: datetime,
        end_time: datetime | None = None,
    ) -> list[MarketData]:
        """
        시간 범위 내 시장 데이터 조회

        지정된 시간 범위의 데이터를 시간 순으로 조회합니다.

        Args:
            session: 데이터베이스 세션
            start_time: 시작 시간
            end_time: 종료 시간 (기본값: 현재 시간)

        Returns:
            list[MarketData]: 시간 범위 내 시장 데이터 목록 (오래된 순)
        """
        if end_time is None:
            end_time = datetime.now(UTC)

        result = await session.execute(
            select(MarketData)
            .where(MarketData.timestamp >= start_time)
            .where(MarketData.timestamp <= end_time)
            .order_by(MarketData.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_hourly_summary(
        self,
        session: AsyncSession,
        hours: int = 24,
    ) -> dict[str, Any]:
        """
        시간별 요약 통계 조회

        지정된 시간 동안의 가격 변동 통계를 계산합니다.

        Args:
            session: 데이터베이스 세션
            hours: 통계 기간 (시간)

        Returns:
            dict: 요약 통계
                - count: 데이터 포인트 수
                - period_hours: 기간 (시간)
                - latest_price: 최신 가격
                - high: 최고가
                - low: 최저가
                - price_change_pct: 가격 변동률 (%)
                - first_timestamp: 시작 시간
                - last_timestamp: 종료 시간
        """
        start_time = datetime.now(UTC) - timedelta(hours=hours)
        data = await self.get_data_range(session, start_time)

        # 데이터가 없는 경우
        if not data:
            return {
                "count": 0,
                "period_hours": hours,
                "latest_price": None,
                "high": None,
                "low": None,
                "price_change_pct": None,
            }

        # 가격 목록 추출 및 통계 계산
        prices = [d.price for d in data]
        first_price = prices[0]
        last_price = prices[-1]

        # 가격 변동률 계산 (첫 가격 대비)
        price_change_pct = (
            ((last_price - first_price) / first_price * 100)
            if first_price > 0
            else Decimal("0")
        )

        return {
            "count": len(data),
            "period_hours": hours,
            "latest_price": float(last_price),
            "high": float(max(prices)),
            "low": float(min(prices)),
            "price_change_pct": float(price_change_pct),
            "first_timestamp": data[0].timestamp.isoformat(),
            "last_timestamp": data[-1].timestamp.isoformat(),
        }

    async def cleanup_old_data(
        self,
        session: AsyncSession,
        retention_days: int | None = None,
    ) -> int:
        """
        오래된 데이터 정리

        보관 기간이 지난 시장 데이터를 삭제합니다.

        Args:
            session: 데이터베이스 세션
            retention_days: 보관 기간 (일) (기본값: 설정에서 로드)

        Returns:
            int: 삭제된 레코드 수
        """
        if retention_days is None:
            retention_days = settings.data_retention_days

        # 삭제 기준 날짜 계산
        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)

        # 오래된 데이터 삭제
        result = await session.execute(
            delete(MarketData).where(MarketData.timestamp < cutoff_date)
        )

        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.info(f"{retention_days}일 이전 데이터 {deleted_count}건 삭제 완료")

        return deleted_count


# === 싱글톤 인스턴스 ===
_data_collector: DataCollector | None = None


def get_data_collector() -> DataCollector:
    """
    DataCollector 싱글톤 반환

    애플리케이션 전체에서 동일한 수집기 인스턴스를 공유합니다.

    Returns:
        DataCollector: 싱글톤 수집기 인스턴스
    """
    global _data_collector
    if _data_collector is None:
        _data_collector = DataCollector()
    return _data_collector
