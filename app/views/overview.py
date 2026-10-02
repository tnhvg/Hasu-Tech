import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import lib
from hasu import viz

lib.header("Tổng quan cửa hàng", "Bức tranh kinh doanh, các điểm cần chú ý và kế hoạch nhập hàng tuần tới.",
           section="Tổng quan")

monthly = lib.q("SELECT * FROM mart_monthly")
info = lib.q("SELECT * FROM fc_run_info").iloc[0] if lib.has_table("fc_run_info") else None

# ---- Chỉ số chính ----
sales = monthly[monthly["channel"] != "Nội bộ"]
rev, profit = sales["revenue"].sum(), sales["profit"].sum()
daily = lib.q("""
    SELECT date, sum(quantity) AS qty, sum(revenue) AS revenue, sum(n_invoices) AS n_invoices
    FROM fct_retail_daily_category GROUP BY 1 ORDER BY 1""")
daily["date"] = pd.to_datetime(daily["date"])
last4 = daily[daily["date"] > daily["date"].max() - pd.Timedelta(days=28)]
prev4 = daily[(daily["date"] <= daily["date"].max() - pd.Timedelta(days=28))
              & (daily["date"] > daily["date"].max() - pd.Timedelta(days=56))]
inv_now = last4["n_invoices"].mean()

items = [
    {"label": "Doanh thu thuần", "value": lib.vnd(rev), "icon": "payments",
     "note": "Bán lẻ + đơn lớn, đã trừ hàng trả"},
    {"label": "Lợi nhuận gộp", "value": lib.vnd(profit), "icon": "account_balance_wallet", "tone": "green",
     "note": f"Biên lợi nhuận gộp <b>{lib.pct(profit / rev)}</b>"},
    {"label": "Hoá đơn bán lẻ / ngày", "value": lib.num(inv_now), "icon": "receipt_long", "tone": "orange",
     "note": lib.delta(inv_now / prev4["n_invoices"].mean() - 1, " so với 4 tuần trước")},
]
if info is not None:
    items.append({"label": "Độ chính xác dự báo", "value": lib.pct(1 - info["store_wmape"], 0),
                  "icon": "target", "tone": "violet", "note": "Tổng toàn cửa hàng, 8 tuần kiểm định"})
lib.kpis(items)

# ---- Cảnh báo ----
lib.section("Cần chú ý", "notifications_active")
loss = lib.q("SELECT cat_l2, profit FROM mart_category_margin WHERE quadrant = 'Thua lỗ' ORDER BY profit")
if len(loss):
    lib.alert("critical", f"<b>{len(loss)} nhóm hàng đang bán lỗ</b>. Lỗ nhiều nhất: "
              + ", ".join(f"{r.cat_l2} ({lib.vnd(r.profit)})" for r in loss.head(3).itertuples())
              + ". Xem <i>Phân tích kinh doanh → Biên lợi nhuận</i>.")
drop = inv_now / daily["n_invoices"].mean() - 1
if drop < -0.15:
    lib.alert("warning", f"<b>Lượng khách bán lẻ 4 tuần gần nhất thấp hơn {lib.pct(-drop, 0)}</b> so với trung bình "
                         "cả kỳ, trong khi giá trị mỗi hoá đơn gần như không đổi.")
if lib.has_table("mart_stockout_suspects"):
    so = lib.q("SELECT count(DISTINCT sku) AS n FROM mart_stockout_suspects WHERE status LIKE 'Không bán tới cuối%'")
    if so["n"].iloc[0]:
        lib.alert("warning", f"<b>{so['n'].iloc[0]} mã hàng bán đều đã ngừng bán tới cuối kỳ</b>: có thể đang hết "
                             "hàng. Xem <i>Phân tích kinh doanh → Nghi ngờ hết hàng</i>.")
