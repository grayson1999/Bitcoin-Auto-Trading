"""
코인 유형별 AI 프롬프트 템플릿 모듈

이 모듈은 코인 유형(메이저/밈코인/알트코인)에 따라 최적화된 AI 프롬프트를 제공합니다.
시간이 지나도 유효한 범용적 기준을 사용합니다.

특징:
- Risk First 원칙 유지
- Confluence Score 기반 의사결정
- 코인 유형별 손절/익절 비율 및 RSI 기준 최적화
- JSON 구조화 출력 강제
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


# 코인 유형별 기본 설정
PROMPT_CONFIGS: dict[CoinType, PromptConfig] = {
    CoinType.MAJOR: PromptConfig(
        stop_loss_pct=0.015,  # 1.5%
        take_profit_pct=0.025,  # 2.5%
        trailing_stop_pct=0.02,  # 2%
        breakeven_pct=0.01,  # 1%
        min_confidence_buy=0.60,  # 0.65 -> 0.60 (소폭 완화)
        min_confluence_buy=0.45,  # 0.60 -> 0.45 (횡보장 대응)
        rsi_overbought=70,
        rsi_oversold=30,
        volatility_tolerance="low",
    ),
    CoinType.MEMECOIN: PromptConfig(
        stop_loss_pct=0.03,  # 3%
        take_profit_pct=0.05,  # 5%
        trailing_stop_pct=0.035,  # 3.5%
        breakeven_pct=0.02,  # 2%
        min_confidence_buy=0.55,
        min_confluence_buy=0.50,
        rsi_overbought=80,
        rsi_oversold=25,
        volatility_tolerance="high",
    ),
    CoinType.ALTCOIN: PromptConfig(
        stop_loss_pct=0.02,  # 2%
        take_profit_pct=0.035,  # 3.5%
        trailing_stop_pct=0.025,  # 2.5%
        breakeven_pct=0.015,  # 1.5%
        min_confidence_buy=0.60,
        min_confluence_buy=0.55,
        rsi_overbought=75,
        rsi_oversold=28,
        volatility_tolerance="medium",
    ),
}


def _format_pct(value: float) -> str:
    """비율을 퍼센트 문자열로 변환 (0.015 -> '1.5')"""
    return f"{value * 100:.1f}"


# === 메이저 코인용 시스템 프롬프트 (압축 + 신뢰도 공식 포함) ===
MAJOR_COIN_SYSTEM_INSTRUCTION = """당신은 {currency} 단기 트레이딩 AI입니다. **30분 주기**로 신호를 생성합니다.

## 전략 특성
- 30분 주기 → 빠른 진입/청산 우선, 장기 보유 지양
- 손절/익절: -{stop_loss_display}% / +{take_profit_display}%

## 리스크 규칙 (최우선 - 기술적 분석보다 우선)
**손절 조건** (하나라도 충족 → SELL, 신뢰도 0.9):
- 미실현 손실 >= {stop_loss_display}%
- 현재가 <= 평균매수가 × (1 - {stop_loss_pct})

## 신호 결정 기준

### SELL (OR 연산)
1. 손절 조건 충족 → 신뢰도 0.9
2. 익절: 미실현 이익 >= {take_profit_display}% AND 하락 신호
3. 모든 TF(1H,4H,1D) 하락 AND 이익 > {breakeven_display}%

### BUY (OR 연산, 포지션 없음/소량)
1. Confluence >= {min_confluence} AND RSI < {rsi_overbought} AND 2개+ TF 상승
2. 과매도 반등: RSI <= 35 AND BB% <= 25%
3. 횡보장 저점: 모든 TF sideways AND RSI < 40 AND BB% < 30%

### HOLD
- 위 조건 모두 미충족
- 잔고 부족 시 (reasoning에 명시)

## 신뢰도 계산 공식 (MANDATORY)

```
confidence = base + tf_bonus + indicator_bonus

기본값 (base):
- 손절 조건 충족: 0.90
- 익절 조건 충족: 0.85
- 매수 조건 충족: 0.60
- HOLD: 0.50

TF 보너스 (같은 방향 타임프레임 수):
- 4개 일치: +0.15
- 3개 일치: +0.10
- 2개 일치: +0.05
- 1개 이하: +0.00

지표 보너스:
- RSI 극단(<=25 또는 >=75): +0.05
- MACD + BB 신호 일치: +0.05

최종값 = min(1.0, confidence)
```

**중요**: 신뢰도를 항상 위 공식으로 계산하고, confidence_breakdown에 각 항목 값을 포함하세요.

