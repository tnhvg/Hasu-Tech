# Đối chiếu với mô hình nền tảng Chronos-Bolt

_Sinh tự động bởi `python -m hasu.forecasting.chronos_compare`; mô hình `amazon/chronos-bolt-small`, zero-shot, 87 nhóm hàng × 12 mốc cắt. Chronos chạy sau khi đã chốt danh sách dự tuyển, nên không tham gia chọn mô hình._

## 1. Sai số theo tuần ở cấp nhóm hàng cấp 3

| Mô hình | WMAPE 4 tuần chọn | WMAPE 8 tuần chấm | MAE | MdAPE | Bias |
|---|---:|---:|---:|---:|---:|
| Chronos-Bolt (kỳ vọng) _(đối chiếu)_ | 59,2% | 50,6% | 5,74 | 61,6% | −24,9% |
| Kết hợp LightGBM + AutoETS + IMAPA + Chronos _(đối chiếu)_ | 60,4% | 51,9% | 5,89 | 52,6% | −5,8% |
| LightGBM (toàn cục) | 65,0% | 53,0% | 6,01 | 52,9% | −6,3% |
| Kết hợp LightGBM + IMAPA | 65,0% | 53,3% | 6,04 | 53,8% | −2,2% |
| Kết hợp LightGBM + IMAPA + TB 28 ngày | 66,4% | 53,3% | 6,05 | 55,0% | −0,1% |
| Kết hợp LightGBM + AutoETS + IMAPA **(được chọn)** | 63,8% | 54,2% | 6,15 | 53,3% | 0,5% |
| Trung bình trượt 28 ngày | 71,1% | 56,4% | 6,40 | 60,1% | 4,1% |
| IMAPA | 66,4% | 56,9% | 6,45 | 58,6% | 2,0% |
| ADIDA | 66,0% | 57,0% | 6,47 | 58,1% | 2,9% |
| Chronos-Bolt (trung vị theo ngày) _(đối chiếu)_ | 65,4% | 58,4% | 6,63 | 91,3% | −49,5% |
| AutoETS (Holt-Winters) | 64,9% | 59,3% | 6,73 | 58,6% | 5,9% |
| TSB | 67,3% | 59,6% | 6,76 | 64,0% | −1,7% |
| Croston | 70,0% | 63,5% | 7,20 | 58,0% | 12,0% |
| Lặp lại tuần trước | 74,8% | 68,9% | 7,82 | 74,5% | −1,4% |
| Mức nền: trung bình lịch sử | 78,1% | 73,1% | 8,29 | 64,0% | 23,8% |

## 2. Sai số khi cộng lên các cấp

| Cấp | Kết hợp LightGBM + AutoETS + IMAPA | Chronos-Bolt (kỳ vọng) | Kết hợp LightGBM + AutoETS + IMAPA + Chronos | Trung bình trượt 28 ngày |
|---|---:|---:|---:|---:|
| Nhóm hàng cấp 3 | 54,2% | 50,6% | 51,9% | 56,4% |
| Nhóm hàng cấp 2 | 46,0% | 44,4% | 44,2% | 47,6% |
| Ngành hàng cấp 1 | 29,1% | 34,7% | 28,9% | 29,9% |
| Toàn cửa hàng | 14,5% | 26,4% | 16,2% | 14,3% |

## 3. Kiểm định chênh lệch (theo nhóm hàng, 8 tuần chấm)

| So sánh | Tỷ lệ nhóm tốt hơn | Wilcoxon p | Diebold–Mariano p |
|---|---:|---:|---:|
| Chronos-Bolt (kỳ vọng) so với Kết hợp LightGBM + AutoETS + IMAPA | 77,0% | < 0,001 | 0,041 |
| Chronos-Bolt (kỳ vọng) so với Trung bình trượt 28 ngày | 66,3% | < 0,001 | 0,016 |
| Chronos-Bolt (kỳ vọng) so với Mức nền: trung bình lịch sử | 75,9% | < 0,001 | < 0,001 |
| Kết hợp LightGBM + AutoETS + IMAPA + Chronos so với Kết hợp LightGBM + AutoETS + IMAPA | 87,4% | < 0,001 | < 0,001 |
| Kết hợp LightGBM + AutoETS + IMAPA + Chronos so với Trung bình trượt 28 ngày | 60,9% | 0,014 | 0,032 |

## 4. Nhận xét

- Nếu Chronos có mặt trong danh sách dự tuyển, quy tắc chọn theo 4 tuần đầu sẽ chọn **Chronos-Bolt (kỳ vọng)**.
- Chronos dự báo thiếu có hệ thống: 62/87 nhóm có |TS| > 4, nên sai số tăng mạnh khi cộng lên cấp toàn cửa hàng.
- Lấy trung vị theo ngày rồi cộng lên tuần làm dự báo thiếu nặng với chuỗi thưa (trung vị ngày thường bằng 0); bản kỳ vọng (trung bình 9 phân vị) mới cùng bản chất với các mô hình khác.
- Tổ hợp có Chronos gần như không lệch và có sai số thấp hơn mô hình được chọn, nhưng được đề xuất sau khi đã xem kết quả chấm điểm, nên cần kiểm định lại trên dữ liệu mới trước khi dùng.
