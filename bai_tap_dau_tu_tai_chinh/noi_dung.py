"""Nội dung Bài tập tình huống 1 – Nhóm 7, lớp FIN3002_2. Dùng bởi tao_bao_cao.py.

Mỗi khối trong NOI_DUNG["than_bai"] là một tuple:
("phan", tiêu đề) · ("h2"/"h3", tiêu đề) · ("p", đoạn văn) · ("abc", [các ý]) · ("ngat",)
("bang", số, tên, các hàng (hàng đầu là tiêu đề cột), nguồn, độ rộng cột (cm), cột căn phải, ghi chú)
("hinh", số, tên, đường dẫn ảnh, nguồn)
Chữ **đậm** và *nghiêng* viết theo kiểu Markdown. Số trong ngoặc vuông [n] trỏ tới TAI_LIEU.
"""

THANH_VIEN = [
    ("49K29.1", "Nguyễn Công Hiếu"),
    ("49K29.1", "Nguyễn Thị Bảo Na"),
    ("49K29.1", "Nguyễn Thị Mỹ Thanh"),
    ("49K29.1", "Nguyễn Bảo Anh Thư"),
    ("49K29.1", "Dương Mẫn Trân"),
    ("49K29.1", "Ngô Triệu Vy"),
]

CHU_VIET_TAT = [
    ("BVPS", "Giá trị sổ sách trên mỗi cổ phiếu (Book Value Per Share)"),
    ("CAPM", "Mô hình định giá tài sản vốn (Capital Asset Pricing Model)"),
    ("CASA", "Tiền gửi không kỳ hạn (Current Account Savings Account)"),
    ("CPI", "Chỉ số giá tiêu dùng (Consumer Price Index)"),
    ("CTCK", "Công ty chứng khoán"),
    ("DDM", "Mô hình chiết khấu cổ tức (Dividend Discount Model)"),
    ("EPS", "Lợi nhuận trên mỗi cổ phiếu (Earnings Per Share)"),
    ("GDP", "Tổng sản phẩm trong nước (Gross Domestic Product)"),
    ("HOSE", "Sở Giao dịch Chứng khoán TP. Hồ Chí Minh"),
    ("LNG / LPG", "Khí thiên nhiên hóa lỏng / Khí dầu mỏ hóa lỏng"),
    ("LNST / LNTT", "Lợi nhuận sau thuế / Lợi nhuận trước thuế"),
    ("NHNN", "Ngân hàng Nhà nước Việt Nam"),
    ("NIM", "Biên lãi ròng (Net Interest Margin)"),
    ("P/B, P/E", "Hệ số giá trên giá trị sổ sách, hệ số giá trên lợi nhuận"),
    ("ROE", "Tỷ suất lợi nhuận trên vốn chủ sở hữu (Return On Equity)"),
    ("Rf, E(RM)", "Lãi suất phi rủi ro, tỷ suất lợi tức kỳ vọng của thị trường"),
]