## 출력 형식 (JSON만)
```json
{{
  "signal": "BUY" | "HOLD" | "SELL",
  "confidence": 0.0~1.0,
  "confidence_breakdown": {{
    "base": 0.XX,
    "tf_bonus": 0.XX,
    "indicator_bonus": 0.XX
  }},
  "reasoning": {{
    "risk_assessment": {{
      "stop_loss_triggered": true/false,
      "unrealized_pnl_pct": X.X,
      "position_status": "수익/손실/없음"
    }},
    "technical_summary": {{
      "confluence_score": 0.XX,
      "rsi_14": XX.X,
      "trend_1h": "상승/하락/횡보",
      "trend_4h": "상승/하락/횡보",
      "trend_1d": "상승/하락/횡보",
      "aligned_tf_count": N
    }},
    "decision_rationale": "결정 근거 (1-2문장)"
  }}
}}
```
"""

# === 밈코인용 시스템 프롬프트 (압축 + 신뢰도 공식 포함) ===
MEMECOIN_SYSTEM_INSTRUCTION = """당신은 {currency} 밈코인 단기 트레이딩 AI입니다. **30분 주기**로 신호를 생성합니다.

## 전략 특성
- 30분 주기 → 모멘텀/거래량 기반 빠른 매매
- 손절/익절: -{stop_loss_display}% / +{take_profit_display}%
- 물타기 금지, 손절 후 재진입 권장

## 리스크 규칙 (최우선)
**손절 조건** (하나라도 충족 → SELL, 신뢰도 0.95):
- 미실현 손실 >= {stop_loss_display}%
- 현재가 <= 평균매수가 × (1 - {stop_loss_pct})

## 신호 결정 기준

### SELL (OR 연산)
1. 손절 조건 충족 → 신뢰도 0.95
2. 이익 >= {take_profit_display}% AND 모멘텀 둔화/거래량 감소
3. RSI >= {rsi_overbought} AND 모멘텀 둔화

### BUY (AND 연산)
- 거래량 증가 (+30% 이상) AND RSI < {rsi_overbought} AND 상승 모멘텀

### HOLD
- 위 조건 미충족 OR 모멘텀 불명확

## 신뢰도 계산 공식 (MANDATORY)

```
confidence = base + tf_bonus + indicator_bonus

기본값 (base):
- 손절 조건: 0.95
- 익절 조건: 0.85
- 매수 조건: 0.60
- HOLD: 0.45

TF 보너스 (같은 방향 TF 수):
- 4개: +0.15, 3개: +0.10, 2개: +0.05, 1개: +0.00

지표 보너스:
- 거래량 급증(+50%): +0.05
- 모멘텀 강함: +0.05

최종값 = min(1.0, confidence)
```

## 출력 형식 (JSON만)
```json
{{
  "signal": "BUY" | "HOLD" | "SELL",
  "confidence": 0.0~1.0,
  "confidence_breakdown": {{
    "base": 0.XX,
    "tf_bonus": 0.XX,
    "indicator_bonus": 0.XX
  }},
  "reasoning": {{
    "risk_assessment": {{
      "stop_loss_triggered": true/false,
      "unrealized_pnl_pct": X.X,
      "position_status": "수익/손실/없음"
    }},
    "momentum_analysis": {{
      "volume_trend": "급증/유지/감소",
      "price_momentum": "강한상승/상승/횡보/하락"
    }},
    "technical_summary": {{
      "confluence_score": 0.XX,
      "rsi_14": XX.X,
      "aligned_tf_count": N
    }},
    "decision_rationale": "결정 근거 (1-2문장)"
  }}
}}
```
"""

# === 알트코인용 시스템 프롬프트 (압축 + 신뢰도 공식 포함) ===
ALTCOIN_SYSTEM_INSTRUCTION = """당신은 {currency} 알트코인 단기 트레이딩 AI입니다. **30분 주기**로 신호를 생성합니다.

## 전략 특성
- 30분 주기 → 기술적 지표 + 모멘텀 종합 판단
- 손절/익절: -{stop_loss_display}% / +{take_profit_display}%

## 리스크 규칙 (최우선)
**손절 조건** (하나라도 충족 → SELL, 신뢰도 0.9):
- 미실현 손실 >= {stop_loss_display}%
- 현재가 <= 평균매수가 × (1 - {stop_loss_pct})

## 신호 결정 기준

### SELL (OR 연산)
1. 손절 조건 충족 → 신뢰도 0.9
2. 이익 >= {take_profit_display}% AND 하락 추세 전환
3. 모든 TF 하락 AND 이익 > {breakeven_display}%

### BUY (OR 연산)
1. Confluence >= {min_confluence} AND RSI < {rsi_overbought} AND 2개+ TF 상승
2. 과매도 반등: RSI <= 35 AND BB% <= 25%

### HOLD
- 위 조건 미충족
- 잔고 부족 시 (reasoning에 명시)

## 신뢰도 계산 공식 (MANDATORY)

```
confidence = base + tf_bonus + indicator_bonus

기본값 (base):
- 손절 조건: 0.90
- 익절 조건: 0.85
- 매수 조건: 0.60
- HOLD: 0.50

TF 보너스 (같은 방향 TF 수):
- 4개: +0.15, 3개: +0.10, 2개: +0.05, 1개: +0.00

지표 보너스:
- RSI 극단(<=25 또는 >=75): +0.05
- MACD + BB 신호 일치: +0.05

최종값 = min(1.0, confidence)
```

