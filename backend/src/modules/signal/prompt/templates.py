"""
GPT-5 Nano AI 프롬프트 템플릿 모듈

카테고리컬 신호 변환 + 규칙 기반 프롬프트로
GPT-5 Nano에 최적화된 매매 신호를 생성합니다.

- 영어 지시 + 한국어 추론 출력
- 3x 앙상블 self-consistency (AIClient에서 처리)
- Few-shot 3개 예시 (BUY/SELL/HOLD)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.modules.signal.classifier.coin_classifier import CoinType

if TYPE_CHECKING:
    from src.modules.signal.prompt import signal_pre_processor


@dataclass
class PromptConfig:
    """
    프롬프트 설정 데이터 클래스

    Attributes:
        stop_loss_pct: 손절 비율 (0.03 = 3.0%)
        take_profit_pct: 익절 비율 (0.045 = 4.5%)
        trailing_stop_pct: 트레일링 스탑 활성화 수익률
        breakeven_pct: 본전 손절 활성화 수익률
        min_confidence_buy: 최소 매수 신뢰도
        min_confluence_buy: 최소 매수 합류 점수
        rsi_overbought: RSI 과매수 기준
        rsi_oversold: RSI 과매도 기준
        volatility_tolerance: 변동성 허용 수준 ("low", "medium", "high")
    """

    stop_loss_pct: float
    take_profit_pct: float
    trailing_stop_pct: float
    breakeven_pct: float
    min_confidence_buy: float
    min_confluence_buy: float
    rsi_overbought: int
    rsi_oversold: int
    volatility_tolerance: str


# 코인 유형별 기본 설정 (v3.0: 보수적 자본 보존)
PROMPT_CONFIGS: dict[CoinType, PromptConfig] = {
    CoinType.MAJOR: PromptConfig(
        stop_loss_pct=0.02,
        take_profit_pct=0.025,
        trailing_stop_pct=0.015,
        breakeven_pct=0.01,
        min_confidence_buy=0.50,
        min_confluence_buy=0.55,
        rsi_overbought=70,
        rsi_oversold=30,
        volatility_tolerance="low",
    ),
    CoinType.MEMECOIN: PromptConfig(
        stop_loss_pct=0.03,
        take_profit_pct=0.035,
        trailing_stop_pct=0.02,
        breakeven_pct=0.015,
        min_confidence_buy=0.50,
        min_confluence_buy=0.55,
        rsi_overbought=75,
        rsi_oversold=28,
        volatility_tolerance="medium",
    ),
    CoinType.ALTCOIN: PromptConfig(
        stop_loss_pct=0.025,
        take_profit_pct=0.03,
        trailing_stop_pct=0.015,
        breakeven_pct=0.012,
        min_confidence_buy=0.50,
        min_confluence_buy=0.55,
        rsi_overbought=72,
        rsi_oversold=28,
        volatility_tolerance="low",
    ),
}


# === 시스템 프롬프트 (영어 지시 + 한국어 출력) ===
SYSTEM_INSTRUCTION = """You are a {currency}/KRW trading signal generator.

## Rules (STRICT)
- Output ONLY valid JSON. No markdown, no explanation outside JSON.
- reasoning fields (regime_analysis, action_rationale) MUST be written in Korean.
- Do NOT chain-of-thought. Just classify directly.

## CAPITAL PRESERVATION PRIORITY
- When uncertain, ALWAYS prefer HOLD over BUY.
- BUY only when indicators show STRONG confluence (buy_signals >= 5).
- In SIDEWAYS markets, prefer HOLD (do not attempt range trading).
- Require MULTIPLE timeframe confirmation for BUY (at least 2 of: trend_1h, trend_4h, trend_1d must be UP).

## Signal Decision
If stop_loss_triggered == true → signal: "SELL", action_score: -0.95

