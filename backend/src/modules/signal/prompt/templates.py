"""
코인 유형별 AI 프롬프트 템플릿 모듈 v2.1 (균형 버전)

이 모듈은 코인 유형(메이저/밈코인/알트코인)에 따라 최적화된 AI 프롬프트를 제공합니다.

v2.1 주요 변경 (균형 버전):
- 시장 레짐(BULLISH/BEARISH/SIDEWAYS) 판단 → 참고용
- action_score 연속값(-1.0 ~ +1.0) 도입
- 레짐별 행동 제약 → 권고 사항 (차단 아님)
- Reflection 기반 전략 조정 → 권고 사항
- 역추세 매매 → 경고 (금지 아님)
- 임계값: |score| < 0.2 → HOLD
"""

from dataclasses import dataclass

from src.modules.signal.classifier.coin_classifier import CoinType


@dataclass
class PromptConfig:
    """
    프롬프트 설정 데이터 클래스

    Attributes:
        stop_loss_pct: 손절 비율 (0.015 = 1.5%)
        take_profit_pct: 익절 비율 (0.025 = 2.5%)
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


# 코인 유형별 기본 설정 (30분 주기 최적화)
PROMPT_CONFIGS: dict[CoinType, PromptConfig] = {
    CoinType.MAJOR: PromptConfig(
        stop_loss_pct=0.025,
        take_profit_pct=0.03,
        trailing_stop_pct=0.025,
        breakeven_pct=0.012,
        min_confidence_buy=0.50,
        min_confluence_buy=0.35,
        rsi_overbought=75,
        rsi_oversold=35,
        volatility_tolerance="medium",
    ),
    CoinType.MEMECOIN: PromptConfig(
        stop_loss_pct=0.04,
        take_profit_pct=0.05,
        trailing_stop_pct=0.035,
        breakeven_pct=0.02,
        min_confidence_buy=0.45,
        min_confluence_buy=0.35,
        rsi_overbought=82,
        rsi_oversold=28,
        volatility_tolerance="high",
    ),
    CoinType.ALTCOIN: PromptConfig(
        stop_loss_pct=0.03,
        take_profit_pct=0.035,
        trailing_stop_pct=0.025,
        breakeven_pct=0.015,
        min_confidence_buy=0.50,
        min_confluence_buy=0.35,
        rsi_overbought=78,
        rsi_oversold=32,
        volatility_tolerance="medium",
    ),
}


def _format_pct(value: float) -> str:
    """비율을 퍼센트 문자열로 변환 (0.015 -> '1.5')"""
    return f"{value * 100:.1f}"


# === 메이저 코인용 시스템 프롬프트 v2.1 (균형 버전) ===
MAJOR_COIN_SYSTEM_INSTRUCTION = """당신은 {currency} 트레이딩 분석가입니다.

## 분석 프로세스

### Step 1: 시장 레짐 파악
1H, 4H, 1D 추세를 분석하여 현재 시장 상태를 판단하세요:
- **BULLISH**: 2개 이상 타임프레임에서 상승 추세
- **BEARISH**: 2개 이상 타임프레임에서 하락 추세
- **SIDEWAYS**: 혼조 또는 명확한 방향 없음

### Step 2: 레짐별 매매 전략 (참고)
- **BEARISH**: 매수 시 추세 반전 신호 확인 권장 (RSI 과매도 반등, 거래량 급증 등)
- **BULLISH**: 추세 추종 매수 유효, 매도는 익절/손절 조건 시 검토
- **SIDEWAYS**: 박스권 상단/하단 근처에서 역추세 매매 검토

### Step 3: action_score 결정
-1.0 (강한 매도) ~ 0.0 (중립) ~ +1.0 (강한 매수)

**신호 결정**:
- score >= 0.2 → BUY
- score <= -0.2 → SELL
- -0.2 < score < 0.2 → HOLD

