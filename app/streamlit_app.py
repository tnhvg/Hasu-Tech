"""Ứng dụng phân tích bán hàng và dự báo nhu cầu.

    streamlit run app/streamlit_app.py
"""

from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).parent / "assets"

st.set_page_config(page_title="Hasu · Dự báo bán lẻ", page_icon=str(ASSETS / "icon.svg"), layout="wide")

import lib  # noqa: E402  (thêm src/ vào đường dẫn import)

lib.inject_css()
st.logo(str(ASSETS / "logo.svg"), size="large", icon_image=str(ASSETS / "icon.svg"))

pages = {
    "": [st.Page("views/overview.py", title="Tổng quan", icon=":material/space_dashboard:", default=True)],
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
    label, path = lib.source()
    st.caption("NGUỒN DỮ LIỆU")
    st.markdown(f":material/database: **{label}**")
    if st.session_state.get("db_path") and st.button("Quay lại dữ liệu mặc định", icon=":material/undo:"):
        st.session_state.pop("db_path")
        st.session_state["data_version"] = st.session_state.get("data_version", 0) + 1
        st.rerun()
    st.divider()
    st.caption("Phân tích bán hàng & dự báo nhu cầu cho cửa hàng bán lẻ, dữ liệu KiotViet.")
    st.markdown(":material/code: [Mã nguồn trên GitHub](https://github.com/tnhvg/Hasu-Tech)")

st.navigation(pages).run()
lib.footer()
