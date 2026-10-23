"""Vẽ biểu đồ cho Bài tập tình huống 1 (học phần Đầu tư tài chính).

Chạy: python bai_tap_dau_tu_tai_chinh/ve_bieu_do.py
Bảng màu và kiểu vẽ giống src/hasu/viz.py để các báo cáo trông đồng bộ.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
MUTED = "#8a8984"
GRID = "#e6e5e1"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]

THU_MUC = Path(__file__).parent / "figures"

# Giá đóng cửa 21–22/10/2026 và vùng giá hợp lý tính trong mục 2 của báo cáo (đồng/cp).
# thap / cao: hai đầu vùng giá hợp lý; chon: mức nhóm chọn làm giá hợp lý.
CO_PHIEU = [
    {"ma": "MBB", "gia": 19_850, "thap": 24_500, "cao": 29_900, "chon": 25_000},
    {"ma": "MWG", "gia": 75_200, "thap": 90_000, "cao": 109_000, "chon": 90_000},
    {"ma": "GAS", "gia": 76_500, "thap": 71_100, "cao": 87_300, "chon": 78_400},
]


def phan_tram(gia_tri: float, gia: float) -> float:
    return (gia_tri / gia - 1) * 100


def ve_dinh_gia() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
        "axes.edgecolor": GRID, "xtick.color": TEXT_2, "ytick.color": TEXT,
        "xtick.major.size": 0, "ytick.major.size": 0, "font.size": 10,
        "axes.titlelocation": "left", "axes.titlesize": 12, "axes.titleweight": "bold",
    })
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.axvline(0, color=MUTED, linewidth=1.2, linestyle="--")
    ax.text(1, 2.5, "Giá hiện tại", color=TEXT_2, fontsize=9, ha="left")

    for i, cp in enumerate(reversed(CO_PHIEU)):
        mau = SERIES[len(CO_PHIEU) - 1 - i]
        thap, cao = phan_tram(cp["thap"], cp["gia"]), phan_tram(cp["cao"], cp["gia"])
        chon = phan_tram(cp["chon"], cp["gia"])
        ax.plot([thap, cao], [i, i], color=mau, linewidth=7, solid_capstyle="round", alpha=0.35)
        ax.scatter([chon], [i], s=70, color=mau, edgecolor=SURFACE, linewidth=2, zorder=3)
        ax.text(cao + 2, i, f"giá hợp lý {cp['chon']:,.0f} đ ({chon:+.0f}%)".replace(",", "."),
                va="center", fontsize=9, color=TEXT)

    ax.set_yticks(range(len(CO_PHIEU)))
    ax.set_yticklabels([cp["ma"] for cp in reversed(CO_PHIEU)], fontweight="bold")
    ax.set_xlim(-15, 95)
    ax.set_ylim(-0.6, 2.8)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:+.0f}%")
    ax.set_xlabel("Chênh lệch so với giá đóng cửa 21–22/10/2026", color=TEXT_2)
    ax.set_title("Dải mờ: vùng giá trị theo các phương pháp định giá; chấm: mức giá hợp lý nhóm chọn",
                 color=TEXT_2, fontsize=9.5, fontweight="normal")
    THU_MUC.mkdir(exist_ok=True)
    fig.savefig(THU_MUC / "01_vung_gia_hop_ly.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    ve_dinh_gia()
    print("Đã lưu", THU_MUC / "01_vung_gia_hop_ly.png")
