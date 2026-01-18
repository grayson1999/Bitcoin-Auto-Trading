"""
AI 매매 신호 생성 서비스 (동적 코인 지원 버전)

이 모듈은 Gemini AI를 사용하여 암호화폐 매매 신호를 생성하는 서비스를 제공합니다.
- 동적 코인 설정 (환경변수 TRADING_TICKER, TRADING_CURRENCY)
- 코인 유형별 프롬프트 템플릿 (메이저/밈코인/알트코인)
- 기술적 지표 분석 (RSI, MACD, 볼린저밴드, EMA, ATR)
- 멀티 타임프레임 분석 (1H, 4H, 1D, 1W)
- 과거 신호 성과 피드백 (Verbal Feedback)
"""

import json
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models import MarketData, TradingSignal
from src.models.trading_signal import SignalType
from src.services.ai_client import AIClient, AIClientError, get_ai_client
from src.services.coin_classifier import get_coin_type
from src.services.multi_timeframe_analyzer import (
    MultiTimeframeAnalyzer,
    MultiTimeframeResult,
    get_multi_timeframe_analyzer,
)
from src.services.prompt_templates import (
    PromptConfig,
    get_analysis_prompt,
    get_config_for_coin,
    get_system_instruction,
)
from src.services.signal_performance_tracker import (
    PerformanceSummary,
    SignalPerformanceTracker,
)
from src.services.upbit_client import UpbitError, get_upbit_client

# === 신호 생성 상수 ===
MIN_CONFIDENCE = 0.0  # 최소 신뢰도
MAX_CONFIDENCE = 1.0  # 최대 신뢰도
DEFAULT_CONFIDENCE = 0.5  # 기본 신뢰도 (파싱 실패 시)
MARKET_DATA_HOURS = 168  # 분석에 사용할 시장 데이터 기간 (7일)
COOLDOWN_MINUTES = 5  # 수동 신호 생성 쿨다운 (분)


class SignalGeneratorError(Exception):
    """신호 생성 오류"""

    pass


