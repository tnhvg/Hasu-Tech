"""Chuẩn bị chuỗi thời gian cho mô hình.

Kiến trúc hai lớp (theo kế hoạch dự án):
  - Lớp ngày thường: mô hình học trên chuỗi đã thay các ngày bất thường
    (ngày đóng cửa, vùng ±14 ngày quanh Tết) bằng giá trị nội suy, để đường nền
    không bị kéo lệch bởi các đột biến ngắn hạn.
  - Lớp ngày lễ: khi kỳ dự báo rơi vào vùng lễ, nhân thêm hệ số mùa vụ đã đo
    (xem holiday_factors()).
"""

from __future__ import annotations

from datetime import date

import duckdb
import numpy as np
import pandas as pd

TET_DATES = [date(2026, 2, 17), date(2027, 2, 6)]  # mùng 1 Tết Bính Ngọ, Đinh Mùi
TET_WINDOW = (-14, 13)

# Ngưỡng phân loại nhu cầu Syntetos-Boylan (ADI: khoảng cách trung bình giữa
# hai ngày có bán; CV²: bình phương hệ số biến thiên của lượng bán khi có bán).
ADI_CUT, CV2_CUT = 1.32, 0.49
MIN_SALE_DAYS = 20  # ít hơn: không đủ dữ liệu để dự báo


def load_daily(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Chuỗi ngày theo lịch (kể cả ngày đóng cửa) cho mỗi nhóm hàng cấp 3.

    Cột: unique_id, ds, y_raw (NaN nếu đóng cửa), discount_depth, cat_l1, cat_l2,
    is_closed, in_tet_window.
    """
    df = con.execute("""
        SELECT cat_l3 AS unique_id, date AS ds, quantity AS y_raw, discount_depth, cat_l1, cat_l2
        FROM fct_retail_daily_category
    """).df()
    df["ds"] = pd.to_datetime(df["ds"])
    cal = con.execute("SELECT date AS ds, NOT is_open AS is_closed FROM dim_date").df()
    cal["ds"] = pd.to_datetime(cal["ds"])

    meta = df.groupby("unique_id")[["cat_l1", "cat_l2"]].first()
    grid = pd.MultiIndex.from_product([meta.index, cal["ds"]], names=["unique_id", "ds"]).to_frame(index=False)
    out = (grid.merge(cal, on="ds")
               .merge(df.drop(columns=["cat_l1", "cat_l2"]), on=["unique_id", "ds"], how="left")
               .merge(meta, left_on="unique_id", right_index=True))
    out["in_tet_window"] = tet_offset(out["ds"]).between(*TET_WINDOW)
    return out.sort_values(["unique_id", "ds"]).reset_index(drop=True)


def tet_offset(ds: pd.Series) -> pd.Series:
    """Số ngày tính từ mùng 1 Tết gần nhất (âm = trước Tết)."""
    ds = pd.to_datetime(ds)
    tets = pd.to_datetime(pd.Series(TET_DATES))
    diffs = np.stack([(ds - t).dt.days.to_numpy() for t in tets])
    idx = np.abs(diffs).argmin(axis=0)
    return pd.Series(diffs[idx, np.arange(len(ds))], index=ds.index)


def impute_abnormal_days(df: pd.DataFrame, max_weeks: int = 6) -> pd.DataFrame:
    """Lớp ngày thường: thay ngày đóng cửa và vùng Tết bằng trung vị của cùng thứ
    trong các tuần lân cận (tối đa ±max_weeks tuần) không bị thay thế.

    Thêm cột y (chuỗi dùng để huấn luyện) và is_imputed.
    """
    out = []
    for uid, g in df.groupby("unique_id", sort=False):
        g = g.copy()
        mask = (g["is_closed"] | g["in_tet_window"]).to_numpy()
        y = g["y_raw"].to_numpy(dtype=float)
        clean = np.where(mask, np.nan, y)
        filled = clean.copy()
        for i in np.flatnonzero(mask):
            neigh = [clean[i + 7 * k] for k in range(-max_weeks, max_weeks + 1)
                     if k != 0 and 0 <= i + 7 * k < len(clean) and not np.isnan(clean[i + 7 * k])]
            filled[i] = np.median(neigh) if neigh else 0.0
        g["y"] = filled
        g["is_imputed"] = mask
        out.append(g)
    return pd.concat(out, ignore_index=True)


def classify_demand(df: pd.DataFrame) -> pd.DataFrame:
    """Phân loại kiểu nhu cầu mỗi nhóm hàng theo Syntetos-Boylan, trên các ngày mở cửa."""
    open_days = df[~df["is_closed"]]

    def profile(s: pd.Series) -> pd.Series:
        nz = s[s > 0]
        n_nz = len(nz)
        adi = len(s) / n_nz if n_nz else np.inf
        cv2 = (nz.std() / nz.mean()) ** 2 if n_nz > 1 else np.nan
        return pd.Series({"sale_days": n_nz, "open_days": len(s), "adi": adi, "cv2": cv2,
                          "total_qty": s.sum(), "mean_daily_qty": s.mean()})

    p = open_days.groupby("unique_id")["y_raw"].apply(profile).unstack()
    p["demand_class"] = np.select(
        [p["sale_days"] < MIN_SALE_DAYS,
         (p["adi"] < ADI_CUT) & (p["cv2"] < CV2_CUT),
         p["adi"] < ADI_CUT,
         p["cv2"] < CV2_CUT],
        ["insufficient", "smooth", "erratic", "intermittent"],
        default="lumpy",
    )
    meta = df.groupby("unique_id")[["cat_l1", "cat_l2"]].first()
    return p.join(meta).reset_index()


def holiday_factors(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Lớp ngày lễ: hệ số SỐ LƯỢNG theo nhóm hàng cấp 1 cho vùng trước/sau Tết."""
    return con.execute("""
        SELECT cat_l1, tet_window, qty_factor
        FROM mart_tet_effect WHERE cat_l1 <> 'Toàn cửa hàng'
    """).df()
