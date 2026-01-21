# Feature Specification: Backend Layered Architecture Refactoring

**Feature Branch**: `2-backend-layered-arch`
**Created**: 2026-01-21
**Status**: Draft
**Input**: Backend 코드베이스를 계층형 아키텍처로 리팩토링

## User Scenarios & Testing

### User Story 1 - 설정 중앙 관리 (Priority: P1)

개발자가 시스템 설정을 변경할 때, 단일 위치(DB 또는 config/)에서 관리하여 설정 분산으로 인한 혼란을 제거한다.

**Why this priority**: 현재 설정이 4곳 이상에 분산되어 있어 유지보수 시 어떤 값이 적용되는지 파악이 어려움. 모든 후속 작업의 기반이 됨.

**Independent Test**: 설정 값을 DB에서 변경하고, 해당 값이 런타임에 즉시 반영되는지 확인하여 테스트 가능

**Acceptance Scenarios**:

1. **Given** DB에 `trading_enabled=false` 설정이 있을 때, **When** 시스템이 설정을 조회하면, **Then** 환경변수 값보다 DB 값이 우선 적용된다
2. **Given** DB에 특정 설정이 없을 때, **When** 시스템이 설정을 조회하면, **Then** 환경변수 또는 기본값이 적용된다
3. **Given** 민감 정보(API 키)가 필요할 때, **When** 시스템이 조회하면, **Then** 환경변수에서만 로드되고 DB에 저장되지 않는다

---

### User Story 2 - 도메인별 모듈 분리 (Priority: P1)

개발자가 특정 기능을 수정할 때, 해당 도메인 폴더(modules/<domain>/)만 확인하면 관련 코드(routes, service, schemas)를 모두 찾을 수 있다.

**Why this priority**: 현재 flat 구조로 인해 관련 코드가 여러 폴더에 분산되어 있어 기능 파악과 수정이 어려움

**Independent Test**: 특정 도메인(예: trading)의 버그를 수정할 때, modules/trading/ 폴더 내 파일만 수정하여 해결 가능한지 확인

**Acceptance Scenarios**:

1. **Given** trading 도메인 수정이 필요할 때, **When** modules/trading/ 폴더를 열면, **Then** routes.py, service.py, schemas.py가 모두 존재한다
2. **Given** 새 API 엔드포인트를 추가할 때, **When** 해당 도메인 폴더에 코드를 추가하면, **Then** 다른 도메인 폴더를 수정할 필요가 없다
3. **Given** 7개 도메인(market, signal, trading, risk, backtest, config, health)이 있을 때, **When** 각 도메인 폴더를 확인하면, **Then** 동일한 구조(routes, service, schemas)를 가진다

---

### User Story 3 - Repository 패턴을 통한 DB 접근 추상화 (Priority: P2)

개발자가 DB 쿼리를 작성할 때, Repository 계층을 통해 일관된 방식으로 데이터에 접근하여 코드 중복을 줄인다.

**Why this priority**: 서비스 계층에서 직접 DB 쿼리를 수행하면 쿼리 로직이 중복되고 테스트가 어려움

**Independent Test**: OrderRepository.get_pending() 메서드를 호출하여 대기 중인 주문 목록을 조회하고, 동일한 쿼리가 여러 서비스에서 재사용되는지 확인

**Acceptance Scenarios**:

1. **Given** 대기 중인 주문을 조회해야 할 때, **When** OrderRepository.get_pending()을 호출하면, **Then** 일관된 결과를 반환한다
2. **Given** 복잡한 조인 쿼리가 필요할 때, **When** Repository에 메서드를 추가하면, **Then** 여러 서비스에서 재사용할 수 있다
3. **Given** Repository가 5개(market, signal, order, position, config) 존재할 때, **When** 각 Repository를 확인하면, **Then** BaseRepository를 상속하여 공통 CRUD 메서드를 가진다

---

### User Story 4 - 대형 파일 분할 (Priority: P2)

개발자가 특정 기능을 수정할 때, 500줄 이하의 파일에서 단일 책임을 가진 코드를 수정하여 가독성과 유지보수성을 높인다.

**Why this priority**: 1,000줄 이상의 파일은 코드 탐색과 이해가 어려우며, 여러 책임이 혼재되어 버그 발생 위험이 높음

**Independent Test**: order_executor.py(1,129줄)가 3개 파일로 분할되어 각 파일이 500줄 이하인지 확인

**Acceptance Scenarios**:

1. **Given** order_executor.py(1,129줄)가 있을 때, **When** 리팩토링 후, **Then** service.py, order_validator.py, order_monitor.py 3개 파일로 분할되고 각각 500줄 이하이다
2. **Given** signal_generator.py(790줄)가 있을 때, **When** 리팩토링 후, **Then** service.py, prompt_builder.py, response_parser.py 3개 파일로 분할된다
3. **Given** 분할된 파일들이 있을 때, **When** 각 파일을 확인하면, **Then** 단일 책임(검증, 실행, 모니터링 등)만 담당한다

---

### User Story 5 - 외부 클라이언트 분리 (Priority: P3)

