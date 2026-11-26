import numpy as np
import pandas as pd
import pytest

from hasu.forecasting.data import classify_demand, impute_abnormal_days, tet_offset
from hasu.forecasting.evaluate import bias, confidence_label, select_champion, tracking_signal, wmape
from hasu.forecasting.policy import service_class, simulate_orders


def test_wmape_handles_zero_actuals():
    y = pd.Series([0, 0, 10])
    f = pd.Series([2, 0, 8])
    assert wmape(y, f) == pytest.approx(0.4)   # (2 + 0 + 2) / 10


def test_bias_sign_means_over_forecast():
    assert bias(pd.Series([10, 10]), pd.Series([12, 12])) == pytest.approx(0.2)
    assert bias(pd.Series([10, 10]), pd.Series([8, 8])) == pytest.approx(-0.2)


def test_tracking_signal_detects_systematic_under_forecast():
    y = pd.Series([10.0] * 8)
    assert tracking_signal(y, y - 2) == pytest.approx(-8.0)  # luôn dự báo thiếu 2 -> TS = -8 (cùng dấu với Bias)
    assert abs(tracking_signal(y, y + np.array([1, -1] * 4))) < 1e-9


def test_tet_offset():
    s = pd.Series(pd.to_datetime(["2026-02-17", "2026-02-10", "2027-02-01"]))
    assert tet_offset(s).tolist() == [0, -7, -5]


def _frame(values, closed=None):
    n = len(values)
    return pd.DataFrame({
        "unique_id": "A", "ds": pd.date_range("2025-10-01", periods=n),
        "y_raw": values, "is_closed": closed if closed is not None else [False] * n,
        "in_tet_window": [False] * n, "cat_l1": "X", "cat_l2": "Y",
    })


def test_closed_day_is_imputed_from_same_weekday():
    values = [5.0] * 21 + [np.nan] + [5.0] * 20
    values[14], values[28] = 9.0, 9.0   # cùng thứ với ngày 21 (cách 7 ngày)
    closed = [False] * 42
    closed[21] = True
    out = impute_abnormal_days(_frame(values, closed))
    assert out.loc[21, "is_imputed"]
    assert out.loc[21, "y"] == pytest.approx(5.0)   # trung vị của 5,9,9,5,5,5... cùng thứ


def test_classify_demand_classes():
    rng = np.random.default_rng(0)
    # Ngày nào cũng bán, lượng ổn định (CV² thấp) -> smooth
    smooth = _frame(rng.integers(20, 30, 100).astype(float))
    # Ngày nào cũng bán, lượng dao động mạnh (CV² cao) -> erratic
    erratic = _frame(rng.choice([1.0, 60.0], 100)).assign(unique_id="E")
    # Chỉ 5 ngày có bán -> chưa đủ dữ liệu
    sparse = _frame([0.0] * 95 + [3.0] * 5).assign(unique_id="B")
    p = classify_demand(pd.concat([smooth, erratic, sparse])).set_index("unique_id")
    assert p.loc["A", "demand_class"] == "smooth"
    assert p.loc["E", "demand_class"] == "erratic"
    assert p.loc["B", "demand_class"] == "insufficient"


def test_confidence_labels():
    assert confidence_label(0.2, "erratic") == "Cao"
    assert confidence_label(0.45, "lumpy") == "Trung bình"
    assert confidence_label(0.9, "lumpy") == "Thấp"
    assert confidence_label(np.nan, "insufficient") == "Chưa đủ dữ liệu"


def test_service_class_priorities():
    assert service_class("Sữa, sản phẩm từ sữa", "Ngôi sao") == "Dễ hư hỏng"
    assert service_class("Đồ uống", "Ngôi sao") == "Ngôi sao"
    assert service_class("Đồ uống", "Lời mỏng") == "Bảo quản lâu"


def test_simulation_counts_shortage_and_excess():
    w = pd.DataFrame({"unique_id": ["A", "A"], "y": [10.0, 4.0]})
    sim = simulate_orders(w, {"p": pd.Series([6.0, 6.0])}, pd.Series({"A": 1000.0})).iloc[0]
    assert sim.units_short == 4 and sim.units_excess == 2
    assert sim.fill_rate == pytest.approx(1 - 4 / 14)
    assert sim.excess_value == 2000


