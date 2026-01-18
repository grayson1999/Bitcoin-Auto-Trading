"""
AI 클라이언트 모듈 (Gemini + OpenAI Fallback)

이 모듈은 Google Gemini AI를 기본으로 사용하고,
실패 시 OpenAI로 자동 fallback하는 비동기 클라이언트를 제공합니다.
- 매매 신호 생성을 위한 AI 분석
- 토큰 사용량 추적 (비용 모니터링)
- 재시도 로직 및 타임아웃 처리
- Gemini 실패 시 OpenAI fallback
"""

import asyncio
from dataclasses import dataclass

from google import genai
from google.genai import types
from loguru import logger
from openai import AsyncOpenAI

from src.config import settings

# === AI API 상수 ===
DEFAULT_TIMEOUT = 30.0  # 기본 타임아웃 (초)
MAX_RETRIES = 3  # 최대 재시도 횟수
RETRY_DELAY = 2.0  # 재시도 기본 대기 시간 (초)

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


class AIClient:
    """
    AI 비동기 클라이언트 (Gemini + OpenAI Fallback)

    Google Gemini AI를 기본으로 사용하고, 실패 시 OpenAI로 fallback합니다.
    비동기 요청, 재시도 로직, 토큰 사용량 추적을 지원합니다.

    사용 예시:
        client = AIClient()
        response = await client.generate("시장 분석을 해주세요.")
        print(f"응답: {response.text}")
        print(f"토큰 사용량: {response.total_tokens}")
        print(f"Fallback 사용: {response.is_fallback}")
    """

    def __init__(
        self,
        gemini_api_key: str | None = None,
        openai_api_key: str | None = None,
        model: str | None = None,
        fallback_model: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """
        AI 클라이언트 초기화

        Args:
            gemini_api_key: Gemini API 키 (기본값: 설정 파일에서 로드)
            openai_api_key: OpenAI API 키 (기본값: 설정 파일에서 로드)
            model: 기본 모델 이름 (기본값: 설정 파일에서 로드)
            fallback_model: Fallback 모델 이름 (기본값: 설정 파일에서 로드)
            timeout: 요청 타임아웃 (초)
        """
        self.gemini_api_key = gemini_api_key or settings.gemini_api_key
        self.openai_api_key = openai_api_key or settings.openai_api_key
        self.model = model or settings.ai_model
        self.fallback_model = fallback_model or settings.ai_fallback_model
        self.timeout = timeout
        self._gemini_client: genai.Client | None = None
        self._openai_client: AsyncOpenAI | None = None

    def _get_gemini_client(self) -> genai.Client:
        """
        Gemini 클라이언트 반환 (지연 초기화)

        Returns:
            genai.Client: Gemini 클라이언트 인스턴스
        """
        if self._gemini_client is None:
            self._gemini_client = genai.Client(api_key=self.gemini_api_key)
        return self._gemini_client

    def _get_openai_client(self) -> AsyncOpenAI:
        """
        OpenAI 클라이언트 반환 (지연 초기화)

        Returns:
            AsyncOpenAI: OpenAI 비동기 클라이언트 인스턴스
        """
        if self._openai_client is None:
            self._openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        return self._openai_client

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
            return await self._generate_with_gemini(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
        except AIClientError as e:
            gemini_error = e
            logger.warning(f"Gemini API 실패, OpenAI fallback 시도: {e.message}")

        # 2. OpenAI fallback
        if not self.openai_api_key:
            raise AIClientError(
                f"Gemini 실패 후 OpenAI fallback 불가: OpenAI API 키 미설정. "
                f"원인: {gemini_error}",
                is_retryable=False,
            )

        try:
            return await self._generate_with_openai(
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

    async def _generate_with_gemini(
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
        client = self._get_gemini_client()
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
                    self._call_gemini_api(client, prompt, config),
                    timeout=self.timeout,
                )

                # 응답 파싱 및 토큰 사용량 추출
                return self._parse_gemini_response(response)

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

    async def _generate_with_openai(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
    ) -> AIResponse:
        """
        OpenAI API를 사용한 텍스트 생성 (fallback)

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
        client = self._get_openai_client()
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
                        model=self.fallback_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_output_tokens,
                    ),
                    timeout=self.timeout,
                )

                # 응답 파싱
                return self._parse_openai_response(response)

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

    async def _call_gemini_api(
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

    def _parse_gemini_response(
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
        self._log_token_usage(self.model, input_tokens, output_tokens, estimated_cost)

        return AIResponse(
            text=text,
            model_name=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            is_fallback=False,
        )

    def _parse_openai_response(self, response) -> AIResponse:
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
        estimated_cost = self._calculate_cost(
            self.fallback_model, input_tokens, output_tokens
        )

        # 토큰 사용량 로깅
        self._log_token_usage(
            self.fallback_model, input_tokens, output_tokens, estimated_cost
        )

        logger.info(f"OpenAI fallback 사용됨 (모델: {self.fallback_model})")

        return AIResponse(
            text=text,
            model_name=self.fallback_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            is_fallback=True,
        )

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

    def _log_token_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
    ) -> None:
        """
        토큰 사용량 로깅

        비용 추적을 위해 토큰 사용량을 로그에 기록합니다.

        Args:
            model: 사용된 모델 이름
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수
            cost: 예상 비용 ($)
        """
        logger.info(
            f"AI 토큰 사용량 [{model}] - "
            f"입력: {input_tokens:,}, "
            f"출력: {output_tokens:,}, "
            f"총: {input_tokens + output_tokens:,}, "
            f"예상비용: ${cost:.6f}"
        )

    async def health_check(self) -> bool:
        """
        API 연결 상태 확인

        간단한 요청을 보내 API가 정상 작동하는지 확인합니다.

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
_ai_client: AIClient | None = None


def get_ai_client() -> AIClient:
    """
    AI 클라이언트 싱글톤 반환

    애플리케이션 전체에서 동일한 클라이언트 인스턴스를 공유합니다.

    Returns:
        AIClient: 싱글톤 클라이언트 인스턴스
    """
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
