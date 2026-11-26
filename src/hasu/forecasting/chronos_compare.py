"""Đối chiếu mô hình nền tảng Chronos-Bolt với 12 mô hình dự tuyển.

    pip install -e ".[chronos]"
    python -m hasu.forecasting.run               # chạy trước để có fc_backtest_weekly
    python -m hasu.forecasting.chronos_compare   # ~10 giây trên CPU (lần đầu tải ~183 MB)

Chronos chạy trên đúng 87 nhóm hàng, đúng dữ liệu đã điền ngày đóng cửa và đúng 12 mốc cắt
của kiểm định trượt, rồi được ghép với kết quả đã lưu của 12 mô hình. Chronos KHÔNG tham gia
chọn mô hình: nó được chạy sau khi đã chốt danh sách dự tuyển, nên chỉ dùng để đối chiếu.
Kết quả ghi vào docs/chronos_comparison.md.
"""

from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

from hasu.config import DB_PATH, DOCS_DIR
from hasu.forecasting import data as fdata
from hasu.forecasting import models as fm
from hasu.forecasting.evaluate import H, N_WINDOWS, metrics_table, select_champion, to_weekly, tracking_signal, wmape
from hasu.forecasting.run import significance

MODEL_ID = "amazon/chronos-bolt-small"
CANDIDATES = ["HistoricAverage", "MovingAvg28", "SeasonalNaive", "AutoETS", "Croston", "ADIDA", "IMAPA", "TSB",
              "LightGBM", "Ens_LGB_IMAPA", "Ens_LGB_ETS_IMAPA", "Ens_LGB_IMAPA_MA"]
EXTRA = ["Chronos_median", "Chronos", "Ens_LGB_ETS_IMAPA_Chronos"]
LABELS = {**fm.MODEL_LABELS, "Chronos": "Chronos-Bolt (kỳ vọng)", "Chronos_median": "Chronos-Bolt (trung vị theo ngày)",
          "Ens_LGB_ETS_IMAPA_Chronos": "Kết hợp LightGBM + AutoETS + IMAPA + Chronos"}


def pct(x: float) -> str:
    return f"{x * 100:.1f}%".replace(".", ",").replace("-", "−")


def pval(p: float) -> str:
    return "< 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")


def chronos_weekly(con: duckdb.DuckDBPyConnection, pipe) -> pd.DataFrame:
    d_all = fdata.impute_abnormal_days(fdata.load_daily(con))
    first_cutoff = d_all["ds"].max() - pd.Timedelta(days=H * N_WINDOWS)
    profile_bt = fdata.classify_demand(d_all[d_all["ds"] <= first_cutoff])
    d = d_all[d_all["unique_id"].isin(profile_bt.loc[profile_bt["demand_class"] != "insufficient", "unique_id"])]
    saved = con.execute("SELECT * FROM fc_backtest_weekly").df()
    cutoffs = sorted(saved["cutoff"].unique())
    parts = []
    for c in cutoffs:
        hist = d[d["ds"] <= c]
        mean = fm.chronos_predict(pipe, hist, H, point="mean")
        med = fm.chronos_predict(pipe, hist, H, point="median").rename(columns={"Chronos": "Chronos_median"})
        parts.append(mean.merge(med, on=["unique_id", "ds"]).assign(cutoff=c))
    cv = pd.concat(parts).merge(d[["unique_id", "ds", "y_raw", "is_closed"]], on=["unique_id", "ds"])
    wk = to_weekly(cv, ["Chronos", "Chronos_median"])[["unique_id", "cutoff", "y", "Chronos", "Chronos_median"]]
    w = saved.merge(wk.rename(columns={"y": "y_chk"}), on=["unique_id", "cutoff"])
    assert len(w) == len(saved) and np.allclose(w["y"], w["y_chk"]), "Dữ liệu thực tế không khớp kết quả đã lưu"
    w["Ens_LGB_ETS_IMAPA_Chronos"] = w[["LightGBM", "AutoETS", "IMAPA", "Chronos"]].mean(axis=1)
    return w.drop(columns="y_chk")


