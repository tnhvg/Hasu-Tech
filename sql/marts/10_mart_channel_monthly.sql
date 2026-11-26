-- =====================================================================
-- mart_channel_monthly: kiểm tra giả thuyết "khách lẻ chuyển sang mua sỉ".
--
-- Lượng khách bán lẻ giảm từ tháng 5/2026 trong khi số đơn sỉ tăng. Bảng này
-- đặt các chỉ số theo tháng cạnh nhau để xem hai hiện tượng có cùng thời điểm
-- không, khách lẻ giảm ở khung giờ nào, và có dấu hiệu hoá đơn bán lẻ lớn bị
-- "đẩy" sang kênh đơn lớn (vượt ngưỡng 3 triệu đồng) hay không.
-- =====================================================================

CREATE OR REPLACE TABLE mart_channel_monthly AS
WITH inv AS (
    SELECT invoice_id, any_value(txn_channel) AS channel, min(sale_date) AS sale_date,
           min(sale_hour) AS sale_hour, sum(line_revenue) AS value
    FROM stg_sales_lines
    WHERE NOT is_return
    GROUP BY 1
),
days AS (
    SELECT strftime(date, '%Y-%m') AS year_month, count(*) FILTER (is_open) AS open_days
    FROM dim_date GROUP BY 1
)
SELECT
    strftime(i.sale_date, '%Y-%m')                                                  AS year_month,
    any_value(d.open_days)                                                          AS open_days,
    count(*) FILTER (i.channel = 'retail') / any_value(d.open_days)                 AS retail_inv_per_day,
    count(*) FILTER (i.channel = 'retail' AND i.sale_hour < 12) / any_value(d.open_days)
                                                                                    AS retail_morning_per_day,
    count(*) FILTER (i.channel = 'retail' AND i.sale_hour BETWEEN 12 AND 15) / any_value(d.open_days)
                                                                                    AS retail_midday_per_day,
    count(*) FILTER (i.channel = 'retail' AND i.sale_hour >= 16) / any_value(d.open_days)
                                                                                    AS retail_evening_per_day,
    count(*) FILTER (i.channel = 'retail' AND i.value >= 500000)                    AS retail_inv_500k_plus,
    count(*) FILTER (i.channel IN ('bulk', 'organization'))                         AS bulk_orders,
    sum(i.value) FILTER (i.channel IN ('bulk', 'organization'))                     AS bulk_revenue
FROM inv i
JOIN days d ON d.year_month = strftime(i.sale_date, '%Y-%m')
GROUP BY 1
ORDER BY 1;
