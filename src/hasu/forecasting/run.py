"""Chạy toàn bộ quy trình dự báo và ghi kết quả vào DuckDB.

    python -m hasu.forecasting.run

Các bước:
  1. Chuẩn bị chuỗi (lớp ngày thường), phân loại kiểu nhu cầu.
  2. Kiểm định trượt 12 tuần cho mọi mô hình; chọn mô hình trên 4 tuần đầu,
     báo cáo độ chính xác trên 8 tuần sau.
  3. Hiệu chỉnh khoảng dự báo (conformal) và mô phỏng nhập hàng trên 8 tuần holdout.
     Mọi tham số dùng cho kiểm định và mô phỏng (nhóm hàng đủ dữ liệu, kiểu nhu cầu,
     phân nhóm biên lợi nhuận -> τ, giá vốn, giá bán) chỉ tính từ dữ liệu trước mốc
     cắt tương ứng, để không rò rỉ thông tin tương lai.
  4. Huấn luyện lại trên toàn bộ dữ liệu, dự báo 28 ngày tới, áp lớp ngày lễ,
     đề xuất số lượng nhập tuần tới, phân bổ xuống mã hàng.
  5. Giải thích dự báo LightGBM bằng SHAP.
  6. Lưu snapshot dự báo để đối chiếu với thực tế khi có dữ liệu mới.
"""

from __future__ import annotations

from datetime import datetime

import duckdb
import numpy as np
import pandas as pd
import shap
from statsforecast import StatsForecast

from hasu.config import DB_PATH
from hasu.forecasting import data as fdata
from hasu.forecasting import models as fm
from scipy import stats

from hasu.forecasting.evaluate import (
    H,
    N_SELECTION,
    N_WINDOWS,
    confidence_label,
    metrics_table,
    select_champion,
    to_weekly,
    tracking_signal,
    wmape,
)
from hasu.forecasting.monitor import save_snapshot
from hasu.forecasting.policy import (
    PERISHABLE_L1,
    SERVICE_POLICY,
    ratio_quantiles,
    service_class,
    simulate_inventory,
    simulate_orders,
)

HORIZON = 28
TAUS = [0.1, 0.5, 0.55, 0.7, 0.8, 0.9]
BASELINE = "HistoricAverage"


def write(con: duckdb.DuckDBPyConnection, name: str, df: pd.DataFrame) -> None:
    con.register("tmp_df", df)
    con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM tmp_df")
    con.unregister("tmp_df")


# ---------------------------------------------------------------------------
# 2. Kiểm định trượt
# ---------------------------------------------------------------------------

def backtest(d: pd.DataFrame, chronos=None) -> tuple[pd.DataFrame, list[str]]:
    sf = fm.stats_forecaster()
    cv = sf.cross_validation(df=d[["unique_id", "ds", "y"]], h=H, step_size=H, n_windows=N_WINDOWS)
    mf = fm.lgbm_forecaster()
    cvl = mf.cross_validation(df=fm.lgbm_frame(d), h=H, step_size=H, n_windows=N_WINDOWS,
                              static_features=["cat_l1"])
    cv = cv.merge(cvl[["unique_id", "ds", "cutoff", "LightGBM"]], on=["unique_id", "ds", "cutoff"])
    if chronos is not None:
        parts = []
        for cutoff in sorted(cv["cutoff"].unique()):
            hist = d[d["ds"] <= cutoff]
            parts.append(fm.chronos_predict(chronos, hist, H).assign(cutoff=cutoff))
        cv = cv.merge(pd.concat(parts), on=["unique_id", "ds", "cutoff"])
    cv = cv.merge(d[["unique_id", "ds", "y_raw", "is_closed"]], on=["unique_id", "ds"])
    base_models = [c for c in cv.columns if c not in ("unique_id", "ds", "cutoff", "y", "y_raw", "is_closed")]
    cv[base_models] = cv[base_models].clip(lower=0)
    models = base_models + fm.add_ensembles(cv)
    return cv, models


