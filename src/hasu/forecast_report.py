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
    lo, hi = con.execute("""SELECT q10, q90 FROM fc_ratio_quantiles q JOIN fc_profile p ON p.demand_class = q.grp
                            WHERE p.unique_id = ?""", [uid]).fetchone()
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.plot(hw.index, hw.values, color=viz.TEXT_2, marker="o", markersize=4, label="Thực tế")
    ax.fill_between(fw.index, fw.values * lo, fw.values * hi, color=viz.BLUE_RAMP[0], linewidth=0,
                    label="Khoảng 80%")
    ax.plot(fw.index, fw.values, color=viz.SERIES[0], marker="o", markersize=4, label="Dự báo")
    ax.axvline(end + pd.Timedelta(hours=12), color=viz.MUTED, linewidth=1)
    ax.set_ylim(0, None)
    ax.legend(loc="upper left", ncols=3)
    ax.set_ylabel("Số lượng / tuần")
    ax.set_title(f"Ví dụ: nhóm \"{uid}\", 10 tuần thực tế và 4 tuần dự báo")
    fig.autofmt_xdate()
    return save(fig, "15_vi_du_du_bao.png")


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
    s = sim.set_index("policy")
    base_p, model_p = s.loc["Mức nền: trung bình lịch sử"], s.loc["Mô hình + phân vị theo nhóm hàng"]
    ma_p = s.loc["Trung bình 28 ngày (cách nhẩm)"]

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
        f"{pct(lv[('Toàn cửa hàng', baseline)])}.\n"
        f"- **Nhóm hàng cấp 3** (đơn vị ra quyết định nhập hàng): WMAPE {pct(ch['WMAPE'])} so với "
        f"{pct(bl['WMAPE'])} của mức nền, **giảm {pct(1 - ch['WMAPE'] / bl['WMAPE'], 0)} sai số**. "
        f"Độ lệch (bias) {pct(ch['Bias'])}, trong khi mức nền dự báo thừa {pct(bl['Bias'])}.\n"
        f"- **Mô phỏng nhập hàng 8 tuần:** so với nhập theo mức nền, nhập theo mô hình kết hợp phân vị "
        f"giảm **{pct(1 - model_p.units_short / base_p.units_short, 0)} lượng hàng thiếu** và giảm "
        f"**{pct(1 - model_p.excess_value / base_p.excess_value, 0)} giá trị hàng dư** cùng lúc.\n")
    add("**Nói thẳng về giới hạn:** chỉ "
        f"{pct(info['share_improved'], 0)} số nhóm hàng có sai số thấp hơn mức nền khi xét riêng từng "
        f"nhóm, và mô hình chỉ tốt hơn trung bình trượt 28 ngày một chút ({pct(ch['WMAPE'])} so với "
        f"{pct(ma['WMAPE'])}). Với dữ liệu thưa như cửa hàng này, không mô hình nào dự báo chính xác từng "
        "nhóm hàng nhỏ theo tuần. Giá trị thực tế nằm ở: (1) dự báo tổng và nhóm lớn đáng tin cậy, "
        "(2) chính sách nhập hàng theo phân vị, (3) giải thích được và tự động hoá được.\n")

    add("## 1. Dữ liệu đầu vào và phân loại nhu cầu\n")
    add("- Mục tiêu: **số lượng bán lẻ** theo ngày của từng nhóm hàng cấp 3, đã loại đơn lớn, đơn tổ chức, "
        "xuất nội bộ, hàng trả, hàng tặng (xem báo cáo chất lượng dữ liệu).\n"
        "- **Lớp ngày thường:** ngày đóng cửa và vùng ±14 ngày quanh Tết được thay bằng trung vị cùng thứ "
        "trong các tuần lân cận trước khi huấn luyện, để mô hình học đường nền không bị đột biến kéo lệch. "
        "**Lớp ngày lễ:** khi kỳ dự báo rơi vào vùng Tết, dự báo được nhân hệ số số lượng theo ngành hàng "
        "(đo từ Tết 2026, xem báo cáo phân tích kinh doanh).\n"
        "- Phân loại kiểu nhu cầu theo **Syntetos–Boylan** (ADI: khoảng cách trung bình giữa hai ngày có bán; "
        "CV²: độ biến động lượng bán):\n")
    names = {"erratic": "Erratic: ngày nào cũng bán, lượng dao động",
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

    add("## 2. Phương pháp kiểm định\n")
    add("**Kiểm định trượt theo thời gian (walk-forward):** 12 tuần cuối được chia thành 12 cửa sổ. Ở mỗi "
        "cửa sổ, mô hình chỉ thấy dữ liệu tới trước tuần đó, dự báo 7 ngày, rồi so với thực tế. "
        "**4 tuần đầu** dùng để chọn mô hình, **8 tuần sau** dùng để báo cáo. Tách hai giai đoạn để con số "
        "báo cáo không bị \"đẹp giả\" do chọn mô hình trên chính dữ liệu chấm điểm.\n")
    add("| Chỉ số | Ý nghĩa |\n|---|---|\n"
        "| WMAPE | Tổng sai số tuyệt đối / tổng thực tế. Dùng được khi có nhiều tuần bán bằng 0 (MAPE thì không) |\n"
        "| MAE | Sai số tuyệt đối trung bình, theo đơn vị sản phẩm |\n"
        "| MdAPE | Trung vị sai số %, chỉ trên các tuần có bán |\n"
        "| Bias | Sai số có dấu: dương là dự báo thừa (chôn vốn), âm là dự báo thiếu (mất doanh thu) |\n"
        "| Tracking signal | Sai số tích luỹ / sai số trung bình. Lớn hơn 4 về trị tuyệt đối: mô hình lệch hệ thống |\n"
        "| Fill rate, service level | Tỷ lệ nhu cầu được đáp ứng; tỷ lệ tuần không thiếu hàng (trong mô phỏng) |\n")

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
    add(f"\n**Vì sao chọn mô hình kết hợp mà không chọn LightGBM** dù LightGBM có WMAPE thấp nhất trên 8 tuần "
        f"chấm ({pct(lgb_hold)})? Vì quyết định chọn chỉ được dựa trên 4 tuần đầu. Ở đó LightGBM đứng sau "
        "mô hình kết hợp. Thứ hạng thay đổi giữa hai giai đoạn cho thấy mô hình đơn lẻ không ổn định, trong khi "
        "mô hình kết hợp tốt đều ở cả hai giai đoạn và gần như không lệch. Chọn lại theo kết quả chấm điểm "
        "là gian lận dữ liệu kiểm tra.\n")
    add("**Theo kiểu nhu cầu (8 tuần chấm, WMAPE):**\n")
    piv = by_cls.pivot(index="label", columns="scope", values="WMAPE")
    piv = piv[[c for c in ["erratic", "lumpy", "intermittent"] if c in piv.columns]].sort_values("erratic")
    add(md_table(pd.DataFrame({"Mô hình": piv.index, **{c: piv[c].map(pct).values for c in piv.columns}})))
    add("\nNhóm erratic (bán hằng ngày, chiếm phần lớn sản lượng) dự báo khá tốt. Nhóm lumpy và intermittent "
        "rất khó dự báo theo tuần, đúng với lý thuyết: lượng bán của chúng gần như ngẫu nhiên.\n")

    add("## 4. Dự báo phân tầng: sai số theo cấp gộp\n")
    add(f"![Sai số theo cấp]({f2})\n")
    add(md_table(pd.DataFrame({
        "Cấp": LEVEL_ORDER,
        "Mô hình": [pct(lv[(l, champion)]) for l in LEVEL_ORDER],
        "Trung bình 28 ngày": [pct(lv[(l, 'MovingAvg28')]) for l in LEVEL_ORDER],
        "Mức nền": [pct(lv[(l, baseline)]) for l in LEVEL_ORDER],
    })))
    add("\nDự báo cấp nhóm hàng 3 được cộng lên các cấp trên (bottom-up), nên luôn khớp nhau. Sai số giảm "
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
        "phối chuẩn, phù hợp với nhu cầu gián đoạn.\n")
    add("**Mô phỏng nhập hàng trên 8 tuần chấm điểm** (hệ số phân vị ước lượng trên 4 tuần chọn, không "
        "nhìn trước):\n")
    add(md_table(pd.DataFrame({
        "Cách nhập": sim["policy"],
        "Tổng nhập": sim["units_ordered"].map(num),
        "Hàng thiếu": sim["units_short"].map(num),
        "Hàng dư": sim["units_excess"].map(num),
        "Fill rate": sim["fill_rate"].map(pct),
        "Giá trị hàng dư": sim["excess_value"].map(mil),
    })))
    add(f"\n- So với **mức nền**: hàng thiếu giảm {pct(1 - model_p.units_short / base_p.units_short, 0)}, "
        f"giá trị hàng dư giảm {pct(1 - model_p.excess_value / base_p.excess_value, 0)}: tốt hơn ở cả hai mặt.\n"
        f"- So với **trung bình 28 ngày**: hàng thiếu giảm {pct(1 - model_p.units_short / ma_p.units_short, 0)} "
        f"nhưng hàng dư tăng {pct(model_p.excess_value / ma_p.excess_value - 1, 0)}. Đây là đánh đổi có chủ "
        "đích: nhóm ngôi sao được ưu tiên đủ hàng.\n"
        "- **Giả định của mô phỏng:** hàng không mang sang tuần sau, nhập đầu tuần và có hàng ngay. Chưa có "
        "dữ liệu tồn kho và thời gian giao hàng thực tế, nên đây là so sánh tương đối giữa các cách nhập, "
        "không phải con số tiết kiệm thật.\n")
    add(f"![Ví dụ dự báo]({f5})\n")

    add("## 6. Giải thích dự báo bằng SHAP\n")
    add(f"![SHAP]({f4})\n")
    add("SHAP phân rã mỗi dự báo của LightGBM thành đóng góp của từng yếu tố. LightGBM dùng hàm mục tiêu "
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
        "(đã chuẩn hoá theo mức bán của từng nhóm hàng).\n")
    add(md_table(pd.DataFrame({
        "Ngành hàng": price["cat_l1"],
        "Số ngày có chiết khấu": price["discount_days"],
        "Chiết khấu TB": price["avg_depth"].map(lambda v: pct(v) if pd.notna(v) else ""),
        "Lượng bán / ngày thường": price["uplift_ratio"].map(lambda v: num(v, 2) + " lần" if pd.notna(v) else ""),
        "Đủ tin cậy (≥ 30 ngày)": price["reliable"].map({True: "Có", False: "Không"}),
    })))
    add("\n**Cảnh báo quan trọng:** con số này **có thể bị phóng đại**. Ở cửa hàng tạp hoá, giá thấp hơn "
        "giá phổ biến thường do khách **mua theo thùng hoặc lốc** (giá sỉ). Khi đó mua nhiều mới được giá "
        "thấp, chứ không phải giá thấp khiến khách mua nhiều. Dữ liệu hiện tại chưa tách được hai hiệu ứng "
        "này. Ứng dụng hiển thị kết quả kịch bản kèm cảnh báo, và nên coi đó là **mức trần**.\n")

    add("## 8. Vòng lặp cải thiện tự động\n")
    add("Mỗi lần chạy dự báo, hệ thống lưu **snapshot** (bảng `fc_snapshots`). Khi cửa hàng nạp file "
        "KiotViet mới trên ứng dụng: dữ liệu được ghép và khử trùng lặp, snapshot cũ được đối chiếu với thực "
        "tế, tính WMAPE, Bias và tracking signal. Nếu sai số vượt **1,3 lần** sai số kiểm định, hoặc tracking "
        "signal vượt 4, hệ thống cảnh báo suy giảm chất lượng và chạy lại mô hình. Trang \"Lịch sử và đánh "
        "giá\" hiện 8 tuần kiểm định được ghi lại theo đúng cơ chế này để minh hoạ.\n")

    add("## 9. Giới hạn\n")
    add("| Giới hạn | Hướng xử lý |\n|---|---|\n"
        "| 10 tháng dữ liệu, chỉ một kỳ Tết | Dự báo 7–28 ngày; hệ số Tết cập nhật qua vòng lặp |\n"
        "| Không có tồn kho, thời gian giao hàng | Mô phỏng chỉ so sánh tương đối; cần dữ liệu tồn kho để tính tồn kho an toàn |\n"
        "| Hết hàng chỉ suy đoán từ dữ liệu bán | Ứng dụng có danh sách để chủ cửa hàng xác nhận |\n"
        "| Dữ liệu rất thưa ở cấp nhóm nhỏ | Nhãn độ tin cậy; khuyến nghị dùng dự báo cấp cao hơn |\n"
        "| Chưa thử được Chronos (mạng chặn Hugging Face) | Code đã sẵn sàng, tự chạy khi tải được mô hình |\n")
    return "\n".join(out)


def main() -> None:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        report = build(con)
    path = DOCS_DIR / "forecast_report.md"
    path.write_text(report, encoding="utf-8")
    print(f"Đã ghi {path.relative_to(DOCS_DIR.parent)}")


if __name__ == "__main__":
    main()
