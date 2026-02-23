import streamlit as st
import model
import controller


def render_book():
    st.subheader("🗃 หนังสือ")

    st.text_input("ชื่อหนังสือ", key="bt")
    st.text_input("ผู้แต่ง", key="ba")

    if st.button("เพิ่มหนังสือ"):
        controller.create_book(st.session_state.bt, st.session_state.ba)
        st.rerun()

    df = model.get_all_books()
    st.dataframe(df, use_container_width=True)
