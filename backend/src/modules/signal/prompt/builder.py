"""
신호 생성 프롬프트 빌더 모듈

이 모듈은 AI 매매 신호 생성을 위한 기술적 스냅샷 생성을 담당합니다.
"""

import json
from datetime import datetime

from src.modules.market import MultiTimeframeResult
from src.modules.signal.classifier import CoinType
from src.modules.signal.prompt.templates import PromptConfig
from src.utils import UTC


class SignalPromptBuilder:
    """
    신호 생성 프롬프트 빌더

    기술적 지표 스냅샷 생성을 담당합니다.
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
            coin_type: 코인 유형
        """
        self.currency = currency
        self.prompt_config = prompt_config
        self.coin_type = coin_type

    def create_technical_snapshot(self, mtf_result: MultiTimeframeResult) -> str:
        """
        기술적 지표 스냅샷 생성 (JSON)

        Args:
            mtf_result: 멀티 타임프레임 분석 결과

        Returns:
            str: JSON 문자열
        """
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
