"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from src.api import api_router
from src.config import APP_VERSION, settings, setup_logging
from src.database import close_db, init_db

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    setup_logging()
    logger.info("Starting Bitcoin Auto-Trading Backend")

    try:
        await init_db()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Bitcoin Auto-Trading Backend")
    await close_db()
    logger.info("Database connection closed")


app = FastAPI(
    title="Bitcoin Auto-Trading API",
    description="Automated Bitcoin trading system with AI-powered signals",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions globally."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__,
        },
    )


# Include API routers
app.include_router(api_router)


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "name": "Bitcoin Auto-Trading API",
        "version": APP_VERSION,
        "docs": "/docs" if settings.debug else "Disabled in production",
    }
