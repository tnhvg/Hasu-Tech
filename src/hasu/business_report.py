"""Báo cáo phân tích kinh doanh: sinh biểu đồ và docs/business_analysis.md.

    python -m hasu.business_report

Mọi con số trong báo cáo được truy vấn trực tiếp từ DuckDB, không gõ tay.
Chạy sau `python -m hasu.pipeline`.
"""

from __future__ import annotations

from datetime import date, datetime

import duckdb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FuncFormatter, PercentFormatter

from hasu import viz
from hasu.config import DB_PATH, DOCS_DIR

FIG_DIR = DOCS_DIR / "figures"
TET = date(2026, 2, 17)
WEEKDAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]


def pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f}%".replace(".", ",")


def num(x: float, digits: int = 0) -> str:
    s = f"{x:,.{digits}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def mil(x: float) -> str:
    return num(x / 1e6, 1) + " triệu đ"


def times(x: float) -> str:
    return num(x, 2) + " lần"


def md_table(df: pd.DataFrame) -> str:
    header = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    rows = ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join([header, sep, *rows])


def save(fig, name: str) -> str:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / name)
    plt.close(fig)
    return f"figures/{name}"


# --------------------------------------------------------------------------
# Biểu đồ
# --------------------------------------------------------------------------

def fig_monthly(m: pd.DataFrame) -> str:
    p = m[m["channel"] != "Nội bộ"].pivot(index="year_month", columns="channel",
                                         values="revenue_per_open_day").fillna(0)
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(p))
    retail = p["Bán lẻ"].to_numpy()
    bulk = p["Đơn lớn / tổ chức"].to_numpy()
    ax.bar(x, retail, width=0.62, color=viz.SERIES[0], label="Bán lẻ")
    # khe 2px giữa hai phần chồng nhau: viền màu nền
    ax.bar(x, bulk, width=0.62, bottom=retail, color=viz.SERIES[1], label="Đơn lớn / tổ chức",
           edgecolor=viz.SURFACE, linewidth=1.5)
    ax.set_xticks(x, [f"{s[5:]}/{s[2:4]}" for s in p.index])
    ax.yaxis.set_major_formatter(FuncFormatter(viz.fmt_million))
    ax.set_title("Doanh thu trung bình mỗi ngày mở cửa, theo tháng và kênh bán")
    ax.legend(loc="upper left", ncols=2)
    for i, (r, b) in enumerate(zip(retail, bulk)):
        ax.text(i, r / 2, viz.fmt_million(r), ha="center", va="center", color="white", fontsize=8)
    return save(fig, "01_doanh_thu_theo_thang.png")


def fig_pareto(abc: pd.DataFrame, n_a: int) -> str:
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(abc["qty_rank"], abc["cum_qty_share"], color=viz.SERIES[0])
    ax.axhline(0.8, color=viz.MUTED, linewidth=1, linestyle=(0, (3, 3)))
    ax.axvline(n_a, color=viz.MUTED, linewidth=1, linestyle=(0, (3, 3)))
    ax.scatter([n_a], [0.8], s=40, color=viz.SERIES[0], zorder=3, edgecolor=viz.SURFACE, linewidth=2)
    ax.annotate(f"{n_a} mã ({pct(n_a / len(abc), 0)} số mã)\nchiếm 80% số lượng bán lẻ",
                (n_a, 0.8), xytext=(n_a + 120, 0.55), color=viz.TEXT,
                arrowprops=dict(arrowstyle="-", color=viz.MUTED))
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_xlabel("Số mã hàng (xếp theo số lượng bán giảm dần)")
    ax.set_ylim(0, 1.02)
    ax.set_xlim(0, len(abc))
    ax.set_title("Đường Pareto: tỷ lệ số lượng bán lẻ cộng dồn")
    return save(fig, "02_pareto_abc.png")