def test_drift_status_triggers_retrain():
    from hasu.forecasting.monitor import drift_status

    ok = pd.DataFrame({"wmape": [0.5, 0.55], "actual_total": [100, 110], "forecast_total": [105, 100]})
    assert not drift_status(ok, reference_wmape=0.55)["retrain"]
    bad = ok.assign(wmape=[0.5, 0.9])
    assert drift_status(bad, reference_wmape=0.55)["retrain"]
    # luôn dự báo thiếu -> lệch hệ thống
    biased = pd.DataFrame({"wmape": [0.3] * 6, "actual_total": [100] * 6, "forecast_total": [80] * 6})
    assert drift_status(biased, reference_wmape=0.55)["retrain"]
    assert not drift_status(pd.DataFrame(), reference_wmape=0.55)["retrain"]


def test_imputation_uses_only_past_weeks():
    # Ngày 21 đóng cửa; các tuần trước bán 5, các tuần sau bán 100.
    # Nội suy chỉ được nhìn quá khứ, nên phải ra 5 chứ không bị kéo lên bởi tương lai.
    values = [5.0] * 21 + [np.nan] + [100.0] * 20
    closed = [False] * 42
    closed[21] = True
    out = impute_abnormal_days(_frame(values, closed))
    assert out.loc[21, "y"] == pytest.approx(5.0)


def test_service_level_ignores_weeks_without_demand():
    # Tuần 2 không ai mua: không được tính là "đạt dịch vụ".
    w = pd.DataFrame({"unique_id": ["A", "A"], "y": [10.0, 0.0]})
    sim = simulate_orders(w, {"p": pd.Series([5.0, 5.0])}, pd.Series({"A": 1.0})).iloc[0]
    assert sim.service_level == 0.0


def test_inventory_simulation_carries_over_long_life_goods():
    from hasu.forecasting.policy import simulate_inventory

    w = pd.DataFrame({"unique_id": ["A", "A", "M", "M"], "cutoff": [1, 2, 1, 2], "y": [4.0, 10.0, 4.0, 10.0]})
    target = pd.Series([10.0, 10.0, 10.0, 10.0])
    cost, price = pd.Series({"A": 100.0, "M": 100.0}), pd.Series({"A": 150.0, "M": 150.0})
    perishable = pd.Series({"A": False, "M": True})
    a = simulate_inventory(w[w.unique_id == "A"], {"p": target[:2]}, perishable, cost, price, holding_rate=0).iloc[0]
    # Hàng để lâu: dư 6 sau tuần 1 được bán tiếp, tuần 2 chỉ đặt thêm 4 -> không thiếu, không hỏng
    assert a.units_ordered == 14 and a.units_short == 0 and a.excess_value == 0
    m = simulate_inventory(w[w.unique_id == "M"], {"p": target[2:]}, perishable, cost, price,
                           holding_rate=0).iloc[0]
    # Hàng dễ hư: dư 6 bị bỏ (600 đ), tuần 2 đặt lại 10
    assert m.units_ordered == 20 and m.excess_value == 600 and m.lost_profit == 0


def test_drift_flags_every_week_not_only_the_last():
    from hasu.forecasting.monitor import drift_status

    h = pd.DataFrame({"week_start": pd.date_range("2026-05-05", periods=4, freq="7D"),
                      "wmape": [0.5, 0.95, 0.5, 0.5], "actual_total": [100] * 4, "forecast_total": [100] * 4})
    st = drift_status(h, reference_wmape=0.55)
    assert not st["retrain"]                         # tuần gần nhất trong ngưỡng
    assert st["flagged_weeks"] == ["12/05/2026"]     # nhưng tuần 2 vẫn được ghi nhận đã cảnh báo


def test_sku_allocation_matches_group_order():
    from hasu.forecasting.run import allocate_skus

    a = pd.DataFrame({"cat_l3": ["N"] * 3, "unique_id": ["N"] * 3, "sku": ["a", "b", "c"],
                      "qty": [50.0, 30.0, 20.0], "share": [0.5, 0.3, 0.2],
                      "order_qty": [7.0] * 3, "forecast_week": [6.0] * 3})
    out = allocate_skus(a)
    assert out["sku_order_qty"].sum() == 7
    assert out["share"].sum() == pytest.approx(1.0)


def test_select_champion_skips_heavily_biased_model():
    # Mô hình "thap" có WMAPE thấp hơn nhưng luôn dự báo thiếu 30% -> không được chọn
    y = np.array([10.0, 2.0, 0.0, 30.0] * 3)
    weekly = pd.DataFrame({
        "phase": "selection", "y": y,
        "thap": y * 0.7,
        "can_bang": y + np.array([6.0, -6.0, 3.0, -3.0] * 3),  # WMAPE 43% > 30% nhưng không lệch
    })
    assert select_champion(weekly, ["thap", "can_bang"], max_abs_bias=0.10) == "can_bang"
    assert select_champion(weekly, ["thap", "can_bang"], max_abs_bias=1.0) == "thap"
