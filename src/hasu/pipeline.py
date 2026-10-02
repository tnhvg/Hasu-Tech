"""Chạy toàn bộ luồng xử lý dữ liệu từ đầu.

    python -m hasu.pipeline

Các bước:
  1. Nạp mọi file .xlsx trong data/raw vào bảng raw_sales_lines.
  2. Chạy lần lượt các file SQL trong sql/staging (theo thứ tự tên file).
  3. Ghi báo cáo chất lượng dữ liệu ra docs/data_quality_report.md.
"""

from __future__ import annotations

import duckdb

from hasu.config import DATA_PROCESSED, DATA_RAW, DB_PATH, DOCS_DIR, SQL_DIR
from hasu.ingest import load_raw
from hasu.quality import build_report

SQL_LAYERS = ["staging"]


def run_sql_layer(con: duckdb.DuckDBPyConnection, layer: str) -> None:
    for sql_file in sorted((SQL_DIR / layer).glob("*.sql")):
        print(f"  chạy {layer}/{sql_file.name}")
        con.execute(sql_file.read_text(encoding="utf-8"))


def main() -> None:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    files = sorted(DATA_RAW.glob("*.xlsx"))
    if not files:
        raise SystemExit(f"Không tìm thấy file .xlsx nào trong {DATA_RAW}")

    with duckdb.connect(str(DB_PATH)) as con:
        print("1. Nạp dữ liệu raw")
        for f in files:
            print(f"  {f.name}: {load_raw(con, f):,} dòng")

        print("2. Làm sạch và tổng hợp")
        for layer in SQL_LAYERS:
            run_sql_layer(con, layer)

        print("3. Báo cáo chất lượng dữ liệu")
        report_path = DOCS_DIR / "data_quality_report.md"
        report_path.write_text(build_report(con), encoding="utf-8")
        print(f"  đã ghi {report_path.relative_to(DOCS_DIR.parent)}")


if __name__ == "__main__":
    main()
