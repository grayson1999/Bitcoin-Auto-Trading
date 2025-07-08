
## 1. `api.py`

Upbit API와의 통신을 담당

| 함수                                             | 설명                                                           | 파라미터                                                                   | 반환                       |
| ---------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------- | ------------------------ |
| `fetch_ticker(market, retries=3, backoff=1.0)` | 지정된 마켓의 공용 티커(가격·거래량 등) 데이터를 REST API로 조회하고, 실패 시 지수 백오프 재시도 | `market`: 문자열 (예: `"KRW-BTC"`)  <br>`retries`: int<br>`backoff`: float | dict (원시 JSON) 또는 `None` |
| `fetch_accounts()`                             | JWT 인증을 통해 사용자 계좌 정보를 조회                                     | 없음                                                                     | list of dict 또는 `None`   |

---

## 2. `parser.py`

API로부터 받아온 원시 데이터를 DB 저장용으로 **정제**

| 함수                                              | 설명                                    | 파라미터                                                            | 반환                       |
| ----------------------------------------------- | ------------------------------------- | --------------------------------------------------------------- | ------------------------ |
| `parse_ticker(raw: dict)`                       | 원시 티커 JSON에서 필요한 필드만 추출하여 딕셔너리로 반환    | `raw`: UpbitAPI.fetch\_ticker 반환 dict                           | dict (refined) 또는 `None` |
| `parse_account(raw_list: list, currency="BTC")` | 원시 계좌 리스트에서 특정 화폐(기본 BTC) 항목만 추출 후 정제 | `raw_list`: UpbitAPI.fetch\_accounts 반환 list<br>`currency`: 문자열 | dict (refined) 또는 `None` |

---

## 3. `db.py`

SQLAlchemy 기반 DB 스키마 정의 및 **저장 로직**

| 클래스 / 함수                  | 설명                                                                                    |
| ------------------------- | ------------------------------------------------------------------------------------- |
| `TickData`                | 실시간 시장 데이터(`tick_data` 테이블) 모델<br>– `market`, `trade_price`, `data_timestamp` 등 컬럼 정의 |
| `AccountData`             | 계좌 정보(`account_data` 테이블) 모델<br>– `currency`, `balance`, `avg_buy_price` 등 컬럼 정의      |
| `init_db()`               | 정의된 모든 테이블을 한 번에 생성                                                                   |
| `save(session, instance)` | 전달된 모델 인스턴스를 DB에 저장하고 커밋                                                              |

---

## 4. `controller.py`

스케줄러를 이용해 **주기적 수집→파싱→저장**을 수행

| 함수                         | 설명                                                                                     |
| -------------------------- | -------------------------------------------------------------------------------------- |
| `fetch_and_store_ticker()` | 1) `UpbitAPI.fetch_ticker` 호출<br>2) `parse_ticker`로 정제<br>3) `TickData` 인스턴스 생성 후 저장   |
| `main()`                   | 1) `init_db()`로 테이블 생성<br>2) `BackgroundScheduler`에 15분 간격 잡업 등록<br>3) 스케줄러 시작 및 종료 제어 |

---

### 전체 흐름 요약

1. **API 통신**(`api.py`) →
2. **데이터 정제**(`parser.py`) →
3. **DB 저장**(`db.py`) →
4. **스케줄링 제어**(`controller.py`)

