"""
데이터베이스 연결 및 세션 관리 모듈

이 모듈은 SQLAlchemy 비동기 엔진과 세션을 관리합니다.
- PostgreSQL 비동기 연결 (asyncpg 드라이버)
- 커넥션 풀 설정
- 세션 팩토리 및 의존성 주입
- 앱 시작/종료 시 연결 관리
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings

# === 커넥션 풀 설정 ===
POOL_SIZE = 5  # 기본 풀 크기 (동시 연결 수)
MAX_OVERFLOW = 10  # 풀 초과 시 추가 허용 연결 수 (최대 15개)

# 비동기 SQLAlchemy 엔진 생성
# - echo: 디버그 모드에서 SQL 쿼리 로깅
# - pool_pre_ping: 연결 유효성 사전 검사 (끊어진 연결 감지)
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # SQL 쿼리 로깅 (디버그 모드에서만)
    pool_pre_ping=True,  # 연결 건강 검사
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
)

# 비동기 세션 팩토리
# - expire_on_commit=False: 커밋 후에도 객체 속성 접근 가능
# - autocommit=False: 명시적 커밋 필요
# - autoflush=False: 쿼리 전 자동 플러시 비활성화
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    비동기 데이터베이스 세션 의존성

    FastAPI의 Depends와 함께 사용하여 요청별 세션을 제공합니다.
    세션은 컨텍스트 매니저로 관리되어 자동으로 커밋/롤백/종료됩니다.

    사용 예시:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()

    Yields:
        AsyncSession: 데이터베이스 세션

    Raises:
        Exception: 작업 중 오류 발생 시 롤백 후 재발생
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()  # 성공 시 커밋
        except Exception:
            await session.rollback()  # 오류 시 롤백
            raise
        finally:
            await session.close()  # 항상 세션 종료


async def init_db() -> None:
    """
    데이터베이스 연결 초기화

    앱 시작 시 호출되어 데이터베이스 연결을 테스트합니다.
    연결 실패 시 예외가 발생하여 앱 시작이 중단됩니다.

    Raises:
        Exception: 데이터베이스 연결 실패 시
    """
    async with engine.begin() as conn:
        # SELECT 1로 연결 테스트
        await conn.execute(text("SELECT 1"))


async def close_db() -> None:
    """
    데이터베이스 연결 해제

    앱 종료 시 호출되어 모든 연결 풀을 정리합니다.
    열린 연결을 안전하게 닫고 리소스를 해제합니다.
    """
    await engine.dispose()
