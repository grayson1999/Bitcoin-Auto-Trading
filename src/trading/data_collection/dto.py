from dataclasses import dataclass, asdict
from typing import List, Optional

@dataclass
class RealtimeTickData:
    """실시간 시세 데이터(Tick)"""
    market: str
    trade_price: float
    prev_closing_price: float
    opening_price: float
    high_price: float
    low_price: float
    change_type: str
    change_rate: float
    trade_volume: float
    acc_trade_volume_24h: float
    data_timestamp: int

@dataclass
class RealtimeAccountData:
    """실시간 계좌 정보 데이터"""
    currency: str
    balance: float
    locked: float
    avg_buy_price: Optional[float]
    data_timestamp: int

@dataclass
class RealtimeData:
    """GPT 판단 근거용 실시간 데이터 묶음"""
    ticks: List[RealtimeTickData]
    accounts: List[RealtimeAccountData]

    def to_dict(self):
        return asdict(self)
