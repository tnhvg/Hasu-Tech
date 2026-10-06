-- =====================================================================
-- mart_daily_traffic: lượng khách bán lẻ theo ngày (số hoá đơn khác nhau).
--
-- Không cộng cột n_invoices của fct_retail_daily_category để ra số hoá đơn
-- mỗi ngày: bảng đó đếm theo từng nhóm hàng, nên một hoá đơn mua 3 nhóm hàng
-- sẽ bị đếm 3 lần. Bảng này đếm hoá đơn duy nhất trên toàn cửa hàng.
-- =====================================================================

CREATE OR REPLACE TABLE mart_daily_traffic AS
SELECT
    sale_date                       AS date,
    count(DISTINCT invoice_id)      AS n_invoices,
    sum(line_revenue)               AS revenue,
    sum(quantity)                   AS quantity
FROM stg_sales_lines
WHERE txn_channel = 'retail' AND NOT is_return
GROUP BY 1
ORDER BY 1;
