"""Từ dự báo tới quyết định nhập hàng.

1. Khoảng dự báo theo phân vị (quantile): dự báo điểm chỉ là "mức trung tâm".
   Để quyết định nhập bao nhiêu, cần biết "nhập bao nhiêu thì đủ hàng trong τ%
   số tuần". Dùng phương pháp conformal theo tỷ lệ: từ các tuần đã kiểm định,
   tính tỷ lệ thực tế / dự báo; phân vị τ của tỷ lệ này nhân với dự báo điểm.
2. Mức phân vị τ chọn theo đặc điểm nhóm hàng (kết nối với phân tích biên lợi
   nhuận): chi phí hết hàng và chi phí tồn dư khác nhau giữa các nhóm.
3. Mô phỏng nhập hàng trên các tuần holdout để so sánh các cách nhập.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Nhóm hàng cấp 1 dễ hư hỏng / hạn dùng ngắn
PERISHABLE_L1 = {
    "Sữa, sản phẩm từ sữa", "Thực phẩm đông mát", "Rau, củ, trái cây", "Thịt, trứng, thủy hải sản tươi",
}

SERVICE_POLICY = {
    "Ngôi sao": (0.80, "Biên cao, bán chạy: chi phí hết hàng cao hơn chi phí tồn dư"),
    "Dễ hư hỏng": (0.55, "Hạn dùng ngắn: hàng dư gây lỗ trực tiếp, cần cân bằng"),
    "Bảo quản lâu": (0.70, "Biên thấp, để được lâu: rủi ro tồn dư chủ yếu là chi phí vốn"),
}


def service_class(cat_l1: str, quadrant: str | None) -> str:
    if cat_l1 in PERISHABLE_L1:
        return "Dễ hư hỏng"
    if quadrant == "Ngôi sao":
        return "Ngôi sao"
    return "Bảo quản lâu"


def ratio_quantiles(weekly: pd.DataFrame, model: str, groups: pd.Series,
                    taus: list[float]) -> pd.DataFrame:
    """Phân vị của tỷ lệ thực tế/dự báo theo từng nhóm (vd kiểu nhu cầu).

    weekly: bảng tuần (y, model); groups: ánh xạ unique_id -> nhóm.
    """
    w = weekly[weekly[model] > 0.5].copy()
    w["ratio"] = w["y"] / w[model]
    w["grp"] = w["unique_id"].map(groups)
    rows = []
    for g, d in w.groupby("grp"):
        rows.append({"grp": g, **{f"q{int(t * 100)}": float(np.quantile(d["ratio"], t)) for t in taus},
                     "n_weeks": len(d)})
    return pd.DataFrame(rows)


def simulate_orders(weekly: pd.DataFrame, policies: dict[str, pd.Series], unit_cost: pd.Series) -> pd.DataFrame:
    """Mô phỏng: mỗi tuần nhập đúng số lượng của chính sách, so với nhu cầu thực tế.

    Giả định đơn giản (ghi rõ trong báo cáo): hàng không mang sang tuần sau, nhập
    đầu tuần và giao ngay. Đây là mô phỏng trên dữ liệu quá khứ, không phải kết
    quả áp dụng thật.
    """
    rows = []
    cost = weekly["unique_id"].map(unit_cost).fillna(unit_cost.median())
    for name, order in policies.items():
        short = np.maximum(weekly["y"] - order, 0)
        excess = np.maximum(order - weekly["y"], 0)
        rows.append({
            "policy": name,
            "units_ordered": float(order.sum()),
            "units_short": float(short.sum()),
            "units_excess": float(excess.sum()),
            "service_level": float((short <= 0.5).mean()),   # % tuần x nhóm không thiếu hàng
            "fill_rate": float(1 - short.sum() / weekly["y"].sum()),  # % nhu cầu được đáp ứng
            "excess_value": float((excess * cost).sum()),
        })
    return pd.DataFrame(rows)
