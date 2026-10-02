"""Hàm dùng chung cho các màn hình của ứng dụng."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hasu import viz  # noqa: E402
from hasu.config import DB_PATH  # noqa: E402

DEMO_DIR = ROOT / "app" / "demo_data"

CLASS_LABELS = {
    "erratic": "Bán hằng ngày, dao động",
    "lumpy": "Gián đoạn, dao động",
    "intermittent": "Gián đoạn, đều",
    "smooth": "Đều đặn",
    "insufficient": "Chưa đủ dữ liệu",
}
CONF_ICON = {"Cao": "🟢 Cao", "Trung bình": "🟡 Trung bình", "Thấp": "🟠 Thấp", "Chưa đủ dữ liệu": "⚪ Chưa đủ dữ liệu"}


# ---------------------------------------------------------------------------
# Nguồn dữ liệu: dữ liệu người dùng vừa nạp > CSDL cục bộ > bộ demo
# ---------------------------------------------------------------------------

@st.cache_resource
def _demo_connection() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    for f in sorted(DEMO_DIR.glob("*.parquet")):
        con.execute(f"CREATE TABLE {f.stem} AS SELECT * FROM read_parquet('{f.as_posix()}')")
    return con


def source() -> tuple[str, str | None]:
    """(nhãn nguồn dữ liệu, đường dẫn file DuckDB hoặc None nếu là demo)."""
    if st.session_state.get("db_path"):
        return "Dữ liệu bạn vừa nạp", st.session_state["db_path"]
    if DB_PATH.exists() and not os.environ.get("HASU_FORCE_DEMO"):
        return "Cơ sở dữ liệu cục bộ", str(DB_PATH)
    return "Dữ liệu demo (BHS Đại Phúc, đã ẩn danh)", None


def q(sql: str, params: list | None = None) -> pd.DataFrame:
    label, path = source()
    return _query(path, st.session_state.get("data_version", 0), sql, tuple(params or ()))


@st.cache_data(show_spinner=False)
def _query(path: str | None, _version: int, sql: str, params: tuple) -> pd.DataFrame:
    if path is None:
        cur = _demo_connection().cursor()
        return cur.execute(sql, list(params)).df()
    with duckdb.connect(path, read_only=True) as con:
        return con.execute(sql, list(params)).df()


def has_table(name: str) -> bool:
    return bool(q("SELECT count(*) AS n FROM information_schema.tables WHERE table_name = ?", [name])["n"].iloc[0])


# ---------------------------------------------------------------------------
# Định dạng số kiểu Việt Nam
# ---------------------------------------------------------------------------

def num(x: float, digits: int = 0) -> str:
    if pd.isna(x):
        return "–"
    return f"{x:,.{digits}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def vnd(x: float) -> str:
    if pd.isna(x):
        return "–"
    if abs(x) >= 1e9:
        return num(x / 1e9, 2) + " tỷ"
    if abs(x) >= 1e6:
        return num(x / 1e6, 1) + " tr"
    return num(x) + " đ"


def pct(x: float, digits: int = 1) -> str:
    return "–" if pd.isna(x) else num(x * 100, digits) + "%"


# ---------------------------------------------------------------------------
# Giao diện
# ---------------------------------------------------------------------------

def header(title: str, caption: str | None = None) -> None:
    st.title(title)
    label, _ = source()
    info = q("SELECT min(date) AS d0, max(date) AS d1 FROM dim_date") if has_table("dim_date") else None
    period = (f" · {pd.Timestamp(info.d0[0]):%d/%m/%Y} – {pd.Timestamp(info.d1[0]):%d/%m/%Y}"
              if info is not None and len(info) else "")
    st.caption(f"Nguồn: **{label}**{period}" + (f" · {caption}" if caption else ""))


def layout(fig, height: int = 360, **kw):
    fig.update_layout(**viz.plotly_layout(height=height, **kw))
    return fig


def show(fig, height: int = 360, **kw) -> None:
    st.plotly_chart(layout(fig, height, **kw), width="stretch", theme="streamlit")


def note(text: str) -> None:
    st.caption("ℹ️ " + text)


WEEKDAY_VI = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
DATE_AXIS = dict(tickformat="%d/%m", hoverformat="%d/%m/%Y")


def month_label(ym: str) -> str:
    """'2026-02' -> '02/26' (trục danh mục, tránh Plotly tự đổi sang tên tháng tiếng Anh)."""
    return f"{ym[5:7]}/{ym[2:4]}"


def day_label(d) -> str:
    d = pd.Timestamp(d)
    return f"{WEEKDAY_VI[d.weekday()]} {d:%d/%m}"


def weekly_blocks(dates: pd.Series, values: pd.Series, end: pd.Timestamp, future: bool = False) -> pd.Series:
    """Cộng theo khối 7 ngày đầy đủ, neo vào ngày cuối của dữ liệu (không có tuần thiếu ngày ở mép).

    future=False: các khối kết thúc ở `end` (lùi về quá khứ); True: các khối bắt đầu từ `end` + 1.
    Chỉ số của kết quả là ngày đầu mỗi khối.
    """
    dates = pd.to_datetime(dates)
    if future:
        k = (dates - end - pd.Timedelta(days=1)).dt.days // 7
        s = pd.Series(values.to_numpy(), index=k).groupby(level=0).agg(["sum", "size"])
        s = s[s["size"] == 7]["sum"]
        s.index = [end + pd.Timedelta(days=1 + 7 * i) for i in s.index]
    else:
        k = (end - dates).dt.days // 7
        s = pd.Series(values.to_numpy(), index=k).groupby(level=0).sum().sort_index(ascending=False)
        s.index = [end - pd.Timedelta(days=7 * i + 6) for i in s.index]
    return s
