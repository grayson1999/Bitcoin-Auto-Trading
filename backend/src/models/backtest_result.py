"""
백테스트 결과 모델

이 모듈은 백테스트 실행 결과를 저장하는 SQLAlchemy 모델을 정의합니다.
- 백테스트 기간 및 설정
- 성과 지표 (수익률, MDD, 승률, 손익비)
- 거래 내역 요약
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import BigInteger, DateTime, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models import Base


class BacktestStatus(str, Enum):
    """
    백테스트 상태

    - PENDING: 대기 중
    - RUNNING: 실행 중
    - COMPLETED: 완료
    - FAILED: 실패
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BacktestResult(Base):
    """
    백테스트 결과 모델

    과거 데이터로 AI 전략을 시뮬레이션한 결과를 저장합니다.
    수익률, MDD, 승률 등의 성과 지표를 포함합니다.

    Attributes:
        id: 고유 식별자 (자동 증가)
        name: 백테스트 이름 (사용자 지정)
        status: 백테스트 상태 (PENDING/RUNNING/COMPLETED/FAILED)
        start_date: 백테스트 시작 날짜
        end_date: 백테스트 종료 날짜
        initial_capital: 초기 자본금 (KRW)
        final_capital: 최종 자본금 (KRW)
        total_return_pct: 총 수익률 (%)
        max_drawdown_pct: 최대 낙폭 MDD (%)
        win_rate_pct: 승률 (%)
        profit_factor: 손익비 (총이익/총손실)
        total_trades: 총 거래 횟수
        winning_trades: 승리 거래 횟수
        losing_trades: 패배 거래 횟수
        avg_profit_pct: 평균 수익 거래 수익률 (%)
        avg_loss_pct: 평균 손실 거래 손실률 (%)
        sharpe_ratio: 샤프 비율 (위험 조정 수익률)
        trade_history: 거래 내역 JSON
        error_message: 실패 시 오류 메시지
        created_at: 생성 시간
        completed_at: 완료 시간

    인덱스:
        - idx_backtest_created_desc: 최신 결과 조회 최적화
        - idx_backtest_status: 상태별 조회 최적화
    """

    __tablename__ = "backtest_results"

    # === 기본 필드 ===
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # 백테스트 이름 (사용자 지정)
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="백테스트 이름",
    )

    # 백테스트 상태
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BacktestStatus.PENDING.value,
        comment="백테스트 상태 (PENDING/RUNNING/COMPLETED/FAILED)",
    )

    # === 기간 설정 ===
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="백테스트 시작 날짜",
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="백테스트 종료 날짜",
    )

    # === 자본금 ===
    # Numeric(18, 2): KRW 정밀도 (소수점 2자리)
    initial_capital: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="초기 자본금 (KRW)",
    )
    final_capital: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="최종 자본금 (KRW)",
    )

    # === 성과 지표 ===
    # 수익률: -100% ~ 무제한 (Numeric(10, 4)로 소수점 4자리)
    total_return_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        comment="총 수익률 (%)",
    )

    # 최대 낙폭 (MDD): 0% ~ 100%
    max_drawdown_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        comment="최대 낙폭 MDD (%)",
    )

    # 승률: 0% ~ 100%
    win_rate_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        comment="승률 (%)",
    )

    # 손익비: 총이익/총손실
    profit_factor: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        comment="손익비 (총이익/총손실)",
    )

    # === 거래 통계 ===
    total_trades: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="총 거래 횟수",
    )
    winning_trades: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="승리 거래 횟수",
    )
    losing_trades: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=0,
        comment="패배 거래 횟수",
    )

    # === 추가 지표 ===
    avg_profit_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        comment="평균 수익 거래 수익률 (%)",
    )
    avg_loss_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        comment="평균 손실 거래 손실률 (%)",
    )
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        comment="샤프 비율 (위험 조정 수익률)",
    )

    # === 거래 내역 ===
    trade_history: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="거래 내역 (JSON)",
    )

    # === 오류 정보 ===
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="실패 시 오류 메시지",
    )

    # === 시간 정보 ===
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="생성 시간",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="완료 시간",
    )

    # === 테이블 인덱스 정의 ===
    __table_args__ = (
        # 최신 결과 빠른 조회를 위한 내림차순 인덱스
        Index("idx_backtest_created_desc", created_at.desc()),
        # 상태별 조회를 위한 인덱스
        Index("idx_backtest_status", status),
    )

    def __repr__(self) -> str:
        """
        디버깅용 문자열 표현

        Returns:
            str: 모델 정보 문자열
        """
        return (
            f"<BacktestResult(id={self.id}, name='{self.name}', "
            f"status={self.status}, return={self.total_return_pct}%)>"
        )
