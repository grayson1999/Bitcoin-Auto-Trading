"""
신호 생성 프롬프트 빌더 모듈

이 모듈은 AI 매매 신호 생성을 위한 프롬프트 구성을 담당합니다.
- 시장 데이터 포맷
- 기술적 지표 포맷
- 멀티 타임프레임 분석 포맷
"""

from datetime import datetime

from src.clients.sentiment import FearGreedData
from src.entities import MarketData
from src.modules.market import MultiTimeframeResult
from src.modules.signal.classifier import CoinType
from src.modules.signal.prompt.indicator_status import (
    BB_STATUS_KO,
    BIAS_STATUS_KO,
    EMA_STATUS_KO,
    MACD_STATUS_KO,
    RSI_STATUS_KO,
    TIMEFRAME_NAMES_KO,
    TREND_STATUS_KO,
    VOLATILITY_STATUS_KO,
    get_status_ko,
)
from src.modules.signal.prompt.templates import PromptConfig, get_analysis_prompt
from src.utils import UTC


class SignalPromptBuilder:
    """
    신호 생성 프롬프트 빌더

    AI 신호 생성을 위한 프롬프트를 구성합니다.
    """

    def __init__(
        self,
        currency: str,
        prompt_config: PromptConfig,
        coin_type: CoinType | None = None,
    ) -> None:
        """
        프롬프트 빌더 초기화

        Args:
            currency: 거래 통화 (예: "BTC", "SOL")
            prompt_config: 프롬프트 설정
            coin_type: 코인 유형 (Fear & Greed 활용 가이드용)
        """
        self.currency = currency
        self.prompt_config = prompt_config
        self.coin_type = coin_type

    def build_enhanced_prompt(
        self,
        sampled_data: dict[str, list[MarketData]],
        mtf_result: MultiTimeframeResult,
        balance_info: dict | None = None,
        performance_summary: str = "",
        fear_greed: FearGreedData | None = None,
    ) -> str:
        """
        개선된 분석 프롬프트 생성 (prompt_templates 사용, 샘플링된 데이터)

        Args:
            sampled_data: 샘플링된 시장 데이터 {"long_term": [...], "mid_term": [...], "short_term": [...]}
            mtf_result: 멀티 타임프레임 분석 결과
            balance_info: 잔고 정보
            performance_summary: 성과 피드백 문자열 (AI 프롬프트에 포함)
            fear_greed: Fear & Greed Index 데이터 (BTC 기반 시장 심리 지표)

        Returns:
            str: 생성된 프롬프트
        """
        # 모든 시간대 데이터를 합쳐서 최신/최고 데이터 추출
        all_data: list[MarketData] = []
        for period_data in sampled_data.values():
            all_data.extend(period_data)

        if not all_data:
            raise ValueError("샘플링된 데이터가 없습니다")

        # timestamp 기준으로 정렬 (내림차순 - 최신이 먼저)
        all_data.sort(key=lambda x: x.timestamp, reverse=True)
        latest = all_data[0]

        # 24시간 변동률 계산 (mid_term 데이터의 가장 오래된 것과 비교)
        mid_term_data = sampled_data.get("mid_term", [])
        if mid_term_data:
            oldest_mid = min(mid_term_data, key=lambda x: x.timestamp)
            price_change_pct = (
                (float(latest.price) - float(oldest_mid.price))
                / float(oldest_mid.price)
                * 100
            )
        else:
            price_change_pct = 0.0

        # 각 섹션 문자열 생성
        asset_status = self._format_asset_status(balance_info)
        risk_check = self._format_risk_check(balance_info)
        technical_indicators = self._format_technical_indicators(mtf_result)
        multi_timeframe_analysis = self._format_multi_timeframe(mtf_result)
        sentiment_section = self._format_sentiment(fear_greed)

        return get_analysis_prompt(
            currency=self.currency,
            config=self.prompt_config,
            timestamp=latest.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
            current_price=float(latest.price),
            price_change_pct=price_change_pct,
            asset_status=asset_status,
            risk_check=risk_check,
            technical_indicators=technical_indicators,
            multi_timeframe_analysis=multi_timeframe_analysis,
            performance_summary=performance_summary,
            sentiment_section=sentiment_section,
        )

    def _format_asset_status(self, balance_info: dict | None) -> str:
        """자산 상태 문자열 생성 (동적 코인 지원)"""
        if balance_info is None:
            return "- 자산 정보 조회 불가 (API 키 미설정 또는 오류)"

        lines = []
        lines.append(
            f"- KRW 가용 잔고: {float(balance_info['krw_available']):,.0f} KRW"
        )
        lines.append(
            f"- {self.currency} 보유량: "
            f"{float(balance_info['coin_available']):.4f} {self.currency}"
        )

        if balance_info["coin_available"] > 0:
            lines.append(
                f"- {self.currency} 평균 매수가: "
                f"{float(balance_info['coin_avg_price']):,.0f} KRW"
            )
            lines.append(
                f"- 미실현 손익: {float(balance_info['unrealized_pnl']):+,.0f} KRW "
                f"({balance_info['unrealized_pnl_pct']:+.2f}%)"
            )

        lines.append(f"- 총 평가금액: {float(balance_info['total_krw']):,.0f} KRW")

        return "\n".join(lines)

    def _format_risk_check(self, balance_info: dict | None) -> str:
        """손절 조건 체크 결과 포맷 (동적 손절 비율 사용)"""
        if not balance_info or float(balance_info.get("coin_available", 0)) <= 0:
            return "- 포지션 없음: 손절 체크 해당 없음"

        pnl_pct = balance_info["unrealized_pnl_pct"]
        current = float(balance_info["current_price"])
        avg = float(balance_info["coin_avg_price"])
        stop_loss_pct = self.prompt_config.stop_loss_pct
        stop_loss = avg * (1 - stop_loss_pct)
        stop_loss_display = stop_loss_pct * 100

        lines = [f"- 미실현 손익률: {pnl_pct:+.2f}%"]
        lines.append(
            f"- 손절 기준가: {stop_loss:,.0f} KRW (평균매수가 -{stop_loss_display:.1f}%)"
        )
        lines.append(
            f"- 현재가와 손절가 차이: {((current - stop_loss) / stop_loss * 100):+.2f}%"
        )

        # 손절 조건 판단
        if pnl_pct <= -stop_loss_display:
            lines.append("")
            lines.append("=" * 50)
            lines.append(
                f"**[손절 조건 충족] 미실현 손실 {stop_loss_display:.1f}% 초과!**"
            )
            lines.append("-> 즉시 SELL 신호 생성 필수 (신뢰도 0.9)")
            lines.append("=" * 50)
        elif current <= stop_loss:
            lines.append("")
            lines.append("=" * 50)
            lines.append("**[손절 조건 충족] 현재가 < 손절가!**")
            lines.append("-> 즉시 SELL 신호 생성 필수 (신뢰도 0.9)")
            lines.append("=" * 50)
        elif pnl_pct <= -(stop_loss_display * 0.7):
            warning_threshold = stop_loss_display * 0.7
            lines.append("")
            lines.append(
                f"**[경고] 미실현 손실 {warning_threshold:.1f}% 초과 - 추세 확인 후 손절 검토**"
            )

        return "\n".join(lines)

    def _format_technical_indicators(self, mtf_result: MultiTimeframeResult) -> str:
        """기술적 지표 문자열 포맷"""
        if "1d" not in mtf_result.analyses:
            return "- 기술적 지표 데이터 없음"

        daily = mtf_result.analyses["1d"]
        ind = daily.indicators

        lines = [
            f"**RSI (14일):** {ind.rsi_14:.1f} "
            f"({get_status_ko(RSI_STATUS_KO, ind.rsi_signal)})",
            f"**MACD (12-26-9):** Line={ind.macd_line:.4f}, "
            f"Signal={ind.signal_line:.4f}, "
            f"Histogram={ind.macd_histogram:.4f} "
            f"({get_status_ko(MACD_STATUS_KO, ind.macd_signal)})",
            f"**볼린저 밴드 (20일, 2s):** 상단={ind.bb_upper:,.0f}, "
            f"중단={ind.bb_middle:,.0f}, "
            f"하단={ind.bb_lower:,.0f}, 위치={ind.bb_percent:.1f}% "
            f"({get_status_ko(BB_STATUS_KO, ind.bb_signal)})",
            f"**EMA:** 9일={ind.ema_9:,.0f}, 21일={ind.ema_21:,.0f}, "
            f"50일={ind.ema_50:,.0f} "
            f"({get_status_ko(EMA_STATUS_KO, ind.ema_alignment)})",
            f"**변동성:** ATR(14)={ind.atr_14:.2f}, "
            f"수준={get_status_ko(VOLATILITY_STATUS_KO, ind.volatility_level)}",
        ]

        return "\n".join(lines)

    def _format_sentiment(self, fear_greed: FearGreedData | None) -> str:
        """
        시장 심리 지표 포맷 (BTC Fear & Greed Index)

        코인 유형에 따라 다른 활용 가이드를 제공합니다:
        - 메이저 코인: BTC와 상관관계 높음 → 적극 활용
        - 알트코인: BTC와 상관관계 중간 → 참고용
        - 밈코인: BTC와 상관관계 낮음 → 배경 정보로만

        Args:
            fear_greed: Fear & Greed Index 데이터 (None이면 조회 실패)

        Returns:
            str: 포맷된 시장 심리 지표 문자열
        """
        if fear_greed is None:
            return ""

        lines = [
            "### 시장 심리 지표 (BTC 기준)",
            f"- Fear & Greed Index: {fear_greed.value}/100 ({fear_greed.classification_ko})",
            f"- 측정 시각: {fear_greed.timestamp.strftime('%Y-%m-%d %H:%M UTC')}",
        ]

        # 극단값 경고 및 코인 유형별 가이드
        if fear_greed.is_extreme_fear:
            lines.append("")
            lines.append("**[BTC 시장 극도의 공포 구간]**")
            if self.coin_type == CoinType.MAJOR:
                lines.append("- 메이저 코인은 BTC와 상관관계 높음")
                lines.append("- 역발상 매수 기회 적극 검토 (기술적 바닥 확인 필수)")
            elif self.coin_type == CoinType.MEMECOIN:
                lines.append("- 밈코인은 BTC와 상관관계 낮음")
                lines.append("- 배경 정보로만 참고, 거래량/모멘텀 우선")
            else:  # ALTCOIN
                lines.append("- 알트코인은 BTC와 상관관계 중간")
                lines.append("- 참고 지표로 활용, 기술적 지표 우선")

        elif fear_greed.is_extreme_greed:
            lines.append("")
            lines.append("**[BTC 시장 극도의 탐욕 구간]**")
            if self.coin_type == CoinType.MAJOR:
                lines.append("- 메이저 코인은 BTC와 상관관계 높음")
                lines.append("- 시장 과열 주의, 익절 적극 검토")
            elif self.coin_type == CoinType.MEMECOIN:
                lines.append("- 밈코인은 BTC와 상관관계 낮음")
                lines.append("- 배경 정보로만 참고, 거래량/모멘텀 우선")
            else:  # ALTCOIN
                lines.append("- 알트코인은 BTC와 상관관계 중간")
                lines.append("- 참고 지표로 활용, 신규 매수 신중하게")

        lines.append("")
        return "\n".join(lines)

    def _format_multi_timeframe(self, mtf_result: MultiTimeframeResult) -> str:
        """멀티 타임프레임 분석 문자열 포맷"""
        lines = []

        for tf in ["1h", "4h", "1d", "1w"]:
            tf_name = get_status_ko(TIMEFRAME_NAMES_KO, tf)
            if tf in mtf_result.analyses:
                analysis = mtf_result.analyses[tf]
                trend_text = get_status_ko(TREND_STATUS_KO, analysis.trend)
                lines.append(
                    f"- **{tf_name}:** {trend_text} 추세 (강도 {analysis.strength:.0%})"
                )
                lines.append(f"  - {analysis.key_observation}")
            else:
                lines.append(f"- **{tf_name}:** 데이터 없음")

        lines.append("")
        lines.append(
            f"**타임프레임 합류 점수:** {mtf_result.confluence_score:.2f}/1.00"
        )
        lines.append(
            f"**종합 편향:** {get_status_ko(BIAS_STATUS_KO, mtf_result.overall_bias)}"
        )

        return "\n".join(lines)

    def create_technical_snapshot(self, mtf_result: MultiTimeframeResult) -> str:
        """
        기술적 지표 스냅샷 생성 (JSON)

        Args:
            mtf_result: 멀티 타임프레임 분석 결과

        Returns:
            str: JSON 문자열
        """
        import json

        snapshot = {
            "timestamp": datetime.now(UTC).isoformat(),
            "confluence_score": mtf_result.confluence_score,
            "overall_bias": mtf_result.overall_bias,
            "timeframes": {},
        }

        for tf, analysis in mtf_result.analyses.items():
            snapshot["timeframes"][tf] = {
                "trend": analysis.trend,
                "strength": analysis.strength,
                "indicators": {
                    "rsi_14": analysis.indicators.rsi_14,
                    "macd_signal": analysis.indicators.macd_signal,
                    "bb_percent": analysis.indicators.bb_percent,
                    "ema_alignment": analysis.indicators.ema_alignment,
                    "volatility_level": analysis.indicators.volatility_level,
                },
            }

        return json.dumps(snapshot, ensure_ascii=False)
