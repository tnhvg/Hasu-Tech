import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import lib
from hasu import viz

lib.header("Phân tích kinh doanh",
           "Quyết định vận hành dùng số lượng; quyết định tài chính dùng doanh thu và lợi nhuận.",
           section="Phân tích")

tabs = st.tabs(["Xu hướng", "ABC", "Giờ × thứ", "Biên lợi nhuận", "Tết", "Giỏ hàng", "Nghi ngờ hết hàng"])

# ---------------------------------------------------------------- Xu hướng
with tabs[0]:
    m = lib.q("SELECT * FROM mart_monthly WHERE channel <> 'Nội bộ' ORDER BY year_month")
    traffic = lib.q("""
        SELECT strftime(date, '%Y-%m') AS year_month, sum(n_invoices) / count(*) AS inv_per_day,
               sum(revenue) / sum(n_invoices) AS basket
        FROM mart_daily_traffic GROUP BY 1 ORDER BY 1""")
    metric = st.radio("Thước đo", ["Doanh thu / ngày mở cửa", "Lợi nhuận gộp", "Số hoá đơn"], horizontal=True)
    col = {"Doanh thu / ngày mở cửa": "revenue_per_open_day", "Lợi nhuận gộp": "profit", "Số hoá đơn": "n_invoices"}[metric]
    fig = go.Figure()
    for i, ch in enumerate(["Bán lẻ", "Đơn lớn / tổ chức"]):
        d = m[m["channel"] == ch]
        fig.add_bar(x=[lib.month_label(x) for x in d["year_month"]], y=d[col], name=ch, marker_color=viz.SERIES[i])
    lib.show(fig, barmode="stack", title=f"{metric} theo tháng và kênh bán", yaxis_tickformat=",.0f")
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Scatter(x=[lib.month_label(x) for x in traffic["year_month"]], y=traffic["inv_per_day"], mode="lines+markers",
                                   line=dict(color=viz.SERIES[0])))
        lib.show(fig, 280, title="Hoá đơn bán lẻ trung bình / ngày")
    with c2:
        fig = go.Figure(go.Scatter(x=[lib.month_label(x) for x in traffic["year_month"]], y=traffic["basket"], mode="lines+markers",
                                   line=dict(color=viz.SERIES[0])))
        lib.show(fig, 280, title="Giá trị trung bình mỗi hoá đơn bán lẻ (đ)", yaxis_tickformat=",.0f")
    early, late = traffic["inv_per_day"].iloc[:-2].mean(), traffic["inv_per_day"].iloc[-2:].mean()
    lib.alert("info", f"<b>Nhận xét:</b> 2 tháng gần nhất có trung bình <b>{lib.num(late)} hoá đơn/ngày</b>, so với "
              f"{lib.num(early)} các tháng trước ({lib.pct(late / early - 1, 0)}), trong khi giá trị mỗi hoá đơn "
              "gần như không đổi. Thay đổi đến từ <b>lượng khách</b>, không phải mức chi tiêu mỗi khách.")

# ---------------------------------------------------------------- ABC
with tabs[1]:
    abc = lib.q("SELECT * FROM mart_sku_abc ORDER BY qty_rank")
    n_a = int((abc["abc_class"] == "A").sum())
    abc_desc = {"A": ("Nhóm A: ưu tiên cao nhất", "workspace_premium", ""),
                "B": ("Nhóm B", "inventory", "orange"), "C": ("Nhóm C: bán ít", "low_priority", "violet")}
    lib.kpis([{"label": abc_desc[k][0], "value": f"{lib.num(len(abc[abc['abc_class'] == k]))} mã",
               "icon": abc_desc[k][1], "tone": abc_desc[k][2],
               "note": f"Chiếm <b>{lib.pct(abc.loc[abc['abc_class'] == k, 'quantity'].sum() / abc['quantity'].sum(), 0)}</b> số lượng bán lẻ"}
              for k in "ABC"])
    fig = go.Figure(go.Scatter(x=abc["qty_rank"], y=abc["cum_qty_share"], mode="lines",
                               line=dict(color=viz.SERIES[0]), hovertemplate="%{x} mã: %{y:.1%}<extra></extra>"))
    fig.add_hline(y=0.8, line_dash="dot", line_color=viz.MUTED)
    fig.add_vline(x=n_a, line_dash="dot", line_color=viz.MUTED)
    lib.show(fig, 320, title="Đường Pareto: tỷ lệ số lượng bán lẻ cộng dồn", yaxis_tickformat=".0%",
             xaxis_title="Số mã hàng (xếp theo số lượng giảm dần)", hovermode="closest")
    cls = st.segmented_control("Lọc nhóm", ["A", "B", "C"], default="A")
    view = abc[abc["abc_class"] == (cls or "A")][["qty_rank", "product_name", "cat_l3", "quantity", "revenue",
                                                  "sell_day_ratio", "last_sale"]].round({"revenue": 0})
    with lib.card():
        st.dataframe(view, hide_index=True, width="stretch", column_config={
        "qty_rank": "Hạng", "product_name": "Mã hàng", "cat_l3": "Nhóm hàng",
        "quantity": st.column_config.NumberColumn("Số lượng", format="%.0f"),
        "revenue": st.column_config.NumberColumn("Doanh thu (đ)", format="localized"),
        "sell_day_ratio": st.column_config.ProgressColumn("% ngày có bán", format="%.0f%%", min_value=0, max_value=1),
        "last_sale": "Lần bán cuối"})
    lib.note("ABC theo SỐ LƯỢNG bán lẻ vì đây là căn cứ ưu tiên dự báo và tồn kho.")

