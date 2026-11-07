"""Nội dung báo cáo Bài tập nhóm Đầu tư tài chính – Nhóm 7 – FIN3002_2 (dùng bởi tao_bao_cao_nhom.py).

Khối nội dung: ("phan", tiêu đề[, ngắt trang]) · ("h2"/"h3", tiêu đề) · ("p", đoạn) · ("abc"/"gach", [ý])
("ct", công thức, số) · ("bang", số, tên, hàng (hàng đầu là tiêu đề), độ rộng cột cm, cột căn phải, nguồn)
("hinh", số, tên, file trong figures/, nguồn).
Đánh dấu chữ: **đậm**, *nghiêng*, _{chỉ số dưới}, ^{chỉ số trên}. [n] trỏ tới TAI_LIEU.
Số liệu Phần 3–4 lấy từ file Excel Nhom7_FIN3002_2_BaiTapNhom.xlsx (kết quả Excel Solver của nhóm).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from noi_dung import TAI_LIEU as TAI_LIEU_BAI_1  # noqa: E402  (danh mục [1]–[42] của Bài tập tình huống 1)

BIA = {
    "loai_bao_cao": "BÁO CÁO BÀI TẬP NHÓM",
    "hoc_phan": "ĐẦU TƯ TÀI CHÍNH",
    "thu_tiet": "Thứ … – Tiết …",
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
    "ngay": "Đà Nẵng, ngày 23 tháng 10 năm 2026",
}

# Phân công ĐỀ XUẤT – nhóm sửa lại theo đúng thực tế và điền mức độ đóng góp trước khi nộp.
HOAT_DONG = {
    "thanh_vien": [
        ("Nguyễn Thị Mỹ Thanh", "231124029131", "Điều phối; xử lý dữ liệu, Excel và Solver (Phần 3, 4); tổng hợp báo cáo"),
        ("Nguyễn Công Hiếu", "231124029115", "Phân tích các yếu tố vĩ mô (mục 1.1)"),
        ("Nguyễn Thị Bảo Na", "231124029125", "Triển vọng thị trường, ngành; chiến lược đầu tư (mục 1.2, 1.3)"),
        ("Nguyễn Bảo Anh Thư", "231124029133", "Sàng lọc cổ phiếu; phân tích MBB (mục 2.1, 2.2)"),
        ("Dương Mẫn Trân", "231124029139", "Phân tích MWG (mục 2.3); tổng hợp cổ phiếu (mục 2.5)"),
        ("Ngô Triệu Vy", "231124029144", "Phân tích GAS (mục 2.4); lựa chọn, phân bổ danh mục (mục 4.3, 4.4)"),
    ],
    "ghi_chu": ["Mức độ đóng góp do cả nhóm thống nhất, tổng bằng 100%."],
}

NOI_DUNG = [
    # ============================== PHẦN 1 ==============================
    ("phan", "PHẦN 1. PHÂN TÍCH BỐI CẢNH ĐẦU TƯ"),
    ("p", "Nhóm đóng vai trò công ty quản lý quỹ, xây dựng danh mục cổ phiếu niêm yết với vốn **10 tỷ đồng**, "
          "thời gian đầu tư **1 tháng** (26/10 – 25/11/2026), số liệu cập nhật đến 23/10/2026. Nhóm áp dụng "
          "phương pháp **top-down** [39]: phân tích vĩ mô để xác định ngành tăng trưởng, chọn doanh nghiệp tốt "
          "trong ngành, rồi dùng mô hình Markowitz để phân bổ vốn."),
    ("h2", "1.1. Đánh giá các yếu tố kinh tế vĩ mô"),
    ("h3", "1.1.1. Tăng trưởng kinh tế"),
    ("p", "GDP quý III/2026 tăng **9,95%**, cao nhất kể từ năm 2022; 9 tháng tăng 9,01%, trong đó công nghiệp – "
          "xây dựng tăng 12,5%, dịch vụ tăng 9,5% [1], [2]. Tổng mức bán lẻ hàng hóa và dịch vụ 9 tháng tăng "
          "13,4% (loại trừ giá tăng 7,8%) [40]. Tăng trưởng mạnh làm doanh thu, lợi nhuận doanh nghiệp và nhu cầu "
          "vay vốn tăng: **tích cực** cho thị trường, nhất là ngân hàng và bán lẻ."),
    ("h3", "1.1.2. Lạm phát"),
    ("p", "CPI tháng 9/2026 tăng **5,08%**, bình quân 9 tháng 4,52%, **vượt mục tiêu 4,5%** [1], [3]. Nguyên nhân "
          "chính là giá dầu: Brent bình quân tháng 9 lên 114 USD/thùng do xung đột ở Trung Đông; EIA dự báo quý "
          "IV/2026 khoảng 105 USD và năm 2027 giảm về 84 USD/thùng [10]. Lạm phát cao làm giảm sức mua và hạn chế "
          "nới lỏng tiền tệ: **tiêu cực**."),
    ("h3", "1.1.3. Lãi suất và chính sách tiền tệ"),
    ("p", "Ngân hàng Nhà nước giữ lãi suất tái cấp vốn 4,5% [4]. Do tín dụng tăng nhanh hơn huy động, lãi suất huy "
          "động 6–12 tháng tăng khoảng 1,2 điểm % đến tháng 3/2026, lãi suất liên ngân hàng qua đêm từng lên "
          "16,39% (2/2026) [9], [41]; gần đây khoảng 20 ngân hàng đã giảm lãi suất huy động 0,5 điểm % [8]. Định "
          "hướng tín dụng cả năm khoảng 15% [6]. Theo mô hình chiết khấu cổ tức V_{0} = D_{1}/(k − g), lãi suất "
          "cao làm tăng tỷ suất lợi tức yêu cầu k nên làm giảm giá trị cổ phiếu. Chính sách tiền tệ ở trạng thái "
          "**trung tính, khó nới lỏng thêm**."),
    ("h3", "1.1.4. Tỷ giá"),
    ("p", "Tỷ giá trung tâm USD/VND ngày 23/10/2026 là **25.627**, giảm nhẹ trong tháng [7]. Tỷ giá ổn định giảm "
          "rủi ro mất giá cho nhà đầu tư nước ngoài, **hỗ trợ** dòng vốn ngoại."),
    ("h3", "1.1.5. Diễn biến thị trường chứng khoán"),
    ("p", "VN-Index lập đỉnh 1.902,93 điểm (13/1/2026), về gần 1.600 điểm trong tháng 3 rồi dao động 1.680–1.780 "
          "điểm; ngày 22/10 đóng cửa **1.760,63 điểm** [11], [13]. P/E thị trường khoảng 13,1 lần, thấp hơn bình "
          "quân 5 năm (14,4 lần) [14]. FTSE Russell nâng hạng Việt Nam lên thị trường mới nổi từ 21/9/2026, giải "
          "ngân 4 đợt đến 9/2027, dòng vốn dự kiến 3–10 tỷ USD [15], [16]; tuy vậy thanh khoản từ tháng 6 giảm "
          "khoảng 41% so với quý I và khối ngoại vẫn bán ròng giữa tháng 10 [12], [13]."),
    ("p", "**Nhận xét chung.** Vĩ mô có hai mặt đối lập: tăng trưởng thực rất mạnh nhưng lạm phát giữ lãi suất ở "
          "mức cao, tức g đang tăng còn k khó giảm. Cổ phiếu có lợi thế là cổ phiếu **có lợi nhuận tăng trưởng "
          "thật và định giá còn thấp**."),

    ("h2", "1.2. Triển vọng thị trường và triển vọng ngành"),
    ("h3", "1.2.1. Triển vọng thị trường trong thời gian đầu tư"),
    ("p", "Ba chất xúc tác trong tháng đầu tư là mùa báo cáo tài chính quý III, giải ngân của các quỹ theo chỉ số "
          "FTSE và số liệu CPI tháng 10. Nhóm xây dựng ba kịch bản (Bảng 1.1); kịch bản cơ sở là thị trường đi "
          "ngang và phân hóa, nên nhóm ưu tiên cổ phiếu vốn hóa lớn, thanh khoản cao, có kết quả quý III tốt."),
    ("bang", "1.1", "Kịch bản VN-Index đến ngày 25/11/2026",
     [("Kịch bản", "VN-Index", "Điều kiện xảy ra", "Xác suất (nhận định)"),
      ("Tích cực", "1.850 – 1.900", "Kết quả quý III tốt, dòng vốn FTSE giải ngân, giá dầu hạ", "30%"),
      ("Cơ sở", "1.720 – 1.820", "Kết quả quý III đúng kỳ vọng, lãi suất đi ngang", "50%"),
      ("Tiêu cực", "1.620 – 1.680", "CPI vượt 5,5%, NHNN thắt chặt, xung đột Trung Đông leo thang", "20%")],
     [2.2, 2.8, 8.6, 2.9], (3,), "Nhóm nhận định dựa trên [1], [10], [13], [15]."),
    ("h3", "1.2.2. Triển vọng ngành"),
    ("bang", "1.2", "Đánh giá triển vọng các ngành ứng viên",
     [("Ngành", "Động lực tăng trưởng trong tương lai", "Rủi ro chính", "Kết luận"),
      ("Ngân hàng", "GDP tăng gần 10% kéo theo nhu cầu vốn, tín dụng cả năm 15–18%; nợ xấu giảm nhờ Nghị quyết 42 "
       "được luật hóa; tỷ trọng lớn nhất trong chỉ số nên hưởng lợi đầu tiên từ dòng vốn FTSE",
       "Chi phí vốn tăng làm biên lãi ròng giảm", "Chọn"),
      ("Bán lẻ", "Dân số trẻ, thu nhập tăng; bán lẻ 9 tháng +13,4%; chuỗi hiện đại còn chiếm thị phần nhỏ so với "
       "chợ truyền thống", "Lạm phát làm giảm sức mua", "Chọn"),
      ("Khí đốt, năng lượng", "Cầu điện tăng theo kinh tế; điện khí LNG là trụ cột Quy hoạch điện VIII đến 2030; "
       "giá dầu cao làm tăng giá bán khí", "Giá dầu đảo chiều; giá bán bị điều tiết", "Chọn"),
      ("Thép", "Hưởng lợi đầu tư công, xây dựng +12,5%", "Dư cung lớn đến 2029 (VinMetal)", "Không chọn"),
      ("Công nghệ", "Chuyển đổi số, AI", "Lo ngại AI làm giảm nhu cầu gia công phần mềm", "Theo dõi")],
     [2.6, 7.4, 4.4, 2.1], (), "Nhóm tổng hợp từ [1], [6], [10], [35], [37], [40]."),
    ("p", "Ba ngành được chọn đều có động lực tăng trưởng dài hạn gắn với số liệu vĩ mô ở mục 1.1, và phản ứng "
          "**khác nhau** trước cùng một cú sốc: giá dầu tăng gây bất lợi cho bán lẻ (qua lạm phát) nhưng có lợi "
          "cho khí đốt. Đây là cơ sở để đa dạng hóa danh mục."),
    ("h2", "1.3. Chiến lược đầu tư của nhóm"),
    ("p", "Nhóm chọn **chiến lược cân bằng**, kết hợp cổ phiếu **giá trị** (MBB: P/B khoảng 1,0 lần trong khi ROE "
          "khoảng 20%), **tăng trưởng** (MWG: lợi nhuận 6 tháng +88%) và **thu nhập cổ tức, đa dạng hóa** (GAS: "
          "lợi nhuận tăng theo giá dầu, cổ tức tiền mặt đều). Lý do: (1) vĩ mô có rủi ro hai chiều nên danh mục "
          "cần thành phần chịu được kịch bản tiêu cực; (2) theo Markowitz, kết hợp tài sản tương quan thấp giúp "
          "giảm rủi ro danh mục [44]. Tỷ trọng sơ bộ ban đầu là 40% MBB, 35% MWG, 25% GAS; tỷ trọng cuối cùng "
          "được xác định bằng tối ưu hóa ở Phần 4."),

    # ============================== PHẦN 2 ==============================
    ("phan", "PHẦN 2. PHÂN TÍCH CỔ PHIẾU"),
    ("h2", "2.1. Tiêu chí lựa chọn cổ phiếu và giả định định giá"),
    ("p", "Nhóm lọc cổ phiếu theo năm tiêu chí: (1) niêm yết HOSE, vốn hóa lớn, thanh khoản cao; (2) lợi nhuận 2026 "
          "tăng trưởng hai chữ số; (3) giá **ổn định**, không trong xu hướng giảm kéo dài; (4) định giá không cao "
          "hơn trung bình lịch sử; (5) có lịch sử giá đủ dài để ước lượng lợi tức và rủi ro."),
    ("bang", "2.1", "Kết quả sàng lọc cổ phiếu ứng viên",
     [("Mã", "Lợi nhuận gần nhất", "Diễn biến giá", "Kết quả"),
      ("MBB", "LNTT 6 tháng +27,1%", "Đi ngang so với đầu năm (đã điều chỉnh cổ tức cổ phiếu 15% tháng 8)", "Đạt"),
      ("MWG", "LNST 6 tháng +88%", "Thấp hơn đỉnh 52 tuần khoảng 21%, đang hồi lại", "Đạt"),
      ("GAS", "LNTT 9 tháng +31%", "Dao động 76.000 – 82.000 đ trong tháng 10", "Đạt"),
      ("HPG", "LNST quý II +51%", "−12,2% từ đầu năm, 16 quỹ bán ròng 4 tháng liên tiếp", "Loại"),
      ("FPT", "LNST 9 tháng +13,3%", "Từ khoảng 98.000 đ đầu năm còn 57.400 đ", "Loại")],
     [1.5, 3.8, 9.1, 2.1], (), "Nhóm tổng hợp từ [17], [24], [28], [35], [36], [37]."),
    ("p", "HPG và FPT có lợi nhuận tăng nhưng giá giảm kéo dài; với kỳ hạn 1 tháng, nhóm không có cơ sở để tin xu "
          "hướng đảo chiều nên loại hai mã này. Tỷ suất lợi tức yêu cầu k được tính theo **CAPM** [45]:"),
    ("ct", "k = R_{f} + β × [E(R_{M}) − R_{f}]", "2.1"),
    ("p", "với R_{f} = 4,36% (lợi suất trái phiếu Chính phủ 10 năm, tháng 7/2026 [5]), phần bù rủi ro thị trường "
          "giả định 8% và β thận trọng theo ngành: MBB 1,1; MWG 1,2; GAS 0,8. Giá hiện tại là giá đóng cửa ngày "
          "23/10/2026: MBB 19.800 đ, MWG 75.500 đ, GAS 78.300 đ [43]."),

    ("h2", "2.2. Ngân hàng TMCP Quân đội (MBB – HOSE)"),
    ("h3", "2.2.1. Mô hình kinh doanh"),
    ("p", "MB là ngân hàng thương mại cổ phần có cổ đông lớn là các doanh nghiệp thuộc Bộ Quốc phòng. Nguồn thu "
          "chính là **chênh lệch lãi suất**: huy động tiền gửi, đặc biệt tiền gửi không kỳ hạn (CASA) nhờ ứng dụng "
          "ngân hàng số gần 40 triệu khách hàng, rồi cho vay với lãi suất cao hơn. Hệ sinh thái gồm Chứng khoán "
          "MBS (76,35%), tài chính tiêu dùng MCredit (50%), bảo hiểm và ngân hàng MBV (100%) [20]."),
    ("h3", "2.2.2. Kết quả kinh doanh và tình hình tài chính"),
    ("bang", "2.2", "Kết quả kinh doanh chính của MBB",
     [("Chỉ tiêu", "Năm 2025", "6 tháng 2026", "Tăng trưởng"),
      ("LNTT hợp nhất (tỷ đồng)", "34.268", "20.188", "+18,9% / +27,1%"),
      ("Thu nhập lãi thuần (tỷ đồng)", "–", "31.807", "+32,2%"),
      ("Dư nợ tín dụng (nghìn tỷ đồng)", "–", "1.256", "+13% so với đầu năm"),
      ("Tỷ lệ nợ xấu", "1,29%", "1,40%", "Bao phủ nợ xấu 93,6%"),
      ("Kế hoạch LNTT 2026 (tỷ đồng)", "", "39.500", "+15%; đạt 51,1% sau 6 tháng")],
     [5.4, 2.5, 2.8, 5.8], (1, 2), "Nhóm tổng hợp từ [17], [18]."),
    ("p", "Lợi nhuận vượt tiến độ kế hoạch nhờ thu nhập lãi thuần tăng 32,2% và chi phí dự phòng giảm; ROE duy trì "
          "khoảng 20–21%, thuộc nhóm cao nhất ngành [18], [21]."),
    ("h3", "2.2.3. Chính sách cổ tức, rủi ro và triển vọng tăng trưởng"),
    ("p", "**Cổ tức:** kế hoạch 2026 chia 25%, gồm 10% tiền mặt (1.000 đ/cp) và 15% cổ phiếu [21]; tỷ suất cổ tức "
          "tiền mặt khoảng **5,1%**. **Rủi ro:** biên lãi ròng dự phóng giảm còn 3,95% do cho vay tăng nhanh hơn huy "
          "động [20]; nợ nhóm 5 năm 2025 tăng 39,4% lên 6.421 tỷ đồng theo Kiểm toán Nhà nước [19]. **Triển vọng:** "
          "hưởng lợi trực tiếp từ tín dụng tăng 15–18% và dòng vốn FTSE vào nhóm ngân hàng vốn hóa lớn."),
    ("h3", "2.2.4. Nhận định về mức giá hợp lý"),
    ("p", "Từ mô hình cổ tức tăng trưởng đều V_{0} = D_{1}/(k − g), với D_{1} = E_{1}(1 − b), E_{1} = ROE × B_{0} "
          "và g = ROE × b (Chương 4), suy ra hệ số P/B hợp lý:"),
    ("ct", "P/B = (ROE − g) / (k − g)", "2.2"),
    ("p", "Với β = 1,1: k = 4,36% + 1,1 × 8% = 13,16%; giá trị sổ sách mỗi cổ phiếu B_{0} = 19.462 đ [22]."),
    ("bang", "2.3", "Định giá MBB theo P/B hợp lý",
     [("Kịch bản", "ROE bền vững", "g dài hạn", "P/B hợp lý", "Giá trị (đ/cp)"),
      ("Thận trọng", "15%", "6%", "1,26", "24.500"),
      ("Cơ sở", "17%", "6%", "1,54", "29.900"),
      ("Lạc quan", "20%", "7%", "2,11", "41.000")],
     [3.2, 3.2, 3.0, 3.2, 3.9], (1, 2, 3, 4), "Nhóm tính toán."),
    ("p", "Ở P/B hiện tại 1,02 lần, thị trường ngầm định ROE bền vững chỉ khoảng 13%, thấp hơn nhiều mức 20% đang "
          "đạt, tức rủi ro nợ xấu đã phản ánh khá đầy đủ vào giá. Nhóm chọn **giá hợp lý 25.000 đ/cp (+26%)**, gần "
          "kịch bản thận trọng và mức 26.700 đ của FUNAN [20]."),

    ("h2", "2.3. CTCP Đầu tư Thế Giới Di Động (MWG – HOSE)"),
    ("h3", "2.3.1. Mô hình kinh doanh"),
    ("p", "MWG là nhà bán lẻ lớn nhất Việt Nam với ba trụ cột: (1) **Thế Giới Di Động, Điện Máy Xanh** (điện thoại, "
          "điện máy, khoảng 3.000 cửa hàng), tạo dòng tiền ổn định và đang chuẩn bị IPO Điện Máy Xanh; (2) **Bách "
          "Hóa Xanh** (thực phẩm, hàng tiêu dùng, hơn 2.100 cửa hàng), đã có lãi từ 2025 và là động lực tăng trưởng "
          "chính; (3) **EraBlue** tại Indonesia [26], [42]. Lợi thế cạnh tranh là quy mô mua hàng và logistics."),
    ("h3", "2.3.2. Kết quả kinh doanh và tình hình tài chính"),
    ("bang", "2.4", "Kết quả kinh doanh chính của MWG",
     [("Chỉ tiêu (tỷ đồng)", "Năm 2024", "Năm 2025", "Năm 2026"),
      ("Doanh thu thuần", "134.341", "156.457 (+16,4%)", "9 tháng: 147.953 (+30%)"),
      ("Lợi nhuận sau thuế", "3.733", "7.075 (+89,5%)", "6 tháng: 6.017 (+88%)"),
      ("Kế hoạch 2026", "", "", "Doanh thu 185.000; LNST 9.200 (+30%)")],
     [3.7, 2.4, 3.7, 6.7], (1,), "Nhóm tổng hợp từ [23], [24], [26]."),
    ("p", "Doanh thu quý III/2026 ước 52.648 tỷ đồng (+32%), Bách Hóa Xanh tăng 34% [24]; các công ty chứng khoán "
          "dự phóng LNST quý III tăng 43–95% so với cùng kỳ [25]."),
    ("h3", "2.3.3. Chính sách cổ tức, rủi ro và triển vọng tăng trưởng"),
    ("p", "**Cổ tức:** năm 2026 dự kiến chi khoảng 3.000 tỷ đồng tiền mặt, cao nhất từ trước đến nay [26], ước "
          "khoảng 2.000 đ/cp (tỷ suất **2,6%**). **Rủi ro:** từ quý III phải chia khoảng 14% lợi nhuận Điện Máy "
          "Xanh cho cổ đông thiểu số [25]; lợi nhuận 2027 có thể đi ngang; lạm phát làm giảm sức mua hàng không "
          "thiết yếu. **Triển vọng:** Bách Hóa Xanh tiếp tục mở rộng, IPO Điện Máy Xanh giúp định giá lại các mảng."),
    ("h3", "2.3.4. Nhận định về mức giá hợp lý"),
    ("p", "Nhóm dùng phương pháp P/E (Chương 4): giá trị = P/E chuẩn × EPS dự phóng. EPS 2026 ước khoảng 6.000 đ "
          "(kế hoạch LNST sau khi trừ cổ đông thiểu số), nên giá 75.500 đ tương ứng P/E dự phóng khoảng 12,6 lần, "
          "thấp hơn bình quân lịch sử khoảng 17 lần [27]. Chọn **P/E chuẩn 15 lần** để trừ hao rủi ro lợi nhuận "
          "2027 chững lại, giá hợp lý = 15 × 6.000 = **90.000 đ/cp (+19%)**. Kiểm tra bằng công thức:"),
    ("ct", "P_{0}/E_{1} = (D_{1}/E_{1}) / (k − g)", "2.3"),
    ("p", "với k = 4,36% + 1,2 × 8% = 13,96% và tỷ lệ chi trả 33%, P/E 15 lần tương ứng tăng trưởng dài hạn g ≈ "
          "11,7%/năm, phù hợp tốc độ tăng của bán lẻ. Giá mục tiêu của các công ty chứng khoán: 94.400 – 109.000 đ [27]."),

    ("h2", "2.4. Tổng Công ty Khí Việt Nam (GAS – HOSE)"),
    ("h3", "2.4.1. Mô hình kinh doanh"),
    ("p", "PV GAS nắm gần như toàn bộ chuỗi giá trị khí trong nước: thu gom, vận chuyển bằng đường ống, xử lý và "
          "phân phối **khí khô** cho nhà máy điện, đạm; kinh doanh **LPG**; nhập khẩu, phân phối **LNG**. Quý I/2026 "
          "khí khô và LNG chiếm khoảng 55% doanh thu, LPG hơn 40% [31]. Giá bán gắn với giá dầu nên lợi nhuận tăng "
          "khi giá dầu tăng."),
    ("h3", "2.4.2. Kết quả kinh doanh và tình hình tài chính"),
    ("bang", "2.5", "Kết quả kinh doanh chính của GAS",
     [("Chỉ tiêu", "Năm 2025", "9 tháng 2026"),
      ("Doanh thu hợp nhất (tỷ đồng)", "135.129 (+30%)", "Trên 120.900 (+30%)"),
      ("Lợi nhuận (tỷ đồng)", "LNST 11.571 (+9%)", "LNTT trên 16.600 (+31%); quý III +68%"),
      ("So với kế hoạch năm", "", "LNTT đạt 197% kế hoạch"),
      ("Tiền mặt và đầu tư ngắn hạn", "Gần 40.000 tỷ đồng", "")],
     [5.4, 4.6, 6.5], (), "Nhóm tổng hợp từ [28], [29], [30]."),
    ("h3", "2.4.3. Chính sách cổ tức, rủi ro và triển vọng tăng trưởng"),
    ("p", "**Cổ tức:** cổ tức tiền mặt năm 2025 là 25% (2.500 đ/cp, chốt quyền 23/9/2026) [33], tỷ suất **3,2%**. "
          "**Rủi ro:** giá dầu đảo chiều [10]; biên gộp LPG quý I giảm từ 7,5% xuống 5,3% [31]; Tập đoàn Dầu khí nắm "
          "95,76% cổ phần nên PV GAS không còn đủ điều kiện công ty đại chúng (cần tối thiểu 10% do cổ đông nhỏ nắm) "
          "và có 1 năm từ 14/8/2026 để khắc phục [32]. **Triển vọng:** nhu cầu khí cho điện tăng theo Quy hoạch "
          "điện VIII; LNG là động lực trung hạn."),
    ("h3", "2.4.4. Nhận định về mức giá hợp lý"),
    ("p", "Với β = 0,8: k = 4,36% + 0,8 × 8% = 10,76%. Nhóm kết hợp mô hình cổ tức tăng trưởng đều (DDM) với "
          "D_{0} = 2.500 đ, g = 7%:"),
    ("ct", "V_{0} = D_{0}(1 + g) / (k − g) = 2.500 × 1,07 / (0,1076 − 0,07) = 71.100 đ", "2.4"),
    ("p", "và phương pháp P/E với EPS 4 quý khoảng 5.350 đ, P/E chuẩn 16 lần: 85.600 đ [34]. Giá hợp lý bằng bình "
          "quân hai phương pháp, **78.400 đ/cp**, xấp xỉ giá hiện tại 78.300 đ. GAS được định giá sát mức hợp lý nên "
          "không phải mã kỳ vọng tăng giá mạnh; vai trò của GAS là **đa dạng hóa và thu nhập cổ tức** (kiểm chứng ở "
          "Phần 3, 4)."),

    ("h2", "2.5. Tổng hợp ba cổ phiếu"),
    ("hinh", "2.1", "Vùng giá hợp lý của MBB, MWG, GAS so với giá hiện tại (dải mờ: vùng giá trị theo các phương "
     "pháp; chấm: mức nhóm chọn)", "hinh_2_1_vung_gia_hop_ly.png", "Nhóm tính toán."),
    ("bang", "2.6", "So sánh ba cổ phiếu được chọn",
     [("Tiêu chí", "MBB", "MWG", "GAS"),
      ("Ngành", "Ngân hàng", "Bán lẻ", "Khí đốt, năng lượng"),
      ("Giá 23/10/2026", "19.800 đ", "75.500 đ", "78.300 đ"),
      ("Tăng trưởng lợi nhuận", "+27,1% (LNTT 6T)", "+88% (LNST 6T)", "+31% (LNTT 9T)"),
      ("Tỷ suất cổ tức tiền mặt", "5,1%", "2,6%", "3,2%"),
      ("Giá hợp lý / tiềm năng", "25.000 đ / +26%", "90.000 đ / +19%", "78.400 đ / ≈ 0%"),
      ("Vai trò", "Giá trị", "Tăng trưởng", "Đa dạng hóa, cổ tức"),
      ("Rủi ro lớn nhất", "Nợ nhóm 5, biên lãi ròng", "Lợi nhuận 2027 chững", "Giá dầu, tư cách đại chúng")],
     [4.1, 4.1, 4.1, 4.2], (), "Nhóm tổng hợp và tính toán."),

    # ============================== PHẦN 3 ==============================
    ("phan", "PHẦN 3. PHÂN TÍCH RỦI RO VÀ LỢI NHUẬN"),
    ("h2", "3.1. Dữ liệu và cách xử lý"),
    ("p", "Nhóm thu thập **giá đóng cửa điều chỉnh** hằng ngày của MBB, MWG, GAS và VN-Index từ CafeF trong giai "
          "đoạn 01/10/2025 – 30/09/2026 [43]. Hai điểm xử lý quan trọng:"),
    ("abc", ["**Dùng giá điều chỉnh thay cho giá thô.** Ngày 11/08/2026 MBB giao dịch không hưởng quyền cổ tức 15% "
             "bằng cổ phiếu: giá thô giảm từ 24.250 đ xuống 20.350 đ (−16%) dù nhà đầu tư không bị lỗ, còn giá điều "
             "chỉnh tăng 0,7%. Dùng giá thô sẽ tạo một ngày lỗ −16% không có thật.",
             "**Đồng bộ ngày giao dịch.** CafeF không có giá 3 cổ phiếu ngày 29–30/01/2026 nên hai ngày này bị loại; "
             "mẫu còn **246 phiên giá, 245 quan sát lợi tức**."]),
    ("hinh", "3.1", "Diễn biến giá điều chỉnh của MBB, MWG, GAS và VN-Index (01/10/2025 = 100)",
     "hinh_3_1_dien_bien_gia.png", "Nhóm tính toán từ dữ liệu CafeF [43]."),
    ("p", "Trong năm, GAS tăng 39% (đỉnh tháng 1/2026 khi giá dầu tăng vọt), VN-Index tăng 6%, còn MBB và MWG giảm "
          "lần lượt 7% và 5%."),
    ("h2", "3.2. Phương pháp tính"),
    ("p", "Tỷ suất lợi tức ngày t của cổ phiếu i, với P_{t} là giá điều chỉnh:"),
    ("ct", "R_{i,t} = (P_{t} − P_{t−1}) / P_{t−1}", "3.1"),
    ("p", "Tỷ suất lợi tức kỳ vọng và độ lệch chuẩn được ước lượng từ n = 245 quan sát (Excel: AVERAGE, STDEV.S):"),
    ("ct", "E(R_{i}) = (1/n) × Σ R_{i,t};     σ_{i} = √[ Σ (R_{i,t} − E(R_{i}))^{2} / (n − 1) ]", "3.2"),
    ("p", "Hiệp phương sai và hệ số tương quan giữa hai cổ phiếu i, j (Excel: COVARIANCE.S, CORREL):"),
    ("ct", "Cov(R_{i}, R_{j}) = Σ (R_{i,t} − E(R_{i}))(R_{j,t} − E(R_{j})) / (n − 1);     ρ_{ij} = Cov(R_{i}, R_{j}) / (σ_{i}σ_{j})", "3.3"),
    ("p", "Chỉ tiêu ngày được quy đổi theo năm với N = 250 phiên: E_{năm} = E_{ngày} × N; σ_{năm} = σ_{ngày} × √N; "
          "Cov_{năm} = Cov_{ngày} × N. Ngoài ra nhóm ước lượng hệ số β so với VN-Index: β_{i} = Cov(R_{i}, R_{M}) / σ^{2}_{M}."),
    ("h2", "3.3. Tỷ suất lợi tức kỳ vọng và độ lệch chuẩn"),
    ("bang", "3.1", "Tỷ suất lợi tức kỳ vọng, độ lệch chuẩn và hệ số β",
     [("Chỉ tiêu", "MBB", "MWG", "GAS", "VN-Index"),
      ("E(R) – ngày", "−0,015%", "0,003%", "0,184%", "0,033%"),
      ("σ – ngày", "1,710%", "2,258%", "3,140%", "1,327%"),
      ("E(R) – năm", "−3,82%", "0,70%", "46,01%", "8,37%"),
      ("σ – năm", "27,04%", "35,70%", "49,65%", "20,99%"),
      ("Lợi tức cả kỳ", "−7,05%", "−5,37%", "+39,24%", "+6,22%"),
      ("Hệ số β", "0,79", "1,06", "0,62", "1,00")],
     [4.0, 3.1, 3.1, 3.1, 3.2], (1, 2, 3, 4), "Nhóm tính toán trên Excel (trang Thống kê)."),
    ("p", "GAS có lợi tức kỳ vọng cao nhất nhưng cũng **rủi ro cao nhất** (σ = 49,65%/năm) do nhiều phiên tăng, giảm "
          "kịch biên độ khi giá dầu biến động. MBB rủi ro thấp nhất nhưng lợi tức kỳ vọng âm. Giữa ba mã không có "
          "tài sản bị thống trị: không mã nào vừa lợi tức thấp hơn vừa rủi ro cao hơn một mã khác. Lưu ý: E(R) ước "
          "lượng từ 1 năm dữ liệu dao động lớn; mức 46% của GAS chủ yếu đến từ cú sốc giá dầu, khó lặp lại."),
    ("p", "Hệ số β ước lượng (0,79; 1,06; 0,62) **thấp hơn** β giả định ở Phần 2 (1,1; 1,2; 0,8), nên tỷ suất lợi "
          "tức yêu cầu thực tế thấp hơn và các mức giá hợp lý ở Phần 2 là **ước tính thận trọng**. GAS có β thấp "
          "nhất dù σ cao nhất: phần lớn rủi ro của GAS là rủi ro riêng (giá dầu), không đi cùng thị trường."),
    ("h2", "3.4. Hiệp phương sai và hệ số tương quan"),
    ("bang", "3.2", "Ma trận hiệp phương sai (năm) và hệ số tương quan",
     [("", "Cov: MBB", "Cov: MWG", "Cov: GAS", "ρ: MBB", "ρ: MWG", "ρ: GAS"),
      ("MBB", "0,0731", "0,0568", "0,0163", "1,000", "0,588", "0,121"),
      ("MWG", "0,0568", "0,1274", "0,0197", "0,588", "1,000", "0,111"),
      ("GAS", "0,0163", "0,0197", "0,2465", "0,121", "0,111", "1,000")],
     [1.9, 2.4, 2.4, 2.4, 2.4, 2.4, 2.6], (1, 2, 3, 4, 5, 6),
     "Nhóm tính toán trên Excel (trang Hiệp phương sai); đường chéo của ma trận hiệp phương sai là phương sai σ^{2}."),
    ("p", "Mọi cặp đều tương quan dương nhưng ở mức rất khác nhau. MBB – MWG tương quan trung bình (0,59) vì cùng "
          "phụ thuộc chu kỳ kinh tế nội địa. GAS gần như **độc lập** với hai mã còn lại (0,11 – 0,12) vì chịu tác "
          "động chủ yếu của giá dầu thế giới. Điều này xác nhận nhận định ở Phần 1: GAS là công cụ **đa dạng hóa** "
          "hiệu quả, dù bản thân GAS biến động mạnh."),

    # ============================== PHẦN 4 ==============================
    ("phan", "PHẦN 4. XÂY DỰNG DANH MỤC ĐẦU TƯ"),
    ("h2", "4.1. Mô hình Markowitz và cách thực hiện trên Excel"),
    ("p", "Với tỷ trọng w_{i} của mỗi cổ phiếu, lợi nhuận kỳ vọng và phương sai của danh mục là [44]:"),
    ("ct", "E(R_{p}) = Σ w_{i}E(R_{i});     σ^{2}_{p} = Σ_{i} Σ_{j} w_{i}w_{j}Cov(R_{i}, R_{j})", "4.1"),
    ("p", "Ràng buộc chung: Σ w_{i} = 1 và **w_{i} ≥ 0** vì thị trường Việt Nam không cho phép bán khống. Trên Excel, "
          "E(R_{p}) tính bằng SUMPRODUCT, σ^{2}_{p} bằng SUMPRODUCT của véc-tơ tỷ trọng với tích ma trận hiệp phương "
          "sai × tỷ trọng. Nhóm dùng **Solver** (phương pháp GRG Nonlinear) giải ba bài toán ở Bảng 4.1. Hệ số "
          "Sharpe = (E(R_{p}) − R_{f})/σ_{p} dùng để so sánh các danh mục."),
    ("bang", "4.1", "Ba mô hình Solver",
     [("Mô hình", "Hàm mục tiêu", "Ô thay đổi", "Ràng buộc", "Mục đích"),
      ("Solver 1", "Min σ^{2}_{p}", "w_{MBB}, w_{MWG}, w_{GAS}", "Σw = 1; w ≥ 0", "Danh mục phương sai nhỏ nhất"),
      ("Solver 2", "Min σ^{2}_{p}", "w_{MBB}, w_{MWG}, w_{GAS}", "Σw = 1; E(R_{p}) = mức mục tiêu; w ≥ 0",
       "Một điểm của đường biên phương sai bé nhất"),
      ("Solver 3", "Max E(R_{p})", "w_{MBB}, w_{MWG}, w_{GAS}", "Σw = 1; σ_{p} ≤ 25%; w ≥ 0",
       "Danh mục lợi nhuận cao nhất ở mức rủi ro chấp nhận")],
     [2.0, 2.4, 3.5, 4.4, 4.2], (), "Nhóm thiết lập trên Excel."),
    ("p", "Các bước thực hiện trên file Excel nộp kèm:"),
    ("abc", ["**Chuẩn bị đầu vào:** liên kết E(R) năm và ma trận hiệp phương sai năm từ Phần 3 sang các trang Solver.",
             "**Lập mô hình:** ba ô tỷ trọng (ô thay đổi), ô tổng tỷ trọng, ô E(R_{p}) = SUMPRODUCT(w; E(R)), ô "
             "σ^{2}_{p} = SUMPRODUCT(w; MMULT(w; Cov)) và ô σ_{p} = SQRT(σ^{2}_{p}).",
             "**Khai báo Solver** (Data → Solver) theo Bảng 4.1, tích \"Make Unconstrained Variables Non-Negative\" "
             "(w ≥ 0), chọn GRG Nonlinear vì hàm phương sai là hàm bậc hai, không tuyến tính.",
             "**Danh mục phương sai nhỏ nhất:** chạy Solver 1.",
             "**Đường biên:** chạy Solver 2 cho 26 mức E(R_{p}) mục tiêu cách đều từ E(R_{MBB}) = −3,82% (thấp nhất) "
             "đến E(R_{GAS}) = 46,01% (cao nhất), vì không bán khống thì E(R_{p}) chỉ nằm trong khoảng này; ghi lại "
             "tỷ trọng, E(R_{p}), σ_{p} của từng lần rồi vẽ đồ thị XY với σ_{p} ở trục hoành, E(R_{p}) ở trục tung. "
             "Việc chạy lặp được tự động hóa bằng macro VBA gọi Excel Solver; cả 26 lần đều thành công.",
             "**Chọn danh mục:** chạy Solver 3 với mức rủi ro chấp nhận σ_{p} ≤ 25%."]),
    ("p", "Để kiểm tra, nhóm đối chiếu kết quả Solver với một thuật toán tối ưu độc lập (Python, thư viện scipy): "
          "độ lệch chuẩn chênh không quá 0,00002%."),
    ("h2", "4.2. Đường biên phương sai bé nhất và đường biên hiệu quả"),
    ("hinh", "4.1", "Đường biên phương sai bé nhất và đường biên hiệu quả của danh mục MBB – MWG – GAS",
     "hinh_4_1_duong_bien.png", "Nhóm tính toán bằng Excel Solver (trang Đường biên)."),
    ("bang", "4.2", "Một số điểm trên đường biên phương sai bé nhất (theo năm)",
     [("E(R_{p}) mục tiêu", "w MBB", "w MWG", "w GAS", "σ_{p}", "Thuộc phần"),
      ("−3,82%", "100,00%", "0,00%", "0,00%", "27,04%", "Không hiệu quả"),
      ("2,41%", "74,79%", "13,98%", "11,23%", "24,84%", "Không hiệu quả"),
      ("6,20%", "66,66%", "14,54%", "18,80%", "24,51%", "Danh mục phương sai nhỏ nhất"),
      ("10,71%", "57,01%", "15,20%", "27,79%", "24,98%", "Hiệu quả"),
      ("19,02%", "39,24%", "16,42%", "44,34%", "28,11%", "Hiệu quả"),
      ("29,40%", "17,02%", "17,94%", "65,04%", "34,95%", "Hiệu quả"),
      ("46,01%", "0,00%", "0,00%", "100,00%", "49,65%", "Hiệu quả")],
     [2.8, 2.1, 2.1, 2.1, 2.1, 5.3], (0, 1, 2, 3, 4), "Trích từ 26 điểm ở trang Đường biên (Excel)."),
    ("p", "Toàn bộ đường cong là **đường biên phương sai bé nhất**: với mỗi mức lợi nhuận, đó là danh mục có rủi ro "
          "thấp nhất. Điểm có σ nhỏ nhất là **danh mục phương sai nhỏ nhất** (σ_{p} = 24,51%, E(R_{p}) = 6,20%). "
          "Phần phía trên điểm này là **đường biên hiệu quả** (nét liền): cùng mức rủi ro, nó cho lợi nhuận cao hơn "
          "phần phía dưới (nét đứt). Ba quan sát đáng chú ý:"),
    ("abc", ["Danh mục phương sai nhỏ nhất (24,51%) **ít rủi ro hơn cả cổ phiếu ít rủi ro nhất** là MBB (27,04%): "
             "đây là tác dụng của đa dạng hóa khi tương quan thấp.",
             "MWG đứng riêng nằm xa bên dưới đường biên (rủi ro 35,70% nhưng lợi tức gần 0), nhưng vẫn chiếm khoảng "
             "15–19% trên phần lớn đường biên hiệu quả (chỉ giảm về 0 khi tiến tới 100% GAS) vì góp phần giảm "
             "phương sai chung.",
             "Tỷ trọng sơ bộ 40/35/25 ở Phần 1 nằm **dưới** đường biên hiệu quả: cùng σ_{p} = 25,56% có thể đạt "
             "E(R_{p}) ≈ 12,95% thay vì 10,22%. Nhóm vì vậy thay tỷ trọng sơ bộ bằng tỷ trọng tối ưu."]),
    ("h2", "4.3. Lựa chọn danh mục đầu tư"),
    ("bang", "4.3", "So sánh các danh mục ứng viên (theo năm)",
     [("Danh mục", "MBB", "MWG", "GAS", "E(R_{p})", "σ_{p}", "Sharpe"),
      ("Phương sai nhỏ nhất (Solver 1)", "66,66%", "14,54%", "18,80%", "6,20%", "24,51%", "0,075"),
      ("**Được chọn (Solver 3, σ_{p} ≤ 25%)**", "**56,84%**", "**15,20%**", "**27,97%**", "**10,80%**", "**25,00%**",
       "**0,258**"),
      ("Toàn bộ vào GAS (Sharpe cao nhất)", "0%", "0%", "100%", "46,01%", "49,65%", "0,839"),
      ("Tỷ trọng sơ bộ ở Phần 1", "40,00%", "35,00%", "25,00%", "10,22%", "25,56%", "0,229")],
     [5.0, 1.9, 1.9, 1.9, 1.9, 1.9, 2.0], (1, 2, 3, 4, 5, 6), "Nhóm tính toán bằng Excel Solver (trang Danh mục chọn)."),
    ("p", "Nhóm chọn **danh mục có lợi nhuận kỳ vọng cao nhất với mức rủi ro chấp nhận σ_{p} ≤ 25%/năm** "
          "(khoảng 7,2%/tháng), vì:"),
    ("abc", ["Mức 25% phù hợp chiến lược cân bằng và tương đương rủi ro của tỷ trọng sơ bộ đã chấp nhận ở Phần 1.",
             "Gần danh mục phương sai nhỏ nhất, đường biên rất dốc: chỉ chấp nhận thêm 0,49 điểm % rủi ro "
             "(24,51% → 25,00%), lợi nhuận kỳ vọng tăng 4,6 điểm % (6,20% → 10,80%), Sharpe tăng từ 0,075 lên 0,258.",
             "Danh mục phương sai nhỏ nhất có E(R_{p}) = 6,20%, chỉ nhỉnh hơn lãi suất phi rủi ro 4,36%: phần bù rủi "
             "ro quá mỏng.",
             "Danh mục Sharpe cao nhất dồn 100% vào GAS, mất hoàn toàn đa dạng hóa, trong khi E(R) 46% của GAS chủ "
             "yếu do cú sốc giá dầu khó lặp lại; nhóm không chọn."]),
    ("h2", "4.4. Phân bổ vốn 10 tỷ đồng"),
    ("p", "Số cổ phiếu mua = ROUNDDOWN(w_{i} × 10 tỷ / (giá × 100), 0) × 100, vì HOSE giao dịch theo lô 100 cổ phiếu. "
          "Giá mua là giá đóng cửa ngày 23/10/2026 [43]."),
    ("bang", "4.4", "Phân bổ vốn theo danh mục được chọn (mua ngày 26/10/2026)",
     [("Cổ phiếu", "Tỷ trọng", "Giá (đ)", "Số cổ phiếu", "Giá trị mua (đ)", "Tỷ trọng thực tế"),
      ("MBB", "56,84%", "19.800", "287.000", "5.682.600.000", "56,83%"),
      ("MWG", "15,20%", "75.500", "20.100", "1.517.550.000", "15,18%"),
      ("GAS", "27,97%", "78.300", "35.700", "2.795.310.000", "27,95%"),
      ("Tổng", "100,00%", "", "", "9.995.460.000", "99,95%"),
      ("Tiền mặt còn lại", "", "", "", "4.540.000", "0,05%")],
     [2.8, 2.3, 2.3, 2.7, 3.6, 2.8], (1, 2, 3, 4, 5), "Nhóm tính toán (trang Danh mục chọn, Excel)."),
    ("p", "Quy đổi theo tháng, danh mục có E(R_{p}) ≈ 10,80%/12 = **0,90%/tháng**, tương ứng lợi nhuận kỳ vọng "
          "khoảng **90 triệu đồng** trên 10 tỷ, và σ_{p} ≈ 25,00%/√12 = 7,22%/tháng. Để kiểm soát rủi ro, nhóm "
          "giải ngân hai lần (60% đầu kỳ, 40% sau khi MBB và MWG công bố báo cáo tài chính quý III), cắt lỗ một mã "
          "nếu giảm quá 8% so với giá mua, và bán GAS nếu có quyết định hủy tư cách công ty đại chúng."),

    ("phan", "KẾT LUẬN"),
    ("p", "Bối cảnh 2026 có tăng trưởng kinh tế mạnh (GDP quý III +9,95%) nhưng lạm phát vượt mục tiêu, nên nhóm theo "
          "chiến lược cân bằng với ba cổ phiếu thuộc ba ngành: MBB (giá trị), MWG (tăng trưởng) và GAS (đa dạng "
          "hóa, cổ tức). Phân tích dữ liệu một năm cho thấy GAS gần như không tương quan với hai mã còn lại, giúp "
          "danh mục phương sai nhỏ nhất ít rủi ro hơn cả cổ phiếu ít rủi ro nhất. Dùng Solver trên mô hình "
          "Markowitz, nhóm chọn danh mục **56,84% MBB – 15,20% MWG – 27,97% GAS**, có lợi nhuận kỳ vọng 10,80%/năm "
          "với rủi ro 25,00%/năm, hiệu quả hơn tỷ trọng sơ bộ ban đầu. Hạn chế: lợi tức kỳ vọng ước lượng từ một "
          "năm dữ liệu dao động lớn, và hệ số β, phần bù rủi ro trong định giá là giả định; nhóm sẽ cập nhật khi có "
          "báo cáo tài chính quý III chính thức."),
]

TAI_LIEU = TAI_LIEU_BAI_1 + [
    "CafeF. (2026). *Lịch sử giá cổ phiếu MBB, MWG, GAS và chỉ số VN-Index, 01/10/2025 – 23/10/2026* [Dữ liệu]. "
    "https://cafef.vn/du-lieu/lich-su-giao-dich-mbb-1.chn",
    "Markowitz, H. (1952). Portfolio selection. *The Journal of Finance, 7*(1), 77–91.",
    "Sharpe, W. F. (1964). Capital asset prices: A theory of market equilibrium under conditions of risk. "
    "*The Journal of Finance, 19*(3), 425–442.",
]
