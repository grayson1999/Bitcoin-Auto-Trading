"""
신호 응답 파서 모듈

이 모듈은 AI 응답 파싱을 담당합니다.
- JSON 파싱
- 신호 타입 추출
- 신뢰도 추출
- 근거(reasoning) 포맷팅
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


@dataclass
class ParsedSignal:
    """파싱된 신호"""

    signal_type: str
    confidence: float
    reasoning: str


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
        AI 응답 파싱

        JSON 형식의 응답에서 신호, 신뢰도, 근거를 추출합니다.

        Args:
            text: AI 응답 텍스트
            balance_info: 잔고 정보

        Returns:
            ParsedSignal: 파싱된 신호 정보
        """
        # JSON 블록 추출 시도
        json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = text

        try:
            data = json.loads(json_str)
            signal = data.get("signal", "HOLD").upper().strip()
            confidence = float(data.get("confidence", SIGNAL_DEFAULT_CONFIDENCE))
            reasoning_raw = data.get("reasoning", "분석 근거 없음")

            # 신호 타입 검증
            if signal not in [s.value for s in SignalType]:
                signal = SignalType.HOLD.value

            # 신뢰도 범위 검증
            confidence = max(SIGNAL_MIN_CONFIDENCE, min(SIGNAL_MAX_CONFIDENCE, confidence))

            # reasoning 처리 (구조화된 포맷)
            if isinstance(reasoning_raw, dict):
                reasoning = self._format_reasoning(reasoning_raw, balance_info)
            else:
                reasoning = str(reasoning_raw)

            return ParsedSignal(
                signal_type=signal,
                confidence=confidence,
                reasoning=reasoning,
            )

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"AI 응답 파싱 실패: {e}, 원본: {text[:200]}")
            return ParsedSignal(
                signal_type=SignalType.HOLD.value,
                confidence=SIGNAL_DEFAULT_CONFIDENCE,
                reasoning=f"파싱 실패로 기본 HOLD 신호 생성. 원본: {text[:100]}",
            )

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

        elif "facts" in reasoning_raw and reasoning_raw["facts"]:
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
        if "key_factors" in reasoning_raw and reasoning_raw["key_factors"]:
            factors = reasoning_raw["key_factors"]
            sections.append("⭐ 핵심 요소\n" + "\n".join(f"• {f}" for f in factors))

        # 5. 위험 요소 섹션
        if "risks" in reasoning_raw and reasoning_raw["risks"]:
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