class SignalGenerator:
    """
    AI 매매 신호 생성 서비스 (동적 코인 지원)

    Gemini AI를 사용하여 설정된 코인의 시장 데이터를 분석하고
    Buy/Hold/Sell 신호를 생성합니다.

    특징:
    - 동적 코인 설정 (환경변수 기반)
    - 코인 유형별 최적화된 프롬프트 템플릿
    - 기술적 지표 분석 (RSI, MACD, 볼린저밴드, EMA, ATR)
    - 멀티 타임프레임 분석 (1H, 4H, 1D, 1W)
    - 과거 신호 성과 피드백

    사용 예시:
        generator = SignalGenerator(db_session)
        signal = await generator.generate_signal()
        print(f"신호: {signal.signal_type}, 신뢰도: {signal.confidence}")
    """

    def __init__(
        self,
        db: AsyncSession,
        ai_client: AIClient | None = None,
        mtf_analyzer: MultiTimeframeAnalyzer | None = None,
    ):
        """
        신호 생성기 초기화

        Args:
            db: SQLAlchemy 비동기 세션
            ai_client: AI 클라이언트 (기본값: 싱글톤 사용)
            mtf_analyzer: 멀티 타임프레임 분석기 (기본값: 싱글톤 사용)
        """
        self.db = db
        self.ai_client = ai_client or get_ai_client()
        self.mtf_analyzer = mtf_analyzer or get_multi_timeframe_analyzer()

        # 동적 코인 설정
        self.ticker = settings.trading_ticker  # 예: "KRW-SOL"
        self.currency = settings.trading_currency  # 예: "SOL"
        self.coin_type = get_coin_type(self.currency)

        # 코인 유형에 따른 프롬프트 설정 (환경변수로 오버라이드 가능)
        base_config = get_config_for_coin(self.coin_type)
        self.prompt_config = PromptConfig(
            stop_loss_pct=settings.signal_stop_loss_pct,
            take_profit_pct=settings.signal_take_profit_pct,
            trailing_stop_pct=settings.signal_trailing_stop_pct,
            breakeven_pct=settings.signal_breakeven_pct,
            min_confidence_buy=base_config.min_confidence_buy,
            min_confluence_buy=base_config.min_confluence_buy,
            rsi_overbought=base_config.rsi_overbought,
            rsi_oversold=base_config.rsi_oversold,
            volatility_tolerance=base_config.volatility_tolerance,
        )

        logger.info(
            f"SignalGenerator 초기화: {self.currency} ({self.coin_type.value}), "
            f"손절: {self.prompt_config.stop_loss_pct*100:.1f}%, "
            f"익절: {self.prompt_config.take_profit_pct*100:.1f}%"
        )

    async def generate_signal(
        self,
        force: bool = False,
    ) -> TradingSignal:
        """
        매매 신호 생성

        기술적 지표, 멀티 타임프레임 분석, 과거 성과 피드백을 종합하여
        AI에게 분석을 요청하고 매매 신호를 생성합니다.

        Args:
            force: 쿨다운 무시 여부 (스케줄러에서는 True)

        Returns:
            TradingSignal: 생성된 신호 (DB에 저장됨)

        Raises:
            SignalGeneratorError: 신호 생성 실패 시
        """
        # 쿨다운 체크 (수동 호출 시)
        if not force:
            await self._check_cooldown()

        # 1. 시장 데이터 수집
        market_data_list = await self._get_recent_market_data()
        if not market_data_list:
            raise SignalGeneratorError("분석할 시장 데이터가 없습니다")

        latest_data = market_data_list[0]
        current_price = float(latest_data.price)

        # 2. 멀티 타임프레임 분석
        try:
            mtf_result = await self.mtf_analyzer.analyze(self.ticker)
        except Exception as e:
            logger.warning(f"멀티 타임프레임 분석 실패: {e}")
            mtf_result = MultiTimeframeResult()

        # 3. 과거 신호 성과 피드백
        try:
            perf_tracker = SignalPerformanceTracker(self.db)
            perf_summary = await perf_tracker.generate_performance_summary(limit=30)
        except Exception as e:
            logger.warning(f"성과 피드백 생성 실패: {e}")
            perf_summary = PerformanceSummary()

        # 4. 잔고 정보 조회
        balance_info = await self._get_balance_info()

        # 5. 프롬프트 생성 (코인 유형별 템플릿 사용)
        system_instruction = get_system_instruction(
            self.currency, self.coin_type, self.prompt_config
        )
        prompt = self._build_enhanced_prompt(
            market_data_list=market_data_list,
            mtf_result=mtf_result,
            perf_summary=perf_summary,
            balance_info=balance_info,
        )

        # 디버그: 생성된 프롬프트 로깅
        logger.info(f"AI 프롬프트 생성 완료 (길이: {len(prompt)}자)")
        logger.debug(f"프롬프트:\n{prompt}")

        # 6. AI 호출
        try:
            response = await self.ai_client.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=0.3,
                max_output_tokens=1024,
            )
        except AIClientError as e:
            logger.error(f"AI 신호 생성 실패: {e}")
            raise SignalGeneratorError(f"AI API 오류: {e}") from e

        # 7. 응답 파싱
        signal_type, confidence, reasoning = self._parse_response(
            response.text,
            balance_info=balance_info,
        )

        # 8. 기술적 지표 스냅샷 생성
        technical_snapshot = self._create_technical_snapshot(mtf_result)

        # 9. DB에 저장
        signal = TradingSignal(
            market_data_id=latest_data.id,
            signal_type=signal_type,
            confidence=Decimal(str(confidence)),
            reasoning=reasoning,
            created_at=datetime.now(UTC),
            model_name=response.model_name,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            price_at_signal=Decimal(str(current_price)),
            technical_snapshot=technical_snapshot,
        )
        self.db.add(signal)
        await self.db.commit()
        await self.db.refresh(signal)

        logger.info(
            f"신호 생성 완료: {signal_type} (신뢰도: {confidence:.2f}, "
            f"합류점수: {mtf_result.confluence_score:.2f})"
        )

        return signal

    async def _check_cooldown(self) -> None:
        """쿨다운 체크"""
        cooldown_threshold = datetime.now(UTC) - timedelta(minutes=COOLDOWN_MINUTES)

        stmt = select(TradingSignal).where(
            TradingSignal.created_at > cooldown_threshold
        )
        result = await self.db.execute(stmt)
        recent_signal = result.scalar_one_or_none()

        if recent_signal:
            raise SignalGeneratorError(
                f"신호 생성 쿨다운 중입니다. {COOLDOWN_MINUTES}분 후에 다시 시도하세요."
            )

    async def _get_recent_market_data(
        self,
        hours: int = MARKET_DATA_HOURS,
    ) -> list[MarketData]:
        """최근 시장 데이터 조회"""
        since = datetime.now(UTC) - timedelta(hours=hours)

        stmt = (
            select(MarketData)
            .where(MarketData.timestamp > since)
            .order_by(desc(MarketData.timestamp))
            .limit(1000)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_balance_info(self) -> dict | None:
        """
        Upbit 잔고 정보 조회 (동적 코인 지원)

        Returns:
            dict | None: 잔고 정보 딕셔너리 또는 None (조회 실패 시)
        """
        try:
            client = get_upbit_client()
            accounts = await client.get_accounts()

            krw_available = Decimal("0")
            coin_available = Decimal("0")
            coin_avg_price = Decimal("0")

            for acc in accounts:
                if acc.currency == "KRW":
                    krw_available = acc.balance
                elif acc.currency == self.currency:
                    coin_available = acc.balance
                    coin_avg_price = acc.avg_buy_price

            # 현재가 조회
            try:
                ticker = await client.get_ticker(self.ticker)
                current_price = ticker.trade_price
            except UpbitError:
                current_price = coin_avg_price

            # 미실현 손익 계산
            coin_value = coin_available * current_price
            total_krw = krw_available + coin_value
            unrealized_pnl = Decimal("0")
            unrealized_pnl_pct = 0.0

            if coin_available > 0 and coin_avg_price > 0:
                unrealized_pnl = (current_price - coin_avg_price) * coin_available
                unrealized_pnl_pct = float(
                    (current_price - coin_avg_price) / coin_avg_price * 100
                )

            return {
                "krw_available": krw_available,
                "coin_available": coin_available,
                "coin_avg_price": coin_avg_price,
                "current_price": current_price,
                "total_krw": total_krw,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
            }

        except UpbitError as e:
            logger.warning(f"잔고 조회 실패: {e.message}")
            return None
        except Exception as e:
            logger.warning(f"잔고 조회 중 오류: {e}")
            return None

    def _format_asset_status(self, balance_info: dict | None) -> str:
        """자산 상태 문자열 생성 (동적 코인 지원)"""
        if balance_info is None:
            return "- 자산 정보 조회 불가 (API 키 미설정 또는 오류)"

        lines = []
        lines.append(f"- KRW 가용 잔고: {float(balance_info['krw_available']):,.0f} KRW")
        lines.append(
            f"- {self.currency} 보유량: {float(balance_info['coin_available']):.4f} {self.currency}"
        )

        if balance_info["coin_available"] > 0:
            lines.append(
                f"- {self.currency} 평균 매수가: {float(balance_info['coin_avg_price']):,.0f} KRW"
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
        lines.append(f"- 손절 기준가: {stop_loss:,.0f} KRW (평균매수가 -{stop_loss_display:.1f}%)")
        lines.append(f"- 현재가와 손절가 차이: {((current - stop_loss) / stop_loss * 100):+.2f}%")

        # 손절 조건 판단
        if pnl_pct <= -stop_loss_display:
            lines.append("")
            lines.append("=" * 50)
            lines.append(f"**[손절 조건 충족] 미실현 손실 {stop_loss_display:.1f}% 초과!**")
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
            lines.append(f"**[경고] 미실현 손실 {warning_threshold:.1f}% 초과 - 추세 확인 후 손절 검토**")

        return "\n".join(lines)

    def _build_enhanced_prompt(
        self,
        market_data_list: list[MarketData],
        mtf_result: MultiTimeframeResult,
        perf_summary: PerformanceSummary,
        balance_info: dict | None = None,
    ) -> str:
        """개선된 분석 프롬프트 생성 (prompt_templates 사용)"""
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
            f"**RSI (14일):** {ind.rsi_14:.1f} ({rsi_status.get(ind.rsi_signal, ind.rsi_signal)})"
        )

        # MACD
        macd_status = {"bullish": "매수 신호", "bearish": "매도 신호", "neutral": "중립"}
        lines.append(
            f"**MACD (12-26-9):** Line={ind.macd_line:.4f}, Signal={ind.signal_line:.4f}, "
            f"Histogram={ind.macd_histogram:.4f} ({macd_status.get(ind.macd_signal, ind.macd_signal)})"
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
            f"**볼린저 밴드 (20일, 2s):** 상단={ind.bb_upper:,.0f}, 중단={ind.bb_middle:,.0f}, "
            f"하단={ind.bb_lower:,.0f}, 위치={ind.bb_percent:.1f}% ({bb_status.get(ind.bb_signal, ind.bb_signal)})"
        )

        # EMA
        ema_status = {"bullish": "정배열", "bearish": "역배열", "mixed": "혼조"}
        lines.append(
            f"**EMA:** 9일={ind.ema_9:,.0f}, 21일={ind.ema_21:,.0f}, 50일={ind.ema_50:,.0f} "
            f"({ema_status.get(ind.ema_alignment, ind.ema_alignment)})"
        )

        # 변동성
        vol_status = {"low": "낮음", "medium": "보통", "high": "높음"}
        lines.append(
            f"**변동성:** ATR(14)={ind.atr_14:.2f}, 수준={vol_status.get(ind.volatility_level, ind.volatility_level)}"
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
        lines.append(f"**타임프레임 합류 점수:** {mtf_result.confluence_score:.2f}/1.00")
        lines.append(
            f"**종합 편향:** {bias_kr.get(mtf_result.overall_bias, mtf_result.overall_bias)}"
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

    def _create_technical_snapshot(self, mtf_result: MultiTimeframeResult) -> str:
        """기술적 지표 스냅샷 생성 (JSON)"""
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

    def _parse_response(
        self,
        text: str,
        balance_info: dict | None = None,
    ) -> tuple[str, float, str]:
        """
        AI 응답 파싱

        JSON 형식의 응답에서 신호, 신뢰도, 근거를 추출합니다.
        """
        # JSON 블록 추출 시도
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = text

        try:
            data = json.loads(json_str)
            signal = data.get("signal", "HOLD").upper()
            confidence = float(data.get("confidence", DEFAULT_CONFIDENCE))
            reasoning_raw = data.get("reasoning", "분석 근거 없음")

            # 신호 타입 검증
            if signal not in [s.value for s in SignalType]:
                signal = SignalType.HOLD.value

            # 신뢰도 범위 검증
            confidence = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, confidence))

            # reasoning 처리
            if isinstance(reasoning_raw, dict):
                reasoning_parts = []

                if "risk_assessment" in reasoning_raw:
                    risk = reasoning_raw["risk_assessment"]
                    if risk.get("stop_loss_triggered"):
                        reasoning_parts.append(
                            f"[손절 트리거] {risk.get('trigger_reason', '손절 조건 충족')}"
                        )
                    pnl_pct = risk.get("unrealized_pnl_pct")
                    if pnl_pct is not None:
                        reasoning_parts.append(f"손익률: {pnl_pct:+.1f}%")

                if "decision_rationale" in reasoning_raw:
                    reasoning_parts.append(reasoning_raw["decision_rationale"])
                elif "interpretation" in reasoning_raw:
                    reasoning_parts.append(reasoning_raw["interpretation"])

                if "technical_summary" in reasoning_raw:
                    tech = reasoning_raw["technical_summary"]
                    tech_parts = []
                    if tech.get("confluence_score") is not None:
                        tech_parts.append(f"합류: {tech['confluence_score']:.2f}")
                    if tech.get("rsi_14") is not None:
                        tech_parts.append(f"RSI: {tech['rsi_14']:.1f}")
                    trends = []
                    for tf in ["1h", "4h", "1d"]:
                        trend_key = f"trend_{tf}"
                        if tech.get(trend_key):
                            trends.append(f"{tf.upper()}={tech[trend_key]}")
                    if trends:
                        tech_parts.append(" ".join(trends))
                    if tech_parts:
                        reasoning_parts.append("지표: " + " / ".join(tech_parts))
                elif "facts" in reasoning_raw and reasoning_raw["facts"]:
                    key_facts = []
                    for fact in reasoning_raw["facts"][:5]:
                        if any(
                            kw in fact for kw in ["RSI", "볼린저", "BB", "합류", "타임프레임"]
                        ):
                            key_facts.append(fact)
                    if key_facts:
                        reasoning_parts.append("지표: " + " / ".join(key_facts[:3]))
                    else:
                        reasoning_parts.append(
                            "근거: " + ", ".join(reasoning_raw["facts"][:3])
                        )

                if "key_factors" in reasoning_raw and reasoning_raw["key_factors"]:
                    reasoning_parts.append(
                        "핵심: " + ", ".join(reasoning_raw["key_factors"])
                    )

                if "risks" in reasoning_raw and reasoning_raw["risks"]:
                    reasoning_parts.append(
                        "위험: " + ", ".join(reasoning_raw["risks"])
                    )

                if "action_levels" in reasoning_raw:
                    levels = reasoning_raw["action_levels"]
                    validated_levels = self._validate_action_levels(levels, balance_info)
                    level_parts = []
                    if validated_levels.get("stop_loss"):
                        level_parts.append(f"손절: {validated_levels['stop_loss']}")
                    if validated_levels.get("take_profit"):
                        level_parts.append(f"익절: {validated_levels['take_profit']}")
                    if level_parts:
                        reasoning_parts.append(" / ".join(level_parts))

                reasoning = " | ".join(reasoning_parts) if reasoning_parts else "분석 근거 없음"
            else:
                reasoning = str(reasoning_raw)

            return signal, confidence, reasoning

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"AI 응답 파싱 실패: {e}, 원본: {text[:200]}")
            return (
                SignalType.HOLD.value,
                DEFAULT_CONFIDENCE,
                f"파싱 실패로 기본 HOLD 신호 생성. 원본: {text[:100]}",
            )

    def _parse_price(self, price_str: str | None) -> float | None:
        """가격 문자열 파싱"""
        if not price_str:
            return None

        try:
            cleaned = re.sub(r"[^\d.]", "", str(price_str))
            if cleaned:
                return float(cleaned)
            return None
        except (ValueError, TypeError):
            return None

    def _validate_action_levels(
        self,
        levels: dict,
        balance_info: dict | None,
    ) -> dict:
        """익절/손절가가 포지션 평균 매수가 기준으로 유효한지 검증"""
        if not balance_info or float(balance_info.get("coin_available", 0)) <= 0:
            return levels

        avg_price = float(balance_info["coin_avg_price"])
        if avg_price <= 0:
            return levels

        validated = dict(levels)

        if levels.get("take_profit"):
            tp = self._parse_price(levels["take_profit"])
            if tp and tp <= avg_price:
                logger.warning(
                    f"익절가({tp:,.0f}원)가 평균매수가({avg_price:,.0f}원)보다 낮음 - 제거"
                )
                validated["take_profit"] = None

        if levels.get("stop_loss"):
            sl = self._parse_price(levels["stop_loss"])
            if sl and sl >= avg_price:
                logger.warning(
                    f"손절가({sl:,.0f}원)가 평균매수가({avg_price:,.0f}원)보다 높음 - 제거"
                )
                validated["stop_loss"] = None

        return validated

    async def get_latest_signal(self) -> TradingSignal | None:
        """최신 신호 조회"""
        stmt = select(TradingSignal).order_by(desc(TradingSignal.created_at)).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_signals(
        self,
        limit: int = 50,
        offset: int = 0,
        signal_type: str | None = None,
    ) -> list[TradingSignal]:
        """신호 목록 조회"""
        stmt = select(TradingSignal).order_by(desc(TradingSignal.created_at))

        if signal_type and signal_type != "all":
            stmt = stmt.where(TradingSignal.signal_type == signal_type.upper())

        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_signals_count(self, signal_type: str | None = None) -> int:
        """신호 총 개수 조회"""
        stmt = select(func.count()).select_from(TradingSignal)

        if signal_type and signal_type != "all":
            stmt = stmt.where(TradingSignal.signal_type == signal_type.upper())

        result = await self.db.execute(stmt)
        return result.scalar() or 0


# === 싱글톤 팩토리 ===
def get_signal_generator(db: AsyncSession) -> SignalGenerator:
    """SignalGenerator 인스턴스 생성"""
    return SignalGenerator(db)
