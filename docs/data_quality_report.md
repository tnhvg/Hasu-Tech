# Báo cáo chất lượng dữ liệu

_Sinh tự động bởi `python -m hasu.pipeline` lúc 02/10/2026 10:37._

## 1. Tổng quan

| Chỉ số | Giá trị |
|---|---|
| Khoảng thời gian | 11/09/2025 – 30/06/2026 |
| Số dòng (raw → staging) | 27.068 → 27.068 |
| Dòng trùng lặp đã loại | 0 |
| Số hoá đơn | 12.506 |
| Số mã hàng | 2.515 |
| Doanh thu thuần (tính lại ở mức dòng) | 1.333.837.807 đ |

## 2. Đối soát doanh thu

Doanh thu được tính lại ở mức dòng (`số lượng × giá bán`) rồi so với các con số tổng mà KiotViet đã tính sẵn. Nếu khớp, việc làm sạch không làm mất hay nhân đôi tiền.

| Tháng | Doanh thu KiotViet | Doanh thu tính lại | Chênh lệch |
|---|---|---|---|
| 09-2025 | 94.535.635 | 94.535.636 | 1 |
| 10-2025 | 112.686.345 | 112.686.346 | 1 |
| 11-2025 | 95.073.310 | 95.073.312 | 2 |
| 12-2025 | 153.718.113 | 153.718.119 | 6 |
| 01-2026 | 156.366.418 | 156.366.416 | -2 |
| 02-2026 | 177.650.362 | 177.650.361 | -1 |
| 03-2026 | 122.988.870 | 122.988.869 | -1 |
| 04-2026 | 171.347.780 | 171.347.781 | 1 |
| 05-2026 | 120.418.760 | 120.418.761 | 1 |
| 06-2026 | 129.052.200 | 129.052.206 | 6 |

Chênh lệch lớn nhất giữa các tháng: **6 đ** (do KiotViet làm tròn giá bán sau khi phân bổ giảm giá hoá đơn).

Ở mức hoá đơn: 100,0% số hoá đơn khớp tuyệt đối (lệch ≤ 1 đ), 100,0% khớp trong phạm vi 100 đ. Điều này xác nhận **giá bán trên từng dòng đã là giá sau giảm giá hoá đơn**, nên doanh thu dòng = số lượng × giá bán là đúng.

## 3. Các vấn đề phát hiện và cách xử lý

| Vấn đề | Số dòng | Doanh thu (đ) | Tỷ lệ doanh thu | Cách xử lý |
|---|---|---|---|---|
| Phiếu trả hàng (mã TH, số lượng âm) | 38 | -2.943.800 | 0,2% | Giữ lại, gắn cờ is_return; doanh thu thuần đã trừ hàng trả |
| Hoá đơn đã sửa (mã có đuôi .01, .02...) | 1.375 | 415.774.616 | 31,2% | Giữ lại: bản gốc không có trong file nên không bị đếm hai lần |
| Giá vốn = 0 (thiếu giá vốn) | 552 | 24.660.290 | 1,8% | Điền bằng trung vị giá vốn của mã hàng, dự phòng bằng tỷ lệ giá vốn của nhóm hàng |
| Giá bán = 0 trên hoá đơn bán | 23 | 0 | 0,0% | Gắn cờ is_zero_price (chủ yếu hàng tặng khai trương) |
| Hàng khuyến mại khai trương | 66 | 2.101.784 | 0,2% | Gắn cờ is_opening_promo; sửa lỗi chính tả "khai chương" |
| Số lượng lẻ (hàng cân theo kg) | 43 | 3.462.607 | 0,3% | Hợp lệ, giữ nguyên |
| Thiếu thương hiệu | 19.255 | 844.329.803 | 63,3% | Điền "Không rõ"; không dùng thương hiệu làm biến dự báo |
| Mã hàng bị xoá rồi tạo lại (hậu tố {DEL}) | 209 | 14.674.955 | 1,1% | Bỏ hậu tố để gộp lịch sử bán của bản cũ và bản mới; giữ cờ sku_deleted |
| Bán chịu (ghi chú "nợ", "chưa tt") | 13 | 330.500 | 0,0% | Vẫn là nhu cầu thật; gắn cờ is_credit_sale |

