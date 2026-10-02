-- =====================================================================
-- mart_tet_effect: hệ số ảnh hưởng Tết Bính Ngọ (mùng 1 = 17/02/2026) lên bán lẻ.
-- Vùng ảnh hưởng ±14 ngày: "trước Tết" = 14 ngày trước mùng 1, "sau Tết" =
-- 14 ngày từ mùng 1 (đa số các ngày này cửa hàng nghỉ). Mức nền = trung bình
-- các ngày mở cửa ngoài vùng ảnh hưởng.
-- Hệ số = trung bình mỗi ngày mở cửa trong vùng / mức nền, tính riêng cho
-- số lượng và doanh thu, theo nhóm hàng cấp 1.
-- Lưu ý: chỉ có MỘT kỳ Tết trong dữ liệu, nên hệ số này là một lần quan sát.
-- =====================================================================

CREATE OR REPLACE TABLE mart_tet_effect AS
WITH d AS (
    SELECT
        date, cat_l1, sum(quantity) AS quantity, sum(revenue) AS revenue,
        datediff('day', DATE '2026-02-17', date) AS k
    FROM fct_retail_daily_category
    GROUP BY ALL
),
w AS (
    SELECT
        *,
        CASE WHEN k BETWEEN -14 AND -1 THEN 'Trước Tết'
             WHEN k BETWEEN 0 AND 13 THEN 'Sau Tết'
             ELSE 'Nền' END AS tet_window
    FROM d
),
by_cat AS (
    SELECT cat_l1, tet_window, count(DISTINCT date) AS n_days,
           avg(quantity) AS qty_per_day, avg(revenue) AS rev_per_day
    FROM w GROUP BY ALL
),
total AS (
    SELECT 'Toàn cửa hàng' AS cat_l1, tet_window, count(*) AS n_days,
           avg(quantity) AS qty_per_day, avg(revenue) AS rev_per_day
    FROM (SELECT date, tet_window, sum(quantity) AS quantity, sum(revenue) AS revenue FROM w GROUP BY ALL)
    GROUP BY ALL
),
u AS (SELECT * FROM by_cat UNION ALL SELECT * FROM total)
SELECT
    a.cat_l1,
    a.tet_window,
    a.n_days,
    a.qty_per_day,
    a.rev_per_day,
    a.qty_per_day / nullif(b.qty_per_day, 0) AS qty_factor,
    a.rev_per_day / nullif(b.rev_per_day, 0) AS rev_factor
FROM u a
JOIN u b ON b.cat_l1 = a.cat_l1 AND b.tet_window = 'Nền'
WHERE a.tet_window <> 'Nền';