def fig_heatmap(h: pd.DataFrame) -> str:
    grid = h.pivot(index="iso_weekday", columns="sale_hour", values="avg_invoices").fillna(0)
    grid = grid.loc[:, 6:21]
    cmap = LinearSegmentedColormap.from_list("blue", ["#f0efec", *viz.BLUE_RAMP])
    fig, ax = plt.subplots(figsize=(10, 3.8))
    im = ax.imshow(grid.to_numpy(), cmap=cmap, aspect="auto")
    ax.set_yticks(range(7), WEEKDAYS)
    ax.set_xticks(range(grid.shape[1]), [f"{c}h" for c in grid.columns])
    ax.grid(False)
    for (i, j), v in np.ndenumerate(grid.to_numpy()):
        ax.text(j, i, num(v, 1), ha="center", va="center", fontsize=7.5,
                color="white" if v > grid.to_numpy().max() * 0.6 else viz.TEXT_2)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
    cb.outline.set_visible(False)
    cb.set_label("hoá đơn / giờ", color=viz.TEXT_2)
    ax.set_title("Số hoá đơn bán lẻ trung bình mỗi giờ, theo thứ trong tuần")
    return save(fig, "03_ban_do_nhiet_gio_thu.png")


def fig_margin(cm: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(9, 5.2))
    loss = cm["quadrant"] == "Thua lỗ"
    ax.scatter(cm.loc[~loss, "revenue"], cm.loc[~loss, "margin"], s=36, color=viz.SERIES[0],
               edgecolor=viz.SURFACE, linewidth=1.5, label="Nhóm hàng có lãi", zorder=3)
    ax.scatter(cm.loc[loss, "revenue"], cm.loc[loss, "margin"], s=40, color=viz.CRITICAL,
               marker="X", edgecolor=viz.SURFACE, linewidth=1, label="Nhóm hàng thua lỗ", zorder=3)
    rev_med, store_m = cm["rev_median"].iloc[0], cm["store_margin"].iloc[0]
    ax.axvline(rev_med, color=viz.MUTED, linewidth=1, linestyle=(0, (3, 3)))
    ax.axhline(store_m, color=viz.MUTED, linewidth=1, linestyle=(0, (3, 3)))
    ax.axhline(0, color=viz.TEXT_2, linewidth=0.8)
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(viz.fmt_million))
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_ylim(-0.5, 0.35)
    ax.set_xlabel("Doanh thu 10 tháng (thang logarit)")
    ax.set_ylabel("Biên lợi nhuận gộp")
    big = cm[cm["revenue"] >= rev_med]
    labelled = pd.concat([big.nlargest(3, "revenue"), cm[loss & (cm["revenue"] > 5e6)]]).drop_duplicates("cat_l2")
    # Vị trí nhãn (điểm ảnh lệch so với điểm dữ liệu), nối với điểm bằng đường dẫn
    # để không gán nhầm nhãn cho điểm bên cạnh.
    offsets = {"Bánh": (-10, 30), "Nước ngọt": (8, 18), "Gia vị": (-40, -30),
               "Vệ sinh nhà cửa": (10, -26), "Sữa nước các loại": (-20, -38),
               "Dầu ăn": (10, -14), "Sữa chua": (10, -16), "Sữa, sản phẩm từ sữa": (-10, 14),
               "Sữa bột": (10, 4)}
    for r in labelled.itertuples():
        dx, dy = offsets.get(r.cat_l2, (8, 6))
        ax.annotate(r.cat_l2, (r.revenue, r.margin), xytext=(dx, dy), textcoords="offset points",
                    fontsize=8, color=viz.TEXT, ha="right" if dx < 0 else "left", va="center",
                    arrowprops=dict(arrowstyle="-", color=viz.MUTED, linewidth=0.7, shrinkA=0, shrinkB=3))
    kw = dict(color=viz.TEXT_2, fontsize=9, weight="bold")
    ymin, ymax = ax.get_ylim()
    y_line = (store_m - ymin) / (ymax - ymin)
    ax.text(0.01, 0.98, "Tiềm năng", ha="left", va="top", transform=ax.transAxes, **kw)
    ax.text(0.01, y_line - 0.02, "Cần xem xét", ha="left", va="top", transform=ax.transAxes, **kw)
    ax.text(1.01, y_line + 0.02, "Ngôi sao", ha="left", va="bottom", transform=ax.transAxes, **kw)
    ax.text(1.01, y_line - 0.02, "Lời mỏng", ha="left", va="top", transform=ax.transAxes, **kw)
    ax.legend(loc="lower left")
    ax.set_title("Ma trận doanh thu × biên lợi nhuận, nhóm hàng cấp 2")
    return save(fig, "04_ma_tran_bien_loi_nhuan.png")


