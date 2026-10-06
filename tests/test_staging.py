"""Kiểm thử các quy tắc làm sạch trong sql/staging trên một bộ dữ liệu nhỏ tự tạo."""

from datetime import datetime

import duckdb
import pandas as pd
import pytest

from hasu.config import SQL_DIR
from hasu.ingest import COLUMN_MAP, coerce_types


def _line(invoice_id, sku, qty, price, cost, category="Đồ uống>>Nước ngọt>>Nước giải khát",
          seller="Nhân viên A", note=None, sold_at="2026-06-01 10:00:00", loaded_at=None):
    row = dict.fromkeys(COLUMN_MAP.values())
    row.update(
        period_month="06-2026", invoice_id=invoice_id, branch="CN1", seller=seller, note=note,
        sold_at=pd.Timestamp(sold_at), sku=sku, product_name=f"SP {sku}",
        category_path=category, quantity=qty, unit_price=price, unit_cost=cost,
    )
    row.update(source_file="test.xlsx", source_hash="x", loaded_at=loaded_at or datetime(2026, 7, 1))
    return row


@pytest.fixture
def stg():
    rows = [
        _line("HD001", "A", 1, 10000, 8000),
        _line("HD001", "A", 1, 10000, 8000, loaded_at=datetime(2026, 7, 2)),  # trùng lặp
        _line("HD002", "A", 2, 10000, 0),                                      # thiếu giá vốn
        _line("HD003", "A", 500, 9000, 8000),                                  # đơn số lượng lớn
        _line("HD004", "B", 1, 5000, 0, category="Gạo", seller="Nhân viên B{DEL}"),
        _line("TH001", "A", -1, 10000, 8000),                                  # trả hàng
        _line("HD005.01", "A", 1, 10000, 8000, note="Xuất dùng nội bộ"),
        _line("HD006", "C", 1, 20000, 15000, category="Thực phẩm đông mát>>Kem"),
        _line("HD007", "C", 30, 60000, 50000),                                 # 1,8 triệu
        _line("HD007", "A", 40, 40000, 30000),                                 # + 1,6 triệu
    ]
    con = _staging(rows)
    return con.execute("SELECT * FROM stg_sales_lines ORDER BY invoice_id").df().set_index("invoice_id")


def _staging(rows, files=("01_stg_sales_lines.sql",)):
    """Nạp các dòng tự tạo vào raw_sales_lines rồi chạy các file SQL staging được chỉ định."""
    con = duckdb.connect()
    raw = pd.DataFrame(rows)
    raw = pd.concat([coerce_types(raw[list(COLUMN_MAP.values())]),
                     raw[["source_file", "source_hash", "loaded_at"]]], axis=1)
    con.register("rows", raw)
    con.execute("CREATE TABLE raw_sales_lines AS SELECT * FROM rows")
    for f in files:
        con.execute((SQL_DIR / "staging" / f).read_text(encoding="utf-8"))
    return con


def test_duplicates_are_removed(stg):
    assert len(stg) == 9


def test_return_invoice_is_flagged(stg):
    assert stg.loc["TH001", "is_return"]
    assert stg.loc["TH001", "line_revenue"] == -10000


def test_missing_cost_is_filled_from_same_sku(stg):
    assert stg.loc["HD002", "cost_missing"]
    assert stg.loc["HD002", "unit_cost_filled"] == 8000
    assert stg.loc["HD002", "cost_fill_method"] == "sku_median"


def test_missing_cost_without_history_cannot_be_filled_from_sku(stg):
    # Mã B chưa từng có giá vốn và nhóm "Gạo" chưa có tỷ lệ tham chiếu
    assert pd.isna(stg.loc["HD004", "cost_fill_method"])


def test_misplaced_category_is_fixed(stg):
    row = stg.loc["HD004"]
    assert (row.cat_l1, row.cat_l2, row.cat_l3) == ("Gạo, bột và thực phẩm khô", "Gạo", "Gạo")


def test_missing_level3_falls_back_to_level2(stg):
    assert stg.loc["HD006", "cat_l3"] == "Kem"


def test_seller_names_are_anonymised(stg):
    assert set(stg["seller_code"]) == {"NV01", "NV02"}
    assert "seller" not in stg.columns
    assert not stg.loc["HD004", "seller_active"]


def test_transaction_channels(stg):
    assert stg.loc["HD003", "txn_channel"] == "bulk"
    # mỗi dòng không lớn, nhưng cả hoá đơn 3,4 triệu -> đơn lớn
    assert (stg.loc["HD007", "txn_channel"] == "bulk").all()
    assert stg.loc["HD005.01", "txn_channel"] == "internal"
    assert stg.loc["HD001", "txn_channel"] == "retail"
    assert stg.loc["HD005.01", "invoice_base_id"] == "HD005"


def test_flags_are_never_null(stg):
    flags = [c for c in stg.columns if c.startswith("is_")]
    assert not stg[flags].isna().any().any()


def test_usual_price_tie_takes_higher_price():
    # Hai mức giá bán số lần bằng nhau: luôn lấy giá cao hơn (giá chưa giảm),
    # để mỗi lần chạy cho cùng một kết quả.
    rows = [_line(f"HD{i}", "T", 1, price, 5000, sold_at=f"2026-06-0{i} 10:00:00")
            for i, price in enumerate([10000, 9000, 10000, 9000], start=1)]
    con = _staging(rows, files=("01_stg_sales_lines.sql", "03_sku_month_price.sql"))
    assert con.execute("SELECT usual_price FROM sku_month_price WHERE sku = 'T'").fetchone()[0] == 10000
