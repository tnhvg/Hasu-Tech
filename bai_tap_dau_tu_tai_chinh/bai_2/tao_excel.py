"""Bước 2 – Tạo file Excel Bài tập tình huống 2 từ dữ liệu giá đã tải (tai_du_lieu.py).

Chạy: python bai_tap_dau_tu_tai_chinh/bai_2/tao_excel.py
Mọi chỉ tiêu trong file là CÔNG THỨC Excel (không dán số tính sẵn), để giảng viên bấm vào ô nào
cũng thấy cách tính, và file tự tính lại nếu thay dữ liệu giá.

Các trang tính:
  Giới thiệu        – mục tiêu, nguồn dữ liệu, cách xử lý, chú thích màu
  Giá               – giá đóng cửa điều chỉnh hằng ngày (dữ liệu đầu vào)
  Lợi tức           – tỷ suất lợi tức ngày R = (P_t − P_{t−1}) / P_{t−1}
  Thống kê          – lợi tức kỳ vọng, độ lệch chuẩn, phương sai (theo ngày và theo năm)
  Hiệp phương sai   – ma trận hiệp phương sai và ma trận hệ số tương quan
"""

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

THU_MUC = Path(__file__).parent
NGUON = THU_MUC / "du_lieu" / "gia_dong_cua.csv"
DICH = THU_MUC / "Nhom7_FIN3002_2_BaiTapTinhHuong2.xlsx"

CO_PHIEU = ["MBB", "MWG", "GAS"]
CHI_SO = "VNINDEX"
TEN_DAY_DU = {"MBB": "Ngân hàng TMCP Quân đội", "MWG": "CTCP Đầu tư Thế Giới Di Động",
              "GAS": "Tổng Công ty Khí Việt Nam", "VNINDEX": "Chỉ số VN-Index"}

# Màu theo quy ước mô hình tài chính: xanh dương = số nhập tay, đen = công thức, xanh lá = liên kết trang khác
FONT = "Times New Roman"
XANH_DUONG, XANH_LA, DEN = "0000FF", "008000", "000000"
NEN_TIEU_DE = PatternFill("solid", fgColor="1F3864")
NEN_NHAT = PatternFill("solid", fgColor="D9E1F2")
NEN_GIA_DINH = PatternFill("solid", fgColor="FFFF00")
VIEN = Border(*(Side(style="thin", color="A6A6A6"),) * 4)

TRANG_GIA, TRANG_LT, TRANG_TK, TRANG_HPS = "Giá", "Lợi tức", "Thống kê", "Hiệp phương sai"


def f(mau=DEN, dam=False, co=12, nghieng=False):
    return Font(name=FONT, color=mau, bold=dam, size=co, italic=nghieng)


def tieu_de_cot(ws, hang, cac_tieu_de, cot_dau=1):
    for j, chu in enumerate(cac_tieu_de):
        o = ws.cell(hang, cot_dau + j, chu)
        o.font = Font(name=FONT, color="FFFFFF", bold=True, size=12)
        o.fill = NEN_TIEU_DE
        o.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        o.border = VIEN


def doc_gia():
    """Chỉ giữ những ngày cả 3 cổ phiếu đều có giá (CafeF thiếu 29–30/01/2026 cho cổ phiếu)."""
    with open(NGUON, encoding="utf-8-sig") as fh:
        hang = [d for d in csv.DictReader(fh) if all(d[ma] for ma in CO_PHIEU)]
    return [(d["Ngay"], *(float(d[ma]) for ma in CO_PHIEU + [CHI_SO])) for d in hang]


