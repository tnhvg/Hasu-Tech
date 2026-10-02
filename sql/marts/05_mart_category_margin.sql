-- =====================================================================
-- mart_category_margin: doanh thu x biên lợi nhuận theo nhóm hàng cấp 2
-- (quyết định tài chính: định giá, đàm phán nhà cung cấp).
-- Tính trên mọi giao dịch bán (cả bán lẻ và đơn lớn), trừ nội bộ; bỏ các dòng
-- không xác định được giá vốn và hàng tặng khai trương.
--
-- Phân nhóm theo hai ngưỡng: doanh thu trung vị giữa các nhóm và biên lợi nhuận
-- chung của cửa hàng:
--   Ngôi sao    : doanh thu cao, biên cao
--   Lời mỏng    : doanh thu cao, biên thấp
--   Tiềm năng   : doanh thu thấp, biên cao
--   Cần xem xét : doanh thu thấp, biên thấp
--   Thua lỗ     : lợi nhuận gộp âm
-- =====================================================================

CREATE OR REPLACE TABLE mart_category_margin AS
WITH c AS (
    SELECT
        cat_l1,
        cat_l2,
        sum(line_revenue)                   AS revenue,
        sum(line_profit)                    AS profit,
        sum(line_profit) FILTER (txn_channel = 'retail') / nullif(sum(line_revenue) FILTER (txn_channel = 'retail'), 0)
                                            AS retail_margin,
        sum(line_revenue) FILTER (txn_channel = 'retail') / sum(line_revenue)
                                            AS retail_share,
        count(DISTINCT sku)                 AS n_sku
    FROM stg_sales_lines
    WHERE txn_channel <> 'internal' AND cost_fill_method IS NOT NULL
      AND NOT is_opening_promo   -- hàng tặng khai trương không phải hàng kinh doanh
    GROUP BY ALL
    HAVING sum(line_revenue) > 0
),
thresholds AS (
    SELECT median(revenue) AS rev_median, sum(profit) / sum(revenue) AS store_margin FROM c
)
SELECT
    c.*,
    c.profit / c.revenue                    AS margin,
    c.revenue / sum(c.revenue) OVER ()      AS revenue_share,
    t.rev_median,
    t.store_margin,
    CASE
        WHEN c.profit < 0 THEN 'Thua lỗ'
        WHEN c.revenue >= t.rev_median AND c.profit / c.revenue >= t.store_margin THEN 'Ngôi sao'
        WHEN c.revenue >= t.rev_median THEN 'Lời mỏng'
        WHEN c.profit / c.revenue >= t.store_margin THEN 'Tiềm năng'
        ELSE 'Cần xem xét'
    END                                     AS quadrant
FROM c, thresholds t
ORDER BY c.revenue DESC;
