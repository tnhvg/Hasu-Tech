import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import lib
from hasu import viz

lib.header("Tổng quan cửa hàng")

monthly = lib.q("SELECT * FROM mart_monthly")
info = lib.q("SELECT * FROM fc_run_info").iloc[0] if lib.has_table("fc_run_info") else None

# ---- Chỉ số chính ----
sales = monthly[monthly["channel"] != "Nội bộ"]
rev, profit = sales["revenue"].sum(), sales["profit"].sum()
inv = sales["n_invoices"].sum()
daily = lib.q("""
    SELECT date, sum(quantity) AS qty, sum(revenue) AS revenue, sum(n_invoices) AS n_invoices
    FROM fct_retail_daily_category GROUP BY 1 ORDER BY 1""")
daily["date"] = pd.to_datetime(daily["date"])
last4 = daily[daily["date"] > daily["date"].max() - pd.Timedelta(days=28)]
prev4 = daily[(daily["date"] <= daily["date"].max() - pd.Timedelta(days=28))
              & (daily["date"] > daily["date"].max() - pd.Timedelta(days=56))]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Doanh thu thuần", lib.vnd(rev), help="Bán lẻ + đơn lớn/tổ chức, đã trừ hàng trả")
c2.metric("Lợi nhuận gộp", lib.vnd(profit), help=f"Biên lợi nhuận gộp {lib.pct(profit / rev)}")
c2.caption(f"Biên lợi nhuận gộp **{lib.pct(profit / rev)}**")
c3.metric("Hoá đơn bán lẻ/ngày (4 tuần)", lib.num(last4["n_invoices"].mean()),
          lib.pct(last4["n_invoices"].mean() / prev4["n_invoices"].mean() - 1) + " so với 4 tuần trước")
if info is not None:
    c4.metric("Độ chính xác dự báo tuần", lib.pct(1 - info["store_wmape"], 0),
              help="1 − WMAPE của tổng nhu cầu bán lẻ toàn cửa hàng theo tuần, trên 8 tuần kiểm định")

# ---- Cảnh báo ----
st.subheader("Cần chú ý")
alerts = []
loss = lib.q("SELECT cat_l2, profit FROM mart_category_margin WHERE quadrant = 'Thua lỗ' ORDER BY profit")
if len(loss):
    alerts.append(("error", f"**{len(loss)} nhóm hàng đang bán lỗ**, lỗ nhiều nhất: "
                            + ", ".join(f"{r.cat_l2} ({lib.vnd(r.profit)})" for r in loss.head(3).itertuples())
                            + ". Xem *Phân tích kinh doanh → Biên lợi nhuận*."))
drop = last4["n_invoices"].mean() / daily["n_invoices"].mean() - 1
if drop < -0.15:
    alerts.append(("warning", f"**Lượng khách bán lẻ 4 tuần gần nhất thấp hơn {lib.pct(-drop, 0)}** so với "
                              "trung bình cả kỳ."))
if lib.has_table("mart_stockout_suspects"):
    so = lib.q("SELECT count(DISTINCT sku) AS n FROM mart_stockout_suspects WHERE status LIKE 'Không bán tới cuối%'")
    if so["n"].iloc[0]:
        alerts.append(("warning", f"**{so['n'].iloc[0]} mã hàng bán đều đã ngừng bán tới cuối kỳ**: có thể đang hết "
                                  "hàng. Xem *Phân tích kinh doanh → Nghi ngờ hết hàng*."))
if info is not None:
    plan = lib.q("SELECT sum(order_value) AS v, count(*) FILTER (order_qty > 0) AS n FROM fc_order_plan")
    alerts.append(("info", f"**Đề xuất nhập tuần tới:** {plan['n'].iloc[0]} nhóm hàng, giá vốn ước tính "
                           f"{lib.vnd(plan['v'].iloc[0])}. Xem *Dự báo & đề xuất nhập*."))
for kind, text in alerts:
    getattr(st, kind)(text)

# ---- Biểu đồ ----
left, right = st.columns(2)
with left:
    m = monthly[monthly["channel"] != "Nội bộ"].pivot(index="year_month", columns="channel",
                                                      values="revenue_per_open_day").fillna(0)
    fig = go.Figure()
    for i, ch in enumerate(["Bán lẻ", "Đơn lớn / tổ chức"]):
        if ch in m:
            fig.add_bar(x=[lib.month_label(x) for x in m.index], y=m[ch], name=ch, marker_color=viz.SERIES[i],
                        hovertemplate="%{y:,.0f} đ")
    lib.show(fig, barmode="stack", title="Doanh thu trung bình mỗi ngày mở cửa (đ)", yaxis_tickformat=",.0f")
    lib.note("Dùng doanh thu/ngày mở cửa để so sánh công bằng tháng thiếu ngày (09/2025) và tháng nghỉ Tết.")

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
    lib.show(fig, title="Số lượng bán lẻ theo tuần: 16 tuần qua và 4 tuần tới", xaxis=lib.DATE_AXIS)
    lib.note("Mỗi điểm là một khối 7 ngày liên tiếp, tính lùi từ ngày cuối của dữ liệu.")
