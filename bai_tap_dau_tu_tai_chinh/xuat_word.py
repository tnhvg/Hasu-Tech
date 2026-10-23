"""Xuất báo cáo Markdown sang Word (.docx) theo định dạng nộp bài: A4, Times New Roman.

Chạy: python bai_tap_dau_tu_tai_chinh/xuat_word.py
Cần pandoc. Bước 1: pandoc chuyển Markdown sang .docx. Bước 2: python-docx chỉnh font, lề, bảng.
"""

import subprocess
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

THU_MUC = Path(__file__).parent
NGUON = THU_MUC / "bai_tap_tinh_huong_1.md"
DICH = THU_MUC / "bai_tap_tinh_huong_1.docx"
FONT = "Times New Roman"


def dat_font(run, co_chu: float) -> None:
    run.font.name = FONT
    run.font.size = Pt(co_chu)
    run.font.color.rgb = RGBColor(0, 0, 0)
    # Font cho ký tự tiếng Việt (East Asian / complex script) cũng phải đặt riêng
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for thuoc_tinh in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(thuoc_tinh), FONT)


def ke_vien_bang(bang) -> None:
    tbl_pr = bang._tbl.tblPr
    vien = OxmlElement("w:tblBorders")
    for canh in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{canh}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:color"), "808080")
        vien.append(e)
    tbl_pr.append(vien)


def chia_do_rong_cot(bang, tong_rong_cm: float = 16.5) -> None:
    """Pandoc chia đều độ rộng cột nên cột nhiều chữ bị xuống dòng liên tục.
    Ở đây chia lại theo độ dài chữ trung bình của từng cột (có sàn và trần)."""
    so_cot = len(bang.columns)
    do_dai = [0.0] * so_cot
    for hang in bang.rows:
        for j, o in enumerate(hang.cells[:so_cot]):
            do_dai[j] += len(o.text) ** 0.8
    tong = sum(do_dai) or 1
    # Độ rộng tối thiểu của cột đủ chứa từ dài nhất (để "Ngân hàng" không bị ngắt giữa chữ),
    # phần còn lại chia theo độ dài chữ
    tu_dai_nhat = [max((len(t) for o in bang.columns[j].cells for t in o.text.split()), default=1)
                   for j in range(so_cot)]
    toi_thieu = [min(2.2, max(0.9, 0.24 * n + 0.4)) for n in tu_dai_nhat]
    con_lai = tong_rong_cm - sum(toi_thieu)
    rong = [Cm(toi_thieu[j] + con_lai * do_dai[j] / tong) for j in range(so_cot)]

    tbl_pr = bang._tbl.tblPr
    for cu in tbl_pr.findall(qn("w:tblW")) + tbl_pr.findall(qn("w:tblLayout")):
        tbl_pr.remove(cu)
    tbl_w = OxmlElement("w:tblW")
    tbl_w.set(qn("w:w"), str(int(Cm(tong_rong_cm).twips)))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_pr.append(tbl_w)
    bo_cuc = OxmlElement("w:tblLayout")
    bo_cuc.set(qn("w:type"), "fixed")
    tbl_pr.append(bo_cuc)

    grid = bang._tbl.tblGrid
    for j, cot in enumerate(grid.findall(qn("w:gridCol"))):
        cot.set(qn("w:w"), str(int(rong[j].twips)))
    for hang in bang.rows:
        for j, o in enumerate(hang.cells[:so_cot]):
            o.width = rong[j]


def main() -> None:
    subprocess.run(
        ["pandoc", NGUON.name, "-o", DICH.name, "--resource-path", "."],
        cwd=THU_MUC, check=True,
    )
    doc = Document(DICH)
    for section in doc.sections:
        section.page_height, section.page_width = Cm(29.7), Cm(21.0)
        section.top_margin = section.bottom_margin = Cm(2)
        section.left_margin, section.right_margin = Cm(2.5), Cm(2)

    co_tieu_de = {"Title": 16, "Heading 1": 16, "Heading 2": 14, "Heading 3": 13}
    trong_muc_nguon = False  # danh mục nguồn cuối bài in cỡ nhỏ hơn cho gọn
    for p in doc.paragraphs:
        ten_style = p.style.name
        if ten_style.startswith("Heading"):
            trong_muc_nguon = p.text.strip() == "Nguồn số liệu"
        co = co_tieu_de.get(ten_style, 10 if trong_muc_nguon else 12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        if ten_style.startswith("Heading") or ten_style == "Title":
            p.paragraph_format.space_before = Pt(8)
        for run in p.runs:
            dat_font(run, co)
            if ten_style.startswith("Heading") or ten_style == "Title":
                run.font.bold = True
        if ten_style == "Source Code":  # sơ đồ chuỗi logic vĩ mô → cổ phiếu
            for run in p.runs:
                run.font.name = "Courier New"
                run.font.size = Pt(8)

    for bang in doc.tables:
        bang.alignment = WD_TABLE_ALIGNMENT.CENTER
        ke_vien_bang(bang)
        chia_do_rong_cot(bang)
        for i, hang in enumerate(bang.rows):
            for o in hang.cells:
                for p in o.paragraphs:
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.line_spacing = 1.0
                    for run in p.runs:
                        dat_font(run, 10.5)
                        if i == 0:
                            run.font.bold = True

    for hinh in doc.inline_shapes:
        ty_le = Cm(13.5) / hinh.width
        hinh.width, hinh.height = Cm(13.5), int(hinh.height * ty_le)

    doc.save(DICH)
    print("Đã lưu", DICH)


if __name__ == "__main__":
    main()
