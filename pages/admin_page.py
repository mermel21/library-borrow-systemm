import streamlit as st
import model
import controller


def render_admin():
    st.subheader("🛠️ จัดการผู้ใช้ระบบ")

    # ---------- เพิ่มผู้ใช้ ----------
    with st.form("add_user"):
        username = st.text_input("ชื่อผู้ใช้")
        password = st.text_input("รหัสผ่าน", type="password")
        role = st.selectbox("หน้าที่", ["staff", "admin"])
        is_active = st.checkbox("เปิดใช้งาน", value=True)
        submit = st.form_submit_button("[บันทึกผู้ใช้งานใหม่]")

    if submit:
        ok, msgs = controller.create_user(username, password, role, is_active)
        for m in msgs:
            st.success(m) if ok else st.error(m)
        if ok:
            st.rerun()

    st.divider()

    # ---------- รายชื่อผู้ใช้ ----------
    users_df = model.get_all_users()
    st.dataframe(users_df, use_container_width=True)

    st.divider()

    # ---------- แก้ไข ----------
    options = [
        f"{r['id']} - {r['username']} ({r['role']}) [{r['status']}]"
        for _, r in users_df.iterrows()
    ]

    selected = st.selectbox("เลือกผู้ใช้", options)
    user_id = int(selected.split(" - ")[0])
    current_username = st.session_state["user"]["username"]

    col1, col2 = st.columns(2)

    with col1:
        new_role = st.selectbox("หน้าที่", ["staff", "admin"])
        if st.button("บันทึกหน้าที่"):
            ok, msgs = controller.set_user_role(
                user_id, new_role, current_username
            )
            for m in msgs:
                st.success(m) if ok else st.error(m)
            if ok:
                st.rerun()

    with col2:
        new_status = st.selectbox("สถานะใหม่", ["ใช้งาน", "ปิดใช้งาน"])
        is_active = 1 if new_status == "ใช้งาน" else 0

        if st.button("บันทึกสถานะ"):
            ok, msgs = controller.set_user_active(
                user_id, is_active, current_username
            )
            for m in msgs:
                st.success(m) if ok else st.error(m)
            if ok:
                st.rerun()
