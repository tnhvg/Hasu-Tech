# Bài tập tình huống 2 – Nhóm 7, FIN3002_2

Ước lượng tỷ suất lợi tức kỳ vọng, độ lệch chuẩn, hiệp phương sai và hệ số tương quan của MBB, MWG, GAS
từ giá đóng cửa điều chỉnh hằng ngày, 01/10/2025 – 30/09/2026.

## File nộp

| File | Nội dung |
|---|---|
| `Nhom7_FIN3002_2_BaiTapTinhHuong2.xlsx` | Kết quả. Mọi chỉ tiêu là công thức Excel (AVERAGE, STDEV.S, VAR.S, COVARIANCE.S, CORREL) |
| `tai_du_lieu.py` | Bước 1: tải giá từ CafeF, lưu vào `du_lieu/` |
| `tao_excel.py` | Bước 2: tạo file Excel từ dữ liệu đã tải |
| `du_lieu/` | Dữ liệu gốc từng mã (giá điều chỉnh, giá thô, khối lượng) và bảng giá gộp |

## Cách chạy lại

Cần Python 3.10 trở lên và thư viện `openpyxl` (`pip install openpyxl`).

```
python tai_du_lieu.py     # tải lại dữ liệu từ CafeF
python tao_excel.py       # tạo lại file Excel
```

Mở file Excel, các công thức sẽ tự tính. Có thể đổi giả định số phiên giao dịch một năm (N = 250) ở ô
`B3` trang **Thống kê**; mọi chỉ tiêu theo năm tự cập nhật.

## Xử lý dữ liệu

- Dùng **giá điều chỉnh** để loại bỏ bước nhảy giá do chia cổ tức. Ví dụ ngày 11/08/2026 MBB chia cổ tức
  15% bằng cổ phiếu: giá thô giảm 16%, giá điều chỉnh tăng 0,7%.
- CafeF không có giá của 3 cổ phiếu ngày 29/01 và 30/01/2026, nên chỉ dùng các ngày cả 3 mã đều có giá
  (246 phiên, 245 quan sát lợi tức). Lợi tức ngày 02/02/2026 vì vậy gộp 3 phiên.
- Kết quả trong Excel đã được đối chiếu với tính toán độc lập bằng pandas: khớp ở mọi ô.
