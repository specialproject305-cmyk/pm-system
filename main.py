import streamlit as st
from auth import login_page, check_permission, show_permission_denied
from bulk_import import bulk_import_page
from workforce_page import workforce_page


# ═══════════════════════════════════════════════
# 🎨 KONFIGURASI HALAMAN & CSS CUSTOM
# ═══════════════════════════════════════════════
st.set_page_config(page_title="PM System", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")

# Inject CSS sekaligus untuk efisiensi render
st.markdown("""
<style>
    /* ===== GLOBAL PREMIUM STYLING ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%);
        color: #1E293B;
        font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
        letter-spacing: -0.2px;
    }
    
    /* ===== GLASSMORPHISM SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255,255,255,0.08) !important;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.08) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        color: #E2E8F0 !important;
        font-weight: 500 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(99, 102, 241, 0.2) !important;
        border-color: #6366F1 !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stSidebar"] .stSelectbox > div {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
    }
    
    /* ===== GLOBAL BUTTON ===== */
    .stButton > button {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 8px 18px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.25) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.35) !important;
    }
    
    /* ===== GLOBAL INPUT ===== */
    .stTextInput > div > div, .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 1px solid #E2E8F0 !important;
        transition: all 0.3s ease !important;
    }
    .stTextInput > div > div:focus-within, .stSelectbox > div > div:focus-within {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }
    
    /* ===== GLOBAL TABLE ===== */
    [data-testid="stDataFrame"] {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06) !important;
    }
    thead th {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        padding: 10px 12px !important;
    }
    tbody tr {
        transition: background 0.2s ease !important;
    }
    tbody tr:hover {
        background: rgba(99, 102, 241, 0.04) !important;
    }
    tbody td {
        font-size: 0.85rem !important;
        padding: 8px 12px !important;
    }
    
    /* ===== SCROLLBAR PREMIUM ===== */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #94A3B8; }
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
        menu_options = ["📊 Dashboard", "📁 Site Tracker", "🧱 Milestones", "👷 Workforce", "📋 Kanban Board", "📋 Daily Tasks", "📦 Inventory", "🤖 AI Insights", "🔍 RCA Analysis", "💬 Chat & Notif", "📱 Field App", "📽️ Presentation", "📊 Export Report", "📢 Marketing Sites", "📢 Marketing Dashboard", "🔔 Notifications"]
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
        menu_options.append("📥 Bulk Import")

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
    elif menu == "📥 Bulk Import": bulk_import_page()
    elif menu == "👷 Workforce": workforce_page()

if __name__ == "__main__":
    main()
