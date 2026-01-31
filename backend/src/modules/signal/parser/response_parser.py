"""
신호 응답 파서 모듈 v2.1 (균형 버전)

이 모듈은 AI 응답 파싱을 담당합니다.
- JSON 파싱
- action_score 기반 신호 결정 (v2.1 균형 버전)
- 시장 레짐 파싱 (참고용, 차단 없음)
- 근거(reasoning) 포맷팅

v2.1 변경사항:
- 임계값 완화: 0.3 → 0.2
- 레짐 기반 차단 로직 제거 (AI 판단 존중)
"""

import json
import re
from dataclasses import dataclass

from loguru import logger

from src.config.constants import (
    SIGNAL_DEFAULT_CONFIDENCE,
    SIGNAL_MAX_CONFIDENCE,
    SIGNAL_MIN_CONFIDENCE,
)
from src.entities.trading_signal import SignalType

# action_score 임계값 상수 (v2 균형 버전: 0.3 → 0.2로 완화)
ACTION_SCORE_BUY_THRESHOLD = 0.2
ACTION_SCORE_SELL_THRESHOLD = -0.2
ACTION_SCORE_STOP_LOSS = -0.95  # 손절 신호 임계값


@dataclass
class ParsedSignal:
    """파싱된 신호"""

    signal_type: str
    confidence: float
    reasoning: str
    market_regime: str | None = None
    action_score: float | None = None