def trang_gioi_thieu(wb, so_phien):
    ws = wb.active
    ws.title = "Giới thiệu"
    dong = [
        ("BÀI TẬP TÌNH HUỐNG 2 – ƯỚC LƯỢNG LỢI TỨC, RỦI RO VÀ TƯƠNG QUAN", f(dam=True, co=14)),
        ("Học phần Đầu tư tài chính – Lớp FIN3002_2 – Nhóm 7", f(nghieng=True)),
        ("", None),
        ("1. Dữ liệu", f(dam=True)),
        ("• Cổ phiếu: MBB (ngân hàng), MWG (bán lẻ), GAS (khí đốt) – 3 mã đã chọn ở Bài tập tình huống 1. "
         "Thêm VN-Index để ước lượng hệ số β.", f()),
        (f"• Thời gian: 01/10/2025 – 30/09/2026, {so_phien} phiên giao dịch có đủ giá của cả 3 mã.", f()),
        ("• Nguồn: CafeF – Lịch sử giá (https://cafef.vn/du-lieu/lich-su-giao-dich-mbb-1.chn), "
         "cột \"Giá điều chỉnh\", tải ngày 31/10/2026 bằng file tai_du_lieu.py.", f()),
        ("• Dùng GIÁ ĐIỀU CHỈNH thay cho giá đóng cửa thô: ngày 11/08/2026 MBB giao dịch không hưởng quyền "
         "cổ tức 15% bằng cổ phiếu, giá thô giảm từ 24,25 xuống 20,35 (−16%) dù nhà đầu tư không bị lỗ. "
         "Giá điều chỉnh đã loại bỏ bước nhảy này.", f()),
        ("• CafeF không có giá của 3 cổ phiếu ngày 29/01 và 30/01/2026 (VN-Index có), nên hai ngày này bị loại; "
         "lợi tức ngày 02/02/2026 được tính so với giá ngày 28/01/2026.", f()),
        ("", None),
        ("2. Phương pháp (theo Chương 2 – Lý thuyết danh mục đầu tư)", f(dam=True)),
        ("• Tỷ suất lợi tức ngày: R_t = (P_t − P_{t−1}) / P_{t−1}  (trang Lợi tức).", f()),
        ("• Tỷ suất lợi tức kỳ vọng E(R) = trung bình cộng các R_t (AVERAGE).", f()),
        ("• Độ lệch chuẩn σ = độ lệch chuẩn mẫu của R_t (STDEV.S); phương sai σ² (VAR.S).", f()),
        ("• Hiệp phương sai Cov(R_i, R_j) (COVARIANCE.S) và hệ số tương quan ρ = Cov/(σ_i σ_j) (CORREL).", f()),
        ("• Quy đổi theo năm: E(R) năm = E(R) ngày × N;  σ năm = σ ngày × √N;  Cov năm = Cov ngày × N, "
         "với N = số phiên giao dịch một năm (ô giả định ở trang Thống kê).", f()),
        ("", None),
        ("3. Chú thích màu", f(dam=True)),
        ("Chữ xanh dương: số liệu nhập tay (giá tải về, giả định)", f(XANH_DUONG)),
        ("Chữ đen: công thức tính trong cùng trang", f()),
        ("Chữ xanh lá: liên kết lấy từ trang khác", f(XANH_LA)),
        ("Nền vàng: giả định quan trọng, có thể thay đổi", f()),
    ]
    for i, (chu, phong) in enumerate(dong, start=1):
        o = ws.cell(i, 1, chu)
        if phong:
            o.font = phong
        o.alignment = Alignment(wrap_text=True, vertical="top")
    ws.cell(len(dong), 1).fill = NEN_GIA_DINH
    ws.column_dimensions["A"].width = 120


