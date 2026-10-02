from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import lib
from hasu import viz

lib.header("Kịch bản mô phỏng", "Đặt câu hỏi \"nếu... thì...\" và xem nhu cầu dự kiến thay đổi thế nào.")
if not lib.has_table("fc_order_plan"):
    st.warning("Chưa có kết quả dự báo.")
    st.stop()

plan = lib.q("SELECT * FROM fc_order_plan")
tab1, tab2 = st.tabs(["Giảm giá một ngành hàng", "Kỳ nghỉ Tết"])

# ---------------------------------------------------------------- Giảm giá
with tab1:
    pr = lib.q("SELECT * FROM fc_price_response")
    c1, c2, c3 = st.columns(3)
    l1 = c1.selectbox("Ngành hàng", pr.sort_values("discount_days", ascending=False)["cat_l1"])
    disc = c2.slider("Mức giảm giá (%)", 0, 30, 10, step=5)
    cannibal = c3.slider("Phần tăng lấy từ mã khác cùng nhóm (%)", 0, 100, 50, step=10,
                         help="Hiện tượng triệt tiêu chéo: khách chuyển từ mã không giảm giá sang mã giảm giá trong "
                              "cùng nhóm, nên tổng nhu cầu nhóm tăng ít hơn nhu cầu của mã được giảm giá.")
    r = pr.set_index("cat_l1").loc[l1]
    slope = r["uplift_per_pct"] if r["reliable"] else r["store_uplift_per_pct"]
    gross = 1 + slope * disc
    net = 1 + (gross - 1) * (1 - cannibal / 100)
    base = plan[plan["cat_l1"] == l1]
    tot_base = base["forecast_week"].sum()
    k1, k2, k3 = st.columns(3)
    k1.metric("Nhu cầu tuần hiện tại", lib.num(tot_base))
    k2.metric("Nhu cầu tuần theo kịch bản", lib.num(tot_base * net), lib.pct(net - 1, 0))
    k3.metric("Cần nhập thêm (ước tính)", lib.num(max(base["order_qty"].sum() * (net - 1), 0)))
    top = base.nlargest(10, "forecast_week")
    fig = go.Figure()
    fig.add_bar(y=top["unique_id"], x=top["forecast_week"], name="Hiện tại", orientation="h", marker_color=viz.NEUTRAL)
    fig.add_bar(y=top["unique_id"], x=top["forecast_week"] * net, name="Kịch bản", orientation="h",
                marker_color=viz.SERIES[0])
    lib.show(fig, 380, barmode="group", title=f"{l1}: dự báo tuần, 10 nhóm lớn nhất", hovermode="y unified",
             yaxis=dict(autorange="reversed"))
    src = "của chính ngành hàng" if r["reliable"] else "chung toàn cửa hàng (ngành này có dưới 30 ngày khuyến mãi)"
    st.warning(
        f"**Độ tin cậy thấp: hãy coi đây là mức trần.** Hệ số phản ứng giá ({lib.num(slope * 100, 1)}% lượng bán "
        f"cho mỗi 1% giảm giá) được ước lượng {src}, từ {lib.num(r['discount_days'])} ngày có chiết khấu. Ở cửa "
        "hàng tạp hoá, giá thấp hơn giá phổ biến thường do khách **mua theo thùng/lốc**: mua nhiều mới được giá "
        "thấp, chứ không phải giá thấp làm khách mua nhiều. Dữ liệu chưa tách được hai hiệu ứng này.")

# ---------------------------------------------------------------- Tết
with tab2:
    tet = lib.q("SELECT * FROM mart_tet_effect WHERE cat_l1 <> 'Toàn cửa hàng'")
    c1, c2, c3 = st.columns(3)
    tet_day = c1.date_input("Mùng 1 Tết", date(2027, 2, 6))
    closed = c2.slider("Số ngày cửa hàng nghỉ", 3, 14, 7, help="Tết 2026 cửa hàng nghỉ 7 ngày (16–23/02)")
    stock_share = c3.slider("Tỷ lệ khách mua tích trữ trước cho ngày nghỉ (%)", 0, 100, 50, step=10,
                            help="Giả định: mỗi ngày nghỉ thêm, phần nhu cầu này được mua dồn vào trước Tết.")
    base_l1 = plan.groupby("cat_l1", as_index=False)["forecast_week"].sum()
    pre = tet[tet["tet_window"] == "Trước Tết"][["cat_l1", "qty_factor"]]
    s = base_l1.merge(pre, on="cat_l1", how="left").fillna({"qty_factor": 1.0})
    s["daily_base"] = s["forecast_week"] / 7
    s["pre_tet_2w"] = s["daily_base"] * 14 * s["qty_factor"]
    s["extra_closed"] = s["daily_base"] * max(closed - 7, 0) * stock_share / 100
    s["total"] = s["pre_tet_2w"] + s["extra_closed"]
    s = s.sort_values("total", ascending=False)
    k1, k2 = st.columns(2)
    k1.metric("Nhu cầu 14 ngày trước Tết", lib.num(s["total"].sum()),
              lib.pct(s["total"].sum() / (s["daily_base"].sum() * 14) - 1, 0) + " so với 2 tuần thường")
    k2.metric("Phần tăng do nghỉ dài hơn 7 ngày", lib.num(s["extra_closed"].sum()))
    fig = go.Figure()
    fig.add_bar(x=s["cat_l1"], y=s["daily_base"] * 14, name="2 tuần bình thường", marker_color=viz.NEUTRAL)
    fig.add_bar(x=s["cat_l1"], y=s["total"], name="2 tuần trước Tết (kịch bản)", marker_color=viz.SERIES[0])
    lib.show(fig, 380, barmode="group", title=f"Nhu cầu 2 tuần trước Tết {tet_day:%d/%m/%Y} theo ngành hàng")
    lib.note("Hệ số Tết lấy từ Tết 2026, chỉ một lần quan sát. Nhu cầu nền dùng dự báo hiện tại; khi tới gần Tết, "
             "chạy lại dự báo để có nền mới hơn.")
