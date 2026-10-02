# Hướng dẫn đưa ứng dụng lên Streamlit Community Cloud

Streamlit Community Cloud cho phép chạy ứng dụng miễn phí, có đường link công khai để gửi nhà tuyển dụng.
Các bước dưới đây cần **tài khoản GitHub của bạn**, nên bạn tự làm.

## 0. Chuẩn bị (một lần)

1. Gộp nhánh làm việc vào `main`. Vào GitHub → repo `Hasu-Tech` → **Pull requests** → **New pull request**,
   chọn `base: main` ← `compare: claude/ecstatic-shannon-snxl2a` → **Create pull request** → **Merge**.
   (Cũng có thể triển khai thẳng từ nhánh làm việc, nhưng link sẽ đẹp hơn nếu dùng `main`.)
2. Kiểm tra trên GitHub: thư mục `app/demo_data/` có 23 file `.parquet`, và **không có** file `.xlsx` hay `.duckdb` nào.

## 1. Tạo ứng dụng

1. Vào <https://share.streamlit.io> → **Sign in with GitHub** → cho phép Streamlit truy cập repo.
2. Bấm **Create app** → **Deploy a public app from GitHub**.
3. Điền:

   | Ô | Giá trị |
   |---|---|
   | Repository | `tnhvg/Hasu-Tech` |
   | Branch | `main` |
   | Main file path | `app/streamlit_app.py` |
   | App URL | ví dụ `hasu-du-bao-ban-le` |

4. Mở **Advanced settings**:
   - **Python version:** 3.11.
   - **Secrets:** thêm dòng sau để ứng dụng luôn dùng dữ liệu demo:
     ```toml
     HASU_FORCE_DEMO = "1"
     ```
5. Bấm **Deploy**. Lần đầu mất khoảng 5–10 phút để cài thư viện (statsforecast, lightgbm, shap...).

## 2. Kiểm tra sau khi chạy

- Trang **Tổng quan** hiện nguồn "Dữ liệu demo (BHS Đại Phúc, đã ẩn danh)".
- Thử trang **Nạp dữ liệu** với file KiotViet của bạn: xử lý mất khoảng 1–2 phút trên máy chủ miễn phí.

## 3. Nếu gặp lỗi

| Hiện tượng | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| `ModuleNotFoundError: hasu` | Chạy sai file chính | Main file path phải là `app/streamlit_app.py` |
| Hết bộ nhớ khi nạp file lớn | Máy chủ miễn phí có khoảng 1 GB RAM | Nạp file theo từng quý thay vì cả năm |
| Ứng dụng "ngủ" sau vài ngày | Bản miễn phí tự ngủ khi không ai dùng | Mở link, bấm **Wake up**; chờ khoảng 1 phút |

## 4. Cập nhật dữ liệu demo khi có dữ liệu mới

Chạy trên máy của bạn (cần file KiotViet trong `data/raw/`):

```bash
python -m hasu.pipeline
python -m hasu.forecasting.run
python -m hasu.export_demo      # tự kiểm tra, không xuất nếu có cột nhạy cảm
git add app/demo_data && git commit -m "Cập nhật dữ liệu demo" && git push
```

Streamlit Cloud tự triển khai lại khi có commit mới.
