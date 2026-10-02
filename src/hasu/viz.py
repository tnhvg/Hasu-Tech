"""Bảng màu và kiểu vẽ dùng chung cho mọi biểu đồ (matplotlib và Plotly).

Bảng màu phân loại đã được kiểm tra khả năng phân biệt cho người mù màu
(CVD ΔE >= 8 giữa các màu liền kề). Thứ tự màu cố định, không xoay vòng.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
MUTED = "#8a8984"
GRID = "#e6e5e1"

# Màu phân loại theo thứ tự cố định (slot 1, 2, 3...)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
# Màu trạng thái: chỉ dùng khi màu mang nghĩa tốt/xấu, luôn kèm nhãn chữ.
GOOD, WARNING, SERIOUS, CRITICAL = "#0ca30c", "#fab219", "#ec835a", "#d03b3b"
# Thang tuần tự một màu (xanh), từ nhạt tới đậm, cho bản đồ nhiệt.
BLUE_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
NEUTRAL = "#c3c2b7"


def apply_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT_2,
        "axes.titlecolor": TEXT,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 12,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": TEXT_2,
        "ytick.color": TEXT_2,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "font.size": 10,
        "legend.frameon": False,
        "lines.linewidth": 2,
        "figure.dpi": 110,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
    })


def fmt_million(x: float, _pos=None) -> str:
    return f"{x / 1e6:,.1f}".replace(".", ",") + " tr"


def fmt_int(x: float, _pos=None) -> str:
    return f"{x:,.0f}".replace(",", ".")


def plotly_layout(**overrides) -> dict:
    """Bố cục Plotly cho ứng dụng: không cố định màu chữ/nền để tự theo giao diện sáng/tối
    của Streamlit; chỉ cố định bảng màu phân loại, lưới mờ, tooltip theo trục x."""
    layout = dict(
        colorway=SERIES,
        margin=dict(l=8, r=8, t=40, b=40),
        hovermode="x unified",
        xaxis=dict(showgrid=False, ticks=""),
        yaxis=dict(gridcolor="rgba(128,128,128,0.18)", zeroline=False, ticks=""),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0, title_text="",
                    traceorder="normal"),
        separators=",.",
        title=dict(x=0, xanchor="left", font=dict(size=15)),
    )
    layout.update(overrides)
    return layout
