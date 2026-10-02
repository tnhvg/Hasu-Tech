import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import lib
from hasu import viz

lib.header("Giải thích dự báo",
           "SHAP phân rã dự báo của LightGBM thành đóng góp của từng yếu tố.")
if not lib.has_table("fc_shap_global"):
    st.warning("Chưa có kết quả dự báo.")
    st.stop()

info = lib.q("SELECT * FROM fc_run_info").iloc[0]
st.markdown(f"Mô hình đang dùng là **{info['champion_label']}**, tức trung bình của các mô hình thành phần. "
            "Trang này giải thích thành phần **LightGBM**, thành phần duy nhất học từ nhiều yếu tố cùng lúc. "
            "AutoETS và IMAPA chỉ dựa vào chuỗi lịch sử của chính nhóm hàng.")

g = lib.q("SELECT * FROM fc_shap_global ORDER BY mean_abs_shap")
fig = go.Figure(go.Bar(x=g["mean_abs_shap"], y=g["group"], orientation="h", marker_color=viz.SERIES[0],
                       hovertemplate="%{y}: %{x:.3f}<extra></extra>"))
lib.show(fig, 360, title="Yếu tố quan trọng nhất trên toàn bộ dữ liệu (mức ảnh hưởng trung bình)",
         hovermode="closest", xaxis_title="|SHAP| trung bình (thang log)")

st.subheader("Vì sao dự báo ra con số này?")
loc = lib.q("SELECT * FROM fc_shap_local")
loc["ds"] = pd.to_datetime(loc["ds"])
c1, c2 = st.columns([2, 1])
uid = c1.selectbox("Nhóm hàng", sorted(loc["unique_id"].unique()),
                   index=sorted(loc["unique_id"].unique()).index("Nước giải khát")
                   if "Nước giải khát" in set(loc["unique_id"]) else 0)
days = sorted(loc.loc[loc["unique_id"] == uid, "ds"].unique())
day = c2.selectbox("Ngày", days, format_func=lib.day_label)
d = loc[(loc["unique_id"] == uid) & (loc["ds"] == day)].sort_values("shap", key=abs, ascending=False)
fc = lib.q("SELECT * FROM fc_forecast_daily WHERE unique_id = ? AND ds = ?", [uid, pd.Timestamp(day)])

import numpy as np  # noqa: E402

# Gộp các yếu tố "mức bán thường" thành điểm xuất phát, rồi xem các yếu tố ngắn hạn
# và lịch đẩy dự báo lên/xuống bao nhiêu phần trăm.
LEVEL = {"Xu hướng nền 28 ngày", "Mức bán dài hạn", "Ngành hàng", "Độ biến động 28 ngày"}
base_log = float(d["base_value"].iloc[0]) + d.loc[d["group"].isin(LEVEL), "shap"].sum()
adj = d[~d["group"].isin(LEVEL)].sort_values("shap", key=abs, ascending=False)
start = float(np.exp(base_log))
steps = [start]
for v in adj["shap"]:
    steps.append(steps[-1] * float(np.exp(v)))
lgb_pred = steps[-1]
fig = go.Figure(go.Waterfall(
    orientation="h", measure=["absolute", *["relative"] * len(adj), "total"],
    y=["Mức bán thường của nhóm", *adj["group"], "Dự báo LightGBM"],
    x=[start, *np.diff(steps), lgb_pred],
    text=[lib.num(start, 1), *[("+" if e >= 0 else "") + lib.pct(e, 0) for e in np.exp(adj["shap"]) - 1],
          lib.num(lgb_pred, 1)],
    textposition="outside",
    increasing=dict(marker=dict(color=viz.SERIES[0])), decreasing=dict(marker=dict(color=viz.SERIES[1])),
    totals=dict(marker=dict(color=viz.TEXT_2)), connector=dict(line=dict(color=viz.GRID)),
))
lib.show(fig, 400, title=f"{uid}, {lib.day_label(day)}: từ mức bán thường tới dự báo", hovermode="closest",
         yaxis=dict(autorange="reversed"), xaxis_title="Số lượng / ngày")
if len(fc):
    r = fc.iloc[0]
    parts = {k: r[k] for k in ["LightGBM", "AutoETS", "IMAPA"] if k in r and pd.notna(r[k])}
    st.markdown("**Dự báo cuối cùng** là trung bình các thành phần: "
                + " · ".join(f"{k} {lib.num(v, 1)}" for k, v in parts.items())
                + f" → **{lib.num(r['forecast'], 1)}** sản phẩm.")
lib.note("**Mức bán thường** gộp xu hướng nền 28 ngày, mức bán dài hạn, ngành hàng và độ biến động. Phần trăm trên "
         "mỗi thanh: yếu tố đó làm dự báo tăng (+) hoặc giảm (−) bao nhiêu. LightGBM dự báo trên thang log nên các "
         "tác động nhân với nhau.")
st.markdown("**Vì sao không có yếu tố khuyến mãi?** Giá bán chỉ quan sát được ở ngày có bán, nên đưa giá vào "
            "mô hình sẽ \"lộ đề\" thông tin hôm đó có bán hay không. Ảnh hưởng của giảm giá được ước lượng riêng "
            "ở trang *Kịch bản mô phỏng*.")
