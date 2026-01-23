"""
OpenAI 클라이언트 모듈

OpenAI API를 사용한 텍스트 생성 클라이언트입니다.
Gemini API 실패 시 fallback으로 사용됩니다.
"""

import asyncio

from loguru import logger
from openai import AsyncOpenAI

from src.clients.ai.base import (
    AIClientError,
    AIResponse,
    BaseAIClient,
)
from src.config import settings
from src.config.constants import DEFAULT_MAX_RETRIES as MAX_RETRIES
from src.config.constants import DEFAULT_RETRY_DELAY_SECONDS as RETRY_DELAY
from src.config.constants import DEFAULT_TIMEOUT_SECONDS as DEFAULT_TIMEOUT


class OpenAIClient(BaseAIClient):
    """
    OpenAI 클라이언트

    OpenAI API를 사용하여 텍스트 생성 기능을 제공합니다.
    주로 Gemini API 실패 시 fallback으로 사용됩니다.

    사용 예시:
        client = OpenAIClient()
        response = await client.generate("시장 분석을 해주세요.")
        print(f"응답: {response.text}")
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        OpenAI 클라이언트 초기화

        Args:
            api_key: OpenAI API 키 (기본값: 설정 파일에서 로드)
            model: 모델 이름 (기본값: 설정 파일에서 로드)
            timeout: 요청 타임아웃 (초)
        """
        model = model or settings.ai_fallback_model
        super().__init__(model=model, timeout=timeout)

        self.api_key = api_key or settings.openai_api_key
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        """
        OpenAI 클라이언트 반환 (지연 초기화)

        Returns:
            AsyncOpenAI: OpenAI 비동기 클라이언트 인스턴스
        """
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
    ) -> AIResponse:
        """
        OpenAI API를 사용한 텍스트 생성

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
        client = self._get_client()
        last_error: Exception | None = None

        # 메시지 구성
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        # 재시도 로직
        for attempt in range(MAX_RETRIES):
            try:
                # 타임아웃과 함께 비동기 실행
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_output_tokens,
                    ),
                    timeout=self.timeout,
                )

                # 응답 파싱
                return self._parse_response(response)

            except TimeoutError:
                last_error = TimeoutError(
                    f"OpenAI API 요청 타임아웃 ({self.timeout}초)"
                )
                logger.warning(
                    f"OpenAI API 타임아웃 (시도 {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                # 재시도 불가능한 오류
                if "api_key" in error_msg or "invalid" in error_msg:
                    raise AIClientError(
                        f"OpenAI API 인증 오류: {e}",
                        is_retryable=False,
                    ) from e

                if "quota" in error_msg or "rate" in error_msg or "429" in error_msg:
                    raise AIClientError(
                        "AI API 요청 한도 초과 (Rate Limit). 잠시 후 다시 시도해주세요.",
                        is_retryable=True,
                    ) from e

                logger.warning(
                    f"OpenAI API 오류 (시도 {attempt + 1}/{MAX_RETRIES}): {e}"
                )
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))

        raise AIClientError(
            f"{MAX_RETRIES}회 재시도 후 OpenAI API 요청 실패: {last_error}",
            is_retryable=False,
        )

    def _parse_response(self, response) -> AIResponse:
        """
        OpenAI API 응답 파싱

        응답에서 텍스트와 토큰 사용량을 추출합니다.

        Args:
            response: OpenAI API 응답

        Returns:
            AIResponse: 파싱된 응답
        """
        # 텍스트 추출
        text = response.choices[0].message.content or ""

        # 토큰 사용량 추출
        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0

        # 비용 계산
        estimated_cost = self._calculate_cost(self.model, input_tokens, output_tokens)

        # 토큰 사용량 로깅
        self._log_token_usage(input_tokens, output_tokens, estimated_cost)

        return AIResponse(
            text=text,
            model_name=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            is_fallback=True,  # OpenAI는 항상 fallback으로 표시
        )

    def _log_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cost: float,
    ) -> None:
        """
        토큰 사용량 로깅

        Args:
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수
            cost: 예상 비용 ($)
        """
        logger.info(
            f"AI 토큰 사용량 [{self.model}] (Fallback) - "
            f"입력: {input_tokens:,}, "
            f"출력: {output_tokens:,}, "
            f"총: {input_tokens + output_tokens:,}, "
            f"예상비용: ${cost:.6f}"
        )

    async def health_check(self) -> bool:
        """
        API 연결 상태 확인

        Returns:
            bool: 연결 정상 여부
        """
        try:
            await self.generate(
                prompt="Hello",
                max_output_tokens=10,
            )
            return True
        except AIClientError:
            return False


# === 싱글톤 인스턴스 ===
_openai_client: OpenAIClient | None = None


def get_openai_client() -> OpenAIClient:
    """
    OpenAI 클라이언트 싱글톤 반환

    Returns:
        OpenAIClient: 싱글톤 클라이언트 인스턴스
    """
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAIClient()
    return _openai_client
