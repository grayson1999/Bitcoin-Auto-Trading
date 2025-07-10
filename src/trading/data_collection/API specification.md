## 1. API Layer (`api.py`)

업비트 서버와의 통신만 담당하는 계층입니다.

| 함수                                             | 설명                                       | 파라미터                                                                 | 반환                         |
| ---------------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------- | -------------------------- |
| `fetch_ticker(market, retries=3, backoff=1.0)` | 지정 마켓의 티커(가격·거래량 등)를 조회, 실패 시 지수 백오프 재시도 | `market`: 문자열 (예: `"KRW-BTC"`)<br>`retries`: int<br>`backoff`: float | `dict` (원시 JSON) 또는 `None` |
| `fetch_accounts()`                             | JWT 인증 헤더를 생성해 비공개 계좌 정보를 조회             | 없음                                                                   | `list[dict]` 또는 `None`     |

---

## 2. Parsing Layer (`parser.py`)

API에서 받은 원시 JSON을 DB 저장용 필드로 **정제**하는 계층입니다.

| 함수                                              | 설명                                  | 파라미터                                                    | 반환                          |
| ----------------------------------------------- | ----------------------------------- | ------------------------------------------------------- | --------------------------- |
| `parse_ticker(raw: dict)`                       | 티커 원시 JSON에서 필요한 필드만 추출             | `raw`: `fetch_ticker` 반환 dict                           | `dict` (DB 필드 매핑) 또는 `None` |
| `parse_account(raw_list: list, currency="BTC")` | 계좌 원시 리스트에서 특정 화폐(기본 BTC) 정보만 골라 반환 | `raw_list`: `fetch_accounts` 반환 list<br>`currency`: 문자열 | `dict` (DB 필드 매핑) 또는 `None` |

---

## 3. Service Layer (`service.py`)

비즈니스 로직(수집 → 정제 → 저장)을 한곳에 모아둔 계층입니다.

| 메서드                         | 설명                                                                                    |
| --------------------------- | ------------------------------------------------------------------------------------- |
| `collect_ticker(market)`    | 1) `fetch_ticker` 호출 → 2) `parse_ticker`로 정제 → 3) `TickData` 모델 인스턴스 생성 및 DB 저장       |
| `collect_account(currency)` | 1) `fetch_accounts` 호출 → 2) `parse_account`로 정제 → 3) `AccountData` 모델 인스턴스 생성 및 DB 저장 |

---

## 4. Orchestration Layer (`controller.py`)

스케줄러를 이용해 Service 계층의 메서드를 주기적으로 실행하도록 제어합니다.

| 함수                         | 설명                                                                                                      |
| -------------------------- | ------------------------------------------------------------------------------------------------------- |
| `fetch_and_store_ticker()` | `DataCollectionService.collect_ticker` 호출 (Controller 내 래핑)                                             |
| `main()`                   | 1) `init_db()` 호출(테이블 생성)<br>2) `BackgroundScheduler`에 Service 메서드 잡업 등록(15분·1시간 등)<br>3) 스케줄러 시작·종료 제어 |

---

### 전체 데이터 흐름

1. **API 호출** (`api.py`) →
2. **데이터 정제** (`parser.py`) →
3. **비즈니스 로직 실행** (`service.py`) →
4. **스케줄러 제어** (`controller.py`)


