"""
불변 상수 정의

애플리케이션 전반에서 사용되는 하드코딩된 상수값을 정의합니다.
환경변수나 DB로 변경할 수 없는 고정값입니다.
"""

# === 애플리케이션 정보 ===
APP_VERSION = "0.1.0"
APP_NAME = "Bitcoin Auto-Trading API"

# === 데이터베이스 풀 설정 ===
DB_POOL_SIZE = 5  # 기본 풀 크기 (동시 연결 수)
DB_POOL_MAX_OVERFLOW = 10  # 풀 초과 시 추가 허용 연결 수 (최대 15개)

# === 거래소 제한 ===
UPBIT_FEE_RATE = 0.0005  # 거래 수수료 (0.05%)
UPBIT_MIN_ORDER_KRW = 5000  # 최소 주문 금액 (원)
UPBIT_RATE_LIMIT_ORDER = 10  # 초당 주문 요청 제한
UPBIT_RATE_LIMIT_QUERY = 30  # 초당 조회 요청 제한

# === 재시도 설정 ===
DEFAULT_MAX_RETRIES = 3  # 기본 재시도 횟수
DEFAULT_RETRY_DELAY_SECONDS = 2  # 기본 재시도 대기 시간
DEFAULT_TIMEOUT_SECONDS = 30  # 기본 타임아웃

# === 로깅 설정 ===
LOG_ROTATION_SIZE = "10MB"  # 로그 로테이션 크기
LOG_RETENTION_DAYS = 7  # 로그 보관 일수
LOG_RETENTION_PERIOD = "1 week"  # loguru 형식

# === AI 모델 비용 (USD per 1M tokens) ===
AI_MODEL_COSTS = {
    "gemini-2.5-pro": {"input": 1.25, "output": 10.0},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
}

# === 스케줄러 기본 주기 ===
DATA_COLLECTION_INTERVAL_SECONDS = 10  # 시세 수집 간격
DATA_CLEANUP_INTERVAL_HOURS = 24  # 데이터 정리 주기
VOLATILITY_CHECK_INTERVAL_SECONDS = 30  # 변동성 체크 주기 (초)
SIGNAL_PERFORMANCE_EVAL_HOURS = 4  # 신호 성과 평가 주기 (시간)
PENDING_ORDER_SYNC_MINUTES = 5  # PENDING 주문 동기화 주기 (분)

# === HTTP 상태 코드 ===
HTTP_STATUS_OK = 200
HTTP_STATUS_CREATED = 201
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_RATE_LIMIT = 429
HTTP_STATUS_INTERNAL_SERVER_ERROR = 500
HTTP_STATUS_SERVICE_UNAVAILABLE = 503

# === API 페이지네이션 ===
API_PAGINATION_MIN_LIMIT = 1  # 최소 조회 개수
API_PAGINATION_MAX_LIMIT = 100  # 최대 조회 개수
API_PAGINATION_DEFAULT_LIMIT = 50  # 기본 조회 개수

# === 시장 데이터 조회 ===
MARKET_MIN_HOURS = 1  # 최소 조회 시간 (시간)
MARKET_MAX_HOURS = 168  # 최대 조회 시간 (7일 = 168시간)
MARKET_DEFAULT_HOURS = 24  # 기본 조회 시간
MARKET_MAX_LIMIT_HISTORY = 1000  # 히스토리 최대 레코드 수
MARKET_DEFAULT_LIMIT_HISTORY = 100  # 히스토리 기본 레코드 수
MARKET_MAX_LIMIT_LATEST = 100  # 최신 데이터 최대 레코드 수
MARKET_DEFAULT_LIMIT_LATEST = 10  # 최신 데이터 기본 레코드 수
MS_TO_SECONDS = 1000  # 밀리초 → 초 변환 상수

# === 신호 생성 설정 ===
SIGNAL_MARKET_DATA_HOURS = 168  # 분석에 사용할 시장 데이터 기간 (7일)
SIGNAL_COOLDOWN_MINUTES = 5  # 수동 신호 생성 쿨다운 (분)
SIGNAL_MIN_CONFIDENCE = 0.0  # 최소 신뢰도
SIGNAL_MAX_CONFIDENCE = 1.0  # 최대 신뢰도
SIGNAL_DEFAULT_CONFIDENCE = 0.5  # 기본 신뢰도 (파싱 실패 시)

# === 주문 실행 설정 ===
ORDER_POLL_INTERVAL_SECONDS = 1.0  # 주문 체결 확인 간격 (초)
ORDER_POLL_MAX_ATTEMPTS = 30  # 주문 체결 확인 최대 시도 횟수
ORDER_MAX_RETRIES = 3  # 주문 재시도 횟수
ORDER_RETRY_DELAY_SECONDS = 1.0  # 주문 재시도 대기 시간 (초)

# === 리스크 관리 설정 ===
RISK_WARNING_THRESHOLD_RATIO = 0.8  # 경고 발생 임계값 비율 (80%)

# === 데이터 보관 설정 ===
DATA_RETENTION_DAYS = 365  # 시장 데이터 보관 기간 (일)

# === 에러 메시지 ===
ERROR_INTERNAL_SERVER = "서버 내부 오류가 발생했습니다"
ERROR_UNAUTHORIZED = "인증이 필요합니다"
ERROR_NOT_FOUND = "요청한 리소스를 찾을 수 없습니다"
