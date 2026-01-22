"""
날짜/시간 유틸리티

Python 3.10 호환성을 위한 UTC 상수 및 유틸리티 함수.
"""

from datetime import UTC

# Python 3.10 호환: datetime.UTC 대신 timezone.utc 사용
UTC = UTC

__all__ = ["UTC"]
