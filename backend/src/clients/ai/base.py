"""
AI 클라이언트 기본 인터페이스

모든 AI 클라이언트가 구현해야 하는 공통 인터페이스와 데이터 클래스를 정의합니다.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.clients.common import DEFAULT_TIMEOUT, MAX_RETRIES, RETRY_DELAY

# Re-export for backward compatibility
__all__ = ["DEFAULT_TIMEOUT", "MAX_RETRIES", "RETRY_DELAY"]

# === 모델별 토큰 비용 ($ per 1M tokens) ===
COST_CONFIG = {
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
}
TOKENS_PER_M = 1_000_000  # 1M 토큰


@dataclass
class AIResponse:
    """
    AI 응답 데이터 클래스

    Attributes:
        text: 응답 텍스트
        model_name: 사용된 모델 이름
        input_tokens: 입력 토큰 수
        output_tokens: 출력 토큰 수
        total_tokens: 총 토큰 수
        estimated_cost: 예상 비용 ($)
        is_fallback: fallback 모델 사용 여부
    """

    text: str
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    is_fallback: bool = False


class AIClientError(Exception):
    """
    AI 클라이언트 오류 예외

    API 요청 실패 또는 오류 응답 시 발생합니다.

    Attributes:
        message: 오류 메시지
        is_retryable: 재시도 가능 여부
    """

    def __init__(self, message: str, is_retryable: bool = False):
        self.message = message
        self.is_retryable = is_retryable
        super().__init__(self.message)


class BaseAIClient(ABC):
    """
    AI 클라이언트 추상 기본 클래스

    모든 AI 클라이언트(Gemini, OpenAI 등)가 구현해야 하는 인터페이스를 정의합니다.
    """

    def __init__(self, model: str, timeout: float = DEFAULT_TIMEOUT):
        """
        AI 클라이언트 초기화

        Args:
            model: 사용할 모델 이름
            timeout: 요청 타임아웃 (초)
        """
        self.model = model
        self.timeout = timeout

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
    ) -> AIResponse:
        """
        텍스트 생성 요청

        Args:
            prompt: 사용자 프롬프트
            system_instruction: 시스템 지시 (선택)
            temperature: 창의성 파라미터 (0~1)
            max_output_tokens: 최대 출력 토큰 수

        Returns:
            AIResponse: AI 응답

        Raises:
            AIClientError: API 오류 시
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        API 연결 상태 확인

        Returns:
            bool: 연결 정상 여부
        """
        pass

    def _calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """
        모델별 토큰 비용 계산

        Args:
            model: 모델 이름
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수

        Returns:
            float: 예상 비용 ($)
        """
        # 모델별 비용 조회 (기본값: gpt-4o-mini 가격)
        cost = COST_CONFIG.get(model, COST_CONFIG["gpt-4o-mini"])

        input_cost = (input_tokens / TOKENS_PER_M) * cost["input"]
        output_cost = (output_tokens / TOKENS_PER_M) * cost["output"]
        return input_cost + output_cost