class SignalResponseParser:
    """
    신호 응답 파서

    AI 응답에서 매매 신호 정보를 추출합니다.
    """

    def parse_response(
        self,
        text: str,
        balance_info: dict | None = None,
    ) -> ParsedSignal:
        """
        AI 응답 파싱 (v2 - action_score 기반)

        JSON 형식의 응답에서 action_score를 기반으로 신호를 결정합니다.

        Args:
            text: AI 응답 텍스트
            balance_info: 잔고 정보

        Returns:
            ParsedSignal: 파싱된 신호 정보
        """
        # JSON 블록 추출 시도
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        json_str = json_match.group(1) if json_match else text

        try:
            data = json.loads(json_str)

            # v2: action_score 기반 신호 결정
            action_score = data.get("action_score")
            market_regime = data.get("market_regime", "SIDEWAYS").upper()

            if action_score is not None:
                # action_score 범위 검증 (-1.0 ~ 1.0)
                action_score = max(-1.0, min(1.0, float(action_score)))

                # action_score 기반 신호 결정
                signal = self._determine_signal_from_score(action_score, market_regime)

                # confidence = |action_score| (action_score의 절대값을 신뢰도로 사용)
                confidence = abs(action_score)

                logger.info(
                    f"action_score 기반 신호: {signal} "
                    f"(score={action_score:.2f}, regime={market_regime})"
                )
            else:
                # fallback: 기존 방식
                signal = data.get("signal", "HOLD").upper().strip()
                confidence = float(data.get("confidence", SIGNAL_DEFAULT_CONFIDENCE))
                action_score = None

            # 신호 타입 검증
            if signal not in [s.value for s in SignalType]:
                signal = SignalType.HOLD.value

            # 신뢰도 범위 검증
            confidence = max(
                SIGNAL_MIN_CONFIDENCE, min(SIGNAL_MAX_CONFIDENCE, confidence)
            )

            # reasoning 처리 (구조화된 포맷)
            reasoning_raw = data.get("reasoning", "분석 근거 없음")

            # 포지션 없을 때 SELL 신호 차단 (v2.1)
            if signal == "SELL" and balance_info:
                coin_available = float(balance_info.get("coin_available", 0))
                if coin_available <= 0:
                    logger.warning(
                        f"포지션 없음 - SELL 신호 차단 (score={action_score}) → HOLD"
                    )
                    signal = "HOLD"
                    # reasoning에 차단 사유 추가
                    if isinstance(reasoning_raw, dict):
                        reasoning_raw["position_blocked"] = "잔고 부족으로 HOLD 처리"
            if isinstance(reasoning_raw, dict):
                reasoning = self._format_reasoning_v2(
                    reasoning_raw, balance_info, market_regime, action_score
                )
            else:
                reasoning = str(reasoning_raw)

            return ParsedSignal(
                signal_type=signal,
                confidence=confidence,
                reasoning=reasoning,
                market_regime=market_regime,
                action_score=action_score,
            )

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"AI 응답 파싱 실패: {e}, 원본: {text[:200]}")
            return ParsedSignal(
                signal_type=SignalType.HOLD.value,
                confidence=SIGNAL_DEFAULT_CONFIDENCE,
                reasoning=f"파싱 실패로 기본 HOLD 신호 생성. 원본: {text[:100]}",
            )

    def _determine_signal_from_score(
        self,
        action_score: float,
        market_regime: str,
    ) -> str:
        """
        action_score 기반으로 신호 결정 (v2 균형 버전)

        v2 변경사항:
        - 레짐 기반 차단 로직 제거 (AI가 레짐을 참고하여 판단)
        - 임계값 완화: |score| < 0.2 → HOLD (기존 0.3)
        - score >= 0.2 → BUY
        - score <= -0.2 → SELL
        """
        # 임계값 기반 신호 결정 (레짐 차단 없음)
        if action_score >= ACTION_SCORE_BUY_THRESHOLD:
            # BEARISH에서 BUY는 차단하지 않음 (AI가 판단)
            if market_regime == "BEARISH":
                logger.info(
                    f"BEARISH 레짐에서 BUY 신호 허용 (score={action_score:.2f}) - AI 판단 존중"
                )
            return "BUY"
        elif action_score <= ACTION_SCORE_SELL_THRESHOLD:
            # BULLISH에서 SELL도 차단하지 않음 (손절/익절 가능)
            if market_regime == "BULLISH" and action_score > ACTION_SCORE_STOP_LOSS:
                logger.info(
                    f"BULLISH 레짐에서 SELL 신호 허용 (score={action_score:.2f}) - 익절/전략적 매도"
                )
            return "SELL"
        else:
            return "HOLD"  # 불확실 → HOLD

    def _format_reasoning_v2(
        self,
        reasoning_raw: dict,
        balance_info: dict | None,
        market_regime: str | None = None,
        action_score: float | None = None,
    ) -> str:
        """
        reasoning을 v2 형식으로 포맷팅 (레짐 + action_score 포함)
        """
        sections = []

        # 0. 시장 레짐 섹션
        if market_regime:
            regime_emoji = {
                "BULLISH": "🟢",
                "BEARISH": "🔴",
                "SIDEWAYS": "🟡",
            }.get(market_regime, "⚪")
            sections.append(f"{regime_emoji} 시장 레짐: {market_regime}")

        # 0.5. action_score 표시
        if action_score is not None:
            score_desc = (
                "강한 매수"
                if action_score > 0.7
                else "매수"
                if action_score > 0.3
                else "관망"
                if abs(action_score) < 0.3
                else "매도"
                if action_score > -0.7
                else "강한 매도"
            )
            sections.append(f"📊 액션 스코어: {action_score:+.2f} ({score_desc})")

        # 0.6. 포지션 차단 표시 (v2.1)
        if reasoning_raw.get("position_blocked"):
            sections.append(f"⚠️ [{reasoning_raw['position_blocked']}]")

        # 1. 손절 트리거 / 손익률 섹션
        if "risk_check" in reasoning_raw:
            risk = reasoning_raw["risk_check"]
            if risk.get("stop_loss_triggered"):
                sections.append("🚨 손절 조건 충족 → 즉시 매도")

            pnl_pct = risk.get("unrealized_pnl_pct")
            if pnl_pct is not None:
                sections.append(f"💰 미실현 손익: {pnl_pct:+.1f}%")
        elif "risk_assessment" in reasoning_raw:
            # fallback for old format
            risk = reasoning_raw["risk_assessment"]
            if risk.get("stop_loss_triggered"):
                sections.append("🚨 손절 조건 충족 → 즉시 매도")
            pnl_pct = risk.get("unrealized_pnl_pct")
            if pnl_pct is not None:
                sections.append(f"💰 미실현 손익: {pnl_pct:+.1f}%")

        # 2. 레짐 분석 근거
        if "regime_analysis" in reasoning_raw:
            sections.append(f"📈 레짐 분석\n{reasoning_raw['regime_analysis']}")

        # 3. 의사결정 근거 섹션
        if "action_rationale" in reasoning_raw:
            sections.append(f"💡 판단 근거\n{reasoning_raw['action_rationale']}")
        elif "decision_rationale" in reasoning_raw:
            sections.append(f"💡 판단 근거\n{reasoning_raw['decision_rationale']}")

        # 4. 기술적 지표 섹션
        if "technical_summary" in reasoning_raw:
            tech = reasoning_raw["technical_summary"]
            tech_lines = ["📉 기술적 지표"]

            if tech.get("confluence_score") is not None:
                tech_lines.append(f"• 합류 점수: {tech['confluence_score']:.2f}")
            if tech.get("rsi_14") is not None:
                tech_lines.append(f"• RSI(14): {tech['rsi_14']:.1f}")

            trends = []
            for tf in ["1h", "4h", "1d"]:
                trend_key = f"trend_{tf}"
                if tech.get(trend_key):
                    trends.append(f"{tf.upper()}={tech[trend_key]}")
            if trends:
                tech_lines.append(f"• 추세: {' / '.join(trends)}")

            if tech.get("fear_greed") is not None:
                tech_lines.append(f"• Fear & Greed: {tech['fear_greed']}")

            if len(tech_lines) > 1:
                sections.append("\n".join(tech_lines))

        return "\n\n".join(sections) if sections else "분석 근거 없음"

    def _format_reasoning(
        self,
        reasoning_raw: dict,
        balance_info: dict | None,
    ) -> str:
        """
        reasoning을 구조화된 형식으로 포맷팅

        가독성을 높이기 위해 섹션별로 구분하고 줄바꿈을 사용합니다.
        """
        sections = []

        # 1. 손절 트리거 / 손익률 섹션
        if "risk_assessment" in reasoning_raw:
            risk = reasoning_raw["risk_assessment"]
            if risk.get("stop_loss_triggered"):
                trigger_reason = risk.get("trigger_reason", "손절 조건 충족")
                sections.append(f"🚨 손절 트리거\n{trigger_reason}")

            pnl_pct = risk.get("unrealized_pnl_pct")
            if pnl_pct is not None:
                sections.append(f"📊 손익률: {pnl_pct:+.1f}%")

        # 2. 의사결정 근거 섹션
        if "decision_rationale" in reasoning_raw:
            sections.append(f"💡 의사결정\n{reasoning_raw['decision_rationale']}")
        elif "interpretation" in reasoning_raw:
            sections.append(f"💡 분석\n{reasoning_raw['interpretation']}")

        # 3. 기술적 지표 섹션
        if "technical_summary" in reasoning_raw:
            tech = reasoning_raw["technical_summary"]
            tech_lines = ["📈 기술적 지표"]

            if tech.get("confluence_score") is not None:
                tech_lines.append(f"• 합류 점수: {tech['confluence_score']:.2f}")
            if tech.get("rsi_14") is not None:
                tech_lines.append(f"• RSI: {tech['rsi_14']:.1f}")

            trends = []
            for tf in ["1h", "4h", "1d"]:
                trend_key = f"trend_{tf}"
                if tech.get(trend_key):
                    trends.append(f"{tf.upper()}={tech[trend_key]}")
            if trends:
                tech_lines.append(f"• 추세: {' / '.join(trends)}")

            if len(tech_lines) > 1:
                sections.append("\n".join(tech_lines))

        elif reasoning_raw.get("facts"):
            # facts 기반 지표 표시 (fallback)
            key_facts = []
            for fact in reasoning_raw["facts"][:5]:
                if any(
                    kw in fact for kw in ["RSI", "볼린저", "BB", "합류", "타임프레임"]
                ):
                    key_facts.append(fact)

            if key_facts:
                sections.append(
                    "📈 지표\n" + "\n".join(f"• {f}" for f in key_facts[:3])
                )
            else:
                sections.append(
                    "📋 근거\n"
                    + "\n".join(f"• {f}" for f in reasoning_raw["facts"][:3])
                )

        # 4. 핵심 요소 섹션
        if reasoning_raw.get("key_factors"):
            factors = reasoning_raw["key_factors"]
            sections.append("⭐ 핵심 요소\n" + "\n".join(f"• {f}" for f in factors))

        # 5. 위험 요소 섹션
        if reasoning_raw.get("risks"):
            risks = reasoning_raw["risks"]
            sections.append("⚠️ 위험 요소\n" + "\n".join(f"• {r}" for r in risks))

        # 6. 목표가 섹션
        if "action_levels" in reasoning_raw:
            levels = self._validate_action_levels(
                reasoning_raw["action_levels"], balance_info
            )
            level_lines = ["🎯 목표가"]
            if levels.get("stop_loss"):
                level_lines.append(f"• 손절: {levels['stop_loss']}")
            if levels.get("take_profit"):
                level_lines.append(f"• 익절: {levels['take_profit']}")
            if len(level_lines) > 1:
                sections.append("\n".join(level_lines))

        return "\n\n".join(sections) if sections else "분석 근거 없음"

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
