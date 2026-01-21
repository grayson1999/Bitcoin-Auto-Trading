"""
Common constants for all clients

Shared constants used across Upbit, AI, Slack, and Auth clients.
"""

# === Retry settings ===
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds (base delay, may be multiplied for backoff)

# === Timeout settings ===
DEFAULT_TIMEOUT = 30.0  # seconds

# === HTTP status codes ===
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_RATE_LIMIT = 429
HTTP_SERVICE_UNAVAILABLE = 503
