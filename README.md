# Hasu-Tech — Phân tích bán hàng & dự báo nhu cầu cho cửa hàng bán lẻ

> Đang xây dựng.

## Bài toán kinh doanh

_(sẽ viết)_

## Dữ liệu

- Nguồn: file xuất báo cáo bán hàng theo lợi nhuận từ phần mềm KiotViet của một cửa hàng tạp hoá.
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