def horizon_ratio_quantiles(d: pd.DataFrame, groups: pd.Series, taus: list[float],
                            n_windows: int = 9) -> pd.DataFrame:
    """Hiệu chỉnh conformal riêng cho tuần dự báo thứ 1..4.

    Kiểm định trượt với chân trời 28 ngày (bước 7 ngày) cho mô hình kết hợp
    LightGBM + AutoETS + IMAPA, cộng theo tuần thứ k của chân trời, rồi tính phân
    vị tỷ lệ thực tế / dự báo theo (kiểu nhu cầu, tuần thứ k). Độ bất định tăng
    theo chân trời nên khoảng của tuần 4 rộng hơn tuần 1.
    """
    sf = StatsForecast(models=[m for m in fm.STATS_MODELS if m.alias in ("AutoETS", "IMAPA")], freq="D", n_jobs=-1)
    cv = sf.cross_validation(df=d[["unique_id", "ds", "y"]], h=HORIZON, step_size=H, n_windows=n_windows)
    cvl = fm.lgbm_forecaster().cross_validation(df=fm.lgbm_frame(d), h=HORIZON, step_size=H, n_windows=n_windows,
                                                static_features=["cat_l1"])
    cv = cv.merge(cvl[["unique_id", "ds", "cutoff", "LightGBM"]], on=["unique_id", "ds", "cutoff"])
    cv = cv.merge(d[["unique_id", "ds", "y_raw", "is_closed"]], on=["unique_id", "ds"])
    cv[["AutoETS", "IMAPA", "LightGBM"]] = cv[["AutoETS", "IMAPA", "LightGBM"]].clip(lower=0)
    cv["fc"] = cv[["LightGBM", "AutoETS", "IMAPA"]].mean(axis=1)
    cv["hweek"] = (cv["ds"] - cv["cutoff"]).dt.days.sub(1) // 7 + 1
    w = (cv[~cv["is_closed"]].groupby(["unique_id", "cutoff", "hweek"], as_index=False)
         .agg(y=("y_raw", "sum"), fc=("fc", "sum")))
    out = []
    for k, g in w.groupby("hweek"):
        out.append(ratio_quantiles(g, "fc", groups, taus).assign(horizon_week=int(k)))
    return pd.concat(out, ignore_index=True)


def significance(hold: pd.DataFrame, champion: str, others: list[str]) -> pd.DataFrame:
    """Kiểm định chênh lệch sai số có ý nghĩa thống kê không.

    Với mỗi nhóm hàng, lấy sai số tuyệt đối trung bình theo tuần của mô hình được
    chọn trừ của mô hình so sánh (âm = mô hình được chọn tốt hơn). Gộp theo nhóm
    hàng trước để xử lý tương quan giữa các tuần của cùng một nhóm, rồi dùng:
      - kiểm định Wilcoxon dấu-hạng (không cần giả định phân phối chuẩn);
      - kiểm định Diebold–Mariano dạng gộp: thống kê t trên chênh lệch trung bình
        theo nhóm hàng.
    """
    rows = []
    for o in others:
        dl = (hold.assign(diff=(hold[champion] - hold["y"]).abs() - (hold[o] - hold["y"]).abs())
              .groupby("unique_id")["diff"].mean())
        dl = dl[dl != 0]
        w = stats.wilcoxon(dl)
        t = dl.mean() / (dl.std(ddof=1) / np.sqrt(len(dl)))
        rows.append({"model": champion, "compared_to": o, "n_series": int(len(dl)),
                     "mean_abs_err_diff": float(dl.mean()), "share_series_better": float((dl < 0).mean()),
                     "wilcoxon_p": float(w.pvalue), "dm_stat": float(t),
                     "dm_p": float(2 * stats.t.sf(abs(t), df=len(dl) - 1))})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. Dự báo tương lai
# ---------------------------------------------------------------------------

