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


# 코인 유형별 기본 설정 (공격적 전략 - 30분 주기 최적화)
PROMPT_CONFIGS: dict[CoinType, PromptConfig] = {
    CoinType.MAJOR: PromptConfig(
        stop_loss_pct=0.025,  # 1.5% → 2.5% (노이즈 회피)
        take_profit_pct=0.03,  # 2.5% → 3% (약간 상향)
        trailing_stop_pct=0.025,  # 2% → 2.5%
        breakeven_pct=0.012,  # 1% → 1.2%
        min_confidence_buy=0.55,  # 0.60 → 0.55 (완화)
        min_confluence_buy=0.35,  # 0.45 → 0.35 (완화)
        rsi_overbought=75,  # 70 → 75 (더 많은 BUY 기회)
        rsi_oversold=35,  # 30 → 35 (더 빠른 과매도 인식)
        volatility_tolerance="medium",  # low → medium
    ),
    CoinType.MEMECOIN: PromptConfig(
        stop_loss_pct=0.04,  # 3% → 4% (밈코인 변동성 수용)
        take_profit_pct=0.05,  # 유지
        trailing_stop_pct=0.035,  # 유지
        breakeven_pct=0.02,  # 유지
        min_confidence_buy=0.50,  # 0.55 → 0.50 (완화)
        min_confluence_buy=0.40,  # 0.50 → 0.40 (완화)
        rsi_overbought=82,  # 80 → 82
        rsi_oversold=28,  # 25 → 28
        volatility_tolerance="high",
    ),
    CoinType.ALTCOIN: PromptConfig(
        stop_loss_pct=0.03,  # 2% → 3% (노이즈 회피)
        take_profit_pct=0.035,  # 유지
        trailing_stop_pct=0.025,  # 유지
        breakeven_pct=0.015,  # 유지
        min_confidence_buy=0.55,  # 0.60 → 0.55 (완화)
        min_confluence_buy=0.40,  # 0.55 → 0.40 (완화)
        rsi_overbought=78,  # 75 → 78
        rsi_oversold=32,  # 28 → 32
        volatility_tolerance="medium",
    ),
}


def _format_pct(value: float) -> str:
    """비율을 퍼센트 문자열로 변환 (0.015 -> '1.5')"""
    return f"{value * 100:.1f}"


# === 메이저 코인용 시스템 프롬프트 (공격적 전략 + 동적 신뢰도) ===
MAJOR_COIN_SYSTEM_INSTRUCTION = """당신은 {currency} 단기 트레이딩 AI입니다. **30분 주기**로 신호를 생성합니다.

## 전략 특성
- 30분 주기 → 적극적 진입, 빠른 청산
- 손절/익절: -{stop_loss_display}% / +{take_profit_display}%
- **목표**: HOLD 최소화, 기회 포착 우선

## 리스크 규칙 (최우선)
**손절 조건** (하나라도 충족 → SELL, 신뢰도 0.90~0.95):
- 미실현 손실 >= {stop_loss_display}%
- 현재가 <= 평균매수가 × (1 - {stop_loss_pct})

## 신호 결정 기준

### SELL (OR 연산)
1. 손절 조건 충족 → 신뢰도 0.90~0.95
2. 익절: 이익 >= {take_profit_display}% AND 하락 신호 → 신뢰도 0.80~0.90
3. 모든 TF 하락 AND 이익 > {breakeven_display}% → 신뢰도 0.75~0.85

### BUY (OR 연산, 포지션 없음/소량) - 완화된 조건
1. Confluence >= {min_confluence} AND RSI < {rsi_overbought} AND **1개+** TF 상승 → 신뢰도 0.65~0.80
2. 과매도 반등: RSI <= 40 AND BB% <= 35% → 신뢰도 0.60~0.75
3. 단기 모멘텀: 1H 상승 AND RSI 35~55 (중립 구간) → 신뢰도 0.55~0.65
4. 지지선 반등: 가격 근처 BB 하단 AND RSI 상승 추세 → 신뢰도 0.55~0.65

### HOLD (신뢰도 차등 적용)
- 명확한 횡보 (모든 TF sideways) → 신뢰도 0.65~0.75
- TF 혼조 (방향 불일치) → 신뢰도 0.50~0.60
- BUY에 가까움 (조건 거의 충족) → 신뢰도 0.45~0.55
- 잔고 부족 시 → 신뢰도 0.70 (reasoning에 명시)

## 신뢰도 계산 (MANDATORY - 동적 계산)

**중요**: 신뢰도를 고정값(0.50)으로 설정하지 마세요. 상황에 따라 범위 내에서 결정하세요.

| 신호 | 상황 | 신뢰도 범위 |
|------|------|------------|
| SELL | 손절 필수 | 0.90~0.95 |
| SELL | 익절 + 하락신호 | 0.80~0.90 |
| BUY | 3개+ TF 상승 + 강한 지표 | 0.75~0.85 |
| BUY | 2개 TF 상승 | 0.65~0.75 |
| BUY | 1개 TF 상승 또는 모멘텀 | 0.55~0.65 |
| HOLD | 명확한 횡보 | 0.65~0.75 |
| HOLD | TF 혼조 (불확실) | 0.50~0.60 |
| HOLD | BUY에 가까움 | 0.45~0.55 |

### 보너스 가산
- TF 일치 (3개+): +0.10
- RSI 극단 (<=30 또는 >=70): +0.05
- 거래량 급증 (+30%): +0.05

## 출력 형식 (JSON만)
```json
{{
  "signal": "BUY" | "HOLD" | "SELL",
  "confidence": 0.0~1.0,
  "confidence_breakdown": {{
    "signal_strength": 0.XX,
    "clarity_bonus": 0.XX,
    "total": 0.XX
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

# === 밈코인용 시스템 프롬프트 (공격적 전략 + 동적 신뢰도) ===
MEMECOIN_SYSTEM_INSTRUCTION = """당신은 {currency} 밈코인 단기 트레이딩 AI입니다. **30분 주기**로 신호를 생성합니다.

