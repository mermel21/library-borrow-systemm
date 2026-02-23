import streamlit as st
import model
import controller


def render_member():
    st.subheader("🧑🏼‍🦰 สมาชิก")

    st.text_input("ชื่อ", key="mn")
    st.text_input("อีเมล", key="me")
    st.text_input("โทรศัพท์", key="mp")

    if st.button("เพิ่มสมาชิก"):
        controller.create_member(
            st.session_state.mn,
            st.session_state.me,
            st.session_state.mp
        )
        st.rerun()

    df = model.get_all_members()
    st.dataframe(df, use_container_width=True)
