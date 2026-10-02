"""Vòng lặp cải thiện: lưu snapshot dự báo, đối chiếu với thực tế khi có dữ liệu mới,
phát hiện mô hình suy giảm chất lượng (drift).

Luồng (Bước 10 của kế hoạch):
  dự báo tuần tới -> LƯU SNAPSHOT -> nạp dữ liệu thực tế -> ĐỐI CHIẾU -> nếu sai số
  vượt ngưỡng thì cảnh báo và huấn luyện lại -> dự báo chu kỳ tiếp theo.
"""

from __future__ import annotations

from datetime import datetime

import duckdb
import pandas as pd

SNAPSHOT_DDL = """
CREATE TABLE IF NOT EXISTS fc_snapshots (
    run_id VARCHAR, kind VARCHAR, created_at TIMESTAMP, data_until TIMESTAMP,
    week_start TIMESTAMP, model VARCHAR, unique_id VARCHAR,
    forecast_week DOUBLE, order_qty DOUBLE
)
"""

DRIFT_FACTOR = 1.3   # sai số tuần mới > 1,3 lần sai số kiểm định -> cảnh báo
TS_LIMIT = 4         # |tracking signal| > 4 -> lệch hệ thống


def save_snapshot(con: duckdb.DuckDBPyConnection, fc_daily: pd.DataFrame, plan: pd.DataFrame,
                  model: str, data_until: pd.Timestamp, kind: str) -> str:
    con.execute(SNAPSHOT_DDL)
    run_id = f"run-{datetime.now():%Y%m%d-%H%M%S}"
    # Mỗi lần dữ liệu tới cùng một ngày chỉ giữ một snapshot "Dự báo thật" mới nhất
    con.execute("DELETE FROM fc_snapshots WHERE kind = ? AND data_until = ?", [kind, data_until])
    rows = plan[["unique_id", "forecast_week", "order_qty"]].assign(
        run_id=run_id, kind=kind, created_at=datetime.now(), data_until=data_until,
        week_start=data_until + pd.Timedelta(days=1), model=model)
    con.register("tmp_df", rows)
    con.execute("INSERT INTO fc_snapshots BY NAME SELECT * FROM tmp_df")
    con.unregister("tmp_df")
    return run_id


# Đối chiếu mọi snapshot đã có đủ 7 ngày thực tế (dùng chung cho ứng dụng).
SNAPSHOT_EVAL_SQL = """
    WITH actual AS (
        SELECT s.run_id, s.unique_id, sum(f.quantity) AS actual_week, count(DISTINCT f.date) AS open_days
        FROM fc_snapshots s
        JOIN fct_retail_daily_category f
          ON f.cat_l3 = s.unique_id
         AND f.date >= CAST(s.week_start AS DATE)
         AND f.date < CAST(s.week_start AS DATE) + INTERVAL 7 DAY
        GROUP BY ALL
    ),
    complete AS (
        SELECT run_id FROM fc_snapshots s
        WHERE CAST(s.week_start AS DATE) + INTERVAL 6 DAY <= (SELECT max(date) FROM dim_date)
        GROUP BY 1
    )
    SELECT s.run_id, any_value(s.kind) AS kind, any_value(s.week_start) AS week_start,
           any_value(s.model) AS model,
           sum(abs(a.actual_week - s.forecast_week)) / nullif(sum(a.actual_week), 0) AS wmape,
           sum(s.forecast_week - a.actual_week) / nullif(sum(a.actual_week), 0) AS bias,
           sum(a.actual_week) AS actual_total, sum(s.forecast_week) AS forecast_total,
           count(*) AS n_series
    FROM fc_snapshots s
    JOIN actual a USING (run_id, unique_id)
    WHERE s.run_id IN (SELECT run_id FROM complete)
    GROUP BY s.run_id
    ORDER BY week_start
"""


def evaluate_snapshots(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Đối chiếu mọi snapshot đã có đủ 7 ngày thực tế."""
    con.execute(SNAPSHOT_DDL)
    return con.execute(SNAPSHOT_EVAL_SQL).df()


def drift_status(history: pd.DataFrame, reference_wmape: float) -> dict:
    """Quyết định giữ hay huấn luyện lại mô hình dựa trên tuần đối chiếu gần nhất."""
    if history.empty:
        return {"status": "Chưa có tuần nào đủ dữ liệu để đối chiếu", "retrain": False}
    last = history.iloc[-1]
    e = history["actual_total"] - history["forecast_total"]
    ts = e.sum() / e.abs().mean() if e.abs().mean() else 0.0
    if last["wmape"] > reference_wmape * DRIFT_FACTOR:
        return {"status": f"Cảnh báo: sai số tuần gần nhất {last['wmape']:.0%} vượt ngưỡng "
                          f"{reference_wmape * DRIFT_FACTOR:.0%}. Nên huấn luyện lại.",
                "retrain": True, "tracking_signal": ts}
    if abs(ts) > 4:
        return {"status": f"Cảnh báo: mô hình lệch hệ thống (tracking signal {ts:.1f}).",
                "retrain": True, "tracking_signal": ts}
    return {"status": "Trong ngưỡng: giữ mô hình, huấn luyện lại theo chu kỳ.", "retrain": False,
            "tracking_signal": ts}
