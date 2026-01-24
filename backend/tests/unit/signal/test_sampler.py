"""
MarketDataSampler 단위 테스트

테스트 시나리오:
1. sample_by_interval: 간격별 샘플링 로직
2. get_sampled_data: 시간대별 분류 및 샘플링
3. 엣지 케이스: 빈 데이터, 경계 조건
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from src.entities.market_data import MarketData
from src.modules.signal.sampler import MarketDataSampler


def create_market_data(
    timestamp: datetime,
    price: Decimal = Decimal("100000.0"),
    id_: int = 1,
) -> MarketData:
    """테스트용 MarketData 객체 생성"""
    data = MarketData(
        id=id_,
        symbol="KRW-SOL",
        timestamp=timestamp,
        price=price,
        volume=Decimal("1000.0"),
        high_price=price + Decimal("1000"),
        low_price=price - Decimal("1000"),
        trade_count=100,
    )
    return data


class TestSampleByInterval:
    """sample_by_interval 메서드 테스트"""

    def test_empty_data(self):
        """빈 데이터 입력 시 빈 리스트 반환"""
        sampler = MarketDataSampler()
        result = sampler.sample_by_interval([], 60)
        assert result == []

    def test_invalid_interval(self):
        """유효하지 않은 간격 시 빈 리스트 반환"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)
        data = [create_market_data(now)]
        assert sampler.sample_by_interval(data, 0) == []
        assert sampler.sample_by_interval(data, -1) == []

    def test_single_data_point(self):
        """단일 데이터 포인트는 그대로 반환"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)
        data = [create_market_data(now)]
        result = sampler.sample_by_interval(data, 60)
        assert len(result) == 1
        assert result[0].timestamp == now

    def test_sampling_60_min_interval(self):
        """60분 간격 샘플링 테스트"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)

        # 10분 간격으로 13개 데이터 생성 (0~120분, 2시간)
        data = [
            create_market_data(
                now - timedelta(minutes=i * 10),
                id_=i,
            )
            for i in range(13)
        ]

        # 60분 간격으로 샘플링
        result = sampler.sample_by_interval(data, 60)

        # 0분, 60분, 120분 = 3개 예상
        assert len(result) == 3

    def test_sampling_15_min_interval(self):
        """15분 간격 샘플링 테스트"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)

        # 5분 간격으로 12개 데이터 생성 (55분)
        data = [
            create_market_data(
                now - timedelta(minutes=i * 5),
                id_=i,
            )
            for i in range(12)
        ]

        # 15분 간격으로 샘플링
        result = sampler.sample_by_interval(data, 15)

        # 0분, 15분, 30분, 45분 = 4개 예상
        assert len(result) == 4

    def test_sampling_preserves_order(self):
        """샘플링 결과가 시간순 정렬되는지 확인"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)

        # 역순으로 데이터 생성
        data = [
            create_market_data(
                now - timedelta(minutes=i * 10),
                id_=i,
            )
            for i in range(6)
        ]

        result = sampler.sample_by_interval(data, 30)

        # 시간순 정렬 확인
        for i in range(len(result) - 1):
            assert result[i].timestamp < result[i + 1].timestamp


