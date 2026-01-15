"""
Upbit API 클라이언트 모듈

이 모듈은 Upbit 거래소 API와 통신하는 비동기 HTTP 클라이언트를 제공합니다.
- JWT 인증 기반 API 요청
- 시세 조회 (공개 API)
- 계좌 잔고 조회 (인증 필요)
- 주문 생성/조회/취소 (인증 필요)
- 자동 재시도 및 Rate Limit 처리
"""

import asyncio
import hashlib
import time
import uuid
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt
from loguru import logger
from pydantic import BaseModel

from src.config import settings

# === Upbit API 상수 ===
UPBIT_API_URL = "https://api.upbit.com/v1"  # API 기본 URL
REQUEST_TIMEOUT = 10.0  # 요청 타임아웃 (초)
MAX_RETRIES = 3  # 최대 재시도 횟수
RETRY_DELAY = 1.0  # 재시도 기본 대기 시간 (초)

# === JWT/해시 알고리즘 상수 ===
JWT_ALGORITHM = "HS256"  # JWT 서명 알고리즘
HASH_ALGORITHM = "SHA512"  # 쿼리 해시 알고리즘

# === 오류 메시지 상수 ===
ERROR_INVALID_TICKER = "잘못된 시세 응답"
ERROR_INVALID_ACCOUNT = "잘못된 계좌 응답"
ERROR_INVALID_ORDER = "잘못된 주문 응답"
ERROR_INVALID_CANCEL = "잘못된 취소 응답"

# === 인덱스 상수 ===
FIRST_ITEM = 0  # 응답 리스트의 첫 번째 항목


def _to_decimal(value: str | int | float | None) -> Decimal | None:
    """
    값을 Decimal로 변환하는 헬퍼 함수

    Args:
        value: 변환할 값 (문자열, 정수, 실수 또는 None)

    Returns:
        Decimal | None: 변환된 Decimal 값 또는 None
    """
    if value is None:
        return None
    return Decimal(str(value))


class UpbitTickerData(BaseModel):
    """
    Upbit 시세 데이터 모델

    Attributes:
        market: 마켓 코드 (예: KRW-XRP)
        trade_price: 현재 거래가
        acc_trade_volume_24h: 24시간 누적 거래량
        high_price: 24시간 고가
        low_price: 24시간 저가
        timestamp: 타임스탬프 (밀리초)
    """

    market: str
    trade_price: Decimal
    acc_trade_volume_24h: Decimal
    high_price: Decimal
    low_price: Decimal
    timestamp: int


class UpbitCandleData(BaseModel):
    """
    Upbit 캔들 데이터 모델

    OHLCV (시가, 고가, 저가, 종가, 거래량) 캔들스틱 데이터입니다.

    Attributes:
        market: 마켓 코드 (예: KRW-XRP)
        candle_date_time_utc: 캔들 시간 (UTC)
        candle_date_time_kst: 캔들 시간 (KST)
        opening_price: 시가
        high_price: 고가
        low_price: 저가
        trade_price: 종가 (현재가)
        candle_acc_trade_volume: 캔들 누적 거래량
        candle_acc_trade_price: 캔들 누적 거래대금
    """

    market: str
    candle_date_time_utc: str
    candle_date_time_kst: str
    opening_price: Decimal
    high_price: Decimal
    low_price: Decimal
    trade_price: Decimal
    candle_acc_trade_volume: Decimal
    candle_acc_trade_price: Decimal


class UpbitBalance(BaseModel):
    """
    Upbit 계좌 잔고 모델

    Attributes:
        currency: 화폐 코드 (예: KRW, BTC)
        balance: 사용 가능 잔고
        locked: 주문 중 잠금된 금액
        avg_buy_price: 평균 매수 단가
    """

    currency: str
    balance: Decimal
    locked: Decimal
    avg_buy_price: Decimal