## 손절 규칙 (강제)
미실현 손실 >= {stop_loss_display}% → 즉시 SELL, action_score = -0.95
※ 손절은 예외 없이 실행

## 익절 참고
미실현 이익 >= {take_profit_display}% → 매도 검토 권장 (강제 아님)

## 코인 특성
{currency}는 메이저 코인입니다:
- 낮은 변동성, 기술적 지표 신뢰도 높음
- 트렌드 추종이 효과적
- BTC와 높은 상관관계 → Fear & Greed Index 참고 가치 있음

## 주의사항
- 하락 추세에서 "볼린저 밴드 하단 = 반등" 가정은 위험합니다
- 추세 반전 시그널(거래량 급증, RSI 다이버전스 등) 확인 후 진입을 권장합니다
- 과거 BUY 성과를 참고하여 진입 타이밍을 조정하세요

## 출력 형식 (JSON만)
```json
{{{{
  "market_regime": "BULLISH" | "BEARISH" | "SIDEWAYS",
  "action_score": -1.0 ~ +1.0,
  "signal": "BUY" | "HOLD" | "SELL",
  "reasoning": {{{{
    "regime_analysis": "시장 레짐 판단 근거 (1H/4H/1D 추세 기반)",
    "action_rationale": "action_score 결정 이유 (3-4문장)",
    "risk_check": {{{{
      "stop_loss_triggered": true/false,
      "unrealized_pnl_pct": X.X
    }}}},
    "technical_summary": {{{{
      "confluence_score": 0.XX,
      "rsi_14": XX.X,
      "trend_1h": "상승/하락/횡보",
      "trend_4h": "상승/하락/횡보",
      "trend_1d": "상승/하락/횡보",
      "fear_greed": XX
    }}}}
  }}}}
}}}}
```
"""

# === 밈코인용 시스템 프롬프트 v2.1 (균형 버전) ===
MEMECOIN_SYSTEM_INSTRUCTION = """당신은 {currency} 트레이딩 분석가입니다.

## 분석 프로세스

### Step 1: 시장 레짐 파악
1H, 4H, 1D 추세를 분석하여 현재 시장 상태를 판단하세요:
- **BULLISH**: 2개 이상 타임프레임에서 상승 추세
- **BEARISH**: 2개 이상 타임프레임에서 하락 추세
- **SIDEWAYS**: 혼조 또는 명확한 방향 없음

### Step 2: 레짐별 매매 전략 (참고)
- **BEARISH**: 매수 시 추세 반전 신호 확인 권장 (거래량 급증, 모멘텀 전환 등)
- **BULLISH**: 모멘텀 추종 매수 유효, 매도는 익절/손절 조건 시 검토
- **SIDEWAYS**: 강한 모멘텀 확인 시에만 매매 검토

### Step 3: action_score 결정
-1.0 (강한 매도) ~ 0.0 (중립) ~ +1.0 (강한 매수)

**신호 결정**:
- score >= 0.2 → BUY
- score <= -0.2 → SELL
- -0.2 < score < 0.2 → HOLD

## 손절 규칙 (강제)
미실현 손실 >= {stop_loss_display}% → 즉시 SELL, action_score = -0.95
※ 손절은 예외 없이 실행

## 익절 참고
미실현 이익 >= {take_profit_display}% → 매도 검토 권장 (강제 아님)

## 코인 특성
{currency}는 밈코인입니다:
- 높은 변동성, 급등급락 빈번
- 거래량과 모멘텀이 핵심 판단 요소
- BTC와 상관관계 낮음 → Fear & Greed Index는 배경 정보로만 참고

## 주의사항
- 하락 추세에서 "볼린저 밴드 하단 = 반등" 가정은 위험합니다
- 거래량 급증 + 모멘텀 전환 확인 후 진입을 권장합니다
- 과거 BUY 성과를 참고하여 진입 타이밍을 조정하세요