class TestGetSampledData:
    """get_sampled_data 메서드 테스트"""

    def test_empty_data(self):
        """빈 데이터 입력 시 빈 딕셔너리 반환"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)
        result = sampler.get_sampled_data([], now)
        assert result == {
            "long_term": [],
            "mid_term": [],
            "short_term": [],
        }

    def test_short_term_classification(self):
        """최근 1시간 데이터가 short_term에 분류되는지 확인"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)

        # 최근 30분 데이터
        data = [
            create_market_data(
                now - timedelta(minutes=5),
                id_=1,
            ),
            create_market_data(
                now - timedelta(minutes=30),
                id_=2,
            ),
        ]

        result = sampler.get_sampled_data(data, now)
        assert len(result["short_term"]) == 2
        assert len(result["mid_term"]) == 0
        assert len(result["long_term"]) == 0

    def test_mid_term_classification(self):
        """1시간~24시간 전 데이터가 mid_term에 분류되는지 확인"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)

        # 2시간 전, 12시간 전 데이터
        data = [
            create_market_data(
                now - timedelta(hours=2),
                id_=1,
            ),
            create_market_data(
                now - timedelta(hours=12),
                id_=2,
            ),
        ]

        result = sampler.get_sampled_data(data, now)
        assert len(result["short_term"]) == 0
        assert len(result["mid_term"]) == 2
        assert len(result["long_term"]) == 0

    def test_long_term_classification(self):
        """24시간~14일 전 데이터가 long_term에 분류되는지 확인"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)

        # 2일 전, 10일 전 데이터
        data = [
            create_market_data(
                now - timedelta(days=2),
                id_=1,
            ),
            create_market_data(
                now - timedelta(days=10),
                id_=2,
            ),
        ]

        result = sampler.get_sampled_data(data, now)
        assert len(result["short_term"]) == 0
        assert len(result["mid_term"]) == 0
        assert len(result["long_term"]) == 2

    def test_mixed_time_classification(self):
        """혼합 시간대 데이터 분류 테스트"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)

        data = [
            # short_term: 최근 1시간
            create_market_data(now - timedelta(minutes=10), id_=1),
            create_market_data(now - timedelta(minutes=30), id_=2),
            # mid_term: 1시간~24시간
            create_market_data(now - timedelta(hours=2), id_=3),
            create_market_data(now - timedelta(hours=10), id_=4),
            # long_term: 24시간~14일
            create_market_data(now - timedelta(days=2), id_=5),
            create_market_data(now - timedelta(days=7), id_=6),
        ]

        result = sampler.get_sampled_data(data, now)
        assert len(result["short_term"]) == 2
        assert len(result["mid_term"]) == 2
        assert len(result["long_term"]) == 2

    def test_old_data_excluded(self):
        """14일 이전 데이터는 제외되는지 확인"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)

        # 15일 전 데이터
        data = [
            create_market_data(now - timedelta(days=15), id_=1),
        ]

        result = sampler.get_sampled_data(data, now)
        total = sampler.get_total_count(result)
        assert total == 0

    def test_sampling_applied_to_each_term(self):
        """각 시간대에 샘플링이 적용되는지 확인"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)

        # short_term: 5분 간격으로 많은 데이터 생성
        short_term_data = [
            create_market_data(
                now - timedelta(minutes=i),
                id_=i,
            )
            for i in range(30)  # 최근 30분, 1분 간격
        ]

        result = sampler.get_sampled_data(short_term_data, now)

        # 5분 간격 샘플링으로 약 6개 예상 (0, 5, 10, 15, 20, 25분)
        assert len(result["short_term"]) <= 7
        assert len(result["short_term"]) >= 5


class TestGetTotalCount:
    """get_total_count 메서드 테스트"""

    def test_empty_sampled(self):
        """빈 샘플링 결과"""
        sampler = MarketDataSampler()
        sampled = {
            "long_term": [],
            "mid_term": [],
            "short_term": [],
        }
        assert sampler.get_total_count(sampled) == 0

    def test_total_count(self):
        """총 개수 계산"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)
        sampled = {
            "long_term": [create_market_data(now, id_=i) for i in range(3)],
            "mid_term": [create_market_data(now, id_=i) for i in range(2)],
            "short_term": [create_market_data(now, id_=i) for i in range(1)],
        }
        assert sampler.get_total_count(sampled) == 6


class TestGetStatistics:
    """get_statistics 메서드 테스트"""

    def test_statistics(self):
        """통계 정보 반환"""
        sampler = MarketDataSampler()
        now = datetime.now(UTC)
        sampled = {
            "long_term": [create_market_data(now, id_=i) for i in range(100)],
            "mid_term": [create_market_data(now, id_=i) for i in range(50)],
            "short_term": [create_market_data(now, id_=i) for i in range(10)],
        }
        stats = sampler.get_statistics(sampled)
        assert stats == {
            "long_term": 100,
            "mid_term": 50,
            "short_term": 10,
            "total": 160,
        }


class TestCustomConfig:
    """커스텀 설정 테스트"""

    def test_custom_sampling_config(self):
        """커스텀 샘플링 설정 적용"""
        custom_config = {
            "long_term": {"hours": 48, "interval_min": 30},
            "mid_term": {"hours": 6, "interval_min": 10},
            "short_term": {"hours": 2, "interval_min": 1},
        }
        sampler = MarketDataSampler(config=custom_config)
        assert sampler.config == custom_config