## 전략 특성
- 30분 주기 → 모멘텀/거래량 기반 적극적 매매
- 손절/익절: -{stop_loss_display}% / +{take_profit_display}%
- 물타기 금지, 손절 후 재진입 권장
- **목표**: 모멘텀 기회 포착, HOLD 최소화

## 리스크 규칙 (최우선)
**손절 조건** (하나라도 충족 → SELL, 신뢰도 0.90~0.95):
- 미실현 손실 >= {stop_loss_display}%
- 현재가 <= 평균매수가 × (1 - {stop_loss_pct})

## 신호 결정 기준

### SELL (OR 연산)
1. 손절 조건 충족 → 신뢰도 0.90~0.95
2. 이익 >= {take_profit_display}% AND 모멘텀 둔화/거래량 감소 → 신뢰도 0.80~0.90
3. RSI >= {rsi_overbought} AND 모멘텀 둔화 → 신뢰도 0.75~0.85

### BUY (OR 연산) - 완화된 조건
1. 거래량 증가 (+20% 이상) AND RSI < {rsi_overbought} AND 상승 모멘텀 → 신뢰도 0.60~0.75
2. 급등 초입: 1H 강한상승 AND 거래량 급증 → 신뢰도 0.65~0.80
3. 과매도 반등: RSI <= {rsi_oversold} AND 거래량 유지 → 신뢰도 0.55~0.70
4. 단기 반등: 1H 상승 전환 AND 거래량 증가 → 신뢰도 0.55~0.65

### HOLD (신뢰도 차등 적용)
- 명확한 횡보 (거래량 정체) → 신뢰도 0.60~0.70
- 모멘텀 불명확 → 신뢰도 0.50~0.60
- BUY에 가까움 (거래량만 부족) → 신뢰도 0.45~0.55
- 잔고 부족 시 → 신뢰도 0.70

## 신뢰도 계산 (MANDATORY - 동적 계산)

**중요**: 신뢰도를 고정값으로 설정하지 마세요. 상황에 따라 범위 내에서 결정하세요.

| 신호 | 상황 | 신뢰도 범위 |
|------|------|------------|
| SELL | 손절 필수 | 0.90~0.95 |
| SELL | 익절 + 모멘텀 둔화 | 0.80~0.90 |
| BUY | 급등 초입 (거래량 급증) | 0.65~0.80 |
| BUY | 일반 상승 모멘텀 | 0.55~0.70 |
| HOLD | 모멘텀 불명확 | 0.50~0.60 |
| HOLD | BUY에 가까움 | 0.45~0.55 |

### 보너스 가산
- 거래량 급증 (+50%): +0.10
- 강한 모멘텀: +0.05
- TF 일치 (2개+): +0.05