NOI_DUNG = {
    "tom_tat": [
        "Nhóm 7 đóng vai trò công ty quản lý quỹ, xây dựng danh mục cổ phiếu niêm yết với vốn giả định "
        "10 tỷ đồng trong 1 tháng (26/10 – 25/11/2026). Báo cáo đi theo phương pháp **top-down**: phân "
        "tích vĩ mô, chọn ngành hưởng lợi, rồi phân tích và định giá từng doanh nghiệp.",
        "Bối cảnh vĩ mô có hai mặt: GDP quý III/2026 tăng 9,95%, cao nhất từ năm 2022, nhưng CPI tháng 9 "
        "tăng 5,08%, vượt mục tiêu 4,5% do giá dầu cao. Ngân hàng Nhà nước vì vậy khó hạ lãi suất thêm. "
        "Thị trường đang ở vùng định giá thấp (P/E khoảng 13,1 lần) và vừa được FTSE Russell nâng hạng "
        "lên thị trường mới nổi, nhưng biến động mạnh.",
        "Nhóm chọn **chiến lược cân bằng** với ba cổ phiếu thuộc ba ngành khác nhau: **MBB** (ngân hàng, "
        "vai trò giá trị, giá hợp lý 25.000 đ, +26%), **MWG** (bán lẻ, vai trò tăng trưởng, 90.000 đ, "
        "+20%) và **GAS** (khí đốt, vai trò phòng thủ và cổ tức, 78.400 đ, +2%). HPG và FPT bị loại vì giá "
        "đang giảm kéo dài, dễ trở thành tài sản bị thống trị khi tối ưu danh mục ở Bài tập tình huống 2.",
        "**Từ khóa:** phân tích top-down, CAPM, định giá cổ phiếu, chiến lược cân bằng, MBB, MWG, GAS.",
    ],
    "than_bai": [
        # ================= PHẦN 1 =================
        ("phan", "PHẦN 1. PHÂN TÍCH BỐI CẢNH ĐẦU TƯ"),
        ("p", "Nhóm 7 đóng vai trò công ty quản lý quỹ với vốn đầu tư giả định **10 tỷ đồng**, thời gian "
              "đầu tư **1 tháng** (26/10 – 25/11/2026). Số liệu trong báo cáo cập nhật đến 23/10/2026. Nhóm "
              "áp dụng phương pháp **top-down** (Chương 4): phân tích vĩ mô để xác định ngành tăng trưởng, "
              "sau đó chọn doanh nghiệp tốt và đang được định giá hợp lý trong ngành đó."),

        ("h2", "1.1. Đánh giá các yếu tố kinh tế vĩ mô"),
        ("h3", "1.1.1. Tăng trưởng kinh tế"),
        ("p", "GDP quý III/2026 tăng **9,95%**, mức cao nhất kể từ năm 2022; 9 tháng tăng 9,01%. Khu vực "
              "công nghiệp – xây dựng tăng 12,5%, dịch vụ tăng 9,5% [1], [2]. Tổng mức bán lẻ hàng hóa và "
              "dịch vụ 9 tháng tăng 13,4% (loại trừ yếu tố giá tăng 7,8%) [40]. Tăng trưởng mạnh giúp doanh "
              "thu và lợi nhuận doanh nghiệp tăng, nhu cầu vay vốn tăng. Đây là yếu tố **tích cực** cho thị "
              "trường, đặc biệt với ngân hàng và bán lẻ."),
        ("h3", "1.1.2. Lạm phát"),
        ("p", "CPI tháng 9/2026 tăng **5,08%** so với cùng kỳ, bình quân 9 tháng 4,52%, lạm phát cơ bản "
              "4,26%. Mức này **vượt mục tiêu 4,5%** của Chính phủ [1], [3]. Nguyên nhân chính là giá dầu: "
              "Brent bình quân tháng 9 lên 114 USD/thùng do xung đột ở Trung Đông. EIA dự báo giá dầu bình "
              "quân quý IV/2026 khoảng 105 USD/thùng, năm 2027 giảm về 84 USD/thùng [10]. Lạm phát cao làm "
              "giảm sức mua và hạn chế khả năng nới lỏng tiền tệ, là yếu tố **tiêu cực**."),
        ("h3", "1.1.3. Lãi suất và chính sách tiền tệ"),
        ("p", "NHNN giữ lãi suất tái cấp vốn ở 4,5% [4]. Do tín dụng tăng nhanh hơn huy động, lãi suất huy "
              "động kỳ hạn 6–12 tháng đã tăng khoảng 1,2 điểm % đến tháng 3/2026 và lãi suất liên ngân hàng "
              "qua đêm từng lên 16,39% (tháng 2/2026) [9], [41]. Gần đây áp lực đã giảm: khoảng 20 ngân hàng "
              "giảm lãi suất huy động khoảng 0,5 điểm %, 14 ngân hàng giảm lãi suất cho vay [8]. NHNN định "
              "hướng tín dụng cả năm khoảng 15%, VCBS dự báo 16–18% [6]. Theo mô hình chiết khấu cổ tức "
              "V₀ = D₁/(k − g), lãi suất cao làm tăng tỷ suất lợi tức yêu cầu k và làm giảm giá trị cổ phiếu. "
              "Chính sách tiền tệ vì vậy ở trạng thái **trung tính, khó nới lỏng thêm**."),
        ("h3", "1.1.4. Tỷ giá"),
        ("p", "Tỷ giá trung tâm USD/VND ngày 23/10/2026 là **25.627**, giảm nhẹ trong tháng 10, biên độ "
              "±5% [7]. Tỷ giá ổn định giúp nhà đầu tư nước ngoài bớt lo rủi ro mất giá tiền đồng. Đây là "
              "yếu tố **hỗ trợ** dòng vốn ngoại."),
        ("h3", "1.1.5. Diễn biến thị trường chứng khoán"),
        ("p", "VN-Index lập đỉnh 1.902,93 điểm ngày 13/1/2026, về gần 1.600 điểm trong tháng 3 rồi dao "
              "động 1.680–1.780 điểm; ngày 22/10 đóng cửa **1.760,63 điểm** [11], [13]. P/E thị trường "
              "khoảng 13,1 lần, thấp hơn bình quân 5 năm 14,4 lần [14]. FTSE Russell chính thức nâng hạng "
              "Việt Nam lên thị trường mới nổi từ 21/9/2026, giải ngân theo 4 đợt đến 9/2027, dòng vốn dự "
              "kiến 3–10 tỷ USD [15], [16]. Tuy vậy, thanh khoản từ tháng 6 giảm khoảng 41% so với quý I và "
              "khối ngoại vẫn bán ròng giữa tháng 10 [12], [13]."),
        ("p", "**Nhận xét chung.** Vĩ mô có **hai mặt đối lập**: tăng trưởng thực rất mạnh nhưng lạm phát "
              "giữ lãi suất ở mức cao. Trong công thức V₀ = D₁/(k − g), g đang tăng còn k khó giảm. Do đó, "
              "cổ phiếu có lợi thế là cổ phiếu **có lợi nhuận tăng trưởng thật và định giá còn thấp**, "
              "không phải cổ phiếu chỉ tăng nhờ kỳ vọng lãi suất giảm."),

        ("h2", "1.2. Nhận định triển vọng thị trường và triển vọng ngành"),
        ("h3", "1.2.1. Triển vọng thị trường trong thời gian đầu tư"),
        ("p", "Trong tháng đầu tư có ba chất xúc tác chính: (1) mùa công bố báo cáo tài chính quý III (cuối "
              "tháng 10); (2) giải ngân của các quỹ theo chỉ số FTSE; (3) số liệu CPI tháng 10 (đầu tháng 11). "
              "Nhóm xây dựng ba kịch bản như Bảng 1-1."),
        ("bang", "1-1", "Kịch bản VN-Index đến ngày 25/11/2026",
         [("Kịch bản", "VN-Index (điểm)", "Điều kiện xảy ra", "Xác suất"),
          ("Tích cực", "1.850 – 1.900", "Kết quả quý III tốt, dòng vốn FTSE giải ngân, giá dầu hạ", "30%"),
          ("Cơ sở", "1.720 – 1.820", "Kết quả quý III đúng kỳ vọng, lãi suất đi ngang", "50%"),
          ("Tiêu cực", "1.620 – 1.680", "CPI vượt 5,5%, NHNN thắt chặt, xung đột Trung Đông leo thang",
           "20%")],
         "Nhóm 7 nhận định dựa trên [1], [10], [13], [15].", [2.4, 3.2, 8.4, 2.0], (3,),
         "Xác suất là nhận định chủ quan của nhóm, không phải kết quả của mô hình."),
        ("p", "Kịch bản cơ sở là thị trường đi ngang và phân hóa mạnh, nên nhóm ưu tiên cổ phiếu vốn hóa "
              "lớn, thanh khoản cao, có kết quả quý III tốt."),
        ("h3", "1.2.2. Triển vọng ngành"),
        ("bang", "1-2", "Đánh giá triển vọng các ngành ứng viên",
         [("Ngành", "Động lực tăng trưởng trong tương lai", "Rủi ro chính", "Kết luận"),
          ("Ngân hàng", "GDP tăng gần 10% kéo theo nhu cầu vốn; tín dụng cả năm dự kiến 15–18%; nợ xấu "
           "giảm nhờ Nghị quyết 42 được luật hóa; tỷ trọng lớn nhất trong chỉ số nên hưởng lợi đầu tiên "
           "từ dòng vốn FTSE", "Chi phí vốn tăng làm NIM giảm", "Chọn"),
          ("Bán lẻ tiêu dùng", "Dân số trẻ, thu nhập tăng; bán lẻ 9 tháng +13,4%; chuỗi bán lẻ hiện đại "
           "còn chiếm thị phần nhỏ so với chợ truyền thống", "Lạm phát làm giảm sức mua", "Chọn"),
          ("Khí đốt, năng lượng", "Cầu điện tăng theo kinh tế; điện khí LNG là trụ cột của Quy hoạch điện "
           "VIII đến 2030; giá dầu cao làm tăng giá bán khí", "Giá dầu đảo chiều; giá bán bị điều tiết",
           "Chọn"),
          ("Thép", "Hưởng lợi đầu tư công, xây dựng +12,5%", "Dư cung: VinMetal có thể thêm 4,2 triệu tấn "
           "thép xây dựng và 4 triệu tấn thép cuộn cán nóng đến 2029", "Không chọn"),
          ("Công nghệ", "Chuyển đổi số, AI (doanh thu AI của FPT +55%)", "Lo ngại AI làm giảm nhu cầu gia "
           "công phần mềm; giá cổ phiếu giảm mạnh", "Theo dõi")],
         "Nhóm 7 tổng hợp từ [1], [6], [10], [35], [37], [40].", [2.6, 7.2, 4.2, 2.0], (), None),
        ("p", "Ba ngành được chọn đều có **động lực tăng trưởng dài hạn** gắn với số liệu vĩ mô ở mục 1.1, "
              "và phản ứng **khác nhau** trước cùng một cú sốc: giá dầu tăng gây bất lợi cho bán lẻ (qua lạm "
              "phát) nhưng có lợi cho khí đốt."),

        ("h2", "1.3. Chiến lược đầu tư của nhóm"),
        ("p", "Nhóm chọn **chiến lược cân bằng**, kết hợp ba vai trò giá trị, tăng trưởng và phòng thủ – thu "
              "nhập cổ tức, thay vì dồn vốn vào một phong cách. Có hai lý do:"),
        ("abc", ["Vĩ mô có rủi ro hai chiều (tăng trưởng mạnh nhưng lạm phát cao), nên danh mục cần thành "
                 "phần chịu được kịch bản tiêu cực ở Bảng 1-1.",
                 "Theo lý thuyết Markowitz (Chương 2), kết hợp các tài sản có tương quan thấp giúp giảm rủi "
                 "ro danh mục mà không phải hy sinh nhiều lợi tức kỳ vọng."]),
        ("bang", "1-3", "Vai trò của từng cổ phiếu trong chiến lược cân bằng",
         [("Mã", "Vai trò", "Lý do phù hợp với bối cảnh", "Tỷ trọng sơ bộ"),
          ("MBB", "Giá trị", "P/B khoảng 1,0 lần trong khi ROE khoảng 20%", "40% (4 tỷ đồng)"),
          ("MWG", "Tăng trưởng", "LNST 6 tháng +88%, doanh thu 9 tháng +30%", "35% (3,5 tỷ đồng)"),
          ("GAS", "Phòng thủ, cổ tức", "Lợi nhuận tăng theo giá dầu, nhiều tiền mặt, cổ tức tiền mặt đều",
           "25% (2,5 tỷ đồng)")],
         "Nhóm 7 đề xuất.", [1.6, 3.0, 8.0, 3.4], (), "Tỷ trọng cuối cùng sẽ được xác định bằng đường "
         "biên hiệu quả và danh mục tối ưu ở Bài tập tình huống 2."),

        # ================= PHẦN 2 =================
        ("phan", "PHẦN 2. PHÂN TÍCH CỔ PHIẾU"),
        ("h2", "2.1. Tiêu chí lựa chọn cổ phiếu"),
        ("p", "Từ ba ngành được chọn, nhóm lọc cổ phiếu theo năm tiêu chí: (1) niêm yết trên HOSE, vốn "
              "hóa lớn, thanh khoản cao; (2) lợi nhuận 2026 tăng trưởng hai chữ số; (3) giá **ổn định**, "
              "không trong xu hướng giảm kéo dài; (4) định giá không cao hơn mức trung bình lịch sử; (5) có "
              "lịch sử giá dài để ước lượng lợi tức và phương sai ở Bài tập tình huống 2."),
        ("bang", "2-1", "Kết quả sàng lọc các cổ phiếu ứng viên",
         [("Mã", "Lợi nhuận gần nhất", "Diễn biến giá", "Kết quả"),
          ("MBB", "LNTT 6 tháng +27,1%", "Đi ngang so với đầu năm đến phiên 4/8 (+0,09%); giảm sau đó chủ "
           "yếu do điều chỉnh kỹ thuật khi chia cổ tức 15% bằng cổ phiếu", "Đạt"),
          ("MWG", "LNST 6 tháng +88%", "Thấp hơn đỉnh 52 tuần khoảng 21%; đang hồi lại (73.900 đ ngày 16/10 "
           "lên 75.200 đ ngày 22/10)", "Đạt"),
          ("GAS", "LNTT 9 tháng +31%", "Dao động 76.000–82.000 đ trong tháng 10", "Đạt"),
          ("HPG", "LNST quý II +51%", "−12,2% từ đầu năm; dưới đường MA200 gần 5 tháng; 16 quỹ bán ròng 4 "
           "tháng liên tiếp", "Loại"),
          ("FPT", "LNST 9 tháng +13,3%", "Từ khoảng 98.000 đ đầu năm còn 57.400 đ (22/10)", "Loại")],
         "Nhóm 7 tổng hợp từ [17], [24], [28], [35], [36], [37].", [1.6, 3.6, 8.6, 2.2], (), None),
        ("p", "HPG và FPT có **lợi nhuận tăng nhưng giá giảm kéo dài**; với kỳ hạn 1 tháng, nhóm không có lý "
              "do để tin xu hướng sẽ đảo chiều. Hai mã này nhiều khả năng có lợi tức kỳ vọng thấp nhưng độ "
              "lệch chuẩn cao, tức là **tài sản bị thống trị** trên đồ thị lợi tức – rủi ro."),
        ("p", "**Giả định chung khi định giá.** Tỷ suất lợi tức yêu cầu k được tính bằng CAPM (Chương 3): "
              "k = Rf + β × [E(RM) − Rf], với Rf = 4,36% (lợi suất trái phiếu Chính phủ kỳ hạn 10 năm, "
              "phiên đấu thầu cuối tháng 7/2026 [5]) và phần bù rủi ro thị trường giả định 8%. Hệ số β tạm "
              "giả định theo đặc điểm ngành (MBB 1,1; MWG 1,2; GAS 0,8). Ở Bài tập tình huống 2, β sẽ được "
              "ước lượng từ dữ liệu giá ngày theo công thức β = Cov(Ri, RM)/σ²M."),

        # ---------- MBB ----------
        ("h2", "2.2. Ngân hàng TMCP Quân đội (MBB – HOSE)"),
        ("h3", "2.2.1. Mô hình kinh doanh"),
        ("p", "MB là ngân hàng thương mại cổ phần có cổ đông lớn là các doanh nghiệp thuộc Bộ Quốc phòng. "
              "Nguồn thu chính là **chênh lệch lãi suất**: huy động tiền gửi, đặc biệt tiền gửi không kỳ hạn "
              "(CASA) nhờ ứng dụng ngân hàng số với gần 40 triệu khách hàng, rồi cho vay với lãi suất cao "
              "hơn. MB xây dựng hệ sinh thái tài chính gồm Chứng khoán MBS (sở hữu 76,35%), tài chính tiêu "
              "dùng MCredit (50%), bảo hiểm và ngân hàng MBV (100%, nhận chuyển giao bắt buộc) [20]."),
        ("h3", "2.2.2. Kết quả kinh doanh và tình hình tài chính"),
        ("bang", "2-2", "Kết quả kinh doanh chính của MBB",
         [("Chỉ tiêu", "Năm 2025", "6 tháng 2026", "Tăng trưởng"),
          ("LNTT hợp nhất (tỷ đồng)", "34.268", "20.188", "+18,9% / +27,1%"),
          ("Thu nhập lãi thuần (tỷ đồng)", "–", "31.807", "+32,2%"),
          ("Dư nợ tín dụng (nghìn tỷ đồng)", "–", "1.256", "+13% so với đầu năm"),
          ("Tỷ lệ nợ xấu", "1,29%", "1,4%", "Bao phủ nợ xấu 93,6%"),
          ("Kế hoạch LNTT 2026 (tỷ đồng)", "", "39.500", "+15%; đạt 51,1% sau 6 tháng")],
         "Nhóm 7 tổng hợp từ [17], [18].", [5.4, 2.6, 2.8, 5.2], (1, 2), None),
        ("p", "Lợi nhuận tăng nhanh hơn kế hoạch nhờ thu nhập lãi thuần tăng 32,2% và chi phí dự phòng "
              "giảm. ROE duy trì khoảng 20–21%, thuộc nhóm cao nhất ngành [18], [21]."),
        ("h3", "2.2.3. Chính sách cổ tức, rủi ro và triển vọng tăng trưởng"),
        ("p", "**Cổ tức:** kế hoạch 2026 chia 25%, gồm 10% tiền mặt (1.000 đ/cp) và 15% cổ phiếu [21]. Tại "
              "giá 19.850 đ, **tỷ suất cổ tức tiền mặt khoảng 5%**."),
        ("p", "**Rủi ro:** (1) NIM bị thu hẹp, dự phóng 3,95% năm 2026, giảm 0,1 điểm %, vì cho vay tăng nhanh "
              "hơn huy động và tỷ lệ CASA giảm [20]; (2) Kiểm toán Nhà nước ghi nhận nợ nhóm 5 (có khả năng "
              "mất vốn) năm 2025 tăng 39,4%, lên 6.421 tỷ đồng [19]; (3) pha loãng do chia cổ tức bằng cổ "
              "phiếu."),
        ("p", "**Triển vọng:** hưởng lợi trực tiếp từ tín dụng tăng 15–18% và dòng vốn FTSE vào nhóm ngân "
              "hàng vốn hóa lớn; MCredit đang được tái cấu trúc để hướng tới IPO [20]."),
        ("h3", "2.2.4. Nhận định về mức giá hợp lý"),
        ("p", "Nhóm dùng **P/B hợp lý** suy ra từ mô hình cổ tức tăng trưởng đều (Chương 4): từ "
              "V₀ = D₁/(k − g), D₁ = E₁(1 − b), E₁ = ROE × B₀ và g = ROE × b, ta có "
              "**P/B = (ROE − g)/(k − g)**. Với β = 1,1: k = 4,36% + 1,1 × 8% = 13,16%. Giá trị sổ sách mỗi "
              "cổ phiếu (BVPS) là 19.462 đ [22]."),
        ("bang", "2-3", "Định giá MBB theo P/B hợp lý",
         [("Kịch bản", "ROE bền vững", "g dài hạn", "P/B hợp lý", "Giá trị (đ/cp)"),
          ("Thận trọng", "15%", "6%", "1,26", "24.500"),
          ("Cơ sở", "17%", "6%", "1,54", "29.900"),
          ("Lạc quan", "20%", "7%", "2,11", "41.000")],
         "Nhóm 7 tính toán.", [3.2, 3.2, 3.0, 3.0, 3.6], (1, 2, 3, 4), None),
        ("p", "Ở mức P/B 1,02 hiện tại, thị trường đang ngầm định ROE bền vững của MB chỉ khoảng 13%, thấp "
              "hơn nhiều mức 20% đang đạt được, nghĩa là rủi ro nợ xấu và NIM đã phản ánh khá đầy đủ vào giá. "
              "Do chưa loại trừ được rủi ro nợ nhóm 5, nhóm chọn **giá hợp lý 25.000 đ/cp, tương ứng tiềm "
              "năng tăng 26%**, gần kịch bản thận trọng và mức 26.700 đ của FUNAN [20]."),

        # ---------- MWG ----------
        ("h2", "2.3. CTCP Đầu tư Thế Giới Di Động (MWG – HOSE)"),
        ("h3", "2.3.1. Mô hình kinh doanh"),
        ("p", "MWG là nhà bán lẻ lớn nhất Việt Nam với ba trụ cột: (1) **Thế Giới Di Động và Điện Máy "
              "Xanh**, kinh doanh điện thoại và điện máy với khoảng 3.000 cửa hàng, tạo dòng tiền ổn định và "
              "đang chuẩn bị IPO Điện Máy Xanh; (2) **Bách Hóa Xanh**, chuỗi thực phẩm và hàng tiêu dùng "
              "hơn 2.100 cửa hàng, đã có lãi từ 2025 và là động lực tăng trưởng chính; (3) **EraBlue** tại "
              "Indonesia [26], [42]. Lợi thế cạnh tranh nằm ở quy mô mua hàng, hệ thống logistics và dữ liệu "
              "khách hàng."),
        ("h3", "2.3.2. Kết quả kinh doanh và tình hình tài chính"),
        ("bang", "2-4", "Kết quả kinh doanh chính của MWG",
         [("Chỉ tiêu (tỷ đồng)", "Năm 2024", "Năm 2025", "Năm 2026"),
          ("Doanh thu thuần", "134.341", "156.457 (+16,4%)", "9 tháng: 147.953 (+30%), đạt 80% kế hoạch"),
          ("Lợi nhuận sau thuế", "3.733", "7.075 (+89,5%)", "6 tháng: 6.017 (+88%)"),
          ("Kế hoạch 2026", "", "", "Doanh thu 185.000; LNST 9.200 (+30%)")],
         "Nhóm 7 tổng hợp từ [23], [24], [26].", [3.8, 2.4, 3.6, 6.2], (1,), None),
        ("p", "Riêng quý III/2026, doanh thu ước 52.648 tỷ đồng (+32%), Bách Hóa Xanh tăng 34% [24]. Các "
              "CTCK dự phóng LNST quý III đạt 2.529–3.456 tỷ đồng, tăng 43–95% so với cùng kỳ [25]."),
        ("h3", "2.3.3. Chính sách cổ tức, rủi ro và triển vọng tăng trưởng"),
        ("p", "**Cổ tức:** năm 2026 MWG dự kiến chi khoảng 3.000 tỷ đồng cổ tức tiền mặt, mức cao nhất từ "
              "trước đến nay [26]; nhóm ước tính khoảng 2.000 đ/cp, **tỷ suất khoảng 2,7%**."),
        ("p", "**Rủi ro:** (1) từ quý III, MWG chia khoảng 14% lợi nhuận Điện Máy Xanh cho cổ đông thiểu số, "
              "nên lợi nhuận của cổ đông công ty mẹ giảm so với quý II [25]; (2) một số CTCK dự báo lợi nhuận "
              "2027 đi ngang; (3) lạm phát làm giảm sức mua hàng không thiết yếu; (4) cạnh tranh trong mảng "
              "bách hóa."),
        ("p", "**Triển vọng:** Bách Hóa Xanh tiếp tục mở rộng và có lãi, IPO Điện Máy Xanh giúp định giá "
              "lại các mảng kinh doanh, tiêu dùng nội địa tăng trên 13%/năm."),
        ("h3", "2.3.4. Nhận định về mức giá hợp lý"),
        ("p", "Nhóm dùng **phương pháp P/E** (Chương 4). EPS 2026 ước khoảng 6.000 đ, tính từ kế hoạch LNST "
              "sau khi trừ phần của cổ đông thiểu số. Giá hiện tại 75.200 đ (22/10) tương ứng P/E dự phóng "
              "khoảng 12,5 lần, thấp hơn mức bình quân lịch sử khoảng 17 lần [27]. Nhóm chọn **P/E chuẩn 15 "
              "lần**, thấp hơn mức lịch sử để trừ hao rủi ro lợi nhuận 2027 chững lại:"),
        ("p", "Giá hợp lý = 15 × 6.000 = **90.000 đ/cp (tiềm năng tăng 20%)**."),
        ("p", "Kiểm tra bằng P/E = (D₁/E₁)/(k − g) với k = 13,96% (β = 1,2) và tỷ lệ chi trả 33%: P/E 15 lần "
              "tương ứng tăng trưởng dài hạn 11,7%/năm, phù hợp với tốc độ tăng của bán lẻ. Giá mục tiêu của "
              "các CTCK: Kafi 94.400 đ, SSI 106.000 đ, MBS 109.000 đ [27]."),

        # ---------- GAS ----------
        ("h2", "2.4. Tổng Công ty Khí Việt Nam (GAS – HOSE)"),
        ("h3", "2.4.1. Mô hình kinh doanh"),
        ("p", "PV GAS nắm gần như toàn bộ chuỗi giá trị khí trong nước: thu gom, vận chuyển bằng đường ống, "
              "xử lý và phân phối **khí khô** cho nhà máy điện, đạm và khu công nghiệp; kinh doanh **LPG**; "
              "nhập khẩu và phân phối **LNG**. Quý I/2026, khí khô và LNG chiếm khoảng 55% doanh thu, LPG hơn "
              "40% [31]. Đây là mô hình gần độc quyền, giá bán gắn với giá dầu, nên lợi nhuận tăng khi giá "
              "dầu tăng."),
        ("h3", "2.4.2. Kết quả kinh doanh và tình hình tài chính"),
        ("bang", "2-5", "Kết quả kinh doanh chính của GAS",
         [("Chỉ tiêu", "Năm 2025", "9 tháng 2026"),
          ("Doanh thu hợp nhất (tỷ đồng)", "135.129 (+30%)", "Trên 120.900 (+30%)"),
          ("Lợi nhuận (tỷ đồng)", "LNST 11.571 (+9%)", "LNTT trên 16.600 (+31%); quý III +68%"),
          ("So với kế hoạch năm", "", "LNTT đạt 197% kế hoạch"),
          ("Tiền mặt và đầu tư ngắn hạn", "Gần 40.000 tỷ đồng", "")],
         "Nhóm 7 tổng hợp từ [28], [29], [30].", [5.4, 4.6, 6.0], (), None),
        ("h3", "2.4.3. Chính sách cổ tức, rủi ro và triển vọng tăng trưởng"),
        ("p", "**Cổ tức:** cổ tức tiền mặt năm 2025 là 25% (2.500 đ/cp, tổng hơn 6.000 tỷ đồng, chốt quyền "
              "23/9/2026) [33], **tỷ suất khoảng 3,3%**. GAS duy trì chia cổ tức tiền mặt cao nhiều năm."),
        ("p", "**Rủi ro:** (1) giá dầu đảo chiều, EIA dự báo Brent về 84 USD năm 2027 [10]; (2) biên lợi "
              "nhuận gộp LPG quý I giảm từ 7,5% xuống 5,3% do giá nhập khẩu tăng [31]; (3) **tư cách công ty "
              "đại chúng**: Tập đoàn Dầu khí nắm 95,76% cổ phần, cổ đông nhỏ chỉ giữ 4,24% (yêu cầu tối "
              "thiểu 10%); PV GAS có 1 năm từ 14/8/2026 để khắc phục [32]. Nguy cơ hủy niêm yết trong kỳ đầu "
              "tư 1 tháng thấp, nhưng tỷ lệ cổ phiếu tự do chuyển nhượng thấp hạn chế dòng vốn ngoại."),
        ("p", "**Triển vọng:** nhu cầu khí cho điện tăng theo Quy hoạch điện VIII; mảng LNG là động lực tăng "
              "trưởng trung hạn."),
        ("h3", "2.4.4. Nhận định về mức giá hợp lý"),
        ("p", "Với β = 0,8: k = 4,36% + 0,8 × 8% = 10,76%. Nhóm kết hợp hai phương pháp:"),
        ("abc", ["**Mô hình cổ tức tăng trưởng đều (DDM):** D₀ = 2.500 đ, g = 7%. "
                 "V₀ = 2.500 × 1,07/(0,1076 − 0,07) = **71.100 đ**. Kết quả rất nhạy với g: nếu g = 6% thì V₀ "
                 "chỉ còn 55.700 đ, vì k − g quá nhỏ.",
                 "**P/E:** EPS 4 quý gần nhất khoảng 5.350 đ; P/E chuẩn 16 lần (mức SSI sử dụng) cho "
                 "**85.600 đ** [34]."]),
        ("p", "Giá hợp lý bằng bình quân hai phương pháp, **78.400 đ/cp (tiềm năng tăng 2%)**; giá mục tiêu "
              "bình quân của 7 CTCK là 87.308 đ [34]. GAS đang được định giá gần mức hợp lý nên **không phải "
              "mã để kỳ vọng tăng giá mạnh**. Nhóm vẫn chọn GAS vì β thấp và lợi nhuận đi ngược chiều bán "
              "lẻ khi giá dầu tăng, giúp **giảm phương sai danh mục**; cổ tức và lượng tiền mặt lớn tạo đệm an "
              "toàn trong kịch bản tiêu cực. Nếu ở Bài tập tình huống 2 GAS bị thống trị, nhóm sẽ thay bằng "
              "**POW** (LNTT 9 tháng gấp 2,3 lần cùng kỳ [38])."),

        # ---------- Tổng hợp ----------
        ("h2", "2.5. Tổng hợp và kết luận"),
        ("hinh", "2.1", "Vùng giá hợp lý của MBB, MWG, GAS so với giá hiện tại",
         "figures/01_vung_gia_hop_ly.png", "Nhóm 7 tính toán."),
        ("bang", "2-6", "So sánh ba cổ phiếu được chọn",
         [("Tiêu chí", "MBB", "MWG", "GAS"),
          ("Giá 21–22/10/2026", "19.850 đ", "75.200 đ", "76.500 đ"),
          ("Tăng trưởng lợi nhuận", "+27,1% (LNTT 6T)", "+88% (LNST 6T)", "+31% (LNTT 9T)"),
          ("Định giá hiện tại", "P/B 1,02; P/E 5–6", "P/E dự phóng 12,5", "P/E 14,3; P/B 2,3–2,9"),
          ("Tỷ suất cổ tức tiền mặt", "~5%", "~2,7%", "~3,3%"),
          ("Giá hợp lý / tiềm năng", "25.000 đ / +26%", "90.000 đ / +20%", "78.400 đ / +2%"),
          ("Rủi ro lớn nhất", "Nợ nhóm 5, NIM", "Lợi nhuận 2027 chững", "Giá dầu, tư cách đại chúng")],
         "Nhóm 7 tổng hợp và tính toán.", [4.0, 4.0, 4.0, 4.0], (), None),
        ("p", "Ba cổ phiếu thuộc ba ngành khác nhau, đều có lợi nhuận 2026 tăng trưởng hai chữ số và giá "
              "không trong xu hướng giảm kéo dài. MBB và MWG mang lại tiềm năng tăng giá; GAS giữ vai trò giảm "
              "rủi ro. Trong 1 tháng, nhóm kỳ vọng giá thu hẹp một phần khoảng cách tới mức hợp lý nhờ các "
              "chất xúc tác ở mục 1.2.1. Khuyến nghị thực hiện:"),
        ("abc", ["Giải ngân theo tỷ trọng sơ bộ 40/35/25, chia 2 lần: 60% đầu kỳ, 40% sau khi MBB và MWG "
                 "công bố báo cáo tài chính quý III.",
                 "Cắt lỗ một mã nếu giảm quá 8% so với giá mua; bán GAS nếu có quyết định hủy tư cách công ty "
                 "đại chúng.",
                 "Nếu CPI tháng 10 vượt 5,5%, giảm tỷ trọng MWG và tăng GAS."]),
        ("p", "**Giới hạn:** nhiều số liệu quý III/2026 là số ước tính công bố trước báo cáo tài chính chính "
              "thức; hệ số β và phần bù rủi ro 8% là giả định, giá trị hợp lý thay đổi đáng kể khi k thay đổi "
              "(nhất là với GAS)."),
    ],
}

