"""Kiểm định trượt theo thời gian (walk-forward) và các chỉ số đánh giá.

Quy trình: chia 12 tuần cuối thành 12 cửa sổ. Ở mỗi cửa sổ, mô hình chỉ được
thấy dữ liệu tới trước ngày bắt đầu cửa sổ, dự báo 7 ngày, rồi so với thực tế.
  - 4 cửa sổ đầu ("selection"): dùng để CHỌN một mô hình chung (xem select_champion).
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
    """Tổng sai số tích luỹ / sai số tuyệt đối trung bình. |TS| > 4: mô hình lệch hệ thống.

    Cùng quy ước dấu với Bias và công thức trong báo cáo: e = dự báo − thực tế,
    nên TS > 0 là dự báo thừa có hệ thống, TS < 0 là dự báo thiếu có hệ thống.
    """
    e = f - y
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


def diebold_mariano(d: np.ndarray, h: int) -> tuple[float, float]:
    """Kiểm định Diebold–Mariano trên chuỗi chênh lệch tổn thất d_t theo thời gian.

    Phương sai dài hạn ước lượng theo Newey–West với h−1 độ trễ (sai số dự báo h bước
    tự tương quan tới bậc h−1), kèm hiệu chỉnh mẫu nhỏ Harvey–Leybourne–Newbold (1997);
    p-value hai phía theo phân phối t với T−1 bậc tự do.
    """
    from scipy import stats

    d = np.asarray(d, dtype=float)
    t_len = len(d)
    dc = d - d.mean()
    gamma = [float(dc[k:] @ dc[:t_len - k]) / t_len for k in range(h)]
    var = (gamma[0] + 2 * sum(gamma[1:])) / t_len
    if var <= 0:
        var = gamma[0] / t_len
    dm = d.mean() / np.sqrt(var)
    dm *= np.sqrt((t_len + 1 - 2 * h + h * (h - 1) / t_len) / t_len)
    return float(dm), float(2 * stats.t.sf(abs(dm), df=t_len - 1))


MAX_ABS_BIAS = 0.10


def select_champion(weekly: pd.DataFrame, model_cols: list[str], max_abs_bias: float = MAX_ABS_BIAS) -> str:
    """Chọn MỘT mô hình có WMAPE thấp nhất trên các cửa sổ "selection".

    Chỉ xét các mô hình có |Bias| trên giai đoạn chọn không quá `max_abs_bias`: dự báo
    lệch một chiều không bù trừ được khi cộng lên các cấp trên và làm sai lượng nhập,
    dù WMAPE ở cấp nhóm nhỏ có thể thấp (WMAPE ưu ái dự báo nghiêng về phía thấp khi
    lượng bán lệch phải). Nếu không mô hình nào đạt, chọn theo WMAPE như cũ.
    Thử nghiệm cho thấy chọn riêng theo từng kiểu nhu cầu với chỉ 4 tuần là không
    ổn định, nên chọn một mô hình chung.
    """
    sel = weekly[weekly["phase"] == "selection"]
    m = metrics_table(sel, model_cols)
    ok = m[m["Bias"].abs() <= max_abs_bias]
    m = ok if len(ok) else m
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
