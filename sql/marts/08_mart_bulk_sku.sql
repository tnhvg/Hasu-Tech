-- =====================================================================
-- mart_bulk_sku: mặt hàng nào hay được mua sỉ (đơn lớn và đơn tổ chức).
--
-- Mô hình dự báo chỉ dự báo kênh bán lẻ, vì đơn sỉ đến bất chợt và mỗi đơn
-- rất lớn. Bảng này trả lời câu hỏi còn lại của chủ cửa hàng: những mã nào
-- khách sỉ hay mua, mỗi lần mua khoảng bao nhiêu, để giữ thêm một lượng hàng
-- dự phòng ngoài phần dự báo bán lẻ.
--
-- Cách làm:
--   1. Gộp các dòng của cùng một mã trong cùng một hoá đơn sỉ thành một "lần mua".
--   2. Với mỗi mã: đếm số lần mua sỉ, số tháng có mua sỉ, trung vị số lượng
--      mỗi lần mua, tỷ trọng sỉ trong tổng số lượng bán ra.
--   3. Phân loại theo số tháng có đơn sỉ trên tổng số tháng có dữ liệu:
--        thuong_xuyen : có đơn sỉ ở ít nhất một nửa số tháng
--        thinh_thoang : từ 2 lần mua trở lên nhưng chưa đủ nửa số tháng
--        mot_lan      : chỉ được mua sỉ đúng 1 lần
--      Ngưỡng "một nửa số tháng" là lựa chọn của người phân tích, đủ đơn giản để
--      chủ cửa hàng tự kiểm tra lại; không phải ngưỡng thống kê chuẩn.
--   4. Lượng dự phòng gợi ý (reserve_qty) = trung vị số lượng một lần mua sỉ,
--      làm tròn lên, chỉ tính cho nhóm thuong_xuyen. Tức là luôn giữ sẵn đủ
--      hàng cho khoảng một đơn sỉ điển hình. reserve_value là số vốn tương ứng
--      (lượng dự phòng x giá vốn trung vị).
--
-- Bảng chỉ có mã hàng, tên sản phẩm và số liệu tổng hợp: không có mã hoá đơn,
-- tên khách hay tên nhân viên.
-- =====================================================================

CREATE OR REPLACE TABLE mart_bulk_sku AS
WITH
bulk_purchase AS (      -- mỗi dòng = một mã trong một hoá đơn sỉ
    SELECT
        invoice_id,
        sku,
        min(sale_date)      AS sale_date,
        sum(quantity)       AS qty,
        sum(line_revenue)   AS revenue,
        median(unit_cost_filled) AS unit_cost
    FROM stg_sales_lines
    WHERE txn_channel IN ('bulk', 'organization')
      AND NOT is_return AND NOT is_zero_price AND quantity > 0
    GROUP BY 1, 2
),
retail AS (
    SELECT sku, sum(quantity) AS retail_qty
    FROM stg_sales_lines
    WHERE txn_channel = 'retail' AND NOT is_return AND NOT is_zero_price
    GROUP BY 1
),
sku_info AS (           -- tên và nhóm hàng theo lần bán gần nhất
    SELECT sku,
           arg_max(product_name, sold_at) AS product_name,
           arg_max(cat_l1, sold_at)       AS cat_l1,
           arg_max(cat_l3, sold_at)       AS cat_l3
    FROM stg_sales_lines
    GROUP BY 1
),
n_months AS (
    SELECT count(DISTINCT date_trunc('month', sale_date)) AS n_data_months
    FROM stg_sales_lines
),
per_sku AS (
    SELECT
        sku,
        count(*)                                        AS n_bulk_orders,
        count(DISTINCT date_trunc('month', sale_date))  AS n_bulk_months,
        sum(qty)                                        AS bulk_qty,
        median(qty)                                     AS median_qty_per_order,
        max(qty)                                        AS max_qty_per_order,
        sum(revenue)                                    AS bulk_revenue,
        max(sale_date)                                  AS last_bulk_date,
        median(unit_cost)                               AS unit_cost
    FROM bulk_purchase
    GROUP BY 1
)
SELECT
    p.sku,
    i.product_name,
    i.cat_l1,
    i.cat_l3,
    p.n_bulk_orders,
    p.n_bulk_months,
    m.n_data_months,
    p.bulk_qty,
    p.median_qty_per_order,
    p.max_qty_per_order,
    p.bulk_revenue,
    coalesce(r.retail_qty, 0)                                   AS retail_qty,
    p.bulk_qty / (p.bulk_qty + coalesce(r.retail_qty, 0))       AS bulk_share_qty,
    p.last_bulk_date,
    CASE
        WHEN p.n_bulk_months * 2 >= m.n_data_months THEN 'thuong_xuyen'
        WHEN p.n_bulk_orders >= 2                   THEN 'thinh_thoang'
        ELSE 'mot_lan'
    END                                                         AS bulk_frequency,
    CASE
        WHEN p.n_bulk_months * 2 >= m.n_data_months THEN ceil(p.median_qty_per_order)
        ELSE 0
    END                                                         AS reserve_qty,
    p.unit_cost,
    -- vốn cần để giữ lượng dự phòng, tính theo giá vốn trung vị
    CASE
        WHEN p.n_bulk_months * 2 >= m.n_data_months THEN ceil(p.median_qty_per_order) * p.unit_cost
        ELSE 0
    END                                                         AS reserve_value
FROM per_sku p
JOIN sku_info i USING (sku)
LEFT JOIN retail r USING (sku)
CROSS JOIN n_months m
ORDER BY p.n_bulk_months DESC, p.n_bulk_orders DESC, p.bulk_revenue DESC;
