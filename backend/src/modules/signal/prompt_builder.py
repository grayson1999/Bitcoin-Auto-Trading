"""
신호 생성 프롬프트 빌더 모듈

이 모듈은 AI 매매 신호 생성을 위한 프롬프트 구성을 담당합니다.
- 시장 데이터 포맷
- 기술적 지표 포맷
- 멀티 타임프레임 분석 포맷
- 성과 피드백 포맷
"""

from datetime import UTC, datetime

from src.entities import MarketData
from src.services.multi_timeframe_analyzer import MultiTimeframeResult
from src.services.prompt_templates import PromptConfig, get_analysis_prompt
from src.services.signal_performance_tracker import PerformanceSummary


class SignalPromptBuilder:
    """
    신호 생성 프롬프트 빌더

    AI 신호 생성을 위한 프롬프트를 구성합니다.
    """

    def __init__(self, currency: str, prompt_config: PromptConfig) -> None:
        """
        프롬프트 빌더 초기화

        Args:
            currency: 거래 통화 (예: "BTC", "SOL")
            prompt_config: 프롬프트 설정
        """
        self.currency = currency
        self.prompt_config = prompt_config

    def build_enhanced_prompt(
        self,
        market_data_list: list[MarketData],
        mtf_result: MultiTimeframeResult,
        perf_summary: PerformanceSummary,
        balance_info: dict | None = None,
    ) -> str:
        """
        개선된 분석 프롬프트 생성 (prompt_templates 사용)

        Args:
            market_data_list: 시장 데이터 목록
            mtf_result: 멀티 타임프레임 분석 결과
            perf_summary: 성과 요약
            balance_info: 잔고 정보

        Returns:
            str: 생성된 프롬프트
        """
        latest = market_data_list[0]

        # 24시간 변동률 계산
        if len(market_data_list) > 1:
            oldest = market_data_list[-1]
            price_change_pct = (
                (float(latest.price) - float(oldest.price)) / float(oldest.price) * 100
            )
        else:
            price_change_pct = 0.0

        # 각 섹션 문자열 생성
        asset_status = self._format_asset_status(balance_info)
        risk_check = self._format_risk_check(balance_info)
        technical_indicators = self._format_technical_indicators(mtf_result)
        multi_timeframe_analysis = self._format_multi_timeframe(mtf_result)
        performance_feedback = self._format_performance_feedback(perf_summary)

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
            performance_feedback=performance_feedback,
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

        lines = []

        # RSI
        rsi_status = {"oversold": "과매도", "overbought": "과매수", "neutral": "중립"}
        lines.append(
            f"**RSI (14일):** {ind.rsi_14:.1f} "
            f"({rsi_status.get(ind.rsi_signal, ind.rsi_signal)})"
        )

        # MACD
        macd_status = {
            "bullish": "매수 신호",
            "bearish": "매도 신호",
            "neutral": "중립",
        }
        lines.append(
            f"**MACD (12-26-9):** Line={ind.macd_line:.4f}, "
            f"Signal={ind.signal_line:.4f}, "
            f"Histogram={ind.macd_histogram:.4f} "
            f"({macd_status.get(ind.macd_signal, ind.macd_signal)})"
        )

        # 볼린저 밴드
        bb_status = {
            "overbought": "상단 돌파",
            "oversold": "하단 돌파",
            "upper_zone": "상단 접근",
            "lower_zone": "하단 접근",
            "neutral": "중립",
        }
        lines.append(
            f"**볼린저 밴드 (20일, 2s):** 상단={ind.bb_upper:,.0f}, "
            f"중단={ind.bb_middle:,.0f}, "
            f"하단={ind.bb_lower:,.0f}, 위치={ind.bb_percent:.1f}% "
            f"({bb_status.get(ind.bb_signal, ind.bb_signal)})"
        )

        # EMA
        ema_status = {"bullish": "정배열", "bearish": "역배열", "mixed": "혼조"}
        lines.append(
            f"**EMA:** 9일={ind.ema_9:,.0f}, 21일={ind.ema_21:,.0f}, "
            f"50일={ind.ema_50:,.0f} "
            f"({ema_status.get(ind.ema_alignment, ind.ema_alignment)})"
        )

        # 변동성
        vol_status = {"low": "낮음", "medium": "보통", "high": "높음"}
        lines.append(
            f"**변동성:** ATR(14)={ind.atr_14:.2f}, "
            f"수준={vol_status.get(ind.volatility_level, ind.volatility_level)}"
        )

        return "\n".join(lines)

    def _format_multi_timeframe(self, mtf_result: MultiTimeframeResult) -> str:
        """멀티 타임프레임 분석 문자열 포맷"""
        lines = []

        tf_names = {"1h": "1시간봉", "4h": "4시간봉", "1d": "일봉", "1w": "주봉"}
        trend_kr = {"bullish": "상승", "bearish": "하락", "sideways": "횡보"}

        for tf in ["1h", "4h", "1d", "1w"]:
            if tf in mtf_result.analyses:
                analysis = mtf_result.analyses[tf]
                trend_text = trend_kr.get(analysis.trend, analysis.trend)
                lines.append(
                    f"- **{tf_names[tf]}:** {trend_text} 추세 (강도 {analysis.strength:.0%})"
                )
                lines.append(f"  - {analysis.key_observation}")
            else:
                lines.append(f"- **{tf_names[tf]}:** 데이터 없음")

        # 합류 점수
        bias_kr = {
            "strong_buy": "강한 매수",
            "buy": "매수",
            "neutral": "중립",
            "sell": "매도",
            "strong_sell": "강한 매도",
        }
        lines.append("")
        lines.append(
            f"**타임프레임 합류 점수:** {mtf_result.confluence_score:.2f}/1.00"
        )
        lines.append(
            f"**종합 편향:** "
            f"{bias_kr.get(mtf_result.overall_bias, mtf_result.overall_bias)}"
        )

        return "\n".join(lines)

    def _format_performance_feedback(self, perf_summary: PerformanceSummary) -> str:
        """성과 피드백 포맷"""
        lines = []

        if perf_summary.total_signals == 0:
            return "- 평가된 신호가 없습니다. 첫 분석입니다."

        lines.append(f"**분석 대상:** 최근 {perf_summary.total_signals}개 신호")
        lines.append(
            f"**신호 분포:** 매수 {perf_summary.buy_signals}건, "
            f"매도 {perf_summary.sell_signals}건, 홀드 {perf_summary.hold_signals}건"
        )
        lines.append(f"**매수 정확도:** {perf_summary.buy_accuracy:.1f}%")
        lines.append(f"**매도 정확도:** {perf_summary.sell_accuracy:.1f}%")
        lines.append(f"**평균 24시간 수익률:** {perf_summary.avg_pnl_24h:+.2f}%")

        if perf_summary.feedback_summary:
            lines.append("")
            lines.append(f"**피드백:** {perf_summary.feedback_summary}")

        if perf_summary.improvement_suggestions:
            lines.append("")
            lines.append("**개선 제안:**")
            for suggestion in perf_summary.improvement_suggestions[:3]:
                lines.append(f"- {suggestion}")

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
