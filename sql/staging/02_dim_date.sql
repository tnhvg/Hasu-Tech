-- =====================================================================
-- dim_date: bảng lịch, mỗi dòng = một ngày trong khoảng có dữ liệu.
-- Mục đích: phân biệt "cửa hàng đóng cửa" với "mở cửa nhưng không bán được".
-- Ngày đóng cửa KHÔNG được coi là nhu cầu bằng 0 khi huấn luyện mô hình.
-- =====================================================================

CREATE OR REPLACE TABLE dim_date AS
WITH bounds AS (
    SELECT min(sale_date) AS d0, max(sale_date) AS d1 FROM stg_sales_lines
),
spine AS (
    SELECT CAST(unnest(generate_series(d0, d1, INTERVAL 1 DAY)) AS DATE) AS date
    FROM bounds
),
daily AS (
    SELECT sale_date, count(DISTINCT invoice_id) AS n_sale_invoices
    FROM stg_sales_lines
    WHERE invoice_type = 'sale'
    GROUP BY sale_date
)
SELECT
    s.date,
    year(s.date)                        AS year,
    month(s.date)                       AS month,
    strftime(s.date, '%Y-%m')           AS year_month,
    isodow(s.date)                      AS iso_weekday,   -- 1 = Thứ Hai ... 7 = Chủ Nhật
    isodow(s.date) >= 6                 AS is_weekend,
    coalesce(d.n_sale_invoices, 0)      AS n_sale_invoices,
    d.sale_date IS NOT NULL             AS is_open
FROM spine s
LEFT JOIN daily d ON d.sale_date = s.date
ORDER BY s.date;