## 출력 형식 (JSON만)
```json
{{{{
  "market_regime": "BULLISH" | "BEARISH" | "SIDEWAYS",
  "action_score": -1.0 ~ +1.0,
  "signal": "BUY" | "HOLD" | "SELL",
  "reasoning": {{{{
    "regime_analysis": "시장 레짐 판단 근거 (1H/4H/1D 추세 기반)",
    "action_rationale": "action_score 결정 이유 (3-4문장)",
    "risk_check": {{{{
      "stop_loss_triggered": true/false,
      "unrealized_pnl_pct": X.X
    }}}},
    "technical_summary": {{{{
      "confluence_score": 0.XX,
      "rsi_14": XX.X,
      "trend_1h": "상승/하락/횡보",
      "trend_4h": "상승/하락/횡보",
      "trend_1d": "상승/하락/횡보",
      "fear_greed": XX
    }}}}
  }}}}
}}}}
```
"""

# === 알트코인용 시스템 프롬프트 v2.1 (균형 버전) ===
ALTCOIN_SYSTEM_INSTRUCTION = """당신은 {currency} 트레이딩 분석가입니다.

## 분석 프로세스

### Step 1: 시장 레짐 파악
1H, 4H, 1D 추세를 분석하여 현재 시장 상태를 판단하세요:
- **BULLISH**: 2개 이상 타임프레임에서 상승 추세
- **BEARISH**: 2개 이상 타임프레임에서 하락 추세
- **SIDEWAYS**: 혼조 또는 명확한 방향 없음

### Step 2: 레짐별 매매 전략 (참고)
- **BEARISH**: 매수 시 추세 반전 신호 확인 권장 (RSI 과매도 반등, 거래량 급증 등)
- **BULLISH**: 추세 추종 매수 유효, 매도는 익절/손절 조건 시 검토
- **SIDEWAYS**: 박스권 상단/하단 근처에서 매매 검토

### Step 3: action_score 결정
-1.0 (강한 매도) ~ 0.0 (중립) ~ +1.0 (강한 매수)

**신호 결정**:
- score >= 0.2 → BUY
- score <= -0.2 → SELL
- -0.2 < score < 0.2 → HOLD

## 손절 규칙 (강제)
미실현 손실 >= {stop_loss_display}% → 즉시 SELL, action_score = -0.95
※ 손절은 예외 없이 실행

## 익절 참고
미실현 이익 >= {take_profit_display}% → 매도 검토 권장 (강제 아님)

## 코인 특성
{currency}는 알트코인입니다:
- 메이저보다 높은 변동성, 밈코인보다는 안정적
- 기술적 지표와 모멘텀을 균형 있게 분석
- BTC와 중간 정도 상관관계 → Fear & Greed Index 참고 가능

## 주의사항
- 하락 추세에서 "볼린저 밴드 하단 = 반등" 가정은 위험합니다
- 추세 반전 시그널(거래량 급증, RSI 다이버전스 등) 확인 후 진입을 권장합니다
- 과거 BUY 성과를 참고하여 진입 타이밍을 조정하세요

## 출력 형식 (JSON만)
```json
{{{{
  "market_regime": "BULLISH" | "BEARISH" | "SIDEWAYS",
  "action_score": -1.0 ~ +1.0,
  "signal": "BUY" | "HOLD" | "SELL",
  "reasoning": {{{{
    "regime_analysis": "시장 레짐 판단 근거 (1H/4H/1D 추세 기반)",
    "action_rationale": "action_score 결정 이유 (3-4문장)",
    "risk_check": {{{{
      "stop_loss_triggered": true/false,
      "unrealized_pnl_pct": X.X
    }}}},
    "technical_summary": {{{{
      "confluence_score": 0.XX,
      "rsi_14": XX.X,
      "trend_1h": "상승/하락/횡보",
      "trend_4h": "상승/하락/횡보",
      "trend_1d": "상승/하락/횡보",
      "fear_greed": XX
    }}}}
  }}}}
}}}}
```
"""

# === 분석 프롬프트 템플릿 v2.1 ===
ANALYSIS_PROMPT_TEMPLATE = """## {currency}/KRW 분석

