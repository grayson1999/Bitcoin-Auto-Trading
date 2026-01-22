# Research: Bitcoin Auto-Trading System

**Date**: 2026-01-11
**Branch**: `001-bitcoin-auto-trading`

## 1. AI 모델 선택 (비용 최적화)

### 요구사항 분석
- **호출 빈도**: 1시간 주기 = 24회/일 = 720회/월
- **예상 토큰**: 입력 ~2,000 토큰 (시장 데이터), 출력 ~500 토큰 (신호+근거)
- **월간 예상**: 입력 1.44M 토큰, 출력 360K 토큰
- **목표 예산**: 월 $10 이내

### AI 모델 가격 비교 (2026년 1월 기준)

| Provider | Model | Input $/1M | Output $/1M | 월 비용 예상 | 성능 |
|----------|-------|------------|-------------|------------|------|
| **Google** | Gemini 2.5 Flash-Lite | $0.10 | $0.40 | **$0.29** | 양호 |
| **Google** | Gemini 2.5 Flash | $0.15 | $0.60 | **$0.44** | 우수 |
| **OpenAI** | GPT-4o-mini | $0.15 | $0.60 | **$0.44** | 우수 |
| Google | Gemini 3 Flash | $0.50 | $3.00 | $1.80 | 매우 우수 |
| **Anthropic** | Claude 3 Haiku | $0.25 | $1.25 | **$0.81** | 우수 |
| Anthropic | Claude 3.5 Haiku | $0.80 | $4.00 | $2.59 | 매우 우수 |
| OpenAI | GPT-4o | $2.50 | $10.00 | $7.20 | 최상 |
| Google | Gemini 2.5 Pro | $1.25 | $10.00 | $5.40 | 최상 |
| Anthropic | Claude Sonnet 4.5 | $3.00 | $15.00 | $9.72 | 최상 |

### 결정: **Gemini 2.5 Flash** (주력) + **GPT-4o-mini** (대안)

**Rationale**:
1. **최저 비용**: Gemini 2.5 Flash는 월 $0.44로 예산의 4.4%만 사용
2. **무료 티어**: Google은 일일 1,000회 무료 요청 제공 → 실제 비용 $0 가능
3. **충분한 성능**: Flash 모델도 트레이딩 신호 생성에 충분한 추론 능력
4. **대안 확보**: GPT-4o-mini를 백업으로 설정 (동일 가격대, 다른 provider)

**Alternatives Considered**:
- Claude 3 Haiku: 약간 더 비쌈 ($0.81/월), 하지만 분석력 우수
- GPT-4o: 성능 최상이지만 비용 16배 ($7.20/월)
- Gemini 2.5 Flash-Lite: 가장 저렴하지만 추론 품질 우려

### 비용 최적화 전략

1. **Prompt Caching 활용**
   - 시스템 프롬프트와 분석 지침을 캐싱
   - 캐시 읽기는 기본 가격의 10% → 90% 절감
   - 예상 절감: 월 $0.44 → $0.10 이하

2. **배치 처리** (선택적)
   - 급하지 않은 분석은 Batch API 활용
   - 50% 할인 적용 가능

3. **토큰 최적화**
   - 시장 데이터 요약 전송 (불필요한 상세 제거)
   - JSON 스키마로 출력 구조화 (토큰 절약)

---

## 2. Upbit 거래 수수료 분석

### 수수료 구조

| 마켓 | Maker | Taker | 비고 |
|------|-------|-------|------|
| **KRW 마켓** | 0.05% | 0.05% | BTC/KRW 거래 시 적용 |
| BTC/USDT 마켓 | 0.25% | 0.25% | 사용 안함 |
| 지정가 손절 | 0.139% | 0.139% | Stop-limit 주문 |

### 비용 시뮬레이션

**가정**: 월 100만원 거래량 (일평균 ~3.3만원)

| 시나리오 | 거래 횟수/월 | 총 거래량 | 수수료 |
|----------|-------------|----------|--------|
| 보수적 | 10회 | 100만원 | 1,000원 |
| 표준 | 30회 | 100만원 | 1,000원 |
| 적극적 | 100회 | 500만원 | 5,000원 |

**결론**: 수수료는 0.05%로 업계 최저 수준. 비용 우려 낮음.

### AI 호출 vs 거래 수수료 비교

| 항목 | 월 비용 | 비고 |
|------|--------|------|
| AI API (Gemini Flash) | ~$0.44 (~600원) | 720회 호출 |
| AI API (무료 티어 활용) | $0 | 일일 1,000회 무료 |
| 거래 수수료 | ~1,000원 | 100만원 거래 기준 |
| **월 총 비용** | **~1,000~1,600원** | 매우 경제적 |

