# app.py
import streamlit as st
from pages import book_page, member_page, borrow_page
from pages import login_page
from pages import admin_page
from pages import report_page

st.set_page_config(
    page_title="ระบบยืม-คืนหนังสือ",
    page_icon="📒"
)

# =========================
# Session State
# =========================
if "is_logged_in" not in st.session_state:
    st.session_state["is_logged_in"] = False

if "user" not in st.session_state:
    st.session_state["user"] = None

if "page" not in st.session_state:
    st.session_state["page"] = "books"

# =========================
# Hide Streamlit multipage menu
# =========================
st.markdown(
    """
    <style>
    section[data-testid="stSidebarNav"] { display: none !important; }
    div[data-testid="stSidebarNav"] { display: none !important; }
    nav[data-testid="stSidebarNav"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# Login Gate
# =========================
if not st.session_state["is_logged_in"]:
    login_page.render_login()
    st.stop()

# =========================
# Header
# =========================
st.title("📒 ระบบยืม-คืนหนังสือ (Streamlit + SQLite)📖")
st.write("ตัวอย่าง Web App เชื่อมฐานข้อมูล (แนวคิด MVC)")

# =========================
# Sidebar: User info + Logout
# =========================
user = st.session_state.get("user") or {}
role = user.get("role", "")

st.sidebar.markdown(f"👱🏼‍♀️ ผู้ใช้: **{user.get('username', '-')}**")


if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state["is_logged_in"] = False
    st.session_state["user"] = None
    st.session_state["page"] = "books"
    st.rerun()

# =========================
# Sidebar Menu
# =========================
st.sidebar.markdown("## 📇 เมนู")

def nav_button(label, key, icon=""):
    if st.sidebar.button(f"{icon} {label}", use_container_width=True):
        st.session_state["page"] = key
        st.rerun()

role= user.get("role")

nav_button("หนังสือ", "books", "📒")
nav_button("สมาชิก", "members", "🪪")
nav_button("ยืม-คืน", "borrows", "🔁")
nav_button("รายงาน", "reports", "📊")

if role == "admin":
    nav_button("จัดการผู้ใช้", "admin", "🛠️")

# ---------- Routing ----------
# ป้องกัน staff เข้าหน้า admin ด้วยการบังคับ routing
# เอาการบังคับ staff ไปหน้า borrows ออก (staff ทำได้ทุกอย่างแล้ว)

if st.session_state.page == "books":
    book_page.render_book()

elif st.session_state.page == "members":
    member_page.render_member()

elif st.session_state.page == "borrows":
    borrow_page.render_borrow()

elif st.session_state.page == "reports":
    report_page.render_report()

elif st.session_state.page == "admin":
    # guard กัน staff เข้าหน้า admin แม้พยายามเปลี่ยน state เอง
    if role != "admin":
        st.warning("⚠ หน้านี้อนุญาตเฉพาะผู้ดูแลระบบ (admin) เท่านั้น")
    else:
        admin_page.render_admin()

else:
    # fallback
    book_page.render_book()

   