def trang_gia(wb, gia):
    ws = wb.create_sheet(TRANG_GIA)
    ws["A1"] = "GIÁ ĐÓNG CỬA ĐIỀU CHỈNH HẰNG NGÀY (cổ phiếu: nghìn đồng; VN-Index: điểm)"
    ws["A1"].font = f(dam=True, co=13)
    ws["A2"] = "Nguồn: CafeF, cột \"Giá điều chỉnh\", 01/10/2025 – 30/09/2026."
    ws["A2"].font = f(nghieng=True, co=11)
    tieu_de_cot(ws, 3, ["Ngày"] + CO_PHIEU + [CHI_SO])
    for i, (ngay, *cac_gia) in enumerate(gia, start=4):
        o = ws.cell(i, 1, ngay)
        o.font, o.alignment = f(XANH_DUONG), Alignment(horizontal="center")
        for j, p in enumerate(cac_gia, start=2):
            o = ws.cell(i, j, p)
            o.font = f(XANH_DUONG)
            o.number_format = "#,##0.00"
    for cot, rong in zip("ABCDE", (14, 12, 12, 12, 13)):
        ws.column_dimensions[cot].width = rong
    ws.freeze_panes = "B4"
    return 4, 3 + len(gia)  # dòng đầu, dòng cuối có dữ liệu


def trang_loi_tuc(wb, dau, cuoi):
    ws = wb.create_sheet(TRANG_LT)
    ws["A1"] = "TỶ SUẤT LỢI TỨC HẰNG NGÀY: R_t = (P_t − P_{t−1}) / P_{t−1}"
    ws["A1"].font = f(dam=True, co=13)
    ws["A2"] = "Mỗi ô lấy giá ngày hôm đó và giá phiên liền trước ở trang Giá. Phiên đầu tiên (01/10/2025) không có lợi tức."
    ws["A2"].font = f(nghieng=True, co=11)
    tieu_de_cot(ws, 3, ["Ngày"] + CO_PHIEU + [CHI_SO])
    tg = f"'{TRANG_GIA}'"
    for i, dong_gia in enumerate(range(dau + 1, cuoi + 1), start=4):
        o = ws.cell(i, 1, f"={tg}!A{dong_gia}")
        o.font, o.alignment = f(XANH_LA), Alignment(horizontal="center")
        for j in range(2, 3 + len(CO_PHIEU)):
            c = get_column_letter(j)
            o = ws.cell(i, j, f"=({tg}!{c}{dong_gia}-{tg}!{c}{dong_gia - 1})/{tg}!{c}{dong_gia - 1}")
            o.font, o.number_format = f(), "0.00%"
    for cot, rong in zip("ABCDE", (14, 12, 12, 12, 13)):
        ws.column_dimensions[cot].width = rong
    ws.freeze_panes = "B4"
    return 4, 3 + (cuoi - dau)


def vung(cot, dau, cuoi):
    return f"'{TRANG_LT}'!${cot}${dau}:${cot}${cuoi}"


