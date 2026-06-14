"""
중복 주문 방지 (C5) 단위 테스트

3개 방어층 검증:
1. place_order가 identifier를 Upbit POST 바디에 포함한다
2. POST /orders 타임아웃/네트워크 오류는 재시도하지 않는다 (이중 발주 방지)
3. GET 등 멱등 요청의 타임아웃 재시도는 유지된다 (회귀 가드)
4. get_order_by_identifier는 404를 None으로 변환한다
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.clients.upbit.private_api import UpbitPrivateAPI, UpbitPrivateAPIError
from src.config.constants import DEFAULT_MAX_RETRIES


def _make_api() -> UpbitPrivateAPI:
    return UpbitPrivateAPI(
        access_key="test-access",
        secret_key="test-secret",  # noqa: S106 - 테스트용 더미 키
    )


def _ok_order_response() -> dict:
    """Upbit 주문 응답(최소 필드)."""
    return {
        "uuid": "test-uuid-1234",
        "side": "bid",
        "ord_type": "price",
        "state": "wait",
        "market": "KRW-BTC",
        "executed_volume": "0",
        "paid_fee": "0",
    }


@pytest.mark.asyncio
async def test_place_order_includes_identifier_in_body() -> None:
    """place_order(identifier=...) → POST json 바디에 identifier 포함."""
    api = _make_api()
    api._request = AsyncMock(return_value=_ok_order_response())

    await api.place_order(
        market="KRW-BTC",
        side="bid",
        price=10000,
        ord_type="price",
        identifier="idem-key-abc",
    )

    api._request.assert_awaited_once()
    _, kwargs = api._request.call_args
    assert kwargs["json_data"]["identifier"] == "idem-key-abc"


@pytest.mark.asyncio
async def test_place_order_omits_identifier_when_none() -> None:
    """identifier 미전달 시 바디에 identifier 키가 없다."""
    api = _make_api()
    api._request = AsyncMock(return_value=_ok_order_response())

    await api.place_order(market="KRW-BTC", side="bid", price=10000, ord_type="price")

    _, kwargs = api._request.call_args
    assert "identifier" not in kwargs["json_data"]


@pytest.mark.asyncio
async def test_post_orders_timeout_does_not_retry() -> None:
    """POST /orders 타임아웃 → 즉시 실패, client.request 1회만 호출."""
    api = _make_api()
    mock_client = MagicMock()
    mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    api._get_client = AsyncMock(return_value=mock_client)

    with pytest.raises(UpbitPrivateAPIError, match="재시도하지 않음"):
        await api._request(
            method="POST", endpoint="/orders", json_data={"market": "KRW-BTC"}
        )

    assert mock_client.request.await_count == 1


@pytest.mark.asyncio
async def test_post_orders_network_error_does_not_retry() -> None:
    """POST /orders 네트워크 오류 → 즉시 실패, 재시도 없음."""
    api = _make_api()
    mock_client = MagicMock()
    mock_client.request = AsyncMock(side_effect=httpx.ConnectError("conn refused"))
    api._get_client = AsyncMock(return_value=mock_client)

    with pytest.raises(UpbitPrivateAPIError, match="재시도하지 않음"):
        await api._request(
            method="POST", endpoint="/orders", json_data={"market": "KRW-BTC"}
        )

    assert mock_client.request.await_count == 1


@pytest.mark.asyncio
async def test_get_request_timeout_still_retries() -> None:
    """GET 요청 타임아웃은 여전히 재시도된다 (회귀 가드)."""
    api = _make_api()
    mock_client = MagicMock()
    mock_client.request = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
    api._get_client = AsyncMock(return_value=mock_client)

    with pytest.raises(UpbitPrivateAPIError, match="Request failed after"):
        await api._request(method="GET", endpoint="/accounts")

    assert mock_client.request.await_count == DEFAULT_MAX_RETRIES


@pytest.mark.asyncio
async def test_get_order_by_identifier_404_returns_none() -> None:
    """get_order_by_identifier: 404 → None (주문 미접수)."""
    api = _make_api()
    api._request = AsyncMock(
        side_effect=UpbitPrivateAPIError("not found", status_code=404)
    )

    result = await api.get_order_by_identifier("idem-key-xyz")
    assert result is None


@pytest.mark.asyncio
async def test_get_order_by_identifier_found_returns_order() -> None:
    """get_order_by_identifier: 주문 존재 → 파싱된 응답 반환."""
    api = _make_api()
    api._request = AsyncMock(return_value=_ok_order_response())

    result = await api.get_order_by_identifier("idem-key-xyz")
    assert result is not None
    assert result.uuid == "test-uuid-1234"


@pytest.mark.asyncio
async def test_get_order_by_identifier_non_404_raises() -> None:
    """get_order_by_identifier: 404 이외 오류는 전파된다."""
    api = _make_api()
    api._request = AsyncMock(
        side_effect=UpbitPrivateAPIError("server error", status_code=500)
    )

    with pytest.raises(UpbitPrivateAPIError):
        await api.get_order_by_identifier("idem-key-xyz")
