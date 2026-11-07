"""Tạo báo cáo Word Bài tập nhóm Đầu tư tài chính – Nhóm 7 – FIN3002_2.

Chạy: python bai_tap_dau_tu_tai_chinh/bai_tap_nhom/tao_bao_cao_nhom.py
Cần: python-docx, matplotlib, pandas, LibreOffice (soffice) và pdftotext để đo số trang cho mục lục.

Quy định trình bày (theo đề): Times New Roman 12, giãn dòng 1,5, khoảng cách trước/sau đoạn 0 pt;
lề trái 2,5 cm, phải 2 cm, trên/dưới 2 cm; header "Bài tập nhóm Đầu tư tài chính"; footer trái
Thứ_Tiết_Nhóm, footer phải số trang; thứ tự: bìa, hoạt động thành viên, mục lục, nội dung, tài liệu
tham khảo; nội dung chính tối đa 15 trang.
"""

import json
import re
import subprocess
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.section import WD_SECTION  # noqa: E402
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt  # noqa: E402

from noi_dung_nhom import BIA, HOAT_DONG, NOI_DUNG, TAI_LIEU  # noqa: E402

THU_MUC = Path(__file__).parent
DU_LIEU_GIA = THU_MUC.parent / "bai_2" / "du_lieu" / "gia_dong_cua.csv"
KET_QUA_SOLVER = THU_MUC / "du_lieu" / "ket_qua_excel_solver.json"
HINH = THU_MUC / "figures"
DICH = THU_MUC / "Nhom7_FIN3002_2_BaoCaoNhom.docx"

FONT = "Times New Roman"
CO = 12
CO_BANG = 11
RONG_TRANG = 16.5  # 21 − 2,5 − 2 (cm)
THUT = Cm(1.0)
FOOTER_TRAI = "Thứ …_Tiết …_Nhóm 7"  # nhóm điền Thứ và Tiết


# ======================= Định dạng chữ =======================

def dat_font(run, co=CO, dam=False, nghieng=False, chi_so=None):
    run.font.name, run.font.size, run.font.bold, run.font.italic = FONT, Pt(co), dam, nghieng
    if chi_so == "duoi":
        run.font.subscript = True
    elif chi_so == "tren":
        run.font.superscript = True
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for k in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(k), FONT)


MAU = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|_\{[^}]*\}|\^\{[^}]*\})")


def them_chu(p, van_ban, co=CO, dam=False, nghieng=False):
    """**đậm**, *nghiêng*, _{chỉ số dưới}, ^{chỉ số trên}. Trong **...** vẫn dùng được _{} và ^{}."""
    for manh in MAU.split(van_ban):
        if not manh:
            continue
        if manh.startswith("**"):
            them_chu(p, manh[2:-2], co, True, nghieng)
        elif manh.startswith("_{"):
            dat_font(p.add_run(manh[2:-1]), co, dam, nghieng, "duoi")
        elif manh.startswith("^{"):
            dat_font(p.add_run(manh[2:-1]), co, dam, nghieng, "tren")
        elif manh.startswith("*") and len(manh) > 1:
            them_chu(p, manh[1:-1], co, dam, True)
        else:
            dat_font(p.add_run(manh), co, dam, nghieng)


def dinh_dang(p, can=WD_ALIGN_PARAGRAPH.JUSTIFY, thut=THUT, gian=1.5, trai=None):
    f = p.paragraph_format
    f.alignment, f.first_line_indent, f.line_spacing = can, thut, gian
    f.space_before = f.space_after = Pt(0)
    if trai is not None:
        f.left_indent = trai


def truong_trang(run):
    for loai, chu in (("begin", None), (None, "PAGE"), ("end", None)):
        if loai:
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), loai)
        else:
            e = OxmlElement("w:instrText")
            e.set(qn("xml:space"), "preserve")
            e.text = chu
        run._r.append(e)


