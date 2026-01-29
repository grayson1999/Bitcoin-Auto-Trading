"""
Fear & Greed Index 클라이언트

Alternative.me API를 통해 비트코인 시장 심리 지표를 조회합니다.

주의: 이 지표는 BTC(비트코인) 기반입니다.
- 메이저 코인: BTC와 상관관계 높음 → 적극 활용
- 알트코인: BTC와 상관관계 중간 → 참고용
- 밈코인: BTC와 상관관계 낮음 → 배경 정보로만 활용
"""

from dataclasses import dataclass
from datetime import datetime

import httpx
from loguru import logger

from src.utils import UTC


@dataclass
class FearGreedData:
    """
    Fear & Greed Index 데이터

    Attributes:
        value: 지표 값 (0-100)
        classification: 분류 (Extreme Fear, Fear, Neutral, Greed, Extreme Greed)
        timestamp: 측정 시각
        time_until_update: 다음 업데이트까지 남은 초
    """

    value: int
    classification: str
    timestamp: datetime
    time_until_update: int = 0

    @property
    def is_extreme_fear(self) -> bool:
        """극도의 공포 구간인지 (0-24)"""
        return self.value <= 24

    @property
    def is_extreme_greed(self) -> bool:
        """극도의 탐욕 구간인지 (75-100)"""
        return self.value >= 75

    @property
    def classification_ko(self) -> str:
        """한글 분류명"""
        mapping = {
            "Extreme Fear": "극도의 공포",
            "Fear": "공포",
            "Neutral": "중립",
            "Greed": "탐욕",
            "Extreme Greed": "극도의 탐욕",
        }
        return mapping.get(self.classification, self.classification)


class FearGreedClient:
    """
    Fear & Greed Index API 클라이언트

    Alternative.me의 무료 API를 사용합니다.
    - 비용: 무료
    - Rate Limit: 없음
    - 업데이트 주기: 하루 1회 (UTC 00:00)
    """

    API_URL = "https://api.alternative.me/fng/"
    TIMEOUT = 10.0

    async def get_current(self) -> FearGreedData:
        """
        현재 Fear & Greed Index 조회

        Returns:
            FearGreedData: 현재 지표 데이터

        Raises:
            httpx.HTTPError: API 호출 실패 시
        """
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.get(self.API_URL)
            response.raise_for_status()

            data = response.json()["data"][0]
            return FearGreedData(
                value=int(data["value"]),
                classification=data["value_classification"],
                timestamp=datetime.fromtimestamp(int(data["timestamp"]), tz=UTC),
                time_until_update=int(data.get("time_until_update", 0)),
            )

    async def get_history(self, days: int = 7) -> list[FearGreedData]:
        """
        과거 Fear & Greed Index 조회

        Args:
            days: 조회할 일수 (기본 7일)

        Returns:
            list[FearGreedData]: 과거 지표 데이터 리스트 (최신순)
        """
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.get(f"{self.API_URL}?limit={days}")
            response.raise_for_status()

            results = []
            for item in response.json()["data"]:
                results.append(
                    FearGreedData(
                        value=int(item["value"]),
                        classification=item["value_classification"],
                        timestamp=datetime.fromtimestamp(
                            int(item["timestamp"]), tz=UTC
                        ),
                        time_until_update=0,
                    )
                )
            return results


# 싱글톤 인스턴스
_fear_greed_client: FearGreedClient | None = None


def get_fear_greed_client() -> FearGreedClient:
    """FearGreedClient 싱글톤 인스턴스 반환"""
    global _fear_greed_client
    if _fear_greed_client is None:
        _fear_greed_client = FearGreedClient()
        logger.info("FearGreedClient 초기화 완료")
    return _fear_greed_client
