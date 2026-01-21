"""
Gemini AI 클라이언트 모듈

Google Gemini AI API를 사용한 텍스트 생성 클라이언트입니다.
"""

import asyncio

from google import genai
from google.genai import types
from loguru import logger

from src.clients.ai.base import (
    AIClientError,
    AIResponse,
    BaseAIClient,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
)
from src.config import settings


class GeminiClient(BaseAIClient):
    """
    Gemini AI 클라이언트

    Google Gemini AI API를 사용하여 텍스트 생성 기능을 제공합니다.

    사용 예시:
        client = GeminiClient()
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
        Gemini 클라이언트 초기화

        Args:
            api_key: Gemini API 키 (기본값: 설정 파일에서 로드)
            model: 모델 이름 (기본값: 설정 파일에서 로드)
            timeout: 요청 타임아웃 (초)
        """
        model = model or settings.ai_model
        super().__init__(model=model, timeout=timeout)

        self.api_key = api_key or settings.gemini_api_key
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        """
        Gemini 클라이언트 반환 (지연 초기화)

        Returns:
            genai.Client: Gemini 클라이언트 인스턴스
        """
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
    ) -> AIResponse:
        """
        Gemini API를 사용한 텍스트 생성

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

        # 설정 구성
        # thinking_budget=0: Gemini 2.5의 thinking 기능 비활성화 (토큰 절약)
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )

        # 재시도 로직
        for attempt in range(MAX_RETRIES):
            try:
                # 타임아웃과 함께 비동기 실행
                response = await asyncio.wait_for(
                    self._call_api(client, prompt, config),
                    timeout=self.timeout,
                )

                # 응답 파싱 및 토큰 사용량 추출
                return self._parse_response(response)

            except TimeoutError:
                last_error = TimeoutError(
                    f"Gemini API 요청 타임아웃 ({self.timeout}초)"
                )
                logger.warning(
                    f"Gemini API 타임아웃 (시도 {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                # 재시도 불가능한 오류 (API 키 문제, 할당량 초과 등)
                if "api_key" in error_msg or "invalid" in error_msg:
                    raise AIClientError(
                        f"Gemini API 인증 오류: {e}",
                        is_retryable=False,
                    ) from e

                if "quota" in error_msg or "rate" in error_msg or "429" in error_msg:
                    raise AIClientError(
                        "AI API 요청 한도 초과 (Rate Limit). 잠시 후 다시 시도해주세요.",
                        is_retryable=True,
                    ) from e

                logger.warning(
                    f"Gemini API 오류 (시도 {attempt + 1}/{MAX_RETRIES}): {e}"
                )
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))

        raise AIClientError(
            f"{MAX_RETRIES}회 재시도 후 Gemini API 요청 실패: {last_error}",
            is_retryable=False,
        )

    async def _call_api(
        self,
        client: genai.Client,
        prompt: str,
        config: types.GenerateContentConfig,
    ) -> types.GenerateContentResponse:
        """
        Gemini API 호출 수행

        Args:
            client: Gemini 클라이언트
            prompt: 프롬프트
            config: 생성 설정

        Returns:
            GenerateContentResponse: API 응답
        """
        # google-genai SDK는 동기 방식이므로 별도 스레드에서 실행
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            ),
        )

    def _parse_response(
        self,
        response: types.GenerateContentResponse,
    ) -> AIResponse:
        """
        Gemini API 응답 파싱

        응답에서 텍스트와 토큰 사용량을 추출합니다.

        Args:
            response: Gemini API 응답

        Returns:
            AIResponse: 파싱된 응답
        """
        # 텍스트 추출
        text = response.text or ""

        # 토큰 사용량 추출
        usage = response.usage_metadata
        input_tokens = usage.prompt_token_count if usage else 0
        output_tokens = usage.candidates_token_count if usage else 0
        total_tokens = usage.total_token_count if usage else 0

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
            is_fallback=False,
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
            f"AI 토큰 사용량 [{self.model}] - "
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
_gemini_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    """
    Gemini 클라이언트 싱글톤 반환

    Returns:
        GeminiClient: 싱글톤 클라이언트 인스턴스
    """
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
