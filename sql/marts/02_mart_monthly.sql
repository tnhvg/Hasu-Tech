-- =====================================================================
-- mart_monthly: doanh thu, lợi nhuận theo tháng và theo kênh bán.
-- revenue_per_open_day giúp so sánh công bằng tháng 09/2025 (chỉ có từ ngày 11)
-- và tháng 02/2026 (nghỉ Tết) với các tháng còn lại.
-- =====================================================================

CREATE OR REPLACE TABLE mart_monthly AS
WITH open_days AS (
    SELECT year_month, count(*) FILTER (is_open) AS open_days
    FROM dim_date GROUP BY 1
)
SELECT
    strftime(s.sale_date, '%Y-%m')                      AS year_month,
    CASE WHEN s.txn_channel = 'retail' THEN 'Bán lẻ'
         WHEN s.txn_channel IN ('bulk', 'organization') THEN 'Đơn lớn / tổ chức'
         ELSE 'Nội bộ' END                              AS channel,
    sum(s.line_revenue)                                 AS revenue,
    sum(s.line_profit) FILTER (s.cost_fill_method IS NOT NULL) AS profit,
    count(DISTINCT s.invoice_id) FILTER (NOT s.is_return) AS n_invoices,
    sum(s.quantity)                                     AS quantity,
    any_value(o.open_days)                              AS open_days,
    sum(s.line_revenue) / any_value(o.open_days)        AS revenue_per_open_day
FROM stg_sales_lines s
JOIN open_days o ON o.year_month = strftime(s.sale_date, '%Y-%m')
GROUP BY ALL
ORDER BY 1, 2;
