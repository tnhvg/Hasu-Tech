"""Nội dung báo cáo Bài tập nhóm Đầu tư tài chính – Nhóm 7 – FIN3002_2 (dùng bởi tao_bao_cao_nhom.py).

Viết cho người đọc chưa học về đầu tư: định nghĩa thuật ngữ ở lần dùng đầu tiên, sau mỗi kết quả có câu
"Ý nghĩa", câu ngắn, trích dẫn gom ở cuối đoạn, chi tiết kỹ thuật của Excel để trong file Excel.

Khối nội dung: ("phan", tiêu đề) · ("h2"/"h3", tiêu đề) · ("p", đoạn) · ("abc"/"gach", [ý])
("ct", công thức, số) · ("bang", số, tên, hàng (hàng đầu là tiêu đề), độ rộng cột cm, cột căn phải, nguồn)
("hinh", số, tên, file trong figures/, nguồn).
Đánh dấu chữ: **đậm**, *nghiêng*, _{chỉ số dưới}, ^{chỉ số trên}. [n] trỏ tới mục thứ n của TAI_LIEU;
khi dựng Word, [n] được đổi thành trích dẫn kiểu APA (Tác giả, năm) và danh mục được xếp theo ABC.
Số liệu Phần 3–4 lấy từ file Excel Nhom7_FIN3002_2_BaiTapNhom.xlsx (kết quả Excel Solver của nhóm).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from noi_dung import TAI_LIEU as TAI_LIEU_BAI_1  # noqa: E402  (danh mục [1]–[42] của Bài tập tình huống 1)

BIA = {
    "truong": "Trường Đại học Kinh tế - Đại học Đà Nẵng",
    "khoa": "Khoa Thương mại điện tử",
    "loai_bao_cao": "BÁO CÁO BÀI TẬP NHÓM",
    "hoc_phan": "ĐẦU TƯ TÀI CHÍNH",
    "thu_tiet": "Thứ 3 – Tiết 789",
    "nhom": "NHÓM 7",
    "de_tai": ["PHÂN TÍCH, LỰA CHỌN CỔ PHIẾU VÀ XÂY DỰNG", "DANH MỤC ĐẦU TƯ 10 TỶ ĐỒNG"],
    "gvhd": "TS. Nguyễn Thanh Hương",
    "lop": "FIN3002_2",
    "thanh_vien": [
        ("Nguyễn Thị Mỹ Thanh", "231124029131"),
        ("Nguyễn Công Hiếu", "231124029115"),
        ("Nguyễn Thị Bảo Na", "231124029125"),
        ("Nguyễn Bảo Anh Thư", "231124029133"),
        ("Dương Mẫn Trân", "231124029139"),
        ("Ngô Triệu Vy", "231124029144"),
    ],
    "lop_sinh_hoat": "49K29.1",
    "ngay": "Đà Nẵng, ngày 7 tháng 11 năm 2026",
}

# Phân công theo bản nhóm đã thống nhất (bản chỉnh trên Google Docs ngày 07/11/2026).
HOAT_DONG = {
    "thanh_vien": [
        ("Nguyễn Thị Mỹ Thanh", "231124029131", "Điều phối; xử lý dữ liệu, Excel và Solver (Phần 3, 4); tổng hợp báo cáo"),
        ("Dương Mẫn Trân", "231124029139", "Phân tích các yếu tố vĩ mô (mục 1.1)"),
        ("Nguyễn Thị Bảo Na", "231124029125", "Triển vọng thị trường, ngành; chiến lược đầu tư (mục 1.2, 1.3)"),
        ("Nguyễn Bảo Anh Thư", "231124029133", "Sàng lọc cổ phiếu; phân tích MBB (mục 2.1, 2.2)"),
        ("Ngô Triệu Vy", "231124029144", "Phân tích MWG (mục 2.3); tổng hợp cổ phiếu (mục 2.5)"),
        ("Nguyễn Công Hiếu", "231124029115", "Phân tích GAS (mục 2.4); lựa chọn, phân bổ danh mục (mục 4.3, 4.4)"),
    ],
    "dong_gop": "16,67%",
    "ghi_chu": ["Mức độ đóng góp do cả nhóm thống nhất: sáu thành viên đóng góp như nhau, mỗi người 1/6 "
                "(≈ 16,67%), tổng bằng 100%."],
    "nhom_truong": "Nguyễn Thị Mỹ Thanh",
}

NOI_DUNG = [
    # ============================== PHẦN 1 ==============================
    ("phan", "PHẦN 1. PHÂN TÍCH BỐI CẢNH ĐẦU TƯ"),
    ("p", "Nhóm đóng vai một công ty quản lý quỹ, nhận **10 tỷ đồng** để đầu tư vào cổ phiếu trong **1 tháng** "
          "(26/10 – 25/11/2026). Báo cáo trả lời bốn câu hỏi theo thứ tự: nền kinh tế đang thuận lợi hay khó khăn "
          "cho thị trường chứng khoán (Phần 1); nên mua cổ phiếu của công ty nào (Phần 2); mỗi cổ phiếu lời và "
          "rủi ro đến đâu (Phần 3); và nên chia 10 tỷ đồng cho từng cổ phiếu bao nhiêu (Phần 4). Cách đi từ bức "
          "tranh chung của nền kinh tế xuống ngành, rồi xuống từng công ty được gọi là phương pháp **từ trên "
          "xuống (top-down)** [39]. Số liệu và giá trong báo cáo cập nhật đến ngày 23/10/2026, thời điểm nhóm ra quyết "
          "định đầu tư."),
    ("p", "**Tóm tắt kết quả:** nhóm chọn cổ phiếu của Ngân hàng Quân đội (MBB), Thế Giới Di Động (MWG) và Tổng "
          "Công ty Khí Việt Nam (GAS), chia vốn theo tỷ lệ **56,84% – 15,20% – 27,97%**. Danh mục này có lợi nhuận "
          "kỳ vọng khoảng 10,8%/năm (khoảng 0,9%/tháng) với mức rủi ro nhóm chấp nhận được."),
    ("h2", "1.1. Đánh giá các yếu tố kinh tế vĩ mô"),
    ("p", "Giá cổ phiếu phụ thuộc vào lợi nhuận doanh nghiệp và vào mặt bằng lãi suất, nên nhóm xem xét sáu yếu "
          "tố của nền kinh tế (yếu tố **vĩ mô**) có ảnh hưởng trực tiếp đến hai điều này."),
    ("h3", "1.1.1. Tăng trưởng kinh tế"),
    ("p", "GDP (tổng giá trị hàng hóa, dịch vụ cả nước làm ra) quý III/2026 tăng **9,95%**, cao nhất kể từ năm "
          "2022. Tính chung 9 tháng, GDP tăng 9,01%; riêng công nghiệp – xây dựng tăng 12,5%. Người dân cũng chi "
          "tiêu nhiều hơn: tổng doanh thu bán lẻ 9 tháng tăng 13,4% [1], [2], [40]. **Ý nghĩa:** kinh tế tăng "
          "nhanh thì doanh nghiệp bán được nhiều hàng hơn, lợi nhuận tăng, nhu cầu vay vốn tăng. Đây là yếu tố "
          "**có lợi** cho thị trường, nhất là ngân hàng và bán lẻ."),
    ("h3", "1.1.2. Lạm phát"),
    ("p", "Lạm phát (mức tăng giá chung của hàng hóa, đo bằng chỉ số giá tiêu dùng CPI) tháng 9/2026 là **5,08%** so với cùng kỳ năm trước, "
          "**cao hơn mục tiêu 4,5%** của Chính phủ. Nguyên nhân chính là giá dầu thế giới tăng mạnh do xung đột ở "
          "Trung Đông: giá dầu Brent bình quân tháng 9 lên 114 USD/thùng. Cơ quan Thông tin Năng lượng Mỹ (EIA) "
          "dự báo giá dầu còn khoảng 105 USD trong quý IV/2026 rồi giảm về 84 USD năm 2027 [1], [3], [10]. "
          "**Ý nghĩa:** giá cả tăng làm người dân bớt mua sắm, và Nhà nước khó hạ lãi suất. Đây là yếu tố **bất lợi**."),
    ("h3", "1.1.3. Lãi suất và chính sách tiền tệ"),
    ("p", "Ngân hàng Nhà nước (NHNN) giữ nguyên lãi suất điều hành (lãi suất tái cấp vốn 4,5%, mức NHNN cho các "
          "ngân hàng vay). Tuy vậy, đầu năm 2026 các ngân hàng phải tăng lãi suất huy động thêm khoảng 1,2 điểm "
          "phần trăm vì cho vay ra nhanh hơn nhận tiền gửi vào [41]. Gần đây áp lực đã giảm: khoảng 20 ngân hàng "
          "hạ lãi suất huy động 0,5 điểm phần trăm [4], [8]. **Chính sách tiền tệ** đang **trung tính** (không "
          "nới lỏng, không thắt chặt): tín dụng cả năm được định hướng tăng khoảng 15% [6], nhưng khó hạ lãi "
          "suất thêm vì lạm phát cao. "
          "**Ý nghĩa:** khi lãi suất gửi tiết kiệm cao, nhà đầu tư đòi hỏi cổ phiếu phải sinh lời cao hơn mới "
          "chịu mua, nên giá cổ phiếu khó tăng."),
    ("h3", "1.1.4. Tỷ giá"),
    ("p", "Tỷ giá trung tâm ngày 23/10/2026 là **25.627 đồng/USD**, giảm nhẹ trong tháng, tức tiền đồng tăng giá nhẹ so với "
          "USD [7]. **Ý nghĩa:** tiền đồng ổn định giúp nhà đầu tư nước ngoài yên tâm không bị lỗ do tỷ giá, nên dễ "
          "đưa vốn vào Việt Nam. Đây là yếu tố **hỗ trợ**."),
    ("h3", "1.1.5. Diễn biến thị trường chứng khoán"),
    ("p", "VN-Index (chỉ số đo biến động giá chung của các cổ phiếu trên sàn TP.HCM) lên 1.902,93 điểm ngày "
          "13/01/2026, giảm về gần 1.600 điểm trong tháng 3, rồi lập đỉnh lịch sử 1.927,94 điểm ngày 18/05/2026 "
          "[43]. Ngày 22/10, chỉ số đóng cửa ở **1.760,63 điểm** [11], thấp hơn đỉnh khoảng 8,7%. Thị trường đang ở mức giá "
          "**rẻ hơn bình thường**: hệ số **P/E** chung (giá cổ phiếu chia cho lợi nhuận mỗi cổ phiếu, xem thêm "
          "mục 2.3.4) khoảng 13,1 lần, thấp hơn mức trung bình 5 năm là 14,4 lần [14]. Điểm sáng lớn là ngày "
          "21/09/2026, tổ chức xếp hạng quốc tế FTSE Russell đã **nâng hạng** Việt Nam lên nhóm \"thị trường mới "
          "nổi thứ cấp\". Nhờ đó, các quỹ toàn cầu đầu tư theo bộ chỉ số của FTSE sẽ phải mua cổ phiếu Việt Nam, "
          "dự kiến 3–10 tỷ USD đến năm 2027 [15], [16]. Mặt hạn chế là lượng giao dịch đã giảm khoảng 41% so với quý I, và "
          "nhà đầu tư nước ngoài vẫn bán ra nhiều hơn mua vào giữa tháng 10 [12], [13]."),
    ("p", "**Nhận xét chung.** Nền kinh tế có hai mặt trái ngược: doanh nghiệp làm ăn tốt hơn, nhưng lạm phát giữ "
          "lãi suất ở mức cao. Vì vậy cổ phiếu đáng mua là cổ phiếu của công ty **có lợi nhuận tăng thật** và "
          "**đang có giá còn rẻ**, thay vì cổ phiếu chỉ tăng nhờ kỳ vọng lãi suất giảm."),

    ("h2", "1.2. Triển vọng thị trường và triển vọng ngành"),
    ("h3", "1.2.1. Triển vọng thị trường trong thời gian đầu tư"),
    ("p", "Trong tháng đầu tư có ba sự kiện có thể làm giá biến động: các công ty công bố kết quả kinh doanh quý "
          "III, các quỹ ngoại giải ngân sau khi nâng hạng, và số liệu lạm phát tháng 10. Nhóm dự kiến ba khả năng "
          "(Bảng 1.1). Khả năng cao nhất là thị trường đi ngang, cổ phiếu tốt tăng còn cổ phiếu yếu giảm. Vì vậy "
          "nhóm ưu tiên cổ phiếu của **công ty lớn, dễ mua bán** và **có kết quả kinh doanh quý III tốt**."),
    ("bang", "1.1", "Ba kịch bản cho VN-Index đến ngày 25/11/2026",
     [("Kịch bản", "VN-Index (điểm)", "Điều kiện xảy ra", "Khả năng (nhận định)"),
      ("Tích cực", "1.850 – 1.900", "Kết quả quý III tốt, quỹ ngoại mua vào, giá dầu hạ", "30%"),
      ("Cơ sở", "1.720 – 1.820", "Kết quả quý III đúng dự kiến, lãi suất đi ngang", "50%"),
      ("Tiêu cực", "1.620 – 1.680", "Lạm phát vượt 5,5%, Nhà nước thắt chặt tiền tệ, xung đột leo thang", "20%")],
     [2.2, 2.8, 8.6, 2.9], (3,), "Nhóm nhận định dựa trên [1], [10], [13], [15]."),
    ("h3", "1.2.2. Triển vọng ngành"),
    ("p", "Nhóm so sánh năm ngành để tìm ngành **sẽ còn tăng trưởng trong tương lai**, không chỉ tốt trong lúc này "
          "(Bảng 1.2) [6], [35], [37]."),
    ("bang", "1.2", "Đánh giá triển vọng các ngành ứng viên",
     [("Ngành", "Vì sao sẽ tăng trưởng", "Rủi ro chính", "Kết luận"),
      ("Ngân hàng", "Kinh tế tăng gần 10% thì doanh nghiệp và người dân vay nhiều hơn (dư nợ cả năm dự kiến tăng "
       "15–18%); khung pháp lý xử lý nợ xấu được hoàn thiện; ngân hàng chiếm tỷ trọng lớn nhất trong VN-Index "
       "nên hưởng lợi trước từ dòng vốn ngoại sau nâng hạng", "Chi phí huy động vốn tăng", "Chọn"),
      ("Bán lẻ", "Dân số trẻ, thu nhập tăng, bán lẻ 9 tháng +13,4%; người dân chuyển dần từ chợ sang chuỗi cửa hàng",
       "Lạm phát làm giảm sức mua", "Chọn"),
      ("Khí đốt, năng lượng", "Kinh tế tăng thì cần nhiều điện; nhà máy điện khí LNG là trụ cột của Quy hoạch "
       "điện VIII đến 2030; giá dầu cao làm giá bán khí cao", "Giá dầu giảm trở lại", "Chọn"),
      ("Thép", "Hưởng lợi từ đầu tư xây dựng", "Sắp dư cung: nhà máy mới có thể thêm khoảng 8 triệu tấn thép đến 2029", "Không chọn"),
      ("Công nghệ", "Chuyển đổi số, trí tuệ nhân tạo", "Lo ngại AI làm giảm nhu cầu gia công phần mềm", "Theo dõi")],
     [2.6, 7.4, 4.4, 2.1], (), "Nhóm tổng hợp từ [1], [6], [10], [35], [37], [40]."),
    ("p", "**Ý nghĩa:** ba ngành được chọn đều có lý do tăng trưởng lâu dài. Điều quan trọng hơn là chúng **phản "
          "ứng khác nhau** trước cùng một biến cố: giá dầu tăng thì bán lẻ gặp khó (người dân chi tiêu ít đi) "
          "nhưng ngành khí lại có lợi. Nhờ vậy, khi một cổ phiếu giảm giá, cổ phiếu khác chưa chắc giảm theo."),
    ("p", "**Trong tháng đầu tư**, ngân hàng vào mùa công bố kết quả quý III và được vốn ngoại ưu tiên sau nâng "
          "hạng; bán lẻ vào mùa mua sắm cuối năm; ngành khí vẫn được hỗ trợ vì giá dầu Brent quý IV dự báo còn "
          "khoảng 105 USD/thùng [10]."),
    ("h2", "1.3. Chiến lược đầu tư của nhóm"),
    ("p", "Có năm phong cách đầu tư phổ biến: **tăng trưởng** (mua công ty có lợi nhuận tăng nhanh), **giá trị** (mua công ty "
          "tốt đang bị định giá rẻ), **thu nhập cổ tức** (mua công ty trả nhiều cổ tức tiền mặt cho cổ đông), "
          "**phòng thủ** (mua công ty ít bị ảnh hưởng khi kinh tế xấu) và **cân bằng** (kết hợp các phong cách). "
          "Nhóm chọn **chiến lược cân bằng**: MBB đại diện cho phong cách giá trị, MWG cho tăng trưởng, GAS cho thu "
          "nhập cổ tức và đa dạng hóa. Lý do là nền kinh tế có cả mặt tốt lẫn mặt xấu, nên không nên đặt cược hết "
          "vào một kịch bản. Nguyên tắc này giống câu \"không bỏ hết trứng vào một giỏ\", và được chứng minh bằng "
          "mô hình Markowitz ở Phần 4 [44]. Ban đầu nhóm dự kiến chia vốn 40% MBB, 35% MWG, 25% GAS; tỷ lệ cuối "
          "cùng được tính lại bằng phương pháp tối ưu ở Phần 4."),

    # ============================== PHẦN 2 ==============================
    ("phan", "PHẦN 2. PHÂN TÍCH CỔ PHIẾU"),
    ("h2", "2.1. Tiêu chí lựa chọn cổ phiếu và cách định giá"),
    ("p", "Nhóm chọn cổ phiếu theo năm tiêu chí: (1) công ty lớn, niêm yết trên sàn TP.HCM (HOSE), dễ mua bán; "
          "(2) lợi nhuận năm 2026 tăng trên 10%; (3) giá cổ phiếu **ổn định**, không nằm trong xu hướng giảm kéo dài; (4) giá không "
          "đắt hơn mức bình thường trong quá khứ; (5) có đủ dữ liệu giá để đo lợi nhuận và rủi ro. Bảng 2.1 dùng "
          "hai chữ viết tắt: **LNTT** là lợi nhuận trước thuế, **LNST** là lợi nhuận sau thuế."),
    ("bang", "2.1", "Kết quả sàng lọc cổ phiếu ứng viên",
     [("Mã", "Lợi nhuận gần nhất", "Diễn biến giá", "Kết quả"),
      ("MBB", "LNTT 6 tháng +27,1%", "Đi ngang so với đầu năm", "Đạt"),
      ("MWG", "LNST 6 tháng +88%", "Giảm khoảng 12% từ đầu năm; đã hồi từ 72.400 đ (30/9) lên 75.500 đ (23/10)", "Đạt"),
      ("GAS", "LNTT 9 tháng +31%", "Dao động 76.000 – 82.000 đ trong tháng 10", "Đạt"),
      ("HPG", "LNST quý II +51%", "Giảm 12% từ đầu năm, 16 quỹ bán ra liên tục 4 tháng", "Loại"),
      ("FPT", "LNST 9 tháng +13,3%", "Giảm từ khoảng 98.000 đ đầu năm còn 57.400 đ", "Loại")],
     [1.5, 3.8, 9.1, 2.1], (), "Nhóm tổng hợp từ [17], [24], [28], [35], [36], [37]."),
    ("p", "HPG và FPT vẫn lãi tăng nhưng giá đang giảm kéo dài, chưa có dấu hiệu dừng [35], [37]. Trong 1 tháng, "
          "nhóm không có căn cứ cho rằng giá sẽ quay đầu tăng, nên loại hai mã này."),
    ("p", "**Vì sao vẫn chọn MBB và MWG dù giá một năm qua giảm?** Lợi nhuận hai công ty vẫn tăng mạnh (+27,1% "
          "và +88%) trong khi giá giảm, nên cổ phiếu **rẻ đi** chứ không phải công ty **xấu đi** (mục 2.2.4, "
          "2.3.4). Giá cũng đã ngừng giảm: MBB đi ngang quanh 19.600 – 20.600 đ suốt tháng 9, MWG đang hồi lại "
          "[43], trong khi HPG gần 5 tháng không có xu hướng tăng [36]."),
    ("p", "**Cách xác định giá hợp lý.** Một cổ phiếu đáng mua khi giá thị trường thấp hơn **giá hợp lý** (giá trị "
          "thật ước tính từ khả năng sinh lời của công ty). Để tính giá hợp lý, trước hết cần biết nhà đầu tư đòi "
          "hỏi lợi nhuận tối thiểu bao nhiêu, ký hiệu **k**. Theo mô hình định giá tài sản vốn **CAPM** (Chương 3) [45], "
          "mức này bằng lãi suất an toàn cộng với phần thưởng cho việc chấp nhận rủi ro:"),
    ("ct", "k = R_{f} + β × [E(R_{M}) − R_{f}]", "2.1"),
    ("p", "Trong đó R_{f} = 4,36% là **lãi suất phi rủi ro** (lợi suất trái phiếu Chính phủ 10 năm, vì Nhà nước "
          "gần như chắc chắn trả đủ gốc và lãi) [5]. E(R_{M}) − R_{f} là phần lợi nhuận thị trường cổ phiếu trả thêm so với "
          "trái phiếu, nhóm giả định bằng 8%. **β** đo mức độ cổ phiếu biến động theo thị trường: β = 1 nghĩa là "
          "cổ phiếu lên xuống cùng mức với VN-Index, β > 1 là biến động mạnh hơn. Ở Phần 2, nhóm dùng β giả "
          "định theo đặc điểm ngành (MBB 1,1; MWG 1,2; GAS 0,8), cao hơn β đo từ dữ liệu ở Phần 3 (0,79; 1,06; "
          "0,62) để định giá thận trọng. Giá hiện tại là giá đóng cửa ngày 23/10/2026: MBB 19.800 đ, MWG 75.500 đ, "
          "GAS 78.300 đ [43]."),

    ("h2", "2.2. Ngân hàng TMCP Quân đội (MBB – HOSE)"),
    ("h3", "2.2.1. Mô hình kinh doanh"),
    ("p", "Ngân hàng Quân đội (gọi tắt là MB, mã cổ phiếu MBB) kiếm tiền chủ yếu từ **chênh lệch lãi suất**: nhận tiền gửi của khách hàng với lãi suất thấp, rồi cho "
          "vay với lãi suất cao hơn. Lợi thế của MB là ứng dụng ngân hàng số gần 40 triệu khách hàng. Ứng dụng này "
          "giúp MB có nhiều tiền gửi không kỳ hạn (tiền khách để trong tài khoản thanh toán), loại tiền gửi mà "
          "ngân hàng chỉ phải trả lãi rất thấp. Ngoài ra, MB sở hữu công ty chứng khoán MBS, công ty tài chính tiêu "
          "dùng MCredit, công ty bảo hiểm và ngân hàng MBV [20]."),
    ("h3", "2.2.2. Kết quả kinh doanh và tình hình tài chính"),
    ("bang", "2.2", "Kết quả kinh doanh chính của MBB",
     [("Chỉ tiêu", "Năm 2025", "6 tháng 2026", "Tăng so với cùng kỳ"),
      ("LNTT (tỷ đồng)", "34.268", "20.188", "+18,9% / +27,1%"),
      ("Thu nhập từ cho vay sau khi trừ chi phí lãi (tỷ đồng)", "–", "31.807", "+32,2%"),
      ("Dư nợ cho vay (nghìn tỷ đồng)", "–", "1.256", "+13% so với đầu năm"),
      ("Tỷ lệ nợ xấu (khoản vay khó đòi)", "1,29%", "1,40%", "Đã trích lập dự phòng 93,6%"),
      ("Kế hoạch LNTT năm 2026 (tỷ đồng)", "", "39.500", "Đã đạt 51,1% sau 6 tháng")],
     [6.4, 2.2, 2.5, 5.4], (1, 2), "Nhóm tổng hợp từ [17], [18]."),
    ("p", "**Ý nghĩa:** MB đang đi nhanh hơn kế hoạch một chút: mới qua nửa năm đã đạt 51,1% chỉ tiêu lợi nhuận cả "
          "năm [17], [18]. Chỉ số "
          "**ROE** (lợi nhuận trên vốn chủ sở hữu, tức mỗi 100 đồng vốn của cổ đông tạo ra bao nhiêu đồng lãi mỗi "
          "năm) của MB khoảng 20–21%, thuộc nhóm cao nhất ngành ngân hàng [18], [21]."),
    ("h3", "2.2.3. Chính sách cổ tức, rủi ro và triển vọng tăng trưởng"),
    ("p", "**Cổ tức** (phần lợi nhuận công ty chia cho cổ đông): năm 2026 MB chia 10% bằng tiền (1.000 đ/cổ phiếu) "
          "và 15% bằng cổ phiếu; MB còn cho cổ đông quyền mua thêm cổ phiếu giá 10.000 đ (cứ 10 cổ phiếu được mua 1) "
          "để tăng vốn [21]. Phần tiền mặt tương đương **5,1%** giá cổ phiếu. "
          "**Rủi ro:** chênh lệch lãi suất cho vay và huy động đang bị thu hẹp vì ngân hàng phải trả lãi tiền gửi "
          "cao hơn [20]; Kiểm toán Nhà nước ghi nhận nợ có khả năng mất vốn năm 2025 tăng 39,4%, lên 6.421 tỷ đồng "
          "[19]. **Triển vọng:** hưởng lợi trực tiếp khi kinh tế tăng trưởng làm nhu cầu vay vốn tăng, và khi quỹ "
          "ngoại mua cổ phiếu ngân hàng lớn sau nâng hạng."),
    ("h3", "2.2.4. Nhận định về mức giá hợp lý"),
    ("p", "Với ngân hàng, cách định giá phổ biến là so giá cổ phiếu với **giá trị sổ sách**, tức phần vốn thực có "
          "của ngân hàng tính trên mỗi cổ phiếu (MBB: 19.462 đ) [22]. Tỷ số giữa hai con số này gọi là **P/B** (P/B = giá cổ phiếu / giá trị sổ sách mỗi cổ "
          "phiếu). "
          "P/B = 1 nghĩa là nhà đầu tư đang mua cổ phiếu đúng bằng giá trị vốn thực có. Ngân hàng có ROE càng cao "
          "thì càng đáng được trả P/B cao. Mức P/B \"đáng có\" được suy ra từ mô hình định giá theo cổ tức "
          "V_{0} = D_{1}/(k − g) ở Chương 4, với g = ROE × b (b: tỷ lệ lợi nhuận giữ lại):"),
    ("ct", "P/B hợp lý = (ROE − g) / (k − g)", "2.2"),
    ("p", "Trong đó g là tốc độ tăng trưởng lợi nhuận lâu dài, và k = 4,36% + 1,1 × 8% = 13,16% theo công thức "
          "(2.1). Giá trị mỗi cổ phiếu = P/B hợp lý × 19.462 đ. Nhóm tính ba kịch bản (Bảng 2.3)."),
    ("bang", "2.3", "Định giá MBB theo P/B hợp lý",
     [("Kịch bản", "ROE lâu dài", "Tăng trưởng g", "P/B hợp lý", "Giá trị (đ/cổ phiếu)"),
      ("Thận trọng", "15%", "6%", "1,26", "24.500"),
      ("Cơ sở", "17%", "6%", "1,54", "29.900"),
      ("Lạc quan", "20%", "7%", "2,11", "41.100")],
     [3.2, 3.0, 3.0, 3.0, 4.3], (1, 2, 3, 4), "Nhóm tính toán."),
    ("p", "**Ý nghĩa:** MBB đang đạt ROE khoảng 20% nhưng chỉ được trả P/B 1,02 (= 19.800 / 19.462). Theo công "
          "thức (2.2), thị trường đang định giá MBB như một ngân hàng chỉ đạt ROE khoảng 13%. Giá đang thấp hơn chất lượng thật, vì nhà đầu tư "
          "lo ngại nợ xấu. Do chưa loại trừ được rủi ro này, nhóm chọn kịch bản gần thận trọng: **giá hợp lý "
          "25.000 đ, cao hơn giá hiện tại 26%** (= 25.000 / 19.800 − 1), thấp hơn mức "
          "26.700 đ của công ty phân tích FUNAN [20]."),

    ("h2", "2.3. CTCP Đầu tư Thế Giới Di Động (MWG – HOSE)"),
    ("h3", "2.3.1. Mô hình kinh doanh"),
    ("p", "Thế Giới Di Động (mã MWG) là công ty bán lẻ lớn nhất Việt Nam, gồm ba mảng: (1) chuỗi **Thế Giới Di Động** và **Điện Máy "
          "Xanh** bán điện thoại, điện máy (khoảng 3.000 cửa hàng), mang lại dòng tiền ổn định; (2) chuỗi **Bách "
          "Hóa Xanh** bán thực phẩm, hàng tiêu dùng (hơn 2.100 cửa hàng), bắt đầu có lãi từ 2025 và là mảng tăng "
          "trưởng chính; (3) chuỗi **EraBlue** ở Indonesia [26], [42]. Lợi thế của MWG là quy mô lớn, nên mua hàng "
          "được giá tốt và vận chuyển hiệu quả hơn đối thủ."),
    ("h3", "2.3.2. Kết quả kinh doanh và tình hình tài chính"),
    ("bang", "2.4", "Kết quả kinh doanh chính của MWG",
     [("Chỉ tiêu (tỷ đồng)", "Năm 2024", "Năm 2025", "Năm 2026"),
      ("Doanh thu", "134.341", "156.457 (+16,5%)", "9 tháng: 147.953 (+30%)"),
      ("LNST", "3.733", "7.075 (+89,5%)", "6 tháng: 6.017 (+88%)"),
      ("Kế hoạch năm 2026", "", "", "Doanh thu 185.000; LNST 9.200 (+30%)")],
     [3.7, 2.4, 3.7, 6.7], (1,), "Nhóm tổng hợp từ [23], [24], [26]."),
    ("p", "**Ý nghĩa:** lợi nhuận MWG gần như **tăng gấp đôi** trong năm 2025 [23], [24] và tiếp tục tăng mạnh năm 2026. Riêng "
          "quý III/2026 doanh thu tăng 32%, Bách Hóa Xanh tăng 34% [24], [25]. Về tài chính, MWG đủ tiền mặt "
          "để chi khoảng 3.000 tỷ đồng trả cổ tức năm 2026, mức cao nhất từ trước đến nay, trong khi lợi nhuận "
          "vẫn tăng mạnh; điều này cho thấy tình hình tài chính lành mạnh [26]."),
    ("h3", "2.3.3. Chính sách cổ tức, rủi ro và triển vọng tăng trưởng"),
    ("p", "**Cổ tức:** năm 2026 MWG chi khoảng 3.000 tỷ đồng tiền mặt, mức cao nhất từ trước đến nay, "
          "tương đương khoảng 2.000 đ/cổ phiếu (**2,6%** giá cổ phiếu) [26]. **Rủi ro:** các nhà đầu tư khác đang sở "
          "hữu khoảng 14% công ty Điện Máy Xanh, nên từ quý III MWG phải chia phần lợi nhuận tương ứng cho họ "
          "[25]; lạm phát có thể làm người dân hoãn mua điện thoại, điện máy. **Triển vọng:** Bách Hóa Xanh tiếp tục "
          "mở rộng; Điện Máy Xanh dự kiến lên sàn chứng khoán (IPO), giúp thị trường định giá lại các mảng của MWG."),
    ("h3", "2.3.4. Nhận định về mức giá hợp lý"),
    ("p", "Với công ty đang tăng trưởng, nhóm dùng hệ số **P/E** (giá cổ phiếu chia cho lợi nhuận mỗi cổ phiếu, "
          "**EPS**). P/E cho biết nhà đầu tư sẵn sàng trả bao nhiêu đồng cho 1 đồng lợi nhuận mỗi năm của công "
          "ty. Giá hợp lý = P/E chuẩn × EPS dự kiến. EPS năm 2026 của MWG ước khoảng 6.000 đ (từ kế hoạch lợi "
          "nhuận), nên với giá 75.500 đ, nhà đầu tư đang trả 75.500 / 6.000 "
          "≈ 12,6 đồng cho 1 đồng lợi nhuận, thấp hơn mức thường thấy của MWG là khoảng 17 [27]. Nhóm chọn P/E chuẩn **15** (thấp hơn 17 để trừ hao rủi ro lợi nhuận năm 2027 chững lại):"),
    ("ct", "Giá hợp lý = P/E chuẩn × EPS = 15 × 6.000 = 90.000 đ", "2.3"),
    ("p", "**Ý nghĩa:** giá hợp lý **cao hơn giá hiện tại 19%**. Mức 15 lần cũng hợp lý theo công thức P/E = "
          "(tỷ lệ chia cổ tức)/(k − g) ở Chương 4: với k = 4,36% + 1,2 × 8% = 13,96% và tỷ lệ chia cổ tức 33%, "
          "P/E 15 tương ứng lợi nhuận tăng khoảng 11,8%/năm trong dài hạn, thấp hơn nhiều so với mức tăng +88% "
          "hiện nay, nên không quá lạc quan. Các công ty chứng khoán đưa ra giá mục tiêu từ 94.400 đến 109.000 đ [27]."),

    ("h2", "2.4. Tổng Công ty Khí Việt Nam (GAS – HOSE)"),
    ("h3", "2.4.1. Mô hình kinh doanh"),
    ("p", "PV GAS (mã GAS) là đơn vị chủ lực của ngành khí Việt Nam: đưa khí đốt từ mỏ ngoài biển vào bờ bằng đường ống, xử "
          "lý và bán cho nhà máy điện, nhà máy phân bón. PV GAS còn kinh doanh **LPG** (khí hóa lỏng dùng nấu ăn, "
          "thường gọi là gas bình) và nhập khẩu **LNG** (khí thiên nhiên hóa lỏng, nhiên liệu cho nhà máy điện "
          "khí) [31]. Giá bán khí được tính theo giá dầu, nên **giá dầu tăng thì lợi nhuận PV GAS tăng**."),
    ("h3", "2.4.2. Kết quả kinh doanh và tình hình tài chính"),
    ("bang", "2.5", "Kết quả kinh doanh chính của GAS",
     [("Chỉ tiêu", "Năm 2025", "9 tháng 2026"),
      ("Doanh thu (tỷ đồng)", "135.129 (+30%)", "Trên 120.900 (+30%)"),
      ("Lợi nhuận (tỷ đồng)", "LNST 11.571 (+9%)", "LNTT trên 16.600 (+31%); quý III +68%"),
      ("So với kế hoạch năm", "", "Đạt 197% kế hoạch lợi nhuận"),
      ("Tiền mặt và tiền gửi ngắn hạn", "Gần 40.000 tỷ đồng", "")],
     [5.4, 4.6, 6.5], (), "Nhóm tổng hợp từ [28], [29], [30]."),
    ("p", "**Ý nghĩa:** chỉ sau 9 tháng, PV GAS đã đạt gần **gấp đôi** kế hoạch lợi nhuận cả năm nhờ giá dầu cao [28], [29]. "
          "Công ty có gần 40.000 tỷ đồng tiền mặt nên gần như không có rủi ro thiếu tiền [30]."),
    ("h3", "2.4.3. Chính sách cổ tức, rủi ro và triển vọng tăng trưởng"),
    ("p", "**Cổ tức:** PV GAS chia cổ tức tiền mặt đều đặn nhiều năm; năm 2025 chia 2.500 đ/cổ phiếu, bằng **3,2%** "
          "giá cổ phiếu [33]. **Rủi ro:** giá dầu có thể giảm trở lại [10]; giá nhập khẩu gas tăng làm lãi mảng LPG "
          "giảm [31]. "
          "Ngoài ra, Tập đoàn Dầu khí Việt Nam (PVN) nắm 95,76% cổ phần, trong khi luật yêu cầu cổ đông nhỏ phải "
          "nắm ít nhất 10%. PV GAS có 1 năm từ 14/08/2026 để khắc phục, nếu không có thể bị hủy tư cách công ty "
          "đại chúng [32]; rủi ro này khó xảy ra trong 1 tháng đầu tư. **Triển vọng:** nhu cầu khí cho phát điện tăng theo quy hoạch điện đến 2030."),
    ("h3", "2.4.4. Nhận định về mức giá hợp lý"),
    ("p", "Vì PV GAS chia cổ tức đều, nhóm dùng **mô hình chiết khấu cổ tức** (Chương 4): giá trị cổ phiếu bằng "
          "tổng giá trị hôm nay của các khoản cổ tức nhận được trong tương lai. Giả sử cổ tức tăng đều g = 7%/năm, "
          "với k = 4,36% + 0,8 × 8% = 10,76% (V_{0}: giá trị hợp lý hôm nay; D_{0} = 2.500 đ: cổ tức gần nhất):"),
    ("ct", "V_{0} = D_{0}(1 + g) / (k − g) = 2.500 × 1,07 / (0,1076 − 0,07) = 71.100 đ", "2.4"),
    ("p", "Theo cách P/E (EPS khoảng 5.350 đ, P/E chuẩn 16), giá trị là 85.600 đ, gần mức giá mục tiêu bình quân 87.300 đ "
          "của bảy công ty phân tích [34]. Lấy trung bình hai cách, "
          "**giá hợp lý khoảng 78.400 đ**, gần đúng bằng giá hiện tại 78.300 đ. **Ý nghĩa:** GAS không bị định "
          "giá rẻ, nên nhóm không mua GAS để chờ tăng giá. Nhóm mua GAS vì cổ tức đều và vì GAS **lên xuống khác "
          "nhịp** với MBB và MWG, giúp giảm rủi ro chung (Phần 3, 4 chứng minh điều này bằng số liệu)."),

    ("h2", "2.5. Tổng hợp ba cổ phiếu"),
    ("hinh", "2.1", "Vùng giá hợp lý của MBB, MWG, GAS so với giá hiện tại (dải mờ: vùng giá trị theo cách định "
     "giá của nhóm và giá mục tiêu của công ty phân tích; chấm: mức nhóm chọn)", "hinh_2_1_vung_gia_hop_ly.png", "Nhóm tính toán."),
    ("bang", "2.6", "So sánh ba cổ phiếu được chọn",
     [("Tiêu chí", "MBB", "MWG", "GAS"),
      ("Ngành", "Ngân hàng", "Bán lẻ", "Khí đốt, năng lượng"),
      ("Giá 23/10/2026", "19.800 đ", "75.500 đ", "78.300 đ"),
      ("Tăng trưởng lợi nhuận", "+27,1% (LNTT 6 tháng)", "+88% (LNST 6 tháng)", "+31% (LNTT 9 tháng)"),
      ("Tỷ suất cổ tức tiền mặt gần nhất", "5,1%", "2,6%", "3,2%"),
      ("Giá hợp lý (chênh lệch)", "25.000 đ (+26%)", "90.000 đ (+19%)", "78.400 đ (≈ 0%)"),
      ("Vai trò trong danh mục", "Giá trị", "Tăng trưởng", "Đa dạng hóa, cổ tức"),
      ("Rủi ro lớn nhất", "Nợ xấu", "Lợi nhuận 2027 chững lại", "Giá dầu giảm")],
     [4.1, 4.1, 4.1, 4.2], (), "Nhóm tổng hợp và tính toán."),
    ("p", "Lưu ý: cổ tức gần nhất của ba mã đã chốt danh sách nhận trước kỳ đầu tư [33], [43], nên chỉ dùng để "
          "đánh giá chính sách chi trả, không tính vào lợi nhuận tháng."),

    # ============================== PHẦN 3 ==============================
    ("phan", "PHẦN 3. PHÂN TÍCH RỦI RO VÀ LỢI NHUẬN"),
    ("p", "Phần 3 dùng **dữ liệu giá thực tế trong một năm** để đo mỗi cổ phiếu sinh lời bao nhiêu và giá của nó "
          "lên xuống mạnh đến mức nào."),
    ("h2", "3.1. Dữ liệu và cách xử lý"),
    ("p", "Nhóm lấy giá đóng cửa từng ngày của MBB, MWG, GAS và VN-Index từ trang CafeF, giai đoạn 01/10/2025 – "
          "30/09/2026 [43]. Có hai điểm cần xử lý:"),
    ("abc", ["**Dùng giá điều chỉnh, không dùng giá thô.** Khi công ty chia cổ tức bằng cổ phiếu, giá cổ phiếu tự "
             "giảm xuống tương ứng, dù nhà đầu tư không mất tiền vì nhận thêm cổ phiếu. Ví dụ, ngày 11/08/2026 MBB "
             "chia cổ tức 15% bằng cổ phiếu, đồng thời cho quyền mua cổ phiếu giá 10.000 đ (tỷ lệ 10:1): giá thô giảm từ 24.250 đ xuống 20.350 đ (−16%). **Giá điều chỉnh** "
             "đã tính lại giá các ngày trước để loại bỏ bước giảm \"giả\" này; theo giá điều chỉnh, MBB hôm đó "
             "thực ra tăng 0,7%.",
             "**Chỉ giữ những ngày có đủ giá của cả ba mã.** CafeF thiếu giá ba cổ phiếu ngày 29 và 30/01/2026 nên "
             "hai ngày này bị bỏ; lợi tức ngày 02/02/2026 vì vậy tính gộp cho ba phiên. Dữ liệu còn **246 ngày giao "
             "dịch**."]),
    ("hinh", "3.1", "Diễn biến giá điều chỉnh của MBB, MWG, GAS và VN-Index (giá ngày 01/10/2025 = 100)",
     "hinh_3_1_dien_bien_gia.png", "Nhóm tính toán từ dữ liệu CafeF [43]."),
    ("p", "**Cách đọc Hình 3.1:** giá mỗi mã được quy về 100 tại ngày đầu. Sau một năm, 100 đồng vào GAS thành "
          "139 đồng, vào VN-Index thành 106 đồng, vào MBB và MWG chỉ còn 93 và 95 đồng. Đường của GAS gồ ghề nhất, "
          "tức giá GAS lên xuống mạnh nhất."),
    ("h2", "3.2. Phương pháp tính"),
    ("p", "**Tỷ suất lợi tức ngày** là phần trăm lãi (hoặc lỗ) nếu mua ở phiên trước, bán ở phiên sau. Với P_{t} là giá "
          "điều chỉnh ngày t:"),
    ("ct", "R_{t} = (P_{t} − P_{t−1}) / P_{t−1}", "3.1"),
    ("p", "Từ 245 tỷ suất lợi tức ngày, nhóm tính hai chỉ tiêu. **Tỷ suất lợi tức kỳ vọng** E(R) là mức lãi trung "
          "bình mỗi ngày, dùng để ước đoán lợi nhuận trong tương lai. **Độ lệch chuẩn** σ đo mức lợi tức hằng ngày "
          "dao động quanh mức trung bình. Đây là thước đo **rủi ro**: σ càng lớn, giá càng lên xuống thất thường."),
    ("ct", "E(R) = (1/n) × Σ R_{t};     σ = √[ Σ (R_{t} − E(R))^{2} / (n − 1) ],  với n = 245", "3.2"),
    ("p", "Để biết hai cổ phiếu có lên xuống cùng lúc hay không, nhóm tính **hiệp phương sai** (Cov) và **hệ số "
          "tương quan** (ρ). Hệ số tương quan nằm từ −1 đến +1: ρ = +1 là hai mã luôn tăng giảm cùng nhau; ρ = 0 là "
          "hai mã không có xu hướng tăng giảm cùng nhau; ρ âm là thường đi ngược chiều."),
    ("ct", "Cov(R_{i}, R_{j}) = Σ (R_{i,t} − E(R_{i}))(R_{j,t} − E(R_{j})) / (n − 1);     ρ_{ij} = Cov(R_{i}, R_{j}) / (σ_{i}σ_{j})", "3.3"),
    ("p", "Số liệu theo ngày rất nhỏ và khó hình dung, nên nhóm quy đổi sang **theo năm**, với 1 năm khoảng 250 "
          "ngày giao dịch: E(R)_{năm} = E(R)_{ngày} × 250; σ_{năm} = σ_{ngày} × √250; Cov_{năm} = Cov_{ngày} × 250 (hệ số tương quan không đổi khi quy đổi). Ngoài ra, nhóm tính hệ số "
          "β thực tế: β_{i} = Cov(R_{i}, R_{M}) / σ^{2}_{M}, với R_{M} là lợi tức của VN-Index. Mọi phép tính được "
          "thực hiện bằng công thức trong file Excel nộp kèm."),
    ("h2", "3.3. Tỷ suất lợi tức kỳ vọng và độ lệch chuẩn"),
    ("bang", "3.1", "Lợi tức kỳ vọng, rủi ro và hệ số β của từng cổ phiếu",
     [("Chỉ tiêu", "MBB", "MWG", "GAS", "VN-Index"),
      ("Lợi tức kỳ vọng E(R) – ngày", "−0,015%", "0,003%", "0,184%", "0,033%"),
      ("Độ lệch chuẩn σ – ngày", "1,710%", "2,258%", "3,140%", "1,327%"),
      ("Lợi tức kỳ vọng E(R) – năm", "−3,82%", "0,70%", "46,01%", "8,37%"),
      ("Độ lệch chuẩn σ – năm", "27,04%", "35,70%", "49,65%", "20,99%"),
      ("Lãi/lỗ thực tế cả năm (giá cuối / giá đầu − 1)", "−7,05%", "−5,37%", "+39,24%", "+6,22%"),
      ("Hệ số β", "0,79", "1,06", "0,62", "1,00")],
     [5.0, 2.8, 2.8, 2.8, 3.1], (1, 2, 3, 4), "Nhóm tính toán trên Excel (trang Thống kê)."),
    ("p", "**Ý nghĩa:**"),
    ("gach", ["**GAS lãi nhiều nhất nhưng cũng rủi ro nhất.** σ năm của GAS là 49,65%, nghĩa là trong một năm bình "
              "thường, lợi tức của GAS có thể lệch khỏi mức trung bình khoảng ±50%. Nguyên nhân là giá dầu biến động "
              "mạnh khiến giá GAS nhiều ngày tăng hoặc giảm kịch biên độ 7% cho phép.",
              "**MBB ít rủi ro nhất** (σ = 27,04%) nhưng lợi tức trung bình hơi âm. **MWG ở giữa.**",
              "**Tài sản bị thống trị** là tài sản vừa lãi ít hơn, vừa rủi ro cao hơn một tài sản hoặc danh mục khác. "
              "So từng cặp cổ phiếu thì không mã nào bị thống trị. Nhưng MBB và MWG đứng riêng đều bị danh mục rủi "
              "ro thấp nhất ở Phần 4 (lãi 6,20%, rủi ro 24,51%) thống trị. Nhóm vẫn giữ hai mã này vì chúng giúp cả "
              "danh mục giảm rủi ro (Phần 4), và vì Phần 2 cho thấy cả hai đang rẻ hơn giá hợp lý.",
              "**Cần thận trọng với con số 46%/năm của GAS:** kết quả này có được chủ yếu nhờ một đợt giá dầu tăng "
              "đột biến, khó lặp lại. Lợi tức tính từ dữ liệu một năm chỉ là ước lượng của quá khứ, còn giá hợp lý ở Phần 2 là nhận định "
              "cho tương lai.",
              "**Hệ số β thực tế** (MBB 0,79; MWG 1,06; GAS 0,62) **thấp hơn** mức giả định ở Phần 2, nên theo "
              "(2.1) giá hợp lý ở Phần 2 là **ước tính thận trọng**. GAS có β thấp nhất dù σ cao nhất vì rủi ro "
              "của GAS chủ yếu đến từ giá dầu, không đi cùng nhịp thị trường chung."]),
    ("h2", "3.4. Hiệp phương sai và hệ số tương quan"),
    ("bang", "3.2", "Ma trận hiệp phương sai (theo năm) và hệ số tương quan giữa các cổ phiếu",
     [("", "Cov: MBB", "Cov: MWG", "Cov: GAS", "ρ: MBB", "ρ: MWG", "ρ: GAS"),
      ("MBB", "0,0731", "0,0568", "0,0163", "1,000", "0,588", "0,121"),
      ("MWG", "0,0568", "0,1274", "0,0197", "0,588", "1,000", "0,111"),
      ("GAS", "0,0163", "0,0197", "0,2465", "0,121", "0,111", "1,000")],
     [1.9, 2.4, 2.4, 2.4, 2.4, 2.4, 2.6], (1, 2, 3, 4, 5, 6),
     "Nhóm tính toán trên Excel (trang Hiệp phương sai). Ô trên đường chéo của ma trận hiệp phương sai là phương "
     "sai σ^{2} của chính cổ phiếu đó."),
    ("p", "**Ý nghĩa:** MBB và MWG có tương quan 0,59: hai mã thường tăng giảm cùng lúc vì cùng phụ thuộc vào kinh "
          "tế trong nước. GAS gần như **không liên quan** đến hai mã còn lại (ρ chỉ 0,11 – 0,12) vì chịu tác động "
          "chủ yếu của giá dầu. Đây là phát hiện quan trọng nhất của Phần 3: trong 89 ngày MBB và MWG cùng giảm "
          "(trung bình −1,37% và −1,74%), GAS chỉ giảm trung bình 0,24%, nên GAS giúp \"đệm\" cho cả danh mục, "
          "đúng như nhận định ở Phần 1."),

    # ============================== PHẦN 4 ==============================
    ("phan", "PHẦN 4. XÂY DỰNG DANH MỤC ĐẦU TƯ"),
    ("h2", "4.1. Phương pháp Markowitz và cách thực hiện trên Excel"),
    ("p", "**Danh mục đầu tư** là cách chia vốn cho nhiều cổ phiếu. Gọi w_{i} là **tỷ trọng** (phần trăm vốn) dành "
          "cho cổ phiếu i. Lợi nhuận kỳ vọng của danh mục là trung bình có trọng số của lợi nhuận từng mã. Rủi ro "
          "của danh mục thì phức tạp hơn, vì phụ thuộc vào việc các mã có lên xuống cùng nhau hay không, tức phụ "
          "thuộc vào hiệp phương sai ở Phần 3 [44]:"),
    ("ct", "E(R_{p}) = Σ w_{i}E(R_{i});     σ^{2}_{p} = Σ_{i} Σ_{j} w_{i}w_{j}Cov(R_{i}, R_{j})", "4.1"),
    ("p", "Công thức thứ hai cho thấy vì sao đa dạng hóa có tác dụng: khi các cổ phiếu tương quan thấp, rủi ro của "
          "danh mục **thấp hơn** trung bình rủi ro của từng mã. **Mô hình Markowitz** tìm cách chia vốn sao cho với "
          "mỗi mức lợi nhuận mong muốn, rủi ro là thấp nhất."),
    ("p", "Danh mục phải thỏa hai điều kiện: tổng tỷ trọng bằng 100% (Σ w_{i} = 1), và **không có tỷ trọng âm** "
          "(w_{i} ≥ 0). Tỷ trọng âm nghĩa là **bán khống**, tức đi vay cổ phiếu để bán trước rồi mua lại sau; thị "
          "trường Việt Nam chưa cho phép cách này. Nhóm dùng công cụ **Solver** của Excel. Solver tự thử nhiều cách "
          "chia vốn cho đến khi tìm được cách tốt nhất theo yêu cầu. Nhóm giải ba bài toán (Bảng 4.1)."),
    ("bang", "4.1", "Ba bài toán giải bằng Solver",
     [("Bài toán", "Solver cần tìm", "Điều kiện", "Kết quả dùng để"),
      ("Solver 1", "Tỷ trọng cho rủi ro σ_{p} nhỏ nhất", "Σw = 1; w ≥ 0", "Tìm danh mục rủi ro thấp nhất"),
      ("Solver 2", "Tỷ trọng cho rủi ro σ_{p} nhỏ nhất", "Σw = 1; w ≥ 0; lợi nhuận kỳ vọng bằng một mức cho trước",
       "Tìm từng điểm để vẽ đường biên"),
      ("Solver 3", "Tỷ trọng cho lợi nhuận E(R_{p}) lớn nhất", "Σw = 1; w ≥ 0; rủi ro σ_{p} ≤ 25%",
       "Chọn danh mục đầu tư")],
     [2.0, 4.6, 5.3, 4.6], (), "Nhóm thiết lập trên Excel."),
    ("p", "Các bước thực hiện:"),
    ("abc", ["Đưa lợi tức kỳ vọng và ma trận hiệp phương sai (theo năm) từ Phần 3 vào trang tính Solver.",
             "Tạo ba ô tỷ trọng cho Solver thay đổi, cùng các ô tính tổng tỷ trọng, E(R_{p}) và σ_{p} theo công "
             "thức (4.1). Trong Solver: ô mục tiêu là σ^{2}_{p} (Min) hoặc E(R_{p}) (Max), ô thay đổi là ba ô "
             "tỷ trọng, cách giải GRG Nonlinear vì σ^{2}_{p} là hàm bậc hai.",
             "Chạy **Solver 1** để tìm danh mục rủi ro thấp nhất.",
             "Chạy **Solver 2** cho 26 mức lợi nhuận mục tiêu: 25 mức cách đều từ thấp nhất (−3,82%, bằng MBB) đến "
             "cao nhất (46,01%, bằng GAS), thêm mức của danh mục rủi ro thấp nhất. Việc chạy 26 lần được tự "
             "động hóa bằng macro (đoạn lệnh tự động) trong Excel; cả 26 lần đều tìm được nghiệm.",
             "Vẽ 26 điểm lên đồ thị, trục ngang là rủi ro σ_{p}, trục đứng là lợi nhuận E(R_{p}).",
             "Chạy **Solver 3** với mức rủi ro chấp nhận 25%/năm để chọn danh mục."]),
    ("p", "Nhóm kiểm tra lại kết quả Solver bằng một chương trình tính toán độc lập; hai cách cho kết quả trùng khớp."),
    ("h2", "4.2. Đường biên phương sai bé nhất và đường biên hiệu quả"),
    ("hinh", "4.1", "Đường biên phương sai bé nhất và đường biên hiệu quả của danh mục MBB – MWG – GAS",
     "hinh_4_1_duong_bien.png", "Nhóm tính toán bằng Excel Solver (trang Đường biên)."),
    ("p", "**Cách đọc Hình 4.1:** mỗi điểm là một cách chia 10 tỷ đồng; càng **sang phải** càng rủi ro, càng **lên "
          "cao** càng lãi nhiều. Đường cong là **đường biên phương sai bé nhất**: với mỗi mức lợi nhuận, đó là cách "
          "chia vốn có rủi ro thấp nhất. Chấm tím xa nhất bên trái là **danh mục phương sai nhỏ nhất**. Phần đường "
          "cong **phía trên** chấm tím (nét liền) là **đường biên hiệu quả**, tức danh sách các lựa chọn tốt nhất: "
          "nhà đầu tư chọn mức rủi ro chịu được, đường biên cho biết mức lãi cao nhất tương ứng. Phần **phía dưới** "
          "(nét đứt) không nên chọn vì ở cùng mức rủi ro luôn có điểm phía trên lãi nhiều hơn."),
    ("bang", "4.2", "Một số điểm trên đường biên phương sai bé nhất (theo năm)",
     [("Lợi nhuận mục tiêu", "MBB", "MWG", "GAS", "Rủi ro σ_{p}", "Thuộc phần"),
      ("−3,82%", "100,00%", "0,00%", "0,00%", "27,04%", "Không hiệu quả"),
      ("6,20%", "66,66%", "14,54%", "18,80%", "24,51%", "Rủi ro thấp nhất"),
      ("10,71%", "57,01%", "15,20%", "27,79%", "24,98%", "Hiệu quả"),
      ("19,02%", "39,24%", "16,42%", "44,34%", "28,11%", "Hiệu quả"),
      ("46,01%", "0,00%", "0,00%", "100,00%", "49,65%", "Hiệu quả")],
     [3.2, 2.2, 2.2, 2.2, 2.4, 4.3], (0, 1, 2, 3, 4), "Trích từ 26 điểm ở trang Đường biên (Excel)."),
    ("p", "**Ý nghĩa:** Đồ thị cho thấy ba điều:"),
    ("abc", ["**Đa dạng hóa giảm rủi ro thật sự.** Danh mục rủi ro thấp nhất có σ = 24,51%, **thấp hơn cả MBB** "
             "(27,04%), cổ phiếu ít rủi ro nhất. Gộp ba cổ phiếu rủi ro lại cho ra danh mục ít rủi ro hơn từng mã, "
             "nhờ GAS gần như không tương quan với hai mã kia.",
             "**MWG đứng riêng thì không hấp dẫn**: rủi ro 35,70% mà lãi gần 0, nằm xa bên dưới đường biên. Nhưng "
             "MWG vẫn chiếm khoảng 15–19% trên phần lớn đường biên hiệu quả. Nếu bỏ MWG, với cùng giới hạn rủi ro "
             "25%, danh mục chỉ lãi tối đa 8,37% thay vì 10,80%.",
             "**Cách chia vốn sơ bộ 40/35/25 ở Phần 1 chưa tối ưu** (ô vuông xám nằm dưới đường biên). Với cùng mức "
             "rủi ro 25,56%, chia vốn đúng cách có thể đạt lãi khoảng 12,95% thay vì 10,22%. Vì vậy nhóm thay tỷ lệ "
             "sơ bộ bằng tỷ lệ tối ưu."]),
    ("h2", "4.3. Lựa chọn danh mục đầu tư"),
    ("p", "Để so sánh các danh mục, nhóm dùng thêm **hệ số Sharpe**: phần lợi nhuận vượt lãi suất an toàn trên mỗi "
          "đơn vị rủi ro, Sharpe = (E(R_{p}) − R_{f}) / σ_{p}. Sharpe càng cao thì mỗi đơn vị rủi ro càng \"đáng "
          "tiền\"."),
    ("bang", "4.3", "So sánh các danh mục ứng viên (theo năm)",
     [("Danh mục", "MBB", "MWG", "GAS", "E(R_{p})", "σ_{p}", "Sharpe"),
      ("Rủi ro thấp nhất (Solver 1)", "66,66%", "14,54%", "18,80%", "6,20%", "24,51%", "0,075"),
      ("**Được chọn (Solver 3)**", "**56,84%**", "**15,20%**", "**27,97%**", "**10,80%**", "**25,00%**", "**0,258**"),
      ("Toàn bộ vào GAS", "0%", "0%", "100%", "46,01%", "49,65%", "0,839"),
      ("Tỷ lệ sơ bộ ở Phần 1", "40,00%", "35,00%", "25,00%", "10,22%", "25,56%", "0,229")],
     [4.6, 1.95, 1.95, 1.95, 1.95, 1.95, 2.15], (1, 2, 3, 4, 5, 6),
     "Nhóm tính toán bằng Excel Solver (trang Danh mục chọn)."),
    ("p", "Nhóm chọn **danh mục có lợi nhuận kỳ vọng cao nhất trong giới hạn rủi ro 25%/năm**, tương đương "
          "khoảng 7,2%/tháng, vì bốn lý do:"),
    ("abc", ["Mức rủi ro 25% phù hợp chiến lược cân bằng, và gần bằng mức rủi ro 25,56% của tỷ lệ sơ bộ 40/35/25 "
             "nhóm đề xuất ở Phần 1.",
             "**Đánh đổi rất có lợi:** so với danh mục rủi ro thấp nhất, chỉ chịu thêm 0,49 điểm % rủi ro (24,51% → "
             "25,00%) nhưng lãi kỳ vọng tăng 4,6 điểm % (6,20% → 10,80%).",
             "Danh mục rủi ro thấp nhất chỉ lãi 6,20%/năm, gần bằng mức 4,36% của trái phiếu Chính phủ, nên không "
             "xứng với rủi ro của cổ phiếu.",
             "Dồn 100% vào GAS có Sharpe cao nhất nhưng mất lợi ích đa dạng hóa, và mức lãi 46% của GAS khó lặp lại."]),
    ("p", "**Vì sao dồn 56,84% vốn vào MBB dù lợi tức quá khứ âm?** Lợi tức một năm qua kém tin cậy (mục 3.3), "
          "nên nhóm chọn danh mục gần danh mục rủi ro thấp nhất, vốn chỉ phụ thuộc vào rủi ro và tương quan. MBB "
          "rủi ro thấp nhất và gần như không tương quan với GAS (ρ = 0,12), nên giữ rủi ro chung thấp; Phần 2 "
          "cũng cho thấy MBB đang rẻ hơn giá hợp lý khoảng 26%."),
    ("h2", "4.4. Phân bổ vốn 10 tỷ đồng"),
    ("p", "Trên sàn HOSE, cổ phiếu được mua theo **lô 100 cổ phiếu**, nên số cổ phiếu mua được làm tròn xuống bội số "
          "của 100. Giá tham chiếu là giá đóng cửa ngày 23/10/2026, phiên cuối trước khi giải ngân [43]:"),
    ("ct", "Số cổ phiếu = làm tròn xuống [w_{i} × 10 tỷ đồng / (giá × 100)] × 100", "4.2"),
    ("bang", "4.4", "Phân bổ 10 tỷ đồng theo danh mục được chọn (giá tham chiếu ngày 23/10/2026)",
     [("Cổ phiếu", "Tỷ trọng", "Giá (đ)", "Số cổ phiếu", "Số tiền mua (đ)", "Tỷ trọng thực tế"),
      ("MBB", "56,84%", "19.800", "287.000", "5.682.600.000", "56,83%"),
      ("MWG", "15,20%", "75.500", "20.100", "1.517.550.000", "15,18%"),
      ("GAS", "27,97%", "78.300", "35.700", "2.795.310.000", "27,95%"),
      ("Tổng", "100,00%", "", "", "9.995.460.000", "99,95%"),
      ("Tiền mặt còn lại", "", "", "", "4.540.000", "0,05%")],
     [2.8, 2.3, 2.3, 2.7, 3.6, 2.8], (1, 2, 3, 4, 5), "Nhóm tính toán (trang Danh mục chọn, Excel)."),
    ("p", "**Ý nghĩa với kỳ đầu tư 1 tháng:** lợi nhuận kỳ vọng khoảng 10,80% / 12 = **0,90%/tháng**, tức khoảng "
          "**90 triệu đồng** trên 10 tỷ đồng, nhưng rủi ro tháng khoảng 25,00% / √12 = 7,22% nên kết quả thực tế có "
          "thể khác đáng kể. Bảng 4.4 là số cổ phiếu mục tiêu, chưa tính phí giao dịch. Để hạn chế thua lỗ, nhóm "
          "áp dụng ba nguyên tắc: giải ngân hai đợt (60% số cổ phiếu mục tiêu ngày 26/10, 40% còn lại sau khi MBB "
          "và MWG công bố báo cáo tài chính quý III); bán một mã nếu giá giảm quá 8% so với giá mua; và bán GAS "
          "nếu cổ phiếu này có quyết định hủy tư cách công ty đại chúng."),

    ("phan", "KẾT LUẬN"),
    ("p", "Năm 2026, kinh tế Việt Nam tăng trưởng mạnh nhưng lạm phát vượt mục tiêu. Nhóm vì vậy theo chiến lược cân "
          "bằng, chọn ba cổ phiếu thuộc ba ngành: MBB (ngân hàng, đang được định giá rẻ), MWG (bán lẻ, lợi nhuận "
          "tăng nhanh) và GAS (khí đốt, chia cổ tức đều). Dữ liệu giá một năm cho thấy GAS gần như không lên xuống "
          "cùng nhịp với hai mã còn lại. Nhờ vậy, danh mục gồm cả ba mã có rủi ro thấp hơn cả cổ phiếu ít rủi ro "
          "nhất. Dùng Solver trên mô hình Markowitz, nhóm chia 10 tỷ đồng theo tỷ lệ **56,84% MBB – 15,20% MWG – "
          "27,97% GAS**, với lợi nhuận kỳ vọng 10,80%/năm và rủi ro 25,00%/năm, tốt hơn cách chia sơ bộ ban đầu. "
          "Hạn chế: lợi nhuận kỳ vọng ước lượng từ một năm dữ liệu nên dao động lớn, và một số thông số định giá ở "
          "Phần 2 là giả định."),
]

TAI_LIEU = TAI_LIEU_BAI_1 + [
    "CafeF. (2026). *Lịch sử giá cổ phiếu MBB, MWG, GAS và chỉ số VN-Index, 01/10/2025 – 23/10/2026* [Dữ liệu]. "
    "https://cafef.vn/du-lieu/lich-su-giao-dich-mbb-1.chn",
    "Markowitz, H. (1952). Portfolio selection. *The Journal of Finance, 7*(1), 77–91.",
    "Sharpe, W. F. (1964). Capital asset prices: A theory of market equilibrium under conditions of risk. "
    "*The Journal of Finance, 19*(3), 425–442.",
]