if info is not None:
    plan_sum = lib.q("SELECT sum(order_value) AS v, count(*) FILTER (order_qty > 0) AS n FROM fc_order_plan")
    lib.alert("info", f"<b>Đề xuất nhập tuần tới đã sẵn sàng:</b> {plan_sum['n'].iloc[0]} nhóm hàng, giá vốn ước tính "
                      f"{lib.vnd(plan_sum['v'].iloc[0])}. Xem <i>Dự báo & đề xuất nhập</i>.")

# ---- Biểu đồ ----
lib.section("Xu hướng", "show_chart")
left, right = st.columns(2, gap="medium")
with left:
    m = monthly[monthly["channel"] != "Nội bộ"].pivot(index="year_month", columns="channel",
                                                      values="revenue_per_open_day").fillna(0)
    fig = go.Figure()
    for i, ch in enumerate(["Bán lẻ", "Đơn lớn / tổ chức"]):
        if ch in m:
            fig.add_bar(x=[lib.month_label(x) for x in m.index], y=m[ch], name=ch, marker_color=viz.SERIES[i],
                        hovertemplate="%{y:,.0f} đ")
    lib.show(fig, 340, barmode="stack", bargap=0.35, title="Doanh thu trung bình mỗi ngày mở cửa (đ)",
             yaxis_tickformat=",.0f", xaxis=dict(tickangle=0, showgrid=False))

with right:
    end = daily["date"].max()
    wk = lib.weekly_blocks(daily["date"], daily["qty"], end).tail(16)
    fig = go.Figure()
    fig.add_scatter(x=wk.index, y=wk.values, name="Thực tế", mode="lines+markers",
                    line=dict(color=viz.TEXT_2, width=2))
    if info is not None:
        fc = lib.q("SELECT ds, sum(forecast) AS f FROM fc_forecast_daily GROUP BY 1 ORDER BY 1")
        fw = lib.weekly_blocks(fc["ds"], fc["f"], end, future=True)
        fig.add_scatter(x=fw.index, y=fw.values, name="Dự báo", mode="lines+markers",
                        line=dict(color=viz.SERIES[0], width=2, dash="dot"))
    lib.show(fig, 340, title="Số lượng bán lẻ mỗi tuần: 16 tuần qua và 4 tuần tới", xaxis=lib.DATE_AXIS)

# ---- Bảng nhanh ----
if info is not None:
    lib.section("Ưu tiên tuần này", "checklist")
    left, right = st.columns([3, 2], gap="medium")
    with left, lib.card():
        st.markdown("**Nhóm hàng cần nhập nhiều nhất**")
        top = lib.q("SELECT unique_id, forecast_week, order_qty, order_value, confidence FROM fc_order_plan "
                    "ORDER BY order_qty DESC LIMIT 8")
        top["confidence"] = top["confidence"].map(lib.CONF_ICON)
        top["order_value"] = top["order_value"].round(0)
        st.dataframe(top, hide_index=True, width="stretch", column_config={
            "unique_id": "Nhóm hàng",
            "forecast_week": st.column_config.NumberColumn("Dự báo tuần", format="%.0f"),
            "order_qty": st.column_config.NumberColumn("Đề xuất nhập", format="%.0f"),
            "order_value": st.column_config.NumberColumn("Giá vốn (đ)", format="localized"),
            "confidence": "Độ tin cậy"})
    with right, lib.card():
        st.markdown("**Nhóm hàng lỗ nhiều nhất**")
        lt = lib.q("SELECT cat_l2, revenue, profit, margin FROM mart_category_margin WHERE profit < 0 "
                   "ORDER BY profit LIMIT 8").round({"revenue": 0, "profit": 0})
        st.dataframe(lt, hide_index=True, width="stretch", column_config={
            "cat_l2": "Nhóm hàng",
            "profit": st.column_config.NumberColumn("Lợi nhuận (đ)", format="localized"),
            "revenue": None,
            "margin": st.column_config.NumberColumn("Biên", format="percent")})