def trang_thong_ke(wb, dau, cuoi, dau_gia, cuoi_gia):
    ws = wb.create_sheet(TRANG_TK)
    ws["A1"] = "THỐNG KÊ TỶ SUẤT LỢI TỨC CỦA TỪNG CỔ PHIẾU"
    ws["A1"].font = f(dam=True, co=13)

    ws["A3"] = "Số phiên giao dịch một năm (N)"
    ws["A3"].font = f(dam=True)
    ws["B3"] = 250
    ws["B3"].font, ws["B3"].fill = f(XANH_DUONG, dam=True), NEN_GIA_DINH
    ws["B3"].comment = Comment("Giả định của nhóm: HOSE giao dịch khoảng 250 phiên mỗi năm. "
                               "Dùng để quy đổi chỉ tiêu ngày sang năm.", "Nhóm 7")
    ws["C3"] = "← giả định, dùng để quy đổi theo năm"
    ws["C3"].font = f(nghieng=True, co=11)

    tieu_de_cot(ws, 5, ["Chỉ tiêu"] + CO_PHIEU + [CHI_SO, "Công thức (ví dụ cột MBB)"])
    tg = f"'{TRANG_GIA}'"
    cac_chi_tieu = [
        ("Số quan sát (số ngày có lợi tức)", "=COUNT({v})", "0"),
        ("Tỷ suất lợi tức kỳ vọng E(R) – ngày", "=AVERAGE({v})", "0.000%"),
        ("Độ lệch chuẩn σ – ngày", "=_xlfn.STDEV.S({v})", "0.000%"),
        ("Phương sai σ² – ngày", "=_xlfn.VAR.S({v})", "0.000000"),
        ("Tỷ suất lợi tức kỳ vọng E(R) – năm", "={c}7*$B$3", "0.00%"),
        ("Độ lệch chuẩn σ – năm", "={c}8*SQRT($B$3)", "0.00%"),
        ("Hệ số biến thiên CV = σ / E(R) (năm)", "=IF({c}10=0,\"-\",{c}11/{c}10)", "0.00"),
        ("Lợi tức thấp nhất trong một ngày", "=MIN({v})", "0.00%"),
        ("Lợi tức cao nhất trong một ngày", "=MAX({v})", "0.00%"),
        ("Tỷ suất lợi tức cả kỳ (giá cuối / giá đầu − 1)", "={tg}!{c}" + str(cuoi_gia) + "/{tg}!{c}"
         + str(dau_gia) + "-1", "0.00%"),
        ("Hệ số β so với VN-Index = Cov(R_i, R_M) / σ²_M", "=_xlfn.COVARIANCE.S({v},{vm})/_xlfn.VAR.S({vm})",
         "0.000"),
    ]
    for i, (ten, mau_ct, dinh_dang) in enumerate(cac_chi_tieu, start=6):
        o = ws.cell(i, 1, ten)
        o.font, o.border = f(dam=True), VIEN
        for j in range(2, 3 + len(CO_PHIEU)):
            c = get_column_letter(j)
            ct = mau_ct.format(v=vung(c, dau, cuoi), vm=vung("E", dau, cuoi), c=c, tg=tg)
            o = ws.cell(i, j, ct)
            o.font = f(XANH_LA if "{tg}" in mau_ct else DEN)
            o.number_format, o.border = dinh_dang, VIEN
            o.alignment = Alignment(horizontal="right")
        vi_du = ws.cell(i, 2).value
        o = ws.cell(i, 7, vi_du.replace("_xlfn.", ""))
        o.data_type = "s"  # chỉ hiển thị công thức dạng chữ, không tính
        o.font = f(co=10, nghieng=True, mau="595959")
    ws.cell(16, 5).value = None  # β của VN-Index với chính nó = 1, không cần hiển thị
    ws.cell(16, 5, 1).font = f()
    ws.cell(16, 5).border = VIEN

    ghi_chu = [
        "Ghi chú:",
        "• E(R) và σ được ước lượng từ dữ liệu quá khứ của 1 năm, là đầu vào cho đường biên hiệu quả (Chương 2).",
        "• Hệ số β đo rủi ro hệ thống (Chương 3), dùng để thay các β giả định ở Bài tập tình huống 1.",
        "• σ năm = σ ngày × √N vì phương sai cộng dồn theo thời gian khi lợi tức các ngày độc lập.",
    ]
    for k, chu in enumerate(ghi_chu, start=18):
        ws.cell(k, 1, chu).font = f(dam=k == 18, co=11, nghieng=k > 18)
    ws.column_dimensions["A"].width = 50
    for cot in "BCDE":
        ws.column_dimensions[cot].width = 13
    ws.column_dimensions["G"].width = 60


