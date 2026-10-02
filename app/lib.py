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

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,500,0,0');
.block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1320px;}
.ms {font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal; line-height: 1;
     letter-spacing: normal; text-transform: none; display: inline-block; white-space: nowrap;
     -webkit-font-feature-settings: 'liga'; font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased;}

/* Đầu trang */
.hx-head {display: flex; flex-direction: column; align-items: flex-start; gap: 14px;
          margin-bottom: 1.4rem; padding-bottom: 1.1rem; border-bottom: 1px solid #e3e8ef;}
.hx-over {font-size: .74rem; font-weight: 600; letter-spacing: .09em; text-transform: uppercase; color: #2a78d6;
          margin-bottom: .35rem;}
.hx-title {font-size: 2rem; font-weight: 700; line-height: 1.2; color: #101828; margin: 0;}
.hx-sub {color: #475467; margin-top: .4rem; font-size: .95rem; max-width: 760px;}
.hx-chips {display: flex; gap: 8px; flex-wrap: wrap;}
.hx-chip {display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px;
          background: #ffffff; border: 1px solid #e3e8ef; color: #344054; font-size: .82rem; font-weight: 500;}
.hx-chip .ms {font-size: 17px; color: #2a78d6;}
.hx-chip.demo {background: #eef5fd; border-color: #cfe1f8; color: #1c5cab;}

/* Thẻ chỉ số */
.hx-kpis {display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin: .2rem 0 1.4rem;}
.hx-kpi {background: #ffffff; border: 1px solid #e3e8ef; border-radius: 14px; padding: 16px 18px;
         box-shadow: 0 1px 2px rgba(16,24,40,.04);}
.hx-kpi-top {display: flex; align-items: center; gap: 10px; color: #475467; font-size: .85rem; font-weight: 500;}
.hx-kpi-icon {width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center;
              background: #eef5fd; color: #2a78d6;}
.hx-kpi-icon .ms {font-size: 20px;}
.hx-kpi-icon.green {background: #e8f6ef; color: #12805c;}
.hx-kpi-icon.orange {background: #fdf0e9; color: #c4531f;}
.hx-kpi-icon.violet {background: #efedfb; color: #4a3aa7;}
.hx-kpi-value {font-size: 1.75rem; font-weight: 700; color: #101828; margin-top: 10px; line-height: 1.15;}
.hx-kpi-note {font-size: .8rem; color: #667085; margin-top: 6px;}
.hx-up {color: #12805c; font-weight: 600;} .hx-down {color: #c4321f; font-weight: 600;}

/* Cảnh báo */
.hx-alert {display: flex; gap: 12px; align-items: flex-start; background: #ffffff; border: 1px solid #e3e8ef;
           border-left: 4px solid #2a78d6; border-radius: 12px; padding: 13px 16px; margin-bottom: 10px;}
.hx-alert .ms {font-size: 22px; color: #2a78d6; margin-top: 1px;}
.hx-alert b {color: #101828;}
.hx-alert-text {color: #344054; font-size: .92rem; line-height: 1.5;}
.hx-alert.critical {border-left-color: #d03b3b;} .hx-alert.critical .ms {color: #d03b3b;}
.hx-alert.warning {border-left-color: #e19a0c;} .hx-alert.warning .ms {color: #c98500;}
.hx-alert.good {border-left-color: #12a06a;} .hx-alert.good .ms {color: #12805c;}

/* Tiêu đề mục */
.hx-section {display: flex; align-items: center; gap: 8px; font-size: 1.12rem; font-weight: 600;
             color: #101828; margin: 1.3rem 0 .7rem;}
.hx-section .ms {font-size: 21px; color: #2a78d6;}

/* Thẻ chứa biểu đồ / bảng */
div[class*="st-key-card"] {background: #ffffff; border: 1px solid #e3e8ef; border-radius: 14px;
                           padding: 14px 16px 8px; box-shadow: 0 1px 2px rgba(16,24,40,.04);}

div[class*="st-key-card"] h2 {font-size: 1.25rem; margin-top: .6rem;}
div[class*="st-key-card"] h3 {font-size: 1.05rem;}

/* Các thành phần có sẵn của Streamlit */
[data-testid="stMetric"] {background: #ffffff; border: 1px solid #e3e8ef; border-radius: 14px; padding: 14px 16px;
                          box-shadow: 0 1px 2px rgba(16,24,40,.04);}
[data-testid="stMetricLabel"] p {color: #475467; font-weight: 500;}
.stTabs [data-baseweb="tab-list"] {gap: 4px; border-bottom: 1px solid #e3e8ef;}
.stTabs [data-baseweb="tab"] {padding: 8px 14px; font-weight: 500;}
[data-testid="stExpander"] details {background: #ffffff; border-radius: 12px;}
[data-testid="stSidebarNav"] a span {font-weight: 500;}
[data-testid="stSidebar"] hr {border-color: #22344f;}
.hx-foot {color: #98a2b3; font-size: .8rem; text-align: center; margin-top: 2.5rem;}
</style>
"""

_card_counter = {"n": 0}


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def _icon(name: str) -> str:
    return f'<span class="ms">{name}</span>'


def header(title: str, caption: str | None = None, section: str | None = None) -> None:
    """Đầu trang: nhãn nhóm, tiêu đề, mô tả, và các chip nguồn dữ liệu / khoảng thời gian."""
    _card_counter["n"] = 0
    label, path = source()
    info = q("SELECT min(date) AS d0, max(date) AS d1 FROM dim_date") if has_table("dim_date") else None
    chips = [f'<span class="hx-chip{" demo" if path is None else ""}">{_icon("database")}{label}</span>']
    if info is not None and len(info):
        chips.append(f'<span class="hx-chip">{_icon("calendar_month")}'
                     f'{pd.Timestamp(info.d0[0]):%d/%m/%Y} – {pd.Timestamp(info.d1[0]):%d/%m/%Y}</span>')
    st.markdown(
        f'<div class="hx-head"><div>'
        + (f'<div class="hx-over">{section}</div>' if section else "")
        + f'<div class="hx-title">{title}</div>'
        + (f'<div class="hx-sub">{caption}</div>' if caption else "")
        + f'</div><div class="hx-chips">{"".join(chips)}</div></div>',
        unsafe_allow_html=True)


def kpis(items: list[dict]) -> None:
    """Hàng thẻ chỉ số. Mỗi phần tử: label, value, note (tuỳ chọn, cho phép HTML), icon, tone."""
    cards = []
    for it in items:
        cards.append(
            f'<div class="hx-kpi"><div class="hx-kpi-top">'
            f'<div class="hx-kpi-icon {it.get("tone", "")}">{_icon(it.get("icon", "insights"))}</div>'
            f'{it["label"]}</div><div class="hx-kpi-value">{it["value"]}</div>'
            + (f'<div class="hx-kpi-note">{it["note"]}</div>' if it.get("note") else "")
            + "</div>")
    st.markdown(f'<div class="hx-kpis">{"".join(cards)}</div>', unsafe_allow_html=True)


def delta(x: float, suffix: str = "") -> str:
    """Mũi tên tăng/giảm có màu cho phần ghi chú của thẻ chỉ số."""
    if pd.isna(x):
        return ""
    cls, arrow = ("hx-up", "▲") if x >= 0 else ("hx-down", "▼")
    return f'<span class="{cls}">{arrow} {pct(abs(x))}</span>{suffix}'


ALERT_ICONS = {"critical": "error", "warning": "warning", "info": "info", "good": "check_circle"}


def alert(kind: str, html: str) -> None:
    """Thẻ cảnh báo: kind là critical / warning / info / good. Nội dung cho phép HTML (<b>, <i>)."""
    st.markdown(f'<div class="hx-alert {kind}">{_icon(ALERT_ICONS.get(kind, "info"))}'
                f'<div class="hx-alert-text">{html}</div></div>', unsafe_allow_html=True)


def section(title: str, icon: str = "bar_chart") -> None:
    st.markdown(f'<div class="hx-section">{_icon(icon)}{title}</div>', unsafe_allow_html=True)


def card():
    """Khung thẻ trắng bo góc để đặt biểu đồ hoặc bảng: `with lib.card(): ...`."""
    _card_counter["n"] += 1
    return st.container(key=f"card_{_card_counter['n']}")


def layout(fig, height: int = 360, **kw):
    fig.update_layout(**viz.plotly_layout(height=height, **kw))
    return fig


def show(fig, height: int = 360, card_frame: bool = True, **kw) -> None:
    fig = layout(fig, height, **kw)
    if card_frame:
        with card():
            st.plotly_chart(fig, width="stretch", theme="streamlit")
    else:
        st.plotly_chart(fig, width="stretch", theme="streamlit")


def note(text: str) -> None:
    st.caption(text)


def footer() -> None:
    st.markdown('<div class="hx-foot">Hasu · Phân tích bán hàng & dự báo nhu cầu cho cửa hàng bán lẻ · '
                'Dữ liệu KiotViet</div>', unsafe_allow_html=True)


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