def dat_do_rong_bang(t, rong_cm):
    tbl_pr = t._tbl.tblPr
    for cu in tbl_pr.findall(qn("w:tblW")) + tbl_pr.findall(qn("w:tblLayout")):
        tbl_pr.remove(cu)
    w = OxmlElement("w:tblW")
    w.set(qn("w:w"), str(int(Cm(sum(rong_cm)).twips)))
    w.set(qn("w:type"), "dxa")
    tbl_pr.append(w)
    bc = OxmlElement("w:tblLayout")
    bc.set(qn("w:type"), "fixed")
    tbl_pr.append(bc)
    for j, cot in enumerate(t._tbl.tblGrid.findall(qn("w:gridCol"))):
        cot.set(qn("w:w"), str(int(Cm(rong_cm[j]).twips)))
    for hang in t.rows:
        for j, o in enumerate(hang.cells):
            o.width = Cm(rong_cm[j])


def vien(t, kieu="ba_duong"):
    """ba_duong: viền trên, dưới tiêu đề và viền dưới (bảng nội dung); luoi: kẻ ô đầy đủ."""
    tbl_pr = t._tbl.tblPr
    v = OxmlElement("w:tblBorders")
    canh = ("top", "bottom") if kieu == "ba_duong" else ("top", "left", "bottom", "right", "insideH", "insideV")
    for c in canh:
        e = OxmlElement(f"w:{c}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "8" if kieu == "ba_duong" else "4")
        e.set(qn("w:color"), "000000")
        v.append(e)
    if kieu == "ba_duong":
        e = OxmlElement("w:insideH")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "2")
        e.set(qn("w:color"), "BFBFBF")
        v.append(e)
    tbl_pr.append(v)
    if kieu == "ba_duong":
        for o in t.rows[0].cells:
            tc = o._tc.get_or_add_tcPr()
            b = OxmlElement("w:tcBorders")
            e = OxmlElement("w:bottom")
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), "6")
            e.set(qn("w:color"), "000000")
            b.append(e)
            tc.append(b)


# ======================= Trình tạo tài liệu =======================

