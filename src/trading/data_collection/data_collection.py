import schedule
import os
import uuid
import time
import jwt
import requests
from dotenv import load_dotenv
from src.utils.logger import get_logger
from src.realtime.models import init_db, SessionLocal, save_ticker, save_account

logger = get_logger(
    name="realtime.data_collection",
    log_file="data_collection.log"
)


# .env 파일의 환경변수를 로드합니다.
load_dotenv("../../config/.env")


# =============================================================================
# Upbit API 연동 및 데이터 파싱/정제 예제 (임시 저장소 및 stub 함수 방식)
#
# 1. 인증 및 API 키 관리:
#    - 공용 데이터 요청은 인증 없이 진행합니다.
#    - 비공개 데이터(예: 계좌 정보) 요청은 인증 및 JWT 토큰을 통해 진행하며,
#      환경변수(.env)나 config 파일에서 UPBIT_ACCESS와 UPBIT_SECRET을 로드합니다.
#
# 2. 데이터 요청:
#    - 공용 데이터: Upbit API의 티커 엔드포인트를 사용하여 가격, 거래량, 체결 정보 등
#      필요한 데이터를 요청합니다.
#    - 비공개 데이터: 계좌 정보 등 민감한 데이터 요청을 위해 적절한 엔드포인트(예: /v1/accounts)를 사용합니다.
#
# 3. 응답 포맷 이해 및 데이터 파싱/정제:
#    - 공용 데이터 API 응답은 JSON 형식이며, 필요한 필드(예: market, trade_price,
#      prev_closing_price, opening_price, high_price, low_price, change, change_rate,
#      trade_volume, acc_trade_volume_24h, timestamp)를 추출하여 정제된 데이터로 반환합니다.
#    - 비공개 데이터(계좌 정보)는 JSON 리스트 형식으로 제공되며, 특정 자산에 대한 정보를 파싱하여 반환합니다.
#
# 4. 오류 처리 및 재시도 로직:
#    - API 호출 실패, 네트워크 오류, 타임아웃 등의 예외 상황을 처리합니다.
#    - 실패 시 지수 백오프 메커니즘을 적용하여, 최대 재시도 횟수 내에 안정적으로 데이터를 요청합니다.
#
# 5. 데이터 수집 주기 및 스케줄링:
#    - schedule 라이브러리를 사용하여 1초 간격으로 데이터를 주기적으로 요청합니다.
# =============================================================================


def get_ticker_data(market="KRW-BTC", max_retries=3, base_delay=1):
    """
    Upbit API의 티커 엔드포인트를 통해 지정된 마켓의 원시 데이터를 요청합니다.
    재시도 로직이 포함되어 있으며, 실패 시 지수 백오프로 재시도합니다.
    
    :param market: 요청할 마켓 코드 (기본값 "KRW-BTC")
    :param max_retries: 최대 재시도 횟수 (기본값 3)
    :param base_delay: 재시도 시 초기 대기 시간 (초, 기본값 1)
    :return: API 응답으로 받은 원시 JSON 데이터 (리스트 형태), 실패 시 None
    """
    url = "https://api.upbit.com/v1/ticker"
    params = {"markets": market}
    attempt = 0

    while attempt < max_retries:
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()  # HTTP 에러 발생 시 예외 발생
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            attempt += 1
            delay = base_delay * (2 ** (attempt - 1))  # 지수 백오프 적용
            print(f"Attempt {attempt} failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)

    print("Max retries reached. Failed to fetch ticker data.")
    return None

def get_private_data():
    """
    민감한 데이터를 요청할 때 사용하는 예제 함수.
    API 키와 시크릿은 .env 파일에 저장된 환경변수에서 로드하고,
    JWT 토큰을 생성하여 인증을 수행합니다.
    
    :return: 요청 성공 시 JSON 데이터, 실패 시 None
    """
    access_key = os.getenv("UPBIT_ACCESS")
    secret_key = os.getenv("UPBIT_SECRET")
    
    if not access_key or not secret_key:
        print("API 키 또는 시크릿이 .env 파일에 설정되어 있지 않습니다.")
        return None

    # JWT 페이로드 생성: nonce를 포함하여 고유 값 생성
    payload = {
        "access_key": access_key,
        "nonce": str(uuid.uuid4()),
        # 추가적으로 필요한 파라미터가 있다면 여기에 포함
    }
    
    # JWT 토큰 생성 (PyJWT 사용)
    jwt_token = jwt.encode(payload, secret_key, algorithm="HS256")
    authorization_token = f"Bearer {jwt_token}"
    
    headers = {
        "Authorization": authorization_token
    }
    
    # 올바른 계좌 정보 엔드포인트 (복수: accounts)
    url = "https://api.upbit.com/v1/accounts"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"Error occurred: {err}")
    
    return None

