"""Báo cáo chất lượng dữ liệu.

Chạy các phép kiểm tra trên bảng raw và staging, rồi ghi kết quả ra
docs/data_quality_report.md. Báo cáo chỉ chứa số liệu tổng hợp, không chứa
tên người, nên an toàn để đưa lên GitHub.
"""

from __future__ import annotations

from datetime import datetime

import duckdb
import pandas as pd


def _one(con: duckdb.DuckDBPyConnection, sql: str):
    return con.execute(sql).fetchone()


def _df(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return con.execute(sql).df()


def _vnd(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def _num(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def _pct(x: float) -> str:
    return f"{x:.1%}".replace(".", ",")


def _table(df: pd.DataFrame) -> str:
    header = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    rows = ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join([header, sep, *rows])


def build_report(con: duckdb.DuckDBPyConnection) -> str:
    out: list[str] = []
    add = out.append

    raw_n, stg_n = _one(con, "SELECT (SELECT count(*) FROM raw_sales_lines), (SELECT count(*) FROM stg_sales_lines)")
    d0, d1, n_inv, n_sku = _one(con, """
        SELECT min(sale_date), max(sale_date), count(DISTINCT invoice_id), count(DISTINCT sku)
        FROM stg_sales_lines""")
    total_rev = _one(con, "SELECT sum(line_revenue) FROM stg_sales_lines")[0]

    add("# Báo cáo chất lượng dữ liệu\n")
    add(f"_Sinh tự động bởi `python -m hasu.pipeline` lúc {datetime.now():%d/%m/%Y %H:%M}._\n")
    add("## 1. Tổng quan\n")
    add(_table(pd.DataFrame([
        ["Khoảng thời gian", f"{d0:%d/%m/%Y} – {d1:%d/%m/%Y}"],
        ["Số dòng (raw → staging)", f"{_num(raw_n)} → {_num(stg_n)}"],
        ["Dòng trùng lặp đã loại", _num(raw_n - stg_n)],
        ["Số hoá đơn", _num(n_inv)],
        ["Số mã hàng", _num(n_sku)],
        ["Doanh thu thuần (tính lại ở mức dòng)", _vnd(total_rev) + " đ"],
    ], columns=["Chỉ số", "Giá trị"])))

    # --- Đối soát doanh thu ---
    add("\n## 2. Đối soát doanh thu\n")
    add("Doanh thu được tính lại ở mức dòng (`số lượng × giá bán`) rồi so với các con số "
        "tổng mà KiotViet đã tính sẵn. Nếu khớp, việc làm sạch không làm mất hay nhân đôi tiền.\n")
    monthly = _df(con, """
        WITH kv AS (
            SELECT period_month, any_value(month_revenue) AS kv_revenue
            FROM raw_sales_lines GROUP BY 1
        ), ours AS (
            SELECT strftime(sale_date, '%m-%Y') AS period_month, sum(line_revenue) AS our_revenue
            FROM stg_sales_lines GROUP BY 1
        )
        SELECT kv.period_month, kv_revenue, our_revenue, our_revenue - kv_revenue AS diff
        FROM kv JOIN ours USING (period_month)
        ORDER BY right(period_month, 4), left(period_month, 2)""")
    max_diff = monthly["diff"].abs().max()
    monthly_fmt = pd.DataFrame({
        "Tháng": monthly["period_month"],
        "Doanh thu KiotViet": monthly["kv_revenue"].map(_vnd),
        "Doanh thu tính lại": monthly["our_revenue"].map(_vnd),
        "Chênh lệch": monthly["diff"].map(_vnd),
    })
    add(_table(monthly_fmt))
    add(f"\nChênh lệch lớn nhất giữa các tháng: **{_vnd(max_diff)} đ** "
        "(do KiotViet làm tròn giá bán sau khi phân bổ giảm giá hoá đơn).\n")

    inv_match = _one(con, """
        WITH x AS (
            SELECT invoice_id, sum(quantity * unit_price) AS s, any_value(invoice_revenue) AS r
            FROM raw_sales_lines GROUP BY 1
        )
        SELECT avg(CASE WHEN abs(s - r) <= 1 THEN 1 ELSE 0 END),
               avg(CASE WHEN abs(s - r) <= 100 THEN 1 ELSE 0 END)
        FROM x""")
    add(f"Ở mức hoá đơn: {_pct(inv_match[0])} số hoá đơn khớp tuyệt đối (lệch ≤ 1 đ), "
        f"{_pct(inv_match[1])} khớp trong phạm vi 100 đ. Điều này xác nhận **giá bán trên từng dòng "
        "đã là giá sau giảm giá hoá đơn**, nên doanh thu dòng = số lượng × giá bán là đúng.\n")

    # --- Các vấn đề phát hiện ---
    add("## 3. Các vấn đề phát hiện và cách xử lý\n")
    issues = _df(con, """
        SELECT 'Phiếu trả hàng (mã TH, số lượng âm)' AS issue,
               count(*) FILTER (is_return) AS n_lines,
               sum(line_revenue) FILTER (is_return) AS revenue,
               'Giữ lại, gắn cờ is_return; doanh thu thuần đã trừ hàng trả' AS action
        FROM stg_sales_lines
        UNION ALL
        SELECT 'Hoá đơn đã sửa (mã có đuôi .01, .02...)', count(*) FILTER (is_edited_invoice),
               sum(line_revenue) FILTER (is_edited_invoice),
               'Giữ lại: bản gốc không có trong file nên không bị đếm hai lần'
        FROM stg_sales_lines
        UNION ALL
        SELECT 'Giá vốn = 0 (thiếu giá vốn)', count(*) FILTER (cost_missing),
               sum(line_revenue) FILTER (cost_missing),
               'Điền bằng trung vị giá vốn của mã hàng, dự phòng bằng tỷ lệ giá vốn của nhóm hàng'
        FROM stg_sales_lines
        UNION ALL
        SELECT 'Giá bán = 0 trên hoá đơn bán', count(*) FILTER (is_zero_price),
               sum(line_revenue) FILTER (is_zero_price),
               'Gắn cờ is_zero_price (chủ yếu hàng tặng khai trương)'
        FROM stg_sales_lines
        UNION ALL
        SELECT 'Hàng khuyến mại khai trương', count(*) FILTER (is_opening_promo),
               sum(line_revenue) FILTER (is_opening_promo),
               'Gắn cờ is_opening_promo; sửa lỗi chính tả "khai chương"'
        FROM stg_sales_lines
        UNION ALL
        SELECT 'Số lượng lẻ (hàng cân theo kg)', count(*) FILTER (is_fractional_qty),
               sum(line_revenue) FILTER (is_fractional_qty),
               'Hợp lệ, giữ nguyên'
        FROM stg_sales_lines
        UNION ALL
        SELECT 'Thiếu thương hiệu', count(*) FILTER (brand = 'Không rõ'),
               sum(line_revenue) FILTER (brand = 'Không rõ'),
               'Điền "Không rõ"; không dùng thương hiệu làm biến dự báo'
        FROM stg_sales_lines
        UNION ALL
        SELECT 'Mã hàng bị xoá rồi tạo lại (hậu tố {DEL})', count(*) FILTER (sku_deleted),
               sum(line_revenue) FILTER (sku_deleted),
               'Bỏ hậu tố để gộp lịch sử bán của bản cũ và bản mới; giữ cờ sku_deleted'
        FROM stg_sales_lines
        UNION ALL
        SELECT 'Bán chịu (ghi chú "nợ", "chưa tt")', count(*) FILTER (is_credit_sale),
               sum(line_revenue) FILTER (is_credit_sale),
               'Vẫn là nhu cầu thật; gắn cờ is_credit_sale'
        FROM stg_sales_lines""")
    issues["Tỷ lệ doanh thu"] = (issues["revenue"].abs() / total_rev).map(_pct)
    issues["n_lines"] = issues["n_lines"].map(_num)
    issues["revenue"] = issues["revenue"].fillna(0).map(_vnd)
    issues.columns = ["Vấn đề", "Số dòng", "Doanh thu (đ)", "Cách xử lý", "Tỷ lệ doanh thu"]
    add(_table(issues[["Vấn đề", "Số dòng", "Doanh thu (đ)", "Tỷ lệ doanh thu", "Cách xử lý"]]))

    cost = _df(con, """
        SELECT coalesce(cost_fill_method, 'không điền được') AS m, count(*) AS n
        FROM stg_sales_lines WHERE cost_missing GROUP BY 1 ORDER BY 2 DESC""")
    add("\nCách điền giá vốn bị thiếu: " + ", ".join(f"`{m}` {n} dòng" for m, n in cost.itertuples(index=False))
        + ". Các dòng không điền được bị loại khỏi phân tích biên lợi nhuận.\n")

    # --- Nhóm hàng ---
    add("## 4. Nhóm hàng\n")
    cat = _one(con, """
        SELECT count(DISTINCT cat_l1), count(DISTINCT cat_l2), count(DISTINCT cat_l3),
               count(*) FILTER (category_path NOT LIKE '%>>%>>%')
        FROM stg_sales_lines""")
    fixed = _one(con, """
        SELECT count(*) FROM raw_sales_lines
        WHERE trim(category_path) IN ('Gạo', 'Dưỡng Thể', 'Dung Dịch Vệ Sinh', 'Bánh{DEL}', 'chưa khai báo')""")[0]
    add(f"- Sau làm sạch: **{cat[0]} nhóm cấp 1, {cat[1]} nhóm cấp 2, {cat[2]} nhóm cấp 3**.\n"
        f"- {_num(fixed)} dòng có nhóm hàng không chuẩn (nằm sai cấp, đã bị xoá, \"chưa khai báo\") "
        "được ánh xạ về đúng cây nhóm hàng.\n"
        f"- {_num(cat[3])} dòng chỉ có 1–2 cấp: cấp còn thiếu được lấy theo cấp trên "
        "(ví dụ `Thực phẩm đông mát>>Kem` → cấp 3 = `Kem`).\n")

    # --- Loại giao dịch ---
    add("## 5. Loại giao dịch: không phải dòng nào cũng là nhu cầu bán lẻ\n")
    add("Ghi chú hoá đơn và số lượng bất thường cho thấy một phần giao dịch không phản ánh "
        "nhu cầu mua lẻ hằng ngày. Nếu đưa nguyên vào mô hình, các đơn này sẽ tạo ra những "
        "\"đỉnh\" giả mà mô hình không thể và không nên học theo.\n")
    ch = _df(con, """
        SELECT txn_channel, count(*) AS n, count(DISTINCT invoice_id) AS inv,
               sum(quantity) AS qty, sum(line_revenue) AS rev
        FROM stg_sales_lines GROUP BY 1 ORDER BY rev DESC""")
    labels = {
        "retail": "Bán lẻ",
        "bulk": "Đơn lớn (hoá đơn ≥ 100 sản phẩm hoặc ≥ 3 triệu đ; hoặc dòng ≥ 48 và ≥ 10 lần mức mua điển hình)",
        "organization": "Đơn tổ chức / công ty (theo ghi chú)",
        "internal": "Nội bộ: hàng mẫu, trả NCC, chuyển kho (theo ghi chú)",
    }
    add(_table(pd.DataFrame({
        "Loại": ch["txn_channel"].map(labels),
        "Số dòng": ch["n"].map(_num),
        "Số hoá đơn": ch["inv"].map(_num),
        "Tỷ lệ số lượng": (ch["qty"] / ch["qty"].sum()).map(_pct),
        "Tỷ lệ doanh thu": (ch["rev"] / ch["rev"].sum()).map(_pct),
    })))
    add("\n**Hệ quả:** mô hình dự báo nhu cầu bán lẻ sẽ chỉ dùng loại `Bán lẻ`. Đơn số lượng lớn và "
        "đơn tổ chức được phân tích riêng như một kênh bán sỉ.\n")

    # --- Lịch ---
    add("## 6. Tính liên tục theo thời gian\n")
    closed = _df(con, "SELECT date FROM dim_date WHERE NOT is_open ORDER BY date")
    n_days, n_open = _one(con, "SELECT count(*), count(*) FILTER (is_open) FROM dim_date")
    add(f"- {_num(n_days)} ngày trong khoảng dữ liệu, cửa hàng có bán hàng {_num(n_open)} ngày.\n"
        f"- {len(closed)} ngày không có giao dịch: "
        + ", ".join(f"{d:%d/%m/%Y}" for d in closed["date"]) + ".\n"
        "- Chuỗi 16–23/02/2026 trùng kỳ nghỉ Tết Bính Ngọ (mùng 1 Tết = 17/02/2026); "
        "30/04–01/05 là nghỉ lễ. Các ngày này được đánh dấu `is_open = false` trong `dim_date` "
        "và **không** được coi là nhu cầu bằng 0.\n"
        f"- Tháng đầu tiên chỉ có dữ liệu từ {d0:%d/%m/%Y}, nên tổng tháng 09/2025 không so sánh "
        "trực tiếp được với các tháng khác.\n")

    # --- Độ thưa ---
    add("## 7. Độ thưa của dữ liệu bán\n")
    sp = _one(con, """
        WITH open_days AS (SELECT count(*) AS n FROM dim_date WHERE is_open),
        sku AS (
            SELECT sku, count(DISTINCT sale_date) AS d FROM stg_sales_lines
            WHERE txn_channel = 'retail' AND NOT is_return GROUP BY 1
        ),
        cat AS (
            SELECT cat_l3, count(DISTINCT sale_date) AS d FROM stg_sales_lines
            WHERE txn_channel = 'retail' AND NOT is_return GROUP BY 1
        )
        SELECT
            (SELECT avg(CASE WHEN d < 0.1 * n THEN 1 ELSE 0 END) FROM sku, open_days),
            (SELECT count(*) FILTER (d >= 0.5 * n) FROM sku, open_days),
            (SELECT count(*) FILTER (d >= 0.5 * n) FROM cat, open_days),
            (SELECT count(*) FROM cat)""")
    add(f"Chỉ tính bán lẻ, trên các ngày cửa hàng mở cửa:\n\n"
        f"- {_pct(sp[0])} mã hàng bán ra dưới 10% số ngày.\n"
        f"- Chỉ {sp[1]} mã hàng bán ra từ 50% số ngày trở lên.\n"
        f"- Ở cấp nhóm hàng 3: {sp[2]}/{sp[3]} nhóm bán ra từ 50% số ngày trở lên.\n\n"
        "→ Cần dự báo phân tầng theo mức độ đầy đủ dữ liệu, và dùng mô hình cho nhu cầu "
        "gián đoạn (intermittent demand) ở các nhóm thưa.\n")

    return "\n".join(out)
