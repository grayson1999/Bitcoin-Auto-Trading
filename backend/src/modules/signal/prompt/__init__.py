"""Signal prompt module - AI prompt building and templates."""

from src.modules.signal.prompt.builder import SignalPromptBuilder
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
from src.modules.signal.prompt.signal_pre_processor import (
    PreComputedSignals,
    pre_compute_signals,
)
from src.modules.signal.prompt.templates import (
    PromptConfig,
    build_small_model_prompt,
    get_analysis_prompt,
    get_config_for_coin,
    get_small_model_system_instruction,
    get_system_instruction,
)

__all__ = [
    # Builder
    "SignalPromptBuilder",
    # Templates
    "PromptConfig",
    "build_small_model_prompt",
    "get_analysis_prompt",
    "get_config_for_coin",
    "get_small_model_system_instruction",
    "get_system_instruction",
    # Pre-processor
    "PreComputedSignals",
    "pre_compute_signals",
    # Indicator Status
    "BIAS_STATUS_KO",
    "BB_STATUS_KO",
    "EMA_STATUS_KO",
    "MACD_STATUS_KO",
    "RSI_STATUS_KO",
    "TIMEFRAME_NAMES_KO",
    "TREND_STATUS_KO",
    "VOLATILITY_STATUS_KO",
    "get_status_ko",
]
