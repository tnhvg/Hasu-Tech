-- =====================================================================
-- mart_hour_weekday: số hoá đơn bán lẻ trung bình theo (thứ, giờ), tính trên
-- số ngày mở cửa của từng thứ. Dùng cho bản đồ nhiệt và xếp ca.
-- =====================================================================

CREATE OR REPLACE TABLE mart_hour_weekday AS
WITH weekday_days AS (
    SELECT iso_weekday, count(*) AS n_days
    FROM dim_date WHERE is_open GROUP BY 1
),
inv AS (
    SELECT DISTINCT invoice_id, iso_weekday, sale_hour, sale_date
    FROM stg_sales_lines
    WHERE txn_channel = 'retail' AND NOT is_return
),
rev AS (
    SELECT iso_weekday, sale_hour, sum(line_revenue) AS revenue
    FROM stg_sales_lines
    WHERE txn_channel = 'retail' AND NOT is_return
    GROUP BY ALL
),
cnt AS (
    SELECT iso_weekday, sale_hour, count(*) AS n_invoices
    FROM inv GROUP BY ALL
)
SELECT
    c.iso_weekday,
    c.sale_hour,
    c.n_invoices / w.n_days         AS avg_invoices,
    r.revenue / w.n_days            AS avg_revenue,
    w.n_days
FROM cnt c
JOIN weekday_days w USING (iso_weekday)
JOIN rev r USING (iso_weekday, sale_hour)
ORDER BY 1, 2;
