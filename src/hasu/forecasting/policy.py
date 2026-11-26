"""Từ dự báo tới quyết định nhập hàng.

1. Khoảng dự báo theo phân vị (quantile): dự báo điểm chỉ là "mức trung tâm".
   Để quyết định nhập bao nhiêu, cần biết "nhập bao nhiêu thì đủ hàng trong τ%
   số tuần". Dùng phương pháp conformal theo tỷ lệ: từ các tuần đã kiểm định,
   tính tỷ lệ thực tế / dự báo; phân vị τ của tỷ lệ này nhân với dự báo điểm.
2. Mức phân vị τ chọn theo đặc điểm nhóm hàng (kết nối với phân tích biên lợi
   nhuận): chi phí hết hàng và chi phí tồn dư khác nhau giữa các nhóm.
3. Mô phỏng nhập hàng trên các tuần holdout để so sánh các cách nhập, theo hai
   giả định: (a) một kỳ, hàng dư không mang sang tuần sau; (b) có chuyển tồn:
   hàng bảo quản lâu được bán tiếp tuần sau, hàng dễ hư hỏng còn dư thì bỏ đi.
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
    """Mô phỏng một kỳ: mỗi tuần nhập đúng số lượng của chính sách (làm tròn lên như
    trong ứng dụng), hàng dư không mang sang tuần sau.

    Service level chỉ tính trên các tuần có nhu cầu (y > 0): tuần không ai mua thì
    không thể "thiếu hàng", nếu tính vào sẽ làm chỉ số đẹp giả.
    """
    rows = []
    cost = weekly["unique_id"].map(unit_cost).fillna(unit_cost.median())
    has_demand = weekly["y"] > 0
    for name, order in policies.items():
        order = np.ceil(np.asarray(order, dtype=float))
        short = np.maximum(weekly["y"] - order, 0)
        excess = np.maximum(order - weekly["y"], 0)
        rows.append({
            "mode": "Một kỳ (không chuyển tồn)",
            "policy": name,
            "units_ordered": float(order.sum()),
            "units_short": float(short.sum()),
            "units_excess": float(excess.sum()),
            "service_level": float((short[has_demand] <= 0.5).mean()),
            "fill_rate": float(1 - short.sum() / weekly["y"].sum()),
            "excess_value": float((excess * cost).sum()),
        })
    return pd.DataFrame(rows)


HOLDING_RATE_WEEK = 0.01 * 12 / 52   # chi phí vốn 1%/tháng, quy ra tuần


def simulate_inventory(weekly: pd.DataFrame, policies: dict[str, pd.Series], perishable: pd.Series,
                       unit_cost: pd.Series, unit_price: pd.Series,
                       holding_rate: float = HOLDING_RATE_WEEK) -> pd.DataFrame:
    """Mô phỏng nhiều kỳ có chuyển tồn (chính sách "đặt lên mức mục tiêu").

    Mỗi tuần, với mỗi nhóm hàng: mức mục tiêu S = số lượng của chính sách;
    lượng đặt = max(0, ⌈S⌉ − tồn đầu tuần); bán = min(nhu cầu, tồn + đặt).
    Hàng bảo quản lâu còn dư được chuyển sang tuần sau, chịu chi phí vốn
    holding_rate mỗi tuần; hàng dễ hư hỏng còn dư bị bỏ (mất trọn giá vốn).
    Thiếu hàng được quy ra lợi nhuận gộp bị mất = số thiếu × (giá bán − giá vốn).
    Tồn đầu kỳ bằng 0 cho mọi chính sách.
    """
    w = weekly.sort_values(["unique_id", "cutoff"]).reset_index()
    cost = w["unique_id"].map(unit_cost).fillna(unit_cost.median()).to_numpy()
    price = w["unique_id"].map(unit_price).fillna(unit_price.median()).to_numpy()
    margin = np.maximum(price - cost, 0)
    spoil = w["unique_id"].map(perishable).fillna(False).to_numpy(dtype=bool)
    y = w["y"].to_numpy(dtype=float)
    uid = w["unique_id"].to_numpy()
    rows = []
    for name, target in policies.items():
        tgt = pd.Series(np.asarray(target, dtype=float), index=weekly.index)
        s_target = np.ceil(tgt.loc[w["index"]].to_numpy())
        on_hand = 0.0
        ordered = short = waste_u = 0.0
        lost_profit = waste_v = hold_v = 0.0
        demand_weeks = served_weeks = 0
        for i in range(len(w)):
            if i == 0 or uid[i] != uid[i - 1]:
                on_hand = 0.0
            q = max(0.0, s_target[i] - on_hand)
            avail = on_hand + q
            sold = min(y[i], avail)
            miss = y[i] - sold
            left = avail - sold
            ordered += q
            short += miss
            lost_profit += miss * margin[i]
            if y[i] > 0:
                demand_weeks += 1
                served_weeks += miss <= 0.5
            if spoil[i]:
                waste_u += left
                waste_v += left * cost[i]
                on_hand = 0.0
            else:
                hold_v += left * cost[i] * holding_rate
                on_hand = left
        rows.append({
            "mode": "Nhiều kỳ (có chuyển tồn)",
            "policy": name,
            "units_ordered": ordered,
            "units_short": short,
            "units_excess": waste_u,
            "service_level": served_weeks / demand_weeks if demand_weeks else np.nan,
            "fill_rate": 1 - short / y.sum(),
            "excess_value": waste_v,
            "lost_profit": lost_profit,
            "holding_cost": hold_v,
            "total_cost": lost_profit + waste_v + hold_v,
        })
    return pd.DataFrame(rows)
