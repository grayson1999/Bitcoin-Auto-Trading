# tests/conftest.py

import sys
from pathlib import Path
import os
from pathlib import Path
from dotenv import load_dotenv

# ─────────── 프로젝트 구조 가정 ───────────
# Bitcoin-Auto-Trading/
# ├── src/
# │   └── trading/
# │       └── data_collection/
# └── tests/
#     └── test_api.py
# ──────────────────────────────────────────

# 프로젝트 루트 경로
ROOT = Path(__file__).parent.parent

# src 디렉터리를 최상단에 추가 (PYTHONPATH)
sys.path.insert(0, str(ROOT))


root = Path(__file__).resolve().parents[1]
load_dotenv(root / "config" / ".env")