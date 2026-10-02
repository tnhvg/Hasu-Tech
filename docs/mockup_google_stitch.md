# Mockup giao diện với Google Stitch và Figma

Ứng dụng thật đã chạy được (xem `docs/screenshots/`). Mockup vẫn có giá trị cho portfolio: nó cho thấy bạn
**thiết kế trước khi xây**, và là nơi thử các ý tưởng giao diện mà Streamlit khó làm (ví dụ bản cho điện thoại).

## Quy trình đề xuất

1. **Google Stitch** (<https://stitch.withgoogle.com>): dán từng mô tả bên dưới để sinh bản nháp màn hình.
2. Xuất sang **Figma** (Stitch có nút *Copy to Figma*), chỉnh màu, chữ, khoảng cách cho thống nhất.
3. Đặt ảnh mockup cạnh ảnh ứng dụng thật trong README hoặc slide: "thiết kế → sản phẩm".

## Hệ thống thiết kế (dán vào đầu mọi prompt)

```
Design system: clean analytics web app for a Vietnamese convenience store owner. Language: Vietnamese.
Background #FCFCFB, sidebar #F0EFEC, text #0B0B0B, secondary text #52514E.
Primary blue #2A78D6 (main data series), orange #EB6834 (comparison / baseline series),
red #D03B3B only for losses and alerts. Font: Inter or Source Sans. Thin chart marks, light grid,
no 3D, no gradients. Numbers use Vietnamese format: 1.234.567 đ, 12,5%.
Left sidebar navigation groups: "Tổng quan" | "Dữ liệu": Nạp dữ liệu, Chất lượng dữ liệu |
"Phân tích": Phân tích kinh doanh | "Dự báo": Dự báo & đề xuất nhập, Giải thích dự báo, Kịch bản mô phỏng, Lịch sử & đánh giá.
```

## Prompt cho từng màn hình

### 1. Tổng quan
```
Dashboard home "Tổng quan cửa hàng". Top row: 4 KPI cards — Doanh thu thuần 1,32 tỷ; Lợi nhuận gộp 97,3 tr
(biên 7,4%); Hoá đơn bán lẻ/ngày 60 (↑5,3% so với 4 tuần trước); Độ chính xác dự báo tuần 84%.
Section "Cần chú ý" with 4 alert banners: red "7 nhóm hàng đang bán lỗ", yellow "Lượng khách giảm 20%",
yellow "27 mã hàng ngừng bán tới cuối kỳ", blue "Đề xuất nhập tuần tới: 149 nhóm hàng, 20,9 tr".
Bottom: two charts side by side — stacked monthly bar chart (blue Bán lẻ, orange Đơn lớn) and a weekly
line chart (grey actual, dotted blue forecast for next 4 weeks).
```

### 2. Nạp dữ liệu
```
Upload page "Nạp dữ liệu". Drag-and-drop area for KiotViet .xlsx files. Step 1 "Xác nhận ánh xạ cột":
a table with two columns "Cột trong file" and "Cột chuẩn" (dropdown per row), green check "26/26 cột".
Step 2 "Xử lý dữ liệu và dự báo": primary button "Xử lý", progress log card with steps
(Nạp dữ liệu → Làm sạch → Phân tích → Kiểm định mô hình → Dự báo), success banner and a small grey note
"Khoảng nghỉ trùng dịp Tết (bình thường)".
```

### 3. Dự báo & đề xuất nhập
```
Page "Dự báo & đề xuất nhập hàng". KPI row: Tuần dự báo 01/07–07/07; Mô hình: Kết hợp 3 mô hình;
Sai số tổng tuần 15,7% (mức nền 19,2%); Giá vốn hàng đề xuất nhập 20,9 tr.
Filters: Ngành hàng, Độ tin cậy, Loại nhóm hàng. Main table columns: Nhóm hàng, Ngành, Dự báo tuần,
Khoảng 80%, Đề xuất nhập, Giá vốn, Độ tin cậy (colored dot + label: Cao/Trung bình/Thấp/Chưa đủ dữ liệu),
Loại (Ngôi sao / Bảo quản lâu / Dễ hư hỏng). Button "Tải bảng đề xuất (CSV)".
Detail panel: line chart 12 weeks actual + 4 weeks forecast with light-blue 80% band, and a table
"Phân bổ xuống mã hàng" with share progress bars.
```

### 4. Giải thích dự báo
```
Page "Giải thích dự báo". Horizontal bar chart "Yếu tố quan trọng nhất" (Xu hướng nền 28 ngày,
Độ biến động, Xu hướng 7 ngày, Ngày trong tuần...). Below: selectors Nhóm hàng and Ngày, then a horizontal
waterfall chart: grey "Mức bán thường của nhóm 12,1" → blue "+101% Xu hướng 7 ngày" → blue "+44%" →
orange "−13% Ngày trong tháng" → grey total "Dự báo 37,9". Caption explaining percentages.
```

### 5. Kịch bản mô phỏng
```
Page "Kịch bản mô phỏng" with two tabs: "Giảm giá một ngành hàng" and "Kỳ nghỉ Tết".
Tab 1: dropdown Ngành hàng, slider Mức giảm giá (%), slider "Phần tăng lấy từ mã khác cùng nhóm (%)",
three KPI cards (nhu cầu hiện tại, theo kịch bản, cần nhập thêm), grouped horizontal bars grey vs blue,
and a yellow warning box "Độ tin cậy thấp: hãy coi đây là mức trần".
```

### 6. Lịch sử & đánh giá
```
Page "Lịch sử & đánh giá". Green status banner "Trong ngưỡng: giữ mô hình". Left chart: weekly WMAPE bars
with a red dotted threshold line "Ngưỡng cảnh báo". Right chart: saved forecast vs actual weekly totals.
Big KPI "Độ chính xác tổng tuần đã kiểm chứng 84%". Table of saved forecast runs.
```

### 7. (Thêm) Bản cho điện thoại, chỉ làm mockup
```
Mobile version (390×844) of "Đề xuất nhập tuần tới" for the store owner checking on the phone:
a list of cards, each card shows Nhóm hàng, big number "Đề xuất nhập 312", small "dự báo 222 · khoảng 78–390",
and a colored confidence chip. Sticky bottom button "Tải danh sách".
```

## Gợi ý trình bày trong portfolio

- Đặt mockup Stitch/Figma và ảnh ứng dụng thật cạnh nhau, ghi chú những gì đã thay đổi khi xây thật và vì sao
  (ví dụ: biểu đồ SHAP ban đầu bắt đầu từ trung bình toàn cửa hàng, khó đọc; bản thật bắt đầu từ
  "mức bán thường của nhóm").
- Mockup bản điện thoại là ý tưởng mở rộng, ghi rõ "chưa triển khai".
