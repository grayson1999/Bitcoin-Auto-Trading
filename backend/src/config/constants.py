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

# === HTTP 상태 코드 ===
HTTP_STATUS_OK = 200
HTTP_STATUS_CREATED = 201
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_INTERNAL_SERVER_ERROR = 500

# === 에러 메시지 ===
ERROR_INTERNAL_SERVER = "서버 내부 오류가 발생했습니다"
ERROR_UNAUTHORIZED = "인증이 필요합니다"
ERROR_NOT_FOUND = "요청한 리소스를 찾을 수 없습니다"
