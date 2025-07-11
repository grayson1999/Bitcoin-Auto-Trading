import os
import time
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import openai

from dotenv import load_dotenv
from pathlib import Path
env_path = Path(__file__).resolve().parents[3] / "config" / ".env"
load_dotenv(env_path)


# ─── 데이터 클래스 정의 ───────────────────────────────────────────────────
@dataclass
class SignalResponse:
    """ChatGPT 응답을 구조화하기 위한 데이터 클래스"""
    signal: str
    reason: str
    confidence: float
    raw_response: Optional[Dict[str, Any]] = None


# ─── 환경 변수에서 API 키 로드 ─────────────────────────────────────────────
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("환경 변수 OPENAI_API_KEY가 설정되지 않았습니다.")

client = openai.OpenAI(api_key=api_key)

# ─── 설정 ────────────────────────────────────────────────────────────────
MAX_RETRIES = 3
BACKOFF_FACTOR = 2
CONFIDENCE_THRESHOLD = 0.4
RETRY_DELAY_SECONDS = 10

def _parse_to_signal_response(raw_dump: Dict[str, Any]) -> SignalResponse:
    """
    OpenAI API의 원시 응답 dict를 SignalResponse 객체로 파싱합니다.
    파싱 오류 발생 시, 오류 정보를 담은 기본 객체를 반환합니다.

    :param raw_dump: OpenAI 응답의 model_dump()
    :return: 파싱된 SignalResponse 객체
    """
    try:
        message_content = raw_dump['choices'][0]['message']['content']
        # 마크다운 코드 블록 제거
        if message_content.startswith('```json') and message_content.endswith('```'):
            json_string = message_content[len('```json\n'):-len('\n```')]
        else:
            json_string = message_content
        parsed_content = json.loads(json_string)

        return SignalResponse(
            signal=parsed_content.get('signal', 'N/A'),
            reason=parsed_content.get('reason', 'No reason provided'),
            confidence=float(parsed_content.get('confidence', 0.0)),
            raw_response=raw_dump
        )

    except (json.JSONDecodeError, TypeError, KeyError, ValueError) as e:
        content_for_error = raw_dump.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')
        return SignalResponse(
            signal='parsing_error',
            reason=f"Failed to parse content: '{content_for_error}'. Error: {e}",
            confidence=0.0,
            raw_response=raw_dump
        )

def send_signal_request(data: Dict[str, Any]) -> SignalResponse:
    """
    ChatGPT API에 매매 신호 요청을 보냅니다.
    신뢰도가 임계값 미만이면 10초 후 재시도합니다.

    :param data: OpenAI API 요청 페이로드
    :return: 파싱된 SignalResponse 객체
    :raises: OpenAI 관련 예외 및 RuntimeError
    """
    payload = data.copy()
    timeout = payload.pop("timeout", 15)
    if "max_tokens" not in payload:
        payload["max_tokens"] = 500 # 기본값 설정

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                **payload,
                timeout=timeout
            )
            signal_response = _parse_to_signal_response(response.model_dump())

            # 신뢰도 또는 파싱 오류 확인
            if signal_response.confidence < CONFIDENCE_THRESHOLD or signal_response.signal == 'parsing_error':
                if attempt == MAX_RETRIES:
                    return signal_response  # 마지막 시도면 그냥 반환
                
                time.sleep(RETRY_DELAY_SECONDS)
                continue  # 재시도
            
            return signal_response # 신뢰도 통과 및 파싱 성공 시 즉시 반환

        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            wait = BACKOFF_FACTOR ** attempt
            time.sleep(wait)

    raise RuntimeError("send_signal_request: 알 수 없는 오류 발생")


if __name__ == "__main__":
    try:
        result = send_signal_request({
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a quantitative trading signal generator. "
                        "When you reply, output a JSON object with exactly three fields: "
                        "1) signal: one of [\"buy\", \"hold\", \"sell\"] (lowercase), "
                        "2) reason: in Korean, 구체적인 근거(예: 최근 24시간 가격 변동률, 5분·1시간 이동평균 값, 거래량 등 주요 지표)를 포함하여 설명, "
                        "3) confidence: 0~1 사이 부동소수점, 그리고 간단한 설명(confidence_reason)도 한 문장 정도 덧붙여 주세요."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "현재 비트코인 가격과 주요 지표를 기반으로 매수·보류·매도 중 하나를 추천해 주세요."
                    )
                }
            ],
            "temperature": 0.5,
            "max_tokens": 500
        })

        print("응답 객체:", result)
        print("신호:", result.signal)
        print("이유:", result.reason)
        print("신뢰도:", result.confidence)
    except Exception as e:
        print("오류 발생:", e)