class UpbitOrderResponse(BaseModel):
    """
    Upbit 주문 응답 모델

    Attributes:
        uuid: 주문 고유 식별자
        side: 주문 방향 (bid=매수, ask=매도)
        ord_type: 주문 유형 (limit=지정가, price=시장가매수, market=시장가매도)
        price: 주문 가격 (지정가 주문 시)
        state: 주문 상태 (wait=대기, done=완료, cancel=취소)
        market: 마켓 코드
        volume: 주문 수량
        remaining_volume: 미체결 수량
        executed_volume: 체결 수량
        trades_count: 체결 건수
    """

    uuid: str
    side: str
    ord_type: str
    price: Decimal | None
    state: str
    market: str
    volume: Decimal
    remaining_volume: Decimal
    executed_volume: Decimal
    trades_count: int


class UpbitError(Exception):
    """
    Upbit API 오류 예외

    API 요청 실패 또는 오류 응답 시 발생합니다.

    Attributes:
        message: 오류 메시지
        status_code: HTTP 상태 코드 (있는 경우)
    """

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UpbitClient:
    """
    Upbit 거래소 비동기 API 클라이언트

    JWT 인증을 사용하여 Upbit API와 통신합니다.
    - 공개 API: 시세 조회, 오더북 조회
    - 비공개 API: 잔고 조회, 주문 생성/조회/취소

    사용 예시:
        client = UpbitClient()
        ticker = await client.get_ticker("KRW-XRP")
        print(f"현재가: {ticker.trade_price}")
    """

    def __init__(
        self,
        access_key: str | None = None,
        secret_key: str | None = None,
    ):
        """
        Upbit 클라이언트 초기화

        Args:
            access_key: Upbit API 접근 키 (기본값: 설정 파일에서 로드)
            secret_key: Upbit API 비밀 키 (기본값: 설정 파일에서 로드)
        """
        self.access_key = access_key or settings.upbit_access_key
        self.secret_key = secret_key or settings.upbit_secret_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """
        HTTP 클라이언트 반환 (지연 초기화)

        클라이언트가 없거나 닫혔으면 새로 생성합니다.

        Returns:
            httpx.AsyncClient: HTTP 클라이언트 인스턴스
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=UPBIT_API_URL,
                timeout=REQUEST_TIMEOUT,
                headers={"Accept": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        """
        HTTP 클라이언트 종료

        리소스를 정리하고 연결을 닫습니다.
        """
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _generate_jwt_token(self, query_params: dict[str, Any] | None = None) -> str:
        """
        JWT 인증 토큰 생성

        Upbit API 인증에 필요한 JWT 토큰을 생성합니다.
        쿼리 파라미터가 있는 경우 SHA512 해시를 포함합니다.

        Args:
            query_params: 요청에 포함될 쿼리 파라미터 (해시에 포함)

        Returns:
            str: 생성된 JWT 토큰
        """
        payload: dict[str, Any] = {
            "access_key": self.access_key,
            "nonce": str(uuid.uuid4()),  # 일회용 난수
            "timestamp": int(time.time() * 1000),  # 밀리초 타임스탬프
        }

        # 쿼리 파라미터가 있으면 해시 추가
        if query_params:
            query_string = urlencode(query_params)
            query_hash = hashlib.sha512(query_string.encode()).hexdigest()
            payload["query_hash"] = query_hash
            payload["query_hash_alg"] = HASH_ALGORITHM

        return jwt.encode(payload, self.secret_key, algorithm=JWT_ALGORITHM)

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        authenticated: bool = False,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Upbit API HTTP 요청 수행

        재시도 로직과 Rate Limit 처리를 포함합니다.

        Args:
            method: HTTP 메서드 (GET, POST, DELETE)
            endpoint: API 엔드포인트 경로
            params: URL 쿼리 파라미터
            json_data: JSON 요청 본문
            authenticated: JWT 인증 포함 여부

        Returns:
            API 응답 데이터 (dict 또는 list)

        Raises:
            UpbitError: API 오류 또는 네트워크 실패 시
        """
        client = await self._get_client()
        headers: dict[str, str] = {}

        # 인증이 필요한 경우 JWT 토큰 추가
        if authenticated:
            token = self._generate_jwt_token(params or json_data)
            headers["Authorization"] = f"Bearer {token}"

        last_error: Exception | None = None

        # 재시도 로직 (최대 MAX_RETRIES 회)
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=json_data,
                    headers=headers,
                )

                # Rate Limit (429) 처리 - 지수 백오프 후 재시도
                if response.status_code == 429:
                    wait_time = RETRY_DELAY * (2**attempt)
                    logger.warning(f"Rate limit 도달, {wait_time}초 후 재시도")
                    await self._sleep(wait_time)
                    continue

                # 4xx/5xx 오류 처리
                if response.status_code >= 400:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error", {}).get(
                        "message", response.text
                    )
                    raise UpbitError(
                        f"Upbit API 오류: {error_msg}",
                        status_code=response.status_code,
                    )

                return response.json()

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"요청 타임아웃 (시도 {attempt + 1}/{MAX_RETRIES})")
                await self._sleep(RETRY_DELAY)

            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"요청 오류 (시도 {attempt + 1}/{MAX_RETRIES}): {e}")
                await self._sleep(RETRY_DELAY)

        raise UpbitError(f"{MAX_RETRIES}회 재시도 후 요청 실패: {last_error}")

    async def _sleep(self, seconds: float) -> None:
        """
        비동기 대기 헬퍼

        Args:
            seconds: 대기 시간 (초)
        """
        await asyncio.sleep(seconds)

    def _parse_order_response(self, response: dict[str, Any]) -> UpbitOrderResponse:
        """
        주문 응답 파싱

        API 응답을 UpbitOrderResponse 객체로 변환합니다.

        Args:
            response: API 응답 딕셔너리

        Returns:
            UpbitOrderResponse: 파싱된 주문 응답 객체
        """
        return UpbitOrderResponse(
            uuid=response["uuid"],
            side=response["side"],
            ord_type=response["ord_type"],
            price=_to_decimal(response.get("price")),
            state=response["state"],
            market=response["market"],
            volume=_to_decimal(response["volume"]),
            remaining_volume=_to_decimal(response["remaining_volume"]),
            executed_volume=_to_decimal(response["executed_volume"]),
            trades_count=response["trades_count"],
        )

    # ==================== 공개 API ====================

    async def get_ticker(self, market: str = "KRW-XRP") -> UpbitTickerData:
        """
        시세 조회

        특정 마켓의 현재 시세 정보를 조회합니다.

        Args:
            market: 마켓 코드 (기본값: KRW-XRP)

        Returns:
            UpbitTickerData: 시세 데이터 (가격, 거래량 등)

        Raises:
            UpbitError: API 오류 시
        """
        response = await self._request(
            method="GET",
            endpoint="/ticker",
            params={"markets": market},
        )

        if not response or not isinstance(response, list):
            raise UpbitError(ERROR_INVALID_TICKER)

        data = response[FIRST_ITEM]
        return UpbitTickerData(
            market=data["market"],
            trade_price=_to_decimal(data["trade_price"]),
            acc_trade_volume_24h=_to_decimal(data["acc_trade_volume_24h"]),
            high_price=_to_decimal(data["high_price"]),
            low_price=_to_decimal(data["low_price"]),
            timestamp=data["timestamp"],
        )

    async def get_orderbook(self, market: str = "KRW-XRP") -> dict[str, Any]:
        """
        오더북 조회

        특정 마켓의 호가 정보를 조회합니다.

        Args:
            market: 마켓 코드

        Returns:
            dict: 오더북 데이터 (매수/매도 호가 목록)
        """
        response = await self._request(
            method="GET",
            endpoint="/orderbook",
            params={"markets": market},
        )
        return response[FIRST_ITEM] if response else {}

    async def get_minute_candles(
        self,
        market: str = "KRW-XRP",
        unit: int = 60,
        count: int = 200,
    ) -> list[UpbitCandleData]:
        """
        분봉 캔들 조회

        특정 마켓의 분봉 캔들 데이터를 조회합니다.

        Args:
            market: 마켓 코드 (기본값: KRW-XRP)
            unit: 분 단위 (1, 3, 5, 10, 15, 30, 60, 240)
            count: 조회할 캔들 개수 (최대 200)

        Returns:
            list[UpbitCandleData]: 캔들 데이터 목록 (최신순)

        Raises:
            UpbitError: API 오류 시
        """
        response = await self._request(
            method="GET",
            endpoint=f"/candles/minutes/{unit}",
            params={"market": market, "count": min(count, 200)},
        )

        if not isinstance(response, list):
            return []

        return [
            UpbitCandleData(
                market=candle["market"],
                candle_date_time_utc=candle["candle_date_time_utc"],
                candle_date_time_kst=candle["candle_date_time_kst"],
                opening_price=_to_decimal(candle["opening_price"]),
                high_price=_to_decimal(candle["high_price"]),
                low_price=_to_decimal(candle["low_price"]),
                trade_price=_to_decimal(candle["trade_price"]),
                candle_acc_trade_volume=_to_decimal(candle["candle_acc_trade_volume"]),
                candle_acc_trade_price=_to_decimal(candle["candle_acc_trade_price"]),
            )
            for candle in response
        ]

    async def get_day_candles(
        self,
        market: str = "KRW-XRP",
        count: int = 200,
    ) -> list[UpbitCandleData]:
        """
        일봉 캔들 조회

        특정 마켓의 일봉 캔들 데이터를 조회합니다.

        Args:
            market: 마켓 코드 (기본값: KRW-XRP)
            count: 조회할 캔들 개수 (최대 200)

        Returns:
            list[UpbitCandleData]: 캔들 데이터 목록 (최신순)

        Raises:
            UpbitError: API 오류 시
        """
        response = await self._request(
            method="GET",
            endpoint="/candles/days",
            params={"market": market, "count": min(count, 200)},
        )

        if not isinstance(response, list):
            return []

        return [
            UpbitCandleData(
                market=candle["market"],
                candle_date_time_utc=candle["candle_date_time_utc"],
                candle_date_time_kst=candle["candle_date_time_kst"],
                opening_price=_to_decimal(candle["opening_price"]),
                high_price=_to_decimal(candle["high_price"]),
                low_price=_to_decimal(candle["low_price"]),
                trade_price=_to_decimal(candle["trade_price"]),
                candle_acc_trade_volume=_to_decimal(candle["candle_acc_trade_volume"]),
                candle_acc_trade_price=_to_decimal(candle["candle_acc_trade_price"]),
            )
            for candle in response
        ]

    async def get_week_candles(
        self,
        market: str = "KRW-XRP",
        count: int = 52,
    ) -> list[UpbitCandleData]:
        """
        주봉 캔들 조회

        특정 마켓의 주봉 캔들 데이터를 조회합니다.

        Args:
            market: 마켓 코드 (기본값: KRW-XRP)
            count: 조회할 캔들 개수 (최대 200)

        Returns:
            list[UpbitCandleData]: 캔들 데이터 목록 (최신순)

        Raises:
            UpbitError: API 오류 시
        """
        response = await self._request(
            method="GET",
            endpoint="/candles/weeks",
            params={"market": market, "count": min(count, 200)},
        )

        if not isinstance(response, list):
            return []

        return [
            UpbitCandleData(
                market=candle["market"],
                candle_date_time_utc=candle["candle_date_time_utc"],
                candle_date_time_kst=candle["candle_date_time_kst"],
                opening_price=_to_decimal(candle["opening_price"]),
                high_price=_to_decimal(candle["high_price"]),
                low_price=_to_decimal(candle["low_price"]),
                trade_price=_to_decimal(candle["trade_price"]),
                candle_acc_trade_volume=_to_decimal(candle["candle_acc_trade_volume"]),
                candle_acc_trade_price=_to_decimal(candle["candle_acc_trade_price"]),
            )
            for candle in response
        ]

    # ==================== 비공개 API (인증 필요) ====================

    async def get_accounts(self) -> list[UpbitBalance]:
        """
        계좌 잔고 조회

        모든 보유 자산의 잔고 정보를 조회합니다.

        Returns:
            list[UpbitBalance]: 자산별 잔고 목록

        Raises:
            UpbitError: API 오류 시
        """
        response = await self._request(
            method="GET",
            endpoint="/accounts",
            authenticated=True,
        )

        if not isinstance(response, list):
            raise UpbitError(ERROR_INVALID_ACCOUNT)

        return [
            UpbitBalance(
                currency=acc["currency"],
                balance=_to_decimal(acc["balance"]),
                locked=_to_decimal(acc["locked"]),
                avg_buy_price=_to_decimal(acc["avg_buy_price"]),
            )
            for acc in response
        ]

    async def get_balance(self, currency: str = "KRW") -> Decimal:
        """
        특정 자산 잔고 조회

        Args:
            currency: 화폐 코드 (KRW, BTC 등)

        Returns:
            Decimal: 사용 가능 잔고 (없으면 0)
        """
        accounts = await self.get_accounts()
        for acc in accounts:
            if acc.currency == currency:
                return acc.balance
        return Decimal("0")

    async def place_order(
        self,
        market: str,
        side: str,
        volume: Decimal | None = None,
        price: Decimal | None = None,
        ord_type: str = "limit",
    ) -> UpbitOrderResponse:
        """
        주문 생성

        Args:
            market: 마켓 코드 (예: KRW-XRP)
            side: 주문 방향 (bid=매수, ask=매도)
            volume: 주문 수량 (지정가/시장가매도 시 필수)
            price: 주문 가격 (지정가/시장가매수 시 필수)
            ord_type: 주문 유형
                - limit: 지정가 주문
                - price: 시장가 매수 (총액 지정)
                - market: 시장가 매도 (수량 지정)

        Returns:
            UpbitOrderResponse: 주문 응답 (UUID, 상태 등)

        Raises:
            UpbitError: 주문 실패 시
        """
        params: dict[str, Any] = {
            "market": market,
            "side": side,
            "ord_type": ord_type,
        }

        if volume is not None:
            params["volume"] = str(volume)
        if price is not None:
            params["price"] = str(price)

        logger.info(f"주문 요청: {params}")

        response = await self._request(
            method="POST",
            endpoint="/orders",
            json_data=params,
            authenticated=True,
        )

        if not isinstance(response, dict):
            raise UpbitError(ERROR_INVALID_ORDER)

        return self._parse_order_response(response)

    async def get_order(self, uuid: str) -> UpbitOrderResponse:
        """
        주문 상태 조회

        Args:
            uuid: 주문 고유 식별자

        Returns:
            UpbitOrderResponse: 주문 상세 정보

        Raises:
            UpbitError: 조회 실패 시
        """
        response = await self._request(
            method="GET",
            endpoint="/order",
            params={"uuid": uuid},
            authenticated=True,
        )

        if not isinstance(response, dict):
            raise UpbitError(ERROR_INVALID_ORDER)

        return self._parse_order_response(response)

    async def cancel_order(self, uuid: str) -> UpbitOrderResponse:
        """
        주문 취소

        Args:
            uuid: 취소할 주문의 고유 식별자

        Returns:
            UpbitOrderResponse: 취소된 주문 정보

        Raises:
            UpbitError: 취소 실패 시
        """
        response = await self._request(
            method="DELETE",
            endpoint="/order",
            params={"uuid": uuid},
            authenticated=True,
        )

        if not isinstance(response, dict):
            raise UpbitError(ERROR_INVALID_CANCEL)

        return self._parse_order_response(response)


# === 싱글톤 인스턴스 ===
_upbit_client: UpbitClient | None = None


def get_upbit_client() -> UpbitClient:
    """
    Upbit 클라이언트 싱글톤 반환

    애플리케이션 전체에서 동일한 클라이언트 인스턴스를 공유합니다.

    Returns:
        UpbitClient: 싱글톤 클라이언트 인스턴스
    """
    global _upbit_client
    if _upbit_client is None:
        _upbit_client = UpbitClient()
    return _upbit_client
