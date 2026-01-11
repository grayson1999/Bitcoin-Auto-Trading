"""MarketData SQLAlchemy model for storing real-time market data."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class MarketData(Base):
    """Real-time market data collected from Upbit.

    Stores BTC/KRW price, volume, and trade information at 1-second intervals.
    Data is retained for 1 year (configurable via data_retention_days setting).
    """

    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        comment="Current price in KRW",
    )
    volume: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        comment="24-hour trading volume",
    )
    high_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        comment="24-hour high price",
    )
    low_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        nullable=False,
        comment="24-hour low price",
    )
    trade_count: Mapped[int] = mapped_column(
        nullable=False,
        comment="Number of trades",
    )

    __table_args__ = (
        Index("idx_market_data_timestamp_desc", timestamp.desc()),
        Index("idx_market_data_date", timestamp),
    )

    def __repr__(self) -> str:
        return (
            f"<MarketData(id={self.id}, timestamp={self.timestamp}, "
            f"price={self.price})>"
        )
