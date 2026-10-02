"""Ứng dụng phân tích bán hàng và dự báo nhu cầu.

    streamlit run app/streamlit_app.py
"""

import streamlit as st

st.set_page_config(page_title="Hasu · Dự báo bán lẻ", page_icon="🛒", layout="wide")

import lib  # noqa: E402  (thêm src/ vào đường dẫn import)

pages = {
    "": [st.Page("views/overview.py", title="Tổng quan", icon=":material/dashboard:", default=True)],
    "Dữ liệu": [
        st.Page("views/upload.py", title="Nạp dữ liệu", icon=":material/upload_file:"),
        st.Page("views/quality.py", title="Chất lượng dữ liệu", icon=":material/fact_check:"),
    ],
    "Phân tích": [
        st.Page("views/analysis.py", title="Phân tích kinh doanh", icon=":material/insights:"),
    ],
    "Dự báo": [
        st.Page("views/forecast.py", title="Dự báo & đề xuất nhập", icon=":material/inventory_2:"),
        st.Page("views/explain.py", title="Giải thích dự báo", icon=":material/psychology:"),
        st.Page("views/scenario.py", title="Kịch bản mô phỏng", icon=":material/tune:"),
        st.Page("views/history.py", title="Lịch sử & đánh giá", icon=":material/history:"),
    ],
}

with st.sidebar:
    label, _ = lib.source()
    st.markdown(f"**Nguồn dữ liệu**  \n{label}")
    if st.session_state.get("db_path") and st.button("Quay lại dữ liệu mặc định"):
        st.session_state.pop("db_path")
        st.session_state["data_version"] = st.session_state.get("data_version", 0) + 1
        st.rerun()
    st.divider()
    st.caption("Dự án phân tích bán hàng & dự báo nhu cầu cho cửa hàng bán lẻ, dữ liệu KiotViet. "
               "[Mã nguồn](https://github.com/tnhvg/Hasu-Tech)")

st.navigation(pages).run()