# ---------------------------------------------------------------- Giờ × thứ
with tabs[2]:
    h = lib.q("SELECT * FROM mart_hour_weekday")
    measure = st.radio("Hiển thị", ["Số hoá đơn / giờ", "Doanh thu / giờ"], horizontal=True)
    grid = h.pivot(index="iso_weekday", columns="sale_hour",
                   values="avg_invoices" if measure.startswith("Số") else "avg_revenue").fillna(0)
    grid = grid.loc[:, [c for c in grid.columns if 6 <= c <= 21]]
    days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]
    fig = go.Figure(go.Heatmap(z=grid.values, x=[f"{c}h" for c in grid.columns], y=days[:len(grid)],
                               colorscale=[[0, "#f0efec"]] + [[(i + 1) / len(viz.BLUE_RAMP), c]
                                                             for i, c in enumerate(viz.BLUE_RAMP)],
                               xgap=2, ygap=2, hovertemplate="%{y} %{x}: %{z:,.1f}<extra></extra>",
                               colorbar=dict(thickness=10)))
    lib.show(fig, 340, title=f"{measure} trung bình theo thứ và giờ", hovermode="closest",
             yaxis=dict(autorange="reversed", showgrid=False))
    by_hour = h.groupby("sale_hour")["avg_invoices"].mean()
    lib.alert("info", f"<b>Cao điểm:</b> {by_hour.idxmax()}h ({lib.num(by_hour.max(), 1)} hoá đơn/giờ). "
              f"<b>Thấp điểm ban ngày:</b> {by_hour.loc[12:15].idxmin()}h. "
              "Gợi ý: đủ người đứng quầy 16h–19h và 7h–9h; nhận hàng, kiểm kho vào 13h–15h.")

# ---------------------------------------------------------------- Biên lợi nhuận
with tabs[3]:
    cm = lib.q("SELECT * FROM mart_category_margin")
    colors = {"Ngôi sao": viz.SERIES[0], "Lời mỏng": viz.SERIES[1], "Tiềm năng": viz.SERIES[2],
              "Cần xem xét": viz.NEUTRAL, "Thua lỗ": viz.CRITICAL}
    fig = go.Figure()
    for qd, c in colors.items():
        d = cm[cm["quadrant"] == qd]
        fig.add_scatter(x=d["revenue"], y=d["margin"], mode="markers", name=qd, text=d["cat_l2"],
                        marker=dict(color=c, size=10, line=dict(color="white", width=1.5),
                                    symbol="x" if qd == "Thua lỗ" else "circle"),
                        hovertemplate="<b>%{text}</b><br>Doanh thu %{x:,.0f} đ<br>Biên %{y:.1%}<extra></extra>")
    fig.add_hline(y=cm["store_margin"].iloc[0], line_dash="dot", line_color=viz.MUTED)
    fig.add_vline(x=cm["rev_median"].iloc[0], line_dash="dot", line_color=viz.MUTED)
    lib.show(fig, 440, title="Doanh thu × biên lợi nhuận theo nhóm hàng cấp 2", hovermode="closest",
             xaxis=dict(type="log", title="Doanh thu (thang log)", showgrid=False),
             yaxis=dict(tickformat=".0%", title="Biên lợi nhuận gộp", gridcolor="rgba(128,128,128,0.18)"))
    with lib.card():
      st.dataframe(cm[["cat_l2", "cat_l1", "quadrant", "revenue", "profit", "margin", "retail_share"]]
                 .round({"revenue": 0, "profit": 0}).sort_values("profit"), hide_index=True, width="stretch", column_config={
        "cat_l2": "Nhóm hàng", "cat_l1": "Ngành", "quadrant": "Phân nhóm",
        "revenue": st.column_config.NumberColumn("Doanh thu (đ)", format="localized"),
        "profit": st.column_config.NumberColumn("Lợi nhuận gộp (đ)", format="localized"),
        "margin": st.column_config.NumberColumn("Biên", format="percent"),
        "retail_share": st.column_config.NumberColumn("Tỷ trọng bán lẻ", format="percent")})
    lib.note("Nhóm thua lỗ cần đối chiếu hoá đơn nhập: giá vốn trong KiotViet có thể bị nhập sai đơn vị.")