Cách điền giá vốn bị thiếu: `sku_median` 421 dòng, `category_ratio` 127 dòng, `không điền được` 4 dòng. Các dòng không điền được bị loại khỏi phân tích biên lợi nhuận.

## 4. Nhóm hàng

- Sau làm sạch: **15 nhóm cấp 1, 67 nhóm cấp 2, 188 nhóm cấp 3**.
- 81 dòng có nhóm hàng không chuẩn (nằm sai cấp, đã bị xoá, "chưa khai báo") được ánh xạ về đúng cây nhóm hàng.
- 1.759 dòng chỉ có 1–2 cấp: cấp còn thiếu được lấy theo cấp trên (ví dụ `Thực phẩm đông mát>>Kem` → cấp 3 = `Kem`).

## 5. Loại giao dịch: không phải dòng nào cũng là nhu cầu bán lẻ

Ghi chú hoá đơn và số lượng bất thường cho thấy một phần giao dịch không phản ánh nhu cầu mua lẻ hằng ngày. Nếu đưa nguyên vào mô hình, các đơn này sẽ tạo ra những "đỉnh" giả mà mô hình không thể và không nên học theo.

| Loại | Số dòng | Số hoá đơn | Tỷ lệ số lượng | Tỷ lệ doanh thu |
|---|---|---|---|---|
| Bán lẻ | 25.820 | 12.320 | 50,5% | 62,9% |
| Đơn lớn (hoá đơn ≥ 100 sản phẩm hoặc ≥ 3 triệu đ; hoặc dòng ≥ 48 và ≥ 10 lần mức mua điển hình) | 1.033 | 206 | 42,9% | 31,9% |
| Đơn tổ chức / công ty (theo ghi chú) | 157 | 16 | 6,4% | 4,4% |
| Nội bộ: hàng mẫu, trả NCC, chuyển kho (theo ghi chú) | 58 | 13 | 0,2% | 0,9% |

**Hệ quả:** mô hình dự báo nhu cầu bán lẻ sẽ chỉ dùng loại `Bán lẻ`. Đơn số lượng lớn và đơn tổ chức được phân tích riêng như một kênh bán sỉ.

## 6. Tính liên tục theo thời gian

- 293 ngày trong khoảng dữ liệu, cửa hàng có bán hàng 281 ngày.
- 12 ngày không có giao dịch: 16/02/2026, 17/02/2026, 18/02/2026, 19/02/2026, 20/02/2026, 21/02/2026, 23/02/2026, 03/03/2026, 12/04/2026, 30/04/2026, 01/05/2026, 14/06/2026.
- Chuỗi 16–23/02/2026 trùng kỳ nghỉ Tết Bính Ngọ (mùng 1 Tết = 17/02/2026); 30/04–01/05 là nghỉ lễ. Các ngày này được đánh dấu `is_open = false` trong `dim_date` và **không** được coi là nhu cầu bằng 0.
- Tháng đầu tiên chỉ có dữ liệu từ 11/09/2025, nên tổng tháng 09/2025 không so sánh trực tiếp được với các tháng khác.

## 7. Độ thưa của dữ liệu bán

Chỉ tính bán lẻ, trên các ngày cửa hàng mở cửa:

- 94,1% mã hàng bán ra dưới 10% số ngày.
- Chỉ 3 mã hàng bán ra từ 50% số ngày trở lên.
- Ở cấp nhóm hàng 3: 16/185 nhóm bán ra từ 50% số ngày trở lên.

→ Cần dự báo phân tầng theo mức độ đầy đủ dữ liệu, và dùng mô hình cho nhu cầu gián đoạn (intermittent demand) ở các nhóm thưa.
