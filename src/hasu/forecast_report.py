"""Báo cáo mô hình dự báo: docs/forecast_report.md và biểu đồ.

    python -m hasu.forecast_report

Chạy sau `python -m hasu.forecasting.run`.
"""

from __future__ import annotations

from datetime import datetime

import duckdb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

from hasu import viz
from hasu.business_report import md_table, mil, num, pct, save
from hasu.config import DB_PATH, DOCS_DIR
from hasu.forecasting.monitor import drift_status
from hasu.forecasting.policy import SERVICE_POLICY

LEVEL_ORDER = ["Nhóm hàng cấp 3", "Nhóm hàng cấp 2", "Ngành hàng cấp 1", "Toàn cửa hàng"]


def fig_models(m: pd.DataFrame, champion: str, baseline: str) -> str:
    m = m.sort_values("WMAPE", ascending=True)
    colors = [viz.SERIES[0] if r == champion else (viz.SERIES[1] if r == baseline else viz.NEUTRAL)
              for r in m["model"]]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    y = np.arange(len(m))[::-1]
    ax.barh(y, m["WMAPE"], color=colors, height=0.62)
    ax.set_yticks(y, m["label"])
    ax.xaxis.set_major_formatter(PercentFormatter(1.0))
    ax.grid(axis="x"), ax.grid(axis="y", visible=False)
    for yi, v in zip(y, m["WMAPE"]):
        ax.text(v + 0.005, yi, pct(v), va="center", fontsize=8.5, color=viz.TEXT_2)
    ax.set_xlim(0, m["WMAPE"].max() * 1.15)
    ax.set_title("WMAPE theo tuần trên 8 tuần kiểm định (thấp hơn là tốt hơn)")
    ax.text(0, -0.13, "Xanh: mô hình được chọn  ·  Cam: mức nền  ·  Xám: các mô hình khác",
            transform=ax.transAxes, color=viz.TEXT_2, fontsize=8.5)
    return save(fig, "11_so_sanh_mo_hinh.png")


def fig_levels(lv: pd.DataFrame, champion: str, baseline: str) -> str:
    fig, ax = plt.subplots(figsize=(9, 4))
    x = np.arange(len(LEVEL_ORDER))
    for i, (mdl, color, name) in enumerate([(champion, viz.SERIES[0], "Mô hình được chọn"),
                                            (baseline, viz.SERIES[1], "Mức nền: trung bình lịch sử")]):
        vals = lv[lv["model"] == mdl].set_index("level").loc[LEVEL_ORDER, "WMAPE"].to_numpy()
        ax.bar(x + (i - 0.5) * 0.36, vals, width=0.34, color=color, label=name)
        for xi, v in zip(x + (i - 0.5) * 0.36, vals):
            ax.text(xi, v + 0.01, pct(v, 0), ha="center", fontsize=8.5, color=viz.TEXT_2)
    ax.set_xticks(x, LEVEL_ORDER)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.legend(loc="upper right")
    ax.set_title("Sai số giảm mạnh khi gộp dự báo lên cấp cao hơn (WMAPE theo tuần)")
    return save(fig, "12_sai_so_theo_cap.png")


def fig_store_backtest(w: pd.DataFrame, champion: str, baseline: str) -> str:
    g = w.groupby("cutoff")[["y", champion, baseline]].sum().reset_index()
    g["week"] = pd.to_datetime(g["cutoff"]) + pd.Timedelta(days=1)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(g["week"], g["y"], color=viz.TEXT, marker="o", markersize=4, label="Thực tế")
    ax.plot(g["week"], g[champion], color=viz.SERIES[0], marker="o", markersize=4, label="Mô hình")
    ax.plot(g["week"], g[baseline], color=viz.SERIES[1], marker="o", markersize=4, label="Mức nền",
            linestyle=(0, (4, 2)))
    ax.axvspan(g["week"].iloc[0] - pd.Timedelta(days=3), g["week"].iloc[3] + pd.Timedelta(days=3),
               color="#f0efec", zorder=0)
    ax.text(g["week"].iloc[0], ax.get_ylim()[0] + 20, "4 tuần chọn mô hình", color=viz.TEXT_2, fontsize=8.5)
    ax.yaxis.set_major_formatter(lambda v, _p: viz.fmt_int(v))
    ax.set_ylabel("Số lượng bán lẻ / tuần")
    ax.legend(loc="upper right", ncols=3)
    ax.set_title("Kiểm định trượt: tổng nhu cầu bán lẻ toàn cửa hàng theo tuần")
    fig.autofmt_xdate()
    return save(fig, "13_kiem_dinh_toan_cua_hang.png")


def fig_shap(g: pd.DataFrame) -> str:
    g = g.sort_values("mean_abs_shap")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(g["group"], g["mean_abs_shap"], color=viz.SERIES[0], height=0.6)
    ax.grid(axis="x"), ax.grid(axis="y", visible=False)
    ax.set_xlabel("Mức ảnh hưởng trung bình |SHAP| (thang log)")
    ax.set_title("Yếu tố nào quyết định dự báo của LightGBM?")
    return save(fig, "14_shap_toan_cuc.png")


