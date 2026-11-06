"""Tạo file Excel Bài tập tình huống 3: đường biên phương sai bé nhất, đường biên hiệu quả và danh
mục được chọn, giải bằng Solver.

Chạy: python bai_tap_dau_tu_tai_chinh/bai_3/tao_excel_bai3.py   (cần openpyxl, numpy, scipy)

Các trang tính:
  Giới thiệu           – bài toán, cách dùng Solver, chú thích màu
  Giá, Lợi tức,
  Thống kê,
  Hiệp phương sai      – dựng lại y hệt Bài tập tình huống 2 (dùng chung code bai_2/tao_excel.py)
  Solver 1 - PSNN      – danh mục phương sai nhỏ nhất (GMV): min σ², Σw = 1, w ≥ 0
  Solver 2 - Đường biên– min σ² với E(Rp) = mức mục tiêu: chạy cho từng mức để vẽ đường biên
  Solver 3 - DM chọn   – max E(Rp) với σp ≤ mức rủi ro chấp nhận
  Đường biên           – bảng các điểm trên đường biên phương sai bé nhất và đồ thị
  Danh mục chọn        – so sánh các danh mục, phân bổ 10 tỷ đồng thành số cổ phiếu

Tỷ trọng ở các trang Solver và bảng Đường biên được giải sẵn bằng scipy (cùng bài toán, cùng ràng
buộc với Solver) để file có kết quả ngay khi mở. Nhóm kiểm chứng bằng cách chạy lại Solver trong Excel.
Excel lưu cài đặt Solver dưới dạng các tên (defined name) solver_* gắn với từng trang, nên khi mở
Data → Solver, ô mục tiêu, ô thay đổi và ràng buộc đã được điền sẵn.
"""

import sys
from pathlib import Path

import numpy as np
from openpyxl import Workbook
from openpyxl.chart import Reference, ScatterChart, Series
from openpyxl.comments import Comment
from openpyxl.styles import Alignment
from openpyxl.workbook.defined_name import DefinedName
from scipy.optimize import minimize

THU_MUC = Path(__file__).parent
sys.path.insert(0, str(THU_MUC.parent / "bai_2"))
import tao_excel as b2  # noqa: E402  (dùng lại trang Giá, Lợi tức, Thống kê, Hiệp phương sai)

from tao_excel import (CO_PHIEU, DEN, NEN_GIA_DINH, NEN_NHAT, VIEN, XANH_DUONG, XANH_LA,  # noqa: E402
                       f, tieu_de_cot)

DICH = THU_MUC / "Nhom7_FIN3002_2_BaiTapTinhHuong3.xlsx"

# ---- Giả định (đều hiển thị trong file, chữ xanh dương nền vàng) ----
RF = 0.0436          # lãi suất phi rủi ro: lợi suất TPCP 10 năm, đấu thầu cuối 7/2026 (như Bài 1)
SIGMA_CHAP_NHAN = 0.25  # mức rủi ro chấp nhận tối đa của nhóm (σ năm)
VON = 10_000_000_000   # vốn đầu tư 10 tỷ đồng
GIA_MUA = {"MBB": 19.80, "MWG": 75.50, "GAS": 78.30}  # giá đóng cửa thô 23/10/2026, nghìn đồng (CafeF)
TY_TRONG_BAI_1 = [0.40, 0.35, 0.25]
SO_DIEM = 25           # số mức lợi nhuận mục tiêu trên đường biên

# Vị trí các ô trong file Bài 2 (xem bai_2/tao_excel.py)
TK, HPS = "'Thống kê'", "'Hiệp phương sai'"
O_E_NAM, O_SIGMA_NAM = "{c}10", "{c}11"   # trang Thống kê, cột B..D
COV_NAM_DONG_DAU = 12                     # trang Hiệp phương sai, B12:D14


# ---------------- Tính trước bằng scipy (cùng bài toán với Solver) ----------------

def uoc_luong(gia):
    p = np.array([[g[1], g[2], g[3]] for g in gia])
    r = p[1:] / p[:-1] - 1
    n = 250
    return r.mean(axis=0) * n, np.cov(r, rowvar=False, ddof=1) * n


def giai(mu, S, muc_tieu_E=None, sigma_max=None):
    rang_buoc = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    if muc_tieu_E is not None:
        rang_buoc.append({"type": "eq", "fun": lambda w: w @ mu - muc_tieu_E})
    if sigma_max is not None:
        rang_buoc.append({"type": "ineq", "fun": lambda w: sigma_max**2 - w @ S @ w})
        ham = lambda w: -(w @ mu)  # noqa: E731
    else:
        ham = lambda w: w @ S @ w  # noqa: E731
    kq = minimize(ham, np.ones(3) / 3, bounds=[(0, 1)] * 3, constraints=rang_buoc,
                  method="SLSQP", options={"ftol": 1e-14, "maxiter": 500})
    w = np.clip(kq.x, 0, None)
    return w / w.sum()


