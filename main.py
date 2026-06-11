import streamlit as st
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

with st.sidebar:
    st.title("🏗️ PM System")
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
    
    menu = st.sidebar.radio("📂 Navigasi:", [
        "📊 Dashboard", "📁 Site Tracker", "🧱 Milestones", "📋 Kanban Board",
        "📋 Daily Tasks", "📦 Inventory", "🤖 AI Insights", "🔍 RCA Analysis",
        "💬 Chat & Notif", "📱 Field App", "📽️ Presentation", "📊 Export Report",
        "👥 User Management", "⚙️ Settings"
    ])
    
    if st.button("📽️ Presentation Mode", use_container_width=True):
        st.session_state.presentation_mode = True
        st.rerun()

def main():
    if st.session_state.presentation_mode:
        presentation_page()
    else:
        if menu == "📊 Dashboard": dashboard_page()
        elif menu == "📁 Site Tracker": project_tracker_page()
        elif menu == "🧱 Milestones": milestone_page()
        elif menu == "📋 Kanban Board": kanban_page()
        elif menu == "📦 Inventory": inventory_page()
        elif menu == "🤖 AI Insights": ai_insights_page()
        elif menu == "📊 Export Report": export_report_page()
        elif menu == "💬 Chat & Notif": chat_notif_page()
        elif menu == "📋 Daily Tasks": daily_task_page()
        elif menu == "🔍 RCA Analysis": rca_page()
        elif menu == "📽️ Presentation": presentation_page()
        elif menu == "📱 Field App": field_app_page()
        elif menu == "👥 User Management": user_management_page()
        elif menu == "⚙️ Settings": settings_page()

if __name__ == "__main__":
    main()
