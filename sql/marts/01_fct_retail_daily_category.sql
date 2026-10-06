-- =====================================================================
-- fct_retail_daily_category: nhu cầu bán lẻ theo ngày x nhóm hàng cấp 3.
-- Đây là bảng đầu vào chính cho mô hình dự báo.
--
--  - Chỉ tính giao dịch bán lẻ (txn_channel = 'retail'), bỏ phiếu trả hàng,
--    hàng tặng giá 0 và hàng khuyến mại khai trương.
--  - Đủ mọi tổ hợp (ngày mở cửa x nhóm hàng): ngày mở cửa mà không bán được
--    thì quantity = 0. Ngày đóng cửa KHÔNG có dòng nào (không phải nhu cầu 0).
--  - promo_qty_share: tỷ lệ số lượng bán với giá thấp hơn giá phổ biến trong
--    tháng của chính mã hàng từ 5% trở lên (dấu hiệu khuyến mãi / giảm giá).
--  - discount_depth: mức chiết khấu bình quân so với giá phổ biến
--    = 1 - sum(giá bán x SL) / sum(giá phổ biến x SL). Dùng làm biến giá cho
--    mô hình và kịch bản "giảm giá X%". Trống khi ngày đó không bán được.
-- =====================================================================

CREATE OR REPLACE TABLE fct_retail_daily_category AS
WITH retail AS (
    SELECT *
    FROM stg_sales_lines
    WHERE txn_channel = 'retail'
      AND NOT is_return
      AND NOT is_zero_price
      AND NOT is_opening_promo
),
-- Giá phổ biến của mỗi mã hàng trong tháng: bảng sku_month_price (sql/staging/03).
lines AS (
    SELECT
        r.*,
        r.unit_price < 0.95 * p.usual_price AS is_discounted,
        p.usual_price
    FROM retail r
    JOIN sku_month_price p
      ON p.sku = r.sku AND p.month = date_trunc('month', r.sale_date)
),
agg AS (
    SELECT
        sale_date AS date,
        cat_l3,
        sum(quantity)                                   AS quantity,
        sum(line_revenue)                               AS revenue,
        sum(line_profit)                                AS profit,
        count(DISTINCT invoice_id)                      AS n_invoices,
        sum(quantity) FILTER (is_discounted)            AS discounted_qty,
        1 - sum(unit_price * quantity) / nullif(sum(usual_price * quantity), 0) AS discount_depth
    FROM lines
    GROUP BY ALL
),
categories AS (
    SELECT DISTINCT cat_l1, cat_l2, cat_l3 FROM retail
),
grid AS (
    SELECT d.date, c.cat_l1, c.cat_l2, c.cat_l3
    FROM dim_date d CROSS JOIN categories c
    WHERE d.is_open
)
SELECT
    g.date,
    g.cat_l1,
    g.cat_l2,
    g.cat_l3,
    coalesce(a.quantity, 0)                             AS quantity,
    coalesce(a.revenue, 0)                              AS revenue,
    coalesce(a.profit, 0)                               AS profit,
    coalesce(a.n_invoices, 0)                           AS n_invoices,
    coalesce(a.discounted_qty, 0) / nullif(a.quantity, 0) AS promo_qty_share,
    a.discount_depth
FROM grid g
LEFT JOIN agg a ON a.date = g.date AND a.cat_l3 = g.cat_l3
ORDER BY g.cat_l3, g.date;
