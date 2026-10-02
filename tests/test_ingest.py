import pandas as pd
import pytest

from hasu.ingest import COLUMN_MAP, normalize_header, read_kiotviet_excel

# Tên cột đúng như trong file KiotViet (có chữ hoa, có dấu).
KIOTVIET_HEADERS = [
    "Thời gian", "Tổng tiền hàng (theo thời gian)", "Giảm giá (theo thời gian)",
    "Doanh thu (theo thời gian)", "Tổng giá vốn (theo thời gian)",
    "Lợi nhuận gộp (theo thời gian)", "Mã giao dịch", "Chi nhánh", "Người bán", "Ghi chú",
    "Thời gian (theo giao dịch)", "Tổng tiền hàng (theo giao dịch)",
    "Giảm giá (theo giao dịch)", "Doanh thu (theo giao dịch)",
    "Tổng giá vốn (theo giao dịch)", "Lợi nhuận gộp (theo giao dịch)", "Mã hàng", "Mã vạch",
    "Tên hàng", "Thương hiệu", "Nhóm hàng(3 Cấp)", "SL", "Giá bán/SP", "Giá vốn/SP",
    "Lợi nhuận/SP", "Tổng lợi nhuận hàng hóa",
]


def _sample_row():
    return [
        "06-2026", 100, 0, 100, 80, 20, "HD000001", "CN1", "A", None,
        "2026-06-30 19:27:56", 18000, 0, 18000, 15000, 3000, "02000758", "893", "Nước",
        None, "Đồ uống>>Nước ngọt>>Nước giải khát", 2, 9000, 7500, 1500, 3000,
    ]


def test_normalize_header_ignores_case_and_extra_spaces():
    assert normalize_header("  Giá  bán/SP ") == "giá bán/sp"


def test_every_kiotviet_header_is_mapped():
    assert {normalize_header(h) for h in KIOTVIET_HEADERS} == set(COLUMN_MAP)


def test_read_keeps_leading_zeros_in_sku(tmp_path):
    path = tmp_path / "kv.xlsx"
    pd.DataFrame([_sample_row()], columns=KIOTVIET_HEADERS).to_excel(path, index=False)

    df = read_kiotviet_excel(path)

    assert df.loc[0, "sku"] == "02000758"
    assert df.loc[0, "quantity"] == 2
    assert list(df.columns) == list(COLUMN_MAP.values())


def test_read_fails_clearly_when_a_column_is_missing(tmp_path):
    path = tmp_path / "kv.xlsx"
    df = pd.DataFrame([_sample_row()], columns=KIOTVIET_HEADERS).drop(columns=["SL"])
    df.to_excel(path, index=False)

    with pytest.raises(ValueError, match="quantity"):
        read_kiotviet_excel(path)