def fig_example(con: duckdb.DuckDBPyConnection, uid: str) -> str:
    """Thực tế 10 tuần gần nhất và dự báo 4 tuần tới, theo TUẦN (đúng đơn vị của khoảng 80%)."""
    end = pd.Timestamp(con.execute("SELECT max(date) FROM dim_date").fetchone()[0])
    hist = con.execute("""
        SELECT date, quantity FROM fct_retail_daily_category
        WHERE cat_l3 = ? AND date > ? - INTERVAL 70 DAY""", [uid, end]).df()
    hist["k"] = ((end - pd.to_datetime(hist["date"])).dt.days // 7)
    hw = hist.groupby("k")["quantity"].sum().sort_index(ascending=False)
    hw.index = [end - pd.Timedelta(days=7 * k + 6) for k in hw.index]
    fc = con.execute("SELECT ds, forecast FROM fc_forecast_daily WHERE unique_id = ?", [uid]).df()
    fc["k"] = (pd.to_datetime(fc["ds"]) - end - pd.Timedelta(days=1)).dt.days // 7
    fw = fc.groupby("k")["forecast"].sum()
    fw.index = [end + pd.Timedelta(days=1 + 7 * k) for k in fw.index]
    rq = con.execute("""SELECT horizon_week, q10, q90 FROM fc_ratio_quantiles q
                        JOIN fc_profile p ON p.demand_class = q.grp
                        WHERE p.unique_id = ? ORDER BY horizon_week""", [uid]).df().set_index("horizon_week")
    k = np.arange(1, len(fw) + 1)
    lo = rq["q10"].reindex(k).ffill().to_numpy()
    hi = rq["q90"].reindex(k).ffill().to_numpy()
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.plot(hw.index, hw.values, color=viz.TEXT_2, marker="o", markersize=4, label="Thực tế")
    ax.fill_between(fw.index, fw.values * lo, fw.values * hi, color=viz.BLUE_RAMP[0], linewidth=0,
                    label="Khoảng 80% (hiệu chỉnh riêng từng tuần)")
    ax.plot(fw.index, fw.values, color=viz.SERIES[0], marker="o", markersize=4, label="Dự báo")
    ax.axvline(end + pd.Timedelta(hours=12), color=viz.MUTED, linewidth=1)
    ax.set_ylim(0, None)
    ax.legend(loc="upper left", ncols=3)
    ax.set_ylabel("Số lượng / tuần")
    ax.set_title(f"Ví dụ: nhóm \"{uid}\", 10 tuần thực tế và 4 tuần dự báo")
    fig.autofmt_xdate()
    return save(fig, "15_vi_du_du_bao.png")


def fm_label(m: str) -> str:
    from hasu.forecasting.models import MODEL_LABELS
    return MODEL_LABELS.get(m, m)


def evaluate_snapshots_df(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    from hasu.forecasting.monitor import SNAPSHOT_EVAL_SQL
    try:
        return con.execute(SNAPSHOT_EVAL_SQL).df()
    except duckdb.CatalogException:
        return pd.DataFrame()


def build(con: duckdb.DuckDBPyConnection) -> str:
    viz.apply_style()
    q = lambda sql: con.execute(sql).df()  # noqa: E731
    info = q("SELECT * FROM fc_run_info").iloc[0]
    champion, baseline = info["champion"], "HistoricAverage"
    metrics = q("SELECT * FROM fc_metrics")
    overall = metrics[metrics["scope"] == "Tổng thể"]
    sel = metrics[metrics["scope"] == "Giai đoạn chọn mô hình"]
    by_cls = metrics[metrics["scope"].isin(["erratic", "lumpy", "intermittent"])]
    levels = q("SELECT * FROM fc_metrics_levels")
    weekly = q("SELECT * FROM fc_backtest_weekly WHERE phase = 'holdout'")
    allw = q("SELECT * FROM fc_backtest_weekly")
    profile = q("SELECT * FROM fc_profile")
    sim = q("SELECT * FROM fc_simulation")
    shap_g = q("SELECT * FROM fc_shap_global")
    price = q("SELECT * FROM fc_price_response WHERE discount_days > 0 ORDER BY discount_days DESC")
    plan = q("SELECT * FROM fc_order_plan ORDER BY forecast_week DESC")
    sig = q("SELECT * FROM fc_significance").set_index("compared_to")
    rqs = q("SELECT * FROM fc_ratio_quantiles ORDER BY grp, horizon_week")

    f1 = fig_models(overall, champion, baseline)
    f2 = fig_levels(levels, champion, baseline)
    f3 = fig_store_backtest(allw, champion, baseline)
    f4 = fig_shap(shap_g)
    f5 = fig_example(con, plan["unique_id"].iloc[0])

    ch = overall.set_index("model").loc[champion]
    bl = overall.set_index("model").loc[baseline]
    ma = overall.set_index("model").loc["MovingAvg28"]
    lv = levels.set_index(["level", "model"])["WMAPE"]
    cls_counts = profile["demand_class"].value_counts()
    cls_qty = profile.groupby("demand_class")["total_qty"].sum() / profile["total_qty"].sum()
    sim1 = sim[sim["mode"].str.startswith("Một kỳ")]
    simc = sim[sim["mode"].str.startswith("Nhiều kỳ")]
    s = sim1.set_index("policy")
    base_p, model_p = s.loc["Mức nền: trung bình lịch sử"], s.loc["Mô hình + phân vị theo nhóm hàng"]
    ma_p = s.loc["Trung bình 28 ngày (cách nhẩm)"]
    c = simc.set_index("policy")
    base_c, model_c = c.loc["Mức nền: trung bình lịch sử"], c.loc["Mô hình + phân vị theo nhóm hàng"]
    ma_c = c.loc["Trung bình 28 ngày (cách nhẩm)"]
    n_bt = int(info["n_backtest"])
    ts_over = profile["tracking_signal"].abs() > 4
    n_ts, n_ts_pos = int(ts_over.sum()), int((profile["tracking_signal"] > 4).sum())
    s_ma, s_bl = sig.loc["MovingAvg28"], sig.loc[baseline]

    out: list[str] = []
    add = out.append
    add("# Mô hình dự báo nhu cầu\n")
    add(f"_Sinh tự động bởi `python -m hasu.forecast_report` lúc {datetime.now():%d/%m/%Y %H:%M}. "
        f"Dữ liệu tới {pd.Timestamp(info['data_until']):%d/%m/%Y}._\n")

    add("## Kết quả chính\n")
    add(f"- **Mô hình được chọn:** {info['champion_label']}, chọn trên 4 tuần đầu của kiểm định, "
        "không nhìn vào 8 tuần dùng để chấm điểm.\n"
        f"- **Toàn cửa hàng:** sai số dự báo tuần (WMAPE) {pct(lv[('Toàn cửa hàng', champion)])}, "
        f"tức độ chính xác khoảng **{pct(1 - lv[('Toàn cửa hàng', champion)], 0)}**. Mức nền: "
        f"{pct(lv[('Toàn cửa hàng', baseline)])}. Lưu ý: ở cấp này trung bình trượt 28 ngày còn tốt hơn "
        f"mô hình ({pct(lv[('Toàn cửa hàng', 'MovingAvg28')])}).\n"
        f"- **Nhóm hàng cấp 3** (đơn vị ra quyết định nhập hàng): WMAPE {pct(ch['WMAPE'])} so với "
        f"{pct(bl['WMAPE'])} của mức nền, **giảm {pct(1 - ch['WMAPE'] / bl['WMAPE'], 0)} sai số**. "
        f"Độ lệch (bias) {pct(ch['Bias'])}, trong khi mức nền dự báo thừa {pct(bl['Bias'])}.\n"
        f"- **Kiểm định thống kê:** mô hình tốt hơn mức nền có ý nghĩa thống kê (Wilcoxon p = "
        f"{num(s_bl.wilcoxon_p, 3)}), nhưng chênh lệch với trung bình trượt 28 ngày **không có ý nghĩa thống kê** "
        f"(Wilcoxon p = {num(s_ma.wilcoxon_p, 2)}; Diebold–Mariano p = {num(s_ma.dm_p, 2)}).\n"
        f"- **Mô phỏng nhập hàng 8 tuần có chuyển tồn** (hàng bảo quản lâu bán tiếp tuần sau, hàng dễ hư hỏng "
        f"còn dư bị bỏ): nhập theo mô hình kết hợp phân vị có tổng chi phí (lợi nhuận mất do thiếu hàng + "
        f"hàng hỏng + chi phí vốn) **{mil(model_c.total_cost)}**, so với {mil(ma_c.total_cost)} của cách nhẩm "
        f"theo trung bình 28 ngày và {mil(base_c.total_cost)} của mức nền (mục 5).\n")
    n_imp = round(info["share_improved"] * n_bt)
    add("**Nói thẳng về giới hạn:** chỉ "
        f"{pct(info['share_improved'], 0)} số nhóm hàng ({n_imp}/{n_bt} nhóm) có sai số thấp "
        f"hơn mức nền khi xét riêng từng nhóm, mô hình chỉ tốt hơn trung bình trượt 28 ngày một chút và "
        f"không có ý nghĩa thống kê ({pct(ch['WMAPE'])} so với {pct(ma['WMAPE'])}), ở cấp toàn cửa hàng còn "
        f"kém trung bình trượt 28 ngày. Mức giảm {pct(1 - ch['WMAPE'] / bl['WMAPE'], 0)} so với mức nền một "
        "phần là do lượng khách giảm khoảng một phần tư đúng trong 8 tuần chấm điểm (tháng 5–6/2026): trung "
        f"bình lịch sử không theo kịp nên dự báo thừa {pct(bl['Bias'])}. Với dữ liệu thưa như cửa hàng này, không mô hình nào dự báo chính xác từng "
        "nhóm hàng nhỏ theo tuần. Giá trị thực tế nằm ở: (1) dự báo tổng và nhóm lớn đáng tin cậy, "
        "(2) chính sách nhập hàng theo phân vị, (3) giải thích được và tự động hoá được.\n")

    add("## 1. Dữ liệu đầu vào và phân loại nhu cầu\n")
    add("- Mục tiêu: **số lượng bán lẻ** theo ngày của từng nhóm hàng cấp 3, đã loại đơn lớn, đơn tổ chức, "
        "xuất nội bộ, hàng trả, hàng tặng (xem báo cáo chất lượng dữ liệu). Phần đơn sỉ được xử lý riêng bằng "
        "lượng dự phòng cho các mã hay được mua sỉ (báo cáo phân tích kinh doanh, mục 8).\n"
        "- **Lớp ngày thường:** ngày đóng cửa và vùng 28 ngày quanh Tết (từ 14 ngày trước đến 13 ngày sau "
        "mùng 1) được thay bằng trung vị cùng thứ "
        "trong các tuần trước đó (không dùng tuần sau) trước khi huấn luyện, để mô hình học đường nền không bị đột biến kéo lệch. "
        "**Lớp ngày lễ:** khi kỳ dự báo rơi vào vùng Tết, dự báo được nhân hệ số số lượng theo ngành hàng "
        "(đo từ Tết 2026, xem báo cáo phân tích kinh doanh).\n"
        "- Phân loại kiểu nhu cầu theo **Syntetos–Boylan** (ADI: khoảng cách trung bình giữa hai ngày có bán; "
        "CV²: độ biến động lượng bán):\n")
    names = {"erratic": "Erratic: bán gần như mọi ngày, lượng dao động",
             "lumpy": "Lumpy: bán gián đoạn, lượng dao động",
             "intermittent": "Intermittent: bán gián đoạn, lượng đều",
             "smooth": "Smooth: bán đều, lượng ổn định",
             "insufficient": "Chưa đủ dữ liệu (dưới 20 ngày có bán)"}
    add(md_table(pd.DataFrame({
        "Kiểu nhu cầu": [names[c] for c in cls_counts.index],
        "Số nhóm hàng": cls_counts.values,
        "Tỷ trọng số lượng": [pct(cls_qty.get(c, 0)) for c in cls_counts.index],
    })))
    add("\nNhóm \"chưa đủ dữ liệu\" không được dự báo bằng mô hình: dùng trung bình 8 tuần gần nhất và "
        "gắn nhãn rõ trên ứng dụng (đề xuất nhập lô nhỏ thăm dò).\n")
    add(f"Bảng trên dùng toàn bộ dữ liệu, cho dự báo thật. Riêng **kiểm định** chỉ dùng dữ liệu tới trước cửa sổ "
        f"đầu tiên ({pd.Timestamp(info['first_cutoff']):%d/%m/%Y}) để chọn nhóm đủ dữ liệu và xác định kiểu nhu "
        f"cầu, nên có {n_bt} nhóm hàng tham gia kiểm định.\n")

    add("## 2. Phương pháp kiểm định\n")
    add("**Kiểm định trượt theo thời gian (walk-forward):** 12 tuần cuối được chia thành 12 cửa sổ. Ở mỗi "
        "cửa sổ, mô hình chỉ thấy dữ liệu tới trước tuần đó, dự báo 7 ngày, rồi so với thực tế. "
        "**4 tuần đầu** dùng để chọn mô hình, **8 tuần sau** dùng để báo cáo. Tách hai giai đoạn để con số "
        "báo cáo không bị \"đẹp giả\" do chọn mô hình trên chính dữ liệu chấm điểm.\n")
    add("**Không nhìn trước:** mọi thông tin dùng trong kiểm định và mô phỏng chỉ lấy từ dữ liệu trước mốc cắt "
        "tương ứng: danh sách nhóm đủ dữ liệu và kiểu nhu cầu (trước cửa sổ đầu tiên); phân nhóm biên lợi nhuận "
        "để gán τ, giá vốn và giá bán (trước tuần chấm điểm đầu tiên, chỉ dùng giá vốn thật); ngày đóng cửa được "
        "nội suy từ các tuần trước đó; dòng số lượng lớn được nhận diện bằng mức mua điển hình của các lần bán "
        "trước đó.\n")
    add("| Chỉ số | Ý nghĩa |\n|---|---|\n"
        "| WMAPE | Tổng sai số tuyệt đối / tổng thực tế. Dùng được khi có nhiều tuần bán bằng 0 (MAPE thì không) |\n"
        "| MAE | Sai số tuyệt đối trung bình, theo đơn vị sản phẩm |\n"
        "| MdAPE | Trung vị sai số %, chỉ trên các tuần có bán |\n"
        "| Bias | Sai số có dấu: dương là dự báo thừa (chôn vốn), âm là dự báo thiếu (mất doanh thu) |\n"
        "| Tracking signal | Sai số tích luỹ (dự báo − thực tế) / sai số trung bình, cùng dấu với Bias. Lớn hơn 4 về trị tuyệt đối: mô hình lệch hệ thống |\n"
        "| Fill rate, service level | Tỷ lệ nhu cầu được đáp ứng; tỷ lệ tuần có nhu cầu mà không thiếu hàng (trong mô phỏng) |\n")

    add("## 3. So sánh mô hình\n")
    add(f"![So sánh mô hình]({f1})\n")
    comp = overall.merge(sel[["model", "WMAPE"]].rename(columns={"WMAPE": "WMAPE_sel"}), on="model")
    comp = comp.sort_values("WMAPE")
    add(md_table(pd.DataFrame({
        "Mô hình": comp["label"] + np.where(comp["is_champion"], " ✅", ""),
        "WMAPE (4 tuần chọn)": comp["WMAPE_sel"].map(pct),
        "WMAPE (8 tuần chấm)": comp["WMAPE"].map(pct),
        "MAE": comp["MAE"].map(lambda v: num(v, 2)),
        "MdAPE": comp["MdAPE"].map(pct),
        "Bias": comp["Bias"].map(pct),
    })))
    lgb_hold = overall.set_index("model").loc["LightGBM", "WMAPE"]
    rank_hold = int(comp["WMAPE"].rank().loc[comp["model"] == champion].iloc[0])
    rank_sel = int(comp["WMAPE_sel"].rank().loc[comp["model"] == champion].iloc[0])
    add(f"\n**Vì sao chọn mô hình kết hợp mà không chọn LightGBM** dù LightGBM có WMAPE thấp nhất trên 8 tuần "
        f"chấm ({pct(lgb_hold)})? Vì quyết định chọn chỉ được dựa trên 4 tuần đầu. Ở đó LightGBM đứng sau "
        f"mô hình kết hợp. Mô hình được chọn xếp hạng {rank_sel} ở 4 tuần chọn và hạng {rank_hold} ở 8 tuần "
        f"chấm (kém LightGBM {num((ch['WMAPE'] - lgb_hold) * 100, 1)} điểm %): không phải mô hình tốt nhất trên "
        "dữ liệu chấm điểm, nhưng gần như không lệch. Thứ hạng của các mô hình đứng đầu đảo qua lại giữa hai "
        "giai đoạn, cho thấy chênh lệch giữa chúng rất nhỏ so với dao động ngẫu nhiên (xem kiểm định bên dưới). "
        "Chọn lại theo kết quả chấm điểm là dùng dữ liệu kiểm tra để ra quyết định, làm con số báo cáo lạc quan "
        "hơn thực tế.\n")
    add("**Chênh lệch có ý nghĩa thống kê không?** Với mỗi nhóm hàng, lấy sai số tuyệt đối trung bình theo tuần "
        "của mô hình được chọn trừ của mô hình so sánh, rồi kiểm định trên các nhóm hàng (gộp theo nhóm để xử "
        "lý tương quan giữa các tuần):\n")
    add(md_table(pd.DataFrame({
        "So với": [fm_label(m) for m in sig.index],
        "Số nhóm": sig["n_series"].values,
        "Tỷ lệ nhóm mô hình tốt hơn": sig["share_series_better"].map(pct).values,
        "Wilcoxon p": sig["wilcoxon_p"].map(lambda v: num(v, 3)).values,
        "Diebold–Mariano p": sig["dm_p"].map(lambda v: num(v, 3)).values,
    })))
    add("\nMô hình tốt hơn mức nền có ý nghĩa thống kê (p < 0,05), nhưng **không** tốt hơn trung bình trượt 28 "
        "ngày hay LightGBM đơn lẻ một cách có ý nghĩa thống kê. Vì vậy không nên quảng bá mô hình là \"chính xác "
        "hơn hẳn cách nhẩm\"; giá trị của nó nằm ở chính sách nhập hàng (mục 5), giải thích và tự động hoá.\n")
    add(f"**Tracking signal theo nhóm hàng:** {n_ts}/{n_bt} nhóm có |TS| > 4 trên 8 tuần chấm, trong đó "
        f"{n_ts_pos} nhóm dự báo thừa có hệ thống. Điều này khớp với việc lượng khách bán lẻ giảm trong tháng "
        "5–6/2026: mô hình học từ các tháng trước nên chậm theo kịp đà giảm. Vòng lặp tự đánh giá (mục 8) "
        "dùng chính chỉ số này để cảnh báo và huấn luyện lại.\n")
    add("**Theo kiểu nhu cầu (8 tuần chấm, WMAPE):**\n")
    piv = by_cls.pivot(index="label", columns="scope", values="WMAPE")
    piv = piv[[c for c in ["erratic", "lumpy", "intermittent"] if c in piv.columns]].sort_values("erratic")
    add(md_table(pd.DataFrame({"Mô hình": piv.index, **{c: piv[c].map(pct).values for c in piv.columns}})))
    add("\nNhóm erratic (bán gần như mọi ngày, chiếm phần lớn sản lượng) dự báo khá tốt. Nhóm lumpy và intermittent "
        "rất khó dự báo theo tuần, đúng với lý thuyết: lượng bán của chúng gần như ngẫu nhiên.\n")

    add("## 4. Dự báo phân tầng: sai số theo cấp gộp\n")
    add(f"![Sai số theo cấp]({f2})\n")
    add(md_table(pd.DataFrame({
        "Cấp": LEVEL_ORDER,
        "Mô hình": [pct(lv[(l, champion)]) for l in LEVEL_ORDER],
        "Trung bình 28 ngày": [pct(lv[(l, 'MovingAvg28')]) for l in LEVEL_ORDER],
        "Mức nền": [pct(lv[(l, baseline)]) for l in LEVEL_ORDER],
    })))
    add("\nDự báo ở nhóm hàng cấp 3 được cộng lên các cấp trên (bottom-up), nên luôn khớp nhau. Sai số giảm "
        "mạnh khi gộp vì dao động ngẫu nhiên của các nhóm nhỏ triệt tiêu lẫn nhau. Đây là lý do ứng dụng "
        "hiển thị nhãn độ tin cậy cho từng dòng và khuyến nghị dùng dự báo ngành hàng cho kế hoạch vốn.\n")
    add(f"![Kiểm định toàn cửa hàng]({f3})\n")

    add("## 5. Từ dự báo tới số lượng nhập\n")
    add("Dự báo điểm là mức trung tâm. Nhập đúng bằng dự báo điểm thì khoảng một nửa số tuần sẽ thiếu hàng. "
        "Vì vậy số lượng đề xuất nhập = dự báo × hệ số phân vị τ, với τ chọn theo đặc điểm nhóm hàng. Đây là "
        "mắt xích nối phân tích biên lợi nhuận với mô hình:\n")
    add(md_table(pd.DataFrame({
        "Loại nhóm hàng": list(SERVICE_POLICY),
        "Phân vị τ": [num(v[0], 2) for v in SERVICE_POLICY.values()],
        "Lý do": [v[1] for v in SERVICE_POLICY.values()],
    })))
    add("\nHệ số phân vị được ước lượng bằng **conformal prediction** theo tỷ lệ: từ các tuần đã kiểm định, "
        "lấy phân vị τ của tỷ lệ thực tế/dự báo cho từng kiểu nhu cầu. Phương pháp này không giả định phân "
        "phối chuẩn, phù hợp với nhu cầu gián đoạn. Hệ số dùng trong ứng dụng được ước lượng sau khi đã chốt "
        "mô hình; mô phỏng dưới đây dùng hệ số chỉ ước lượng từ 4 tuần chọn.\n")
    add("**Khoảng dự báo cho 4 tuần tới được hiệu chỉnh riêng từng tuần:** tuần 1 dùng 12 tuần kiểm định; tuần "
        "2–4 dùng một kiểm định trượt riêng với chân trời 28 ngày (9 mốc cắt). Hệ số q10 và q90 theo tuần dự "
        "báo:\n")
    piv = rqs.pivot(index="grp", columns="horizon_week", values=["q10", "q90"])
    add(md_table(pd.DataFrame({
        "Kiểu nhu cầu": piv.index,
        **{f"Tuần {k}": [f"{num(a, 2)} – {num(b, 2)}" for a, b in zip(piv[("q10", k)], piv[("q90", k)])]
           for k in sorted(rqs["horizon_week"].unique())},
    })))
    add("\nKhoảng tương đối gần như không rộng ra theo tuần, vì sai số chủ yếu là dao động ngẫu nhiên từ tuần "
        "này sang tuần khác chứ không cộng dồn; nhưng mức giữa giảm dần ở tuần xa hơn, tức dự báo xa dễ thừa "
        "hơn trong giai đoạn khách giảm. Khoảng của nhóm gián đoạn rộng vì gộp chung nhiều nhóm hàng có biến "
        "động khác nhau; đây là cái giá của việc có quá ít tuần dữ liệu cho từng nhóm.\n")
    add("**Mô phỏng nhập hàng trên 8 tuần chấm điểm.** Mọi tham số (hệ số phân vị, τ, giá vốn, giá bán) chỉ "
        "lấy từ dữ liệu trước tuần chấm điểm đầu tiên. Số lượng đặt được làm tròn lên như trong ứng dụng. "
        "Service level chỉ tính trên các tuần có nhu cầu.\n")
    add("*(a) Nhiều kỳ, có chuyển tồn* (gần thực tế hơn): mỗi tuần đặt lên mức mục tiêu = số lượng của chính sách "
        "trừ tồn đầu tuần; hàng bảo quản lâu còn dư bán tiếp tuần sau, chịu chi phí vốn 1%/tháng; hàng dễ hư "
        "hỏng còn dư bị bỏ. Hàng thiếu quy ra lợi nhuận gộp bị mất.\n")
    add(md_table(pd.DataFrame({
        "Cách nhập": simc["policy"],
        "Tổng đặt": simc["units_ordered"].map(num),
        "Hàng thiếu": simc["units_short"].map(num),
        "Fill rate": simc["fill_rate"].map(pct),
        "Service level": simc["service_level"].map(pct),
        "Lợi nhuận mất": simc["lost_profit"].map(mil),
        "Hàng hỏng": simc["excess_value"].map(mil),
        "Chi phí vốn": simc["holding_cost"].map(mil),
        "Tổng chi phí": simc["total_cost"].map(mil),
    })))
    add(f"\nCó chuyển tồn, chính sách phân vị **tốt hơn cách nhẩm theo trung bình 28 ngày ở các chỉ số chính**: "
        f"hàng thiếu giảm {pct(1 - model_c.units_short / ma_c.units_short, 0)}, lợi nhuận mất giảm "
        f"{pct(1 - model_c.lost_profit / ma_c.lost_profit, 0)}, giá trị hàng hỏng giảm "
        f"{pct(1 - model_c.excess_value / ma_c.excess_value, 0)}, tổng chi phí giảm "
        f"{pct(1 - model_c.total_cost / ma_c.total_cost, 0)}; chỉ chi phí vốn nhỉnh hơn vì giữ nhiều hàng hơn. "
        "Mức nền có tổng chi phí cao nhất vì dự báo thừa nhiều, làm hỏng hàng dễ hư.\n")
    add("*(b) Một kỳ, không chuyển tồn* (giả định bi quan: mọi hàng dư coi như mất trọn giá vốn):\n")
    add(md_table(pd.DataFrame({
        "Cách nhập": sim1["policy"],
        "Tổng nhập": sim1["units_ordered"].map(num),
        "Hàng thiếu": sim1["units_short"].map(num),
        "Hàng dư": sim1["units_excess"].map(num),
        "Fill rate": sim1["fill_rate"].map(pct),
        "Service level": sim1["service_level"].map(pct),
        "Giá trị hàng dư": sim1["excess_value"].map(mil),
    })))
    add(f"\n- So với **mức nền**: hàng thiếu giảm {pct(1 - model_p.units_short / base_p.units_short, 0)}, "
        f"giá trị hàng dư giảm {pct(1 - model_p.excess_value / base_p.excess_value, 0)}.\n"
        f"- So với **trung bình 28 ngày**: hàng thiếu giảm {pct(1 - model_p.units_short / ma_p.units_short, 0)} "
        f"nhưng hàng dư tăng {pct(model_p.excess_value / ma_p.excess_value - 1, 0)}. Giả định này tính mọi hàng "
        "dư là mất trắng, kể cả nước ngọt hay hàng khô, nên phóng đại chi phí của việc nhập dư; vì vậy mô "
        "phỏng (a) là căn cứ chính.\n"
        f"- **Service level** của chính sách phân vị ({pct(model_c.service_level)} ở mô phỏng a) vẫn thấp hơn "
        f"mức nền ({pct(base_c.service_level)}): mức nền dự báo thừa đều nên ít tuần thiếu, đổi lại hàng hỏng "
        "nhiều nhất. Chính sách phân vị giảm tổng *lượng* hàng thiếu hơn là số tuần có thiếu hàng.\n"
        "- **Còn thiếu so với thực tế:** chưa có tồn kho đầu kỳ thật, thời gian giao hàng và quy cách đóng thùng "
        "(phải đặt theo bội số thùng/lốc). Khi áp dụng thật: lượng đặt = max(0, mức mục tiêu − tồn hiện có), "
        "làm tròn lên theo quy cách thùng.\n")
    add(f"![Ví dụ dự báo]({f5})\n")

    add("## 6. Giải thích dự báo bằng SHAP\n")
    add(f"![SHAP]({f4})\n")
    add("SHAP phân rã mỗi dự báo của LightGBM thành đóng góp của từng yếu tố. Lưu ý: SHAP chỉ giải thích "
        "thành phần LightGBM, một trong ba mô hình của tổ hợp, nên phản ánh xu hướng chính của dự báo chứ "
        "không phân rã chính xác con số đề xuất cuối cùng. LightGBM dùng hàm mục tiêu "
        "Tweedie (hợp với số đếm nhiều số 0), nên dự báo nằm trên thang log. Vì vậy trong ứng dụng, đóng góp "
        "được đổi thành **% tác động**, ví dụ \"ngày Chủ nhật làm dự báo giảm 12%\".\n")
    top = shap_g.head(3)["group"].tolist()
    add(f"- Ba yếu tố quan trọng nhất: **{top[0]}**, **{top[1]}**, **{top[2]}**. Mô hình dựa chủ yếu vào mức "
        "bán gần đây, tức hành vi giống một trung bình trượt thông minh, cộng thêm hiệu chỉnh theo ngày "
        "trong tuần và ngành hàng.\n"
        "- **Khuyến mãi không được đưa vào mô hình chính.** Giá bán trong dữ liệu chỉ quan sát được ở ngày "
        "có bán, nên dùng nó làm biến dự báo sẽ làm rò rỉ thông tin \"hôm đó có bán\". Ảnh hưởng của giảm "
        "giá được ước lượng riêng cho phần kịch bản (mục 7).\n")

    add("## 7. Kịch bản mô phỏng: giảm giá\n")
    add("Ước lượng sơ bộ: trong các ngày có bán, lượng bán ngày có chiết khấu trên 5% so với ngày bình thường "
        "(đã chuẩn hoá theo mức bán của từng nhóm hàng). Mỗi lượt là một nhóm hàng cấp 3 trong một ngày.\n")
    add(md_table(pd.DataFrame({
        "Ngành hàng": price["cat_l1"],
        "Số lượt nhóm hàng × ngày có chiết khấu": price["discount_days"],
        "Chiết khấu TB": price["avg_depth"].map(lambda v: pct(v) if pd.notna(v) else ""),
        "Lượng bán / ngày thường": price["uplift_ratio"].map(lambda v: num(v, 2) + " lần" if pd.notna(v) else ""),
        "Đủ tin cậy (≥ 30 lượt)": price["reliable"].map({True: "Có", False: "Không"}),
    })))
    add("\n**Cảnh báo quan trọng:** con số này **có thể bị phóng đại**. Ở cửa hàng tạp hoá, giá thấp hơn "
        "giá phổ biến thường do khách **mua theo thùng hoặc lốc** (giá sỉ). Khi đó mua nhiều mới được giá "
        "thấp, chứ không phải giá thấp khiến khách mua nhiều. Dữ liệu hiện tại chưa tách được hai hiệu ứng "
        "này. Ứng dụng hiển thị kết quả kịch bản kèm cảnh báo, và nên coi đó là **mức trần**.\n")

    add("## 8. Vòng lặp tự đánh giá và cải thiện\n")
    hist = evaluate_snapshots_df(con)
    st = drift_status(hist, info["holdout_wmape"]) if len(hist) else {"flagged_weeks": []}
    add("Mỗi lần chạy dự báo, hệ thống lưu **snapshot** (bảng `fc_snapshots`). Khi cửa hàng nạp file "
        "KiotViet mới trên ứng dụng: dữ liệu được ghép và khử trùng lặp, snapshot cũ được đối chiếu với thực "
        "tế, tính WMAPE, Bias và tracking signal. **Mọi tuần** đã đối chiếu đều được kiểm tra theo thứ tự thời "
        "gian: tuần nào có sai số vượt **1,3 lần** sai số kiểm định, hoặc tracking signal tích luỹ vượt ±4, được "
        "đánh dấu kích hoạt cảnh báo (lúc đó hệ thống huấn luyện lại). Trang \"Lịch sử và đánh giá\" hiện 8 "
        "tuần kiểm định được ghi lại theo đúng cơ chế này để minh hoạ"
        + (f"; trong đó {len(st['flagged_weeks'])} tuần kích hoạt cảnh báo "
           f"({', '.join(st['flagged_weeks'])}).\n" if st["flagged_weeks"] else ".\n"))
    add("**Phạm vi hiện tại:** khi chạy trên máy của cửa hàng, cơ sở dữ liệu được lưu lâu dài nên dữ liệu mới "
        "được ghép với dữ liệu cũ và đối chiếu với các snapshot trước. Trên bản triển khai công khai, dữ liệu "
        "tải lên chỉ dùng trong một phiên làm việc, nên vòng lặp chỉ phát huy khi nạp nhiều file trong cùng "
        "phiên. Vòng lặp mới được minh hoạ bằng dữ liệu kiểm định, chưa được kiểm chứng trên dữ liệu thật "
        "phát sinh sau ngày 30/06/2026.\n")

    add("## 9. Giới hạn\n")
    add("| Giới hạn | Hướng xử lý |\n|---|---|\n"
        "| 10 tháng dữ liệu, chỉ một kỳ Tết | Dự báo 7–28 ngày; hệ số Tết cập nhật qua vòng lặp |\n"
        "| Không có tồn kho, thời gian giao hàng | Mô phỏng chỉ so sánh tương đối; cần dữ liệu tồn kho để tính tồn kho an toàn |\n"
        "| Hết hàng chỉ suy đoán từ dữ liệu bán | Ứng dụng có danh sách để chủ cửa hàng xác nhận |\n"
        "| Dữ liệu rất thưa ở cấp nhóm nhỏ | Nhãn độ tin cậy; khuyến nghị dùng dự báo cấp cao hơn |\n"
        "| Mô hình chỉ tốt hơn trung bình 28 ngày một chút; ở cấp toàn cửa hàng còn kém hơn | Thử chọn mô hình theo kiểu nhu cầu; dùng song song trung bình 28 ngày cho kế hoạch vốn tổng |\n"
        "| Vòng lặp tự đánh giá chưa kiểm chứng trên dữ liệu mới | Chạy với dữ liệu từ tháng 7/2026 |\n"
        "| Mô hình không tốt hơn trung bình 28 ngày có ý nghĩa thống kê | Báo cáo đúng phạm vi; dùng giá trị ở chính sách nhập và giải thích |\n"
        "| Chronos-Bolt chỉ được đối chiếu sau khi đã chốt mô hình; dùng riêng thì dự báo thiếu khoảng 25% "
        "([chi tiết](chronos_comparison.md)) | Đưa tổ hợp LightGBM + AutoETS + IMAPA + Chronos vào danh sách dự tuyển, kiểm định lại trên dữ liệu từ tháng 7/2026 |
")
    return "\n".join(out)


def main() -> None:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        report = build(con)
    path = DOCS_DIR / "forecast_report.md"
    path.write_text(report, encoding="utf-8")
    print(f"Đã ghi {path.relative_to(DOCS_DIR.parent)}")


if __name__ == "__main__":
    main()
