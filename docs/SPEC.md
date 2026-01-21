# Bitcoin Auto-Trading System Specification

## 1. 프로젝트 개요 (Project Overview)

Upbit 거래소와 ChatGPT API를 연동하여 비트코인 자동 매매를 수행하는 시스템입니다. 실시간 시장 데이터를 수집하고, AI 기반 매매 신호를 생성하며, 리스크 관리 하에 자동 주문을 실행합니다.

## 2. 시스템 구성 요소 (System Components)

### 2.1 데이터 수집 모듈 (Data Collection Module)

| 항목 | 사양 |
|------|------|
| 데이터 소스 | Upbit API |
| 수집 데이터 | 비트코인 가격, 거래량, 체결 정보 |
| 업데이트 주기 | 1초 간격 (설정 가능) |
| 오류 처리 | 자동 재시도, 예외 처리 로직 포함 |

### 2.2 AI 신호 생성 모듈 (AI Signal Generation Module)

| 항목 | 사양 |
|------|------|
| AI 엔진 | ChatGPT API |
| 입력 | 정제된 시장 데이터 |
| 출력 | 매매 신호 (Buy / Hold / Sell) |
| 데이터 정제 | 원시 데이터를 AI 분석 가능 형식으로 변환 |

### 2.3 주문 실행 모듈 (Order Execution Module)

| 항목 | 사양 |
|------|------|
| 거래소 API | Upbit API |
| 주문 유형 | 시장가/지정가 주문 지원 |
| 재시도 로직 | 주문 실패 시 자동 재시도 |
| 피드백 | 체결 정보 및 오류 메시지 수신 처리 |

### 2.4 리스크 관리 모듈 (Risk Management Module)

| 항목 | 사양 |
|------|------|
| 포지션 사이징 | 전체 자본 대비 1~2% 제한 |
| 손절 기준 | 개별 거래 3~5% 손실 시 자동 손절 |
| 자동 정지 | 손실 한도 초과 시 시스템 자동 정지 |
| 모니터링 | 실시간 리스크 상태 감시 및 알림 |

### 2.5 백테스팅 모듈 (Backtesting Module)

| 항목 | 사양 |
|------|------|
| 데이터 소스 | 데이터베이스 저장 히스토리 데이터 |
| 테스트 기간 | 최소 6개월 ~ 1년 |
| 성과 지표 | 총 수익률, 최대 낙폭, 승률, 손익비 |
| 프레임워크 | Python 기반 (Backtrader, PyAlgoTrade 등) |

### 2.6 웹 대시보드 (Web Dashboard)

| 항목 | 사양 |
|------|------|
| 구성 | 1~2페이지 간단한 웹 UI |
| 기술 스택 | HTML, CSS, JavaScript |
| 시각화 | Chart.js, D3.js 또는 Plotly |
| 데이터 갱신 | 폴링 또는 WebSocket 실시간 업데이트 |

## 3. 데이터 흐름 (Data Flow)

```
[Upbit API]
    ↓ 실시간 데이터 (가격, 거래량, 체결 정보)
[데이터 수집 모듈]
    ↓ 정제된 데이터
[ChatGPT 신호 생성 모듈]
    ↓ 매매 신호 (Buy/Hold/Sell)
[리스크 관리 모듈]
    ↓ 검증된 신호
[주문 실행 모듈]
    ↓ 주문 실행 결과
[데이터베이스]
    ↓ 히스토리 데이터
[백테스팅 모듈] → [전략 평가 결과]
```

## 4. 데이터베이스 스키마 (Database Schema)

### 4.1 market_data (시장 데이터)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | Primary Key |
| timestamp | DATETIME | 데이터 수집 시간 |
| price | DECIMAL | 비트코인 가격 |
| volume | DECIMAL | 거래량 |
| trade_info | JSON | 체결 정보 |

### 4.2 trading_signals (매매 신호)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | Primary Key |
| timestamp | DATETIME | 신호 생성 시간 |
| signal | ENUM | Buy / Hold / Sell |
| confidence | DECIMAL | 신뢰도 점수 |
| raw_response | TEXT | ChatGPT 원본 응답 |

### 4.3 orders (주문 기록)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | Primary Key |
| timestamp | DATETIME | 주문 시간 |
| signal_id | INTEGER | Foreign Key (trading_signals) |
| order_type | ENUM | Buy / Sell |
| amount | DECIMAL | 주문 수량 |
| price | DECIMAL | 주문 가격 |
| status | ENUM | Pending / Executed / Failed |
| executed_price | DECIMAL | 체결 가격 |
| error_message | TEXT | 오류 메시지 (실패 시) |

### 4.4 backtest_results (백테스팅 결과)

| 필드 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | Primary Key |
| run_timestamp | DATETIME | 백테스트 실행 시간 |
| start_date | DATE | 테스트 시작일 |
| end_date | DATE | 테스트 종료일 |
| total_return | DECIMAL | 총 수익률 |
| max_drawdown | DECIMAL | 최대 낙폭 |
| win_rate | DECIMAL | 승률 |
| profit_loss_ratio | DECIMAL | 손익비 |
| total_trades | INTEGER | 총 거래 횟수 |

## 5. API 사양 (API Specifications)

### 5.1 Upbit API 연동

- **인증**: JWT 토큰 기반 인증
- **엔드포인트**:
  - `GET /v1/ticker` - 현재 시세 조회
  - `GET /v1/trades/ticks` - 체결 정보 조회
  - `POST /v1/orders` - 주문 생성
  - `GET /v1/orders` - 주문 조회

