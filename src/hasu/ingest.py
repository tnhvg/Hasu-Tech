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

# Tên gọi khác thường gặp (file từ phần mềm bán hàng khác, hoặc tự đổi tên cột).
SYNONYMS = {
    "số lượng": "quantity", "sl bán": "quantity", "qty": "quantity",
    "mã hóa đơn": "invoice_id", "mã hoá đơn": "invoice_id", "số hóa đơn": "invoice_id", "mã hđ": "invoice_id",
    "ngày bán": "sold_at", "thời gian bán": "sold_at", "ngày giờ": "sold_at",
    "mã sản phẩm": "sku", "mã sp": "sku", "sku": "sku",
    "tên sản phẩm": "product_name", "tên sp": "product_name",
    "nhóm hàng": "category_path", "danh mục": "category_path", "ngành hàng": "category_path",
    "đơn giá": "unit_price", "giá bán": "unit_price", "giá vốn": "unit_cost",
    "nhân viên": "seller", "nhân viên bán": "seller", "thu ngân": "seller",
    "cửa hàng": "branch", "barcode": "barcode",
}

# Cột bắt buộc ở mức dòng sản phẩm. Các cột còn lại (tổng tháng, tổng hoá đơn...)
# chỉ dùng để đối soát, thiếu thì vẫn xử lý được.
REQUIRED_FIELDS = [
    "invoice_id", "sold_at", "sku", "product_name", "category_path", "quantity", "unit_price", "unit_cost",
]

# Các cột mã (invoice_id, sku, barcode) luôn được đọc dưới dạng chữ để không mất
# số 0 ở đầu (vd "02000758").

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


def detect_mapping(headers: list[str]) -> dict[str, str | None]:
    """Đoán cột chuẩn cho từng cột của file, theo từ điển KiotViet rồi từ điển đồng nghĩa."""
    mapping = {}
    for h in headers:
        key = normalize_header(h)
        mapping[h] = COLUMN_MAP.get(key) or SYNONYMS.get(key)
    return mapping


def missing_required(mapping: dict[str, str | None]) -> list[str]:
    return [f for f in REQUIRED_FIELDS if f not in set(mapping.values())]


def read_kiotviet_excel(path: Path, mapping: dict[str, str | None] | None = None) -> pd.DataFrame:
    """Đọc file Excel và đổi tên cột theo ánh xạ (mặc định: tự nhận diện).

    Báo lỗi rõ ràng nếu thiếu cột bắt buộc, thay vì để lỗi xảy ra ở bước sau.
    Cột không bắt buộc bị thiếu sẽ được thêm vào với giá trị trống.
    """
    headers = pd.read_excel(path, nrows=0).columns.tolist()
    mapping = mapping or detect_mapping(headers)
    text_cols = [h for h, std in mapping.items() if std in ("invoice_id", "sku", "barcode")]
    df = pd.read_excel(path, dtype={c: str for c in text_cols})

    missing = missing_required(mapping)
    if missing:
        raise ValueError(f"File thiếu các cột bắt buộc: {missing}")

    unknown = [h for h, std in mapping.items() if std is None]
    if unknown:
        print(f"[cảnh báo] Bỏ qua các cột không nhận diện được: {unknown}")

    df = df.rename(columns={h: std for h, std in mapping.items() if std})
    df = df.loc[:, ~df.columns.duplicated()]
    for col in COLUMN_MAP.values():
        if col not in df.columns:
            df[col] = None
    return coerce_types(df[list(COLUMN_MAP.values())])


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


def load_raw(con: duckdb.DuckDBPyConnection, path: Path,
             mapping: dict[str, str | None] | None = None) -> int:
    """Nạp một file vào bảng raw. Nạp lại cùng một file sẽ không bị nhân đôi."""
    df = read_kiotviet_excel(path, mapping)
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