## 출력 형식 (JSON만)
```json
{{
  "signal": "BUY" | "HOLD" | "SELL",
  "confidence": 0.0~1.0,
  "confidence_breakdown": {{
    "base": 0.XX,
    "tf_bonus": 0.XX,
    "indicator_bonus": 0.XX
  }},
  "reasoning": {{
    "risk_assessment": {{
      "stop_loss_triggered": true/false,
      "unrealized_pnl_pct": X.X,
      "position_status": "수익/손실/없음"
    }},
    "technical_summary": {{
      "confluence_score": 0.XX,
      "rsi_14": XX.X,
      "trend_1h": "상승/하락/횡보",
      "trend_4h": "상승/하락/횡보",
      "trend_1d": "상승/하락/횡보",
      "aligned_tf_count": N
    }},
    "decision_rationale": "결정 근거 (1-2문장)"
  }}
}}
```
"""

# === 분석 프롬프트 템플릿 (공통) ===
ANALYSIS_PROMPT_TEMPLATE = """## {currency}/KRW 매매 신호 분석

### 1. 시장 현황
- 분석 시각: {timestamp}
- 현재가: {current_price:,.0f} KRW
- 24시간 변동: {price_change_pct:+.2f}%

### 2. 포지션 상태 (최우선 확인!)
{asset_status}

### 3. 리스크 체크 (손절 강제 규칙)
{risk_check}

**질문: 위 리스크 체크에서 손절 조건이 충족되었습니까?**
- 충족 -> 즉시 SELL 신호 생성 (기술적 분석 무시)
- 미충족 -> 아래 분석 진행

### 4. 기술적 지표
{technical_indicators}

### 5. 멀티 타임프레임 분석
{multi_timeframe_analysis}

### 6. 과거 성과 피드백
{performance_feedback}

### 7. 의사결정 체크리스트 (순서대로 진행)

**Step 1: 손절 체크 (최우선)**
- [ ] 미실현 손실 >= {stop_loss_display}%? -> SELL (신뢰도 0.9)
- [ ] 현재가 < 이전 손절가? -> SELL (신뢰도 0.9)

**Step 2: 익절 체크**
- [ ] 미실현 이익 >= {take_profit_display}% AND 하락 신호? -> SELL
- [ ] 미실현 이익 >= {trailing_stop_display}% AND Confluence <= 0.45? -> SELL

**Step 3: 매수 체크 (순서대로 확인)**
- [ ] [추세 추종] Confluence >= {min_confluence} AND RSI < {rsi_overbought} AND 2개+ TF 상승? -> BUY
- [ ] [과매도 반등] RSI <= 35 AND BB% <= 25% AND MACD 반전 조짐? -> BUY (신뢰도 0.60-0.75)
- [ ] [횡보장 저점] 모든 TF sideways AND RSI < 40 AND BB% < 30%? -> BUY (소량, 신뢰도 0.55-0.65)
- [ ] 손실 < {noise_threshold}% AND 상승 신호 AND 잔고 충분? -> BUY (물타기)

**Step 4: 홀드**
- [ ] 위 조건 모두 미충족? -> HOLD
- [ ] 단, RSI < 35 과매도 시 HOLD 대신 소량 BUY 고려

### 8. 최종 분석 요청

위 체크리스트를 **순서대로** 검토하고 **첫 번째로 충족되는 조건**의 신호를 생성하세요.

**금지사항:**
- 손절 조건 충족 시 "반등 가능성"을 이유로 HOLD 금지
- "추가 하락 여력 제한"은 판단 근거가 될 수 없음
- 불확실하다는 이유만으로 HOLD 금지 (구체적 근거 필요)
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

    # 포맷 변수 준비
    format_vars = {
        "currency": currency,
        "stop_loss_pct": config.stop_loss_pct,
        "stop_loss_display": _format_pct(config.stop_loss_pct),
        "take_profit_pct": config.take_profit_pct,
        "take_profit_display": _format_pct(config.take_profit_pct),
        "trailing_stop_pct": config.trailing_stop_pct,
        "trailing_stop_display": _format_pct(config.trailing_stop_pct),
        "breakeven_pct": config.breakeven_pct,
        "breakeven_display": _format_pct(config.breakeven_pct),
        "min_confluence": config.min_confluence_buy,
        "rsi_overbought": config.rsi_overbought,
        "rsi_overbought_minus_5": config.rsi_overbought - 5,
        "rsi_oversold": config.rsi_oversold,
        # 추가 계산 값
        "warning_threshold": _format_pct(config.stop_loss_pct * 0.7),  # 손절의 70%
        "noise_threshold": _format_pct(config.stop_loss_pct * 0.5),  # 손절의 50%
        "take_profit_extended": config.take_profit_pct * 1.2,
        "take_profit_max": config.take_profit_pct * 1.5,
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
    performance_feedback: str,
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
        performance_feedback: 성과 피드백 문자열

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
        "performance_feedback": performance_feedback,
        "stop_loss_display": _format_pct(config.stop_loss_pct),
        "take_profit_display": _format_pct(config.take_profit_pct),
        "trailing_stop_display": _format_pct(config.trailing_stop_pct),
        "min_confluence": config.min_confluence_buy,
        "rsi_overbought": config.rsi_overbought,
        "noise_threshold": _format_pct(config.stop_loss_pct * 0.5),
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
