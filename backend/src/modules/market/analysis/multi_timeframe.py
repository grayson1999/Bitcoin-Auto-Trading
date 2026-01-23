"""
멀티 타임프레임 분석 서비스

여러 시간 단위(1시간, 4시간, 일봉, 주봉)의 캔들 데이터를 분석하여
종합적인 시장 상황을 파악합니다.
"""

import asyncio
from dataclasses import dataclass, field

from loguru import logger

from src.clients.upbit import (
    UpbitCandleData,
    UpbitPublicAPI,
    get_upbit_public_api,
)
from src.config import settings
from src.modules.market.analysis.indicators import (
    IndicatorResult,
    TechnicalIndicatorCalculator,
    get_technical_calculator,
)


@dataclass
class TimeframeAnalysis:
    """
    단일 타임프레임 분석 결과

    Attributes:
        timeframe: 타임프레임 식별자 ("1h", "4h", "1d", "1w")
        trend: 추세 방향 ("bullish", "bearish", "sideways")
        strength: 추세 강도 (0.0 - 1.0)
        indicators: 기술적 지표 결과
        current_price: 현재 종가
        price_change_pct: 가격 변화율 (%)
        key_observation: 핵심 관찰 사항 (한국어)
    """

    timeframe: str
    trend: str
    strength: float
    indicators: IndicatorResult
    current_price: float
    price_change_pct: float
    key_observation: str


@dataclass
class MultiTimeframeResult:
    """
    멀티 타임프레임 분석 결과

    Attributes:
        analyses: 타임프레임별 분석 결과
        overall_bias: 종합 편향 ("strong_buy", "buy", "neutral", "sell", "strong_sell")
        confluence_score: 타임프레임 간 일치도 (0.0 - 1.0)
        facts: 객관적 사실 목록
        interpretations: 주관적 해석 목록
        summary: 종합 요약 (한국어)
    """

    analyses: dict[str, TimeframeAnalysis] = field(default_factory=dict)
    overall_bias: str = "neutral"
    confluence_score: float = 0.5
    facts: list[str] = field(default_factory=list)
    interpretations: list[str] = field(default_factory=list)
    summary: str = ""