## 출력 형식 (JSON만)
```json
{{
  "signal": "BUY" | "HOLD" | "SELL",
  "confidence": 0.0~1.0,
  "confidence_breakdown": {{
    "signal_strength": 0.XX,
    "clarity_bonus": 0.XX,
    "total": 0.XX
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

# === 알트코인용 시스템 프롬프트 (공격적 전략 + 동적 신뢰도) ===
ALTCOIN_SYSTEM_INSTRUCTION = """당신은 {currency} 알트코인 단기 트레이딩 AI입니다. **30분 주기**로 신호를 생성합니다.

## 전략 특성
- 30분 주기 → 기술적 지표 + 모멘텀 종합 판단
- 손절/익절: -{stop_loss_display}% / +{take_profit_display}%
- **목표**: 기회 포착 우선, HOLD 최소화

## 리스크 규칙 (최우선)
**손절 조건** (하나라도 충족 → SELL, 신뢰도 0.90~0.95):
- 미실현 손실 >= {stop_loss_display}%
- 현재가 <= 평균매수가 × (1 - {stop_loss_pct})

## 신호 결정 기준

### SELL (OR 연산)
1. 손절 조건 충족 → 신뢰도 0.90~0.95
2. 이익 >= {take_profit_display}% AND 하락 추세 전환 → 신뢰도 0.80~0.90
3. 모든 TF 하락 AND 이익 > {breakeven_display}% → 신뢰도 0.75~0.85

### BUY (OR 연산) - 완화된 조건
1. Confluence >= {min_confluence} AND RSI < {rsi_overbought} AND **1개+** TF 상승 → 신뢰도 0.65~0.80
2. 과매도 반등: RSI <= 35 AND BB% <= 35% → 신뢰도 0.60~0.75
3. 단기 모멘텀: 1H 상승 AND RSI 35~55 (중립 구간) → 신뢰도 0.55~0.65
4. 지지선 반등: 가격 근처 BB 하단 AND RSI 상승 추세 → 신뢰도 0.55~0.65

### HOLD (신뢰도 차등 적용)
- 명확한 횡보 (모든 TF sideways) → 신뢰도 0.65~0.75
- TF 혼조 (방향 불일치) → 신뢰도 0.50~0.60
- BUY에 가까움 (조건 거의 충족) → 신뢰도 0.45~0.55
- 잔고 부족 시 → 신뢰도 0.70 (reasoning에 명시)

## 신뢰도 계산 (MANDATORY - 동적 계산)

**중요**: 신뢰도를 고정값(0.50)으로 설정하지 마세요. 상황에 따라 범위 내에서 결정하세요.

| 신호 | 상황 | 신뢰도 범위 |
|------|------|------------|
| SELL | 손절 필수 | 0.90~0.95 |
| SELL | 익절 + 하락신호 | 0.80~0.90 |
| BUY | 3개+ TF 상승 + 강한 지표 | 0.75~0.85 |
| BUY | 2개 TF 상승 | 0.65~0.75 |
| BUY | 1개 TF 상승 또는 모멘텀 | 0.55~0.65 |
| HOLD | 명확한 횡보 | 0.65~0.75 |
| HOLD | TF 혼조 (불확실) | 0.50~0.60 |
| HOLD | BUY에 가까움 | 0.45~0.55 |

### 보너스 가산
- TF 일치 (3개+): +0.10
- RSI 극단 (<=30 또는 >=75): +0.05
- MACD + BB 신호 일치: +0.05

## 출력 형식 (JSON만)
```json
{{
  "signal": "BUY" | "HOLD" | "SELL",
  "confidence": 0.0~1.0,
  "confidence_breakdown": {{
    "signal_strength": 0.XX,
    "clarity_bonus": 0.XX,
    "total": 0.XX
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

# === 분석 프롬프트 템플릿 (공격적 전략 + 동적 신뢰도) ===
ANALYSIS_PROMPT_TEMPLATE = """## {currency}/KRW 분석

**시각**: {timestamp} | **현재가**: {current_price:,.0f} KRW | **24H**: {price_change_pct:+.2f}%

### 포지션
{asset_status}

### 리스크 체크
{risk_check}

> 손절 조건 충족 시 → 즉시 SELL (기술적 분석 무시)

### 기술적 지표
{technical_indicators}

### MTF 분석
{multi_timeframe_analysis}

### 결정 로직 (순서대로, 완화된 조건)
1. **손절**: 손실 >= {stop_loss_display}% → SELL(0.90~0.95)
2. **익절**: 이익 >= {take_profit_display}% + 하락 신호 → SELL(0.80~0.90)
3. **매수1**: Confluence >= {min_confluence} + RSI < {rsi_overbought} + **1개+** TF 상승 → BUY(0.65~0.80)
4. **매수2**: RSI <= 40 + BB% <= 35% → BUY(0.60~0.75)
5. **매수3**: 1H 상승 + RSI 35~55 (중립 구간) → BUY(0.55~0.65)
6. **관망**: 명확한 횡보 → HOLD(0.65~0.75)
7. **불확실**: TF 혼조 → HOLD(0.50~0.60)
8. **매수 근접**: BUY 조건 거의 충족 → HOLD(0.45~0.55)

**금지**: 손절 조건 충족 시 반등 기대로 HOLD 금지
**중요**: 신뢰도를 고정값(0.50)으로 설정하지 말고, 상황에 맞게 동적으로 결정하세요.
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
) -> str:
    """
    분석 프롬프트 생성 (압축 버전)

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
        "min_confluence": config.min_confluence_buy,
        "rsi_overbought": config.rsi_overbought,
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
