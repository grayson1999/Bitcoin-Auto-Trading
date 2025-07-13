import os
import time
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

import openai

from dotenv import load_dotenv
from pathlib import Path

from src.trading.data_collection.dto import RealtimeData

env_path = Path(__file__).resolve().parents[3] / "config" / ".env"
load_dotenv(env_path)


# ─── 데이터 클래스 정의 ───────────────────────────────────────────────────
@dataclass
class SignalResponse:
    """ChatGPT 응답을 구조화하기 위한 데이터 클래스"""
    signal: str
    reason: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
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

def _create_prompt(realtime_data: RealtimeData) -> str:
    """RealtimeData를 기반으로 ChatGPT 프롬프트를 생성합니다."""
    # 데이터를 JSON 문자열로 변환하여 프롬프트에 포함
    data_json = json.dumps(realtime_data.to_dict(), indent=2, ensure_ascii=False)
    
    return (
        f"""현재 비트코인(KRW-BTC)의 실시간 데이터는 다음과 같습니다.\n\n```json\n{data_json}\n```\n\n위 데이터를 종합적으로 분석하여 매수(buy), 보류(hold), 매도(sell) 중 하나의 신호를 생성해주세요.\n판단 근거에는 반드시 데이터에 기반한 구체적인 수치를 포함해야 합니다."""
    )

def send_signal_request(realtime_data: RealtimeData, options: Optional[Dict[str, Any]] = None) -> SignalResponse:
    """
    ChatGPT API에 매매 신호 요청을 보냅니다.
    신뢰도가 임계값 미만이면 10초 후 재시도합니다.

    :param realtime_data: GPT 판단 근거용 실시간 데이터
    :param options: OpenAI API 요청에 사용할 추가 옵션 (model, temperature 등)
    :return: 파싱된 SignalResponse 객체
    :raises: OpenAI 관련 예외 및 RuntimeError
    """
    if options is None:
        options = {}

    # 기본 요청 설정
    payload = {
        "model": options.get("model", "gpt-4o-mini"),
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
                "content": _create_prompt(realtime_data)
            }
        ],
        "temperature": options.get("temperature", 0.5),
        "max_tokens": options.get("max_tokens", 500),
        "timeout": options.get("timeout", 15)
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(**payload)
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
    # 테스트용 예시 데이터 생성
    from src.trading.data_collection.dto import RealtimeTickData, RealtimeAccountData
    
    mock_ticks = [
        RealtimeTickData(
            market='KRW-BTC', trade_price=90500000, prev_closing_price=90000000, 
            opening_price=90100000, high_price=90800000, low_price=89900000,
            change_type='RISE', change_rate=0.0055, trade_volume=0.1, 
            acc_trade_volume_24h=1500, data_timestamp=int(time.time() * 1000)
        )
    ]
    mock_accounts = [
        RealtimeAccountData(
            currency='KRW', balance=1000000, locked=0, avg_buy_price=None, 
            data_timestamp=int(time.time() * 1000)
        ),
        RealtimeAccountData(
            currency='BTC', balance=0.01, locked=0, avg_buy_price=85000000, 
            data_timestamp=int(time.time() * 1000)
        )
    ]
    mock_realtime_data = RealtimeData(ticks=mock_ticks, accounts=mock_accounts)

    try:
        result = send_signal_request(mock_realtime_data)

        print("응답 객체:", result)
        print("신호:", result.signal)
        print("이유:", result.reason)
        print("신뢰도:", result.confidence)
    except Exception as e:
        print("오류 발생:", e)


