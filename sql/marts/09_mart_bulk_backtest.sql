-- =====================================================================
-- mart_bulk_backtest: kiểm chứng NGOÀI MẪU chính sách dự phòng hàng sỉ.
--
-- Chia dữ liệu theo thời gian: 3 tháng dương lịch cuối là giai đoạn kiểm tra,
-- các tháng trước đó là giai đoạn học. Trên giai đoạn học, áp dụng đúng quy tắc
-- của mart_bulk_sku (có đơn sỉ ở ít nhất một nửa số tháng -> "thường xuyên",
-- dự phòng = trung vị số lượng mỗi lần mua, làm tròn lên). Trên giai đoạn kiểm
-- tra, đo xem dự phòng đó đáp ứng được bao nhiêu lần mua sỉ thật sự xảy ra.
--
-- Mỗi dòng là một chỉ số (metric, value) để dễ đọc trong báo cáo.
-- =====================================================================

CREATE OR REPLACE TABLE mart_bulk_backtest AS
WITH
purchase AS (
    SELECT invoice_id, sku, min(sale_date) AS sale_date, sum(quantity) AS qty,
           median(unit_cost_filled) AS unit_cost
    FROM stg_sales_lines
    WHERE txn_channel IN ('bulk', 'organization')
      AND NOT is_return AND NOT is_zero_price AND quantity > 0
    GROUP BY 1, 2
),
cut AS (
    SELECT date_trunc('month', max(sale_date)) - INTERVAL 2 MONTH AS test_start,
           (SELECT count(DISTINCT date_trunc('month', sale_date)) FROM stg_sales_lines) - 3 AS train_months
    FROM stg_sales_lines
),
train AS (
    SELECT p.sku,
           count(DISTINCT date_trunc('month', p.sale_date)) AS n_months,
           ceil(median(p.qty))                               AS reserve_qty,
           median(p.unit_cost)                               AS unit_cost
    FROM purchase p, cut
    WHERE p.sale_date < cut.test_start
    GROUP BY 1
),
frequent AS (
    SELECT t.* FROM train t, cut WHERE t.n_months * 2 >= cut.train_months
),
test AS (
    SELECT p.*, f.reserve_qty, f.sku IS NOT NULL AS is_frequent
    FROM purchase p
    CROSS JOIN cut
    LEFT JOIN frequent f ON f.sku = p.sku
    WHERE p.sale_date >= cut.test_start
)
SELECT * FROM (
    SELECT 1 AS ord, 'test_start' AS metric, epoch(any_value(test_start)) AS value FROM cut
    UNION ALL SELECT 2, 'train_months', any_value(train_months) FROM cut
    UNION ALL SELECT 3, 'frequent_skus', count(*) FROM frequent
    UNION ALL SELECT 4, 'reserve_value', sum(reserve_qty * unit_cost) FROM frequent
    UNION ALL SELECT 5, 'frequent_skus_reordered',
        count(DISTINCT sku) FILTER (is_frequent) FROM test
    UNION ALL SELECT 6, 'test_purchases', count(*) FROM test
    UNION ALL SELECT 7, 'test_purchases_frequent', count(*) FILTER (is_frequent) FROM test
    UNION ALL SELECT 8, 'share_purchases_fully_covered',
        avg(CASE WHEN qty <= reserve_qty THEN 1.0 ELSE 0.0 END) FILTER (is_frequent) FROM test
    UNION ALL SELECT 9, 'share_qty_covered',
        sum(least(qty, reserve_qty)) FILTER (is_frequent) / sum(qty) FILTER (is_frequent) FROM test
    UNION ALL SELECT 10, 'share_bulk_qty_of_frequent',
        sum(qty) FILTER (is_frequent) / sum(qty) FROM test
) ORDER BY ord;