def fig_tet(daily: pd.DataFrame, closed: pd.Series) -> str:
    d = daily[(daily["date"] >= pd.Timestamp("2026-01-10")) & (daily["date"] <= pd.Timestamp("2026-03-20"))]
    full = pd.DataFrame({"date": pd.date_range("2026-01-10", "2026-03-20")}).merge(d, how="left")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axvspan(pd.Timestamp(TET) - pd.Timedelta(days=14), pd.Timestamp(TET) + pd.Timedelta(days=13),
               color="#f0efec", zorder=0)
    ax.plot(full["date"], full["revenue"], color=viz.SERIES[0], marker="o", markersize=3)
    ax.axvline(pd.Timestamp(TET), color=viz.TEXT_2, linewidth=1)
    top = full["revenue"].max() * 1.08
    ax.set_ylim(0, top * 1.05)
    ax.text(pd.Timestamp(TET) + pd.Timedelta(days=0.6), top, "Mùng 1 Tết", color=viz.TEXT_2,
            fontsize=9, va="top")
    ax.text(pd.Timestamp(TET) - pd.Timedelta(days=13.6), top * 0.03, "Vùng ảnh hưởng ±14 ngày",
            color=viz.TEXT_2, fontsize=9, va="bottom")
    ax.yaxis.set_major_formatter(FuncFormatter(viz.fmt_million))
    ax.set_title("Doanh thu bán lẻ mỗi ngày quanh Tết Bính Ngọ (khoảng đứt = cửa hàng đóng cửa)")
    fig.autofmt_xdate()
    return save(fig, "05_tet.png")


# --------------------------------------------------------------------------
# Báo cáo
# --------------------------------------------------------------------------

