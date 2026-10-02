# Kịch bản thuyết trình và câu hỏi phỏng vấn

## Video demo 3 phút

| Thời gian | Màn hình | Nói gì |
|---|---|---|
| 0:00–0:20 | README | "Cửa hàng tạp hoá BHS Đại Phúc có 2.521 mã hàng, chủ cửa hàng nhập hàng bằng kinh nghiệm. Em xây hệ thống trả lời câu hỏi: tuần tới nhập nhóm hàng nào, bao nhiêu." |
| 0:20–0:45 | Chất lượng dữ liệu | "Trước khi phân tích, em đối soát doanh thu tính lại với KiotViet, lệch tối đa 6 đồng mỗi tháng. Em phát hiện 1/3 doanh thu đến từ đơn lớn chỉ chiếm 1,8% hoá đơn, nên tách riêng khỏi nhu cầu bán lẻ." |
| 0:45–1:20 | Phân tích kinh doanh | Ma trận biên lợi nhuận: "7 nhóm hàng đang bán lỗ, nhiều nhất là sữa bột và dầu ăn." Tab Tết: "Doanh thu tăng 1,76 lần nhưng số lượng chỉ 1,13 lần, nên nhập hàng Tết theo hệ số doanh thu sẽ dư." |
| 1:20–2:00 | Dự báo & đề xuất nhập | "94% mã hàng bán dưới 10% số ngày, nên em dự báo ở cấp nhóm hàng, so sánh 12 mô hình bằng kiểm định trượt. Mỗi dòng có nhãn độ tin cậy, và số lượng đề xuất nhập dùng phân vị theo loại hàng." |
| 2:00–2:25 | Giải thích dự báo | "SHAP cho biết vì sao dự báo ra con số này: bán gần đây tăng làm dự báo tăng 101%..." |
| 2:25–2:50 | Lịch sử & đánh giá | "Mỗi lần chạy, dự báo được lưu lại. Khi nạp dữ liệu tuần mới, hệ thống đối chiếu và tự cảnh báo nếu mô hình kém đi." |
| 2:50–3:00 | Tổng quan | "Độ chính xác tổng tuần 84%. Mô phỏng 8 tuần: giảm 11% hàng thiếu và 20% giá trị hàng dư so với cách nhập theo trung bình." |

## Câu hỏi nhà tuyển dụng hay hỏi, và ý chính để trả lời

**1. Vì sao dùng WMAPE mà không dùng MAPE?**
MAPE chia cho lượng bán thực tế từng ngày. Dữ liệu có rất nhiều ngày bán bằng 0 nên MAPE không tính được. WMAPE
chia cho tổng lượng bán cả kỳ.

**2. Mô hình của bạn chỉ tốt hơn mức nền ở 50% số nhóm hàng. Vậy có đáng dùng không?**
Có, nhưng phải nói đúng phạm vi. Ở cấp nhóm nhỏ theo tuần, nhu cầu gần như ngẫu nhiên nên không mô hình nào
chính xác. Ở cấp ngành hàng và toàn cửa hàng, sai số giảm mạnh (24% và 16%). Giá trị lớn nhất nằm ở chính
sách nhập theo phân vị: mô phỏng giảm cả hàng thiếu lẫn hàng dư so với nhập theo trung bình.

**3. Vì sao chọn mô hình kết hợp, trong khi LightGBM có điểm tốt nhất?**
Chỉ được chọn mô hình trên 4 tuần "chọn mô hình". Ở đó mô hình kết hợp thắng. Nếu nhìn kết quả 8 tuần chấm
điểm rồi mới chọn LightGBM, con số báo cáo sẽ bị đẹp giả (rò rỉ dữ liệu kiểm tra).

**4. Bạn xử lý ngày cửa hàng đóng cửa thế nào?**
Ngày đóng cửa không phải nhu cầu bằng 0. Em đánh dấu trong bảng lịch, thay bằng trung vị cùng thứ ở các tuần
lân cận khi huấn luyện, và không tính vào đánh giá.

**5. Làm sao biết một sản phẩm hết hàng khi không có dữ liệu tồn kho?**
Không biết chắc. Em ước lượng xác suất để một mã bán đều có L ngày liên tiếp không bán do tình cờ, là (1 − p)^L.
Nếu xác suất dưới 1% thì đánh dấu nghi ngờ, và để chủ cửa hàng xác nhận. Hàng theo mùa cũng có biểu hiện
giống vậy, nên em ghi rõ đây là suy đoán.

**6. Vì sao không đưa giá/khuyến mãi vào mô hình?**
Giá chỉ quan sát được ở ngày có bán. Đưa vào sẽ làm mô hình "biết trước" hôm đó có bán. Em ước lượng riêng ảnh
hưởng giảm giá cho phần kịch bản, và cảnh báo rằng nó có thể bị phóng đại do khách mua theo thùng được giá sỉ.

**7. Nếu có thêm thời gian, bạn sẽ làm gì?**
(1) Lấy dữ liệu tồn kho và thời gian giao hàng để tính tồn kho an toàn thật. (2) Chạy thử Chronos (code đã sẵn
sàng, máy chủ thử nghiệm chặn tải mô hình). (3) Gộp các nhóm hàng trùng nghĩa trong KiotViet. (4) Theo dõi vòng
lặp đối chiếu qua vài tháng để công bố độ chính xác đã kiểm chứng.

**8. Phát hiện kinh doanh nào bạn thấy giá trị nhất?**
Lượng khách bán lẻ giảm 27% từ tháng 5 trong khi giá trị mỗi hoá đơn không đổi. Đây là vấn đề lưu lượng khách,
không phải chi tiêu, nên giải pháp nằm ở thu hút khách chứ không phải tăng giá trị giỏ hàng.
