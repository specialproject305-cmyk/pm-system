import streamlit as st
from auth import login_page, check_permission, show_permission_denied
from dashboard import dashboard_page
from project_tracker import project_tracker_page
from milestone_module import milestone_page
from inventory_module import inventory_page
from ai_insights import ai_insights_page
from chat_module import chat_notif_page
from settings_page import settings_page
from kanban_board import kanban_page
from export_report import export_report_page
from daily_task import daily_task_page
from rca_page import rca_page
from presentation import presentation_page
from field_app import field_app_page
from user_management import user_management_page

st.set_page_config(page_title="PM System", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")

if 'presentation_mode' not in st.session_state:
    st.session_state.presentation_mode = False
if 'global_project_filter' not in st.session_state:
    st.session_state.global_project_filter = "ALL"
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login_page()
    st.stop()

user = st.session_state.get('user', {})
role = user.get('role', 'viewer')

# Engineer / Field App mode
if role == 'engineer' or st.session_state.get('app_mode') == '📱 Field App':
    field_app_page()
    st.stop()

with st.sidebar:
    st.title("🏗️ PM System")
    st.markdown(f"👤 **{user.get('full_name', user.get('username', 'User'))}**")
    st.caption(f"🔹 Role: {role.upper()}")
    st.markdown("---")
    
    # Global Project Filter
    st.markdown("### 🏢 Filter Project")
    try:
        from supabase_db import read_sheet
        master_df = read_sheet("master_projects")
        if not master_df.empty:
            project_options = ["ALL"] + master_df['id'].tolist()
            selected = st.selectbox("Pilih Project:", project_options,
                format_func=lambda x: "🌐 SEMUA PROJECT" if x == "ALL" 
                else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}",
                key="global_proj_select")
            st.session_state.global_project_filter = selected
    except:
        st.session_state.global_project_filter = "ALL"
    st.markdown("---")
    
    # Menu
    menu_options = [
        "📊 Dashboard", "📁 Site Tracker", "🧱 Milestones", "📋 Kanban Board",
        "📋 Daily Tasks", "📦 Inventory", "🤖 AI Insights", "🔍 RCA Analysis",
        "💬 Chat & Notif", "📽️ Presentation", "📊 Export Report"
    ]
    if role in ['admin', 'editor']:
        menu_options.append("📱 Field App")
    if role == 'admin':
        menu_options.append("👥 User Management")
        menu_options.append("⚙️ Settings")
    
    menu = st.sidebar.radio("📂 Navigasi:", menu_options)
    st.markdown("---")
    
    if st.button("📽️ Presentation Mode", use_container_width=True):
        st.session_state.presentation_mode = True
        st.rerun()
    
    if st.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state['logged_in'] = False
        st.rerun()

def main():
    if st.session_state.presentation_mode:
        presentation_page()
    else:
        if menu == "📊 Dashboard": dashboard_page()
        elif menu == "📁 Site Tracker":
            if check_permission('editor'): project_tracker_page()
            else: show_permission_denied()
        elif menu == "🧱 Milestones":
            if check_permission('editor'): milestone_page()
            else: show_permission_denied()
        elif menu == "📋 Kanban Board": kanban_page()
        elif menu == "📦 Inventory":
            if check_permission('editor'): inventory_page()
            else: show_permission_denied()
        elif menu == "🤖 AI Insights": ai_insights_page()
        elif menu == "📊 Export Report": export_report_page()
        elif menu == "💬 Chat & Notif": chat_notif_page()
        elif menu == "📋 Daily Tasks": daily_task_page()
        elif menu == "🔍 RCA Analysis": rca_page()
        elif menu == "📽️ Presentation": presentation_page()
        elif menu == "📱 Field App": field_app_page()
        elif menu == "👥 User Management":
            if check_permission('admin'): user_management_page()
            else: show_permission_denied()
        elif menu == "⚙️ Settings":
            if check_permission('admin'): settings_page()
            else: show_permission_denied()

if __name__ == "__main__":
    main()