def forecast_future(d: pd.DataFrame) -> tuple[pd.DataFrame, object, list[pd.DataFrame]]:
    sf = fm.stats_forecaster()
    fc = sf.forecast(df=d[["unique_id", "ds", "y"]], h=HORIZON)
    mf = fm.lgbm_forecaster()
    mf.fit(fm.lgbm_frame(d), static_features=["cat_l1"])
    captured: list[pd.DataFrame] = []

    def capture(features: pd.DataFrame) -> pd.DataFrame:
        captured.append(features.copy())
        return features

    fl = mf.predict(h=HORIZON, before_predict_callback=capture)
    fc = fc.merge(fl, on=["unique_id", "ds"])
    cols = [c for c in fc.columns if c not in ("unique_id", "ds")]
    fc[cols] = fc[cols].clip(lower=0)
    fm.add_ensembles(fc)
    return fc, mf.models_["LightGBM"], captured


def apply_holiday_layer(fc: pd.DataFrame, meta: pd.DataFrame, factors: pd.DataFrame, col: str) -> pd.DataFrame:
    """Lớp ngày lễ: nhân hệ số số lượng theo nhóm hàng cấp 1 khi ngày dự báo rơi vào vùng Tết."""
    fc = fc.merge(meta[["unique_id", "cat_l1"]], on="unique_id", how="left")
    k = fdata.tet_offset(fc["ds"])
    fc["holiday_window"] = np.select([k.between(-14, -1), k.between(0, 13)], ["Trước Tết", "Sau Tết"], default="")
    f = factors.rename(columns={"tet_window": "holiday_window"})
    fc = fc.merge(f, on=["cat_l1", "holiday_window"], how="left")
    fc["holiday_factor"] = fc["qty_factor"].fillna(1.0)
    fc["forecast"] = fc[col] * fc["holiday_factor"]
    return fc.drop(columns=["qty_factor"])


# ---------------------------------------------------------------------------
# 5. SHAP
# ---------------------------------------------------------------------------

FEATURE_GROUPS = {
    "lag1": "Bán hôm trước", "lag2": "Bán 2–3 ngày trước", "lag3": "Bán 2–3 ngày trước",
    "lag7": "Cùng thứ tuần trước", "lag14": "Cùng thứ 2–4 tuần trước", "lag21": "Cùng thứ 2–4 tuần trước",
    "lag28": "Cùng thứ 2–4 tuần trước",
    "rolling_mean_lag1_window_size7": "Xu hướng 7 ngày",
    "rolling_mean_lag1_window_size28": "Xu hướng nền 28 ngày",
    "rolling_mean_lag7_window_size28": "Xu hướng nền 28 ngày",
    "expanding_mean_lag1": "Mức bán dài hạn",
    "rolling_std_lag1_window_size28": "Độ biến động 28 ngày",
    "dayofweek": "Ngày trong tuần", "day": "Ngày trong tháng", "cat_l1": "Ngành hàng",
}


def explain(model, captured: list[pd.DataFrame], fc_dates: pd.DataFrame, train_X: pd.DataFrame):
    """SHAP cho mô hình LightGBM.

    Với mục tiêu tweedie, LightGBM dự báo log(nhu cầu), nên SHAP cộng dồn trên
    thang log. Đổi sang dạng "% tác động": exp(shap) - 1, tức yếu tố đó làm dự
    báo tăng/giảm bao nhiêu phần trăm so với mức cơ sở.
    """
    explainer = shap.TreeExplainer(model)
    # Toàn cục: trên mẫu dữ liệu huấn luyện
    sample = train_X.sample(min(5000, len(train_X)), random_state=0)
    sv = explainer.shap_values(sample)
    glob = pd.DataFrame({"feature": sample.columns, "mean_abs_shap": np.abs(sv).mean(axis=0)})
    glob["group"] = glob["feature"].map(FEATURE_GROUPS).fillna(glob["feature"])
    glob = glob.groupby("group", as_index=False)["mean_abs_shap"].sum().sort_values("mean_abs_shap", ascending=False)

    # Cục bộ: cho 7 ngày dự báo đầu tiên
    local = []
    for step, X in enumerate(captured[:H]):
        vals = explainer.shap_values(X)
        ids = fc_dates["unique_id"].unique()
        day = fc_dates.groupby("unique_id")["ds"].apply(lambda s: s.sort_values().iloc[step])
        for i, uid in enumerate(ids):
            row = pd.DataFrame({"feature": X.columns, "shap": vals[i]})
            row["group"] = row["feature"].map(FEATURE_GROUPS).fillna(row["feature"])
            row = row.groupby("group", as_index=False)["shap"].sum()
            row["unique_id"], row["ds"] = uid, day[uid]
            local.append(row)
    local = pd.concat(local, ignore_index=True)
    local["base_value"] = float(np.atleast_1d(explainer.expected_value)[0])
    local["effect_pct"] = np.exp(local["shap"]) - 1
    return glob, local