### 5.2 ChatGPT API 연동

- **모델**: GPT-4 또는 GPT-3.5-turbo
- **입력 형식**: 정제된 시장 데이터 (JSON)
- **출력 형식**: 구조화된 매매 신호 (JSON)

```json
{
  "signal": "Buy | Hold | Sell",
  "confidence": 0.0 ~ 1.0,
  "reasoning": "분석 근거"
}
```

## 6. 리스크 관리 규칙 (Risk Management Rules)

| 규칙 | 조건 | 동작 |
|------|------|------|
| 포지션 제한 | 전체 자본 대비 1~2% 초과 | 주문 거부 |
| 개별 손절 | 3~5% 손실 | 자동 청산 |
| 일일 손실 한도 | 설정값 초과 | 시스템 일시 정지 |
| 변동성 감지 | 급격한 가격 변동 | 추가 안전장치 발동 |

## 7. 성능 요구사항 (Performance Requirements)

| 항목 | 요구사항 |
|------|----------|
| 데이터 수집 지연 | < 100ms |
| 신호 생성 지연 | < 5초 (ChatGPT API 응답 포함) |
| 주문 실행 지연 | < 500ms |
| 시스템 가용성 | 99.5% 이상 |
| 동시 처리 | 초당 10건 이상 데이터 처리 |

## 8. 보안 요구사항 (Security Requirements)

- API 키는 환경 변수 또는 암호화된 설정 파일에 저장
- HTTPS 통신 필수
- 주문 실행 전 이중 검증 로직
- 로그 데이터 민감 정보 마스킹
- 접근 권한 최소화 원칙 적용

## 9. 로깅 및 모니터링 (Logging & Monitoring)

### 9.1 로그 레벨

| 레벨 | 용도 |
|------|------|
| DEBUG | 개발 및 디버깅용 상세 정보 |
| INFO | 일반 운영 정보 |
| WARNING | 주의가 필요한 상황 |
| ERROR | 오류 발생 |
| CRITICAL | 시스템 중단 수준 오류 |

### 9.2 모니터링 항목

- API 응답 시간
- 주문 성공/실패율
- 시스템 리소스 사용량
- 리스크 이벤트 발생 빈도

## 10. 배포 환경 (Deployment Environment)

| 항목 | 사양 |
|------|------|
| 런타임 | Python 3.10+ |
| 데이터베이스 | SQLite (개발) / PostgreSQL (운영) |
| 스케줄러 | APScheduler 또는 Celery |
| 웹 서버 | Flask 또는 FastAPI |
| 컨테이너 | Docker (선택사항) |

## 11. 기술 스택 및 라이브러리 (Tech Stack & Libraries)

> **Note**: Context7 MCP를 활용하여 각 라이브러리의 최신 문서를 참조합니다.
> Claude Code에서 `resolve-library-id` → `get-library-docs` 도구를 사용하여 최신 API 문서를 조회할 수 있습니다.

### 11.1 핵심 라이브러리

| 카테고리 | 라이브러리 | Context7 ID | 용도 |
|----------|------------|-------------|------|
| HTTP 클라이언트 | httpx | `/pypi/httpx` | Upbit API 비동기 통신 |
| 비동기 처리 | asyncio | (Python 내장) | 비동기 데이터 수집 |
| 데이터 처리 | pandas | `/pypi/pandas` | 시계열 데이터 분석 |
| AI API | openai | `/pypi/openai` | ChatGPT API 연동 |
| 웹 프레임워크 | FastAPI | `/pypi/fastapi` | REST API 서버 |
| ORM | SQLAlchemy | `/pypi/sqlalchemy` | 데이터베이스 ORM |
| 백테스팅 | backtrader | `/pypi/backtrader` | 전략 시뮬레이션 |
| 시각화 | plotly | `/pypi/plotly` | 차트 생성 |

### 11.2 보조 라이브러리

| 카테고리 | 라이브러리 | Context7 ID | 용도 |
|----------|------------|-------------|------|
| 환경 변수 | python-dotenv | `/pypi/python-dotenv` | 설정 관리 |
| 유효성 검사 | pydantic | `/pypi/pydantic` | 데이터 검증 |
| 스케줄링 | APScheduler | `/pypi/apscheduler` | 작업 스케줄링 |
| 로깅 | loguru | `/pypi/loguru` | 구조화된 로깅 |
| 테스트 | pytest | `/pypi/pytest` | 단위 테스트 |
| WebSocket | websockets | `/pypi/websockets` | 실시간 데이터 수신 |

### 11.3 Context7 MCP 활용 가이드

Context7 MCP 서버가 `~/.claude/settings.json`에 등록되어 있습니다.

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

**사용 방법:**

1. **라이브러리 검색**: `resolve-library-id` 도구로 라이브러리 ID 조회
   ```
   예: "fastapi" → /pypi/fastapi
   ```

2. **문서 조회**: `get-library-docs` 도구로 최신 문서 가져오기
   ```
   예: get-library-docs("/pypi/fastapi", topic="routing")
   ```

3. **버전별 문서**: 특정 버전의 문서도 조회 가능

**활용 시나리오:**
- 새로운 API 엔드포인트 구현 시 FastAPI 최신 문서 참조
- OpenAI API 변경사항 확인
- SQLAlchemy 쿼리 문법 확인
- 백테스팅 전략 구현 시 Backtrader 예제 참조
