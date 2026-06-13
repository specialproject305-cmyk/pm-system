import streamlit as st
from auth import login_page, check_permission, show_permission_denied

# ═══════════════════════════════════════════════
# 🎨 KONFIGURASI HALAMAN & CSS CUSTOM
# ═══════════════════════════════════════════════
st.set_page_config(page_title="PM System", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")

# Inject CSS sekaligus untuk efisiensi render
st.markdown("""
<style>
    div[data-testid="stSidebar"] .stButton > button,
    div[data-testid="stSidebar"] .stSelectbox > div {
        background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #334155;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# 🧠 SESSION STATE INITIALIZATION
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
pic_roles = {'sitac', 'engineering', 'procurement', 'project', 'vendor_mgmt', 'legal'}
if role in pic_roles or app_mode == '📱 Field App':
    from field_app import field_app_page
    field_app_page()
    st.stop()

# ═══════════════════════════════════════════════
# 📂 SIDEBAR (Untuk Non-PIC)
# ═══════════════════════════════════════════════
with st.sidebar:
    st.title("🏗️ PM System")
    st.markdown(f"👤 **{user.get('full_name', user.get('username', 'User'))}**")
    st.markdown("---")

    # Global Filter dengan optimasi O(1) mapping lookup
    if role in ['admin', 'pm', 'pmo', 'planning']:
        st.markdown("### 🏢 Filter Project")
        try:
            from supabase_db import read_sheet
            master_df = read_sheet("master_projects")
            if not master_df.empty:
                # Membaca & memetakan id ke string format (mencegah query berulang di lambda)
                project_map = {
                    row['id']: f"{row['project_code']} - {row['project_name']}" 
                    for _, row in master_df.iterrows()
                }
                project_options = ["ALL"] + list(project_map.keys())
                
                selected = st.selectbox(
                    "Pilih Project:", 
                    project_options,
                    format_func=lambda x: "🌐 SEMUA PROJECT" if x == "ALL" else project_map.get(x, str(x)),
                    key="global_proj_select"
                )
                st.session_state.global_project_filter = selected
        except Exception:
            pass
        st.markdown("---")

    # Penentuan Menu Navigasi (Clean & No Duplicate)
    if role in ['admin', 'pm', 'pmo']:
        menu_options = ["📊 Dashboard", "📁 Site Tracker", "🧱 Milestones", "📋 Kanban Board", "📋 Daily Tasks", "📦 Inventory", "🤖 AI Insights", "🔍 RCA Analysis", "💬 Chat & Notif", "📱 Field App", "📽️ Presentation", "📊 Export Report", "📢 Marketing Sites", "📢 Marketing Dashboard", "🔔 Notifications"]
    elif role == 'planning':
        menu_options = ["📊 Dashboard", "📁 Site Tracker", "🧱 Milestones", "📊 Export Report", "🔔 Notifications"]
    elif role == 'marketing':
        menu_options = ["📊 Dashboard", "📢 Marketing Dashboard", "📢 Marketing Sites", "💬 Chat & Notif", "🔔 Notifications"]
    else: # viewer
        menu_options = ["📊 Dashboard", "🤖 AI Insights", "💬 Chat & Notif", "📽️ Presentation", "📊 Export Report"]

    if role == 'admin':
        # Menjaga urutan tetap unik tanpa fungsi append berulang
        menu_options.extend(["👥 User Management", "⚙️ Settings"])
        menu_options = list(dict.fromkeys(menu_options))

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
        st.session_state.clear()  # Lebih bersih dan cepat menghapus seluruh keys
        st.session_state['logged_in'] = False
        st.rerun()

# ═══════════════════════════════════════════════
# 🚀 ROUTING (Lazy Loading Enabled)
# ═══════════════════════════════════════════════
def main():
    if st.session_state.presentation_mode:
        from presentation import presentation_page
        presentation_page()
        st.stop()

    # Module di-import hanya jika menu tersebut dipilih secara aktif
    if menu == "📊 Dashboard":
        from dashboard import dashboard_page
        dashboard_page()
    elif menu == "📁 Site Tracker":
        from project_tracker import project_tracker_page
        project_tracker_page()
    elif menu == "🧱 Milestones":
        from milestone_module import milestone_page
        milestone_page()
    elif menu == "📋 Kanban Board":
        from kanban_board import kanban_page
        kanban_page()
    elif menu == "📦 Inventory":
        from inventory_module import inventory_page
        inventory_page()
    elif menu == "🤖 AI Insights":
        from ai_insights import ai_insights_page
        ai_insights_page()
    elif menu == "📊 Export Report":
        from export_report import export_report_page
        export_report_page()
    elif menu == "💬 Chat & Notif":
        from chat_module import chat_notif_page
        chat_notif_page()
    elif menu == "📋 Daily Tasks":
        from daily_task import daily_task_page
        daily_task_page()
    elif menu == "🔍 RCA Analysis":
        from rca_page import rca_page
        rca_page()
    elif menu == "📽️ Presentation":
        from presentation import presentation_page
        presentation_page()
    elif menu == "📱 Field App":
        from field_app import field_app_page
        field_app_page()
    elif menu == "👥 User Management":
        from user_management import user_management_page
        user_management_page()
    elif menu == "⚙️ Settings":
        from settings_page import settings_page
        settings_page()
    elif menu == "📢 Marketing Sites":
        from marketing_page import marketing_page
        marketing_page()
    elif menu == "📢 Marketing Dashboard":
        from marketing_dashboard import marketing_dashboard_page
        marketing_dashboard_page()
    elif menu == "🔔 Notifications":
        from notification_page import notification_page
        notification_page()

if __name__ == "__main__":
    main()
