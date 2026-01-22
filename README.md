# Bitcoin Auto-Trading System

비트코인 자동 거래 시스템 - Gemini AI 기반 매매 신호 생성 및 Upbit 자동 거래

## 시스템 구성

- **Backend**: FastAPI + SQLAlchemy + APScheduler
- **Frontend**: React + Vite + TailwindCSS
- **Database**: PostgreSQL
- **AI**: Google Gemini 2.5 Flash
- **거래소**: Upbit

## 서버 관리

### Backend 서비스 관리

```bash
# 상태 확인
sudo systemctl status bitcoin-trading-backend

# 시작
sudo systemctl start bitcoin-trading-backend

# 중지
sudo systemctl stop bitcoin-trading-backend

# 재시작
sudo systemctl restart bitcoin-trading-backend

# 부팅 시 자동 시작 활성화
sudo systemctl enable bitcoin-trading-backend

# 부팅 시 자동 시작 비활성화
sudo systemctl disable bitcoin-trading-backend
```

### 로그 확인

```bash
# 실시간 로그 보기
sudo journalctl -u bitcoin-trading-backend -f

# 최근 100줄 로그
sudo journalctl -u bitcoin-trading-backend -n 100

# 오늘 로그만 보기
sudo journalctl -u bitcoin-trading-backend --since today

# 오류 로그만 보기
sudo journalctl -u bitcoin-trading-backend -p err
```

### Nginx 관리

```bash
# 상태 확인
sudo systemctl status nginx

# 재시작
sudo systemctl restart nginx

# 설정 테스트
sudo nginx -t

# 설정 리로드 (무중단)
sudo systemctl reload nginx
```

### 데이터베이스 마이그레이션

```bash
cd /home/ubuntu/Bitcoin-Auto-Trading/backend
source .venv/bin/activate

# 현재 마이그레이션 상태 확인
alembic current

# 마이그레이션 히스토리 보기
alembic history

# 최신 마이그레이션 적용
alembic upgrade head

# 한 단계 롤백
alembic downgrade -1
```

## 개발 환경

### Backend 개발 서버

```bash
cd /home/ubuntu/Bitcoin-Auto-Trading/backend
source .venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

### Frontend 개발 서버

```bash
cd /home/ubuntu/Bitcoin-Auto-Trading/frontend
npm run dev
```

### Frontend 빌드 (프로덕션)

```bash
cd /home/ubuntu/Bitcoin-Auto-Trading/frontend
npm run build
# 빌드 결과: /home/ubuntu/Bitcoin-Auto-Trading/frontend/dist
```

## API 엔드포인트

| 경로 | 설명 |
|------|------|
| `GET /api/v1/health` | 서버 상태 확인 |
| `GET /api/v1/dashboard/summary` | 대시보드 요약 |
| `GET /api/v1/signals` | AI 신호 목록 |
| `POST /api/v1/signals/generate` | AI 신호 수동 생성 |
| `GET /api/v1/trading/orders` | 주문 내역 |
| `GET /api/v1/risk/status` | 리스크 상태 |
| `POST /api/v1/backtest/run` | 백테스트 실행 |
| `GET /api/v1/backtest/results` | 백테스트 결과 목록 |

## 디렉토리 구조

```
Bitcoin-Auto-Trading/
├── backend/
│   ├── src/
│   │   ├── main.py           # FastAPI 앱
│   │   ├── config.py         # 설정
│   │   ├── database.py       # DB 연결
│   │   ├── models/           # SQLAlchemy 모델
│   │   ├── services/         # 비즈니스 로직
│   │   ├── api/              # API 엔드포인트
│   │   └── scheduler/        # 스케줄러 작업
│   ├── alembic/              # DB 마이그레이션
│   ├── .venv/                # Python 가상환경
│   └── .env                  # 환경 변수
├── frontend/
│   ├── src/
│   │   ├── pages/            # 페이지 컴포넌트
│   │   ├── components/       # 재사용 컴포넌트
│   │   ├── hooks/            # React 훅
│   │   └── api/              # API 클라이언트
│   └── dist/                 # 빌드 결과물
└── specs/                    # 설계 문서
```

## 환경 변수

Backend `.env` 파일 위치: `/home/ubuntu/Bitcoin-Auto-Trading/backend/.env`

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/bitcoin
UPBIT_ACCESS_KEY=your-access-key
UPBIT_SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

## 문제 해결

### Backend가 시작되지 않을 때

```bash
# 로그 확인
sudo journalctl -u bitcoin-trading-backend -n 50

# 포트 사용 중인지 확인
sudo lsof -i :8000

# 수동으로 실행해서 에러 확인
cd /home/ubuntu/Bitcoin-Auto-Trading/backend
source .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 데이터베이스 연결 오류

```bash
# PostgreSQL 상태 확인
sudo systemctl status postgresql

# PostgreSQL 재시작
sudo systemctl restart postgresql
```

### Frontend 변경사항이 반영되지 않을 때

```bash
# 프론트엔드 재빌드
cd /home/ubuntu/Bitcoin-Auto-Trading/frontend
npm run build

# Nginx 캐시 무효화 (브라우저에서 Ctrl+Shift+R)
```