TAI_LIEU = [
    "Cục Thống kê. (2026, 3 tháng 10). *Một số nét chính tình hình kinh tế – xã hội quý III và 9 tháng năm "
    "2026*. https://www.nso.gov.vn/bai-top/2026/10/mot-so-net-chinh-tinh-hinh-kinh-te-xa-hoi-quy-iii-va-9-"
    "thang-nam-2026/",
    "VT Markets. (2026). *Vietnam Q3 GDP growth hits post-pandemic high as inflation rises, limiting central "
    "bank easing*. https://www.vtmarkets.com/en-eu/live-updates/vietnam-q3-gdp-growth-hits-post-pandemic-"
    "high-as-inflation-rises-limiting-central-bank-easing/",
    "FXStreet. (2026, 7 tháng 10). *Vietnam: Strong GDP but rising inflation risks – Commerzbank*. "
    "https://www.fxstreet.com/news/vietnam-strong-gdp-but-rising-inflation-risks-commerzbank-202610071518",
    "Trading Economics. (2026). *Vietnam interest rate*. https://tradingeconomics.com/vietnam/interest-rate",
    "Tạp chí Kinh tế Tài chính. (2026). *Tháng 7/2026 huy động 18.603 tỷ đồng trái phiếu Chính phủ qua đấu "
    "thầu*. https://tapchikinhtetaichinh.vn/thang-7-2026-huy-dong-18-603-ty-dong-trai-phieu-chinh-phu-qua-"
    "dau-thau-164137.html",
    "VietnamFinance. (2026). *Tăng trưởng tín dụng 2026 có thể đạt 18%, lãi suất không còn đi ngang*. "
    "https://vietnamfinance.vn/tang-truong-tin-dung-2026-co-the-dat-18-lai-suat-khong-con-di-ngang-d139109.html",
    "VietnamPlus. (2026, 23 tháng 10). *Reference exchange rate continues going down on October 23*. "
    "https://en.vietnamplus.vn/reference-exchange-rate-continues-going-down-on-october-23-post354181.vnp",
    "VietnamPlus. (2026). *Lending rates cut by up to 3%, to lower borrowing costs for businesses and "
    "priority sectors*. https://en.vietnamplus.vn/lending-rates-cut-by-up-to-3-to-lower-borrowing-costs-for-"
    "businesses-and-priority-sectors-post354078.vnp",
    "CEIC. (2026). *State Bank of Vietnam: VNIBOR: Interbank: VND: Overnight*. https://www.ceicdata.com/en/"
    "vietnam/vietnam-interbank-offered-rate/state-bank-of-vietnam-vnibor-interbank-vnd-overnight",
    "Thị trường Tài chính Tiền tệ. (2026). *EIA nâng dự báo giá dầu 2026 nhưng kỳ vọng dầu Brent giảm về 84 "
    "USD/thùng năm 2027*. https://thitruongtaichinhtiente.vn/eia-nang-du-bao-gia-dau-2026-nhung-ky-vong-dau-"
    "brent-giam-ve-84-usd-thung-nam-2027-86120.html",
    "Báo Nhân Dân. (2026, 22 tháng 10). *Infographic: VN-Index up 1.26% on October 22*. "
    "https://en.nhandan.vn/infographic-vn-index-up-126-on-october-22-post168101.html",
    "Vietnam.vn. (2026, 14 tháng 10). *Chứng khoán hôm nay 14/10/2026: VN-Index tiếp tục giảm về vùng 1.700 "
    "điểm*. https://www.vietnam.vn/en/chung-khoan-hom-nay-14-10-2026-vn-index-tiep-tuc-giam-ve-vung-1-700-diem",
    "Tuổi Trẻ. (2026). *VN-Index biến động mạnh: Tại sao thị trường chứng khoán như tàu lượn năm 2026?* "
    "https://tuoitre.vn/sang-giam-gan-50-diem-chieu-bat-tang-vn-index-tau-luon-vi-dau-100260716225550451.htm",
    "Tạp chí Kinh tế Tài chính. (2026). *VN-Index hướng về đỉnh cũ trong nửa cuối năm 2026*. "
    "https://tapchikinhtetaichinh.vn/vn-index-huong-ve-dinh-cu-trong-nua-cuoi-nam-2026-163653.html",
    "Mondaq. (2026). *Vietnam is now an emerging market: What exactly changes for foreign investors*. "
    "https://www.mondaq.com/financial-services/1853862/vietnam-is-now-an-emerging-market-what-exactly-"
    "changes-for-foreign-investors",
    "Vietnam News. (2025). *FTSE Russell upgrades Việt Nam to secondary emerging market status*. "
    "https://vietnamnews.vn/economy/1726818/ftse-russell-upgrades-viet-nam-to-secondary-emerging-market-"
    "status.html",
    "Tin nhanh Chứng khoán. (2026). *MB lãi hơn 20.188 tỷ đồng sau 6 tháng đầu năm 2026, tăng hơn 27% so với "
    "cùng kỳ*. https://www.tinnhanhchungkhoan.vn/mb-lai-hon-20188-ty-dong-sau-6-thang-dau-nam-2026-tang-hon-"
    "27-so-voi-cung-ky-post395064.html",
    "ABS Research. (2026, tháng 3). *Báo cáo cập nhật MBB*. https://www.abs.vn/wp-content/uploads/2026/03/"
    "MBB_260302_Note-1.pdf",
    "VnBusiness. (2026). *Kiểm toán Nhà nước \"bóc tách\" sai lệch tại MB*. https://vnbusiness.vn/kiem-toan-"
    "nha-nuoc-boc-tach-sai-lech-tai-mb-no-co-kha-nang-mat-von-phinh-to-lo-loat-chi-tieu-sai-quy-dinh.html",
    "FUNAN Research. (2026, tháng 10). *Company report – Military Commercial Joint Stock Bank (MBB)*. "
    "https://funan.com.vn/upload/media/LocalNews/09102026/Company%20Report%20-%20Military%20Commercial%20"
    "Joint%20Stock%20Bank%20(MBB).pdf",
    "VietnamPlus. (2026). *MB tăng vốn điều lệ vượt 102.000 tỷ đồng, chia cổ tức 25% trong 2026*. "
    "https://www.vietnamplus.vn/mb-du-kien-tang-von-dieu-le-len-hon-102000-ty-dong-chia-co-tuc-ty-le-25-"
    "post1105670.vnp",
    "Ngân hàng TMCP Quân đội. (2026). *Thông tin thị trường MBB*. https://thongtinthitruong.mbbank.com.vn/",
    "Finhay. (2026). *Có nên đầu tư cổ phiếu MWG? Giải mã tương lai \"ông lớn\" ngành di động năm 2026*. "
    "https://www.finhay.com.vn/co-phieu-mwg",
    "Thời báo Tài chính Việt Nam. (2026). *Doanh thu 9 tháng của Thế Giới Di Động tăng 30%, đạt gần 148.000 "
    "tỷ đồng*. https://thoibaotaichinhvietnam.vn/doanh-thu-9-thang-cua-the-gioi-di-dong-tang-30-dat-gan-148-"
    "000-ty-dong-205356.html",
    "Elibook. (2026, 17 tháng 9). *MWG và FRT: VDSC hé lộ dự phóng quý 3/2026*. https://elibook.vn/2026/09/17/"
    "mwg-va-frt-vdsc-he-lo-du-phong-quy-3-2026-mua-tuu-truong-keo-dai-nhung-mwg-phai-chia-bot-mieng-banh-"
    "cho-co-dong-thieu-so/",
    "Báo Pháp luật – Doanh nhân. (2026). *ĐHĐCĐ Thế Giới Di Động (MWG) 2026: Mục tiêu lợi nhuận kỷ lục 9.200 "
    "tỷ*. https://doanhnhan.baophapluat.vn/dhdcd-the-gioi-di-dong-mwg-2026-muc-tieu-loi-nhuan-ky-luc-9-200-"
    "ty-bao-chi-3-000-ty-tra-co-tuc-va-tham-vong-ipo-bach-hoa-xanh.html",
    "VOV. (2026, 20 tháng 10). *Một số cổ phiếu cần quan tâm 20/10: Cơ hội tiềm năng với MWG và GAS*. "
    "http://vov.vn/thi-truong/mot-so-co-phieu-can-quan-tam-2010-co-hoi-tiem-nang-voi-mwg-va-gas-post1342091.vov",
    "Người Quan sát. (2026). *PV GAS báo lãi 9 tháng gấp đôi kế hoạch cả năm*. https://nguoiquansat.vn/pv-"
    "gas-bao-lai-9-thang-gap-doi-ke-hoach-ca-nam-321947.html",
    "Vietstock. (2026, tháng 10). *PV GAS lãi trước thuế 5.4 ngàn tỷ đồng trong quý 3, tăng trưởng 68%*. "
    "https://vietstock.vn/2026/10/pv-gas-lai-truoc-thue-54-ngan-ty-dong-trong-quy-3-tang-truong-68-737-"
    "1502664.htm",
    "Mekong ASEAN. (2026). *PV GAS: Doanh thu năm 2025 bứt phá, nắm giữ lượng tiền gần 40.000 tỷ đồng*. "
    "https://mekongasean.vn/pv-gas-doanh-thu-nam-2025-but-pha-nam-giu-luong-tien-gan-40000-ty-dong-51505.html",
    "Báo Pháp luật – Doanh nhân. (2026). *PV GAS (GAS) quý I/2026: doanh thu tăng gần 50%, lãi sau thuế đạt "
    "gần 3.000 tỷ đồng*. https://doanhnhan.baophapluat.vn/pv-gas-gas-quy-i-2026-doanh-thu-tang-gan-50-lai-"
    "sau-thue-dat-gan-3-000-ty-dong.html",
    "DNSE. (2026). *PV GAS không còn đáp ứng điều kiện công ty đại chúng*. https://www.dnse.com.vn/senses/"
    "tin-tuc/pv-gas-khong-con-dap-ung-dieu-kien-cong-ty-dai-chung-35279510",
    "CafeF. (2026, tháng 9). *PV Gas sắp chi hơn 6.000 tỷ đồng trả cổ tức năm 2025*. https://cafef.vn/pv-"
    "gas-sap-chi-hon-6000-ty-dong-tra-co-tuc-nam-2025-188260910150319815.chn",
    "Ad-hoc News. (2026, tháng 10). *Petrovietnam Gas stock: Seven analysts see VND 87,308.10*. "
    "https://www.ad-hoc-news.de/boerse/news/corporate-news/petrovietnam-gas-stock-seven-analysts-see-vnd-87-"
    "308-10-for-petrovietnam-gas-stock/70363045",
    "Dân trí. (2026, 16 tháng 10). *Nghịch lý cổ phiếu \"vua thép\" HPG: Liên tục dò đáy dù lãi vẫn tăng*. "
    "https://dantri.com.vn/kinh-doanh/nghich-ly-co-phieu-vua-thep-hpg-lien-tuc-do-day-du-lai-van-tang-"
    "20261016152743557.htm",
    "Vietstock. (2026, tháng 10). *Gần 5 tháng không xu hướng tăng của HPG, ngành thép cùng trong \"vùng "
    "trũng\"*. https://vietstock.vn/2026/10/gan-5-thang-khong-xu-huong-tang-cua-hpg-nganh-thep-cung-trong-"
    "vung-trung-830-1501684.htm",
    "Tiền Phong. (2026). *VN-Index biến động mạnh, FPT trở nên hấp dẫn?* https://tienphong.vn/vn-index-bien-"
    "dong-manh-fpt-tro-nen-hap-dan-post1884895.tpo",
    "Vietnambiz. (2026, 15 tháng 10). *Lợi nhuận 9 tháng của PV Power gấp 2,3 lần cùng kỳ*. "
    "https://vietnambiz.vn/loi-nhuan-9-thang-cua-pv-power-gap-23-lan-cung-ky-20261015144949959.htm",
    "Khoa Tài chính, Trường Đại học Kinh tế – Đại học Đà Nẵng. (2025–2026). *Bài giảng học phần Đầu tư tài "
    "chính: Chương 2 – Lý thuyết danh mục đầu tư; Chương 3 – Lý thuyết định giá tài sản; Chương 4 – Đầu tư "
    "cổ phiếu*.",
    "Tạp chí Kinh tế Tài chính. (2026). *Tổng mức bán lẻ hàng hóa và doanh thu dịch vụ tiêu dùng 9 tháng tăng "
    "13,4%*. https://tapchikinhtetaichinh.vn/tong-muc-ban-le-hang-hoa-va-doanh-thu-dich-vu-tieu-dung-9-thang-"
    "tang-13-4-168577.html",
    "Tạp chí Kinh tế Tài chính. (2026). *Lãi suất tăng nhanh, Ngân hàng Nhà nước yêu cầu ổn định thị "
    "trường*. https://tapchikinhtetaichinh.vn/lai-suat-tang-nhanh-ngan-hang-nha-nuoc-yeu-cau-on-dinh-thi-"
    "truong-152382.html",
    "Tạp chí Công Thương. (2025). *Thế Giới Di Động (MWG) mở mới 2–3 cửa hàng Bách Hóa Xanh mỗi ngày*. "
    "https://tapchicongthuong.vn/the-gioi-di-dong--mwg--mo-moi-2-3-cua-hang-bach-hoa-xanh-moi-ngay-142119.htm",
]