Otherwise use these rules:
- BUY: overall_bias == "BUY" AND buy_signals >= 5 AND at least 2 trends UP → score +0.5 to +0.7
- SELL: overall_bias == "SELL" AND sell_signals >= 3 → score -0.3 to -0.7
- SELL: trend_1h == "DOWN" AND holding position → score -0.3 to -0.5
- Otherwise → HOLD, score -0.1 to +0.1

## Output Format (JSON only)
{{"market_regime": "BULLISH"|"BEARISH"|"SIDEWAYS", "action_score": -1.0 to +1.0, "signal": "BUY"|"HOLD"|"SELL", "reasoning": {{"regime_analysis": "Korean text", "action_rationale": "Korean text", "risk_check": {{"stop_loss_triggered": true/false, "unrealized_pnl_pct": X.X}}, "technical_summary": {{"confluence_score": 0.XX, "rsi_14": XX.X, "trend_1h": "UP/DOWN/FLAT", "trend_4h": "UP/DOWN/FLAT", "trend_1d": "UP/DOWN/FLAT"}}}}}}

## Few-Shot Examples

### Example 1: BUY (strong confluence required)
Input: trend_1h=UP, trend_4h=UP, trend_1d=UP, rsi=SLIGHTLY_OVERSOLD(32), macd=BULLISH_CROSS, ema=BULLISH_ALIGNED, bb=NEAR_LOWER_BUY, overall_bias=BUY, buy_signals=6, sell_signals=0, no position
Output: {{"market_regime":"BULLISH","action_score":0.60,"signal":"BUY","reasoning":{{"regime_analysis":"1시간, 4시간, 일봉 모두 상승 추세로 강세장 판단","action_rationale":"RSI 과매도 구간 벗어나며 반등 중. MACD 골든크로스와 EMA 정배열이 매수 신호를 강화. 6개 매수 신호와 3개 타임프레임 상승으로 강한 매수 합류","risk_check":{{"stop_loss_triggered":false,"unrealized_pnl_pct":0.0}},"technical_summary":{{"confluence_score":0.78,"rsi_14":32.0,"trend_1h":"UP","trend_4h":"UP","trend_1d":"UP"}}}}}}

### Example 2: SELL
Input: trend_1h=DOWN, trend_4h=DOWN, rsi=SLIGHTLY_OVERBOUGHT(68), macd=BEARISH_CROSS, ema=BEARISH_ALIGNED, bb=NEAR_UPPER_SELL, overall_bias=SELL, buy_signals=1, sell_signals=6, holding position, unrealized_pnl=-1.5%
Output: {{"market_regime":"BEARISH","action_score":-0.65,"signal":"SELL","reasoning":{{"regime_analysis":"1시간, 4시간 하락 추세로 약세장 판단","action_rationale":"하락 추세 지속 중 MACD 데드크로스 발생. 볼린저밴드 상단 근접으로 추가 하락 가능성. 미실현 손실 -1.5%로 추가 하락 전 매도 권장","risk_check":{{"stop_loss_triggered":false,"unrealized_pnl_pct":-1.5}},"technical_summary":{{"confluence_score":0.25,"rsi_14":68.0,"trend_1h":"DOWN","trend_4h":"DOWN","trend_1d":"FLAT"}}}}}}

### Example 3: HOLD (uncertain → preserve capital)
Input: trend_1h=FLAT, trend_4h=UP, rsi=NEUTRAL(48), macd=NEUTRAL, ema=MIXED, bb=NEUTRAL, overall_bias=NEUTRAL, buy_signals=3, sell_signals=2, no position
Output: {{"market_regime":"SIDEWAYS","action_score":0.05,"signal":"HOLD","reasoning":{{"regime_analysis":"1시간 횡보, 4시간 상승으로 혼조 판단","action_rationale":"기술적 지표가 혼재되어 명확한 방향 없음. 자본 보존을 위해 강한 합류 신호까지 관망이 적절","risk_check":{{"stop_loss_triggered":false,"unrealized_pnl_pct":0.0}},"technical_summary":{{"confluence_score":0.50,"rsi_14":48.0,"trend_1h":"FLAT","trend_4h":"UP","trend_1d":"FLAT"}}}}}}
"""

ANALYSIS_PROMPT = """## {currency}/KRW Signal Analysis

