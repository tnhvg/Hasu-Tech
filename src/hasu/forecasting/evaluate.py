"""Kiểm định trượt theo thời gian (walk-forward) và các chỉ số đánh giá.

Quy trình: chia 12 tuần cuối thành 12 cửa sổ. Ở mỗi cửa sổ, mô hình chỉ được
thấy dữ liệu tới trước ngày bắt đầu cửa sổ, dự báo 7 ngày, rồi so với thực tế.
  - 4 cửa sổ đầu ("selection"): dùng để CHỌN mô hình cho từng kiểu nhu cầu.
  - 8 cửa sổ sau ("holdout"): dùng để BÁO CÁO độ chính xác. Không dùng để chọn
    mô hình, nên con số không bị "đẹp giả".

Đơn vị đánh giá chính là TUẦN x NHÓM HÀNG, vì quyết định nhập hàng của cửa hàng
là theo tuần. Ngày đóng cửa không được tính.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

H = 7
N_WINDOWS = 12
N_SELECTION = 4


def wmape(y: pd.Series, f: pd.Series) -> float:
    """Tổng sai số tuyệt đối / tổng thực tế. Dùng được khi có nhiều ngày bán bằng 0."""
    denom = np.abs(y).sum()
    return float(np.abs(y - f).sum() / denom) if denom else np.nan


def bias(y: pd.Series, f: pd.Series) -> float:
    """Sai số có dấu, tương đối: > 0 là dự báo thừa, < 0 là dự báo thiếu."""
    denom = np.abs(y).sum()
    return float((f - y).sum() / denom) if denom else np.nan


def mdape(y: pd.Series, f: pd.Series) -> float:
    """Trung vị sai số phần trăm, chỉ tính các tuần có bán (> 0)."""
    m = y > 0
    return float(np.median(np.abs(y[m] - f[m]) / y[m])) if m.any() else np.nan


def tracking_signal(y: pd.Series, f: pd.Series) -> float:
    """Tổng sai số tích luỹ / sai số tuyệt đối trung bình. |TS| > 4: mô hình lệch hệ thống."""
    e = y - f
    mad = np.abs(e).mean()
    return float(e.sum() / mad) if mad else 0.0


def to_weekly(cv: pd.DataFrame, model_cols: list[str]) -> pd.DataFrame:
    """Cộng dự báo ngày thành tuần theo từng cửa sổ, chỉ trên ngày mở cửa."""
    open_days = cv[~cv["is_closed"]]
    agg = {c: "sum" for c in ["y_raw", *model_cols]}
    w = open_days.groupby(["unique_id", "cutoff"], as_index=False).agg(agg)
    w = w.rename(columns={"y_raw": "y"})
    windows = sorted(w["cutoff"].unique())
    w["window"] = w["cutoff"].map({c: i + 1 for i, c in enumerate(windows)})
    w["phase"] = np.where(w["window"] <= N_SELECTION, "selection", "holdout")
    return w


def metrics_table(weekly: pd.DataFrame, model_cols: list[str], by: list[str] | None = None) -> pd.DataFrame:
    """Bảng MAE, WMAPE, Bias, MdAPE cho mỗi mô hình (và theo nhóm nếu có `by`)."""
    rows = []
    groups = weekly.groupby(by) if by else [((), weekly)]
    for key, g in groups:
        key = key if isinstance(key, tuple) else (key,)
        for m in model_cols:
            rows.append({
                **dict(zip(by or [], key)),
                "model": m,
                "MAE": float(np.abs(g["y"] - g[m]).mean()),
                "WMAPE": wmape(g["y"], g[m]),
                "Bias": bias(g["y"], g[m]),
                "MdAPE": mdape(g["y"], g[m]),
            })
    return pd.DataFrame(rows)


def select_champion(weekly: pd.DataFrame, model_cols: list[str]) -> str:
    """Chọn MỘT mô hình có WMAPE thấp nhất trên các cửa sổ "selection".

    Thử nghiệm cho thấy chọn riêng theo từng kiểu nhu cầu với chỉ 4 tuần là không
    ổn định (mô hình thắng ở 4 tuần đầu thường không thắng ở 8 tuần sau), nên
    chọn một mô hình chung, ưu tiên mô hình kết hợp vốn ổn định hơn.
    """
    sel = weekly[weekly["phase"] == "selection"]
    m = metrics_table(sel, model_cols)
    return str(m.loc[m["WMAPE"].idxmin(), "model"])


def confidence_label(series_wmape: float, demand_class: str) -> str:
    """Nhãn độ tin cậy hiển thị cạnh mỗi dòng dự báo trong ứng dụng."""
    if demand_class == "insufficient" or np.isnan(series_wmape):
        return "Chưa đủ dữ liệu"
    if series_wmape <= 0.30:
        return "Cao"
    if series_wmape <= 0.50:
        return "Trung bình"
    return "Thấp"