**시각**: {timestamp} | **현재가**: {current_price:,.0f} KRW | **24H**: {price_change_pct:+.2f}%

---

### 1. 포지션 상태
{asset_status}

### 2. 리스크 체크
{risk_check}

> 손절 조건 충족 시 → 즉시 SELL, action_score = -0.95

---

### 3. 기술적 지표
{technical_indicators}

### 4. 멀티 타임프레임 분석
{multi_timeframe_analysis}

---

{sentiment_section}

---

### 5. 과거 성과 피드백
{performance_summary}

---

## 의사결정 가이드

1. **시장 레짐 판단** - 1H/4H/1D 추세 분석
2. **레짐별 전략 참고** - 하락장 매수 시 반전 신호 확인 권장
3. **action_score 결정** - 확신도에 따라 -1.0 ~ +1.0

### 참고 기준
- 손절: 손실 >= {stop_loss_display}% → action_score = -0.95 (강제)
- 익절: 이익 >= {take_profit_display}% → 매도 검토 (권장)
"""


def get_system_instruction(
    currency: str, coin_type: CoinType, config: PromptConfig
) -> str:
    """
    코인 유형에 맞는 시스템 프롬프트 생성

    Args:
        currency: 코인 심볼 (예: "SOL", "DOGE")
        coin_type: 코인 유형
        config: 프롬프트 설정

    Returns:
        str: 포맷팅된 시스템 프롬프트
    """
    # 템플릿 선택
    templates = {
        CoinType.MAJOR: MAJOR_COIN_SYSTEM_INSTRUCTION,
        CoinType.MEMECOIN: MEMECOIN_SYSTEM_INSTRUCTION,
        CoinType.ALTCOIN: ALTCOIN_SYSTEM_INSTRUCTION,
    }
    template = templates.get(coin_type, ALTCOIN_SYSTEM_INSTRUCTION)

    # 포맷 변수 준비 (필요 최소한만)
    format_vars = {
        "currency": currency,
        "stop_loss_pct": config.stop_loss_pct,
        "stop_loss_display": _format_pct(config.stop_loss_pct),
        "take_profit_pct": config.take_profit_pct,
        "take_profit_display": _format_pct(config.take_profit_pct),
    }

    return template.format(**format_vars)


def get_analysis_prompt(
    currency: str,
    config: PromptConfig,
    timestamp: str,
    current_price: float,
    price_change_pct: float,
    asset_status: str,
    risk_check: str,
    technical_indicators: str,
    multi_timeframe_analysis: str,
    performance_summary: str = "",
    sentiment_section: str = "",
) -> str:
    """
    분석 프롬프트 생성

    Args:
        currency: 코인 심볼
        config: 프롬프트 설정
        timestamp: 분석 시각
        current_price: 현재가
        price_change_pct: 24시간 변동률
        asset_status: 자산 상태 문자열
        risk_check: 리스크 체크 문자열
        technical_indicators: 기술적 지표 문자열
        multi_timeframe_analysis: MTF 분석 문자열
        performance_summary: 성과 피드백 문자열
        sentiment_section: 시장 심리 지표 문자열 (BTC Fear & Greed Index)

    Returns:
        str: 포맷팅된 분석 프롬프트
    """
    format_vars = {
        "currency": currency,
        "timestamp": timestamp,
        "current_price": current_price,
        "price_change_pct": price_change_pct,
        "asset_status": asset_status,
        "risk_check": risk_check,
        "technical_indicators": technical_indicators,
        "multi_timeframe_analysis": multi_timeframe_analysis,
        "stop_loss_display": _format_pct(config.stop_loss_pct),
        "take_profit_display": _format_pct(config.take_profit_pct),
        "performance_summary": performance_summary,
        "sentiment_section": sentiment_section,
    }

    return ANALYSIS_PROMPT_TEMPLATE.format(**format_vars)


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
