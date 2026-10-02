import shutil
import tempfile
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

import lib
from hasu.forecasting.data import tet_offset
from hasu.forecasting.monitor import drift_status, evaluate_snapshots
from hasu.forecasting.run import run_forecasting
from hasu.ingest import COLUMN_MAP, REQUIRED_FIELDS, detect_mapping, missing_required
from hasu.pipeline import build_database

lib.header("Nạp dữ liệu")
st.markdown(
    "Tải lên file **Báo cáo bán hàng theo lợi nhuận** xuất từ KiotViet (định dạng `.xlsx`). Có thể tải nhiều "
    "file một lúc, hoặc tải file mới nối tiếp dữ liệu cũ: hệ thống tự ghép và **khử trùng lặp** theo khoá "
    "*mã hoá đơn + thời gian + mã hàng*.\n\n"
    "Dữ liệu chỉ nằm trong phiên làm việc của bạn, không được lưu lại sau khi đóng trình duyệt."
)

FIELD_LABELS = {
    "invoice_id": "Mã hoá đơn", "sold_at": "Thời gian bán", "sku": "Mã hàng", "product_name": "Tên hàng",
    "category_path": "Nhóm hàng (3 cấp, phân cách bằng >>)", "quantity": "Số lượng", "unit_price": "Giá bán / SP",
    "unit_cost": "Giá vốn / SP", "seller": "Người bán", "branch": "Chi nhánh", "note": "Ghi chú",
    "barcode": "Mã vạch", "brand": "Thương hiệu",
}
SKIP = "(bỏ qua cột này)"
OPTIONS = [SKIP, *COLUMN_MAP.values()]

files = st.file_uploader("Chọn file Excel", type=["xlsx"], accept_multiple_files=True)
if not files:
    st.info("Chưa có file nào. Trong lúc chờ, ứng dụng đang hiển thị dữ liệu demo của cửa hàng BHS Đại Phúc.")
    st.stop()

# ---- Bước 1: xác nhận ánh xạ cột ----
st.subheader("1. Xác nhận ánh xạ cột")
st.caption("Hệ thống tự nhận diện cột theo từ điển KiotViet và từ điển đồng nghĩa. Kiểm tra lại, đặc biệt các "
           "cột bắt buộc: " + ", ".join(FIELD_LABELS.get(f, f) for f in REQUIRED_FIELDS) + ".")
mappings, ok = {}, True
for f in files:
    headers = pd.read_excel(f, nrows=0).columns.tolist()
    f.seek(0)
    auto = detect_mapping(headers)
    with st.expander(f"📄 {f.name}: nhận diện được {sum(v is not None for v in auto.values())}/{len(headers)} cột",
                     expanded=bool(missing_required(auto))):
        table = pd.DataFrame({"Cột trong file": headers, "Cột chuẩn": [v or SKIP for v in auto.values()]})
        edited = st.data_editor(
            table, key=f"map_{f.name}", hide_index=True, use_container_width=True, disabled=["Cột trong file"],
            column_config={"Cột chuẩn": st.column_config.SelectboxColumn(options=OPTIONS, required=True)},
        )
        mapping = {h: (None if v == SKIP else v) for h, v in zip(edited["Cột trong file"], edited["Cột chuẩn"])}
        miss = missing_required(mapping)
        if miss:
            st.error("Thiếu cột bắt buộc: " + ", ".join(FIELD_LABELS.get(m, m) for m in miss))
            ok = False
        mappings[f.name] = mapping

if not ok:
    st.stop()

# ---- Bước 2: xử lý ----
st.subheader("2. Xử lý dữ liệu và dự báo")
_, source_db = lib.source()   # None nếu đang dùng dữ liệu demo
merge = source_db is not None
st.caption("Dữ liệu mới sẽ được **ghép vào dữ liệu hiện có**." if merge else
           "Bản triển khai công khai không chứa dữ liệu gốc, nên hệ thống xử lý riêng các file bạn tải lên.")
if not st.button("Xử lý", type="primary"):
    st.stop()

work = Path(tempfile.mkdtemp(prefix="hasu_"))
db_path = work / "hasu.duckdb"
if source_db:
    shutil.copy(source_db, db_path)

with st.status("Đang xử lý...", expanded=True) as status:
    with duckdb.connect(str(db_path)) as con:
        old_until = None
        if con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name = 'fc_run_info'").fetchone()[0]:
            old_until = pd.Timestamp(con.execute("SELECT data_until FROM fc_run_info").fetchone()[0])
        paths = []
        for f in files:
            p = work / f.name
            p.write_bytes(f.getbuffer())
            paths.append(p)
        from hasu.ingest import load_raw
        st.write("Nạp dữ liệu...")
        for p in paths:
            n = load_raw(con, p, mappings[p.name])
            st.write(f"  · {p.name}: {n:,} dòng")
        report = build_database(con, [], log=st.write)

        # Kiểm tra khoảng trống thời gian (ngoài kỳ nghỉ Tết)
        gaps = con.execute("""
            WITH c AS (SELECT date, NOT is_open AS closed,
                              row_number() OVER (ORDER BY date) - row_number() OVER (PARTITION BY NOT is_open ORDER BY date) AS grp
                       FROM dim_date)
            SELECT min(date) AS d0, max(date) AS d1, count(*) AS n FROM c WHERE closed GROUP BY grp HAVING count(*) >= 3
        """).df()
        new_until = pd.Timestamp(con.execute("SELECT max(date) FROM dim_date").fetchone()[0])

        # Vòng lặp: đối chiếu snapshot cũ với thực tế mới
        history = evaluate_snapshots(con)
        ref = con.execute("SELECT holdout_wmape FROM fc_run_info").fetchone()[0] if old_until is not None else None
        decision = drift_status(history[history["kind"] == "Dự báo thật"], ref) if ref else None
        need_retrain = (old_until is None or new_until >= old_until + pd.Timedelta(days=7)
                        or (decision or {}).get("retrain", False))
        if need_retrain:
            st.write("Huấn luyện và dự báo (khoảng 1 phút)...")
            run_forecasting(con, use_chronos=False, log=st.write)
    status.update(label="Xong", state="complete")

st.session_state["db_path"] = str(db_path)
st.session_state["data_version"] = st.session_state.get("data_version", 0) + 1
st.session_state["quality_report"] = report

st.success(f"Đã xử lý dữ liệu tới **{new_until:%d/%m/%Y}**. Mọi màn hình giờ dùng dữ liệu bạn vừa nạp.")
if len(gaps):
    near_tet = tet_offset(pd.to_datetime(gaps["d0"])).abs() <= 14
    if near_tet.any():
        st.caption("Khoảng nghỉ trùng dịp Tết (bình thường): "
                   + "; ".join(f"{r.d0:%d/%m} – {r.d1:%d/%m/%Y}" for r in gaps[near_tet].itertuples()))
    other = gaps[~near_tet]
    if len(other):
        st.warning("Phát hiện các giai đoạn ≥ 3 ngày liên tiếp không có giao dịch: "
                   + "; ".join(f"{r.d0:%d/%m} – {r.d1:%d/%m/%Y} ({r.n} ngày)" for r in other.itertuples())
                   + ". Nếu không phải ngày nghỉ, có thể file bị thiếu dữ liệu giai đoạn này.")
if decision:
    st.info(f"**Đối chiếu dự báo cũ với thực tế mới:** {decision['status']}")
elif old_until is not None:
    st.info("Chưa có tuần dự báo thật nào đủ 7 ngày thực tế để đối chiếu.")
st.page_link("views/quality.py", label="Xem báo cáo chất lượng dữ liệu", icon=":material/fact_check:")
