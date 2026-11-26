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
    """Đánh giá MỌI tuần đã đối chiếu, theo đúng thứ tự thời gian.

    Mỗi tuần, khi có thực tế, hệ thống kiểm tra: sai số tuần đó có vượt
    DRIFT_FACTOR lần sai số kiểm định không, và tracking signal tích luỹ tới tuần
    đó có vượt ±TS_LIMIT không. Tuần nào vượt thì được đánh dấu "kích hoạt cảnh
    báo" (lúc đó hệ thống huấn luyện lại). Trạng thái hiện tại dựa trên tuần mới
    nhất, kèm danh sách các tuần đã từng kích hoạt để người dùng không bỏ sót.
    """
    if history.empty:
        return {"status": "Chưa có tuần nào đủ dữ liệu để đối chiếu", "retrain": False,
                "flagged_weeks": [], "tracking_signal": 0.0}
    h = history.reset_index(drop=True)
    e = h["forecast_total"] - h["actual_total"]          # cùng dấu với Bias: > 0 là dự báo thừa
    mad = e.abs().expanding().mean()
    ts = (e.cumsum() / mad.where(mad > 0)).fillna(0.0)
    limit = reference_wmape * DRIFT_FACTOR
    over = h["wmape"] > limit
    biased = ts.abs() > TS_LIMIT
    labels = (pd.to_datetime(h["week_start"]).dt.strftime("%d/%m/%Y") if "week_start" in h.columns
              else h.index.astype(str))
    flagged = [labels.iloc[i] if hasattr(labels, "iloc") else labels[i]
               for i in range(len(h)) if over.iloc[i] or biased.iloc[i]]
    n_flag = len(flagged)
    past_note = (f" Trong {len(h)} tuần đã đối chiếu, {n_flag} tuần từng kích hoạt cảnh báo "
                 "(tại thời điểm đó hệ thống huấn luyện lại).") if n_flag else ""
    last_ts = float(ts.iloc[-1])
    if over.iloc[-1]:
        return {"status": f"Cảnh báo: sai số tuần gần nhất {h['wmape'].iloc[-1]:.0%} vượt ngưỡng "
                          f"{limit:.0%}. Nên huấn luyện lại." + past_note,
                "retrain": True, "tracking_signal": last_ts, "flagged_weeks": flagged}
    if biased.iloc[-1]:
        side = "thừa" if last_ts > 0 else "thiếu"
        return {"status": f"Cảnh báo: mô hình đang dự báo {side} có hệ thống (tracking signal {last_ts:.1f})."
                          + past_note,
                "retrain": True, "tracking_signal": last_ts, "flagged_weeks": flagged}
    return {"status": "Tuần gần nhất trong ngưỡng: giữ mô hình, huấn luyện lại theo chu kỳ." + past_note,
            "retrain": False, "tracking_signal": last_ts, "flagged_weeks": flagged}
