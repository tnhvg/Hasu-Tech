"""Tầng raw: đọc file xuất từ KiotViet và nạp vào DuckDB.

Nguyên tắc: ở tầng này chỉ đổi tên cột sang tiếng Anh không dấu, KHÔNG sửa
giá trị nào. Mọi quy tắc làm sạch nằm trong sql/staging để có thể xem lại
và chạy lại từ đầu.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd

# Từ điển ánh xạ: tên cột trong file KiotViet "Báo cáo bán hàng theo lợi nhuận"
# -> tên cột chuẩn. Khoá đã được chuẩn hoá bằng normalize_header().
# Có 3 mức chi tiết (grain) khác nhau trong cùng một file:
#   month_*   : tổng của cả tháng, lặp lại trên mọi dòng của tháng đó
#   invoice_* : tổng của cả hoá đơn, lặp lại trên mọi dòng của hoá đơn đó
#   còn lại   : riêng cho từng dòng sản phẩm
COLUMN_MAP = {
    "thời gian": "period_month",
    "tổng tiền hàng (theo thời gian)": "month_gross_amount",
    "giảm giá (theo thời gian)": "month_discount",
    "doanh thu (theo thời gian)": "month_revenue",
    "tổng giá vốn (theo thời gian)": "month_cogs",
    "lợi nhuận gộp (theo thời gian)": "month_gross_profit",
    "mã giao dịch": "invoice_id",
    "chi nhánh": "branch",
    "người bán": "seller",
    "ghi chú": "note",
    "thời gian (theo giao dịch)": "sold_at",
    "tổng tiền hàng (theo giao dịch)": "invoice_gross_amount",
    "giảm giá (theo giao dịch)": "invoice_discount",
    "doanh thu (theo giao dịch)": "invoice_revenue",
    "tổng giá vốn (theo giao dịch)": "invoice_cogs",
    "lợi nhuận gộp (theo giao dịch)": "invoice_gross_profit",
    "mã hàng": "sku",
    "mã vạch": "barcode",
    "tên hàng": "product_name",
    "thương hiệu": "brand",
    "nhóm hàng(3 cấp)": "category_path",
    "sl": "quantity",
    "giá bán/sp": "unit_price",
    "giá vốn/sp": "unit_cost",
    "lợi nhuận/sp": "unit_profit",
    "tổng lợi nhuận hàng hóa": "line_profit",
}

# Các cột mã phải đọc dưới dạng chữ để không mất số 0 ở đầu (vd "02000758").
TEXT_COLUMNS = ["Mã giao dịch", "Mã hàng", "Mã vạch"]

# Kiểu dữ liệu của từng cột chuẩn. Ép kiểu tường minh thay vì để pandas tự đoán:
# một cột toàn ô trống (vd thương hiệu) sẽ bị đoán sai thành kiểu số.
STRING_FIELDS = [
    "period_month", "invoice_id", "branch", "seller", "note",
    "sku", "barcode", "product_name", "brand", "category_path",
]
DATETIME_FIELDS = ["sold_at"]

RAW_TABLE = "raw_sales_lines"


def normalize_header(name: str) -> str:
    """Chuẩn hoá tên cột: bỏ khoảng trắng thừa, viết thường."""
    return re.sub(r"\s+", " ", str(name)).strip().lower()


def file_fingerprint(path: Path) -> str:
    """Mã SHA-256 của file, dùng để nhận biết một file đã từng được nạp chưa."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_kiotviet_excel(path: Path) -> pd.DataFrame:
    """Đọc file Excel và đổi tên cột theo COLUMN_MAP.

    Báo lỗi rõ ràng nếu file thiếu cột, thay vì để lỗi xảy ra ở bước sau.
    """
    df = pd.read_excel(path, dtype={c: str for c in TEXT_COLUMNS})
    renamed = {col: COLUMN_MAP.get(normalize_header(col)) for col in df.columns}

    missing = set(COLUMN_MAP.values()) - {v for v in renamed.values() if v}
    if missing:
        raise ValueError(f"File thiếu các cột bắt buộc: {sorted(missing)}")

    unknown = [col for col, new in renamed.items() if new is None]
    if unknown:
        print(f"[cảnh báo] Bỏ qua các cột không nhận diện được: {unknown}")

    df = df.rename(columns=renamed)[list(COLUMN_MAP.values())]
    return coerce_types(df)


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Ép mọi cột về đúng kiểu: chữ, thời gian, còn lại là số."""
    df = df.copy()
    for col in df.columns:
        if col in STRING_FIELDS:
            df[col] = df[col].astype("string")
        elif col in DATETIME_FIELDS:
            df[col] = pd.to_datetime(df[col])
        else:
            df[col] = pd.to_numeric(df[col]).astype("float64")
    return df


def load_raw(con: duckdb.DuckDBPyConnection, path: Path) -> int:
    """Nạp một file vào bảng raw. Nạp lại cùng một file sẽ không bị nhân đôi."""
    df = read_kiotviet_excel(path)
    fingerprint = file_fingerprint(path)
    df["source_file"] = path.name
    df["source_hash"] = fingerprint
    df["loaded_at"] = datetime.now()

    con.register("incoming", df)
    con.execute(f"CREATE TABLE IF NOT EXISTS {RAW_TABLE} AS SELECT * FROM incoming LIMIT 0")
    con.execute(f"DELETE FROM {RAW_TABLE} WHERE source_hash = ?", [fingerprint])
    con.execute(f"INSERT INTO {RAW_TABLE} SELECT * FROM incoming")
    con.unregister("incoming")
    return len(df)
