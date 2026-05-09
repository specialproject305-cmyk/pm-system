import streamlit as st
from auth import login_page, check_permission, show_permission_denied
from dashboard import dashboard_page
from project_tracker import project_tracker_page
from milestone_module import milestone_page
from inventory_module import inventory_page
from ai_insights import ai_insights_page
from chat_module import chat_notif_page
from export_module import export_page
from settings_page import settings_page

st.set_page_config(page_title="PM System", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
    st.stop()

user = st.session_state.get('user', {})
role = user.get('role', 'viewer')

with st.sidebar:
    st.title("🏗️ PM System")
    st.markdown(f"👤 **{user.get('full_name', user.get('username', 'User'))}**")
    st.caption(f"🔹 Role: {role.upper()}")
    st.markdown("---")
    
    menu_options = [
        "📊 Dashboard", "📁 Site Tracker", "🧱 Milestones",
        "📦 Inventory", "🤖 AI Insights", "💬 Chat & Notif", "📄 Export Report"
    ]
    if role == 'admin':
        menu_options.append("⚙️ Settings")
    
    menu = st.sidebar.radio("📂 Navigasi:", menu_options)
    st.markdown("---")
    
    if st.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state['logged_in'] = False
        st.rerun()

def main():
    if menu == "📊 Dashboard": dashboard_page()
    elif menu == "📁 Site Tracker":
        if check_permission('editor'): project_tracker_page()
        else: show_permission_denied()
    elif menu == "🧱 Milestones":
        if check_permission('editor'): milestone_page()
        else: show_permission_denied()
    elif menu == "📦 Inventory":
        if check_permission('editor'): inventory_page()
        else: show_permission_denied()
    elif menu == "🤖 AI Insights": ai_insights_page()
    elif menu == "💬 Chat & Notif": chat_notif_page()
    elif menu == "📄 Export Report": export_page()
    elif menu == "⚙️ Settings":
        if check_permission('admin'): settings_page()
        else: show_permission_denied()

if __name__ == "__main__":
    main()
