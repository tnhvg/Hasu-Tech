"""Các mô hình dự báo.

| Mô hình             | Vai trò                                                         |
|---------------------|-----------------------------------------------------------------|
| HistoricAverage     | Mức nền bắt buộc: trung bình toàn bộ lịch sử (chỉ tiêu 1 trong README) |
| MovingAvg28         | Trung bình trượt 28 ngày: cách "nhẩm" phổ biến của chủ cửa hàng |
| SeasonalNaive       | Lặp lại tuần trước: mức nền có tính đến thứ trong tuần          |
| AutoETS             | Họ Holt-Winters, tự chọn cấu hình, mùa vụ tuần (7 ngày)         |
| CrostonOptimized    | Chuyên cho nhu cầu gián đoạn: tách "khi nào bán" và "bán bao nhiêu" |
| ADIDA, IMAPA        | Gộp chuỗi thưa theo khoảng thời gian rồi dự báo, dùng cho nhu cầu gián đoạn |
| TSB                 | Croston cải tiến, giảm dần dự báo khi lâu không bán (hợp với hàng sắp ngừng) |
| LightGBM            | Mô hình toàn cục học chung mọi nhóm hàng, giải thích được bằng SHAP |
| Chronos-Bolt        | Mô hình nền tảng (foundation model) dự báo không cần huấn luyện (tuỳ chọn) |
"""

from __future__ import annotations

import lightgbm as lgb
import numpy as np
import pandas as pd
from mlforecast import MLForecast
from mlforecast.lag_transforms import ExpandingMean, RollingMean, RollingStd
from statsforecast import StatsForecast
from statsforecast.models import (
    ADIDA,
    IMAPA,
    TSB,
    AutoETS,
    CrostonOptimized,
    HistoricAverage,
    SeasonalNaive,
    WindowAverage,
)

SEASON = 7

STATS_MODELS = [
    HistoricAverage(alias="HistoricAverage"),
    WindowAverage(window_size=28, alias="MovingAvg28"),
    SeasonalNaive(season_length=SEASON, alias="SeasonalNaive"),
    AutoETS(season_length=SEASON, alias="AutoETS"),
    CrostonOptimized(alias="Croston"),
    ADIDA(alias="ADIDA"),
    IMAPA(alias="IMAPA"),
    TSB(alpha_d=0.2, alpha_p=0.2, alias="TSB"),
]

# Mô hình kết hợp: trung bình cộng dự báo của các mô hình thành phần.
ENSEMBLES = {
    "Ens_LGB_IMAPA": ["LightGBM", "IMAPA"],
    "Ens_LGB_ETS_IMAPA": ["LightGBM", "AutoETS", "IMAPA"],
    "Ens_LGB_IMAPA_MA": ["LightGBM", "IMAPA", "MovingAvg28"],
}

# Tên hiển thị tiếng Việt
MODEL_LABELS = {
    "HistoricAverage": "Mức nền: trung bình lịch sử",
    "MovingAvg28": "Trung bình trượt 28 ngày",
    "SeasonalNaive": "Lặp lại tuần trước",
    "AutoETS": "AutoETS (Holt-Winters)",
    "Croston": "Croston",
    "ADIDA": "ADIDA",
    "IMAPA": "IMAPA",
    "TSB": "TSB",
    "LightGBM": "LightGBM (toàn cục)",
    "Chronos": "Chronos-Bolt (nền tảng)",
    "Ens_LGB_IMAPA": "Kết hợp LightGBM + IMAPA",
    "Ens_LGB_ETS_IMAPA": "Kết hợp LightGBM + AutoETS + IMAPA",
    "Ens_LGB_IMAPA_MA": "Kết hợp LightGBM + IMAPA + TB 28 ngày",
}


def add_ensembles(df: pd.DataFrame) -> list[str]:
    """Thêm cột dự báo của các mô hình kết hợp; trả về tên các cột đã thêm."""
    added = []
    for name, parts in ENSEMBLES.items():
        if all(p in df.columns for p in parts):
            df[name] = df[parts].mean(axis=1)
            added.append(name)
    return added


LGBM_PARAMS = dict(
    objective="tweedie",          # phù hợp với số đếm có nhiều số 0
    tweedie_variance_power=1.2,
    n_estimators=400,
    learning_rate=0.03,
    num_leaves=31,
    min_child_samples=30,
    subsample=0.8,
    subsample_freq=1,
    colsample_bytree=0.8,
    verbose=-1,
    random_state=42,
)

LAGS = [1, 2, 3, 7, 14, 21, 28]
LAG_TRANSFORMS = {
    1: [RollingMean(window_size=7), RollingMean(window_size=28), RollingStd(window_size=28),
        ExpandingMean()],
    7: [RollingMean(window_size=4 * 7)],
}
DATE_FEATURES = ["dayofweek", "day"]


def stats_forecaster(n_jobs: int = -1) -> StatsForecast:
    return StatsForecast(models=STATS_MODELS, freq="D", n_jobs=n_jobs)


def lgbm_forecaster(params: dict | None = None) -> MLForecast:
    return MLForecast(
        models={"LightGBM": lgb.LGBMRegressor(**(params or LGBM_PARAMS))},
        freq="D",
        lags=LAGS,
        lag_transforms=LAG_TRANSFORMS,
        date_features=DATE_FEATURES,
    )


def lgbm_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Khung dữ liệu cho LightGBM: thêm nhóm hàng cấp 1 làm đặc trưng tĩnh (static)."""
    out = df[["unique_id", "ds", "y", "cat_l1"]].copy()
    out["cat_l1"] = out["cat_l1"].astype("category")
    return out


# ---------------------------------------------------------------------------
# Chronos (tuỳ chọn): chỉ chạy khi tải được mô hình từ Hugging Face
# ---------------------------------------------------------------------------

def load_chronos(model_id: str = "amazon/chronos-bolt-small"):
    try:
        import torch
        from chronos import BaseChronosPipeline

        return BaseChronosPipeline.from_pretrained(model_id, device_map="cpu", torch_dtype=torch.float32)
    except Exception as exc:  # thiếu thư viện hoặc không tải được mô hình
        print(f"  [bỏ qua Chronos] {type(exc).__name__}: {str(exc).splitlines()[0][:120]}")
        return None


def chronos_predict(pipeline, df: pd.DataFrame, h: int) -> pd.DataFrame:
    """Dự báo trung vị h ngày cho mọi chuỗi trong df (cột unique_id, ds, y)."""
    import torch

    ids, contexts, last = [], [], []
    for uid, g in df.groupby("unique_id", sort=False):
        ids.append(uid)
        contexts.append(torch.tensor(g["y"].to_numpy(dtype=np.float32)))
        last.append(g["ds"].max())
    quantiles, _ = pipeline.predict_quantiles(context=contexts, prediction_length=h, quantile_levels=[0.5])
    rows = []
    for uid, q, ds0 in zip(ids, quantiles[:, :, 0].numpy(), last):
        for k in range(h):
            rows.append((uid, ds0 + pd.Timedelta(days=k + 1), max(float(q[k]), 0.0)))
    return pd.DataFrame(rows, columns=["unique_id", "ds", "Chronos"])
