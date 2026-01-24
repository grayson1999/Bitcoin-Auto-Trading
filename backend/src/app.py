"""
FastAPI 애플리케이션 진입점

이 모듈은 Bitcoin Auto-Trading 백엔드 서버의 메인 진입점입니다.
- FastAPI 앱 초기화 및 설정
- CORS 미들웨어 구성
- 앱 라이프사이클 관리 (시작/종료)
- 전역 예외 처리
- API 라우터 통합
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.api import api_router
from src.clients import (
    close_auth_client,
    close_slack_client,
    close_upbit_private_api,
    close_upbit_public_api,
    get_auth_client,
)
from src.config import APP_VERSION, settings, setup_logging
from src.scheduler import setup_scheduler, start_scheduler, stop_scheduler
from src.utils.database import close_db, init_db

# CORS 허용 오리진 목록
# 프론트엔드 개발 서버 주소들을 허용
CORS_ORIGINS = [
    "http://localhost:3000",  # React 기본 포트
    "http://localhost:5173",  # Vite 기본 포트
    "http://127.0.0.1:5173",  # 로컬호스트 대체 주소
]

# === 에러 응답 상수 ===
INTERNAL_SERVER_ERROR_STATUS = 500
INTERNAL_SERVER_ERROR_MESSAGE = "서버 내부 오류가 발생했습니다"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    애플리케이션 라이프사이클 관리자

    FastAPI의 lifespan 이벤트를 처리하여 앱 시작 시 초기화 작업과
    종료 시 정리 작업을 수행합니다.

    시작 시:
        1. 로깅 설정 초기화
        2. 데이터베이스 연결 수립
        3. 스케줄러 설정 및 시작 (시장 데이터 수집)

    종료 시:
        1. 스케줄러 중지
        2. 데이터베이스 연결 해제

    Yields:
        None: 앱 실행 중 상태
    """
    # === 시작 단계 ===
    setup_logging()
    logger.info("Bitcoin Auto-Trading 백엔드 시작 중...")

    # 데이터베이스 연결 초기화
    try:
        await init_db()
        logger.info("데이터베이스 연결 완료")
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        raise

    # 스케줄러 설정 및 시작 (시장 데이터 자동 수집)
    setup_scheduler()
    start_scheduler()
    logger.info("스케줄러 시작됨")

    # Auth Client 초기화 (싱글톤)
    get_auth_client()
    logger.info("Auth Client 초기화됨")

    yield  # 앱 실행 중

    # === 종료 단계 ===
    logger.info("Bitcoin Auto-Trading 백엔드 종료 중...")
    stop_scheduler()
    logger.info("스케줄러 중지됨")

    # Slack 로그 핸들러 종료
    if settings.slack_webhook_url:
        from src.modules.notification import get_slack_log_handler

        get_slack_log_handler().close()
        logger.info("Slack 로그 핸들러 종료됨")

    # HTTP 클라이언트들 정리 (리소스 누수 방지)
    await close_auth_client()
    logger.info("Auth Client 종료됨")

    await close_slack_client()
    logger.info("Slack Client 종료됨")

    await close_upbit_private_api()
    await close_upbit_public_api()
    logger.info("Upbit API 클라이언트 종료됨")

    await close_db()
    logger.info("데이터베이스 연결 해제됨")


# FastAPI 앱 인스턴스 생성
# - debug 모드에서만 Swagger/ReDoc 문서 활성화
app = FastAPI(
    title="Bitcoin Auto-Trading API",
    description="AI 기반 자동 암호화폐 거래 시스템",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,  # Swagger UI
    redoc_url="/redoc" if settings.debug else None,  # ReDoc
)

# CORS 미들웨어 추가
# 프론트엔드에서 API 호출을 허용하기 위한 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # 허용할 오리진 목록
    allow_credentials=True,  # 쿠키/인증 정보 허용
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    전역 예외 처리기

    처리되지 않은 모든 예외를 캐치하여 일관된 JSON 응답으로 변환합니다.
    예외 상세 정보는 로그에 기록되고, 클라이언트에는 일반적인 오류 메시지만 반환됩니다.

    Args:
        request: 요청 객체
        exc: 발생한 예외

    Returns:
        JSONResponse: 500 상태 코드와 오류 정보를 담은 JSON 응답
    """
    logger.exception(f"처리되지 않은 예외 발생: {exc}")
    return JSONResponse(
        status_code=INTERNAL_SERVER_ERROR_STATUS,
        content={
            "detail": INTERNAL_SERVER_ERROR_MESSAGE,
            "type": type(exc).__name__,
        },
    )


# API 라우터 등록 (/api/v1 접두사)
app.include_router(api_router)


@app.get("/")
async def root() -> dict:
    """
    루트 엔드포인트

    API 기본 정보를 반환합니다.

    Returns:
        dict: API 이름, 버전, 문서 URL 정보
    """
    return {
        "name": "Bitcoin Auto-Trading API",
        "version": APP_VERSION,
        "docs": "/docs" if settings.debug else "프로덕션 모드에서는 비활성화됨",
    }
