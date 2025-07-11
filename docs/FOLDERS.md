# 폴더 구조 계획

이 문서는 프로젝트의 소스 코드와 관련 문서를 구성하는 기본 폴더 구조에 대한 개요를 제공합니다. 1인 개발 환경에서 부담 없이 관리할 수 있도록 최소한의 정보를 포함합니다.

## 최상위 폴더 구조

- **docs/**  
  - **목적:** 프로젝트 개요, 아키텍처, 요구사항 분석, DB 전략, 진행 일정 등 각종 문서를 저장  
  - **예시 파일:** `PROJECT_OVERVIEW.md`, `ARCHITECTURE.md`, `REQUIREMENTS.md`, `DB_STRATEGY.md`, `TIMELINE.md`

- **src/**  
  - **목적:** 실제 소스 코드가 포함되는 폴더  
  - **구성:**  
    - `src/trading/` : 실시간 트레이딩 엔진 관련 모듈  
      - `data_collection/`   : Upbit API 기반 실시간 데이터 수집 및 아카이빙  
      - `signal_generation/` : ChatGPT API 기반 매매 신호 생성  
      - `order_execution/`   : Upbit API 기반 주문 실행  
      - `risk_management/`   : 포지션 사이징, 손절/익절 로직 등 리스크 관리  
    - `src/database/`        : DB 연결, 세션 관리, 모델 정의  
    - `src/utils/`           : 로깅, 유틸리티 함수 등 공통 기능  
    - `src/backtesting/`     : 백테스팅 및 전략 평가 관련 코드  
    - `src/web/`             : 웹 대시보드 구현 (HTML, CSS, JavaScript 파일)  

- **config/**  
  - **목적:** API 키, 환경 변수 등 설정 파일을 별도로 관리하여 코드와 분리

- **data/**  
  - **목적:** 예제 데이터, 백테스팅 데이터 등 프로젝트에 사용되는 데이터 파일들을 보관

- **logs/**  
  - **목적:** 실행 중 발생하는 로그 파일들을 저장하여 디버깅 및 모니터링에 활용

## 각 폴더의 역할 요약

- **docs/**: 프로젝트 관련 모든 문서를 한 곳에 모아둡니다.  
- **src/**: 주요 기능별로 모듈을 구분하여 코드가 작성됩니다.  
- **config/**: API 키와 같은 민감한 설정 정보를 관리합니다.  
- **data/**: 개발 및 테스트에 사용되는 데이터 파일을 보관합니다.  
- **logs/**: 시스템 실행 및 오류 로그를 저장하여 문제 발생 시 참고합니다.

## 변경 사항 추적 및 유지 관리

- **버전 관리:**  
  - Git을 통해 폴더 구조 및 파일 변경 내역을 추적합니다.
- **서브 폴더 README:**  
  - 필요 시 각 서브 폴더(`src/realtime`, `src/backtesting`, `src/web` 등)에 간단한 README 파일을 추가하여 해당 폴더의 역할과 사용 방법을 설명합니다.


# src 폴더 구조

```
src/
  ├── trading/
  │     ├── data_collection/       # Upbit API 연동, 데이터 수집, 파싱, 오류 처리 등 실시간 데이터 처리 및 아카이빙 모듈
  │     ├── signal_generation.py     # 정제 데이터를 기반으로 ChatGPT API를 호출해 매매 신호 생성
  │     ├── risk_management.py       # 포지션 사이징, 손절, 자동 정지 등 리스크 관리 로직 구현
  │     └── order_execution.py       # 생성된 신호에 따라 Upbit API로 주문 실행 및 결과 피드백 처리
  │
  ├── database/
  │     ├── base.py                # SQLAlchemy Declarative Base 정의
  │     ├── models.py              # DB 테이블 모델 정의 (TickData, AccountData, FiveMinOHLCV 등)
  │     └── session.py             # DB 연결 엔진 및 세션 관리
  │
  ├── utils/
  │     └── logger.py              # 로깅 설정 및 유틸리티 함수
  │
  ├── backtesting/
  │     └── backtesting_module.py    # 히스토리 데이터를 활용한 전략 시뮬레이션 및 평가, 백테스팅 결과 산출
  │
  └── web/
        ├── dashboard.html         # 웹 대시보드 UI (HTML)
        ├── dashboard.js           # 대시보드 인터랙션 및 실시간 데이터 표시 로직 (JavaScript)
        └── dashboard.css          # 대시보드 스타일 정의 (CSS)
```

## 각 서브폴더 역할

- **realtime/**  
  - **data_collection.py:** Upbit API를 통해 실시간 데이터를 받아오고, 오류 처리 및 재시도 로직을 포함한 데이터 수집 기능을 담당합니다.  
  - **signal_generation.py:** 수집된 정제 데이터를 이용하여 ChatGPT API를 호출하고, 매매 신호(Buy, Hold, Sell)를 생성합니다.  
  - **risk_management.py:** 생성된 신호를 바탕으로 포지션 사이징, 손절 기준 설정 및 자동 정지 로직을 구현하여 리스크를 관리합니다.  
  - **order_execution.py:** 리스크 관리 모듈을 통과한 신호를 바탕으로 실제 주문을 실행하고, 주문 결과(체결 정보, 오류 메시지)를 처리합니다.

- **backtesting/**  
  - **backtesting_module.py:** 히스토리 데이터를 활용해 전략의 백테스팅을 수행하고, 수익률, 최대 낙폭 등 성과 지표를 산출하여 전략 평가에 활용합니다.

- **web/**  
  - **dashboard.html:** 실시간 데이터 및 백테스팅 결과를 시각화하기 위한 웹 대시보드의 기본 HTML 구조를 제공합니다.  
  - **dashboard.js:** 웹 대시보드에서 실시간 데이터 업데이트, 사용자 인터랙션 처리 등을 위한 JavaScript 코드가 포함됩니다.  
  - **dashboard.css:** 대시보드의 스타일과 레이아웃을 정의합니다.

