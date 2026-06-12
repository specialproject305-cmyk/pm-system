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
from marketing_page import marketing_page

# ═══════════════════════════════════════════════
# 🎨 KONFIGURASI HALAMAN & CSS CUSTOM
# ═══════════════════════════════════════════════
st.set_page_config(page_title="PM System", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")

# CSS untuk tombol dan dropdown di sidebar
st.markdown("""
<style>
    div[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    div[data-testid="stSidebar"] .stSelectbox > div {
        background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%) !important;
        border: 1px solid #334155;
        border-radius: 8px;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# 🧠 SESSION STATE
# ═══════════════════════════════════════════════
if 'presentation_mode' not in st.session_state:
    st.session_state.presentation_mode = False
if 'global_project_filter' not in st.session_state:
    st.session_state.global_project_filter = "ALL"
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# ═══════════════════════════════════════════════
# 🔐 LOGIN CHECK & AUTO-REDIRECT
# ═══════════════════════════════════════════════
if not st.session_state['logged_in']:
    login_page()
    st.stop()

user = st.session_state.get('user', {})
role = user.get('role', 'viewer')
app_mode = st.session_state.get('app_mode', '🏢 Full Dashboard')

# Auto-redirect PIC ke Field App
pic_roles = ['sitac', 'engineering', 'procurement', 'project', 'vendor_mgmt', 'legal']
if role in pic_roles or app_mode == '📱 Field App':
    field_app_page()
    st.stop()

# ═══════════════════════════════════════════════
# 📂 SIDEBAR (Untuk Non-PIC)
# ═══════════════════════════════════════════════
with st.sidebar:
    st.title("🏗️ PM System")
    st.markdown(f"👤 **{user.get('full_name', user.get('username', 'User'))}**")
    st.markdown("---")

    # Global Filter (hanya untuk admin/pm/pmo/planning)
    if role in ['admin', 'pm', 'pmo', 'planning']:
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
            pass
        st.markdown("---")

    # Menu Navigasi berdasarkan Role
    menu_options = []
    if role in ['admin', 'pm', 'pmo']:
        menu_options = ["📊 Dashboard", "📁 Site Tracker", "🧱 Milestones", "📋 Kanban Board", "📋 Daily Tasks", "📦 Inventory", "🤖 AI Insights", "🔍 RCA Analysis", "💬 Chat & Notif", "📱 Field App", "📽️ Presentation", "📊 Export Report", "📢 Marketing Sites"]
    elif role == 'planning':
        menu_options = ["📊 Dashboard", "📁 Site Tracker", "🧱 Milestones", "📊 Export Report"]
    elif role == 'marketing':
        menu_options = ["📊 Dashboard", "📢 Marketing Sites", "💬 Chat & Notif"]
    else: # viewer
        menu_options = ["📊 Dashboard", "🤖 AI Insights", "💬 Chat & Notif", "📽️ Presentation", "📊 Export Report"]

    if role == 'admin':
        menu_options.append("👥 User Management")
        menu_options.append("⚙️ Settings")

    menu = st.sidebar.radio("📂 Navigasi:", menu_options)
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True, key="sidebar_refresh"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        if st.button("📽️ Presentation", use_container_width=True, key="sidebar_presentation"):
            st.session_state.presentation_mode = True
            st.rerun()
    if st.button("🚪 Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state['logged_in'] = False
        st.rerun()

# ═══════════════════════════════════════════════
# 🚀 ROUTING
# ═══════════════════════════════════════════════
def main():
    if st.session_state.presentation_mode:
        presentation_page()
        st.stop()

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
    elif menu == "📢 Marketing Sites": marketing_page()

if __name__ == "__main__":
    main()