**Price**: {current_price:,.0f} KRW | **24H Change**: {price_change_pct:+.2f}%

### Position
{position_status}

### Risk Check
{risk_check}

### Pre-Computed Signals
- RSI(14): {rsi_signal} ({rsi_value:.1f})
- MACD: {macd_signal}
- EMA: {ema_signal}
- Bollinger: {bb_signal}
- Volume: {volume_signal}

### Trend
- 1H: {trend_1h}
- 4H: {trend_4h}
- 1D: {trend_1d}

### Summary
- Buy signals: {buy_signals_count} | Sell signals: {sell_signals_count}
- Overall bias: {overall_bias}
- Confluence: {confluence_score:.2f}

Decide: BUY, SELL, or HOLD. Output JSON only.
"""


def get_system_instruction(currency: str) -> str:
    """시스템 프롬프트 생성"""
    return SYSTEM_INSTRUCTION.format(currency=currency)


def build_prompt(
    pre_computed: signal_pre_processor.PreComputedSignals,
    currency: str,
    current_price: float,
    price_change_pct: float,
    balance_info: dict | None,
    stop_loss_pct: float,
) -> str:
    """
    분석 프롬프트 생성

    Args:
        pre_computed: 사전 계산된 신호 라벨
        currency: 코인 심볼
        current_price: 현재가
        price_change_pct: 24시간 변동률
        balance_info: 잔고 정보
        stop_loss_pct: 손절 비율

    Returns:
        str: 분석 프롬프트
    """
    # 포지션 상태
    position_status = "No position (KRW only)"
    risk_check = "No position → no risk check needed"

    if balance_info:
        coin = float(balance_info.get("coin_available", 0))
        if coin > 0:
            avg_price = float(balance_info.get("coin_avg_price", 0))
            unrealized_pnl_pct = float(balance_info.get("unrealized_pnl_pct", 0))
            stop_triggered = unrealized_pnl_pct <= -(stop_loss_pct * 100)
            position_status = (
                f"Holding {coin:.6f} {currency} "
                f"(avg: {avg_price:,.0f}, PnL: {unrealized_pnl_pct:+.2f}%)"
            )
            risk_check = (
                f"Unrealized PnL: {unrealized_pnl_pct:+.2f}% | "
                f"Stop loss ({stop_loss_pct * 100:.1f}%): "
                f"{'TRIGGERED → SELL immediately' if stop_triggered else 'not triggered'}"
            )

    return ANALYSIS_PROMPT.format(
        currency=currency,
        current_price=current_price,
        price_change_pct=price_change_pct,
        position_status=position_status,
        risk_check=risk_check,
        rsi_signal=pre_computed.rsi_signal,
        rsi_value=pre_computed.rsi_value,
        macd_signal=pre_computed.macd_signal,
        ema_signal=pre_computed.ema_signal,
        bb_signal=pre_computed.bb_signal,
        volume_signal=pre_computed.volume_signal,
        trend_1h=pre_computed.trend_1h,
        trend_4h=pre_computed.trend_4h,
        trend_1d=pre_computed.trend_1d,
        buy_signals_count=pre_computed.buy_signals_count,
        sell_signals_count=pre_computed.sell_signals_count,
        overall_bias=pre_computed.overall_bias,
        confluence_score=pre_computed.confluence_score,
    )


def get_config_for_coin(
    coin_type: CoinType, custom_config: PromptConfig | None = None
) -> PromptConfig:
    """
    코인 유형에 맞는 설정 반환

    Args:
        coin_type: 코인 유형
        custom_config: 커스텀 설정 (None이면 기본값 사용)

    Returns:
        PromptConfig: 프롬프트 설정
    """
    if custom_config:
        return custom_config
    return PROMPT_CONFIGS.get(coin_type, PROMPT_CONFIGS[CoinType.ALTCOIN])
