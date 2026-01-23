"""Migrate data ownership to default system user.

Revision ID: 009
Revises: 008
Create Date: 2026-01-24

Actions:
- Create default system user
- Assign all existing records to default user
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


SYSTEM_USER_UUID = "00000000-0000-0000-0000-000000000000"


def upgrade() -> None:
    """Create default user and migrate existing data ownership."""

    # 1. 기본 시스템 사용자 생성
    op.execute(f"""
        INSERT INTO users (auth_user_id, email, name, created_at, updated_at)
        VALUES (
            '{SYSTEM_USER_UUID}',
            'system@local',
            'System',
            NOW(),
            NOW()
        )
        ON CONFLICT (auth_user_id) DO NOTHING
    """)

    # 2. 기존 데이터 소유권 할당 (user_id가 NULL인 레코드만)
    # 서브쿼리를 사용해 실제 시스템 사용자 ID를 조회
    system_user_subquery = (
        f"(SELECT id FROM users WHERE auth_user_id = '{SYSTEM_USER_UUID}')"
    )

    op.execute(
        f"UPDATE orders SET user_id = {system_user_subquery} WHERE user_id IS NULL"
    )
    op.execute(
        f"UPDATE trading_signals SET user_id = {system_user_subquery} WHERE user_id IS NULL"
    )
    op.execute(
        f"UPDATE positions SET user_id = {system_user_subquery} WHERE user_id IS NULL"
    )
    op.execute(
        f"UPDATE daily_stats SET user_id = {system_user_subquery} WHERE user_id IS NULL"
    )
    op.execute(
        f"UPDATE risk_events SET user_id = {system_user_subquery} WHERE user_id IS NULL"
    )


def downgrade() -> None:
    """Reset user_id to NULL and remove system user."""
    # 소유권 해제
    op.execute("UPDATE orders SET user_id = NULL")
    op.execute("UPDATE trading_signals SET user_id = NULL")
    op.execute("UPDATE positions SET user_id = NULL")
    op.execute("UPDATE daily_stats SET user_id = NULL")
    op.execute("UPDATE risk_events SET user_id = NULL")

    # 시스템 사용자 삭제
    op.execute(f"DELETE FROM users WHERE auth_user_id = '{SYSTEM_USER_UUID}'")
