import os
import time
from typing import Any, Dict

import openai

from dotenv import load_dotenv
from pathlib import Path
env_path = Path(__file__).resolve().parents[3] / "config" / ".env"
load_dotenv(env_path)


# ─── 환경 변수에서 API 키 로드 ─────────────────────────────────────────────
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("환경 변수 OPENAI_API_KEY가 설정되지 않았습니다.")

# OpenAI client 초기화 (v1.x 스타일)
client = openai.OpenAI(api_key=api_key)

# ─── 재시도 설정 ────────────────────────────────────────────────────────
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # 지수 백오프 계수

def send_signal_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ChatGPT API에 매매 신호 요청을 보내고, 원시 응답을 dict로 반환합니다.

    요청 페이로드 스펙:
      필수 필드:
        - model (str): 사용할 모델 이름 (예: "gpt-3.5-turbo")
        - messages (List[Dict[str, str]]): 역할(role)과 내용(content)을 담은 메시지 리스트
            * 예시:
                [
                  {"role": "system", "content": "시장 상황 분석 모드 활성화"},
                  {"role": "user",   "content": "비트코인 매수 신호를 알려줘"}
                ]
      선택 필드:
        - temperature (float): 생성 다양성 조절 (기본값 0.7)
        - max_tokens (int): 최대 토큰 수 (기본값 150)
        - top_p (float): nucleus sampling 비율 (기본값 1.0)
        - timeout (int): 요청 타임아웃(초) → 내부적으로 request_timeout에 매핑 (기본값 15)
        - n (int): 생성할 응답 개수
        - stop (List[str] | str): 응답 중단 토큰
        - 기타 openai.ChatCompletion.create() 옵션

    :param data: 위 스펙에 맞춘 dict
    :return: API 응답 JSON이 model_dump()된 dict
    :raises: RateLimitError, Timeout, APIError 등
    """
    # data에서 timeout만 분리
    payload = data.copy()
    timeout = payload.pop("timeout", 15)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                **payload,
                timeout=timeout
            )
            return response.model_dump()
        except Exception as e:
            if attempt == MAX_RETRIES:
                # 마지막 시도 실패 시 예외 전달
                raise
            # 지수 백오프
            wait = BACKOFF_FACTOR ** attempt
            time.sleep(wait)

    # 이 지점에는 도달하지 않습니다.
    raise RuntimeError("send_signal_request: 알 수 없는 오류 발생")

if __name__ == "__main__":
    # 테스트용 예시
    try:
        result = send_signal_request({
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "안녕하세요"}],
            "temperature": 0.7,
            "max_tokens": 100
        })
        print("응답:", result) 
    except Exception as e:
        print("오류 발생:", e)