# ---------------- Trang Giới thiệu ----------------

def trang_gioi_thieu(wb, so_phien):
    ws = wb.active
    ws.title = "Giới thiệu"
    dong = [
        ("BÀI TẬP TÌNH HUỐNG 3 – ĐƯỜNG BIÊN HIỆU QUẢ VÀ LỰA CHỌN DANH MỤC (SOLVER)", f(dam=True, co=14)),
        ("Học phần Đầu tư tài chính – Lớp FIN3002_2 – Nhóm 7", f(nghieng=True)),
        ("", None),
        ("1. Đầu vào", f(dam=True)),
        (f"• Lợi tức kỳ vọng và ma trận hiệp phương sai (theo năm) của MBB, MWG, GAS ước lượng từ {so_phien} "
         "phiên giá điều chỉnh 01/10/2025 – 30/09/2026 (các trang Giá → Hiệp phương sai, giống Bài tập 2).", f()),
        ("• Không bán khống (thị trường Việt Nam không cho phép): tỷ trọng mỗi cổ phiếu w ≥ 0, tổng tỷ trọng = 1.", f()),
        ("", None),
        ("2. Ba mô hình Solver (Chương 2 – mô hình Markowitz)", f(dam=True)),
        ("• Solver 1 – Danh mục phương sai nhỏ nhất: Min σ²p, ràng buộc Σw = 1, w ≥ 0.", f()),
        ("• Solver 2 – Đường biên phương sai bé nhất: Min σ²p, ràng buộc Σw = 1, E(Rp) = mức mục tiêu, w ≥ 0. "
         "Chạy cho từng mức mục tiêu trong bảng Đường biên.", f()),
        ("• Solver 3 – Danh mục được chọn: Max E(Rp), ràng buộc Σw = 1, σp ≤ mức rủi ro chấp nhận, w ≥ 0.", f()),
        ("• Công thức danh mục: E(Rp) = Σ wᵢE(Rᵢ);  σ²p = Σᵢ Σⱼ wᵢwⱼCov(Rᵢ,Rⱼ);  Sharpe = (E(Rp) − Rf)/σp.", f()),
        ("", None),
        ("3. Cách tự chạy lại Solver trong Excel", f(dam=True)),
        ("• Bật Solver: File → Options → Add-ins → Manage: Excel Add-ins → Go → tích Solver Add-in → OK.", f()),
        ("• Mở trang Solver cần chạy, đặt 3 ô tỷ trọng (B5:D5) về 0,3333 để bắt đầu lại từ đầu.", f()),
        ("• Data → Solver: cài đặt đã được điền sẵn (nếu trống, nhập theo hướng dẫn ở cuối mỗi trang Solver). "
         "Chọn phương pháp GRG Nonlinear, tích \"Make Unconstrained Variables Non-Negative\" → Solve → Keep Solver Solution.", f()),
        ("• Trang Đường biên: lần lượt nhập từng mức E(Rp) mục tiêu vào ô B20 trang Solver 2, Solve, rồi chép "
         "3 tỷ trọng vào dòng tương ứng.", f()),
        ("• Tỷ trọng đang có trong file đã được giải sẵn bằng Python (scipy, cùng bài toán và ràng buộc) để kiểm tra "
         "chéo; kết quả Solver có thể lệch ở chữ số thập phân thứ 4 do sai số dừng của thuật toán.", f()),
        ("", None),
        ("4. Chú thích màu", f(dam=True)),
        ("Chữ xanh dương: số liệu nhập tay / kết quả đã giải", f(XANH_DUONG)),
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


# ---------------- Trang Solver ----------------

def o_gia_dinh(o, gia_tri, dinh_dang, ghi_chu=None):
    o.value = gia_tri
    o.font, o.fill, o.number_format, o.border = f(XANH_DUONG, dam=True), NEN_GIA_DINH, dinh_dang, VIEN
    if ghi_chu:
        o.comment = Comment(ghi_chu, "Nhóm 7")


def nhan(ws, o, chu, dam=True):
    ws[o] = chu
    ws[o].font, ws[o].border = f(dam=dam), VIEN


def ten_solver(ws, cai_dat):
    """Lưu cài đặt Solver vào workbook theo cách Excel lưu (tên cục bộ của trang)."""
    mac_dinh = {"solver_ver": "3", "solver_eng": "1", "solver_neg": "1", "solver_val": "0", "solver_lin": "2",
                "solver_cvg": "0.0001", "solver_drv": "1", "solver_est": "1", "solver_itr": "2147483647",
                "solver_pre": "0.000001", "solver_scl": "1", "solver_sho": "2", "solver_tim": "2147483647",
                "solver_tol": "0.01", "solver_rlx": "2", "solver_ssz": "100", "solver_msl": "2", "solver_nwt": "1",
                "solver_rbv": "1", "solver_mip": "2147483647", "solver_nod": "2147483647", "solver_rsd": "0",
                "solver_mrt": "0.075", "solver_mni": "30", "solver_rsm": "2", "solver_seed": "0"}
    mac_dinh.update(cai_dat)
    for ten, gia_tri in mac_dinh.items():
        ws.defined_names[ten] = DefinedName(ten, attr_text=gia_tri, hidden=True)


def trang_solver(wb, ten, kieu, w_san, mu_tham_so):
    """kieu: 'gmv' (Solver 1), 'bien' (Solver 2), 'chon' (Solver 3)."""
    ws = wb.create_sheet(ten)
    tieu_de = {"gmv": "SOLVER 1 – DANH MỤC PHƯƠNG SAI NHỎ NHẤT (GMV)",
               "bien": "SOLVER 2 – MỘT ĐIỂM TRÊN ĐƯỜNG BIÊN PHƯƠNG SAI BÉ NHẤT",
               "chon": "SOLVER 3 – DANH MỤC CÓ LỢI NHUẬN CAO NHẤT VỚI MỨC RỦI RO CHẤP NHẬN"}[kieu]
    bai_toan = {"gmv": "Min σ²p (ô B16)  |  Ràng buộc: Σw = 1 (ô E5 = 1), w ≥ 0",
                "bien": "Min σ²p (ô B16)  |  Ràng buộc: Σw = 1 (E5 = 1), E(Rp) = mục tiêu (B15 = B20), w ≥ 0",
                "chon": "Max E(Rp) (ô B15)  |  Ràng buộc: Σw = 1 (E5 = 1), σp ≤ mức chấp nhận (B17 ≤ B20), w ≥ 0"}[kieu]
    ws["A1"], ws["A2"] = tieu_de, "Bài toán: " + bai_toan
    ws["A1"].font, ws["A2"].font = f(dam=True, co=13), f(nghieng=True, co=11)

    tieu_de_cot(ws, 4, ["Chỉ tiêu"] + CO_PHIEU + ["Tổng"])
    nhan(ws, "A5", "Tỷ trọng w (ô thay đổi của Solver)")
    for j, c in enumerate("BCD"):
        o_gia_dinh(ws[f"{c}5"], float(round(w_san[j], 6)), "0.00%")
    ws["E5"] = "=SUM(B5:D5)"
    ws["E5"].font, ws["E5"].number_format, ws["E5"].border = f(dam=True), "0.00%", VIEN
    nhan(ws, "A6", "Lợi tức kỳ vọng E(R) – năm")
    nhan(ws, "A7", "Độ lệch chuẩn σ – năm")
    for c in "BCD":
        for dong, mau in ((6, O_E_NAM), (7, O_SIGMA_NAM)):
            o = ws[f"{c}{dong}"]
            o.value = f"={TK}!" + mau.format(c=c)
            o.font, o.number_format, o.border = f(XANH_LA), "0.00%", VIEN

    ws["A9"] = "Ma trận hiệp phương sai – năm (lấy từ trang Hiệp phương sai)"
    ws["A9"].font = f(dam=True, co=11)
    for i, ma in enumerate(CO_PHIEU):
        nhan(ws, f"A{10 + i}", ma)
        ws[f"A{10 + i}"].fill = NEN_NHAT
        for j, c in enumerate("BCD"):
            o = ws[f"{c}{10 + i}"]
            o.value = f"={HPS}!{c}{COV_NAM_DONG_DAU + i}"
            o.font, o.number_format, o.border = f(XANH_LA), "0.0000", VIEN
    nhan(ws, "A13", "Cov × w  (hàng i = Σⱼ Cov(i,j)·wⱼ)")
    for i, c in enumerate("BCD"):
        o = ws[f"{c}13"]
        o.value = f"=SUMPRODUCT($B${10 + i}:$D${10 + i},$B$5:$D$5)"
        o.font, o.number_format, o.border = f(), "0.000000", VIEN

    ket_qua = [
        (15, "Lợi nhuận kỳ vọng danh mục E(Rp)", "=SUMPRODUCT(B5:D5,B6:D6)", "0.00%"),
        (16, "Phương sai danh mục σ²p", "=SUMPRODUCT(B5:D5,B13:D13)", "0.000000"),
        (17, "Độ lệch chuẩn danh mục σp", "=SQRT(B16)", "0.00%"),
        (19, "Hệ số Sharpe = (E(Rp) − Rf)/σp", "=(B15-B18)/B17", "0.000"),
    ]
    for dong, chu, ct, dd in ket_qua:
        nhan(ws, f"A{dong}", chu)
        ws[f"B{dong}"] = ct
        ws[f"B{dong}"].font, ws[f"B{dong}"].number_format, ws[f"B{dong}"].border = f(dam=True), dd, VIEN
    nhan(ws, "A18", "Lãi suất phi rủi ro Rf")
    o_gia_dinh(ws["B18"], RF, "0.00%", "Lợi suất trúng thầu trái phiếu Chính phủ kỳ hạn 10 năm, phiên cuối "
               "tháng 7/2026 (Tạp chí Kinh tế Tài chính) – cùng giả định với Bài tập tình huống 1.")
    if kieu == "bien":
        nhan(ws, "A20", "Lợi nhuận kỳ vọng mục tiêu (nhập từng mức)")
        o_gia_dinh(ws["B20"], float(round(mu_tham_so, 6)), "0.00%", "Lấy từng mức ở cột B trang Đường biên.")
    elif kieu == "chon":
        nhan(ws, "A20", "Mức rủi ro chấp nhận tối đa σmax (năm)")
        o_gia_dinh(ws["B20"], SIGMA_CHAP_NHAN, "0.00%", "Giả định của nhóm, giải thích ở trang Danh mục chọn.")

    huong_dan = ["Cài đặt Solver (Data → Solver) – nếu hộp thoại chưa có sẵn thì nhập như sau:",
                 {"gmv": "• Set Objective: $B$16    • To: Min",
                  "bien": "• Set Objective: $B$16    • To: Min",
                  "chon": "• Set Objective: $B$15    • To: Max"}[kieu],
                 "• By Changing Variable Cells: $B$5:$D$5",
                 "• Subject to the Constraints: $E$5 = 1"
                 + {"gmv": "", "bien": "  và  $B$15 = $B$20", "chon": "  và  $B$17 <= $B$20"}[kieu],
                 "• Tích \"Make Unconstrained Variables Non-Negative\" (w ≥ 0, không bán khống)",
                 "• Select a Solving Method: GRG Nonlinear → Solve → Keep Solver Solution"]
    for k, chu in enumerate(huong_dan, start=22):
        ws[f"A{k}"] = chu
        ws[f"A{k}"].font = f(dam=k == 22, co=11)

    cai_dat = {"solver_adj": f"'{ten}'!$B$5:$D$5", "solver_lhs1": f"'{ten}'!$E$5", "solver_rel1": "2",
               "solver_rhs1": "1"}
    if kieu == "gmv":
        cai_dat.update({"solver_opt": f"'{ten}'!$B$16", "solver_typ": "2", "solver_num": "1"})
    elif kieu == "bien":
        cai_dat.update({"solver_opt": f"'{ten}'!$B$16", "solver_typ": "2", "solver_num": "2",
                        "solver_lhs2": f"'{ten}'!$B$15", "solver_rel2": "2", "solver_rhs2": f"'{ten}'!$B$20"})
    else:
        cai_dat.update({"solver_opt": f"'{ten}'!$B$15", "solver_typ": "1", "solver_num": "2",
                        "solver_lhs2": f"'{ten}'!$B$17", "solver_rel2": "1", "solver_rhs2": f"'{ten}'!$B$20"})
    ten_solver(ws, cai_dat)

    ws.column_dimensions["A"].width = 44
    for c in "BCDE":
        ws.column_dimensions[c].width = 13


# ---------------- Trang Đường biên ----------------

def cong_thuc_E(dong, cot_w="C:E"):
    a, b = cot_w.split(":")
    return f"=SUMPRODUCT({a}{dong}:{b}{dong},{TK}!$B$10:$D$10)"


def cong_thuc_sigma(dong, cot_w="C:E"):
    a, b = cot_w.split(":")
    w = f"{a}{dong}:{b}{dong}"
    return f"=SQRT(SUMPRODUCT({w},MMULT({w},{HPS}!$B$12:$D$14)))"


def trang_duong_bien(wb, cac_diem, dong_gmv_trong_bang):
    ws = wb.create_sheet("Đường biên")
    ws["A1"] = "ĐƯỜNG BIÊN PHƯƠNG SAI BÉ NHẤT VÀ ĐƯỜNG BIÊN HIỆU QUẢ (không bán khống)"
    ws["A1"].font = f(dam=True, co=13)
    ws["A2"] = ("Mỗi dòng là một lần chạy Solver 2: với mức E(Rp) mục tiêu ở cột B, tìm tỷ trọng có σp nhỏ nhất. "
                "Cột G, H tính lại E(Rp) và σp từ tỷ trọng bằng công thức để kiểm tra.")
    ws["A2"].font = f(nghieng=True, co=11)
    tieu_de_cot(ws, 4, ["STT", "E(Rp) mục tiêu", "w MBB", "w MWG", "w GAS", "Tổng w", "E(Rp)", "σp", "Phần đường biên"])
    dau = 5
    for k, (muc_tieu, w) in enumerate(cac_diem):
        d = dau + k
        ws[f"A{d}"] = k + 1
        ws[f"B{d}"] = float(round(muc_tieu, 6))
        for j, c in enumerate("CDE"):
            ws[f"{c}{d}"] = float(round(w[j], 6))
        ws[f"F{d}"] = f"=SUM(C{d}:E{d})"
        ws[f"G{d}"] = cong_thuc_E(d)
        ws[f"H{d}"] = cong_thuc_sigma(d)
        ws[f"I{d}"] = f'=IF(G{d}>=$L$6-0.000001,"Hiệu quả","Không hiệu quả")'
        for c in "ABCDEFGHI":
            o = ws[f"{c}{d}"]
            o.border = VIEN
            o.font = f(XANH_DUONG) if c in "BCDE" else f()
            o.number_format = "0" if c == "A" else ("0.00%" if c != "I" else "General")
        if d == dau + dong_gmv_trong_bang:
            for c in "ABCDEFGHI":
                ws[f"{c}{d}"].fill = NEN_GIA_DINH
    cuoi = dau + len(cac_diem) - 1

    # Tóm tắt GMV tìm bằng công thức (σ nhỏ nhất trong bảng)
    ws["K4"], ws["K5"], ws["K6"], ws["K7"] = ("Danh mục phương sai nhỏ nhất (dòng tô vàng)", "σp nhỏ nhất",
                                              "E(Rp) tại σp nhỏ nhất", "Số điểm trên đường biên")
    ws["L5"] = f"=MIN(H{dau}:H{cuoi})"
    ws["L6"] = f"=INDEX(G{dau}:G{cuoi},MATCH(L5,H{dau}:H{cuoi},0))"
    ws["L7"] = f"=COUNTA(B{dau}:B{cuoi})"
    ws["K4"].font = f(dam=True)
    for o in ("K5", "K6", "K7"):
        ws[o].font, ws[o].border = f(), VIEN
    for o, dd in (("L5", "0.00%"), ("L6", "0.00%"), ("L7", "0")):
        ws[o].font, ws[o].number_format, ws[o].border = f(dam=True), dd, VIEN
    ws["K9"] = "Đọc đồ thị:"
    ws["K9"].font = f(dam=True, co=11)
    for k, chu in enumerate([
        "• Toàn bộ đường cong (cả nét liền và nét đứt) là đường biên phương sai bé nhất.",
        "• Nửa trên tính từ danh mục phương sai nhỏ nhất (nét liền) là đường biên hiệu quả.",
        "• Nửa dưới (nét đứt) không hiệu quả: cùng mức σ, nửa trên cho E(Rp) cao hơn.",
        "• Các chấm riêng: từng cổ phiếu, danh mục Bài 1 (40/35/25) và danh mục được chọn.",
    ], start=10):
        ws[f"K{k}"] = chu
        ws[f"K{k}"].font = f(co=11)

    ws.column_dimensions["A"].width = 6
    for c in "BCDEFGH":
        ws.column_dimensions[c].width = 11
    ws.column_dimensions["I"].width = 16
    ws.column_dimensions["K"].width = 36
    ws.column_dimensions["L"].width = 11
    ws.freeze_panes = "A5"
    return ws, dau, cuoi


def them_do_thi(ws_bien, dau, cuoi, dong_gmv, ws_chon):
    ch = ScatterChart()
    ch.title = "Đường biên phương sai bé nhất và đường biên hiệu quả (MBB, MWG, GAS)"
    ch.style = 13
    ch.x_axis.title = "Độ lệch chuẩn σp (năm)"
    ch.y_axis.title = "Lợi nhuận kỳ vọng E(Rp) (năm)"
    ch.x_axis.number_format = ch.y_axis.number_format = "0%"
    ch.x_axis.delete = ch.y_axis.delete = False
    ch.x_axis.scaling.min, ch.x_axis.scaling.max = 0.20, 0.55
    ch.height, ch.width = 11, 19
    ch.legend.position = "b"

    def them_duong(ten, d1, d2, mau, net_dut=False):
        s = Series(Reference(ws_bien, min_col=7, min_row=d1, max_row=d2),
                   Reference(ws_bien, min_col=8, min_row=d1, max_row=d2), title=ten)
        s.marker.symbol = "none"
        s.smooth = True
        s.graphicalProperties.line.solidFill = mau
        s.graphicalProperties.line.width = 28000
        if net_dut:
            s.graphicalProperties.line.dashStyle = "dash"
        ch.series.append(s)

    them_duong("Phần không hiệu quả", dau, dong_gmv, "8A8984", net_dut=True)
    them_duong("Đường biên hiệu quả", dong_gmv, cuoi, "2A78D6")

    def them_diem(ten, ws, o_x, o_y, mau, ky_hieu="circle", co=8):
        s = Series(Reference(ws, range_string=f"'{ws.title}'!{o_y}"),
                   Reference(ws, range_string=f"'{ws.title}'!{o_x}"), title=ten)
        s.marker.symbol, s.marker.size = ky_hieu, co
        s.marker.graphicalProperties.solidFill = mau
        s.marker.graphicalProperties.line.solidFill = mau
        s.graphicalProperties.line.noFill = True
        ch.series.append(s)

    tk = ws_bien.parent["Thống kê"]
    for ma, c, mau in (("MBB", "B", "EB6834"), ("MWG", "C", "1BAF7A"), ("GAS", "D", "EDA100")):
        them_diem(ma, tk, f"${c}$11", f"${c}$10", mau, "diamond", 9)
    them_diem("Danh mục phương sai nhỏ nhất", ws_chon, "$F$6", "$E$6", "4A3AA7", "circle", 9)
    them_diem("Danh mục được chọn", ws_chon, "$F$7", "$E$7", "E34948", "triangle", 10)
    them_diem("Danh mục Bài 1 (40/35/25)", ws_chon, "$F$9", "$E$9", "52514E", "square", 8)
    ws_bien.add_chart(ch, "K16")


# ---------------- Trang Danh mục chọn ----------------

def trang_danh_muc_chon(wb, w_bai1):
    ws = wb.create_sheet("Danh mục chọn")
    ws["A1"] = "SO SÁNH CÁC DANH MỤC VÀ LỰA CHỌN DANH MỤC ĐẦU TƯ"
    ws["A1"].font = f(dam=True, co=13)
    ws["A2"] = "Tỷ trọng của danh mục phương sai nhỏ nhất và danh mục được chọn lấy trực tiếp từ kết quả Solver 1 và Solver 3."
    ws["A2"].font = f(nghieng=True, co=11)
    tieu_de_cot(ws, 5, ["Danh mục", "w MBB", "w MWG", "w GAS", "E(Rp) năm", "σp năm", "Sharpe",
                        "E(Rp) tháng", "σp tháng"])
    cac_dm = [
        (6, "Phương sai nhỏ nhất (Solver 1)", "='Solver 1 - PSNN'!{c}5", XANH_LA),
        (7, "ĐƯỢC CHỌN: E(Rp) lớn nhất với σp ≤ 25% (Solver 3)", "='Solver 3 - DM chọn'!{c}5", XANH_LA),
        (8, "Toàn bộ vào GAS (Sharpe cao nhất)", None, XANH_DUONG),
        (9, "Tỷ trọng sơ bộ ở Bài tập 1 (40/35/25)", None, XANH_DUONG),
    ]
    rf = "'Solver 1 - PSNN'!$B$18"
    for dong, ten, lien_ket, mau in cac_dm:
        ws[f"A{dong}"] = ten
        ws[f"A{dong}"].font, ws[f"A{dong}"].border = f(dam=dong == 7), VIEN
        for j, c in enumerate("BCD"):
            if lien_ket:
                ws[f"{c}{dong}"] = lien_ket.format(c=c)
            else:
                ws[f"{c}{dong}"] = [0.0, 0.0, 1.0][j] if dong == 8 else w_bai1[j]
            ws[f"{c}{dong}"].font = f(mau)
        ws[f"E{dong}"] = cong_thuc_E(dong, "B:D")
        ws[f"F{dong}"] = cong_thuc_sigma(dong, "B:D")
        ws[f"G{dong}"] = f"=(E{dong}-{rf})/F{dong}"
        ws[f"H{dong}"] = f"=E{dong}/12"
        ws[f"I{dong}"] = f"=F{dong}/SQRT(12)"
        for c in "BCDEFGHI":
            o = ws[f"{c}{dong}"]
            o.number_format, o.border = ("0.000" if c == "G" else "0.00%"), VIEN
            if c in "EFGHI":
                o.font = f(dam=dong == 7)
        if dong == 7:
            for c in "ABCDEFGHI":
                ws[f"{c}{dong}"].fill = NEN_GIA_DINH

    ly_do = [
        "Lý do chọn danh mục (dòng tô vàng):",
        "• Nhóm theo chiến lược cân bằng (Bài 1) và chấp nhận rủi ro tối đa σp = 25%/năm, tức khoảng 7,2%/tháng – "
        "gần mức rủi ro của danh mục sơ bộ ở Bài 1 (25,6%).",
        "• Gần danh mục phương sai nhỏ nhất, đường biên rất \"dốc\": chỉ chấp nhận thêm khoảng 0,5 điểm % rủi ro so với "
        "danh mục phương sai nhỏ nhất, lợi nhuận kỳ vọng tăng khoảng 4,6 điểm % (từ 6,2% lên 10,8%).",
        "• Danh mục phương sai nhỏ nhất có E(Rp) chỉ 6,2%, gần bằng lãi suất phi rủi ro 4,36%: rủi ro thấp nhưng phần "
        "bù rủi ro quá mỏng.",
        "• Danh mục Sharpe cao nhất dồn 100% vào GAS: không đa dạng hóa, và E(R) 46% của GAS chủ yếu do cú sốc giá dầu "
        "trong 1 năm dữ liệu, khó lặp lại – nhóm không chọn.",
        "• Danh mục Bài 1 (40/35/25) nằm BÊN DƯỚI đường biên hiệu quả: cùng σ ≈ 25,6% có thể đạt E(Rp) ≈ 13%, "
        "nên nhóm thay tỷ trọng sơ bộ bằng tỷ trọng tối ưu.",
    ]
    for k, chu in enumerate(ly_do, start=11):
        ws[f"A{k}"] = chu
        ws[f"A{k}"].font = f(dam=k == 11, co=11)

    # Phân bổ vốn
    ws["A19"] = "PHÂN BỔ 10 TỶ ĐỒNG THEO DANH MỤC ĐƯỢC CHỌN (mua ngày 26/10/2026, lô chẵn 100 cổ phiếu)"
    ws["A19"].font = f(dam=True, co=12)
    nhan(ws, "A20", "Vốn đầu tư (đồng)")
    o_gia_dinh(ws["B20"], VON, "#,##0", "Vốn giả định theo đề bài.")
    tieu_de_cot(ws, 22, ["Cổ phiếu", "Tỷ trọng", "Số tiền phân bổ (đ)", "Giá 23/10/2026 (nghìn đ)",
                         "Số cổ phiếu mua", "Giá trị mua thực tế (đ)", "Tỷ trọng thực tế"])
    for i, ma in enumerate(CO_PHIEU):
        d = 23 + i
        c = "BCD"[i]
        ws[f"A{d}"] = ma
        ws[f"B{d}"] = f"={c}7"
        ws[f"C{d}"] = f"=B{d}*$B$20"
        o_gia_dinh(ws[f"D{d}"], GIA_MUA[ma], "#,##0.00", "Giá đóng cửa (thô) phiên 23/10/2026, CafeF.")
        ws[f"E{d}"] = f"=ROUNDDOWN(C{d}/(D{d}*1000)/100,0)*100"
        ws[f"F{d}"] = f"=E{d}*D{d}*1000"
        ws[f"G{d}"] = f"=F{d}/$B$20"
        for cc, dd in zip("ABCEFG", ("General", "0.00%", "#,##0", "#,##0", "#,##0", "0.00%")):
            o = ws[f"{cc}{d}"]
            o.number_format, o.border = dd, VIEN
            o.font = f(dam=cc == "A")
    ws["A26"], ws["C26"], ws["F26"], ws["G26"] = "Tổng", "=SUM(C23:C25)", "=SUM(F23:F25)", "=SUM(G23:G25)"
    nhan(ws, "A27", "Tiền mặt còn lại (do mua theo lô 100 cổ phiếu)")
    ws["F27"] = "=B20-F26"
    for o, dd in (("C26", "#,##0"), ("F26", "#,##0"), ("G26", "0.00%"), ("F27", "#,##0")):
        ws[o].number_format, ws[o].font, ws[o].border = dd, f(dam=True), VIEN
    ws["A26"].font = f(dam=True)

    ws.column_dimensions["A"].width = 58
    for c, rong in zip("BCDEFGHI", (17, 18, 14, 14, 18, 12, 11, 11)):
        ws.column_dimensions[c].width = rong
    return ws


def ve_png(cac_diem, dong_gmv, mu, S, w_chon):
    """Bản ảnh của đồ thị đường biên, dùng cho báo cáo Word (bảng màu giống các biểu đồ khác trong repo)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    E = [float(w @ mu) for _, w in cac_diem]
    sd = [float(np.sqrt(w @ S @ w)) for _, w in cac_diem]
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.grid(color="#e6e5e1", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.plot(sd[:dong_gmv + 1], E[:dong_gmv + 1], "--", color="#8a8984", lw=2, label="Phần không hiệu quả")
    ax.plot(sd[dong_gmv:], E[dong_gmv:], color="#2a78d6", lw=2.4, label="Đường biên hiệu quả")
    for i, (ma, mau) in enumerate(zip(CO_PHIEU, ("#eb6834", "#1baf7a", "#eda100"))):
        ax.scatter(np.sqrt(S[i, i]), mu[i], s=70, marker="D", color=mau, edgecolor="#fcfcfb", zorder=3)
        ax.annotate(ma, (np.sqrt(S[i, i]), mu[i]), xytext=(7, -3), textcoords="offset points", fontsize=9)
    w1 = np.array(TY_TRONG_BAI_1)
    for ten, w, mau, mk in (("Phương sai nhỏ nhất", cac_diem[dong_gmv][1], "#4a3aa7", "o"),
                            ("Danh mục được chọn", w_chon, "#e34948", "^"),
                            ("Danh mục Bài 1 (40/35/25)", w1, "#52514e", "s")):
        ax.scatter(np.sqrt(w @ S @ w), w @ mu, s=80, marker=mk, color=mau, edgecolor="#fcfcfb", zorder=4, label=ten)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
    ax.set_xlabel("Độ lệch chuẩn σp (năm)")
    ax.set_ylabel("Lợi nhuận kỳ vọng E(Rp) (năm)")
    ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    (THU_MUC / "figures").mkdir(exist_ok=True)
    fig.savefig(THU_MUC / "figures" / "duong_bien_hieu_qua.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def main():
    gia = b2.doc_gia()
    mu, S = uoc_luong(gia)

    w_gmv = giai(mu, S)
    e_gmv = float(w_gmv @ mu)
    w_chon = giai(mu, S, sigma_max=SIGMA_CHAP_NHAN)
    cac_muc = sorted(set(np.round(np.linspace(mu.min(), mu.max(), SO_DIEM), 6)) | {round(e_gmv, 6)})
    cac_diem = []
    for m in cac_muc:
        w = w_gmv if abs(m - e_gmv) < 1e-6 else giai(mu, S, muc_tieu_E=m)
        cac_diem.append((m, w))
    dong_gmv_trong_bang = [abs(m - e_gmv) < 1e-6 for m, _ in cac_diem].index(True)
    muc_mau = cac_diem[dong_gmv_trong_bang + 6][0]  # một điểm mẫu trên đường biên hiệu quả cho Solver 2

    wb = Workbook()
    trang_gioi_thieu(wb, len(gia))
    dau_gia, cuoi_gia = b2.trang_gia(wb, gia)
    dau, cuoi = b2.trang_loi_tuc(wb, dau_gia, cuoi_gia)
    b2.trang_thong_ke(wb, dau, cuoi, dau_gia, cuoi_gia)
    b2.trang_hiep_phuong_sai(wb, dau, cuoi)
    trang_solver(wb, "Solver 1 - PSNN", "gmv", w_gmv, None)
    trang_solver(wb, "Solver 2 - Đường biên", "bien",
                 cac_diem[dong_gmv_trong_bang + 6][1], muc_mau)
    trang_solver(wb, "Solver 3 - DM chọn", "chon", w_chon, None)
    ws_bien, dau_b, cuoi_b = trang_duong_bien(wb, cac_diem, dong_gmv_trong_bang)
    ws_chon = trang_danh_muc_chon(wb, TY_TRONG_BAI_1)
    them_do_thi(ws_bien, dau_b, cuoi_b, dau_b + dong_gmv_trong_bang, ws_chon)
    wb.save(DICH)
    ve_png(cac_diem, dong_gmv_trong_bang, mu, S, w_chon)
    print("Đã lưu", DICH)
    print("GMV:", np.round(w_gmv, 4), f"E={e_gmv:.4f} σ={np.sqrt(w_gmv @ S @ w_gmv):.4f}")
    print("Chọn:", np.round(w_chon, 4), f"E={w_chon @ mu:.4f} σ={np.sqrt(w_chon @ S @ w_chon):.4f}")


if __name__ == "__main__":
    main()