class TrinhTao:
    def __init__(self, so_trang):
        self.doc = Document()
        self.so_trang = so_trang
        self.de_muc = []
        st = self.doc.styles["Normal"]
        st.font.name, st.font.size = FONT, Pt(CO)
        st.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
        st.paragraph_format.space_before = st.paragraph_format.space_after = Pt(0)
        st.paragraph_format.line_spacing = 1.5
        for ten in ("Heading 1", "Heading 2", "Heading 3"):
            s = self.doc.styles[ten]
            s.font.name, s.font.size, s.font.bold = FONT, Pt(CO), True
            s.font.color.rgb = None
            s.font.italic = ten == "Heading 3"
            rf = s.element.get_or_add_rPr().get_or_add_rFonts()
            for k in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
                rf.set(qn(k), FONT)
            s.paragraph_format.space_before = s.paragraph_format.space_after = Pt(0)
        sec = self.doc.sections[0]
        sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
        sec.top_margin = sec.bottom_margin = Cm(2)
        sec.left_margin, sec.right_margin = Cm(2.5), Cm(2)
        sec.header_distance = sec.footer_distance = Cm(1)

    # ---- khối nội dung ----
    def doan(self, chu, thut=THUT, can=WD_ALIGN_PARAGRAPH.JUSTIFY, co=CO, dam=False, nghieng=False):
        p = self.doc.add_paragraph()
        dinh_dang(p, can, thut)
        them_chu(p, chu, co, dam, nghieng)
        return p

    def liet_ke(self, cac_y, ky_hieu="abc"):
        for i, y in enumerate(cac_y):
            nhan = f"{'abcdefghij'[i]})" if ky_hieu == "abc" else "–"
            p = self.doc.add_paragraph()
            dinh_dang(p, thut=Cm(-0.6), trai=Cm(1.6))
            p.paragraph_format.tab_stops.add_tab_stop(Cm(1.6))
            them_chu(p, f"{nhan}\t{y}")

    def cong_thuc(self, chu, so):
        p = self.doc.add_paragraph()
        dinh_dang(p, can=WD_ALIGN_PARAGRAPH.LEFT, thut=Cm(0))
        p.paragraph_format.tab_stops.add_tab_stop(Cm(RONG_TRANG / 2), WD_TAB_ALIGNMENT.CENTER)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(RONG_TRANG), WD_TAB_ALIGNMENT.RIGHT)
        them_chu(p, f"\t{chu}\t({so})")

    def tieu_de_phan(self, chu, ngat_trang=False):
        p = self.doc.add_paragraph(style="Heading 1")
        dinh_dang(p, WD_ALIGN_PARAGRAPH.CENTER, None)
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.page_break_before = ngat_trang
        dat_font(p.add_run(chu), CO, True)
        self.de_muc.append((1, chu))

    def muc(self, chu, cap):
        p = self.doc.add_paragraph(style=f"Heading {cap}")
        dinh_dang(p, WD_ALIGN_PARAGRAPH.LEFT, None)
        p.paragraph_format.keep_with_next = True
        dat_font(p.add_run(chu), CO, True, cap == 3)
        self.de_muc.append((cap, chu))

    def bang(self, so, ten, hang, rong, can_phai=(), nguon=None):
        p = self.doc.add_paragraph()
        dinh_dang(p, WD_ALIGN_PARAGRAPH.CENTER, None)
        p.paragraph_format.keep_with_next = True
        dat_font(p.add_run(f"Bảng {so}. {ten}"), CO, True)
        t = self.doc.add_table(rows=len(hang), cols=len(rong))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        for i, dong in enumerate(hang):
            for j, gia_tri in enumerate(dong):
                pp = t.cell(i, j).paragraphs[0]
                dinh_dang(pp, WD_ALIGN_PARAGRAPH.LEFT, None, gian=1.0)
                if i == 0:
                    pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    them_chu(pp, str(gia_tri), CO_BANG, dam=True)
                else:
                    pp.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j in can_phai else WD_ALIGN_PARAGRAPH.LEFT
                    them_chu(pp, str(gia_tri), CO_BANG)
                if i < len(hang) - 1:
                    pp.paragraph_format.keep_with_next = True
        tr = t.rows[0]._tr.get_or_add_trPr()
        lap = OxmlElement("w:tblHeader")
        lap.set(qn("w:val"), "true")
        tr.append(lap)
        vien(t)
        dat_do_rong_bang(t, rong)
        if nguon:
            p = self.doc.add_paragraph()
            dinh_dang(p, WD_ALIGN_PARAGRAPH.LEFT, None)
            them_chu(p, f"*Nguồn: {nguon}*", CO_BANG)

    def hinh(self, so, ten, duong_dan, nguon, rong_cm=14.5):
        p = self.doc.add_paragraph()
        dinh_dang(p, WD_ALIGN_PARAGRAPH.CENTER, None, gian=1.0)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(duong_dan), width=Cm(rong_cm))
        p = self.doc.add_paragraph()
        dinh_dang(p, WD_ALIGN_PARAGRAPH.CENTER, None)
        p.paragraph_format.keep_with_next = True
        dat_font(p.add_run(f"Hình {so}. {ten}"), CO, True)
        p = self.doc.add_paragraph()
        dinh_dang(p, WD_ALIGN_PARAGRAPH.CENTER, None)
        them_chu(p, f"*Nguồn: {nguon}*", CO_BANG)

    def ngat_trang(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---- trang bìa ----
    def trang_bia(self):
        sec = self.doc.sections[0]
        pg = OxmlElement("w:pgBorders")
        pg.set(qn("w:offsetFrom"), "page")
        for c in ("top", "left", "bottom", "right"):
            e = OxmlElement(f"w:{c}")
            e.set(qn("w:val"), "thinThickSmallGap")
            e.set(qn("w:sz"), "24")
            e.set(qn("w:space"), "24")
            e.set(qn("w:color"), "1F3864")
            pg.append(e)
        sec._sectPr.append(pg)

        def dong(chu, co=14, dam=True, cach=0):
            for _ in range(cach):
                self.doc.add_paragraph()
            p = self.doc.add_paragraph()
            dinh_dang(p, WD_ALIGN_PARAGRAPH.CENTER, None, gian=1.2)
            dat_font(p.add_run(chu), co, dam)

        dong("ĐẠI HỌC ĐÀ NẴNG", 13, False)
        dong("TRƯỜNG ĐẠI HỌC KINH TẾ", 13)
        dong("KHOA TÀI CHÍNH", 13)
        dong("----------✦✦✦----------", 12, False)
        dong(BIA["loai_bao_cao"], 20, cach=3)
        dong(BIA["hoc_phan"], 16)
        dong(BIA["thu_tiet"], 13, False)
        dong(BIA["nhom"], 16, cach=1)
        for dong_ten in BIA["de_tai"]:
            dong(dong_ten, 15)
        self.doc.add_paragraph()
        self.doc.add_paragraph()

        def thong_tin(nhan, gia_tri):
            p = self.doc.add_paragraph()
            dinh_dang(p, WD_ALIGN_PARAGRAPH.LEFT, None, gian=1.3)
            p.paragraph_format.left_indent = Cm(2.5)
            p.paragraph_format.tab_stops.add_tab_stop(Cm(7.5))
            dat_font(p.add_run(nhan), 13, True)
            dat_font(p.add_run(f"\t{gia_tri}"), 13)

        thong_tin("GVHD:", BIA["gvhd"])
        thong_tin("Lớp học phần:", BIA["lop"])
        for i, (ten, mssv) in enumerate(BIA["thanh_vien"]):
            thong_tin("Thành viên:" if i == 0 else "", f"{ten} – {mssv}")
        thong_tin("Lớp sinh hoạt:", BIA["lop_sinh_hoat"])
        dong(BIA["ngay"], 13, False, cach=3)

    # ---- phần đầu ----
    def tieu_de_trang(self, chu, vao_muc_luc=True):
        p = self.doc.add_paragraph(style="Heading 1")
        dinh_dang(p, WD_ALIGN_PARAGRAPH.CENTER, None)
        dat_font(p.add_run(chu), 14, True)
        if vao_muc_luc:
            self.de_muc.append((1, chu))
        self.doc.add_paragraph()

    def hoat_dong(self):
        self.tieu_de_trang("BÁO CÁO HOẠT ĐỘNG CỦA CÁC THÀNH VIÊN TRONG NHÓM", vao_muc_luc=False)
        hang = [("STT", "Họ và tên", "MSSV", "Nhiệm vụ", "Mức độ đóng góp")]
        hang += [(str(i), t, m, nv, "…%") for i, (t, m, nv) in enumerate(HOAT_DONG["thanh_vien"], start=1)]
        t = self.doc.add_table(rows=len(hang), cols=5)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, dong in enumerate(hang):
            for j, gia_tri in enumerate(dong):
                pp = t.cell(i, j).paragraphs[0]
                dinh_dang(pp, WD_ALIGN_PARAGRAPH.CENTER if j in (0, 2, 4) or i == 0 else WD_ALIGN_PARAGRAPH.LEFT,
                          None, gian=1.2)
                them_chu(pp, gia_tri, CO, dam=i == 0)
        vien(t, "luoi")
        dat_do_rong_bang(t, [1.3, 4.0, 3.0, 5.8, 2.4])
        self.doc.add_paragraph()
        for y in HOAT_DONG["ghi_chu"]:
            self.doan(y, thut=Cm(0), nghieng=True)
        p = self.doc.add_paragraph()
        dinh_dang(p, WD_ALIGN_PARAGRAPH.RIGHT, None)
        them_chu(p, "*Đà Nẵng, ngày 23 tháng 10 năm 2026*")
        p = self.doc.add_paragraph()
        dinh_dang(p, WD_ALIGN_PARAGRAPH.RIGHT, None)
        p.paragraph_format.right_indent = Cm(1.5)
        them_chu(p, "**Nhóm trưởng**")

    def muc_luc(self, de_muc):
        self.tieu_de_trang("MỤC LỤC", vao_muc_luc=False)
        for cap, chu in de_muc:
            p = self.doc.add_paragraph()
            dinh_dang(p, WD_ALIGN_PARAGRAPH.LEFT, None, gian=1.3)
            p.paragraph_format.left_indent = Cm({1: 0, 2: 0.6, 3: 1.2}[cap])
            p.paragraph_format.tab_stops.add_tab_stop(Cm(RONG_TRANG), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            dat_font(p.add_run(chu), CO, cap == 1, cap == 3)
            dat_font(p.add_run(f"\t{self.so_trang.get(chu, '')}"), CO, cap == 1)

    # ---- phân đoạn, header, footer ----
    def phan_moi(self, kieu_so):
        sec = self.doc.add_section(WD_SECTION.NEW_PAGE)
        pg = sec._sectPr.find(qn("w:pgBorders"))
        if pg is not None:
            sec._sectPr.remove(pg)
        so = OxmlElement("w:pgNumType")
        so.set(qn("w:fmt"), kieu_so)
        so.set(qn("w:start"), "1")
        sec._sectPr.append(so)
        sec.header.is_linked_to_previous = False
        sec.footer.is_linked_to_previous = False
        h = sec.header.paragraphs[0]
        h.style = self.doc.styles["Normal"]
        dinh_dang(h, WD_ALIGN_PARAGRAPH.CENTER, None, gian=1.0)
        dat_font(h.add_run("Bài tập nhóm Đầu tư tài chính"), 11, nghieng=True)
        ft = sec.footer.paragraphs[0]
        ft.style = self.doc.styles["Normal"]  # kiểu Footer có sẵn tab giữa trang làm lệch số trang
        dinh_dang(ft, WD_ALIGN_PARAGRAPH.LEFT, None, gian=1.0)
        ft.paragraph_format.tab_stops.add_tab_stop(Cm(RONG_TRANG), WD_TAB_ALIGNMENT.RIGHT)
        dat_font(ft.add_run(f"{FOOTER_TRAI}\t"), 11)
        r = ft.add_run()
        truong_trang(r)
        dat_font(r, 11)


# ======================= Hình vẽ =======================

def ve_hinh():
    """Hình 2.1 (vùng giá hợp lý), Hình 3.1 (diễn biến giá), Hình 4.1 (đường biên theo tỷ trọng Excel Solver)."""
    HINH.mkdir(exist_ok=True)
    ve_vung_gia_hop_ly()
    g = pd.read_csv(DU_LIEU_GIA, parse_dates=["Ngay"]).set_index("Ngay").dropna(subset=["MBB", "MWG", "GAS"])
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "white", "axes.facecolor": "white"})
    mau = {"MBB": "#eb6834", "MWG": "#1baf7a", "GAS": "#eda100", "VNINDEX": "#52514e"}

    fig, ax = plt.subplots(figsize=(7.4, 3.3))
    ax.grid(axis="y", color="#e6e5e1")
    for ma in ("MBB", "MWG", "GAS", "VNINDEX"):
        chi_so = g[ma] / g[ma].iloc[0] * 100
        ax.plot(chi_so.index, chi_so, color=mau[ma], lw=1.6 if ma != "VNINDEX" else 1.3,
                ls="-" if ma != "VNINDEX" else "--", label=ma if ma != "VNINDEX" else "VN-Index")
        ax.annotate(f"{chi_so.iloc[-1]:.0f}", (chi_so.index[-1], chi_so.iloc[-1]), xytext=(4, -3),
                    textcoords="offset points", fontsize=8.5, color=mau[ma])
    ax.axhline(100, color="#8a8984", lw=0.8)
    ax.set_ylabel("Chỉ số giá (01/10/2025 = 100)")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%m/%Y"))
    ax.legend(frameon=False, ncol=4, fontsize=8.5, loc="upper left")
    fig.savefig(HINH / "hinh_3_1_dien_bien_gia.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    r = g[["MBB", "MWG", "GAS"]].pct_change().dropna()
    mu, S = r.mean().values * 250, r.cov().values * 250
    kq = json.loads(KET_QUA_SOLVER.read_text(encoding="utf-8"))
    W = [np.clip(d["w"], 0, None) for d in kq["duong_bien"]]
    E = [w @ mu for w in W]
    sd = [np.sqrt(w @ S @ w) for w in W]
    k = int(np.argmin(sd))
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    ax.grid(color="#e6e5e1")
    ax.set_axisbelow(True)
    ax.plot(sd[:k + 1], E[:k + 1], "--", color="#8a8984", lw=2, label="Phần không hiệu quả")
    ax.plot(sd[k:], E[k:], color="#2a78d6", lw=2.4, label="Đường biên hiệu quả")
    for i, ma in enumerate(("MBB", "MWG", "GAS")):
        ax.scatter(np.sqrt(S[i, i]), mu[i], s=60, marker="D", color=mau[ma], zorder=3)
        ax.annotate(ma, (np.sqrt(S[i, i]), mu[i]), xytext=(7, -3), textcoords="offset points", fontsize=9)
    for ten, w, m, mk in (("Danh mục phương sai nhỏ nhất", np.clip(kq["gmv"]["w"], 0, None), "#4a3aa7", "o"),
                          ("Danh mục được chọn", np.clip(kq["chon"]["w"], 0, None), "#e34948", "^"),
                          ("Tỷ trọng sơ bộ 40/35/25", np.array([0.4, 0.35, 0.25]), "#52514e", "s")):
        ax.scatter(np.sqrt(w @ S @ w), w @ mu, s=70, marker=mk, color=m, zorder=4, label=ten)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
    ax.set_xlabel("Độ lệch chuẩn σ_p (năm)".replace("σ_p", "σp"))
    ax.set_ylabel("Lợi nhuận kỳ vọng E(Rp) (năm)")
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    fig.savefig(HINH / "hinh_4_1_duong_bien.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def ve_vung_gia_hop_ly():
    """Giá 23/10/2026 so với vùng giá trị theo các phương pháp định giá ở mục 2.2.4, 2.3.4, 2.4.4."""
    co_phieu = [("MBB", 19_800, 24_500, 29_900, 25_000, "#eb6834"),   # P/B: thận trọng – cơ sở; chọn
                ("MWG", 75_500, 90_000, 109_000, 90_000, "#1baf7a"),  # P/E chuẩn 15 – giá mục tiêu cao nhất CTCK
                ("GAS", 78_300, 71_100, 87_300, 78_400, "#eda100")]   # DDM – bình quân CTCK; chọn = bình quân 2 cách
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.spines.left": False})
    fig, ax = plt.subplots(figsize=(7.2, 2.4))
    ax.grid(axis="x", color="#e6e5e1")
    ax.set_axisbelow(True)
    ax.axvline(0, color="#8a8984", lw=1.1, ls="--")
    ax.text(1, 2.45, "Giá 23/10/2026", color="#52514e", fontsize=9)
    for i, (ma, gia, thap, cao, chon, mau) in enumerate(reversed(co_phieu)):
        a, b, c = ((x / gia - 1) * 100 for x in (thap, cao, chon))
        ax.plot([a, b], [i, i], color=mau, lw=7, alpha=0.35, solid_capstyle="round")
        ax.scatter([c], [i], s=60, color=mau, edgecolor="white", linewidth=1.5, zorder=3)
        ax.text(b + 2, i, f"giá hợp lý {chon:,.0f} đ ({c:+.0f}%)".replace(",", "."), va="center", fontsize=9)
    ax.set_yticks(range(3))
    ax.set_yticklabels([c[0] for c in reversed(co_phieu)], fontweight="bold")
    ax.set_xlim(-15, 95)
    ax.set_ylim(-0.6, 2.8)
    ax.tick_params(length=0)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:+.0f}%")
    ax.set_xlabel("Chênh lệch so với giá đóng cửa ngày 23/10/2026")
    fig.savefig(HINH / "hinh_2_1_vung_gia_hop_ly.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    plt.rcParams.update({"axes.spines.left": True})


# ======================= Dựng tài liệu =======================

def dung(so_trang, de_muc_truoc):
    tt = TrinhTao(so_trang)
    tt.trang_bia()

    tt.phan_moi("lowerRoman")
    tt.hoat_dong()
    tt.ngat_trang()
    tt.muc_luc(de_muc_truoc)

    tt.phan_moi("decimal")
    for k in NOI_DUNG:
        loai = k[0]
        if loai == "phan":
            tt.tieu_de_phan(k[1], ngat_trang=len(k) > 2 and k[2])
        elif loai in ("h2", "h3"):
            tt.muc(k[1], 2 if loai == "h2" else 3)
        elif loai == "p":
            tt.doan(k[1])
        elif loai == "abc":
            tt.liet_ke(k[1])
        elif loai == "gach":
            tt.liet_ke(k[1], "gach")
        elif loai == "ct":
            tt.cong_thuc(k[1], k[2])
        elif loai == "bang":
            _, so, ten, hang, rong, can_phai, nguon = k
            tt.bang(so, ten, hang, rong, can_phai, nguon)
        elif loai == "hinh":
            _, so, ten, file, nguon = k
            tt.hinh(so, ten, HINH / file, nguon)
        elif loai == "ngat":
            tt.ngat_trang()

    tt.tieu_de_phan("TÀI LIỆU THAM KHẢO", ngat_trang=True)
    for i, tl in enumerate(TAI_LIEU, start=1):
        p = tt.doc.add_paragraph()
        dinh_dang(p, thut=Cm(-0.9), trai=Cm(0.9))
        p.paragraph_format.tab_stops.add_tab_stop(Cm(0.9))
        them_chu(p, f"[{i}]\t{tl}")
    return tt


def do_trang(docx, cac_chu):
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp, str(docx)],
                       check=True, capture_output=True)
        txt = subprocess.run(["pdftotext", "-layout", str(Path(tmp) / (docx.stem + ".pdf")), "-"],
                             check=True, capture_output=True, text=True).stdout
    chuan = lambda s: re.sub(r"\s+", " ", s).strip()  # noqa: E731
    trang = [chuan(t) for t in txt.split("\f")]
    bd = next(i for i, t in enumerate(trang) if "PHẦN 1." in t and "MỤC LỤC" not in t)
    tl = next(i for i, t in enumerate(trang) if i > bd and "TÀI LIỆU THAM KHẢO" in t)
    kq = {}
    for chu in cac_chu:
        for i in range(bd, len(trang)):
            if chuan(chu) in trang[i]:
                kq[chu] = str(i - bd + 1)
                break
    return kq, tl - bd  # số trang nội dung chính (không tính tài liệu tham khảo)


def main():
    ve_hinh()
    tt = dung({}, [])
    tt.doc.save(DICH)
    tt2 = dung({}, tt.de_muc)
    tt2.doc.save(DICH)
    so_trang, _ = do_trang(DICH, [c for _, c in tt.de_muc])
    tt3 = dung(so_trang, tt.de_muc)
    tt3.doc.save(DICH)
    _, so_trang_noi_dung = do_trang(DICH, [])
    print("Đã lưu", DICH)
    print("Số trang nội dung chính:", so_trang_noi_dung, "(tối đa 15)")
    thieu = [c for _, c in tt.de_muc if c not in so_trang]
    if thieu:
        print("Chưa tìm được số trang:", thieu)


if __name__ == "__main__":
    main()
