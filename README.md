# Hasu-Tech — Phân tích bán hàng & dự báo nhu cầu cho cửa hàng bán lẻ

> Đang xây dựng.

## Bài toán kinh doanh

Chủ cửa hàng BHS Đại Phúc phải tự quyết định nhập hàng cho 2.521 mã thuộc 196 nhóm hàng mà chưa có công cụ dự báo nào hỗ trợ, trong khi 94% số mã chỉ phát sinh bán ra dưới 10% số ngày nên không thể nhẩm ra quy luật. Dữ liệu bán hàng hiện cũng không ghi nhận tồn kho, nên thiệt hại do nhập sai không được đo trực tiếp ở bất kỳ đâu.

Nhập thiếu thì mất doanh thu của lần khách hỏi mua, và có thể mất luôn khách sang cửa hàng khác. Nhập dư thì vốn nằm chết trong kho, hàng cận hạn phải đổi trả hoặc bán tháo, và với nhóm hàng có hạn sử dụng ngắn thì phần dư gần như mất trắng.

Dự án xây dựng mô hình dự báo nhu cầu theo nhóm hàng cấp 3, phân tầng theo mức độ đầy đủ dữ liệu, để trả lời một câu hỏi cụ thể mà chủ cửa hàng phải quyết mỗi tuần: tuần tới nhóm hàng nào cần nhập, với số lượng bao nhiêu.

Thành công được đo bằng ba chỉ tiêu:

1. **WMAPE so với mức nền.** Mức nền là dự báo bằng trung bình lịch sử. Chọn WMAPE vì dữ liệu có rất nhiều ngày bán bằng 0: MAPE chia cho lượng bán từng ngày nên không tính được, còn WMAPE chia cho tổng lượng bán cả kỳ nên luôn xác định.
2. **Tỷ lệ nhóm hàng đủ dữ liệu có WMAPE cải thiện so với mức nền**, để tránh trường hợp con số tổng đẹp nhờ vài nhóm lớn trong khi phần lớn nhóm còn lại tệ đi. Nhóm quá thưa được báo cáo riêng, không tính vào tỷ lệ này.
3. **Mô phỏng nhập hàng trên 8 tuần cuối.** So sánh số ngày thiếu hàng và lượng hàng dư ước tính khi nhập theo dự báo với khi nhập theo trung bình lịch sử. Đây là kết quả mô phỏng trên dữ liệu quá khứ, không phải kết quả áp dụng thực tế tại cửa hàng.

## Dữ liệu

- Nguồn: file xuất báo cáo bán hàng theo lợi nhuận từ phần mềm KiotViet của cửa hàng tạp hoá **BHS Đại Phúc** (chủ cửa hàng đã đồng ý công khai tên cửa hàng).
- Phạm vi: 27.068 dòng giao dịch, 11/09/2025 – 30/06/2026, 1 chi nhánh.
- Dữ liệu gốc **không được đưa lên repo** vì chứa thông tin cá nhân (tên nhân viên, tên khách nợ).

## Cấu trúc thư mục

```
data/raw/        dữ liệu gốc, không bao giờ sửa trực tiếp (không đưa lên GitHub)
data/processed/  cơ sở dữ liệu DuckDB sinh ra từ dữ liệu gốc (không đưa lên GitHub)
sql/             các câu lệnh SQL làm sạch và tổng hợp: raw → staging → mart
src/hasu/        code Python dùng lại được (nạp dữ liệu, làm sạch, mô hình)
notebooks/       khám phá và phân tích dữ liệu
app/             ứng dụng web Streamlit
tests/           kiểm thử tự động
docs/            mockup giao diện, báo cáo
```

## Luồng xử lý dữ liệu

```
File Excel KiotViet ──► raw_sales_lines ──► stg_sales_lines ──► (mart: phân tích, dự báo)
                         đổi tên cột,         làm sạch, gắn cờ,
                         không sửa giá trị    ẩn danh người bán
                                              dim_date: lịch mở/đóng cửa
```

| Tầng | Ở đâu | Làm gì |
|---|---|---|
| raw | `src/hasu/ingest.py` | Đọc Excel, đổi tên cột theo từ điển ánh xạ, ép kiểu dữ liệu. Nạp lại cùng một file không bị nhân đôi. |
| staging | `sql/staging/*.sql` | Khử trùng lặp, tính lại doanh thu ở mức dòng, điền giá vốn thiếu, chuẩn hoá nhóm hàng, phân loại giao dịch (bán lẻ / số lượng lớn / tổ chức / nội bộ). |
| kiểm tra | `src/hasu/quality.py` | Đối soát doanh thu với số tổng của KiotViet và sinh [báo cáo chất lượng dữ liệu](docs/data_quality_report.md). |

## Cách chạy

```bash
pip install -e ".[dev]"          # cài dự án và thư viện
# đặt file Excel xuất từ KiotViet vào data/raw/
python -m hasu.pipeline          # nạp, làm sạch, sinh báo cáo chất lượng
python -m pytest                 # chạy kiểm thử
```
