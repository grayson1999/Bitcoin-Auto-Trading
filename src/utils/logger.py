# src/utils/logger.py

import logging
import os
from pathlib import Path

def get_logger(
    name: str,
    log_file: str = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    주어진 이름과 파일명을 사용해 Logger를 생성합니다.
    :param name: Logger 이름 (e.g. "realtime.data_collection")
    :param log_file: 로그 파일명 (없으면 env의 LOG_FILE 또는 "app.log" 사용)
    :param level: 로깅 레벨
    :return: 설정된 Logger 인스턴스
    """
    # 로그 디렉터리 준비
    log_dir = Path(__file__).resolve().parents[2] / "logs"
    log_dir.mkdir(exist_ok=True)

    # 파일명 결정: 인자 > env > default
    if log_file is None:
        log_file = os.getenv("LOG_FILE", "app.log")
    log_path = log_dir / log_file

    # Formatter
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # FileHandler
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)

    # StreamHandler
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)

    # Logger 생성
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # 핸들러 중복 방지
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(sh)
    logger.propagate = False
    return logger