def ma_tran(ws, hang_dau, tieu_de, mau_ct, dinh_dang, dau, cuoi, ghi_chu):
    ws.cell(hang_dau, 1, tieu_de).font = f(dam=True, co=12)
    tieu_de_cot(ws, hang_dau + 1, [""] + CO_PHIEU)
    for i, ma_i in enumerate(CO_PHIEU):
        o = ws.cell(hang_dau + 2 + i, 1, ma_i)
        o.font, o.fill, o.border = f(dam=True), NEN_NHAT, VIEN
        o.alignment = Alignment(horizontal="center")
        ci = get_column_letter(2 + i)
        for j, _ in enumerate(CO_PHIEU):
            cj = get_column_letter(2 + j)
            o = ws.cell(hang_dau + 2 + i, 2 + j, mau_ct.format(vi=vung(ci, dau, cuoi), vj=vung(cj, dau, cuoi),
                                                              hang=hang_dau + 2 + i, cot=cj))
            o.font, o.number_format, o.border = f(), dinh_dang, VIEN
    ws.cell(hang_dau + 2 + len(CO_PHIEU), 1, ghi_chu).font = f(nghieng=True, co=10, mau="595959")
    return hang_dau + 2


def trang_hiep_phuong_sai(wb, dau, cuoi):
    ws = wb.create_sheet(TRANG_HPS)
    ws["A1"] = "HIỆP PHƯƠNG SAI VÀ HỆ SỐ TƯƠNG QUAN GIỮA CÁC CỔ PHIẾU"
    ws["A1"].font = f(dam=True, co=13)
    n = f"'{TRANG_TK}'!$B$3"

    hang_cov = ma_tran(ws, 3, "Bảng 1. Ma trận hiệp phương sai – theo ngày", "=_xlfn.COVARIANCE.S({vi},{vj})",
                       "0.000000", dau, cuoi,
                       "Công thức: =COVARIANCE.S(lợi tức mã hàng, lợi tức mã cột). Đường chéo chính = phương sai σ².")
    ma_tran(ws, 10, "Bảng 2. Ma trận hiệp phương sai – theo năm (× N)",
            "={cot}{{hang_ngay}}*" + n, "0.0000", dau, cuoi,
            "Công thức: Cov năm = Cov ngày × N (N ở trang Thống kê).")
    # Bảng 2 nhân từng ô của Bảng 1 với N: thay chỗ giữ {hang_ngay} bằng dòng tương ứng của Bảng 1
    for i in range(len(CO_PHIEU)):
        for j in range(len(CO_PHIEU)):
            o = ws.cell(12 + i, 2 + j)
            o.value = o.value.replace("{hang_ngay}", str(hang_cov + i))
    ma_tran(ws, 17, "Bảng 3. Ma trận hệ số tương quan ρ", "=CORREL({vi},{vj})", "0.000", dau, cuoi,
            "Công thức: =CORREL(lợi tức mã hàng, lợi tức mã cột). ρ nằm trong [−1; 1]; càng gần 0, đa dạng hóa càng hiệu quả.")

    # Kiểm tra chéo: ρ tính lại bằng Cov / (σ_i × σ_j) phải khớp CORREL
    ws.cell(24, 1, "Kiểm tra: ρ(MBB, MWG) tính bằng Cov / (σ_MBB × σ_MWG)").font = f(co=11)
    ws.cell(24, 3, f"=C5/('{TRANG_TK}'!B8*'{TRANG_TK}'!C8)").number_format = "0.000"
    ws.cell(24, 3).font = f()
    ws.cell(24, 4, "=IF(ABS(C24-C19)<0.000001,\"Khớp với CORREL\",\"Không khớp\")").font = f(co=11)

    ws.column_dimensions["A"].width = 16
    for cot in "BCD":
        ws.column_dimensions[cot].width = 14


def main():
    gia = doc_gia()
    wb = Workbook()
    trang_gioi_thieu(wb, len(gia))
    dau_gia, cuoi_gia = trang_gia(wb, gia)
    dau, cuoi = trang_loi_tuc(wb, dau_gia, cuoi_gia)
    trang_thong_ke(wb, dau, cuoi, dau_gia, cuoi_gia)
    trang_hiep_phuong_sai(wb, dau, cuoi)
    wb.save(DICH)
    print("Đã lưu", DICH, f"– {len(gia)} phiên giá, {cuoi - dau + 1} quan sát lợi tức")


if __name__ == "__main__":
    main()
