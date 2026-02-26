"""
AI 통합 클라이언트 모듈 (Gemini + OpenAI Fallback + 앙상블)

Google Gemini AI를 기본으로 사용하고,
실패 시 OpenAI로 자동 fallback하는 통합 클라이언트입니다.
소형 모델 fallback 시 전용 프롬프트 + 3x 앙상블을 지원합니다.
"""

import asyncio
import json
import statistics

from loguru import logger

from src.clients.ai.base import AIClientError, AIResponse
from src.clients.ai.gemini_client import GeminiClient
from src.clients.ai.openai_client import OpenAIClient
from src.config import settings
from src.config.constants import DEFAULT_TIMEOUT_SECONDS

ENSEMBLE_COUNT = 3


class AIClient:
    """
    AI 통합 클라이언트 (Gemini + OpenAI Fallback + 앙상블)

    Google Gemini AI를 기본으로 사용하고, 실패 시 OpenAI로 fallback합니다.
    소형 모델 fallback 시 전용 프롬프트와 3x 앙상블을 지원합니다.
    """

    def __init__(
        self,
        gemini_api_key: str | None = None,
        openai_api_key: str | None = None,
        model: str | None = None,
        fallback_model: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ):
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
        fallback_prompt: str | None = None,
        fallback_system_instruction: str | None = None,
        fallback_max_output_tokens: int = 4096,
    ) -> AIResponse:
        """
        텍스트 생성 요청 (Gemini 우선, 실패 시 OpenAI fallback)

        Args:
            prompt: 사용자 프롬프트
            system_instruction: 시스템 지시 (선택)
            temperature: 창의성 파라미터 (0~1)
            max_output_tokens: 최대 출력 토큰 수
            fallback_prompt: 소형 모델 전용 프롬프트 (없으면 기존 prompt 사용)
            fallback_system_instruction: 소형 모델 전용 시스템 지시
            fallback_max_output_tokens: 소형 모델 최대 출력 토큰 수

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

        # 소형 모델 전용 프롬프트 사용
        fb_prompt = fallback_prompt or prompt
        fb_system = fallback_system_instruction or system_instruction
        fb_max_tokens = fallback_max_output_tokens

        try:
            # 앙상블 모드
            if settings.ai_fallback_ensemble and fallback_prompt:
                logger.info(
                    f"OpenAI fallback 앙상블 ({ENSEMBLE_COUNT}x) 실행"
                )
                return await self._generate_ensemble(
                    fb_prompt, fb_system, temperature, fb_max_tokens
                )

            # 단일 호출
            logger.info("OpenAI fallback 사용됨 (전용 프롬프트)")
            result = await self._openai_client.generate(
                prompt=fb_prompt,
                system_instruction=fb_system,
                temperature=temperature,
                max_output_tokens=fb_max_tokens,
            )
            logger.debug(
                f"OpenAI fallback 응답 (처음 200자): {result.text[:200]}"
            )
            return result
        except Exception as e:
            raise AIClientError(
                f"Gemini와 OpenAI 모두 실패. Gemini: {gemini_error}, OpenAI: {e}",
                is_retryable=False,
            ) from e

    async def _generate_ensemble(
        self,
        prompt: str,
        system_instruction: str | None,
        temperature: float,
        max_output_tokens: int,
    ) -> AIResponse:
        """
        소형 모델 3x 병렬 앙상블 (self-consistency)

        action_score 중앙값으로 최종 결과를 선택합니다.
        모든 결과가 다른 방향이면 HOLD로 기본값 설정합니다.
        """
        assert self._openai_client is not None

        # 3x 병렬 호출
        tasks = [
            self._openai_client.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            for _ in range(ENSEMBLE_COUNT)
        ]

        results: list[AIResponse] = []
        exceptions: list[Exception] = []

        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                results.append(result)
            except Exception as e:
                exceptions.append(e)

        if not results:
            raise AIClientError(
                f"앙상블 {ENSEMBLE_COUNT}회 모두 실패: {exceptions}",
                is_retryable=False,
            )

        # action_score 추출
        scores: list[tuple[float, AIResponse]] = []
        for r in results:
            score = self._extract_action_score(r.text)
            if score is not None:
                scores.append((score, r))

        if not scores:
            # action_score 추출 실패 시 첫 번째 결과 반환
            logger.warning("앙상블: action_score 추출 실패, 첫 번째 결과 사용")
            return self._merge_ensemble_result(results[0], results)

        # 신호 방향 분석
        signals = set()
        for score, _ in scores:
            if score >= 0.3:
                signals.add("BUY")
            elif score <= -0.2:
                signals.add("SELL")
            else:
                signals.add("HOLD")

        # 모든 결과가 다른 방향이면 HOLD 선택
        if len(signals) == 3:
            logger.warning(
                "앙상블: 3개 결과 모두 다른 방향 → HOLD 선택"
            )
            # HOLD에 가장 가까운 결과 선택
            hold_candidates = [
                (s, r) for s, r in scores if -0.2 < s < 0.3
            ]
            if hold_candidates:
                chosen = min(hold_candidates, key=lambda x: abs(x[0]))
                return self._merge_ensemble_result(chosen[1], results)

        # 중앙값 action_score에 가장 가까운 결과 선택
        score_values = [s for s, _ in scores]
        median_score = statistics.median(score_values)
        chosen = min(scores, key=lambda x: abs(x[0] - median_score))

        logger.info(
            f"앙상블 결과: scores={score_values}, "
            f"median={median_score:.2f}, chosen={chosen[0]:.2f}"
        )

        return self._merge_ensemble_result(chosen[1], results)

    def _extract_action_score(self, text: str) -> float | None:
        """응답 텍스트에서 action_score 추출"""
        try:
            # JSON 블록 추출
            import re

            json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            json_str = json_match.group(1) if json_match else text
            data = json.loads(json_str)
            score = data.get("action_score")
            if score is not None:
                return max(-1.0, min(1.0, float(score)))
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        return None

    def _merge_ensemble_result(
        self, chosen: AIResponse, all_results: list[AIResponse]
    ) -> AIResponse:
        """앙상블 결과 병합 (토큰 합산, 모델명에 접미사 추가)"""
        total_input = sum(r.input_tokens for r in all_results)
        total_output = sum(r.output_tokens for r in all_results)
        total_cost = sum(r.estimated_cost for r in all_results)

        return AIResponse(
            text=chosen.text,
            model_name=f"{chosen.model_name}-ensemble-{len(all_results)}",
            input_tokens=total_input,
            output_tokens=total_output,
            total_tokens=total_input + total_output,
            estimated_cost=total_cost,
            is_fallback=True,
        )

    async def health_check(self) -> bool:
        """API 연결 상태 확인"""
        return await self._gemini_client.health_check() or (
            self._openai_client is not None and await self._openai_client.health_check()
        )


# === 싱글톤 인스턴스 ===
_ai_client: AIClient | None = None


def get_ai_client() -> AIClient:
    """AI 통합 클라이언트 싱글톤 반환"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
