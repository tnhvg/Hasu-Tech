"""Các phân tích cần Python (không viết gọn bằng SQL được).

- Phân tích giỏ hàng (thuật toán FP-Growth, cho kết quả giống Apriori nhưng nhanh hơn)
- Phát hiện giai đoạn nghi ngờ hết hàng

Kết quả được ghi vào DuckDB (mart_basket_rules, mart_stockout_suspects) để
báo cáo và ứng dụng dùng chung.
"""

from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth

# --------------------------------------------------------------------------
# Phân tích giỏ hàng
# --------------------------------------------------------------------------

BASKET_SQL = """
WITH retail AS (
    SELECT * FROM stg_sales_lines
    WHERE txn_channel = 'retail' AND NOT is_return AND NOT is_zero_price AND NOT is_opening_promo
),
usual AS (
    SELECT sku, date_trunc('month', sale_date) AS month, mode(unit_price) AS usual_price
    FROM retail GROUP BY ALL
)
SELECT DISTINCT r.invoice_id, r.cat_l3
FROM retail r
JOIN usual u ON u.sku = r.sku AND u.month = date_trunc('month', r.sale_date)
-- Bỏ các dòng bán dưới giá phổ biến (khuyến mãi) để luật phản ánh hành vi mua tự nhiên
WHERE r.unit_price >= 0.95 * u.usual_price
"""


def basket_rules(con: duckdb.DuckDBPyConnection, min_support: float = 0.01,
                 min_lift: float = 1.2) -> pd.DataFrame:
    """Luật kết hợp giữa các nhóm hàng cấp 3 trong cùng một hoá đơn bán lẻ.

    Dùng nhóm hàng cấp 3 thay vì từng mã hàng: mã hàng quá thưa (94% mã bán
    dưới 10% số ngày) nên hầu như không cặp mã nào đủ độ hỗ trợ.
    Chỉ xét hoá đơn có từ 2 nhóm hàng trở lên.
    """
    lines = con.execute(BASKET_SQL).df()
    size = lines.groupby("invoice_id")["cat_l3"].transform("size")
    lines = lines[size >= 2]
    n_baskets = lines["invoice_id"].nunique()

    onehot = pd.crosstab(lines["invoice_id"], lines["cat_l3"]).astype(bool)
    itemsets = fpgrowth(onehot, min_support=min_support, use_colnames=True)
    rules = association_rules(itemsets, metric="lift", min_threshold=min_lift)

    rules = rules[(rules["antecedents"].map(len) == 1) & (rules["consequents"].map(len) == 1)]
    out = pd.DataFrame({
        "antecedent": rules["antecedents"].map(lambda s: next(iter(s))),
        "consequent": rules["consequents"].map(lambda s: next(iter(s))),
        "support": rules["support"],
        "confidence": rules["confidence"],
        "lift": rules["lift"],
        "n_baskets": (rules["support"] * n_baskets).round().astype(int),
    })
    # Mỗi cặp chỉ giữ một chiều (chiều có độ tin cậy cao hơn)
    out["pair"] = out.apply(lambda r: tuple(sorted([r.antecedent, r.consequent])), axis=1)
    out = out.sort_values("confidence", ascending=False).drop_duplicates("pair").drop(columns="pair")
    out["total_multi_item_baskets"] = n_baskets
    return out.sort_values("lift", ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------
# Nghi ngờ hết hàng
# --------------------------------------------------------------------------

def stockout_suspects(con: duckdb.DuckDBPyConnection, min_sell_ratio: float = 0.15,
                      max_prob: float = 0.01, min_gap: int = 5) -> pd.DataFrame:
    """Tìm các chuỗi ngày mở cửa liên tiếp mà một mã bán đều bỗng không bán được.

    Với mã hàng bán được ở tỷ lệ p số ngày, xác suất ngẫu nhiên có L ngày liên tiếp
    không bán là khoảng (1 - p)^L. Nếu xác suất này < max_prob thì khoảng trống
    khó xảy ra do tình cờ -> nghi ngờ hết hàng (hoặc ngừng kinh doanh).
    Chỉ là SUY ĐOÁN từ dữ liệu bán, cần chủ cửa hàng xác nhận.
    """
    open_days = con.execute("SELECT date FROM dim_date WHERE is_open ORDER BY date").df()["date"]
    open_days = pd.to_datetime(open_days)
    sold = con.execute("""
        SELECT s.sku, s.product_name, s.cat_l3, s.sale_date AS date
        FROM stg_sales_lines s
        JOIN mart_sku_abc a USING (sku)
        WHERE s.txn_channel = 'retail' AND NOT s.is_return AND a.sell_day_ratio >= ?
        GROUP BY ALL
    """, [min_sell_ratio]).df()
    sold["date"] = pd.to_datetime(sold["date"])

    records = []
    for sku, g in sold.groupby("sku"):
        first = g["date"].min()
        days = open_days[open_days >= first].reset_index(drop=True)
        has_sale = days.isin(set(g["date"])).to_numpy()
        p = has_sale.mean()
        # Tìm các đoạn liên tiếp không bán
        gap_start = None
        for i, s in enumerate(np.append(has_sale, True)):
            if not s and gap_start is None:
                gap_start = i
            elif s and gap_start is not None:
                length = i - gap_start
                prob = (1 - p) ** length
                if length >= min_gap and prob < max_prob:
                    ends_at_data_end = i == len(has_sale)
                    records.append({
                        "sku": sku,
                        "product_name": g["product_name"].iloc[0],
                        "cat_l3": g["cat_l3"].iloc[0],
                        "gap_start": days[gap_start].date(),
                        "gap_end": days[i - 1].date(),
                        "gap_open_days": length,
                        "sell_day_ratio": p,
                        "chance_probability": prob,
                        "status": ("Không bán tới cuối kỳ: hết hàng hoặc đã ngừng bán"
                                   if ends_at_data_end else "Nghi ngờ hết hàng"),
                    })
                gap_start = None
    cols = ["sku", "product_name", "cat_l3", "gap_start", "gap_end", "gap_open_days",
            "sell_day_ratio", "chance_probability", "status"]
    return pd.DataFrame(records, columns=cols).sort_values("chance_probability").reset_index(drop=True)


def build_analysis_tables(con: duckdb.DuckDBPyConnection) -> None:
    for name, df in {
        "mart_basket_rules": basket_rules(con),
        "mart_stockout_suspects": stockout_suspects(con),
    }.items():
        con.register("tmp_df", df)
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM tmp_df")
        con.unregister("tmp_df")
        print(f"  {name}: {len(df)} dòng")
