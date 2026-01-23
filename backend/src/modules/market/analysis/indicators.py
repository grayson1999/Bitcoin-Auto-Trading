"""
기술적 지표 계산 서비스

순수 Python으로 구현된 기술적 분석 지표 계산기입니다.
외부 라이브러리 의존성 없이 RSI, MACD, 볼린저 밴드, EMA, ATR 등을 계산합니다.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class IndicatorResult:
    """
    기술적 지표 계산 결과

    Attributes:
        rsi_14: RSI (14일) 값 (0-100)
        rsi_signal: RSI 신호 ("oversold", "overbought", "neutral")

        macd_line: MACD 라인 값
        signal_line: 시그널 라인 값
        macd_histogram: MACD 히스토그램 값
        macd_signal: MACD 신호 ("bullish", "bearish", "neutral")

        bb_upper: 볼린저 밴드 상단
        bb_middle: 볼린저 밴드 중간 (SMA)
        bb_lower: 볼린저 밴드 하단
        bb_percent: 현재가의 밴드 내 위치 (0-100%)
        bb_signal: 볼린저 밴드 신호

        ema_9: 9일 지수이동평균
        ema_21: 21일 지수이동평균
        ema_50: 50일 지수이동평균
        ema_alignment: EMA 정렬 상태 ("bullish", "bearish", "mixed")

        atr_14: ATR (14일) 값
        price_std_20: 20일 가격 표준편차
        volatility_level: 변동성 수준 ("low", "medium", "high")
    """

    # RSI
    rsi_14: float
    rsi_signal: str

    # MACD
    macd_line: float
    signal_line: float
    macd_histogram: float
    macd_signal: str

    # 볼린저 밴드
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_percent: float
    bb_signal: str

    # EMA
    ema_9: float
    ema_21: float
    ema_50: float
    ema_alignment: str

    # 변동성
    atr_14: float
    price_std_20: float
    volatility_level: str


class TechnicalIndicatorCalculator:
    """
    기술적 지표 계산기

    캔들 데이터로부터 다양한 기술적 지표를 계산합니다.

    사용 예시:
        calculator = TechnicalIndicatorCalculator()
        closes = [Decimal("3000"), Decimal("3050"), ...]
        rsi = calculator.calculate_rsi(closes)
    """

    def calculate_rsi(
        self,
        closes: list[Decimal],
        period: int = 14,
    ) -> tuple[float, str]:
        """
        RSI (Relative Strength Index) 계산

        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss

        Args:
            closes: 종가 리스트 (최신순, 즉 closes[0]이 가장 최신)
            period: 계산 기간 (기본값: 14)

        Returns:
            tuple[float, str]: (RSI 값, 신호)
            - oversold: RSI < 30 (과매도)
            - overbought: RSI > 70 (과매수)
            - neutral: 그 외
        """
        if len(closes) < period + 1:
            return 50.0, "neutral"

        # 최신순 데이터를 오래된순으로 변환
        closes_asc = list(reversed(closes))

        gains: list[float] = []
        losses: list[float] = []

        for i in range(1, len(closes_asc)):
            change = float(closes_asc[i] - closes_asc[i - 1])
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        if len(gains) < period:
            return 50.0, "neutral"

        # 초기 평균 (SMA 방식)
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        # Wilder's Smoothing (EMA 방식)
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        # 신호 결정
        if rsi < 30:
            signal = "oversold"
        elif rsi > 70:
            signal = "overbought"
        else:
            signal = "neutral"

        return round(rsi, 2), signal

    def calculate_ema(
        self,
        values: list[Decimal],
        period: int,
    ) -> float:
        """
        EMA (Exponential Moving Average) 계산

        EMA = (현재가 - 이전 EMA) * multiplier + 이전 EMA
        multiplier = 2 / (period + 1)

        Args:
            values: 가격 리스트 (최신순)
            period: EMA 기간

        Returns:
            float: 현재 EMA 값
        """
        if len(values) < period:
            return float(values[0]) if values else 0.0

        # 최신순 데이터를 오래된순으로 변환
        values_asc = list(reversed(values))

        multiplier = 2 / (period + 1)

        # 초기 EMA = SMA
        ema = sum(float(v) for v in values_asc[:period]) / period

        # EMA 계산
        for i in range(period, len(values_asc)):
            ema = (float(values_asc[i]) - ema) * multiplier + ema

        return round(ema, 4)

    def calculate_macd(
        self,
        closes: list[Decimal],
        fast: int = 12,
        slow: int = 26,
        signal_period: int = 9,
    ) -> tuple[float, float, float, str]:
        """
        MACD (Moving Average Convergence Divergence) 계산

        MACD Line = EMA(fast) - EMA(slow)
        Signal Line = EMA(signal_period) of MACD Line
        Histogram = MACD Line - Signal Line

        Args:
            closes: 종가 리스트 (최신순)
            fast: 빠른 EMA 기간 (기본값: 12)
            slow: 느린 EMA 기간 (기본값: 26)
            signal_period: 시그널 라인 EMA 기간 (기본값: 9)

        Returns:
            tuple[float, float, float, str]: (MACD Line, Signal Line, Histogram, 신호)
        """
        if len(closes) < slow + signal_period:
            return 0.0, 0.0, 0.0, "neutral"

        # 최신순 데이터를 오래된순으로 변환
        closes_asc = list(reversed(closes))

        # EMA 계산
        multiplier_fast = 2 / (fast + 1)
        multiplier_slow = 2 / (slow + 1)

        # 초기 EMA (SMA)
        ema_fast = sum(float(c) for c in closes_asc[:fast]) / fast
        ema_slow = sum(float(c) for c in closes_asc[:slow]) / slow

        # MACD 라인 계산을 위해 두 EMA 모두 업데이트
        macd_values: list[float] = []

        for i in range(slow, len(closes_asc)):
            # EMA 업데이트
            if i >= fast:
                ema_fast = (
                    float(closes_asc[i]) - ema_fast
                ) * multiplier_fast + ema_fast
            if i >= slow:
                ema_slow = (
                    float(closes_asc[i]) - ema_slow
                ) * multiplier_slow + ema_slow

            macd_line = ema_fast - ema_slow
            macd_values.append(macd_line)

        if len(macd_values) < signal_period:
            return 0.0, 0.0, 0.0, "neutral"

        # Signal Line 계산 (MACD의 EMA)
        multiplier_signal = 2 / (signal_period + 1)
        signal_line = sum(macd_values[:signal_period]) / signal_period

        for i in range(signal_period, len(macd_values)):
            signal_line = (
                macd_values[i] - signal_line
            ) * multiplier_signal + signal_line

        # 최신 값
        current_macd = macd_values[-1]
        histogram = current_macd - signal_line

        # 신호 결정
        if histogram > 0:
            signal = "bullish"
        elif histogram < 0:
            signal = "bearish"
        else:
            signal = "neutral"

        return (
            round(current_macd, 4),
            round(signal_line, 4),
            round(histogram, 4),
            signal,
        )

    def calculate_bollinger_bands(
        self,
        closes: list[Decimal],
        period: int = 20,
        std_dev: float = 2.0,
    ) -> tuple[float, float, float, float, str]:
        """
        볼린저 밴드 계산

        Middle Band = SMA(period)
        Upper Band = Middle + (std_dev * StdDev)
        Lower Band = Middle - (std_dev * StdDev)
        %B = (Price - Lower) / (Upper - Lower) * 100

        Args:
            closes: 종가 리스트 (최신순)
            period: SMA 기간 (기본값: 20)
            std_dev: 표준편차 배수 (기본값: 2.0)

        Returns:
            tuple: (Upper, Middle, Lower, %B, 신호)
        """
        if len(closes) < period:
            current_price = float(closes[0]) if closes else 0.0
            return current_price, current_price, current_price, 50.0, "neutral"

        # 최근 period개의 종가 사용
        recent = [float(c) for c in closes[:period]]

        # Middle Band (SMA)
        middle = sum(recent) / period

        # Standard Deviation
        variance = sum((x - middle) ** 2 for x in recent) / period
        std = variance**0.5

        # Upper/Lower Bands
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)

        # %B 계산
        current_price = recent[0]
        if upper - lower > 0:
            percent_b = ((current_price - lower) / (upper - lower)) * 100
        else:
            percent_b = 50.0

        # 신호 결정
        if percent_b > 100:
            signal = "overbought"
        elif percent_b < 0:
            signal = "oversold"
        elif percent_b > 80:
            signal = "upper_zone"
        elif percent_b < 20:
            signal = "lower_zone"
        else:
            signal = "neutral"

        return (
            round(upper, 2),
            round(middle, 2),
            round(lower, 2),
            round(percent_b, 2),
            signal,
        )

    def calculate_atr(
        self,
        highs: list[Decimal],
        lows: list[Decimal],
        closes: list[Decimal],
        period: int = 14,
    ) -> float:
        """
        ATR (Average True Range) 계산

        True Range = max(
            High - Low,
            abs(High - Previous Close),
            abs(Low - Previous Close)
        )
        ATR = Smoothed Average of True Range

        Args:
            highs: 고가 리스트 (최신순)
            lows: 저가 리스트 (최신순)
            closes: 종가 리스트 (최신순)
            period: ATR 기간 (기본값: 14)

        Returns:
            float: ATR 값
        """
        if len(closes) < period + 1:
            return 0.0

        # 최신순 데이터를 오래된순으로 변환
        highs_asc = list(reversed(highs))
        lows_asc = list(reversed(lows))
        closes_asc = list(reversed(closes))

        true_ranges: list[float] = []
        for i in range(1, len(closes_asc)):
            high = float(highs_asc[i])
            low = float(lows_asc[i])
            prev_close = float(closes_asc[i - 1])

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close),
            )
            true_ranges.append(tr)

        if len(true_ranges) < period:
            return 0.0

        # 초기 ATR (SMA)
        atr = sum(true_ranges[:period]) / period

        # Wilder's Smoothing
        for i in range(period, len(true_ranges)):
            atr = (atr * (period - 1) + true_ranges[i]) / period

        return round(atr, 4)

    def calculate_price_std(
        self,
        closes: list[Decimal],
        period: int = 20,
    ) -> float:
        """
        가격 표준편차 계산

        Args:
            closes: 종가 리스트 (최신순)
            period: 계산 기간 (기본값: 20)

        Returns:
            float: 표준편차 값
        """
        if len(closes) < period:
            return 0.0

        recent = [float(c) for c in closes[:period]]
        mean = sum(recent) / period
        variance = sum((x - mean) ** 2 for x in recent) / period

        return round(variance**0.5, 4)

    def calculate_ema_alignment(
        self,
        ema_9: float,
        ema_21: float,
        ema_50: float,
        current_price: float,
    ) -> str:
        """
        EMA 정렬 상태 판단

        정배열: 현재가 > EMA9 > EMA21 > EMA50 (상승 추세)
        역배열: 현재가 < EMA9 < EMA21 < EMA50 (하락 추세)
        혼조: 그 외

        Args:
            ema_9: 9일 EMA
            ema_21: 21일 EMA
            ema_50: 50일 EMA
            current_price: 현재가

        Returns:
            str: "bullish", "bearish", "mixed"
        """
        if current_price > ema_9 > ema_21 > ema_50:
            return "bullish"
        elif current_price < ema_9 < ema_21 < ema_50:
            return "bearish"
        else:
            return "mixed"

    def determine_volatility_level(
        self,
        atr: float,
        current_price: float,
        historical_atr_avg: float | None = None,
    ) -> str:
        """
        변동성 수준 판단

        ATR을 현재가 대비 비율로 환산하여 판단합니다.

        Args:
            atr: ATR 값
            current_price: 현재가
            historical_atr_avg: 과거 평균 ATR (없으면 비율 기반 판단)

        Returns:
            str: "low", "medium", "high"
        """
        if current_price <= 0:
            return "medium"

        atr_ratio = (atr / current_price) * 100  # ATR 비율 (%)

        # 일반적인 기준 (암호화폐 기준)
        if atr_ratio < 2.0:
            return "low"
        elif atr_ratio < 5.0:
            return "medium"
        else:
            return "high"

    def calculate_all(
        self,
        closes: list[Decimal],
        highs: list[Decimal],
        lows: list[Decimal],
    ) -> IndicatorResult:
        """
        모든 기술적 지표 계산

        Args:
            closes: 종가 리스트 (최신순)
            highs: 고가 리스트 (최신순)
            lows: 저가 리스트 (최신순)

        Returns:
            IndicatorResult: 모든 지표가 포함된 결과 객체
        """
        current_price = float(closes[0]) if closes else 0.0

        # RSI
        rsi_14, rsi_signal = self.calculate_rsi(closes, 14)

        # MACD
        macd_line, signal_line, macd_histogram, macd_signal = self.calculate_macd(
            closes
        )

        # 볼린저 밴드
        bb_upper, bb_middle, bb_lower, bb_percent, bb_signal = (
            self.calculate_bollinger_bands(closes)
        )

        # EMA
        ema_9 = self.calculate_ema(closes, 9)
        ema_21 = self.calculate_ema(closes, 21)
        ema_50 = self.calculate_ema(closes, 50)
        ema_alignment = self.calculate_ema_alignment(
            ema_9, ema_21, ema_50, current_price
        )

        # 변동성 지표
        atr_14 = self.calculate_atr(highs, lows, closes, 14)
        price_std_20 = self.calculate_price_std(closes, 20)
        volatility_level = self.determine_volatility_level(atr_14, current_price)

        return IndicatorResult(
            rsi_14=rsi_14,
            rsi_signal=rsi_signal,
            macd_line=macd_line,
            signal_line=signal_line,
            macd_histogram=macd_histogram,
            macd_signal=macd_signal,
            bb_upper=bb_upper,
            bb_middle=bb_middle,
            bb_lower=bb_lower,
            bb_percent=bb_percent,
            bb_signal=bb_signal,
            ema_9=ema_9,
            ema_21=ema_21,
            ema_50=ema_50,
            ema_alignment=ema_alignment,
            atr_14=atr_14,
            price_std_20=price_std_20,
            volatility_level=volatility_level,
        )


# === 싱글톤 인스턴스 ===
_calculator: TechnicalIndicatorCalculator | None = None


def get_technical_calculator() -> TechnicalIndicatorCalculator:
    """
    기술적 지표 계산기 싱글톤 반환

    Returns:
        TechnicalIndicatorCalculator: 싱글톤 인스턴스
    """
    global _calculator
    if _calculator is None:
        _calculator = TechnicalIndicatorCalculator()
    return _calculator
