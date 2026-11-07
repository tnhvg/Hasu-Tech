# Bài tập nhóm Đầu tư tài chính – Nhóm 7 – FIN3002_2

Gộp 3 bài tập tình huống thành báo cáo nhóm: phân tích bối cảnh, phân tích MBB – MWG – GAS, rủi ro và
lợi nhuận, xây dựng danh mục 10 tỷ đồng bằng Solver.

## File nộp

| File | Nộp ở đâu |
|---|---|
| `Nhom7_FIN3002_2_BaoCaoNhom.docx` | E-study + bản in tại lớp |
| `Nhom7_FIN3002_2_BaiTapNhom.xlsx` | E-study (dữ liệu giá, bảng tính, biểu đồ, kết quả Solver) |
| `chay_solver.bas` | Nộp kèm nếu cần: macro VBA chạy Excel Solver cho 26 điểm đường biên |

**Trước khi nộp, nhóm cần điền:** nhiệm vụ thực tế và mức độ đóng góp của từng thành viên (trang Báo cáo
hoạt động). Lớp học Thứ 3 – Tiết 789 đã điền ở bìa và footer.

Báo cáo viết cho người đọc chưa học về đầu tư: thuật ngữ được giải thích ở lần dùng đầu tiên, sau mỗi bảng
có đoạn "Ý nghĩa", chi tiết kỹ thuật của Excel (tên hàm, thuật toán) chỉ nằm trong file Excel.

## Nguồn số liệu

- Phần 1–2: các nguồn đã trích trong Bài tập tình huống 1 (`../noi_dung.py`).
- Phần 3–4: dữ liệu giá CafeF (`../bai_2/du_lieu/`) và kết quả Excel Solver nhóm đã chạy
  (`du_lieu/ket_qua_excel_solver.json`, trích từ file Excel sau khi chạy macro).

## Tạo lại

```
python tao_excel_nhom.py      # file Excel (dùng code của bai_2, bai_3)
python tao_bao_cao_nhom.py    # file Word; cần LibreOffice và pdftotext để đánh số trang mục lục
```

Nội dung báo cáo nằm trong `noi_dung_nhom.py`; sửa chữ ở đó rồi chạy lại để mục lục tự cập nhật số trang.
