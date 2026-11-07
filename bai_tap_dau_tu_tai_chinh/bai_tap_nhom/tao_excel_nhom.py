"""Tạo file Excel nộp kèm Bài tập nhóm (gộp Bài tập tình huống 2 và 3).

Chạy: python bai_tap_dau_tu_tai_chinh/bai_tap_nhom/tao_excel_nhom.py

Khác với bai_3/tao_excel_bai3.py: tỷ trọng ở các trang Solver và bảng Đường biên lấy từ kết quả
Excel Solver nhóm đã chạy (du_lieu/ket_qua_excel_solver.json, trích từ file Excel sau khi chạy
macro chay_solver.bas), không phải số giải bằng Python. Thứ tự trang 1–10 giữ nguyên như Bài 3
để macro chay_solver.bas vẫn chạy được trên file này; trang biểu đồ giá đặt ở cuối.
"""

import json
import sys
from pathlib import Path

import numpy as np
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Alignment

THU_MUC = Path(__file__).parent
sys.path.insert(0, str(THU_MUC.parent / "bai_3"))
sys.path.insert(0, str(THU_MUC.parent / "bai_2"))
import tao_excel_bai3 as b3  # noqa: E402
from tao_excel import CO_PHIEU, CHI_SO, NEN_GIA_DINH, XANH_DUONG, XANH_LA, f, tieu_de_cot  # noqa: E402

DICH = THU_MUC / "Nhom7_FIN3002_2_BaiTapNhom.xlsx"
KET_QUA_SOLVER = THU_MUC / "du_lieu" / "ket_qua_excel_solver.json"


def lam_sach(w):
    """Solver dừng khi sai số đủ nhỏ nên có thể để lại tỷ trọng âm cỡ 10⁻⁷; đưa về 0."""
    return np.array([max(float(x), 0.0) for x in w])


def trang_gioi_thieu(wb, so_phien):
    ws = wb.active
    ws.title = "Giới thiệu"
    dong = [
        ("BÀI TẬP NHÓM ĐẦU TƯ TÀI CHÍNH – NHÓM 7 – LỚP FIN3002_2", f(dam=True, co=14)),
        ("Xây dựng danh mục đầu tư cổ phiếu 10 tỷ đồng, kỳ hạn 1 tháng: MBB, MWG, GAS", f(nghieng=True)),
        ("", None),
        ("1. Các trang tính và phần tương ứng trong báo cáo", f(dam=True)),
        ("• Giá, Lợi tức, Thống kê, Hiệp phương sai → Phần 3 (Phân tích rủi ro và lợi nhuận).", f()),
        ("• Solver 1, Solver 2, Solver 3, Đường biên, Danh mục chọn → Phần 4 (Xây dựng danh mục đầu tư).", f()),
        ("• Biểu đồ giá → Hình 3.1 trong báo cáo.", f()),
        ("", None),
        ("2. Dữ liệu", f(dam=True)),
        (f"• Giá đóng cửa ĐIỀU CHỈNH hằng ngày 01/10/2025 – 30/09/2026 từ CafeF (cafef.vn, Lịch sử giá), {so_phien} "
         "phiên có đủ giá của cả 3 mã. Giá điều chỉnh loại bỏ bước nhảy giá do chia cổ tức (ví dụ MBB ngày 11/08/2026).", f()),
        ("• CafeF không có giá 3 cổ phiếu ngày 29–30/01/2026 nên hai ngày này bị loại; lợi tức ngày 02/02/2026 gộp 3 phiên.", f()),
        ("", None),
        ("3. Phương pháp", f(dam=True)),
        ("• R_t = (P_t − P_{t−1})/P_{t−1};  E(R) = AVERAGE;  σ = STDEV.S;  Cov = COVARIANCE.S;  ρ = CORREL;  "
         "quy đổi năm: E × N, σ × √N, Cov × N với N = 250 phiên.", f()),
        ("• Danh mục: E(Rp) = Σ wᵢE(Rᵢ);  σ²p = Σᵢ Σⱼ wᵢwⱼCov(Rᵢ,Rⱼ). Không bán khống: wᵢ ≥ 0, Σwᵢ = 1.", f()),
        ("• Solver (GRG Nonlinear) giải 3 bài toán: Min σ²p (danh mục phương sai nhỏ nhất); Min σ²p với E(Rp) = mục tiêu "
         "(từng điểm đường biên); Max E(Rp) với σp ≤ 25% (danh mục được chọn).", f()),
        ("• 26 điểm đường biên được giải bằng macro VBA gọi Excel Solver (file chay_solver.bas nộp kèm); cột Kiểm chứng "
         "ở trang Đường biên ghi mã kết quả của Solver. Kết quả được đối chiếu với một thuật toán tối ưu độc lập "
         "(Python, scipy): độ lệch chuẩn chênh không quá 0,00002%.", f()),
        ("• Tỷ trọng âm cỡ 10⁻⁷ do sai số dừng của Solver được làm tròn về 0.", f()),
        ("", None),
        ("4. Chú thích màu", f(dam=True)),
        ("Chữ xanh dương: số liệu nhập tay / kết quả Solver", f(XANH_DUONG)),
        ("Chữ đen: công thức tính", f()),
        ("Chữ xanh lá: liên kết lấy từ trang khác", f(XANH_LA)),
        ("Nền vàng: ô thay đổi của Solver hoặc giả định quan trọng", f()),
    ]
    for i, (chu, phong) in enumerate(dong, start=1):
        o = ws.cell(i, 1, chu)
        if phong:
            o.font = phong
        o.alignment = Alignment(wrap_text=True, vertical="top")
    ws.cell(len(dong), 1).fill = NEN_GIA_DINH
    ws.column_dimensions["A"].width = 125


