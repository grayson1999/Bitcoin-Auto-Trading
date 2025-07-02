import os
import time
import uuid
import requests
import jwt
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드 (프로젝트 root/config/.env 기준)
env_path = Path(__file__).resolve().parents[3] / "config" / ".env"
load_dotenv(env_path)

class UpbitAPI:
    BASE_URL = "https://api.upbit.com"

    @staticmethod
    def fetch_ticker(market: str, retries: int = 3, backoff: float = 1.0):
        """
        공용 티커 데이터(가격·거래량) 요청.
        :param market: 마켓 코드, e.g. "KRW-BTC"
        :param retries: 최대 재시도 횟수
        :param backoff: 지수 백오프 기본 대기시간(초)
        :return: 단일 마켓 데이터 dict 또는 None
        """
        url = f"{UpbitAPI.BASE_URL}/v1/ticker"
        params = {"markets": market}
        for attempt in range(1, retries + 1):
            try:
                resp = requests.get(url, params=params, timeout=5)
                resp.raise_for_status()
                data = resp.json()
                return data[0] if isinstance(data, list) and data else None
            except Exception as e:
                delay = backoff * (2 ** (attempt - 1))
                print(f"[UpbitAPI] fetch_ticker 실패({attempt}/{retries}): {e} → {delay}s 후 재시도")
                time.sleep(delay)
        return None

    @staticmethod
    def fetch_accounts():
        """
        비공개 계좌 정보 요청 (JWT 인증).
        :return: 계좌 리스트 JSON 또는 None
        """
        access = os.getenv("UPBIT_ACCESS")
        secret = os.getenv("UPBIT_SECRET")
        if not access or not secret:
            print("[UpbitAPI] UPBIT_ACCESS/SECRET 환경변수 미설정")
            return None

        payload = {
            "access_key": access,
            "nonce": str(uuid.uuid4())
        }
        token = jwt.encode(payload, secret, algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{UpbitAPI.BASE_URL}/v1/accounts"

        try:
            resp = requests.get(url, headers=headers, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[UpbitAPI] fetch_accounts 오류: {e}")
            return None
