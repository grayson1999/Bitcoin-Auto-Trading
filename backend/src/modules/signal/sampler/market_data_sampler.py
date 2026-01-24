"""
시장 데이터 샘플링 모듈

AI 프롬프트 토큰 절감을 위해 시간대별로 다른 간격으로 데이터를 샘플링합니다.
- 장기 (14일): 1시간 간격 → ~336개
- 중기 (24시간): 15분 간격 → ~96개
- 단기 (1시간): 5분 간격 → ~12개
- 총 ~450개 (기존 1000개 대비 55% 절감)
"""

from datetime import UTC, datetime, timedelta

from src.config.constants import SAMPLING_CONFIG
from src.entities.market_data import MarketData


class MarketDataSampler:
    """
    시간대별 시장 데이터 샘플링

    10초 간격으로 수집된 데이터를 시간대별로 다른 간격으로 샘플링하여
    AI 프롬프트에 필요한 최소한의 데이터만 추출합니다.
    """

    def __init__(self, config: dict | None = None):
        """
        샘플러 초기화

        Args:
            config: 샘플링 설정 (기본값: SAMPLING_CONFIG)
        """
        self.config = config or SAMPLING_CONFIG

    def sample_by_interval(
        self,
        data: list[MarketData],
        interval_minutes: int,
    ) -> list[MarketData]:
        """
        주어진 간격으로 데이터 샘플링

        Args:
            data: 시장 데이터 목록 (timestamp 정렬 불필요)
            interval_minutes: 샘플링 간격 (분)

        Returns:
            샘플링된 데이터 목록 (timestamp 오름차순 정렬)
        """
        if not data or interval_minutes <= 0:
            return []

        # timestamp 오름차순 정렬
        sorted_data = sorted(data, key=lambda x: x.timestamp)

        result: list[MarketData] = []
        last_sampled_time: datetime | None = None
        interval_seconds = interval_minutes * 60

        for item in sorted_data:
            if last_sampled_time is None:
                result.append(item)
                last_sampled_time = item.timestamp
            else:
                time_diff = (item.timestamp - last_sampled_time).total_seconds()
                if time_diff >= interval_seconds:
                    result.append(item)
                    last_sampled_time = item.timestamp

        return result

    def get_sampled_data(
        self,
        data: list[MarketData],
        now: datetime | None = None,
    ) -> dict[str, list[MarketData]]:
        """
        장기/중기/단기별 샘플링된 데이터 반환

        각 시간대는 중복 없이 해당 기간에만 해당하는 데이터를 포함합니다:
        - short_term: now ~ 1시간 전
        - mid_term: 1시간 전 ~ 24시간 전
        - long_term: 24시간 전 ~ 14일 전

        Args:
            data: 전체 시장 데이터 목록
            now: 현재 시간 (테스트용, 기본값: UTC now)

        Returns:
            {
                "long_term": [...],   # 14일, 1시간 간격
                "mid_term": [...],    # 24시간, 15분 간격
                "short_term": [...],  # 1시간, 5분 간격
            }
        """
        if now is None:
            now = datetime.now(UTC)

        # 시간대별 경계 계산
        short_term_start = now - timedelta(hours=self.config["short_term"]["hours"])
        mid_term_start = now - timedelta(hours=self.config["mid_term"]["hours"])
        long_term_start = now - timedelta(hours=self.config["long_term"]["hours"])

        # 시간대별 데이터 분류 (중복 없이)
        short_term_data: list[MarketData] = []
        mid_term_data: list[MarketData] = []
        long_term_data: list[MarketData] = []

        for item in data:
            ts = item.timestamp
            if ts >= short_term_start:
                # 최근 1시간: short_term
                short_term_data.append(item)
            elif ts >= mid_term_start:
                # 1시간~24시간: mid_term
                mid_term_data.append(item)
            elif ts >= long_term_start:
                # 24시간~14일: long_term
                long_term_data.append(item)
            # 14일 이전 데이터는 무시

        # 각 시간대별 샘플링 적용
        return {
            "long_term": self.sample_by_interval(
                long_term_data,
                self.config["long_term"]["interval_min"],
            ),
            "mid_term": self.sample_by_interval(
                mid_term_data,
                self.config["mid_term"]["interval_min"],
            ),
            "short_term": self.sample_by_interval(
                short_term_data,
                self.config["short_term"]["interval_min"],
            ),
        }

    def get_total_count(self, sampled: dict[str, list[MarketData]]) -> int:
        """
        샘플링된 총 데이터 개수 반환

        Args:
            sampled: get_sampled_data()의 반환값

        Returns:
            총 데이터 개수
        """
        return sum(len(v) for v in sampled.values())

    def get_statistics(
        self,
        sampled: dict[str, list[MarketData]],
    ) -> dict[str, int]:
        """
        샘플링 통계 반환

        Args:
            sampled: get_sampled_data()의 반환값

        Returns:
            {
                "long_term": 개수,
                "mid_term": 개수,
                "short_term": 개수,
                "total": 총 개수,
            }
        """
        return {
            "long_term": len(sampled.get("long_term", [])),
            "mid_term": len(sampled.get("mid_term", [])),
            "short_term": len(sampled.get("short_term", [])),
            "total": self.get_total_count(sampled),
        }
