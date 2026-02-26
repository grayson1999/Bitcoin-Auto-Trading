"""
OpenAI GPT-5 Nano AI 클라이언트 (앙상블 지원)

GPT-5 Nano를 사용하여 매매 신호를 생성합니다.
3x 앙상블 self-consistency로 신호 안정성을 높입니다.
"""

import asyncio
import json
import statistics

from loguru import logger

from src.clients.ai.base import AIClientError, AIResponse
from src.clients.ai.openai_client import OpenAIClient
from src.config import settings
from src.config.constants import DEFAULT_TIMEOUT_SECONDS

ENSEMBLE_COUNT = 3


class AIClient:
    """
    OpenAI GPT-5 Nano AI 클라이언트 (앙상블 지원)

    GPT-5 Nano를 사용하여 매매 신호를 생성합니다.
    ai_ensemble 설정 시 3x 병렬 호출 후 self-consistency로 최종 결과를 선택합니다.
    """

    def __init__(
        self,
        openai_api_key: str | None = None,
        model: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        self._openai_client = OpenAIClient(
            api_key=openai_api_key,
            model=model,
            timeout=timeout,
        )

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.7,
        max_output_tokens: int = 4096,
    ) -> AIResponse:
        """
        텍스트 생성 요청 (앙상블 모드 지원)

        Args:
            prompt: 사용자 프롬프트
            system_instruction: 시스템 지시 (선택)
            temperature: 창의성 파라미터 (0~1)
            max_output_tokens: 최대 출력 토큰 수

        Returns:
            AIResponse: AI 응답 (텍스트, 토큰 사용량 포함)

        Raises:
            AIClientError: API 호출 실패 시
        """
        if settings.ai_ensemble:
            logger.info(f"앙상블 ({ENSEMBLE_COUNT}x) 실행")
            return await self._generate_ensemble(
                prompt, system_instruction, temperature, max_output_tokens
            )

        result = await self._openai_client.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        logger.debug(f"AI 응답 (처음 200자): {result.text[:200]}")
        return result

    async def _generate_ensemble(
        self,
        prompt: str,
        system_instruction: str | None,
        temperature: float,
        max_output_tokens: int,
    ) -> AIResponse:
        """
        3x 병렬 앙상블 (self-consistency)

        action_score 중앙값으로 최종 결과를 선택합니다.
        모든 결과가 다른 방향이면 HOLD로 기본값 설정합니다.
        """
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
        )

    async def health_check(self) -> bool:
        """API 연결 상태 확인"""
        return await self._openai_client.health_check()


# === 싱글톤 인스턴스 ===
_ai_client: AIClient | None = None


def get_ai_client() -> AIClient:
    """AI 클라이언트 싱글톤 반환"""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
