# Implementation Plan: Backend Layered Architecture Refactoring

**Branch**: `2-backend-layered-arch` | **Date**: 2026-01-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/2-backend-layered-arch/spec.md`

## Summary

기존 flat 구조의 backend 코드베이스를 계층형 아키텍처로 리팩토링한다. 설정 중앙화(config/), ORM 분리(entities/), Repository 패턴 도입(repositories/), 도메인별 모듈화(modules/), 외부 클라이언트 분리(clients/)를 통해 코드 가독성과 유지보수성을 향상시킨다.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI 0.100+, SQLAlchemy 2.0+ (async), Pydantic v2, APScheduler 3.10+
**Storage**: PostgreSQL 15 (asyncpg driver)
**Testing**: pytest, pytest-asyncio (리팩토링 후 작성)
**Target Platform**: Linux server (Ubuntu)
**Project Type**: Web application (backend only, frontend는 별도)
**Performance Goals**: 기존 성능 유지 (하위 호환성)
**Constraints**: API 엔드포인트 경로 유지, DB 테이블 구조 유지
**Scale/Scope**: 50개 파일 → ~70개 파일, 최대 1,129줄 → 500줄 이하

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution이 템플릿 상태이므로 기본 원칙 적용:
- [x] 단일 책임 원칙: 파일 분할을 통해 준수
- [x] 하위 호환성: API 경로 및 DB 구조 유지
- [x] 테스트 가능성: Repository 패턴으로 모킹 용이

**Status**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/2-backend-layered-arch/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - 기존 API 유지)
├── checklists/
│   └── requirements.md  # Quality checklist
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
backend/src/
├── main.py                          # FastAPI 앱 진입점 (유지)
├── database.py                      # SQLAlchemy 엔진/세션 (유지)
│
├── config/                          # [NEW] 설정 중앙화
│   ├── __init__.py
│   ├── settings.py                  # Pydantic BaseSettings
│   ├── constants.py                 # 불변 상수
│   └── logging.py                   # 로깅 설정
│
├── entities/                        # [RENAMED] models → entities
│   ├── __init__.py
│   ├── base.py                      # Base, TimestampMixin
│   ├── market_data.py
│   ├── trading_signal.py
│   ├── order.py
│   ├── position.py
│   ├── daily_stats.py
│   ├── risk_event.py
│   ├── backtest_result.py
│   └── system_config.py
│
├── repositories/                    # [NEW] DB 접근 계층
│   ├── __init__.py
│   ├── base.py                      # BaseRepository (Generic CRUD)
│   ├── market_repository.py
│   ├── signal_repository.py
│   ├── order_repository.py
│   ├── position_repository.py
│   └── config_repository.py
│
├── modules/                         # [NEW] 도메인별 모듈
│   ├── market/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── routes.py
│   │   └── service.py
│   ├── signal/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── routes.py
│   │   ├── service.py
│   │   ├── prompt_builder.py        # [SPLIT] from signal_generator
│   │   └── response_parser.py       # [SPLIT] from signal_generator
│   ├── trading/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── routes.py
│   │   ├── service.py               # [SPLIT] from order_executor
│   │   ├── order_validator.py       # [SPLIT] from order_executor
│   │   └── order_monitor.py         # [SPLIT] from order_executor
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── routes.py
│   │   └── service.py
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── routes.py
│   │   ├── engine.py                # [SPLIT] from backtest_runner
│   │   └── reporter.py              # [SPLIT] from backtest_runner
│   ├── config/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── routes.py
│   │   └── service.py
│   └── health/
│       ├── __init__.py
│       └── routes.py
│
├── clients/                         # [NEW] 외부 API 클라이언트
│   ├── __init__.py
│   ├── upbit/
│   │   ├── __init__.py
│   │   ├── public_api.py            # [SPLIT] from upbit_client
│   │   └── private_api.py           # [SPLIT] from upbit_client
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── base.py                  # 공통 인터페이스
│   │   ├── gemini_client.py
│   │   └── openai_client.py
│   ├── slack_client.py              # [MOVED] from services/notifier
│   └── auth_client.py               # [MOVED] from services/auth_client
│
├── scheduler/                       # [REFACTORED] 스케줄러
│   ├── __init__.py
│   ├── scheduler.py                 # APScheduler 초기화
│   └── jobs/
│       ├── __init__.py
│       ├── data_collection.py
│       ├── signal_generation.py
│       ├── order_sync.py
│       └── cleanup.py
│
└── utils/                           # [NEW] 공통 유틸리티
    ├── __init__.py
    ├── datetime_utils.py
    ├── number_utils.py
    └── decorators.py
```

**Structure Decision**: Web application 구조 선택. backend/ 폴더 내에서 계층형 아키텍처 적용.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Repository 패턴 | 쿼리 중복 제거, 테스트 용이성 | 직접 DB 접근 시 코드 중복, 모킹 어려움 |
| 7개 모듈 분리 | 도메인별 응집도 향상 | flat 구조는 관련 코드 탐색 어려움 |
