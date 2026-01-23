"""
시장 데이터 수집 서비스 모듈

이 모듈은 Upbit에서 실시간 시장 데이터를 수집하고 관리하는 서비스를 제공합니다.
- 실시간 시세 데이터 수집 및 DB 저장
- 네트워크 장애 시 자동 재연결
- 수집 통계 및 상태 관리
"""

import asyncio
import random
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
from src.config.constants import MS_TO_SECONDS
from src.entities import MarketData
from src.utils import UTC

# === 수집 관련 상수 ===
# DEFAULT_MARKET은 settings.trading_ticker에서 동적으로 로드됨
RECONNECT_BASE_DELAY = 1.0  # 재연결 기본 대기 시간 (초)
RECONNECT_MAX_DELAY = 60.0  # 재연결 최대 대기 시간 (초)
RECONNECT_MAX_ATTEMPTS = 10  # 최대 재시도 횟수


class DataCollectorError(Exception):
    """
    데이터 수집 오류 예외

    시장 데이터 수집 중 발생하는 오류를 나타냅니다.
    """

    pass


class DataCollector:
    """
    시장 데이터 수집기

    Upbit API에서 설정된 마켓의 시세를 수집하여 데이터베이스에 저장합니다.
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
        upbit_client: UpbitPublicAPI | None = None,
        market: str | None = None,
    ):
        """
        데이터 수집기 초기화

        Args:
            upbit_client: Upbit Public API 클라이언트 (기본값: 싱글톤 사용)
            market: 수집할 마켓 코드 (기본값: settings.trading_ticker)
        """
        self._client = upbit_client or get_upbit_public_api()
        self._market = market or settings.trading_ticker
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
                symbol=self._market,
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

        except UpbitPublicAPIError as e:
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
