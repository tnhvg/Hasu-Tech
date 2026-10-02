-- =====================================================================
-- stg_sales_lines: mỗi dòng = một sản phẩm trong một hoá đơn, đã làm sạch.
-- Nguồn: raw_sales_lines (giữ nguyên như file KiotViet).
--
-- Các quyết định làm sạch (xem docs/data_quality_report.md để biết số liệu):
--  1. Khử trùng lặp theo khoá (invoice_id, sold_at, sku); nếu cùng một dòng
--     được nạp từ nhiều file thì giữ bản nạp sau cùng.
--  2. Hoá đơn "TH..." là phiếu trả hàng (số lượng âm) -> is_return.
--     Hoá đơn "HD....01" là bản sửa của hoá đơn gốc; bản gốc không còn trong
--     dữ liệu nên không bị đếm hai lần.
--  3. Doanh thu tính lại ở mức dòng = quantity * unit_price. unit_price của
--     KiotViet đã trừ giảm giá hoá đơn được phân bổ xuống từng dòng, nên
--     tổng các dòng khớp với doanh thu hoá đơn. Không dùng các cột invoice_*
--     và month_* để cộng dồn vì chúng bị lặp lại trên nhiều dòng.
--  4. Giá vốn = 0 là giá vốn bị thiếu, không phải hàng miễn phí. Điền theo thứ tự:
--     (a) trung vị giá vốn > 0 của chính mã hàng đó;
--     (b) nếu mã hàng chưa từng có giá vốn: giá bán x tỷ lệ giá vốn/giá bán
--         trung vị của nhóm hàng. Cách điền được ghi ở cột cost_fill_method.
--  5. Nhóm hàng: tách 3 cấp, sửa các giá trị rác/không chuẩn, cấp còn thiếu
--     lấy theo cấp trên.
--  6. Tên người bán được thay bằng mã NV01, NV02... để bảo vệ thông tin cá nhân.
--  7. Gắn cờ các giao dịch không phản ánh nhu cầu bán lẻ thông thường:
--     xuất nội bộ, hàng mẫu, trả nhà cung cấp, đơn tổ chức, đơn số lượng lớn.
--  8. Mã hàng có hậu tố {DEL} là mã đã bị xoá rồi tạo lại với cùng mã: bỏ hậu tố
--     để gộp lịch sử bán của bản cũ và bản mới (cùng một sản phẩm), giữ cờ sku_deleted.
-- =====================================================================

CREATE OR REPLACE TABLE stg_sales_lines AS
WITH deduped AS (
    SELECT *
    FROM raw_sales_lines
    QUALIFY row_number() OVER (
        PARTITION BY invoice_id, sold_at, sku
        ORDER BY loaded_at DESC
    ) = 1
),

-- Sửa các giá trị nhóm hàng cấp 1 không chuẩn (nằm sai cấp, gõ sai, đã xoá).
category_fixes(raw_path, fixed_path) AS (
    VALUES
        ('Gạo',               'Gạo, bột và thực phẩm khô>>Gạo>>Gạo'),
        ('Dưỡng Thể',         'Chăm sóc cá nhân>>Chăm sóc cơ thể>>Dưỡng thể'),
        ('Dung Dịch Vệ Sinh', 'Chăm sóc cá nhân>>Chăm sóc cơ thể>>Dung dịch vệ sinh'),
        ('Bánh{DEL}',         'Bánh, kẹo, snack>>Bánh>>Bánh Tổng Hợp'),
        ('chưa khai báo',     'Chưa phân loại>>Chưa phân loại>>Chưa phân loại')
),

base AS (
    SELECT
        d.*,
        replace(coalesce(f.fixed_path, trim(d.category_path)),
                'Khuyến mại khai chương', 'Khuyến mại khai trương') AS category_clean,
        lower(trim(d.note)) AS note_lc
    FROM deduped d
    LEFT JOIN category_fixes f ON trim(d.category_path) = f.raw_path
),

-- Ẩn danh người bán: đánh số theo số dòng bán, nhiều nhất là NV01.
seller_codes AS (
    SELECT
        seller,
        'NV' || lpad(CAST(row_number() OVER (ORDER BY count(*) DESC, seller) AS VARCHAR), 2, '0')
            AS seller_code
    FROM base
    GROUP BY seller
),

-- Giá vốn tham chiếu của từng mã hàng (chỉ tính trên các dòng có giá vốn > 0).
sku_cost AS (
    SELECT sku, median(unit_cost) AS median_cost
    FROM base
    WHERE unit_cost > 0
    GROUP BY sku
),

-- Tỷ lệ giá vốn / giá bán trung vị của từng nhóm hàng (dự phòng khi mã hàng
-- chưa từng có giá vốn).
category_cost_ratio AS (
    SELECT category_clean, median(unit_cost / unit_price) AS cost_ratio
    FROM base
    WHERE unit_cost > 0 AND unit_price > 0
    GROUP BY category_clean
),

