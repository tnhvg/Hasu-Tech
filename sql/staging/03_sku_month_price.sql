-- =====================================================================
-- sku_month_price: giá bán phổ biến của mỗi mã hàng trong từng tháng,
-- tính trên các dòng bán lẻ thông thường (bỏ hàng trả, hàng tặng, khuyến
-- mại khai trương). Dùng để nhận diện dòng bán giảm giá.
--
-- Không dùng hàm mode(): khi hai mức giá có số lần bán bằng nhau, mode()
-- chọn tuỳ ý nên mỗi lần chạy có thể ra kết quả khác. Ở đây chọn giá có
-- số dòng bán nhiều nhất; nếu hoà thì lấy giá cao hơn (giá chưa giảm).
-- =====================================================================

CREATE OR REPLACE TABLE sku_month_price AS
WITH price_counts AS (
    SELECT sku, date_trunc('month', sale_date) AS month, unit_price, count(*) AS n_lines
    FROM stg_sales_lines
    WHERE txn_channel = 'retail'
      AND NOT is_return
      AND NOT is_zero_price
      AND NOT is_opening_promo
    GROUP BY ALL
)
SELECT sku, month, unit_price AS usual_price
FROM price_counts
QUALIFY row_number() OVER (PARTITION BY sku, month ORDER BY n_lines DESC, unit_price DESC) = 1;