class MultiTimeframeAnalyzer:
    """
    멀티 타임프레임 분석기

    1시간, 4시간, 일봉, 주봉 데이터를 분석하여 종합적인 시장 상황을 판단합니다.

    사용 예시:
        analyzer = MultiTimeframeAnalyzer()
        result = await analyzer.analyze()  # settings.trading_ticker 사용
        print(result.overall_bias)
    """

    def __init__(
        self,
        upbit_client: UpbitPublicAPI | None = None,
        calculator: TechnicalIndicatorCalculator | None = None,
    ):
        """
        멀티 타임프레임 분석기 초기화

        Args:
            upbit_client: Upbit Public API 클라이언트 (기본값: 싱글톤)
            calculator: 기술적 지표 계산기 (기본값: 싱글톤)
        """
        self.upbit_client = upbit_client or get_upbit_public_api()
        self.calculator = calculator or get_technical_calculator()

    async def fetch_candle_data(
        self,
        market: str | None = None,
    ) -> dict[str, list[UpbitCandleData]]:
        """
        모든 타임프레임의 캔들 데이터 병렬 조회

        Args:
            market: 마켓 코드 (기본값: settings.trading_ticker)

        Returns:
            dict: 타임프레임별 캔들 데이터
        """
        market = market or settings.trading_ticker
        tasks = [
            self.upbit_client.get_minute_candles(market, unit=60, count=200),
            self.upbit_client.get_minute_candles(market, unit=240, count=200),
            self.upbit_client.get_day_candles(market, count=200),
            self.upbit_client.get_week_candles(market, count=52),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        candle_data: dict[str, list[UpbitCandleData]] = {}

        timeframes = ["1h", "4h", "1d", "1w"]
        for tf, result in zip(timeframes, results, strict=True):
            if isinstance(result, Exception):
                logger.warning(f"{tf} 캔들 데이터 조회 실패: {result}")
                candle_data[tf] = []
            else:
                candle_data[tf] = result

        return candle_data

    def analyze_timeframe(
        self,
        timeframe: str,
        candles: list[UpbitCandleData],
    ) -> TimeframeAnalysis | None:
        """
        단일 타임프레임 분석

        Args:
            timeframe: 타임프레임 식별자
            candles: 캔들 데이터 (최신순)

        Returns:
            TimeframeAnalysis | None: 분석 결과 (데이터 부족 시 None)
        """
        if len(candles) < 50:
            logger.warning(f"{timeframe} 캔들 데이터 부족: {len(candles)}개")
            return None

        # 데이터 추출 (캔들은 이미 최신순)
        closes = [c.trade_price for c in candles]
        highs = [c.high_price for c in candles]
        lows = [c.low_price for c in candles]

        # 기술적 지표 계산
        indicators = self.calculator.calculate_all(closes, highs, lows)

        # 현재가 및 변화율
        current_price = float(closes[0])
        if len(closes) > 1:
            prev_price = float(closes[1])
            price_change_pct = ((current_price - prev_price) / prev_price) * 100
        else:
            price_change_pct = 0.0

        # 추세 판단
        trend, strength = self._determine_trend(indicators, price_change_pct)

        # 핵심 관찰 사항 생성
        key_observation = self._generate_observation(
            timeframe, indicators, trend, strength
        )

        return TimeframeAnalysis(
            timeframe=timeframe,
            trend=trend,
            strength=strength,
            indicators=indicators,
            current_price=current_price,
            price_change_pct=round(price_change_pct, 2),
            key_observation=key_observation,
        )

    def _determine_trend(
        self,
        indicators: IndicatorResult,
        price_change_pct: float,
    ) -> tuple[str, float]:
        """
        추세 방향 및 강도 판단

        여러 지표를 종합하여 추세를 판단합니다.

        Args:
            indicators: 기술적 지표
            price_change_pct: 가격 변화율

        Returns:
            tuple[str, float]: (추세, 강도)
        """
        bullish_signals = 0
        bearish_signals = 0
        total_signals = 6

        # 1. EMA 정렬
        if indicators.ema_alignment == "bullish":
            bullish_signals += 1
        elif indicators.ema_alignment == "bearish":
            bearish_signals += 1

        # 2. MACD
        if indicators.macd_signal == "bullish":
            bullish_signals += 1
        elif indicators.macd_signal == "bearish":
            bearish_signals += 1

        # 3. RSI
        if indicators.rsi_signal == "oversold":
            bullish_signals += 1  # 반등 기대
        elif indicators.rsi_signal == "overbought":
            bearish_signals += 1  # 조정 기대

        # 4. 볼린저 밴드
        if indicators.bb_signal in ["oversold", "lower_zone"]:
            bullish_signals += 1
        elif indicators.bb_signal in ["overbought", "upper_zone"]:
            bearish_signals += 1

        # 5. 가격 변화
        if price_change_pct > 1.0:
            bullish_signals += 1
        elif price_change_pct < -1.0:
            bearish_signals += 1

        # 6. MACD 히스토그램 방향
        if indicators.macd_histogram > 0:
            bullish_signals += 0.5
        elif indicators.macd_histogram < 0:
            bearish_signals += 0.5

        # 추세 결정
        net_signal = bullish_signals - bearish_signals

        if net_signal > 2:
            trend = "bullish"
            strength = min(net_signal / total_signals, 1.0)
        elif net_signal < -2:
            trend = "bearish"
            strength = min(abs(net_signal) / total_signals, 1.0)
        else:
            trend = "sideways"
            strength = 0.3 + (abs(net_signal) / total_signals) * 0.2

        return trend, round(strength, 2)

    def _generate_observation(
        self,
        timeframe: str,
        indicators: IndicatorResult,
        trend: str,
        strength: float,
    ) -> str:
        """
        핵심 관찰 사항 생성

        Args:
            timeframe: 타임프레임
            indicators: 기술적 지표
            trend: 추세
            strength: 강도

        Returns:
            str: 핵심 관찰 사항 (한국어)
        """
        tf_names = {"1h": "1시간봉", "4h": "4시간봉", "1d": "일봉", "1w": "주봉"}
        tf_name = tf_names.get(timeframe, timeframe)

        parts = []

        # 추세
        trend_text = {"bullish": "상승", "bearish": "하락", "sideways": "횡보"}
        parts.append(
            f"{tf_name} {trend_text.get(trend, trend)} 추세 (강도 {strength:.0%})"
        )

        # RSI
        if indicators.rsi_signal != "neutral":
            rsi_text = {"oversold": "과매도", "overbought": "과매수"}
            rsi_label = rsi_text.get(indicators.rsi_signal, "")
            parts.append(f"RSI {indicators.rsi_14:.1f} ({rsi_label})")

        # MACD
        if indicators.macd_signal != "neutral":
            macd_text = {"bullish": "매수", "bearish": "매도"}
            parts.append(f"MACD {macd_text.get(indicators.macd_signal, '')} 신호")

        return ", ".join(parts)

    def calculate_confluence(
        self,
        analyses: dict[str, TimeframeAnalysis],
    ) -> tuple[float, str]:
        """
        타임프레임 합류 점수 계산 (개선 버전)

        모든 타임프레임의 추세가 일치할수록 높은 점수를 부여합니다.
        sideways도 "일관된 방향성"으로 간주하여 점수에 반영합니다.

        Args:
            analyses: 타임프레임별 분석 결과

        Returns:
            tuple[float, str]: (합류 점수, 종합 편향)
        """
        if not analyses:
            return 0.5, "neutral"

        bullish_count = 0.0
        bearish_count = 0.0
        sideways_count = 0.0  # 횡보 추세 카운트 추가
        total_strength = 0.0

        # 타임프레임 가중치 (장기가 더 중요)
        weights = {"1h": 1.0, "4h": 1.5, "1d": 2.0, "1w": 2.5}

        for tf, analysis in analyses.items():
            weight = weights.get(tf, 1.0)
            total_strength += analysis.strength * weight

            if analysis.trend == "bullish":
                bullish_count += weight
            elif analysis.trend == "bearish":
                bearish_count += weight
            else:  # sideways
                sideways_count += weight  # 횡보도 카운트에 포함

        total_weight = sum(weights.get(tf, 1.0) for tf in analyses)

        # 합류 점수 (일치도) - sideways도 "일관된 방향성"으로 간주
        if total_weight > 0:
            dominant = max(bullish_count, bearish_count, sideways_count)
            confluence = dominant / total_weight
        else:
            confluence = 0.5

        # 종합 편향 결정
        net_bias = bullish_count - bearish_count
        avg_strength = total_strength / total_weight if total_weight > 0 else 0.5

        if net_bias > 3 and avg_strength > 0.6:
            overall_bias = "strong_buy"
        elif net_bias > 1.5:
            overall_bias = "buy"
        elif net_bias < -3 and avg_strength > 0.6:
            overall_bias = "strong_sell"
        elif net_bias < -1.5:
            overall_bias = "sell"
        elif sideways_count >= total_weight * 0.7:
            # 70% 이상 sideways면 횡보장으로 판단
            overall_bias = "sideways"
        else:
            overall_bias = "neutral"

        return round(confluence, 2), overall_bias

    def generate_facts_and_interpretations(
        self,
        analyses: dict[str, TimeframeAnalysis],
    ) -> tuple[list[str], list[str]]:
        """
        사실과 해석 분리 (FS-ReasoningAgent 개념)

        Args:
            analyses: 타임프레임별 분석 결과

        Returns:
            tuple[list[str], list[str]]: (사실 목록, 해석 목록)
        """
        facts: list[str] = []
        interpretations: list[str] = []

        tf_names = {"1h": "1시간봉", "4h": "4시간봉", "1d": "일봉", "1w": "주봉"}

        for tf, analysis in analyses.items():
            tf_name = tf_names.get(tf, tf)
            ind = analysis.indicators

            # 사실 (객관적 수치)
            facts.append(f"{tf_name} RSI: {ind.rsi_14:.1f}")
            facts.append(f"{tf_name} MACD 히스토그램: {ind.macd_histogram:.4f}")
            facts.append(f"{tf_name} 볼린저밴드 위치: {ind.bb_percent:.1f}%")
            facts.append(f"{tf_name} EMA 정렬: {ind.ema_alignment}")

        # 해석 (주관적 판단)
        if "1d" in analyses and "1w" in analyses:
            daily = analyses["1d"]
            weekly = analyses["1w"]

            if daily.trend == weekly.trend == "bullish":
                interpretations.append(
                    "일봉과 주봉 모두 상승 추세로 중장기 상승 모멘텀 확인"
                )
            elif daily.trend == weekly.trend == "bearish":
                interpretations.append(
                    "일봉과 주봉 모두 하락 추세로 중장기 하락 압력 존재"
                )
            elif daily.trend != weekly.trend:
                msg = f"일봉({daily.trend})과 주봉({weekly.trend}) "
                msg += "추세 불일치로 단기 변동성 예상"
                interpretations.append(msg)

        if "1h" in analyses:
            hourly = analyses["1h"]
            if hourly.indicators.rsi_signal == "oversold":
                interpretations.append("1시간봉 RSI 과매도로 단기 반등 가능성")
            elif hourly.indicators.rsi_signal == "overbought":
                interpretations.append("1시간봉 RSI 과매수로 단기 조정 가능성")

        if "4h" in analyses:
            four_hour = analyses["4h"]
            if four_hour.indicators.macd_signal == "bullish":
                interpretations.append("4시간봉 MACD 골든크로스로 중기 상승 신호")
            elif four_hour.indicators.macd_signal == "bearish":
                interpretations.append("4시간봉 MACD 데드크로스로 중기 하락 신호")

        return facts, interpretations

    def generate_summary(
        self,
        overall_bias: str,
        confluence_score: float,
        analyses: dict[str, TimeframeAnalysis],
    ) -> str:
        """
        종합 요약 생성

        Args:
            overall_bias: 종합 편향
            confluence_score: 합류 점수
            analyses: 타임프레임별 분석 결과

        Returns:
            str: 종합 요약 (한국어)
        """
        bias_text = {
            "strong_buy": "강한 매수",
            "buy": "매수",
            "neutral": "중립",
            "sell": "매도",
            "strong_sell": "강한 매도",
        }

        parts = [f"종합 편향: {bias_text.get(overall_bias, overall_bias)}"]
        parts.append(f"타임프레임 일치도: {confluence_score:.0%}")

        # 각 타임프레임 추세 요약
        tf_trends = []
        for tf in ["1h", "4h", "1d", "1w"]:
            if tf in analyses:
                trend_kr = {"bullish": "상승", "bearish": "하락", "sideways": "횡보"}
                tf_trends.append(
                    f"{tf}={trend_kr.get(analyses[tf].trend, analyses[tf].trend)}"
                )

        if tf_trends:
            parts.append(f"추세: {', '.join(tf_trends)}")

        return " | ".join(parts)

    async def analyze(
        self,
        market: str | None = None,
    ) -> MultiTimeframeResult:
        """
        멀티 타임프레임 종합 분석 수행

        Args:
            market: 마켓 코드 (기본값: settings.trading_ticker)

        Returns:
            MultiTimeframeResult: 종합 분석 결과
        """
        # 캔들 데이터 조회
        candle_data = await self.fetch_candle_data(market)

        # 각 타임프레임 분석
        analyses: dict[str, TimeframeAnalysis] = {}

        for tf, candles in candle_data.items():
            analysis = self.analyze_timeframe(tf, candles)
            if analysis:
                analyses[tf] = analysis

        if not analyses:
            logger.warning("분석 가능한 타임프레임 데이터가 없습니다")
            return MultiTimeframeResult()

        # 합류 점수 및 종합 편향 계산
        confluence_score, overall_bias = self.calculate_confluence(analyses)

        # 사실/해석 분리
        facts, interpretations = self.generate_facts_and_interpretations(analyses)

        # 종합 요약
        summary = self.generate_summary(overall_bias, confluence_score, analyses)

        return MultiTimeframeResult(
            analyses=analyses,
            overall_bias=overall_bias,
            confluence_score=confluence_score,
            facts=facts,
            interpretations=interpretations,
            summary=summary,
        )


# === 싱글톤 인스턴스 ===
_analyzer: MultiTimeframeAnalyzer | None = None


def get_multi_timeframe_analyzer() -> MultiTimeframeAnalyzer:
    """
    멀티 타임프레임 분석기 싱글톤 반환

    Returns:
        MultiTimeframeAnalyzer: 싱글톤 인스턴스
    """
    global _analyzer
    if _analyzer is None:
        _analyzer = MultiTimeframeAnalyzer()
    return _analyzer
