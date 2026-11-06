# Bài tập tình huống 3 – Nhóm 7, FIN3002_2

Vẽ đường biên phương sai bé nhất, đường biên hiệu quả của danh mục MBB, MWG, GAS bằng Solver (Excel), và
chọn danh mục đầu tư cho 10 tỷ đồng. Đầu vào là lợi tức kỳ vọng và ma trận hiệp phương sai của Bài tập 2.

## File nộp

`Nhom7_FIN3002_2_BaiTapTinhHuong3.xlsx`. Trang đầu tiên cần đọc là **Danh mục chọn**:

| Trang | Nội dung |
|---|---|
| Giới thiệu | Bài toán, cách tự chạy lại Solver, chú thích màu |
| Giá → Hiệp phương sai | Dữ liệu và ước lượng, giống Bài tập 2 |
| Solver 1 - PSNN | Danh mục phương sai nhỏ nhất: Min σ², Σw = 1, w ≥ 0 |
| Solver 2 - Đường biên | Min σ² với E(Rp) = mức mục tiêu (mỗi lần chạy cho một điểm của đường biên) |
| Solver 3 - DM chọn | Max E(Rp) với σp ≤ 25% |
| Đường biên | 26 điểm của đường biên phương sai bé nhất, đánh dấu phần hiệu quả, đồ thị |
| Danh mục chọn | So sánh 4 danh mục, lý do chọn, phân bổ 10 tỷ đồng thành số cổ phiếu |

Cài đặt Solver (ô mục tiêu, ô thay đổi, ràng buộc) đã lưu sẵn trong từng trang Solver, nên Data → Solver
mở ra là có sẵn.

**Chạy toàn bộ bằng Excel Solver:** file `chay_solver.bas` là macro VBA gọi Excel Solver giải Solver 1,
Solver 3 và lần lượt 26 điểm của đường biên, rồi ghi "Excel Solver" vào cột J trang Đường biên.
Cách chạy: mở file Excel → Alt + F11 → File → Import File… chọn `chay_solver.bas` → đặt con trỏ trong
`ChayToanBoSolver` → F5. Cần bật Solver Add-in trước. Tỷ trọng đang có trong file được giải trước bằng Python (scipy, cùng bài toán) để kiểm
tra chéo; nhóm chạy lại Solver trong Excel để kiểm chứng (hướng dẫn ở trang Giới thiệu).

## Kết quả chính (theo năm)

| Danh mục | MBB | MWG | GAS | E(Rp) | σp |
|---|---|---|---|---|---|
| Phương sai nhỏ nhất | 66,7% | 14,5% | 18,8% | 6,2% | 24,5% |
| **Được chọn (σp ≤ 25%)** | **56,8%** | **15,2%** | **28,0%** | **10,8%** | **25,0%** |
| Bài 1 (40/35/25) | 40% | 35% | 25% | 10,2% | 25,6% |

## Chạy lại

```
python tao_excel_bai3.py    # cần openpyxl, numpy, scipy, matplotlib; dùng dữ liệu ở ../bai_2/du_lieu
```
