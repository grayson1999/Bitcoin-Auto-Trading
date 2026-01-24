# Research: Backend 성능 최적화

**Date**: 2026-01-24 | **Branch**: `002-backend-performance`

## 1. DB 커넥션 풀 크기

**Decision**: 10/20 (min/max)

**Rationale**:
- 현재 동시 작업: 시세 수집(10초), 신호 생성(30분), 변동성 체크(30초), 주문 동기화(5분), API 응답
- 최대 동시 세션 예상: 5-8개 (정상), 10-15개 (피크)
- 풀 크기 10개 + 오버플로우 10개 = 총 20개로 충분한 여유 확보

**Alternatives Considered**:
- 8/15: 보수적이나 피크 시 부족 가능
- 15/30: 과도한 프로비저닝, PostgreSQL 연결 리소스 낭비

---

## 2. TTL 캐시 구현 방식

**Decision**: 인메모리 TTLCache (직접 구현)

**Rationale**:
- 설정값 캐시는 단일 프로세스 내에서만 필요
- Redis 등 외부 캐시는 오버엔지니어링
- TTL 1시간 + 수동 무효화로 충분한 일관성 보장
- asyncio.Lock으로 동시성 안전 보장

**Alternatives Considered**:
- cachetools.TTLCache: 동기 전용, 비동기 환경 부적합
- Redis: 인프라 복잡도 증가, 단일 서비스에 불필요
- aiocache: 외부 의존성 추가 불필요

---

## 3. 재시도 전략

**Decision**: 지수 백오프 3회 (1초→2초→4초)

**Rationale**:
- Rate Limit(429) 오류 시 즉시 재시도는 악화 요인
- 지수 백오프로 서버 부하 분산
- 총 대기 시간 7초는 스케줄러 주기(10초, 30초) 내 수용 가능
- 3회 실패 시 다음 주기로 넘김

**Alternatives Considered**:
- 고정 간격 5초: Rate Limit 해제 전 재시도 가능성
- 5회 재시도: 총 31초 대기로 주기 초과 가능

---

## 4. 헬스체크 구성요소

**Decision**: 6개 (DB, Upbit API, Gemini API, 스케줄러, 최근 신호, 최근 주문)

**Rationale**:
- DB: 핵심 인프라, 연결 실패 = 전체 장애
- Upbit API: 거래 실행 의존성
- Gemini API: 신호 생성 의존성
- 스케줄러: 백그라운드 작업 상태
- 최근 신호: 데이터 파이프라인 정상 확인
- 최근 주문: 거래 실행 상태 확인

**Alternatives Considered**:
- 5개 (최근 주문 제외): 거래 상태 모니터링 부재
- 8개 (캐시, 메모리 추가): 초기 단계에서 오버 모니터링

---

## 5. 메트릭 저장 방식

**Decision**: 구조화된 JSON 로그 (loguru serialize)

**Rationale**:
- 기존 loguru 인프라 활용
- JSON 형식으로 로그 수집 도구(Loki, CloudWatch)와 호환
- DB 저장 대비 저비용
- 필요시 Prometheus로 확장 용이

**Alternatives Considered**:
- 일반 텍스트 로그: 파싱 어려움
- DB 테이블: 추가 스키마 관리, 조회 쿼리 필요

---

## 6. 인덱스 현황 (조사 결과)

**Decision**: 추가 작업 불필요

**Findings**:
- Order 테이블: 4개 인덱스 존재 (status, created_desc, user_created, upbit_uuid)
- TradingSignal 테이블: 3개 인덱스 존재 (created_desc, type_created, user_created)
- MarketData 테이블: 3개 인덱스 존재 (symbol_timestamp, timestamp_desc, date)

**Verification**: EXPLAIN ANALYZE로 인덱스 스캔 사용 확인 예정

---

## 7. 기술 스택 확인

| 항목 | 현재 버전 | 호환성 |
|------|----------|--------|
| Python | 3.11 | ✅ |
| SQLAlchemy | 2.0+ | ✅ asyncio 완전 지원 |
| APScheduler | 3.10+ | ✅ AsyncIOScheduler |
| loguru | 최신 | ✅ JSON serialize 지원 |
| httpx | 최신 | ✅ async 클라이언트 |
| asyncpg | 최신 | ✅ PostgreSQL 15 호환 |