개발자가 외부 API 연동 코드를 수정할 때, clients/ 폴더에서 해당 클라이언트만 수정하여 비즈니스 로직과 분리된 상태를 유지한다.

**Why this priority**: 외부 API 클라이언트가 서비스 로직과 혼재되면 API 변경 시 영향 범위 파악이 어려움

**Independent Test**: Upbit API 응답 형식이 변경될 때, clients/upbit/ 폴더의 파일만 수정하여 대응 가능한지 확인

**Acceptance Scenarios**:

1. **Given** Upbit API 클라이언트가 필요할 때, **When** clients/upbit/를 확인하면, **Then** public_api.py와 private_api.py가 분리되어 있다
2. **Given** AI 클라이언트가 필요할 때, **When** clients/ai/를 확인하면, **Then** gemini_client.py와 openai_client.py가 분리되어 있다
3. **Given** 클라이언트 코드를 수정할 때, **When** clients/ 폴더만 수정하면, **Then** modules/ 폴더의 비즈니스 로직은 수정하지 않아도 된다

---

### Edge Cases

- entities/ 이동 시 기존 models/ import 경로를 사용하는 코드가 있으면 어떻게 처리하는가? → 한번에 전환하여 모든 import 경로 일괄 수정
- DB 설정과 환경변수 설정이 충돌할 때 어떤 값이 적용되는가? → DB 값 우선, DB에 없으면 환경변수 fallback
- 스케줄러 작업 중 설정이 변경되면 어떻게 되는가? → 스케줄러 주기는 하드코딩, 변경 시 재시작 필요

## Requirements

### Functional Requirements

- **FR-001**: 시스템은 config/ 디렉토리에서 모든 환경 설정을 중앙 관리해야 한다 (settings.py, constants.py, logging.py)
- **FR-002**: 시스템은 DB SystemConfig 테이블의 값을 환경변수보다 우선 적용해야 한다
- **FR-003**: 시스템은 민감 정보(API 키, DB URL)를 환경변수에서만 로드하고 DB에 저장하지 않아야 한다
- **FR-004**: 시스템은 entities/ 디렉토리에서 모든 ORM 모델을 DB 테이블명 기준으로 관리해야 한다
- **FR-005**: 시스템은 repositories/ 디렉토리에서 도메인별 DB 접근 로직을 캡슐화해야 한다
- **FR-006**: 시스템은 modules/<domain>/ 구조로 7개 도메인(market, signal, trading, risk, backtest, config, health)을 분리해야 한다
- **FR-007**: 각 모듈은 schemas.py(DTO), routes.py(API), service.py(비즈니스 로직)을 포함해야 한다
- **FR-008**: 시스템은 clients/ 디렉토리에서 외부 API 클라이언트(upbit, ai, slack, auth)를 분리해야 한다
- **FR-009**: 시스템은 order_executor.py를 3개 파일(service, validator, monitor)로 분할해야 한다
- **FR-010**: 시스템은 signal_generator.py를 3개 파일(service, prompt_builder, response_parser)로 분할해야 한다
- **FR-011**: 시스템은 backtest_runner.py를 2개 파일(engine, reporter)로 분할해야 한다
- **FR-012**: 시스템은 upbit_client.py를 2개 파일(public_api, private_api)로 분할해야 한다
- **FR-013**: 분할된 모든 파일은 500줄 이하를 유지해야 한다
- **FR-014**: 시스템은 스케줄러 주기 설정을 환경변수로 관리하고, 변경 시 재시작이 필요하다
- **FR-015**: 리팩토링 후 모든 기존 API 엔드포인트 경로(/api/v1/...)가 유지되어야 한다
- **FR-016**: 리팩토링 후 모든 기존 DB 테이블 구조가 유지되어야 한다

### Key Entities

- **Entity (entities/)**: DB 테이블과 1:1 매핑되는 ORM 모델. 테이블명 기준으로 파일 명명 (예: market_data.py, trading_signal.py)
- **Repository (repositories/)**: 도메인별 DB 쿼리 캡슐화. CRUD 공통 메서드와 도메인 특화 메서드 포함
- **Module (modules/)**: 도메인별 기능 단위. schemas(DTO), routes(API), service(로직) 포함
- **Client (clients/)**: 외부 API 연동 클라이언트. 비즈니스 로직과 분리된 HTTP 호출 담당

## Success Criteria

### Measurable Outcomes

- **SC-001**: 모든 파일이 500줄 이하를 유지한다 (현재 최대 1,129줄 → 500줄 이하)
- **SC-002**: 설정 관리 위치가 2곳(config/ + DB)으로 통합된다 (현재 4곳 이상)
- **SC-003**: 개발자가 특정 도메인 기능 수정 시 해당 모듈 폴더만 확인하면 된다 (탐색 범위 감소)
- **SC-004**: 모든 기존 API 엔드포인트가 동일한 경로와 응답 형식을 유지한다 (하위 호환성 100%)
- **SC-005**: 코드 라인 평균이 290줄에서 200줄로 감소한다
- **SC-006**: Ruff 린트 검사를 통과한다 (기존 규칙 + 추가 규칙 적용)
