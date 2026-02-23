# page/login_page.py
import streamlit as st
import controller


def render_login():
    st.title("🔐 เข้าสู่ระบบ")
    # 👇 เพิ่มตรงนี้
    st.markdown("**รหัสนักศึกษา:** 6762509109")
    st.markdown("**ชื่อ:** จิตราภรณ์ ชินภักดี")
    st.markdown("**หมู่เรียน:*ว.6707T* ")
    with st.form("login_form"):
        username = st.text_input(
            "ชื่อผู้ใช้",
            placeholder=""
        )
        password = st.text_input(
            "รหัสผ่าน",
            type="password",
            placeholder=""
        )
        submitted = st.form_submit_button("Login")

    if submitted:
        ok, msgs, user_info = controller.login(username, password)

        if not ok:
            for m in msgs:
                st.error(m)
        else:
            for m in msgs:
                st.success(m)

            st.session_state["is_logged_in"] = True
            st.session_state["user"] = user_info
            st.session_state["page"] = "books"  # หรือ "borrows"

            st.rerun()