def build_report(w: pd.DataFrame) -> str:
    champ = select_champion(w, CANDIDATES)
    hold, sel = w[w["phase"] == "holdout"], w[w["phase"] == "selection"]
    models = CANDIDATES + EXTRA
    m = (metrics_table(sel, models)[["model", "WMAPE"]].rename(columns={"WMAPE": "sel"})
         .merge(metrics_table(hold, models), on="model").sort_values("WMAPE"))
    out = ["# Đối chiếu với mô hình nền tảng Chronos-Bolt\n",
           f"_Sinh tự động bởi `python -m hasu.forecasting.chronos_compare`; mô hình `{MODEL_ID}`, zero-shot, "
           f"{w['unique_id'].nunique()} nhóm hàng × 12 mốc cắt. Chronos chạy sau khi đã chốt danh sách dự tuyển, "
           "nên không tham gia chọn mô hình._\n",
           "## 1. Sai số theo tuần ở cấp nhóm hàng cấp 3\n",
           "| Mô hình | WMAPE 4 tuần chọn | WMAPE 8 tuần chấm | MAE | MdAPE | Bias |", "|---|---:|---:|---:|---:|---:|"]
    for r in m.itertuples():
        name = LABELS.get(r.model, r.model) + (" **(được chọn)**" if r.model == champ else "")
        name += " _(đối chiếu)_" if r.model in EXTRA else ""
        out.append(f"| {name} | {pct(r.sel)} | {pct(r.WMAPE)} | {r.MAE:.2f} | {pct(r.MdAPE)} | {pct(r.Bias)} |".replace(".", ","))
    out += ["\n## 2. Sai số khi cộng lên các cấp\n", "| Cấp | " + " | ".join(LABELS[x] for x in
            [champ, "Chronos", "Ens_LGB_ETS_IMAPA_Chronos", "MovingAvg28"]) + " |", "|---|---:|---:|---:|---:|"]
    for level, keys in {"Nhóm hàng cấp 3": ["unique_id"], "Nhóm hàng cấp 2": ["cat_l2"],
                        "Ngành hàng cấp 1": ["cat_l1"], "Toàn cửa hàng": []}.items():
        g = hold.groupby([*keys, "cutoff"])[["y", champ, "Chronos", "Ens_LGB_ETS_IMAPA_Chronos", "MovingAvg28"]].sum()
        out.append(f"| {level} | " + " | ".join(pct(wmape(g["y"], g[x])) for x in
                                                 [champ, "Chronos", "Ens_LGB_ETS_IMAPA_Chronos", "MovingAvg28"]) + " |")
    out += ["\n## 3. Kiểm định chênh lệch (theo nhóm hàng, 8 tuần chấm)\n",
            "| So sánh | Tỷ lệ nhóm tốt hơn | Wilcoxon p | Diebold–Mariano p |", "|---|---:|---:|---:|"]
    for a, others in [("Chronos", [champ, "MovingAvg28", "HistoricAverage"]),
                      ("Ens_LGB_ETS_IMAPA_Chronos", [champ, "MovingAvg28"])]:
        for s in significance(hold, a, others).itertuples():
            out.append(f"| {LABELS[a]} so với {LABELS.get(s.compared_to, s.compared_to)} | {pct(s.share_series_better)} | "
                       f"{pval(s.wilcoxon_p)} | {pval(s.dm_p)} |")
    ts = pd.Series({u: tracking_signal(g["y"], g["Chronos"]) for u, g in hold.groupby("unique_id")})
    out += ["\n## 4. Nhận xét\n",
            f"- Nếu Chronos có mặt trong danh sách dự tuyển, quy tắc chọn theo 4 tuần đầu sẽ chọn "
            f"**{LABELS[select_champion(w, models)]}**.",
            f"- Chronos dự báo thiếu có hệ thống: {int((ts.abs() > 4).sum())}/{len(ts)} nhóm có |TS| > 4, nên sai số "
            "tăng mạnh khi cộng lên cấp toàn cửa hàng.",
            "- Lấy trung vị theo ngày rồi cộng lên tuần làm dự báo thiếu nặng với chuỗi thưa (trung vị ngày thường "
            "bằng 0); bản kỳ vọng (trung bình 9 phân vị) mới cùng bản chất với các mô hình khác.",
            "- Tổ hợp có Chronos gần như không lệch và có sai số thấp hơn mô hình được chọn, nhưng được đề xuất sau "
            "khi đã xem kết quả chấm điểm, nên cần kiểm định lại trên dữ liệu mới trước khi dùng.\n"]
    return "\n".join(out)


def main() -> None:
    pipe = fm.load_chronos(MODEL_ID)
    if pipe is None:
        raise SystemExit("Chưa cài được Chronos: chạy pip install -e \".[chronos]\"")
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        w = chronos_weekly(con, pipe)
    (DOCS_DIR / "chronos_comparison.md").write_text(build_report(w), encoding="utf-8")
    print("  đã ghi docs/chronos_comparison.md")


if __name__ == "__main__":
    main()
