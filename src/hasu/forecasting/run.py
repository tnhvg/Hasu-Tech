"""Chạy toàn bộ quy trình dự báo và ghi kết quả vào DuckDB.

    python -m hasu.forecasting.run

Các bước:
  1. Chuẩn bị chuỗi (lớp ngày thường), phân loại kiểu nhu cầu.
  2. Kiểm định trượt 12 tuần cho mọi mô hình; chọn mô hình trên 4 tuần đầu,
     báo cáo độ chính xác trên 8 tuần sau.
  3. Hiệu chỉnh khoảng dự báo (conformal) và mô phỏng nhập hàng trên 8 tuần holdout.
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

from hasu.config import DB_PATH
from hasu.forecasting import data as fdata
from hasu.forecasting import models as fm
from hasu.forecasting.evaluate import (
    H,
    N_WINDOWS,
    confidence_label,
    metrics_table,
    select_champion,
    to_weekly,
    tracking_signal,
    wmape,
)
from hasu.forecasting.monitor import save_snapshot
from hasu.forecasting.policy import SERVICE_POLICY, ratio_quantiles, service_class, simulate_orders

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
        FROM s""").fetchone()
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
    profile = fdata.classify_demand(d_all)
    eligible = profile.loc[profile["demand_class"] != "insufficient", "unique_id"]
    d = d_all[d_all["unique_id"].isin(eligible)].copy()
    data_until = d_all["ds"].max()
    log(f"  {len(eligible)} nhóm hàng đủ dữ liệu / {len(profile)} nhóm; dữ liệu tới {data_until:%d/%m/%Y}")

    log("2. Kiểm định trượt 12 tuần")
    chronos = fm.load_chronos() if use_chronos else None
    cv, models = backtest(d, chronos)
    weekly = to_weekly(cv, models).merge(profile[["unique_id", "demand_class", "cat_l1", "cat_l2"]],
                                         on="unique_id")
    champion = select_champion(weekly, models)
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

    log("3. Khoảng dự báo và mô phỏng nhập hàng")
    quad = con.execute("SELECT cat_l2, quadrant FROM mart_category_margin").df().set_index("cat_l2")["quadrant"]
    profile["quadrant"] = profile["cat_l2"].map(quad)
    profile["service_class"] = [service_class(a, b) for a, b in zip(profile["cat_l1"], profile["quadrant"])]
    profile["tau"] = profile["service_class"].map(lambda s: SERVICE_POLICY[s][0])
    groups = profile.set_index("unique_id")["demand_class"]
    # Hiệu chỉnh trên 4 tuần "selection" để mô phỏng trên holdout không bị rò rỉ thông tin
    rq_sel = ratio_quantiles(weekly[weekly["phase"] == "selection"], champion, groups, TAUS).set_index("grp")
    tau = hold["unique_id"].map(profile.set_index("unique_id")["tau"])
    cls = hold["unique_id"].map(groups)
    mult = [rq_sel.loc[c, f"q{int(t * 100)}"] if c in rq_sel.index else 1.0 for c, t in zip(cls, tau)]
    unit_cost = con.execute("""
        SELECT cat_l3, sum(quantity * unit_cost_filled) / sum(quantity) AS unit_cost
        FROM stg_sales_lines WHERE txn_channel = 'retail' AND quantity > 0 AND cost_fill_method IS NOT NULL
        GROUP BY 1""").df().set_index("cat_l3")["unit_cost"]
    sim = simulate_orders(hold, {
        "Mức nền: trung bình lịch sử": hold[BASELINE],
        "Trung bình 28 ngày (cách nhẩm)": hold["MovingAvg28"],
        "Mô hình: dự báo điểm": hold[champion],
        "Mô hình + phân vị theo nhóm hàng": hold[champion] * np.array(mult),
    }, unit_cost)
    # Hiệu chỉnh cuối cùng trên cả 12 tuần cho dự báo thật
    rq_all = ratio_quantiles(weekly, champion, groups, TAUS)

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
    rq = rq_all.set_index("grp")

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
    alloc["sku_forecast_week"] = alloc["forecast_week"] * alloc["share"]
    alloc["sku_order_qty"] = np.ceil(alloc["order_qty"] * alloc["share"])
    alloc = alloc.drop(columns=["unique_id"])

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
        "n_series": len(profile), "n_modelled": len(eligible), "chronos_used": chronos is not None,
    }]))
    save_snapshot(con, fc_daily, plan, champion, data_until, kind="Dự báo thật")
    backfill_snapshots(con, hold, champion)


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
