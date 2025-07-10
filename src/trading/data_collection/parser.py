## src/trading/data_collection/parser.py

import time

def parse_ticker(raw: dict) -> dict:
    """
    raw 티커 데이터에서 필요한 필드만 추출해 정제.
    :param raw: UpbitAPI.fetch_ticker 반환 dict
    :return: refined dict 또는 None
    """
    if not raw:
        return None

    return {
        "market":               raw.get("market"),
        "trade_price":          raw.get("trade_price"),
        "prev_closing_price":   raw.get("prev_closing_price"),
        "opening_price":        raw.get("opening_price"),
        "high_price":           raw.get("high_price"),
        "low_price":            raw.get("low_price"),
        "change_type":          raw.get("change"),
        "change_rate":          raw.get("change_rate"),
        "trade_volume":         raw.get("trade_volume"),
        "acc_trade_volume_24h": raw.get("acc_trade_volume_24h"),
        "data_timestamp":       raw.get("timestamp"),
    }

def parse_account(raw_list: list, currency: str = "BTC") -> dict:
    """
    raw 계좌 리스트에서 특정 통화 정보만 추출.
    :param raw_list: UpbitAPI.fetch_accounts 반환 리스트
    :param currency: 조회할 통화 코드
    :return: 해당 통화 dict 또는 None
    """
    if not raw_list:
        return None

    for acct in raw_list:
        if acct.get("currency") == currency:
            return {
                "currency":      acct.get("currency"),
                "balance":       float(acct.get("balance", 0)),
                "locked":        float(acct.get("locked", 0)),
                "avg_buy_price": float(acct.get("avg_buy_price") or 0),
                "data_timestamp": int(time.time() * 1000),
            }
    return None
