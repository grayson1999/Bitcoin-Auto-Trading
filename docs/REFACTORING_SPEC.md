# Backend 리팩토링 명세서

> 작성일: 2026-01-21

---

## 1. 현재 문제점

### 1.1 대형 파일
- `order_executor.py` - 1,129줄 (검증/실행/모니터링 혼재)
- `backtest_runner.py` - 792줄 (엔진/리포팅 혼재)
- `signal_generator.py` - 790줄 (프롬프트/파싱/생성 혼재)
- `upbit_client.py` - 741줄 (공개/비공개 API 혼재)

### 1.2 설정 분산
- `config.py` - Pydantic Settings (환경변수)
- `models/system_config.py` - DB 테이블 (런타임)
- `scheduler/jobs.py` - 하드코딩 상수
- 각 서비스 파일 - 하드코딩 상수 (MAX_RETRIES, TIMEOUT 등)

### 1.3 구조적 문제
- 도메인별 분리 없음 (flat 구조)
- Repository 패턴 미적용 (서비스에서 직접 DB 쿼리)
- 스키마가 API 폴더 내부에 위치

---

## 2. 목표 구조

```
backend/src/
├── main.py
├── database.py
├── config/
│   ├── settings.py           # 환경변수 (Pydantic)
│   ├── constants.py          # 불변 상수
│   └── logging.py
├── entities/                  # ORM 모델 (DB 테이블명 기준)
├── repositories/              # DB 접근 계층 (도메인명 기준)
├── modules/
│   └── <domain>/
│       ├── schemas.py         # API 요청/응답 DTO
│       ├── routes.py          # API 엔드포인트
│       └── service.py         # 비즈니스 로직
├── clients/                   # 외부 API
│   ├── upbit/
│   ├── ai/
│   └── slack_client.py
├── scheduler/
│   └── jobs/
└── utils/
```

---

## 3. 계층별 역할

### 3.1 공유 계층

| 계층 | 파일 기준 | 역할 | 이유 |
|------|-----------|------|------|
| Entity | DB 테이블명 | ORM 매핑, DB 구조 1:1 반영 | 테이블 변경 시 추적 용이 |
| Repository | 도메인명 | DB 쿼리 캡슐화, CRUD | 조인 등 복잡한 쿼리 대응 |

### 3.2 기능 모듈 (modules/<domain>/)

| 계층 | 역할 |
|------|------|
| Schemas | API 요청/응답 검증 (도메인별 DTO) |
| Service | 비즈니스 로직, 트랜잭션 처리 |
| Routes | API 엔드포인트, 요청 검증 |

---

## 4. 파일 분할 계획

### 4.1 order_executor.py → 3개
- `modules/trading/service.py` - 주문 실행 코어
- `modules/trading/order_validator.py` - 주문 전 검증
- `modules/trading/order_monitor.py` - 체결 모니터링

### 4.2 signal_generator.py → 3개
- `modules/signal/service.py` - 신호 생성 코어
- `modules/signal/prompt_builder.py` - 프롬프트 구성
- `modules/signal/response_parser.py` - AI 응답 파싱

### 4.3 backtest_runner.py → 2개
- `modules/backtest/engine.py` - 시뮬레이션 엔진
- `modules/backtest/reporter.py` - 결과 분석

### 4.4 upbit_client.py → 2개
- `clients/upbit/public_api.py` - 공개 API (시세, 캔들)
- `clients/upbit/private_api.py` - 비공개 API (주문, 잔고)

---

## 5. 설정 중앙화

### 5.1 설정 우선순위
```
1. DB SystemConfig (최우선, 런타임 변경 가능)
2. 환경변수
3. .env 파일
4. constants.py (기본값)
```

### 5.2 설정 분류

| 유형 | 위치 | 예시 |
|------|------|------|
| 민감 정보 | `config/settings.py` | API 키, DB URL |
| 불변 상수 | `config/constants.py` | 수수료율, 최소주문금액 |
| 런타임 설정 | DB `system_configs` | 거래 활성화, 포지션 비율 |

### 5.3 settings.py 주석 규칙
```python
class Settings(BaseSettings):
    # DB에서 오버라이드 가능: system_configs.position_size_min_pct
    position_size_min_pct: float = 25.0

    # DB에서 오버라이드 가능: system_configs.ai_model
    ai_model: str = "gemini-2.5-pro"

    # DB 오버라이드 없음 (환경변수 전용)
    database_url: str
```

### 5.4 하드코딩 상수 이동 대상
- `ai_client.py`: DEFAULT_TIMEOUT, MAX_RETRIES → `constants.py`
- `order_executor.py`: MIN_ORDER_AMOUNT, UPBIT_FEE → `constants.py`
- `jobs.py`: DATA_COLLECTION_INTERVAL, SIGNAL_INTERVAL_HOURS → DB

---

## 6. 작업 순서

### Phase 1: 기반 작업
1. `config/` 디렉토리 생성 및 설정 분리
2. `entities/` 디렉토리 생성 (models → entities)
3. `repositories/` 생성 및 BaseRepository 구현
4. `utils/` 생성

### Phase 2: 클라이언트 분리
1. `clients/upbit/` 분리
2. `clients/ai/` 분리
3. `clients/slack_client.py`, `auth_client.py` 이동

### Phase 3: 모듈화
1. `modules/market/` 생성
2. `modules/signal/` 생성 (SignalGenerator 분할)
3. `modules/trading/` 생성 (OrderExecutor 분할)
4. `modules/risk/` 생성
5. `modules/backtest/` 생성 (BacktestRunner 분할)
6. `modules/config/` 생성
7. `modules/health/` 생성

### Phase 4: 스케줄러 정리
1. `scheduler/jobs/` 분할

### Phase 5: 정리
1. 기존 `services/`, `api/` 삭제
2. import 경로 정리
3. Ruff 린트 및 테스트 작성

---

## 7. 결정된 사항

| 항목 | 결정 |
|------|------|
| ORM 폴더명 | `entities` |
| 도메인 폴더명 | `modules` |
| 클라이언트 폴더명 | `clients` |
| Repository 패턴 | 전체 적용 |
| 설정 우선순위 | DB 우선 (환경변수는 DB에 없을 때 fallback) |
| 마이그레이션 방식 | 한번에 전환 |
| 테스트 전략 | 리팩토링 후 작성 |
| 스케줄러 주기 | 하드코딩 (환경변수로 받고 재시작) |

---

## 8. 예상 결과

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 파일 수 | 50개 | ~70개 |
| 평균 라인 | 290줄 | 200줄 |
| 최대 라인 | 1,129줄 | ~500줄 |
| 설정 위치 | 4곳 | 2곳 (config/ + DB) |
