# Bài tập nhóm Đầu tư tài chính – Nhóm 7 – FIN3002_2

Gộp 3 bài tập tình huống thành báo cáo nhóm: phân tích bối cảnh, phân tích MBB – MWG – GAS, rủi ro và
lợi nhuận, xây dựng danh mục 10 tỷ đồng bằng Solver.

## File nộp

| File | Nộp ở đâu |
|---|---|
| `Nhom7_FIN3002_2_BaoCaoNhom.docx` | E-study + bản in tại lớp |
| `Nhom7_FIN3002_2_BaiTapNhom.xlsx` | E-study (dữ liệu giá, bảng tính, biểu đồ, kết quả Solver) |
| `chay_solver.bas` | Nên nộp kèm: macro VBA chạy Excel Solver cho 26 điểm đường biên (báo cáo và trang Giới thiệu có nhắc tới) |

Bản Word đã gồm các chỉnh sửa nhóm làm trên Google Docs ngày 07/11/2026 (bìa có logo DUE và khung, Khoa
Thương mại điện tử, phân công và MSSV, mức đóng góp 16,67%, ngày 7/11/2026).

**Trước khi nộp:** mở file Word bằng Microsoft Word, kiểm tra nội dung chính vẫn ≤ 15 trang (bản dựng
hiện khoảng 14,5 trang) và mục lục khớp số trang; nếu Word ngắt trang khác, bấm chuột phải vào mục lục →
Update Field (chỉ cập nhật số trang).

## Cách trình bày

- Times New Roman 12, giãn dòng 1,5, trước/sau đoạn 0 pt; lề trái 2,5 cm, phải/trên/dưới 2 cm.
- Header "Bài tập nhóm Đầu tư tài chính"; footer trái "Thứ 3_Tiết 789_Nhóm 7", phải số trang. Trang
  hoạt động và mục lục đánh số i, ii; nội dung chính đánh số từ 1.
- Trích dẫn kiểu APA (Tác giả, năm) ở cuối câu; danh mục tài liệu tham khảo xếp theo ABC, chỉ gồm nguồn
  được trích. Không in dòng "Nguồn:" dưới bảng và hình (đổi `HIEN_NGUON = True` trong
  `tao_bao_cao_nhom.py` nếu muốn in lại).
- Viết cho người đọc chưa học về đầu tư: thuật ngữ được giải thích ở lần dùng đầu tiên, sau mỗi bảng có
  đoạn "Ý nghĩa", chi tiết kỹ thuật Excel nằm trong file Excel.

## Nguồn số liệu

- Phần 1–2: các nguồn đã trích trong Bài tập tình huống 1 (`../noi_dung.py`).
- Phần 3–4: dữ liệu giá CafeF (`../bai_2/du_lieu/`) và kết quả Excel Solver nhóm đã chạy
  (`du_lieu/ket_qua_excel_solver.json`, trích từ file Excel sau khi chạy macro). File Excel nộp dùng đúng
  các tỷ trọng này, đủ chữ số; tỷ trọng âm cỡ 10⁻⁷ do sai số dừng của Solver được đưa về 0.

## Tạo lại

```
python tao_excel_nhom.py      # file Excel (dùng code của bai_2, bai_3)
python tao_bao_cao_nhom.py    # file Word; cần LibreOffice và pdftotext để đánh số trang mục lục
```

Nội dung báo cáo nằm trong `noi_dung_nhom.py` (trích dẫn ghi dạng [n] trỏ tới danh mục; khi dựng Word
được đổi sang kiểu APA). Sửa chữ ở đó rồi chạy lại để mục lục tự cập nhật số trang.
