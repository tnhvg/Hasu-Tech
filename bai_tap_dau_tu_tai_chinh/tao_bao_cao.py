"""Tạo file Word Bài tập tình huống 1 theo khuôn báo cáo của trường (bìa, mục lục, danh mục,
Times New Roman 13, giãn dòng 1,5, thụt đầu dòng, đánh số mục 1.1 / 1.1.1).

Chạy: python bai_tap_dau_tu_tai_chinh/tao_bao_cao.py
Cần LibreOffice (soffice) và pdftotext để tính số trang cho mục lục: script dựng file hai lần,
lần 1 để đo số trang của từng đề mục, lần 2 ghi số trang thật vào mục lục.
"""

import re
import subprocess
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from noi_dung import NOI_DUNG, THANH_VIEN, CHU_VIET_TAT, TAI_LIEU

THU_MUC = Path(__file__).parent
DICH = THU_MUC / "Nhom7_FIN3002_2_BaiTapTinhHuong1.docx"
FONT = "Times New Roman"
THUT_DONG = Cm(1.27)


# ---------- Định dạng chữ ----------

def dat_font(run, co=13, dam=False, nghieng=False):
    run.font.name = FONT
    run.font.size = Pt(co)
    run.font.bold = dam
    run.font.italic = nghieng
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for k in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(k), FONT)


def them_chu(p, van_ban, co=13, dam=False, nghieng=False):
    """Thêm chữ có đánh dấu **đậm** và *nghiêng* kiểu Markdown."""
    for manh in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", van_ban):
        if not manh:
            continue
        if manh.startswith("**"):
            dat_font(p.add_run(manh[2:-2]), co, True, nghieng)
        elif manh.startswith("*"):
            dat_font(p.add_run(manh[1:-1]), co, dam, True)
        else:
            dat_font(p.add_run(manh), co, dam, nghieng)


def dinh_dang_doan(p, can=WD_ALIGN_PARAGRAPH.JUSTIFY, thut=THUT_DONG, gian=1.3, sau=6, truoc=0):
    f = p.paragraph_format
    f.alignment = can
    f.first_line_indent = thut
    f.line_spacing = gian
    f.space_after = Pt(sau)
    f.space_before = Pt(truoc)


def dat_do_rong_bang(t, do_rong_cm):
    """Khai báo độ rộng ở cả bảng, lưới cột và từng ô; thiếu một trong ba thì Word/LibreOffice
    tự co bảng lại."""
    tbl_pr = t._tbl.tblPr
    for cu in tbl_pr.findall(qn("w:tblW")) + tbl_pr.findall(qn("w:tblLayout")):
        tbl_pr.remove(cu)
    tbl_w = OxmlElement("w:tblW")
    tbl_w.set(qn("w:w"), str(int(Cm(sum(do_rong_cm)).twips)))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_pr.append(tbl_w)
    bo_cuc = OxmlElement("w:tblLayout")
    bo_cuc.set(qn("w:type"), "fixed")
    tbl_pr.append(bo_cuc)
    for j, cot in enumerate(t._tbl.tblGrid.findall(qn("w:gridCol"))):
        cot.set(qn("w:w"), str(int(Cm(do_rong_cm[j]).twips)))
    for hang in t.rows:
        for j, o in enumerate(hang.cells):
            o.width = Cm(do_rong_cm[j])


# ---------- Các khối nội dung ----------