def parse_and_refine_data(raw_data):
    """
    API로부터 받아온 원시 데이터를 파싱하여 GPT 판단을 위한 필수 필드를 추출하고 정제된 데이터로 변환합니다.
    
    필수 필드:
      - market: 자산 종류 (예: KRW-BTC)
      - trade_price: 현재 거래 가격
      - prev_closing_price: 전일 종가
      - opening_price: 당일 시가
      - high_price: 당일 최고 가격
      - low_price: 당일 최저 가격
      - change: 상승/하락 여부
      - change_rate: 변화율
      - trade_volume: 개별 거래량
      - acc_trade_volume_24h: 24시간 누적 거래량
      - timestamp: 데이터 수집 시각
    
    :param raw_data: Upbit API에서 받아온 원시 JSON 데이터 (리스트 형태)
    :return: 정제된 데이터 (dict 형태) 또는 None
    """
    if not raw_data or not isinstance(raw_data, list):
        print("원시 데이터 형식이 올바르지 않습니다.")
        return None
    try:
        # 첫 번째 마켓의 데이터만 사용
        data = raw_data[0]
        refined_data = {
            "market": data.get("market"),
            "trade_price": data.get("trade_price"),
            "prev_closing_price": data.get("prev_closing_price"),
            "opening_price": data.get("opening_price"),
            "high_price": data.get("high_price"),
            "low_price": data.get("low_price"),
            "change": data.get("change"),
            "change_rate": data.get("change_rate"),
            "trade_volume": data.get("trade_volume"),
            "acc_trade_volume_24h": data.get("acc_trade_volume_24h"),
            "timestamp": data.get("timestamp")
        }
        return refined_data
    except Exception as e:
        print(f"데이터 파싱/정제 중 오류 발생: {e}")
        return None
    
def parse_private_account_data(private_data, target_currency="BTC"):
    """
    Upbit 계좌 정보 API 응답(private data)에서 특정 자산(예: BTC)에 대한 데이터를 파싱합니다.
    
    :param private_data: Upbit API로부터 받아온 계좌 정보 데이터 (리스트 형태)
    :param target_currency: 관심 자산 코드 (예: "BTC")
    :return: 해당 자산에 대한 계좌 정보(dict 형태) 또는 None
    """
    if not private_data or not isinstance(private_data, list):
        print("계좌 정보 데이터 형식이 올바르지 않습니다.")
        return None
    
    try:
        for account in private_data:
            if account.get("currency") == target_currency:
                return account
        print(f"{target_currency} 자산에 대한 데이터가 없습니다.")
        return None
    except Exception as e:
        print(f"계좌 데이터 파싱 중 오류 발생: {e}")
        return None
    
if __name__ == "__main__":
    # DB 테이블 생성(최초 1회만 실행해도 됩니다)
    init_db()

    # DB 세션 생성
    session = SessionLocal()
    # 공용 데이터 요청 테스트
    ticker_data = get_ticker_data()
    if ticker_data:
        print("Ticker Data:", ticker_data)
        
    print()
    
    # 비공개 데이터 요청 테스트 (환경변수 설정 필수)
    private_data = get_private_data()
    if private_data:
        print("Private Data:", private_data)
    print()
    
    # 공용 데이터 파싱 테스트
    refined = parse_and_refine_data(ticker_data)
    if refined:
        print("정제된 데이터:", refined)
        save_ticker(session, refined)   # DB에 저장
    else:
        print("데이터 정제 실패")
    print()
    
    # 비공개 데이터 정제 파싱 테스트
    btc_account = parse_private_account_data(private_data, target_currency="XRP")
    if btc_account:
        print("계좌 정보:", btc_account)
        # acct dict에 timestamp 필드 추가 후 저장
        btc_account["timestamp"] = int(time.time() * 1000)
        save_account(session, btc_account)
    print()
    
    # # 스케줄러를 사용해 1초마다 get_ticker_data() 함수 실행 후 데이터 파싱 및 정제
    # def job():
    #     raw_data = get_ticker_data()
    #     if raw_data:
    #         refined = parse_and_refine_data(raw_data)
    #         if refined:
    #             print("정제된 데이터:", refined)
    #         else:
    #             print("데이터 정제 실패")
    #     else:
    #         print("데이터 수집 실패")
    
    # schedule.every(1).seconds.do(job)
    
    # print("데이터 수집 및 정제 시작 (1초 간격)...")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(0.5)
