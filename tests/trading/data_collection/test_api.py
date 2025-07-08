# -*- coding: utf-8 -*-
# tests/trading/data_collection/test_api_business.py

import os
import time
import uuid
import requests
import jwt
import pytest

from trading.data_collection.api import UpbitAPI

class DummyResponse:
    def __init__(self, status_code: int, json_data):
        self.status_code = status_code
        self._json = json_data

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


# ────────── fetch_ticker 비즈니스 로직 검증 ──────────

def test_exponential_backoff_sequence(monkeypatch):
    """
    fetch_ticker에서 실패할 때마다 backoff * 2**(attempt-1) 만큼 sleep을 호출하는지 검증
    """
    delays = []
    # 항상 실패하도록 설정
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: (_ for _ in ()).throw(Exception("err")))
    monkeypatch.setattr(time, "sleep", lambda d: delays.append(d))

    # retries=4, backoff=0.5로 호출
    result = UpbitAPI.fetch_ticker("KRW-BTC", retries=4, backoff=0.5)
    assert result is None

    # 예상 delay: [0.5*2**0, 0.5*2**1, 0.5*2**2, 0.5*2**3]
    assert delays == [0.5, 1.0, 2.0, 4.0]


def test_success_after_retries_stops_sleep(monkeypatch):
    """
    2회 실패 후 3회차에 정상 응답하면, 그 이후로 sleep 호출이 멈추는지 검증
    """
    payload = {"foo": "bar"}
    call_count = {"n": 0}
    delays = []

    def mock_get(url, params=None, timeout=None):
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise Exception("temporary error")
        return DummyResponse(200, [payload])

    monkeypatch.setattr(requests, "get", mock_get)
    monkeypatch.setattr(time, "sleep", lambda d: delays.append(d))

    result = UpbitAPI.fetch_ticker("KRW-BTC", retries=5, backoff=1)
    assert result == payload
    # 두 번 실패했으니 두 번만 sleep: [1*2**0, 1*2**1]
    assert delays == [1.0, 2.0]
    # get 호출 횟수도 3번
    assert call_count["n"] == 3


def test_returns_none_on_empty_list(monkeypatch):
    """
    API가 빈 리스트[]를 반환하면 None을 반환하는지 검증
    """
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: DummyResponse(200, []))
    assert UpbitAPI.fetch_ticker("KRW-BTC") is None


# ────────── fetch_accounts 비즈니스 로직 검증 ──────────

def test_jwt_payload_and_header(monkeypatch):
    """
    fetch_accounts가 올바른 payload로 jwt.encode를 호출하고,
    Authorization 헤더에 Bearer 토큰을 담아 요청하는지 검증
    """
    # 환경변수 세팅
    monkeypatch.setenv("UPBIT_ACCESS", "MYACCESS")
    monkeypatch.setenv("UPBIT_SECRET", "MYSECRET")

    # uuid4 고정
    fixed_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    monkeypatch.setattr(uuid, "uuid4", lambda: fixed_uuid)

    captured = {}
    # jwt.encode 모의: payload, secret, algorithm 기록 후 "TOK" 반환
    def fake_encode(payload, secret, algorithm):
        captured["payload"] = payload
        captured["secret"] = secret
        captured["alg"] = algorithm
        return "TOK"
    monkeypatch.setattr(jwt, "encode", fake_encode)

    # requests.get 모의: url, headers 기록하고 정상 반환
    def fake_get(url, headers=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        return DummyResponse(200, [{"currency": "BTC", "balance": "0.1"}])
    monkeypatch.setattr(requests, "get", fake_get)

    result = UpbitAPI.fetch_accounts()

    # jwt.encode 호출 검증
    assert captured["payload"] == {
        "access_key": "MYACCESS",
        "nonce": str(fixed_uuid)
    }
    assert captured["secret"] == "MYSECRET"
    assert captured["alg"] == "HS256"

    # requests.get 호출 검증
    assert captured["url"] == f"{UpbitAPI.BASE_URL}/v1/accounts"
    assert captured["headers"] == {"Authorization": "Bearer TOK"}

    # 최종 반환값 검증
    assert result == [{"currency": "BTC", "balance": "0.1"}]
