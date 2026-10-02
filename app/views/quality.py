import streamlit as st

import lib

lib.header("Báo cáo chất lượng dữ liệu", section="Dữ liệu", caption=
           "Liệt kê các vấn đề phát hiện và cách xử lý, trước khi dữ liệu được dùng để phân tích.")

report = st.session_state.get("quality_report")
if report is None:
    report = (lib.ROOT / "docs" / "data_quality_report.md").read_text(encoding="utf-8")
# Bỏ dòng tiêu đề và dòng thời gian sinh báo cáo (đã có tiêu đề trang)
lines = [ln for ln in report.splitlines() if not ln.startswith("# ") and not ln.startswith("_Sinh tự động")]
with lib.card():
    st.markdown("\n".join(lines))