class TrinhTao:
    def __init__(self, so_trang=None):
        self.doc = Document()
        self.so_trang = so_trang or {}
        self.de_muc = []      # (cấp, chữ) để làm mục lục
        self.ds_bang = []
        self.ds_hinh = []
        self._dinh_dang_chung()

    def _dinh_dang_chung(self):
        st = self.doc.styles["Normal"]
        st.font.name = FONT
        st.font.size = Pt(13)
        st.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
        for ten, co in (("Heading 1", 14), ("Heading 2", 13), ("Heading 3", 13)):
            s = self.doc.styles[ten]
            s.font.name, s.font.size, s.font.bold = FONT, Pt(co), True
            s.font.color.rgb = None
            s.font.italic = ten == "Heading 3"
            rpr = s.element.get_or_add_rPr()
            rpr.get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
            rpr.get_or_add_rFonts().set(qn("w:ascii"), FONT)
            rpr.get_or_add_rFonts().set(qn("w:hAnsi"), FONT)
        sec = self.doc.sections[0]
        sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
        sec.top_margin, sec.bottom_margin = Cm(2), Cm(2)
        sec.left_margin, sec.right_margin = Cm(3), Cm(2)

    # Đoạn văn thường, có thụt đầu dòng
    def doan(self, van_ban, thut=THUT_DONG, can=WD_ALIGN_PARAGRAPH.JUSTIFY, co=13, dam=False,
             nghieng=False, sau=6):
        p = self.doc.add_paragraph()
        dinh_dang_doan(p, can=can, thut=thut, sau=sau)
        them_chu(p, van_ban, co, dam, nghieng)
        return p

    # Danh sách a) b) c) thụt lề treo
    def liet_ke(self, cac_y, kieu="abc"):
        for i, y in enumerate(cac_y):
            nhan = f"{'abcdefghij'[i]})" if kieu == "abc" else "•"
            p = self.doc.add_paragraph()
            dinh_dang_doan(p, thut=Cm(-0.63), sau=3)
            p.paragraph_format.left_indent = Cm(1.27 + 0.63)
            p.paragraph_format.tab_stops.add_tab_stop(Cm(1.27 + 0.63))
            them_chu(p, f"{nhan}\t{y}")

    def tieu_de_trang(self, chu, dua_vao_muc_luc=True):
        """Tiêu đề in hoa căn giữa (MỤC LỤC, TÓM TẮT, PHẦN 1...)."""
        p = self.doc.add_paragraph(style="Heading 1")
        dinh_dang_doan(p, can=WD_ALIGN_PARAGRAPH.CENTER, thut=None, sau=12)
        p.paragraph_format.keep_with_next = True
        dat_font(p.add_run(chu), 14, True)
        if dua_vao_muc_luc:
            self.de_muc.append((1, chu))

    def muc(self, chu, cap):
        p = self.doc.add_paragraph(style=f"Heading {cap}")
        dinh_dang_doan(p, can=WD_ALIGN_PARAGRAPH.LEFT, thut=None, sau=6, truoc=6)
        p.paragraph_format.keep_with_next = True
        dat_font(p.add_run(chu), 13, True, cap == 3)
        self.de_muc.append((cap, chu))

    def bang(self, ten, tieu_de, hang, nguon, do_rong, can_phai=(), ghi_chu=None):
        so = f"Bảng {ten}"
        self.ds_bang.append(f"{so}. {tieu_de}")
        p = self.doc.add_paragraph()
        dinh_dang_doan(p, can=WD_ALIGN_PARAGRAPH.LEFT, thut=None, sau=3, truoc=6)
        p.paragraph_format.keep_with_next = True
        dat_font(p.add_run(f"{so}. {tieu_de}"), 13, True)

        # hang[0] là dòng tiêu đề cột
        t = self.doc.add_table(rows=len(hang), cols=len(do_rong))
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        self._vien_ba_duong(t)
        self._dien_bang(t, hang, do_rong, can_phai, nguon, ghi_chu)

    def _dien_bang(self, t, hang, do_rong, can_phai, nguon, ghi_chu):
        for i, dong in enumerate(hang):
            for j, gia_tri in enumerate(dong):
                o = t.cell(i, j)
                o.width = Cm(do_rong[j])
                p = o.paragraphs[0]
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.space_before = Pt(1)
                if i == 0:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    them_chu(p, gia_tri, 11, dam=True)
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if j in can_phai else WD_ALIGN_PARAGRAPH.LEFT
                    them_chu(p, gia_tri, 11)
        # Hàng tiêu đề lặp lại khi bảng sang trang
        tr_pr = t.rows[0]._tr.get_or_add_trPr()
        lap = OxmlElement("w:tblHeader")
        lap.set(qn("w:val"), "true")
        tr_pr.append(lap)
        dat_do_rong_bang(t, do_rong)
        if ghi_chu:
            p = self.doc.add_paragraph()
            dinh_dang_doan(p, thut=None, sau=0, gian=1.15)
            them_chu(p, f"Ghi chú: {ghi_chu}", 11)
        p = self.doc.add_paragraph()
        dinh_dang_doan(p, can=WD_ALIGN_PARAGRAPH.LEFT, thut=None, sau=8, gian=1.15)
        them_chu(p, f"*Nguồn:* {nguon}", 11)

    @staticmethod
    def _vien_ba_duong(t):
        """Kiểu bảng ba đường như file mẫu: viền trên, dưới tiêu đề, viền dưới."""
        tbl_pr = t._tbl.tblPr
        vien = OxmlElement("w:tblBorders")
        for canh in ("top", "bottom"):
            e = OxmlElement(f"w:{canh}")
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), "8")
            e.set(qn("w:color"), "000000")
            vien.append(e)
        e = OxmlElement("w:insideH")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "2")
        e.set(qn("w:color"), "BFBFBF")
        vien.append(e)
        tbl_pr.append(vien)

    def ke_duoi_tieu_de_bang(self):
        t = self.doc.tables[-1]
        for o in t.rows[0].cells:
            tc_pr = o._tc.get_or_add_tcPr()
            vien = OxmlElement("w:tcBorders")
            e = OxmlElement("w:bottom")
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), "6")
            e.set(qn("w:color"), "000000")
            vien.append(e)
            tc_pr.append(vien)

    def hinh(self, ten, tieu_de, duong_dan, nguon, rong_cm=11.5):
        p = self.doc.add_paragraph()
        dinh_dang_doan(p, can=WD_ALIGN_PARAGRAPH.CENTER, thut=None, sau=2, truoc=6)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(duong_dan), width=Cm(rong_cm))
        so = f"Hình {ten}"
        self.ds_hinh.append(f"{so}. {tieu_de}")
        p = self.doc.add_paragraph()
        dinh_dang_doan(p, can=WD_ALIGN_PARAGRAPH.CENTER, thut=None, sau=0, gian=1.15)
        p.paragraph_format.keep_with_next = True
        dat_font(p.add_run(f"{so}. {tieu_de}"), 13, True, True)
        p = self.doc.add_paragraph()
        dinh_dang_doan(p, can=WD_ALIGN_PARAGRAPH.CENTER, thut=None, sau=8, gian=1.15)
        them_chu(p, f"*Nguồn: {nguon}*", 11)

    def ngat_trang(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------- Trang bìa ----------

    def trang_bia(self):
        sec = self.doc.sections[0]
        pg = OxmlElement("w:pgBorders")
        pg.set(qn("w:offsetFrom"), "page")
        for canh in ("top", "left", "bottom", "right"):
            e = OxmlElement(f"w:{canh}")
            e.set(qn("w:val"), "thinThickSmallGap")
            e.set(qn("w:sz"), "24")
            e.set(qn("w:space"), "24")
            e.set(qn("w:color"), "1F3864")
            pg.append(e)
        sec._sectPr.append(pg)

        def dong(chu, co=14, dam=True, sau=0, truoc=0, nghieng=False):
            p = self.doc.add_paragraph()
            dinh_dang_doan(p, can=WD_ALIGN_PARAGRAPH.CENTER, thut=None, gian=1.15, sau=sau, truoc=truoc)
            dat_font(p.add_run(chu), co, dam, nghieng)

        dong("ĐẠI HỌC ĐÀ NẴNG", 14, False, truoc=6)
        dong("TRƯỜNG ĐẠI HỌC KINH TẾ", 14)
        dong("KHOA TÀI CHÍNH", 14)
        dong("----------✦✦✦----------", 12, False, sau=60)
        dong("BÁO CÁO BÀI TẬP TÌNH HUỐNG 1", 20, sau=12)
        dong("Đề tài:", 14, sau=4)
        dong("PHÂN TÍCH BỐI CẢNH ĐẦU TƯ VÀ LỰA CHỌN CỔ PHIẾU", 16)
        dong("CHO DANH MỤC ĐẦU TƯ 10 TỶ ĐỒNG", 16, sau=40)

        for nhan, gia_tri in (("Học phần", "ĐẦU TƯ TÀI CHÍNH"), ("Lớp học phần", "FIN3002_2"),
                              ("Giảng viên hướng dẫn", "......................................"),
                              ("Nhóm thực hiện", "Nhóm 7")):
            p = self.doc.add_paragraph()
            dinh_dang_doan(p, can=WD_ALIGN_PARAGRAPH.LEFT, thut=None, gian=1.3, sau=0)
            p.paragraph_format.left_indent = Cm(2)
            p.paragraph_format.tab_stops.add_tab_stop(Cm(7.5))
            dat_font(p.add_run(nhan), 13, True)
            dat_font(p.add_run(f"\t: {gia_tri}"), 13)

        p = self.doc.add_paragraph()
        dinh_dang_doan(p, can=WD_ALIGN_PARAGRAPH.LEFT, thut=None, gian=1.3, sau=4, truoc=10)
        p.paragraph_format.left_indent = Cm(2)
        dat_font(p.add_run("Thành viên nhóm:"), 13, True)

        t = self.doc.add_table(rows=len(THANH_VIEN) + 1, cols=3)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.style = "Table Grid"
        for j, (chu, rong) in enumerate((("STT", 1.5), ("Họ và tên", 7.0), ("Lớp sinh hoạt", 3.5))):
            o = t.cell(0, j)
            o.width = Cm(rong)
            o.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            dat_font(o.paragraphs[0].add_run(chu), 13, True)
        for i, (lop, ten) in enumerate(THANH_VIEN, start=1):
            for j, (chu, rong) in enumerate(((str(i), 1.5), (ten, 7.0), (lop, 3.5))):
                o = t.cell(i, j)
                o.width = Cm(rong)
                o.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 1 else WD_ALIGN_PARAGRAPH.CENTER
                dat_font(o.paragraphs[0].add_run(chu), 13)
        dat_do_rong_bang(t, [1.5, 7.0, 3.5])

        dong("Đà Nẵng, tháng 10 năm 2026", 13, truoc=60)

    # ---------- Phần đầu: mục lục, danh mục ----------

    def _dong_muc_luc(self, chu, trang, thut_cm=0.0, dam=False, nghieng=False):
        p = self.doc.add_paragraph()
        dinh_dang_doan(p, can=WD_ALIGN_PARAGRAPH.LEFT, thut=None, gian=1.3, sau=0)
        p.paragraph_format.left_indent = Cm(thut_cm)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(16), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        dat_font(p.add_run(chu), 13, dam, nghieng)
        dat_font(p.add_run(f"\t{trang}"), 13, dam)

    def muc_luc(self, de_muc):
        self.tieu_de_trang("MỤC LỤC", dua_vao_muc_luc=False)
        for cap, chu in de_muc:
            trang = self.so_trang.get(chu, "")
            self._dong_muc_luc(chu, trang, thut_cm={1: 0, 2: 0.6, 3: 1.2}[cap],
                               dam=cap == 1, nghieng=cap == 3)

    def danh_muc(self, tieu_de, cac_muc):
        self.tieu_de_trang(tieu_de)
        for chu in cac_muc:
            self._dong_muc_luc(chu, self.so_trang.get(chu, ""))

    def chu_viet_tat(self):
        self.tieu_de_trang("DANH MỤC CÁC KÝ HIỆU, CHỮ VIẾT TẮT")
        hang = [("Chữ viết tắt", "Nguyên nghĩa")] + CHU_VIET_TAT
        t = self.doc.add_table(rows=len(hang), cols=2)
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, dong in enumerate(hang):
            for j, chu in enumerate(dong):
                o = t.cell(i, j)
                o.width = Cm((3.5, 12.0)[j])
                p = o.paragraphs[0]
                p.paragraph_format.line_spacing = 1.0
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT
                dat_font(p.add_run(chu), 12, i == 0)
        dat_do_rong_bang(t, [3.5, 12.5])

    # ---------- Phân trang, đánh số trang ----------

    def chuyen_phan(self, kieu_so):
        sec = self.doc.add_section(WD_SECTION.NEW_PAGE)
        pg = sec._sectPr.find(qn("w:pgBorders"))
        if pg is not None:
            sec._sectPr.remove(pg)
        so = OxmlElement("w:pgNumType")
        so.set(qn("w:fmt"), kieu_so)
        so.set(qn("w:start"), "1")
        sec._sectPr.append(so)
        sec.footer.is_linked_to_previous = False
        p = sec.footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        for loai, chu in (("begin", None), (None, "PAGE"), ("end", None)):
            if loai:
                e = OxmlElement("w:fldChar")
                e.set(qn("w:fldCharType"), loai)
            else:
                e = OxmlElement("w:instrText")
                e.set(qn("xml:space"), "preserve")
                e.text = chu
            run._r.append(e)
        dat_font(run, 12)
        return sec


def dung_tai_lieu(so_trang=None, de_muc_truoc=None, bang_truoc=None, hinh_truoc=None):
    tt = TrinhTao(so_trang)
    tt.trang_bia()

    # Phần đầu (đánh số i, ii, iii...)
    tt.chuyen_phan("lowerRoman")
    tt.tieu_de_trang("TÓM TẮT")
    for y in NOI_DUNG["tom_tat"]:
        tt.doan(y)
    tt.ngat_trang()
    tt.muc_luc(de_muc_truoc or [])
    tt.ngat_trang()
    tt.danh_muc("DANH MỤC CÁC BẢNG BIỂU", bang_truoc or [])
    tt.doc.add_paragraph()
    tt.danh_muc("DANH MỤC CÁC HÌNH VẼ, ĐỒ THỊ", hinh_truoc or [])
    tt.ngat_trang()
    tt.chu_viet_tat()

    # Phần nội dung (đánh số 1, 2, 3...)
    tt.chuyen_phan("decimal")
    for khoi in NOI_DUNG["than_bai"]:
        loai = khoi[0]
        if loai == "phan":
            tt.tieu_de_trang(khoi[1])
        elif loai == "ngat":
            tt.ngat_trang()
        elif loai in ("h2", "h3"):
            tt.muc(khoi[1], 2 if loai == "h2" else 3)
        elif loai == "p":
            tt.doan(khoi[1])
        elif loai == "abc":
            tt.liet_ke(khoi[1])
        elif loai == "bang":
            _, ten, tieu_de, hang, nguon, do_rong, can_phai, ghi_chu = khoi
            tt.bang(ten, tieu_de, hang, nguon, do_rong, can_phai, ghi_chu)
            tt.ke_duoi_tieu_de_bang()
        elif loai == "hinh":
            _, ten, tieu_de, file, nguon = khoi
            tt.hinh(ten, tieu_de, THU_MUC / file, nguon)

    tt.ngat_trang()
    tt.tieu_de_trang("TÀI LIỆU THAM KHẢO")
    for i, tl in enumerate(TAI_LIEU, start=1):
        p = tt.doc.add_paragraph()
        dinh_dang_doan(p, thut=Cm(-1.0), gian=1.15, sau=4)
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(1.0))
        them_chu(p, f"[{i}]\t{tl}", 12)
    return tt


