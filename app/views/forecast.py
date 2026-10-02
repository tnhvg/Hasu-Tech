import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import lib
from hasu import viz

lib.header("Dự báo & đề xuất nhập hàng")
if not lib.has_table("fc_order_plan"):
    st.warning("Chưa có kết quả dự báo. Hãy nạp dữ liệu ở trang *Nạp dữ liệu*.")
    st.stop()

info = lib.q("SELECT * FROM fc_run_info").iloc[0]
plan = lib.q("SELECT * FROM fc_order_plan")
week_start = pd.Timestamp(plan["week_start"].iloc[0])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Tuần dự báo", f"{week_start:%d/%m}–{week_start + pd.Timedelta(days=6):%d/%m}",
          help=f"Từ {week_start:%d/%m/%Y} đến {week_start + pd.Timedelta(days=6):%d/%m/%Y}")
n_parts = info["champion_label"].count("+") + 1
c2.metric("Mô hình", f"Kết hợp {n_parts} mô hình" if info["champion"].startswith("Ens") else info["champion_label"],
          help=info["champion_label"])
base_store = lib.q("SELECT WMAPE FROM fc_metrics_levels WHERE level = 'Toàn cửa hàng' "
                   "AND model = 'HistoricAverage'")["WMAPE"].iloc[0]
c3.metric("Sai số tổng tuần (WMAPE)", lib.pct(info["store_wmape"]), f"mức nền {lib.pct(base_store)}",
          delta_color="off")
c4.metric("Giá vốn hàng đề xuất nhập", lib.vnd(plan["order_value"].sum()))

with st.expander("Cách đọc bảng này", icon=":material/help:"):
    st.markdown(
        "- **Dự báo tuần**: số lượng bán lẻ dự kiến (mức trung tâm).\n"
        "- **Khoảng 80%**: 8/10 tuần, nhu cầu thực tế nằm trong khoảng này.\n"
        "- **Đề xuất nhập** = dự báo × hệ số phân vị theo loại nhóm hàng: *Ngôi sao* (τ = 0,80, ưu tiên không "
        "hết hàng), *Bảo quản lâu* (τ = 0,70), *Dễ hư hỏng* (τ = 0,55, hạn chế hàng dư). Với nhóm bán thất "
        "thường, đề xuất có thể **thấp hơn** dự báo trung bình vì phần lớn các tuần nhu cầu thấp hơn mức trung bình.\n"
        "- **Độ tin cậy** dựa trên sai số kiểm định 8 tuần của chính nhóm hàng đó: 🟢 ≤ 30%, 🟡 ≤ 50%, 🟠 > 50%, "
        "⚪ chưa đủ dữ liệu (dùng trung bình 8 tuần, nên nhập lô nhỏ thăm dò).\n"
        "- Đề xuất chưa trừ tồn kho hiện có vì hệ thống chưa có dữ liệu tồn kho.")

f1, f2, f3 = st.columns(3)
l1 = f1.multiselect("Ngành hàng", sorted(plan["cat_l1"].dropna().unique()))
conf = f2.multiselect("Độ tin cậy", list(lib.CONF_ICON), default=["Cao", "Trung bình", "Thấp"])
svc = f3.multiselect("Loại nhóm hàng", sorted(plan["service_class"].dropna().unique()))
view = plan.copy()
if l1:
    view = view[view["cat_l1"].isin(l1)]
if conf:
    view = view[view["confidence"].isin(conf)]
if svc:
    view = view[view["service_class"].isin(svc)]
view["interval"] = [f"{lib.num(a)} – {lib.num(b)}" if pd.notna(a) else "–"
                    for a, b in zip(view["lower_80"], view["upper_80"])]
