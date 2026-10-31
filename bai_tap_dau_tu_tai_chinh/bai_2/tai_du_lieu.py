"""Bước 1 – Tải giá đóng cửa hằng ngày từ CafeF (01/10/2025 – 30/09/2026).

Chạy: python bai_tap_dau_tu_tai_chinh/bai_2/tai_du_lieu.py
Kết quả: du_lieu/gia_<MÃ>.csv (dữ liệu gốc từng mã) và du_lieu/gia_dong_cua.csv (bảng gộp,
mỗi cột là giá ĐIỀU CHỈNH của một mã, đơn vị nghìn đồng; VNINDEX đơn vị điểm).

Vì sao dùng giá điều chỉnh: khi chia cổ tức bằng cổ phiếu (MBB chia 15% tháng 8/2026), giá thô
tự giảm vào ngày giao dịch không hưởng quyền dù nhà đầu tư không mất tiền. Giá điều chỉnh đã
loại bỏ bước nhảy này, nên lợi tức tính ra mới phản ánh đúng lãi/lỗ thật.
"""

import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

MA_CO_PHIEU = ["MBB", "MWG", "GAS", "VNINDEX"]
TU_NGAY, DEN_NGAY = "10/01/2025", "09/30/2026"  # CafeF nhận định dạng tháng/ngày/năm
THU_MUC = Path(__file__).parent / "du_lieu"
API = "https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/PriceHistory.ashx"


def tai_mot_ma(ma: str) -> list[dict]:
    """Tải toàn bộ các phiên của một mã (CafeF trả theo trang, mỗi trang tối đa 100 dòng)."""
    cac_dong, trang = [], 1
    while True:
        tham_so = urllib.parse.urlencode({
            "Symbol": ma, "StartDate": TU_NGAY, "EndDate": DEN_NGAY,
            "PageIndex": trang, "PageSize": 100,
        })
        yeu_cau = urllib.request.Request(f"{API}?{tham_so}", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(yeu_cau, timeout=30) as phan_hoi:
            du_lieu = json.load(phan_hoi)["Data"]
        cac_dong += du_lieu["Data"]
        if len(cac_dong) >= du_lieu["TotalCount"] or not du_lieu["Data"]:
            return cac_dong
        trang += 1
        time.sleep(0.5)  # nghỉ giữa các lần gọi để không làm phiền máy chủ


def main() -> None:
    THU_MUC.mkdir(exist_ok=True)
    bang_gop: dict[str, dict[str, float]] = {}
    for ma in MA_CO_PHIEU:
        cac_dong = tai_mot_ma(ma)
        with open(THU_MUC / f"gia_{ma}.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["Ngay", "GiaDieuChinh", "GiaDongCua", "KhoiLuongKhopLenh"])
            for d in cac_dong:
                w.writerow([d["Ngay"], d["GiaDieuChinh"], d["GiaDongCua"], d["KhoiLuongKhopLenh"]])
        for d in cac_dong:
            ngay = datetime.strptime(d["Ngay"], "%d/%m/%Y").date().isoformat()
            bang_gop.setdefault(ngay, {})[ma] = d["GiaDieuChinh"]
        print(f"{ma}: {len(cac_dong)} phiên, từ {cac_dong[-1]['Ngay']} đến {cac_dong[0]['Ngay']}")

    with open(THU_MUC / "gia_dong_cua.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Ngay"] + MA_CO_PHIEU)
        for ngay in sorted(bang_gop):  # sắp xếp từ cũ đến mới
            w.writerow([ngay] + [bang_gop[ngay].get(ma, "") for ma in MA_CO_PHIEU])
    print("Đã lưu", THU_MUC / "gia_dong_cua.csv")


if __name__ == "__main__":
    main()