def do_so_trang(duong_dan_docx, cac_chu):
    """Chuyển .docx sang PDF và tìm trang (đánh số trong phần đó) chứa từng đề mục."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", tmp,
                        str(duong_dan_docx)], check=True, capture_output=True)
        pdf = Path(tmp) / (duong_dan_docx.stem + ".pdf")
        van_ban = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True,
                                 capture_output=True, text=True).stdout
    trang = van_ban.split("\f")
    chuan = lambda s: re.sub(r"\s+", " ", s).strip()  # noqa: E731
    trang = [chuan(t) for t in trang]
    # Trang 1 là bìa. Phần đầu bắt đầu ở trang 2 (i); phần nội dung bắt đầu ở trang có "PHẦN 1."
    bat_dau_noi_dung = next(i for i, t in enumerate(trang) if t.startswith("PHẦN 1."))
    ket_qua = {}
    so_la_ma = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
    for chu in cac_chu:
        mau = chuan(chu)
        tim_tu = bat_dau_noi_dung if not chu.startswith(("TÓM TẮT", "DANH MỤC")) else 1
        for i in range(tim_tu, len(trang)):
            if mau in trang[i]:
                ket_qua[chu] = (str(i - bat_dau_noi_dung + 1) if i >= bat_dau_noi_dung
                                else so_la_ma[i - 1])
                break
    return ket_qua, len(trang) - bat_dau_noi_dung


def main():
    tt = dung_tai_lieu()
    tt.doc.save(DICH)
    # Lần 2: dựng lại với mục lục, danh mục có đủ dòng; lần 3: điền số trang (số dòng mục lục
    # ảnh hưởng tới vị trí trang, nên đo sau khi mục lục đã đủ dòng).
    tt2 = dung_tai_lieu({}, tt.de_muc, tt.ds_bang, tt.ds_hinh)
    tt2.doc.save(DICH)
    so_trang, _ = do_so_trang(DICH, [c for _, c in tt.de_muc] + tt.ds_bang + tt.ds_hinh)
    tt3 = dung_tai_lieu(so_trang, tt.de_muc, tt.ds_bang, tt.ds_hinh)
    tt3.doc.save(DICH)
    _, so_trang_noi_dung = do_so_trang(DICH, [])
    print("Đã lưu", DICH)
    print("Số trang từ PHẦN 1 tới hết (gồm tài liệu tham khảo):", so_trang_noi_dung)
    thieu = [c for _, c in tt.de_muc if c not in so_trang]
    if thieu:
        print("Chưa tìm được số trang cho:", thieu)


if __name__ == "__main__":
    main()
