-- =====================================================================
-- mart_sku_abc: phân loại ABC mã hàng theo SỐ LƯỢNG bán lẻ (quyết định vận hành,
-- tồn kho). A = nhóm mã cộng dồn tới 80% số lượng, B = 80-95%, C = phần còn lại.
-- Kèm doanh thu, lợi nhuận để đối chiếu với góc nhìn tài chính.
-- =====================================================================

CREATE OR REPLACE TABLE mart_sku_abc AS
WITH open_days AS (SELECT count(*) AS n FROM dim_date WHERE is_open),
sku AS (
    SELECT
        sku,
        any_value(product_name)             AS product_name,
        any_value(cat_l1)                   AS cat_l1,
        any_value(cat_l3)                   AS cat_l3,
        sum(quantity)                       AS quantity,
        sum(line_revenue)                   AS revenue,
        sum(line_profit) FILTER (cost_fill_method IS NOT NULL) AS profit,
        count(DISTINCT sale_date)           AS days_sold,
        min(sale_date)                      AS first_sale,
        max(sale_date)                      AS last_sale
    FROM stg_sales_lines
    WHERE txn_channel = 'retail' AND NOT is_return AND NOT is_zero_price
    GROUP BY sku
),
ranked AS (
    SELECT
        *,
        sum(quantity) OVER (ORDER BY quantity DESC, sku ROWS UNBOUNDED PRECEDING)
            / sum(quantity) OVER ()          AS cum_qty_share,
        row_number() OVER (ORDER BY quantity DESC, sku) AS qty_rank
    FROM sku
    WHERE quantity > 0
)
SELECT
    r.*,
    r.days_sold / o.n                       AS sell_day_ratio,
    CASE
        WHEN r.cum_qty_share - r.quantity / sum(r.quantity) OVER () < 0.80 THEN 'A'
        WHEN r.cum_qty_share - r.quantity / sum(r.quantity) OVER () < 0.95 THEN 'B'
        ELSE 'C'
    END                                     AS abc_class
FROM ranked r, open_days o
ORDER BY qty_rank;
