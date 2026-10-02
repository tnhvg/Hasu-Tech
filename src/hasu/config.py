"""Đường dẫn dùng chung cho toàn dự án."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DB_PATH = DATA_PROCESSED / "hasu.duckdb"
SQL_DIR = ROOT / "sql"
DOCS_DIR = ROOT / "docs"
