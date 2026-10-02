"""Xuất bộ dữ liệu demo cho ứng dụng: chỉ các bảng tổng hợp, KHÔNG có dữ liệu thô.

    python -m hasu.export_demo

Repo công khai nên ứng dụng triển khai trên mạng không được chứa tên nhân viên,
tên khách nợ hay ghi chú hoá đơn. Các bảng dưới đây chỉ chứa số liệu theo
ngày x nhóm hàng, theo mã hàng (tên sản phẩm) và kết quả mô hình.
"""

from __future__ import annotations

import duckdb

from hasu.config import DB_PATH, ROOT

DEMO_DIR = ROOT / "app" / "demo_data"

DEMO_TABLES = [
    "dim_date", "fct_retail_daily_category", "mart_monthly", "mart_sku_abc", "mart_hour_weekday",
    "mart_category_margin", "mart_tet_effect", "mart_basket_rules", "mart_stockout_suspects",
    "fc_profile", "fc_metrics", "fc_metrics_levels", "fc_backtest_weekly", "fc_simulation",
    "fc_ratio_quantiles", "fc_forecast_daily", "fc_order_plan", "fc_sku_allocation",
    "fc_shap_global", "fc_shap_local", "fc_price_response", "fc_run_info", "fc_snapshots",
]

# Cột không được phép xuất hiện trong dữ liệu demo
FORBIDDEN_COLUMNS = {"seller", "note", "seller_code", "invoice_id"}


def main() -> None:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        for t in DEMO_TABLES:
            cols = {c[0] for c in con.execute(f"DESCRIBE {t}").fetchall()}
            leaked = cols & FORBIDDEN_COLUMNS
            if leaked:
                raise ValueError(f"Bảng {t} chứa cột nhạy cảm {leaked}, không xuất.")
            con.execute(f"COPY {t} TO '{DEMO_DIR / (t + '.parquet')}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    size = sum(f.stat().st_size for f in DEMO_DIR.glob("*.parquet"))
    print(f"Đã xuất {len(DEMO_TABLES)} bảng vào {DEMO_DIR.relative_to(ROOT)} ({size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