# ---------------------------------------------------------------------------
# Phản ứng giá (cho kịch bản mô phỏng)
# ---------------------------------------------------------------------------

def price_response(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Ước lượng sơ bộ: trong các ngày CÓ bán, lượng bán ngày có chiết khấu > 5% so với
    ngày không chiết khấu, chuẩn hoá theo mức bán trung bình của từng nhóm hàng cấp 3.

    Giới hạn: chỉ quan sát được ngày có bán, khuyến mãi ít (khoảng 7% số ngày), nên
    đây chỉ là ước lượng định hướng, độ tin cậy thấp.
    """
    df = con.execute("""
        WITH s AS (
            SELECT cat_l1, cat_l3, quantity, discount_depth,
                   quantity / avg(quantity) OVER (PARTITION BY cat_l3) AS rel_qty
            FROM fct_retail_daily_category WHERE quantity > 0 AND discount_depth IS NOT NULL
        )
        SELECT cat_l1,
               count(*) FILTER (discount_depth > 0.05) AS discount_days,
               avg(discount_depth) FILTER (discount_depth > 0.05) AS avg_depth,
               avg(rel_qty) FILTER (discount_depth > 0.05) AS rel_qty_discount,
               avg(rel_qty) FILTER (discount_depth <= 0.05) AS rel_qty_normal
        FROM s GROUP BY 1
    """).df()
    df["uplift_ratio"] = df["rel_qty_discount"] / df["rel_qty_normal"]
    # Độ nhạy: % tăng lượng bán cho mỗi 1% giảm giá (tuyến tính quanh mức quan sát)
    df["uplift_per_pct"] = ((df["uplift_ratio"] - 1) / (df["avg_depth"] * 100)).clip(lower=0)
    df["reliable"] = df["discount_days"] >= 30
    total = con.execute("""
        WITH s AS (SELECT quantity, discount_depth, quantity / avg(quantity) OVER (PARTITION BY cat_l3) AS r
                   FROM fct_retail_daily_category WHERE quantity > 0 AND discount_depth IS NOT NULL)
        SELECT avg(r) FILTER (discount_depth > 0.05) / avg(r) FILTER (discount_depth <= 0.05),
               avg(discount_depth) FILTER (discount_depth > 0.05)
        FROM s""").fetchall()[0]
    df["store_uplift_per_pct"] = max((total[0] - 1) / (total[1] * 100), 0)
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(use_chronos: bool = True) -> None:
    with duckdb.connect(str(DB_PATH)) as con:
        run_forecasting(con, use_chronos=use_chronos)


def run_forecasting(con: duckdb.DuckDBPyConnection, use_chronos: bool = True, log=print) -> None:
    """Toàn bộ quy trình dự báo trên một kết nối DuckDB đã có các bảng mart."""
    log("1. Chuẩn bị chuỗi thời gian")
    d_all = fdata.impute_abnormal_days(fdata.load_daily(con))
    data_until = d_all["ds"].max()
    # Mốc cắt của kiểm định trượt: cửa sổ đầu tiên và cửa sổ holdout đầu tiên
    first_cutoff = data_until - pd.Timedelta(days=H * N_WINDOWS)
    holdout_cutoff = first_cutoff + pd.Timedelta(days=H * N_SELECTION)
    # Phân loại dùng cho kiểm định: chỉ dữ liệu trước cửa sổ đầu tiên (không nhìn trước)
    profile_bt = fdata.classify_demand(d_all[d_all["ds"] <= first_cutoff])
    eligible_bt = profile_bt.loc[profile_bt["demand_class"] != "insufficient", "unique_id"]
    # Phân loại dùng cho dự báo thật: toàn bộ dữ liệu hiện có
    profile = fdata.classify_demand(d_all)
    eligible = profile.loc[profile["demand_class"] != "insufficient", "unique_id"]
    d = d_all[d_all["unique_id"].isin(eligible)].copy()
    d_bt = d_all[d_all["unique_id"].isin(eligible_bt)].copy()
    log(f"  {len(eligible)} nhóm hàng đủ dữ liệu / {len(profile)} nhóm; dữ liệu tới {data_until:%d/%m/%Y}")
    log(f"  kiểm định: {len(eligible_bt)} nhóm đủ dữ liệu tính tới {first_cutoff:%d/%m/%Y}")

    log("2. Kiểm định trượt 12 tuần")
    chronos = fm.load_chronos() if use_chronos else None
    cv, models = backtest(d_bt, chronos)
    weekly = to_weekly(cv, models).merge(profile_bt[["unique_id", "demand_class", "cat_l1", "cat_l2"]],
                                         on="unique_id")
    # Chronos chỉ là phương án đối chiếu (chạy sau khi đã chốt danh sách dự tuyển), không tham gia chọn mô hình
    champion = select_champion(weekly, [m for m in models if m != "Chronos"])
    log(f"  mô hình được chọn (trên 4 tuần đầu): {champion}")
    hold = weekly[weekly["phase"] == "holdout"]

    m_all = metrics_table(hold, models).assign(scope="Tổng thể")
    m_cls = metrics_table(hold, models, by=["demand_class"]).rename(columns={"demand_class": "scope"})
    m_sel = metrics_table(weekly[weekly["phase"] == "selection"], models).assign(scope="Giai đoạn chọn mô hình")
    metrics = pd.concat([m_all, m_cls, m_sel], ignore_index=True)
    metrics["is_champion"] = metrics["model"] == champion
    metrics["label"] = metrics["model"].map(fm.MODEL_LABELS).fillna(metrics["model"])

    # Độ chính xác khi cộng dự báo lên các cấp cao hơn (nhóm cấp 2, ngành, toàn cửa hàng)
    compare = [champion, BASELINE, "MovingAvg28"]
    lv = []
    for level, keys in {"Nhóm hàng cấp 3": ["unique_id"], "Nhóm hàng cấp 2": ["cat_l2"],
                        "Ngành hàng cấp 1": ["cat_l1"], "Toàn cửa hàng": []}.items():
        g = hold.groupby([*keys, "cutoff"])[["y", *compare]].sum()
        for mdl in compare:
            lv.append({"level": level, "model": mdl, "label": fm.MODEL_LABELS.get(mdl, mdl),
                       "WMAPE": wmape(g["y"], g[mdl]),
                       "Bias": float((g[mdl] - g["y"]).sum() / g["y"].sum())})
    levels = pd.DataFrame(lv)

    # Chỉ số theo từng nhóm hàng
    per = []
    for uid, g in hold.groupby("unique_id"):
        per.append({
            "unique_id": uid,
            "wmape": wmape(g["y"], g[champion]),
            "wmape_baseline": wmape(g["y"], g[BASELINE]),
            "bias": float((g[champion] - g["y"]).sum() / max(g["y"].sum(), 1e-9)),
            "tracking_signal": tracking_signal(g["y"], g[champion]),
            "holdout_qty": float(g["y"].sum()),
        })
    per = pd.DataFrame(per)
    per["improved"] = per["wmape"] < per["wmape_baseline"]
    profile = profile.merge(per, on="unique_id", how="left")
    profile["confidence"] = [confidence_label(w, c) for w, c in zip(profile["wmape"], profile["demand_class"])]
    sig = significance(hold, champion, ["MovingAvg28", BASELINE, "LightGBM", *(["Chronos"] if "Chronos" in models else [])])

    log("3. Khoảng dự báo và mô phỏng nhập hàng")
    # Dự báo thật: phân nhóm biên lợi nhuận trên toàn bộ dữ liệu
    quad = con.execute("SELECT cat_l2, quadrant FROM mart_category_margin").df().set_index("cat_l2")["quadrant"]
    profile["quadrant"] = profile["cat_l2"].map(quad)
    profile["service_class"] = [service_class(a, b) for a, b in zip(profile["cat_l1"], profile["quadrant"])]
    profile["tau"] = profile["service_class"].map(lambda s: SERVICE_POLICY[s][0])
    groups = profile.set_index("unique_id")["demand_class"]

    # Mô phỏng trên holdout: mọi tham số chỉ từ dữ liệu trước tuần holdout đầu tiên.
    #   - phân nhóm biên lợi nhuận (-> τ) tính lại với giá vốn THẬT trước mốc cắt
    #   - hệ số phân vị hiệu chỉnh trên 4 tuần "selection"
    #   - giá vốn, giá bán trung bình của từng nhóm hàng trước mốc cắt
    cut = pd.Timestamp(holdout_cutoff).date()
    quad_bt = con.execute("SELECT cat_l2, quadrant FROM category_margin(?, true)", [cut]).df() \
        .set_index("cat_l2")["quadrant"]
    meta_bt = profile_bt.set_index("unique_id")
    sc_bt = pd.Series([service_class(a, quad_bt.get(b)) for a, b in zip(meta_bt["cat_l1"], meta_bt["cat_l2"])],
                      index=meta_bt.index)
    groups_bt = meta_bt["demand_class"]
    rq_sel = ratio_quantiles(weekly[weekly["phase"] == "selection"], champion, groups_bt, TAUS).set_index("grp")
    tau = hold["unique_id"].map(sc_bt.map(lambda s: SERVICE_POLICY[s][0]))
    cls = hold["unique_id"].map(groups_bt)
    mult = [rq_sel.loc[c, f"q{int(t * 100)}"] if c in rq_sel.index else 1.0 for c, t in zip(cls, tau)]
    prices = con.execute("""
        SELECT cat_l3, sum(quantity * unit_cost) / sum(quantity) AS unit_cost,
               sum(line_revenue) / sum(quantity) AS unit_price
        FROM stg_sales_lines
        WHERE txn_channel = 'retail' AND quantity > 0 AND NOT is_zero_price
          AND cost_fill_method = 'actual' AND sale_date <= ?
        GROUP BY 1""", [cut]).df().set_index("cat_l3")
    policies = {
        "Mức nền: trung bình lịch sử": hold[BASELINE],
        "Trung bình 28 ngày (cách nhẩm)": hold["MovingAvg28"],
        "Mô hình: dự báo điểm": hold[champion],
        "Mô hình + phân vị theo nhóm hàng": hold[champion] * np.array(mult),
    }
    perishable = meta_bt["cat_l1"].isin(PERISHABLE_L1)
    sim = pd.concat([
        simulate_orders(hold, policies, prices["unit_cost"]),
        simulate_inventory(hold, policies, perishable, prices["unit_cost"], prices["unit_price"]),
    ], ignore_index=True)
    # Hiệu chỉnh cuối cùng cho dự báo thật: tuần 1 trên cả 12 tuần kiểm định,
    # tuần 2-4 bằng kiểm định riêng với chân trời 28 ngày.
    rq_all = ratio_quantiles(weekly, champion, groups_bt, TAUS).assign(horizon_week=1)
    if champion == "Ens_LGB_ETS_IMAPA":
        rq_h = horizon_ratio_quantiles(d_bt, groups_bt, TAUS)
        rq_all = pd.concat([rq_all, rq_h[rq_h["horizon_week"] > 1]], ignore_index=True)
    unit_cost = con.execute("""
        SELECT cat_l3, sum(quantity * unit_cost_filled) / sum(quantity) AS unit_cost
        FROM stg_sales_lines WHERE txn_channel = 'retail' AND quantity > 0 AND cost_fill_method IS NOT NULL
        GROUP BY 1""").df().set_index("cat_l3")["unit_cost"]

    log("4. Dự báo 28 ngày tới")
    fc, lgb_model, captured = forecast_future(d)
    fc = apply_holiday_layer(fc, profile, fdata.holiday_factors(con), champion)
    fc["model"] = champion
    # Nhóm hàng chưa đủ dữ liệu: trung bình 8 tuần gần nhất, không dùng mô hình
    insuff = profile.loc[profile["demand_class"] == "insufficient", "unique_id"]
    recent = d_all[(d_all["unique_id"].isin(insuff)) & (d_all["ds"] > data_until - pd.Timedelta(days=56))
                   & ~d_all["is_closed"]]
    avg = recent.groupby("unique_id")["y_raw"].mean()
    future_days = pd.date_range(data_until + pd.Timedelta(days=1), periods=HORIZON)
    fc_ins = pd.DataFrame([(u, ds, float(avg.get(u, 0.0))) for u in insuff for ds in future_days],
                          columns=["unique_id", "ds", "forecast"]).assign(model="TB 8 tuần (chưa đủ dữ liệu)")
    fc_ins = fc_ins.merge(profile[["unique_id", "cat_l1"]], on="unique_id")
    keep = ["unique_id", "ds", "forecast", "model", "cat_l1", "holiday_window", "holiday_factor",
            *models_in(fc, models)]
    fc_daily = pd.concat([fc[[c for c in keep if c in fc.columns]], fc_ins], ignore_index=True)

    # Đề xuất nhập hàng tuần tới
    week1 = fc_daily[fc_daily["ds"] <= data_until + pd.Timedelta(days=7)]
    plan = week1.groupby("unique_id", as_index=False)["forecast"].sum().rename(columns={"forecast": "forecast_week"})
    plan = plan.merge(profile[["unique_id", "cat_l1", "cat_l2", "demand_class", "confidence", "service_class",
                               "tau", "wmape", "quadrant"]], on="unique_id")
    rq = rq_all[rq_all["horizon_week"] == 1].set_index("grp")

    def q(cls_, col):
        return rq.loc[cls_, col] if cls_ in rq.index else np.nan

    plan["lower_80"] = [f * q(c, "q10") for f, c in zip(plan["forecast_week"], plan["demand_class"])]
    plan["upper_80"] = [f * q(c, "q90") for f, c in zip(plan["forecast_week"], plan["demand_class"])]
    plan["order_qty"] = [np.ceil(f * q(c, f"q{int(t * 100)}")) if c in rq.index else np.ceil(f)
                         for f, c, t in zip(plan["forecast_week"], plan["demand_class"], plan["tau"])]
    plan["week_start"] = data_until + pd.Timedelta(days=1)
    plan["unit_cost"] = plan["unique_id"].map(unit_cost)
    plan["order_value"] = plan["order_qty"] * plan["unit_cost"]
    plan = plan.sort_values("forecast_week", ascending=False)

    # Phân bổ xuống mã hàng theo thị phần 8 tuần gần nhất
    share = con.execute("""
        WITH r AS (
            SELECT cat_l3, sku, any_value(product_name) AS product_name, sum(quantity) AS qty
            FROM stg_sales_lines
            WHERE txn_channel = 'retail' AND NOT is_return AND NOT is_zero_price
              AND sale_date > (SELECT max(sale_date) FROM stg_sales_lines) - INTERVAL 56 DAY
            GROUP BY 1, 2
        )
        SELECT *, qty / sum(qty) OVER (PARTITION BY cat_l3) AS share,
               row_number() OVER (PARTITION BY cat_l3 ORDER BY qty DESC) AS rk
        FROM r QUALIFY rk <= 8""").df()
    alloc = share.merge(plan[["unique_id", "order_qty", "forecast_week"]], left_on="cat_l3", right_on="unique_id")
    alloc = allocate_skus(alloc)

    log("5. Giải thích dự báo (SHAP)")
    train_X = fm.lgbm_forecaster().preprocess(fm.lgbm_frame(d), static_features=["cat_l1"]).drop(
        columns=["unique_id", "ds", "y"])
    fc_dates = fc[["unique_id", "ds"]]
    shap_global, shap_local = explain(lgb_model, captured, fc_dates, train_X)

    log("6. Ghi kết quả")
    write(con, "fc_profile", profile)
    write(con, "fc_metrics", metrics)
    write(con, "fc_metrics_levels", levels)
    write(con, "fc_backtest_weekly", weekly)
    write(con, "fc_simulation", sim)
    write(con, "fc_significance", sig)
    write(con, "fc_ratio_quantiles", rq_all)
    write(con, "fc_forecast_daily", fc_daily)
    write(con, "fc_order_plan", plan)
    write(con, "fc_sku_allocation", alloc)
    write(con, "fc_shap_global", shap_global)
    write(con, "fc_shap_local", shap_local)
    write(con, "fc_price_response", price_response(con))
    write(con, "fc_run_info", pd.DataFrame([{
        "run_at": datetime.now(), "data_until": data_until, "champion": champion,
        "champion_label": fm.MODEL_LABELS.get(champion, champion),
        "holdout_wmape": float(m_all.loc[m_all["model"] == champion, "WMAPE"].iloc[0]),
        "baseline_wmape": float(m_all.loc[m_all["model"] == BASELINE, "WMAPE"].iloc[0]),
        "store_wmape": float(levels.query("level == 'Toàn cửa hàng' and model == @champion")["WMAPE"].iloc[0]),
        "share_improved": float(per["improved"].mean()),
        "n_series": len(profile), "n_modelled": len(eligible), "n_backtest": len(eligible_bt),
        "first_cutoff": first_cutoff, "holdout_cutoff": holdout_cutoff, "chronos_used": chronos is not None,
    }]))
    save_snapshot(con, fc_daily, plan, champion, data_until, kind="Dự báo thật")
    backfill_snapshots(con, hold, champion)


def allocate_skus(alloc: pd.DataFrame) -> pd.DataFrame:
    """Chia đề xuất nhập của nhóm hàng xuống tối đa 8 mã bán chạy nhất.

    Thị phần được chuẩn hoá lại trong 8 mã này (tổng = 100%), rồi chia số nguyên
    theo phương pháp phần dư lớn nhất, để tổng số lượng của các mã đúng bằng đề
    xuất của nhóm (không hụt, không dư do làm tròn).
    """
    a = alloc.copy()
    a["share"] = a["qty"] / a.groupby("cat_l3")["qty"].transform("sum")
    a["sku_forecast_week"] = a["forecast_week"] * a["share"]
    raw = a["order_qty"] * a["share"]
    base = np.floor(raw)
    a["sku_order_qty"] = base
    rest = (a["order_qty"] - base.groupby(a["cat_l3"]).transform("sum")).round().astype(int)
    a["_frac"] = raw - base
    for cat, g in a.groupby("cat_l3"):
        k = int(rest.loc[g.index[0]])
        if k > 0:
            a.loc[g.sort_values("_frac", ascending=False).index[:k], "sku_order_qty"] += 1
    return a.drop(columns=["unique_id", "_frac"])


def models_in(df: pd.DataFrame, models: list[str]) -> list[str]:
    return [m for m in models if m in df.columns]


def backfill_snapshots(con: duckdb.DuckDBPyConnection, hold: pd.DataFrame, champion: str) -> None:
    """Ghi lại các dự báo của 8 tuần holdout như thể chúng được lưu mỗi tuần, để trang
    "Lịch sử và đánh giá" có dữ liệu minh hoạ vòng lặp đối chiếu dự báo - thực tế."""
    con.execute("DELETE FROM fc_snapshots WHERE kind = 'Mô phỏng lại'")
    for cutoff, g in hold.groupby("cutoff"):
        rows = g[["unique_id", champion]].rename(columns={champion: "forecast_week"})
        rows = rows.assign(run_id=f"backtest-{pd.Timestamp(cutoff):%Y%m%d}", created_at=pd.Timestamp(cutoff),
                           data_until=pd.Timestamp(cutoff), week_start=pd.Timestamp(cutoff) + pd.Timedelta(days=1),
                           model=champion, order_qty=np.nan, kind="Mô phỏng lại")
        con.register("tmp_df", rows)
        con.execute("INSERT INTO fc_snapshots BY NAME SELECT * FROM tmp_df")
        con.unregister("tmp_df")


if __name__ == "__main__":
    main()