def trang_bieu_do_gia(wb, dau_gia, cuoi_gia):
    """Giá điều chỉnh quy về 100 tại ngày 01/10/2025 để so sánh diễn biến 3 mã và VN-Index."""
    ws = wb.create_sheet("Biểu đồ giá")
    ws["A1"] = "DIỄN BIẾN GIÁ ĐIỀU CHỈNH, QUY VỀ 100 TẠI NGÀY 01/10/2025"
    ws["A1"].font = f(dam=True, co=13)
    ws["A2"] = "Chỉ số = Giá ngày t / Giá ngày 01/10/2025 × 100 (lấy từ trang Giá)."
    ws["A2"].font = f(nghieng=True, co=11)
    tieu_de_cot(ws, 3, ["Ngày"] + CO_PHIEU + [CHI_SO])
    for k, dong in enumerate(range(dau_gia, cuoi_gia + 1)):
        d = 4 + k
        ws[f"A{d}"] = f"='Giá'!A{dong}"
        ws[f"A{d}"].font = f(XANH_LA)
        for c in "BCDE":
            ws[f"{c}{d}"] = f"='Giá'!{c}{dong}/'Giá'!{c}${dau_gia}*100"
            ws[f"{c}{d}"].number_format = "0.0"
    cuoi = 3 + (cuoi_gia - dau_gia + 1)
    ch = LineChart()
    ch.title = "Diễn biến giá điều chỉnh (01/10/2025 = 100)"
    ch.y_axis.title, ch.x_axis.title = "Chỉ số giá", "Ngày"
    ch.x_axis.delete = ch.y_axis.delete = False
    ch.x_axis.tickLblSkip, ch.x_axis.number_format = 21, "dd/mm/yy"
    ch.height, ch.width = 10, 20
    ch.add_data(Reference(ws, min_col=2, max_col=5, min_row=3, max_row=cuoi), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=4, max_row=cuoi))
    for s, mau in zip(ch.series, ("EB6834", "1BAF7A", "EDA100", "52514E")):
        s.graphicalProperties.line.solidFill = mau
        s.graphicalProperties.line.width = 19000
        s.smooth = False
    ws.add_chart(ch, "G3")
    ws.column_dimensions["A"].width = 12
    ws.freeze_panes = "B4"


def main():
    kq = json.loads(KET_QUA_SOLVER.read_text(encoding="utf-8"))
    gia = b3.b2.doc_gia()
    mu, _ = b3.uoc_luong(gia)
    w_gmv, w_chon = lam_sach(kq["gmv"]["w"]), lam_sach(kq["chon"]["w"])
    cac_diem = [(d["muc_tieu"], lam_sach(d["w"])) for d in kq["duong_bien"]]
    sigma = [np.sqrt(w @ b3.uoc_luong(gia)[1] @ w) for _, w in cac_diem]
    dong_gmv = int(np.argmin(sigma))

    wb = Workbook()
    trang_gioi_thieu(wb, len(gia))
    dau_gia, cuoi_gia = b3.b2.trang_gia(wb, gia)
    dau, cuoi = b3.b2.trang_loi_tuc(wb, dau_gia, cuoi_gia)
    b3.b2.trang_thong_ke(wb, dau, cuoi, dau_gia, cuoi_gia)
    b3.b2.trang_hiep_phuong_sai(wb, dau, cuoi)
    b3.trang_solver(wb, "Solver 1 - PSNN", "gmv", w_gmv, None)
    b3.trang_solver(wb, "Solver 2 - Đường biên", "bien", lam_sach(kq["bien_mau"]["w"]), kq["bien_mau"]["B20"])
    b3.trang_solver(wb, "Solver 3 - DM chọn", "chon", w_chon, None)
    cot_dau_mut = ("BCD"[int(np.argmin(mu))], "BCD"[int(np.argmax(mu))])
    ws_bien, dau_b, cuoi_b = b3.trang_duong_bien(wb, cac_diem, dong_gmv, cot_dau_mut)
    for k, d in enumerate(kq["duong_bien"]):
        o = ws_bien.cell(dau_b + k, 10, d["kiem_chung"])
        o.font, o.border = f(co=11), b3.VIEN
    ws_chon = b3.trang_danh_muc_chon(wb, b3.TY_TRONG_BAI_1)
    b3.them_do_thi(ws_bien, dau_b, cuoi_b, dau_b + dong_gmv, ws_chon)
    trang_bieu_do_gia(wb, dau_gia, cuoi_gia)
    wb.save(DICH)
    print("Đã lưu", DICH)


if __name__ == "__main__":
    main()