# ---------------------------------------------------------------- Tết
with tabs[4]:
    tet = lib.q("SELECT * FROM mart_tet_effect")
    tot = tet[tet["cat_l1"] == "Toàn cửa hàng"].set_index("tet_window")
    lib.kpis([
        {"label": "Doanh thu 14 ngày trước Tết", "value": f"× {lib.num(tot.loc['Trước Tết', 'rev_factor'], 2)}",
         "icon": "trending_up", "note": "So với ngày mở cửa bình thường"},
        {"label": "Số lượng 14 ngày trước Tết", "value": f"× {lib.num(tot.loc['Trước Tết', 'qty_factor'], 2)}",
         "icon": "shopping_cart", "tone": "orange", "note": "Khách mua hàng đắt hơn, không nhiều hơn hẳn"},
        {"label": "Số ngày nghỉ Tết", "value": "7 ngày", "icon": "event_busy", "tone": "violet",
         "note": "16/02 – 23/02/2026, không tính là nhu cầu 0"},
    ])
    pre = tet[(tet["tet_window"] == "Trước Tết") & (tet["cat_l1"] != "Toàn cửa hàng") & (tet["rev_per_day"] > 50000)]
    pre = pre.sort_values("rev_factor")
    fig = go.Figure()
    fig.add_bar(y=pre["cat_l1"], x=pre["qty_factor"], name="Hệ số số lượng", orientation="h",
                marker_color=viz.SERIES[0])
    fig.add_bar(y=pre["cat_l1"], x=pre["rev_factor"], name="Hệ số doanh thu", orientation="h",
                marker_color=viz.SERIES[1])
    fig.add_vline(x=1, line_color=viz.MUTED)
    lib.show(fig, 420, barmode="group", title="Hệ số Tết theo ngành hàng (14 ngày trước Tết)", hovermode="y unified")
    lib.alert("info", "<b>Nhập hàng Tết theo hệ số số lượng</b>, không theo hệ số doanh thu: doanh thu tăng chủ yếu "
              "do khách mua hàng giá trị cao hơn. Chỉ có một kỳ Tết trong dữ liệu, hệ số sẽ được cập nhật qua các năm.")

# ---------------------------------------------------------------- Giỏ hàng
with tabs[5]:
    rules = lib.q("SELECT * FROM mart_basket_rules ORDER BY lift DESC")
    st.caption(f"FP-Growth trên {lib.num(rules['total_multi_item_baskets'].iloc[0])} hoá đơn bán lẻ có từ 2 nhóm hàng, "
               "đã loại các dòng bán dưới giá phổ biến (khuyến mãi).")
    with lib.card():
      st.dataframe(rules[["antecedent", "consequent", "n_baskets", "confidence", "lift"]], hide_index=True,
                 width="stretch", column_config={
        "antecedent": "Nếu mua", "consequent": "Thì thường mua", "n_baskets": "Số hoá đơn",
        "confidence": st.column_config.NumberColumn("Độ tin cậy", format="percent"),
        "lift": st.column_config.NumberColumn("Lift", format="%.2f")})
    st.markdown("- **Lift** > 1: mua A làm tăng khả năng mua B. **Độ tin cậy**: trong các hoá đơn có A, bao nhiêu % có B.\n"
                "- `Dụng cụ bếp khác` thực chất là **bật lửa** (xếp nhầm nhóm): bày cạnh quầy thuốc lá.\n"
                "- Mì + xúc xích ăn liền, thuốc lá + nước giải khát, sữa tươi + bánh: gợi ý combo / bày kệ cạnh nhau.\n"
                "- Các cặp như *Mì ăn liền* với *Mì, bún, phở...* là cùng loại hàng bị chia hai nhóm, không phải mua kèm.")

# ---------------------------------------------------------------- Hết hàng
with tabs[6]:
    so = lib.q("SELECT * FROM mart_stockout_suspects ORDER BY gap_open_days DESC")
    st.markdown("Mã hàng bán đều (≥ 15% số ngày) bỗng không bán nhiều ngày mở cửa liên tiếp, với xác suất xảy ra "
                "ngẫu nhiên dưới 1%. **Đây là suy đoán**: hàng theo mùa và hàng ngừng kinh doanh cũng trông giống vậy.")
    status = st.multiselect("Đánh giá", so["status"].unique().tolist(), default=so["status"].unique().tolist())
    with lib.card():
      st.dataframe(so[so["status"].isin(status)][["product_name", "cat_l3", "gap_start", "gap_end", "gap_open_days",
                                                "sell_day_ratio", "status"]],
                 hide_index=True, width="stretch", column_config={
        "product_name": "Mã hàng", "cat_l3": "Nhóm hàng", "gap_start": "Từ", "gap_end": "Đến",
        "gap_open_days": "Số ngày không bán", "sell_day_ratio": st.column_config.NumberColumn("% ngày có bán", format="percent"),
        "status": "Đánh giá"})
