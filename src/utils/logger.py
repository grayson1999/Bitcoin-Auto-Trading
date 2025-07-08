# utils/logger.py

import os
import logging
from logging import Logger
from logging.handlers import TimedRotatingFileHandler

def get_logger(
    name: str,
    log_file: str = "app.log",       # 로그 파일명 (logs/ 디렉터리에 생성)
    level: int = logging.INFO,       # 로그 레벨 설정 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    when: str = "midnight",          # 롤링 기준 시점 ('midnight': 매일 자정, 'H': 매시간 등)
    interval: int = 1,               # 롤링 간격 (when 단위 기준으로 몇 개 간격)
    backup_count: int = 30,          # 보관할 롤링 로그 파일 개수 (초과 시 오래된 파일 자동 삭제)
) -> Logger:
    """
    이름(name)의 로거를 생성해 반환.
    - log_file: logs/ 디렉터리에 저장될 파일명
    - level: 로깅 레벨 설정
    - when: 로그 분할 기준 (시간 단위)
    - interval: 분할 주기
    - backup_count: 보관할 파일 개수
    """
    # logs 폴더가 없으면 생성
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    # 로거 인스턴스 생성 및 레벨 설정
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # 부모 로거로 전파 방지 (중복 출력 방지)

    # 1) 파일 핸들러: 일별 롤링 설정
    file_handler = TimedRotatingFileHandler(
        filename=log_path,
        when=when,
        interval=interval,
        backupCount=backup_count,
        encoding="utf-8",
    )
    # 로그 포맷: 시간 [레벨] 로거이름: 메시지
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    # 2) 콘솔 핸들러: 터미널 출력용
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    return logger