---

## 3. 기술 스택 결정

### Backend

| 영역 | 선택 | Rationale |
|------|------|-----------|
| 언어 | Python 3.11+ | AI SDK 지원, 빠른 개발 |
| 웹 프레임워크 | FastAPI | 비동기 지원, 자동 문서화 |
| HTTP 클라이언트 | httpx | 비동기, 현대적 API |
| ORM | SQLAlchemy 2.0 | 비동기 지원, 타입 안전성 |
| 스케줄러 | APScheduler | 간단한 주기적 작업 |
| AI SDK | google-generativeai | Gemini API 공식 SDK |
| 검증 | Pydantic v2 | 데이터 검증, 설정 관리 |
| 로깅 | loguru | 구조화된 로깅, 간편한 설정 |

### Frontend (대시보드)

| 영역 | 선택 | Rationale |
|------|------|-----------|
| 프레임워크 | React + Vite | 빠른 개발, 풍부한 에코시스템 |
| UI 라이브러리 | Tailwind CSS | 빠른 스타일링 |
| 차트 | Recharts | React 네이티브, 간편 |
| 상태 관리 | React Query | 서버 상태 캐싱 |

**Alternatives Considered**:
- Streamlit: 더 간단하지만 커스터마이징 제한
- Django: 오버킬, FastAPI가 더 가볍고 현대적

### Database

| 환경 | 선택 | Rationale |
|------|------|-----------|
| 개발 | SQLite | 설정 불필요, 로컬 테스트 용이 |
| 운영 | PostgreSQL | 동시성, 안정성, 무료 |

---

## 4. Upbit API 연동

### 인증 방식
- JWT 토큰 기반 (access_key, secret_key)
- 요청마다 JWT 서명 필요

### 주요 엔드포인트

| 용도 | 엔드포인트 | Rate Limit |
|------|-----------|------------|
| 시세 조회 | `GET /v1/ticker` | 초당 10회 |
| 체결 내역 | `GET /v1/trades/ticks` | 초당 10회 |
| 주문 생성 | `POST /v1/orders` | 초당 8회 |
| 잔고 조회 | `GET /v1/accounts` | 초당 10회 |
| 주문 조회 | `GET /v1/order` | 초당 10회 |

### 에러 처리 전략
1. **재시도**: 429 (Rate Limit) → exponential backoff
2. **점검 감지**: 503 → 대기 모드 전환
3. **인증 오류**: 401 → 즉시 알림 + 시스템 중단

---

## 5. 리스크 관리 파라미터

### 확정된 설정

| 파라미터 | 기본값 | 설정 가능 |
|----------|--------|----------|
| 포지션 크기 | 2% | 1~5% |
| 개별 손절 | 5% | 3~10% |
| 일일 손실 한도 | 5% | 3~10% |
| AI 신호 주기 | 1시간 | 30분~4시간 |
| 데이터 보존 | 1년 | 6개월~무제한 |

### 변동성 감지 기준
- 5분 내 가격 변동 > 3% → 안전장치 발동
- 시스템 자동 일시 정지 후 슬랙 알림

---

## 6. 배포 환경

### 권장 구성

| 항목 | 선택 | 월 비용 |
|------|------|--------|
| 서버 | Oracle Cloud Free Tier | $0 |
| 대안 | Vultr/Linode 최저 플랜 | ~$5 |
| DB | PostgreSQL (서버 내장) | $0 |
| 도메인 | 선택사항 | $0~12/년 |

### Docker 구성
```
docker-compose.yml
├── backend (FastAPI)
├── frontend (Nginx + React)
├── db (PostgreSQL)
└── scheduler (APScheduler in backend)
```

---

## 7. 모니터링 및 알림

### 슬랙 알림 대상 (심각한 이슈만)
- 시스템 시작/종료
- 일일 손실 한도 도달
- API 연결 실패 (3회 연속)
- 주문 실행 실패
- 서버 상태 이상

### 대시보드 표시 항목
- 현재 포지션 및 수익률
- 최근 거래 내역
- AI 신호 히스토리
- 리스크 상태 (일일 손익)

---

## Sources

- [OpenAI API Pricing](https://openai.com/api/pricing/)
- [Anthropic API Pricing](https://docs.anthropic.com/claude/docs/models-overview)
- [Google Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Upbit Exchange Fees](https://tradersunion.com/brokers/crypto/view/upbit/fees/)
- [Upbit API Documentation](https://docs.upbit.com/)