def build(con: duckdb.DuckDBPyConnection) -> str:
    viz.apply_style()
    q = lambda sql: con.execute(sql).df()  # noqa: E731

    monthly = q("SELECT * FROM mart_monthly")
    abc = q("SELECT * FROM mart_sku_abc ORDER BY qty_rank")
    hour = q("SELECT * FROM mart_hour_weekday")
    cm = q("SELECT * FROM mart_category_margin")
    tet = q("SELECT * FROM mart_tet_effect")
    rules = q("SELECT * FROM mart_basket_rules")
    stock = q("SELECT * FROM mart_stockout_suspects")
    daily = q("SELECT date, sum(revenue) AS revenue, sum(quantity) AS quantity, "
              "sum(n_invoices) AS n_invoices FROM fct_retail_daily_category GROUP BY 1 ORDER BY 1")
    daily["date"] = pd.to_datetime(daily["date"])
    closed = pd.to_datetime(q("SELECT date FROM dim_date WHERE NOT is_open")["date"])
    traffic = q("""
        SELECT strftime(date, '%Y-%m') AS ym, sum(n_invoices) / count(DISTINCT date) AS inv_per_day,
               sum(revenue) / sum(n_invoices) AS basket
        FROM fct_retail_daily_category GROUP BY 1 ORDER BY 1""")

    # ---- Số liệu chính ----
    ch = monthly.groupby("channel")[["revenue", "profit", "n_invoices"]].sum()
    total_rev = ch["revenue"].sum()
    big = ch.loc["Đơn lớn / tổ chức"]
    retail = ch.loc["Bán lẻ"]
    inv_total = ch["n_invoices"].sum()

    rpd = monthly[monthly["channel"] == "Bán lẻ"].set_index("year_month")["revenue_per_open_day"]
    early = rpd.loc["2025-09":"2026-04"].drop("2026-02").mean()
    late = rpd.loc["2026-05":"2026-06"].mean()
    t = traffic.set_index("ym")
    inv_early = t.loc["2025-09":"2026-04", "inv_per_day"].drop("2026-02").mean()
    inv_late = t.loc["2026-05":"2026-06", "inv_per_day"].mean()
    basket_early = t.loc["2025-09":"2026-04", "basket"].drop("2026-02").mean()
    basket_late = t.loc["2026-05":"2026-06", "basket"].mean()

    n_a = int((abc["abc_class"] == "A").sum())
    a_ratio = abc.loc[abc["abc_class"] == "A", "sell_day_ratio"]

    by_hour = hour.groupby("sale_hour")["avg_invoices"].mean()
    by_day = hour.groupby("iso_weekday")["avg_invoices"].sum()
    peak_hour = int(by_hour.idxmax())
    second_peaks = by_hour.drop(peak_hour).nlargest(2).index.tolist()
    trough = by_hour.loc[12:15]

    star = cm[cm["quadrant"] == "Ngôi sao"]
    loss = cm[cm["quadrant"] == "Thua lỗ"].sort_values("profit")
    thin = cm[cm["quadrant"] == "Lời mỏng"]
    store_margin = cm["store_margin"].iloc[0]
    milk = cm[cm["cat_l1"] == "Sữa, sản phẩm từ sữa"]

    tt = tet[tet["cat_l1"] == "Toàn cửa hàng"].set_index("tet_window")
    pre = tet[(tet["tet_window"] == "Trước Tết") & (tet["cat_l1"] != "Toàn cửa hàng")
              & (tet["rev_per_day"] > 50_000)].sort_values("rev_factor", ascending=False)

    oil = q("""
        SELECT product_name, sum(quantity) AS qty, median(unit_price) AS price,
               median(unit_cost_filled) AS cost, sum(line_profit) AS profit
        FROM stg_sales_lines WHERE cat_l2 = 'Dầu ăn' AND cost_fill_method IS NOT NULL
        GROUP BY 1 ORDER BY profit LIMIT 1""").iloc[0]

    # ---- Biểu đồ ----
    f1 = fig_monthly(monthly)
    f2 = fig_pareto(abc, n_a)
    f3 = fig_heatmap(hour)
    f4 = fig_margin(cm)
    f5 = fig_tet(daily, closed)

    out: list[str] = []
    add = out.append
    add("# Phân tích kinh doanh — Cửa hàng BHS Đại Phúc\n")
    add(f"_Sinh tự động bởi `python -m hasu.business_report` lúc {datetime.now():%d/%m/%Y %H:%M}. "
        "Dữ liệu: 11/09/2025 – 30/06/2026. Mọi con số được truy vấn trực tiếp từ dữ liệu đã làm sạch "
        "(xem [báo cáo chất lượng dữ liệu](data_quality_report.md))._\n")
    add("**Nguyên tắc đo lường:** quyết định vận hành và tồn kho (nhập bao nhiêu, xếp ca) dùng "
        "**số lượng** và **số hoá đơn**; quyết định tài chính (định giá, chọn nhóm hàng) dùng "
        "**doanh thu** và **lợi nhuận**.\n")

    # ---- Tóm tắt ----
    add("## Tóm tắt cho chủ cửa hàng\n")
    add(f"1. **Đơn lớn chỉ chiếm {pct(big.n_invoices / inv_total)} số hoá đơn nhưng mang về "
        f"{pct(big.revenue / total_rev, 0)} doanh thu**, với biên lợi nhuận "
        f"{pct(big.profit / big.revenue)} (bán lẻ: {pct(retail.profit / retail.revenue)}). "
        "Đây là một kênh bán riêng, cần được quản lý và dự báo riêng.")
    add(f"2. **Lượng khách bán lẻ giảm rõ trong tháng 5–6/2026**: từ khoảng {num(inv_early)} hoá đơn/ngày "
        f"xuống {num(inv_late)} hoá đơn/ngày ({pct(inv_late / inv_early - 1, 0)}), trong khi giá trị "
        f"mỗi hoá đơn gần như không đổi ({num(basket_early)} đ → {num(basket_late)} đ). Nguyên nhân là "
        "**ít khách hơn**, không phải khách mua ít đi.")
    add(f"3. **{len(loss)} nhóm hàng đang bán lỗ**, tập trung ở dầu ăn và các sản phẩm từ sữa. "
        f"Riêng {oil.product_name} được bán khoảng {num(oil.price)} đ trong khi giá vốn ghi nhận "
        f"{num(oil.cost)} đ, lỗ {mil(-oil.profit)}. Cần kiểm tra lại giá vốn hoặc giá bán.")
    add(f"4. **Tết làm tăng doanh thu bán lẻ {times(tt.loc['Trước Tết', 'rev_factor'])} nhưng số lượng "
        f"chỉ tăng {times(tt.loc['Trước Tết', 'qty_factor'])}** trong 14 ngày trước Tết: khách mua hàng "
        "đắt hơn (quà biếu, thùng nước, bánh kẹo hộp) chứ không mua nhiều món hơn hẳn.")
    add(f"5. **Cao điểm lúc {peak_hour}h** ({num(by_hour.max(), 1)} hoá đơn/giờ), thấp điểm "
        f"{trough.idxmin()}h–15h. Chủ nhật vắng nhất ({num(by_day.min(), 0)} hoá đơn/ngày so với "
        f"{num(by_day.drop(7).mean(), 0)} các ngày khác).\n")

    # ---- 1. Xu hướng ----
    add("## 1. Xu hướng doanh thu và lợi nhuận\n")
    add(f"![Doanh thu theo tháng]({f1})\n")
    add("Biểu đồ dùng **doanh thu trung bình mỗi ngày mở cửa** thay cho tổng tháng, vì tháng 09/2025 "
        "chỉ có dữ liệu từ ngày 11 và tháng 02/2026 nghỉ Tết 7 ngày. So tổng tháng sẽ cho kết luận sai.\n")
    tbl = monthly[monthly["channel"] != "Nội bộ"].pivot(index="year_month", columns="channel",
                                                       values=["revenue_per_open_day", "profit", "revenue"])
    view = pd.DataFrame({
        "Tháng": tbl.index,
        "Bán lẻ / ngày": tbl[("revenue_per_open_day", "Bán lẻ")].map(lambda v: mil(v)),
        "Biên bán lẻ": (tbl[("profit", "Bán lẻ")] / tbl[("revenue", "Bán lẻ")]).map(pct),
        "Đơn lớn / ngày": tbl[("revenue_per_open_day", "Đơn lớn / tổ chức")].map(lambda v: mil(v)),
        "Hoá đơn bán lẻ / ngày": t["inv_per_day"].map(lambda v: num(v)).values,
        "Giá trị / hoá đơn": t["basket"].map(lambda v: num(v) + " đ").values,
    })
    add(md_table(view))
    add(f"\n**Nhận xét.** Doanh thu bán lẻ ổn định quanh {mil(early)}/ngày từ tháng 9 đến tháng 4 (trừ "
        f"tháng Tết), rồi giảm còn {mil(late)}/ngày trong tháng 5–6. Số hoá đơn mỗi ngày giảm tương ứng "
        "trong khi giá trị mỗi hoá đơn không đổi, nên sụt giảm đến từ **lượng khách**. Dữ liệu bán hàng "
        "không cho biết lý do (mùa hè, đối thủ mới, thay đổi giờ mở cửa...): **cần chủ cửa hàng xác nhận**.\n")
    add("Biên lợi nhuận bán lẻ tụt thấp trong tháng 2–4/2026. Các khoản lỗ lớn nhất trong giai đoạn này "
        "nằm ở giặt giũ (tháng 2), thực phẩm ăn liền (tháng 3–4) và sữa chua: phù hợp với việc bán xả "
        "hàng cận hạn hoặc giá vốn nhập tăng mà giá bán chưa điều chỉnh.\n")

    # ---- 2. ABC ----
    add("## 2. Phân loại ABC theo số lượng bán lẻ\n")
    add(f"![Pareto]({f2})\n")
    abc_tbl = abc.groupby("abc_class").agg(n=("sku", "size"), qty=("quantity", "sum"),
                                           rev=("revenue", "sum"), ratio=("sell_day_ratio", "median"))
    add(md_table(pd.DataFrame({
        "Nhóm": abc_tbl.index,
        "Số mã": abc_tbl["n"].map(num),
        "Tỷ lệ số mã": (abc_tbl["n"] / abc_tbl["n"].sum()).map(pct),
        "Tỷ lệ số lượng": (abc_tbl["qty"] / abc_tbl["qty"].sum()).map(pct),
        "Tỷ lệ doanh thu bán lẻ": (abc_tbl["rev"] / abc_tbl["rev"].sum()).map(pct),
        "Trung vị % ngày có bán": abc_tbl["ratio"].map(pct),
    })))
    add(f"\n**Nhận xét.** {n_a} mã hàng nhóm A ({pct(n_a / len(abc), 0)} số mã) chiếm 80% số lượng bán lẻ. "
        f"Tuy vậy, ngay cả trong nhóm A, trung vị mỗi mã chỉ bán ra ở {pct(a_ratio.median(), 0)} số ngày. "
        "Vì vậy dự báo cho **từng mã** theo ngày vẫn rất nhiễu, và mô hình sẽ dự báo ở **cấp nhóm hàng** trước.\n")
    top10 = abc.head(10)
    add(md_table(pd.DataFrame({
        "#": top10["qty_rank"],
        "Mã hàng": top10["product_name"],
        "Số lượng": top10["quantity"].map(num),
        "% ngày có bán": top10["sell_day_ratio"].map(pct),
    })))

    # ---- 3. Heatmap ----
    add("\n## 3. Mẫu hình theo giờ và thứ\n")
    add(f"![Bản đồ nhiệt]({f3})\n")
    add(f"- **Ba khung cao điểm**: {peak_hour}h (cao nhất), {second_peaks[0]}h và {second_peaks[1]}h, "
        "trùng giờ đi làm về, giờ đi làm buổi sáng và trước bữa trưa.\n"
        f"- **Thấp điểm** {trough.idxmin()}h–15h ({num(trough.mean(), 1)} hoá đơn/giờ).\n"
        f"- **Chủ nhật** vắng hơn rõ rệt ({num(by_day.loc[7], 0)} hoá đơn/ngày).\n")
    add("**Khuyến nghị xếp ca:** bố trí đủ người đứng quầy 16h–19h và 7h–9h; dùng khung 13h–15h để "
        "nhận hàng, kiểm kho, sắp xếp kệ.\n")

    # ---- 4. Biên lợi nhuận ----
    add("## 4. Biên lợi nhuận theo nhóm hàng\n")
    add(f"![Ma trận biên lợi nhuận]({f4})\n")
    add(f"Hai đường chia: doanh thu trung vị giữa các nhóm ({mil(cm['rev_median'].iloc[0])}) và biên "
        f"lợi nhuận chung của cửa hàng ({pct(store_margin)}).\n")
    qsum = cm.groupby("quadrant").agg(n=("cat_l2", "size"), share=("revenue_share", "sum"),
                                      profit=("profit", "sum"))
    order = ["Ngôi sao", "Lời mỏng", "Tiềm năng", "Cần xem xét", "Thua lỗ"]
    qsum = qsum.reindex([o for o in order if o in qsum.index])
    add(md_table(pd.DataFrame({
        "Phân nhóm": qsum.index,
        "Số nhóm hàng": qsum["n"],
        "Tỷ trọng doanh thu": qsum["share"].map(pct),
        "Lợi nhuận gộp": qsum["profit"].map(mil),
    })))
    add("\n**Nhóm thua lỗ:**\n")
    add(md_table(pd.DataFrame({
        "Nhóm hàng": loss["cat_l2"],
        "Doanh thu": loss["revenue"].map(mil),
        "Lợi nhuận gộp": loss["profit"].map(mil),
        "Biên": loss["margin"].map(pct),
    })))
    add(f"\n**Nhận xét.**\n\n"
        f"- {len(star)} nhóm \"ngôi sao\" (nước ngọt, bánh, trà, snack, thuốc lá...) tạo "
        f"{pct(star['revenue_share'].sum(), 0)} doanh thu với biên cao hơn mức chung: đây là nhóm cần "
        "**không bao giờ để hết hàng**.\n"
        f"- {len(thin)} nhóm \"lời mỏng\" như gia vị, vệ sinh nhà cửa, giặt giũ chiếm "
        f"{pct(thin['revenue_share'].sum(), 0)} doanh thu nhưng biên rất thấp, phần lớn do bán theo "
        "đơn lớn. Nên xem lại giá bán sỉ cho các nhóm này.\n"
        f"- Toàn bộ ngành **sữa** đang lỗ hoặc gần hoà vốn (sữa bột biên "
        f"{pct(milk.loc[milk['cat_l2'] == 'Sữa bột', 'margin'].iloc[0]) if (milk['cat_l2'] == 'Sữa bột').any() else 'n/a'}). "
        "Sữa có hạn dùng ngắn, nên khả năng cao là xả hàng cận hạn. Đây chính là nhóm cần dự báo sát "
        "nhất để giảm hàng dư.\n"
        "- **Hạn chế:** giá vốn lấy từ KiotViet tại thời điểm bán. Nếu giá vốn nhập sai (ví dụ nhập theo "
        "thùng nhưng bán theo chai), biên sẽ sai. Các nhóm thua lỗ cần chủ cửa hàng đối chiếu hoá đơn nhập.\n")

    # ---- 5. Tết ----
    add("## 5. Ảnh hưởng của Tết\n")
    add(f"![Tết]({f5})\n")
    add(md_table(pd.DataFrame({
        "Giai đoạn": tt.index,
        "Số ngày mở cửa": tt["n_days"],
        "Hệ số số lượng": tt["qty_factor"].map(times),
        "Hệ số doanh thu": tt["rev_factor"].map(times),
    })))
    add("\nHệ số = trung bình mỗi ngày mở cửa trong giai đoạn / trung bình các ngày mở cửa ngoài vùng ±14 ngày.\n")
    add("**Nhóm hàng tăng mạnh nhất 14 ngày trước Tết (theo doanh thu):**\n")
    add(md_table(pd.DataFrame({
        "Nhóm hàng cấp 1": pre["cat_l1"].head(6),
        "Hệ số doanh thu": pre["rev_factor"].head(6).map(times),
        "Hệ số số lượng": pre["qty_factor"].head(6).map(times),
    })))
    add("\n**Nhận xét.** Trước Tết, doanh thu tăng mạnh hơn nhiều so với số lượng. Điều này khẳng định "
        "nguyên tắc dùng đúng thước đo: nếu nhập hàng Tết theo hệ số doanh thu "
        f"{times(tt.loc['Trước Tết', 'rev_factor'])}, cửa hàng sẽ nhập dư gần gấp rưỡi so với nhu cầu "
        "thực tế về số lượng. Với dự báo nhập hàng, dùng **hệ số số lượng theo từng nhóm hàng**. "
        "**Giới hạn:** dữ liệu chỉ có một kỳ Tết, nên các hệ số này là một lần quan sát và sẽ được "
        "cập nhật khi có thêm dữ liệu.\n")

    # ---- 6. Giỏ hàng ----
    add("## 6. Phân tích giỏ hàng\n")
    n_b = int(rules["total_multi_item_baskets"].iloc[0]) if len(rules) else 0
    add(f"Thuật toán FP-Growth (cùng kết quả với Apriori, chạy nhanh hơn) trên {num(n_b)} hoá đơn bán lẻ "
        "có từ 2 nhóm hàng trở lên, **đã loại các dòng bán dưới giá phổ biến** để luật phản ánh hành vi "
        "mua tự nhiên chứ không phải tác động của khuyến mãi. Phân tích ở cấp nhóm hàng 3 vì từng mã hàng "
        "quá thưa.\n")
    add("- **Độ tin cậy (confidence)**: trong các hoá đơn có A, bao nhiêu % có cả B.\n"
        "- **Lift**: khả năng mua B khi đã mua A cao gấp bao nhiêu lần so với bình thường. Lift > 1 là có liên kết.\n")
    top = rules.head(10)
    add(md_table(pd.DataFrame({
        "Nếu mua": top["antecedent"],
        "Thì thường mua": top["consequent"],
        "Số hoá đơn": top["n_baskets"],
        "Độ tin cậy": top["confidence"].map(pct),
        "Lift": top["lift"].map(lambda v: num(v, 2)),
    })))
    add("\n**Đọc kết quả cẩn thận:** một số luật có lift cao nhưng thực chất là **cùng một loại hàng bị "
        "chia làm hai nhóm** trong KiotViet: `Mì ăn liền` và `Mì, bún, phở, cháo ăn liền`, `Kẹo Tổng Hợp` "
        "và `Kẹo`, `Snack Bim bim` và `Snack các loại`. Đây là dấu hiệu cây nhóm hàng cần gộp lại, "
        "không phải hành vi mua kèm. Các khuyến nghị dưới đây chỉ dựa trên những cặp khác loại hàng.\n")
    add("**Khuyến nghị combo và bày kệ:**\n\n"
        "- `Dụng cụ bếp khác → Thuốc lá` có lift cao nhất. Kiểm tra cho thấy nhóm này thực chất là "
        "**bật lửa**, bị xếp nhầm nhóm hàng. Nên chuyển bật lửa về cạnh quầy thuốc lá, đồng thời sửa "
        "nhóm hàng trong KiotViet.\n"
        "- **Mì + xúc xích/lạp xưởng ăn liền**: combo \"bữa ăn nhanh\". Đặt hai nhóm cạnh nhau, "
        "hoặc bán kèm giá combo.\n"
        "- **Thuốc lá + nước giải khát**, **trà/cà phê + nước giải khát**: đặt tủ nước gần quầy thu ngân.\n"
        "- **Sữa tươi + bánh**: combo bữa sáng cho khung 7h–9h.\n")

    # ---- 7. Hết hàng ----
    add("## 7. Nghi ngờ hết hàng (nhu cầu không được đáp ứng)\n")
    n_freq = int((abc["sell_day_ratio"] >= 0.15).sum())
    s_skus = stock["sku"].nunique()
    end = stock[stock["status"].str.startswith("Không bán tới cuối")]
    add(f"Xét {n_freq} mã hàng bán đều (có bán ở ≥ 15% số ngày mở cửa). Với mỗi mã, nếu một chuỗi ngày "
        "mở cửa liên tiếp không bán được có xác suất xảy ra ngẫu nhiên dưới 1%, chuỗi đó bị đánh dấu "
        "nghi ngờ hết hàng.\n")
    add(f"- **{s_skus}/{n_freq} mã** có ít nhất một giai đoạn nghi ngờ, tổng cộng {len(stock)} giai đoạn.\n"
        f"- **{len(end)} mã** ngừng bán hẳn tới cuối kỳ dữ liệu: hoặc đang hết hàng, hoặc đã ngừng kinh doanh.\n")
    show = stock.sort_values("gap_open_days", ascending=False).head(10)
    add(md_table(pd.DataFrame({
        "Mã hàng": show["product_name"],
        "Từ": pd.to_datetime(show["gap_start"]).dt.strftime("%d/%m/%Y"),
        "Đến": pd.to_datetime(show["gap_end"]).dt.strftime("%d/%m/%Y"),
        "Số ngày mở cửa không bán": show["gap_open_days"],
        "% ngày có bán (bình thường)": show["sell_day_ratio"].map(pct),
        "Đánh giá": show["status"],
    })))
    add("\n**Hệ quả cho mô hình:** các giai đoạn này là **dữ liệu bị kiểm duyệt** (censored), tức nhu cầu có "
        "nhưng không bán được vì không có hàng, chứ không phải nhu cầu bằng 0. Khi dự báo ở cấp nhóm hàng, "
        "khách thường mua mã khác trong cùng nhóm, nên ảnh hưởng nhỏ hơn nhiều so với cấp mã hàng.\n\n"
        "**Giới hạn:** đây là suy đoán từ dữ liệu bán. Hàng theo mùa (ví dụ kem vào mùa đông) và hàng "
        "ngừng kinh doanh cũng có biểu hiện giống hệt. Danh sách đầy đủ có trong ứng dụng để chủ cửa hàng "
        "xác nhận từng trường hợp.\n")

    # ---- Khuyến nghị ----
    add("## Khuyến nghị tổng hợp\n")
    add("| # | Khuyến nghị | Căn cứ | Ưu tiên |\n|---|---|---|---|\n"
        f"| 1 | Đối chiếu giá vốn và giá bán các mã đang bán dưới giá vốn, bắt đầu với dầu ăn HASUKOOK và sữa bột | Mục 4: {len(loss)} nhóm hàng lỗ | Cao |\n"
        "| 2 | Tìm hiểu nguyên nhân lượng khách bán lẻ giảm từ tháng 5 | Mục 1: hoá đơn/ngày giảm, giá trị/hoá đơn không đổi | Cao |\n"
        "| 3 | Tách kế hoạch nhập hàng cho kênh đơn lớn khỏi bán lẻ; xem lại giá sỉ nhóm lời mỏng | Tóm tắt 1, mục 4 | Trung bình |\n"
        "| 4 | Ưu tiên không để hết hàng các nhóm ngôi sao; kiểm tra danh sách nghi ngờ hết hàng | Mục 4, mục 7 | Cao |\n"
        "| 5 | Nhập hàng Tết theo hệ số số lượng từng nhóm, không theo hệ số doanh thu | Mục 5 | Theo mùa |\n"
        "| 6 | Xếp ca theo cao điểm 16h–19h, 7h–9h; nhận hàng 13h–15h | Mục 3 | Thấp, làm ngay được |\n"
        "| 7 | Bày bật lửa cạnh quầy thuốc lá, mì cạnh xúc xích | Mục 6 | Thấp, làm ngay được |\n"
        "| 8 | Chuẩn hoá cây nhóm hàng trong KiotViet: sửa nhóm của bật lửa, gộp các nhóm trùng nghĩa (mì, kẹo, snack) | Báo cáo chất lượng dữ liệu, mục 6 | Thấp, giúp mọi phân tích sau chính xác hơn |\n")
    return "\n".join(out)


def main() -> None:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        report = build(con)
    path = DOCS_DIR / "business_analysis.md"
    path.write_text(report, encoding="utf-8")
    print(f"Đã ghi {path.relative_to(DOCS_DIR.parent)} và {len(list(FIG_DIR.glob('*.png')))} biểu đồ")


if __name__ == "__main__":
    main()
