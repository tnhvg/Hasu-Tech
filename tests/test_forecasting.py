import numpy as np
import pandas as pd
import pytest

from hasu.forecasting.data import classify_demand, impute_abnormal_days, tet_offset
from hasu.forecasting.evaluate import bias, confidence_label, tracking_signal, wmape
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
    assert tracking_signal(y, y - 2) == pytest.approx(8.0)  # luôn thiếu 2 -> 8 lần MAD
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