view["conf_label"] = view["confidence"].map(lib.CONF_ICON)
st.dataframe(
    view[["unique_id", "cat_l1", "forecast_week", "interval", "order_qty", "order_value", "conf_label", "service_class"]],
    hide_index=True, use_container_width=True, height=420, column_config={
        "unique_id": "Nhóm hàng", "cat_l1": "Ngành",
        "forecast_week": st.column_config.NumberColumn("Dự báo tuần", format="%.0f"),
        "interval": "Khoảng 80%",
        "order_qty": st.column_config.NumberColumn("Đề xuất nhập", format="%.0f"),
        "order_value": st.column_config.NumberColumn("Giá vốn (đ)", format="localized"),
        "conf_label": "Độ tin cậy", "service_class": "Loại"})
st.download_button("Tải bảng đề xuất (CSV)", view.drop(columns=["conf_label"]).to_csv(index=False).encode("utf-8-sig"),
                   file_name=f"de_xuat_nhap_{week_start:%Y%m%d}.csv", mime="text/csv")

# ---- Chi tiết một nhóm hàng ----
st.subheader("Chi tiết nhóm hàng")
uid = st.selectbox("Chọn nhóm hàng", view["unique_id"] if len(view) else plan["unique_id"])
row = plan.set_index("unique_id").loc[uid]
end = pd.Timestamp(lib.q("SELECT max(date) AS d FROM dim_date")["d"].iloc[0])
hist = lib.q("SELECT date, quantity FROM fct_retail_daily_category WHERE cat_l3 = ? AND date > ? - INTERVAL 84 DAY",
             [uid, end])
hw = lib.weekly_blocks(hist["date"], hist["quantity"], end)
fc = lib.q("SELECT ds, forecast FROM fc_forecast_daily WHERE unique_id = ?", [uid])
fw = lib.weekly_blocks(fc["ds"], fc["forecast"], end, future=True)
ratio = row["upper_80"] / row["forecast_week"] if row["forecast_week"] else None
lo_ratio = row["lower_80"] / row["forecast_week"] if row["forecast_week"] else None

fig = go.Figure()
if ratio and pd.notna(ratio):
    fig.add_scatter(x=list(fw.index) + list(fw.index[::-1]), y=list(fw * ratio) + list((fw * lo_ratio)[::-1]),
                    fill="toself", fillcolor="rgba(42,120,214,0.15)", line=dict(width=0), name="Khoảng 80%",
                    hoverinfo="skip")
fig.add_scatter(x=hw.index, y=hw.values, mode="lines+markers", name="Thực tế", line=dict(color=viz.TEXT_2))
fig.add_scatter(x=fw.index, y=fw.values, mode="lines+markers", name="Dự báo", line=dict(color=viz.SERIES[0]))
lib.show(fig, 340, title=f"{uid}: 12 tuần thực tế và 4 tuần dự báo (số lượng / tuần)", xaxis=lib.DATE_AXIS)

c1, c2, c3 = st.columns(3)
c1.metric("Kiểu nhu cầu", lib.CLASS_LABELS.get(row["demand_class"], row["demand_class"]))
c2.metric("Sai số kiểm định của nhóm", lib.pct(row["wmape"]))
c3.metric("Đề xuất nhập tuần tới", lib.num(row["order_qty"]), f"τ = {lib.num(row['tau'], 2)}", delta_color="off")

alloc = lib.q("SELECT * FROM fc_sku_allocation WHERE cat_l3 = ? ORDER BY share DESC", [uid])
if len(alloc):
    st.markdown("**Phân bổ xuống mã hàng** theo thị phần 8 tuần gần nhất trong nhóm:")
    st.dataframe(alloc[["product_name", "share", "sku_forecast_week", "sku_order_qty"]], hide_index=True,
                 use_container_width=True, column_config={
        "product_name": "Mã hàng", "share": st.column_config.ProgressColumn("Thị phần", format="%.0f%%",
                                                                           min_value=0, max_value=1),
        "sku_forecast_week": st.column_config.NumberColumn("Dự báo tuần", format="%.1f"),
        "sku_order_qty": st.column_config.NumberColumn("Đề xuất nhập", format="%.0f")})
    lib.note("Dự báo ở cấp nhóm trước rồi mới chia xuống mã hàng: tổng nhu cầu nhóm ổn định hơn và ít bị ảnh "
             "hưởng khi một mã trong nhóm giảm giá hay hết hàng.")