-- Số lượng mua điển hình của từng mã hàng, để phát hiện đơn số lượng lớn.
sku_qty AS (
    SELECT sku, median(quantity) AS median_qty
    FROM base
    WHERE quantity > 0
    GROUP BY sku
),

lines AS (
    SELECT
        -- Định danh hoá đơn
        b.invoice_id,
        split_part(b.invoice_id, '.', 1)                        AS invoice_base_id,
        CASE WHEN b.invoice_id LIKE 'TH%' THEN 'return' ELSE 'sale' END AS invoice_type,
        b.invoice_id LIKE '%.%'                                 AS is_edited_invoice,

        -- Thời gian
        b.sold_at,
        CAST(b.sold_at AS DATE)                                 AS sale_date,
        hour(b.sold_at)                                         AS sale_hour,
        isodow(b.sold_at)                                       AS iso_weekday,  -- 1 = Thứ Hai

        -- Cửa hàng, người bán
        b.branch,
        s.seller_code,
        b.seller NOT LIKE '%{DEL}%'                             AS seller_active,

        -- Sản phẩm
        replace(b.sku, '{DEL}', '')                             AS sku,
        b.sku LIKE '%{DEL}%'                                    AS sku_deleted,
        b.barcode,
        trim(b.product_name)                                    AS product_name,
        coalesce(nullif(trim(b.brand), ''), 'Không rõ')         AS brand,
        b.category_clean                                        AS category_path,
        split_part(b.category_clean, '>>', 1)                   AS cat_l1,
        coalesce(nullif(split_part(b.category_clean, '>>', 2), ''),
                 split_part(b.category_clean, '>>', 1))         AS cat_l2,
        coalesce(nullif(split_part(b.category_clean, '>>', 3), ''),
                 nullif(split_part(b.category_clean, '>>', 2), ''),
                 split_part(b.category_clean, '>>', 1))         AS cat_l3,

        -- Số lượng, giá
        b.quantity,
        b.unit_price,
        b.unit_cost,
        CASE
            WHEN b.unit_cost > 0 THEN b.unit_cost
            WHEN c.median_cost IS NOT NULL THEN c.median_cost
            ELSE b.unit_price * r.cost_ratio
        END                                                     AS unit_cost_filled,
        b.unit_cost = 0                                         AS cost_missing,
        CASE
            WHEN b.unit_cost > 0 THEN 'actual'
            WHEN c.median_cost IS NOT NULL THEN 'sku_median'
            WHEN r.cost_ratio IS NOT NULL THEN 'category_ratio'
        END                                                     AS cost_fill_method,

        -- Ghi chú (giữ ở tầng staging, KHÔNG đưa ra ứng dụng vì có tên người thật)
        b.note,
        b.note_lc,
        q.median_qty
    FROM base b
    LEFT JOIN seller_codes s USING (seller)
    LEFT JOIN sku_cost     c ON c.sku = b.sku
    LEFT JOIN category_cost_ratio r ON r.category_clean = b.category_clean
    LEFT JOIN sku_qty      q ON q.sku = b.sku
)

SELECT
    * EXCLUDE (note_lc, median_qty),

    -- Doanh thu, giá vốn, lợi nhuận tính lại ở mức dòng
    quantity * unit_price                                       AS line_revenue,
    quantity * unit_cost_filled                                 AS line_cogs,
    quantity * (unit_price - unit_cost_filled)                  AS line_profit,

    -- Cờ chất lượng / loại giao dịch
    invoice_type = 'return'                                     AS is_return,
    unit_price = 0 AND invoice_type = 'sale'                    AS is_zero_price,
    cat_l1 = 'Khuyến mại khai trương'                           AS is_opening_promo,
    quantity <> floor(quantity)                                 AS is_fractional_qty,
    coalesce(note_lc LIKE '%nợ%' OR note_lc LIKE '%chưa tt%', false) AS is_credit_sale,

    CASE
        WHEN regexp_matches(coalesce(note_lc, ''),
             'nội bộ|hàng mẫu|lấy mẫu|xuất mẫu|làm hàng mẫu|nhà cung cấp|nhà phân phối|chuyển về kho|livestream|đi quay')
            THEN 'internal'
        WHEN regexp_matches(coalesce(note_lc, ''),
             'cty|công ty|công đoàn|ub xã|huyndai|hyundai|vinfast|hải thịnh|dolee|set quà|dính kế')
            THEN 'organization'
        -- Ngưỡng 48 = 2 thùng 24: mua 1 thùng (24 lon/chai) vẫn là hành vi bán lẻ
        -- bình thường ở cửa hàng tạp hoá, đặc biệt dịp lễ Tết.
        WHEN invoice_type = 'sale' AND quantity >= 48 AND quantity >= 10 * median_qty
            THEN 'bulk'
        ELSE 'retail'
    END                                                         AS txn_channel
FROM lines;
