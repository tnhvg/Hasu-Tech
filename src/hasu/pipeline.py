"""Chạy toàn bộ luồng xử lý dữ liệu từ đầu.

    python -m hasu.pipeline

Các bước:
  1. Nạp mọi file .xlsx trong data/raw vào bảng raw_sales_lines.
  2. Chạy lần lượt các file SQL trong sql/staging (theo thứ tự tên file).
  3. Chạy các phân tích cần Python (giỏ hàng, nghi ngờ hết hàng).
  4. Ghi báo cáo chất lượng dữ liệu ra docs/data_quality_report.md.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from hasu.analysis import build_analysis_tables
from hasu.config import DATA_PROCESSED, DATA_RAW, DB_PATH, DOCS_DIR, SQL_DIR
from hasu.ingest import load_raw
from hasu.quality import build_report

SQL_LAYERS = ["staging", "marts"]


def run_sql_layer(con: duckdb.DuckDBPyConnection, layer: str) -> None:
    for sql_file in sorted((SQL_DIR / layer).glob("*.sql")):
        con.execute(sql_file.read_text(encoding="utf-8"))


def build_database(con: duckdb.DuckDBPyConnection, files: list[Path], log=print) -> str:
    """Nạp các file vào bảng raw (cộng dồn, không nhân đôi), rồi dựng lại staging, mart
    và các bảng phân tích. Trả về báo cáo chất lượng dữ liệu (markdown)."""
    log("1. Nạp dữ liệu raw")
    for f in files:
        log(f"  {f.name}: {load_raw(con, f):,} dòng")

    log("2. Làm sạch và tổng hợp")
    for layer in SQL_LAYERS:
        run_sql_layer(con, layer)

    log("3. Phân tích giỏ hàng, nghi ngờ hết hàng")
    build_analysis_tables(con)

    log("4. Báo cáo chất lượng dữ liệu")
    return build_report(con)


def main() -> None:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    files = sorted(DATA_RAW.glob("*.xlsx"))
    if not files:
        raise SystemExit(f"Không tìm thấy file .xlsx nào trong {DATA_RAW}")

    with duckdb.connect(str(DB_PATH)) as con:
        report = build_database(con, files)
    report_path = DOCS_DIR / "data_quality_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"  đã ghi {report_path.relative_to(DOCS_DIR.parent)}")


if __name__ == "__main__":
    main()
