import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import lib
from hasu import viz
from hasu.forecasting.monitor import DRIFT_FACTOR, SNAPSHOT_EVAL_SQL, drift_status

lib.header("Lịch sử & đánh giá", "So sánh các dự báo đã lưu với kết quả thực tế.")
if not lib.has_table("fc_snapshots"):
    st.warning("Chưa có snapshot dự báo nào.")
    st.stop()

info = lib.q("SELECT * FROM fc_run_info").iloc[0]
hist = lib.q(SNAPSHOT_EVAL_SQL)
snaps = lib.q("SELECT run_id, any_value(kind) AS kind, any_value(week_start) AS week_start, "
              "any_value(created_at) AS created_at, sum(forecast_week) AS forecast_total "
              "FROM fc_snapshots GROUP BY 1 ORDER BY week_start")

st.markdown(
    "**Vòng lặp cải thiện:** mỗi lần chạy, dự báo tuần tới được lưu lại (snapshot). Khi nạp dữ liệu mới, "
    "snapshot được đối chiếu với thực tế. Nếu sai số vượt "
    f"**{lib.num(DRIFT_FACTOR, 1)} lần** sai số kiểm định ({lib.pct(info['holdout_wmape'])}), hoặc mô hình lệch "
    "hệ thống (|tracking signal| > 4), hệ thống cảnh báo và huấn luyện lại.")

real = hist[hist["kind"] == "Dự báo thật"]
status = drift_status(real if len(real) else hist, info["holdout_wmape"])
(st.error if status["retrain"] else st.success)(status["status"])
if not len(real):
    st.info("Chưa có dự báo thật nào đủ 7 ngày thực tế. Các tuần bên dưới là **8 tuần kiểm định được ghi lại "
            "theo đúng cơ chế snapshot** để minh hoạ. Khi bạn nạp dữ liệu tuần tiếp theo, dự báo thật sẽ xuất hiện ở đây.")

if len(hist):
    hist["week_start"] = pd.to_datetime(hist["week_start"])
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_bar(x=hist["week_start"], y=hist["wmape"], marker_color=viz.SERIES[0], name="WMAPE tuần",
                    hovertemplate="%{y:.1%}")
        fig.add_hline(y=info["holdout_wmape"] * DRIFT_FACTOR, line_dash="dot", line_color=viz.CRITICAL,
                      annotation_text="Ngưỡng cảnh báo", annotation_position="top left")
        lib.show(fig, 320, title="Sai số theo tuần (nhóm hàng cấp 3)", yaxis_tickformat=".0%", xaxis=lib.DATE_AXIS)
    with c2:
        fig = go.Figure()
        fig.add_scatter(x=hist["week_start"], y=hist["actual_total"], name="Thực tế", mode="lines+markers",
                        line=dict(color=viz.TEXT_2))
        fig.add_scatter(x=hist["week_start"], y=hist["forecast_total"], name="Dự báo đã lưu", mode="lines+markers",
                        line=dict(color=viz.SERIES[0]))
        lib.show(fig, 320, title="Tổng nhu cầu bán lẻ: dự báo đã lưu và thực tế", xaxis=lib.DATE_AXIS)
    tot_err = (hist["forecast_total"] - hist["actual_total"]).abs().sum() / hist["actual_total"].sum()
    st.metric(f"Độ chính xác tổng tuần đã kiểm chứng ({len(hist)} tuần)", lib.pct(1 - tot_err, 0),
              help="1 − (tổng |dự báo − thực tế| / tổng thực tế), cộng ở mức toàn cửa hàng")
    st.dataframe(hist[["week_start", "kind", "wmape", "bias", "actual_total", "forecast_total"]], hide_index=True,
                 width="stretch", column_config={
        "week_start": st.column_config.DateColumn("Tuần bắt đầu", format="DD/MM/YYYY"), "kind": "Loại",
        "wmape": st.column_config.NumberColumn("WMAPE", format="percent"),
        "bias": st.column_config.NumberColumn("Bias", format="percent"),
        "actual_total": st.column_config.NumberColumn("Thực tế", format="%.0f"),
        "forecast_total": st.column_config.NumberColumn("Dự báo", format="%.0f")})

st.subheader("Các lần dự báo đã lưu")
st.dataframe(snaps, hide_index=True, width="stretch", column_config={
    "run_id": "Mã lần chạy", "kind": "Loại",
    "week_start": st.column_config.DateColumn("Tuần dự báo", format="DD/MM/YYYY"),
    "created_at": st.column_config.DatetimeColumn("Thời điểm lưu", format="DD/MM/YYYY HH:mm"),
    "forecast_total": st.column_config.NumberColumn("Tổng dự báo", format="%.0f")})
