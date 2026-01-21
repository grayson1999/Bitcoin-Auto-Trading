"""
AI 통합 클라이언트 모듈 (Gemini + OpenAI Fallback)

Google Gemini AI를 기본으로 사용하고,
실패 시 OpenAI로 자동 fallback하는 통합 클라이언트입니다.
"""

from loguru import logger

from src.clients.ai.base import AIClientError, AIResponse
from src.clients.ai.gemini_client import GeminiClient
from src.clients.ai.openai_client import OpenAIClient
from src.config import settings


class AIClient:
    """
    AI 통합 클라이언트 (Gemini + OpenAI Fallback)

    Google Gemini AI를 기본으로 사용하고, 실패 시 OpenAI로 fallback합니다.

    사용 예시:
        client = AIClient()
        response = await client.generate("시장 분석을 해주세요.")
        print(f"응답: {response.text}")
        print(f"Fallback 사용: {response.is_fallback}")
    """

    def __init__(
        self,
        gemini_api_key: str | None = None,
        openai_api_key: str | None = None,
        model: str | None = None,
        fallback_model: str | None = None,
        timeout: float = 30.0,
    ):
        """
        AI 통합 클라이언트 초기화

        Args:
            gemini_api_key: Gemini API 키 (기본값: 설정 파일에서 로드)
            openai_api_key: OpenAI API 키 (기본값: 설정 파일에서 로드)
            model: 기본 모델 이름 (기본값: 설정 파일에서 로드)
            fallback_model: Fallback 모델 이름 (기본값: 설정 파일에서 로드)
            timeout: 요청 타임아웃 (초)
        """
        self.openai_api_key = openai_api_key or settings.openai_api_key

        self._gemini_client = GeminiClient(
            api_key=gemini_api_key,
            model=model,
            timeout=timeout,
        )
        self._openai_client: OpenAIClient | None = None
        if self.openai_api_key:
            self._openai_client = OpenAIClient(
                api_key=openai_api_key,
                model=fallback_model,
                timeout=timeout,
            )

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
    ) -> AIResponse:
        """
        텍스트 생성 요청 (Gemini 우선, 실패 시 OpenAI fallback)

        프롬프트를 AI 모델에 전달하고 응답을 반환합니다.
        Gemini API 실패 시 자동으로 OpenAI로 fallback합니다.

        Args:
            prompt: 사용자 프롬프트
            system_instruction: 시스템 지시 (선택)
            temperature: 창의성 파라미터 (0~1)
            max_output_tokens: 최대 출력 토큰 수

        Returns:
            AIResponse: AI 응답 (텍스트, 토큰 사용량 포함)

        Raises:
            AIClientError: Gemini와 OpenAI 모두 실패 시
        """
        gemini_error: Exception | None = None

        # 1. Gemini API 시도
        try:
            return await self._gemini_client.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
        except AIClientError as e:
            gemini_error = e
            logger.warning(f"Gemini API 실패, OpenAI fallback 시도: {e.message}")

        # 2. OpenAI fallback
        if not self._openai_client:
            raise AIClientError(
                f"Gemini 실패 후 OpenAI fallback 불가: OpenAI API 키 미설정. "
                f"원인: {gemini_error}",
                is_retryable=False,
            )

        try:
            logger.info("OpenAI fallback 사용됨")
            return await self._openai_client.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
        except Exception as e:
            raise AIClientError(
                f"Gemini와 OpenAI 모두 실패. Gemini: {gemini_error}, OpenAI: {e}",
                is_retryable=False,
            ) from e

    async def health_check(self) -> bool:
        """
        API 연결 상태 확인

        Returns:
            bool: 연결 정상 여부 (Gemini 또는 OpenAI 중 하나라도 정상이면 True)
        """
        # Gemini 먼저 확인
        if await self._gemini_client.health_check():
            return True

        # Gemini 실패 시 OpenAI 확인
        if self._openai_client and await self._openai_client.health_check():
            return True

        return False


# === 싱글톤 인스턴스 ===
_ai_client: AIClient | None = None


def get_ai_client() -> AIClient:
    """
    AI 통합 클라이언트 싱글톤 반환

    애플리케이션 전체에서 동일한 클라이언트 인스턴스를 공유합니다.

    Returns:
        AIClient: 싱글톤 클라이언트 인스턴스
    """
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
