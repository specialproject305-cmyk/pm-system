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

# ═══════════════════════════════════════════════
# 🎨 KONFIGURASI HALAMAN & CSS CUSTOM
# ═══════════════════════════════════════════════
st.set_page_config(page_title="PM System", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")

# CSS untuk tombol dan dropdown di sidebar
st.markdown("""
<style>
    /* === PERBAIKAN SIDEBAR: Tombol & Dropdown === */
    
    /* Target semua tombol di sidebar */
    div[data-testid="stSidebar"] button {
        background: linear-gradient(90deg, #374151 0%, #1F2937 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #4B5563 !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
        font-weight: 500 !important;
    }
    div[data-testid="stSidebar"] button:hover {
        background: linear-gradient(90deg, #38BDF8 0%, #1F2937 100%) !important;
        border-color: #38BDF8 !important;
        color: #FFFFFF !important;
    }

    /* Target Selectbox (Dropdown) di Sidebar */
    div[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: linear-gradient(90deg, #374151 0%, #1F2937 100%) !important;
        border: 1px solid #4B5563 !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }
    
    /* Target teks di dalam Selectbox */
    div[data-testid="stSidebar"] [data-baseweb="select"] * {
        color: #FFFFFF !important;
    }
    
    /* Target label dropdown */
    div[data-testid="stSidebar"] .stSelectbox label {
        color: #CBD5E1 !important;
        font-weight: 600 !important;
    }
    
    /* Target tombol radio di sidebar */
    div[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: #374151 !important;
        color: #FFFFFF !important;
        border: 1px solid #4B5563 !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        margin: 4px 0 !important;
    }
    
    div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: #4B5563 !important;
        border-color: #38BDF8 !important;
    }
    
    div[data-testid="stSidebar"] div[role="radiogroup"] label[data-baseweb="radio"] {
        background-color: #374151 !important;
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

# ═══════════════════════════════════════════════
# 📂 SIDEBAR
# ═══════════════════════════════════════════════
with st.sidebar:
    st.title("🏗️ PMO Management System")
    st.markdown("---")

    # 🌍 Global Project Filter
    st.markdown("### 🏢 Filter Project")
    try:
        from supabase_db import read_sheet
        master_df = read_sheet("master_projects")
        if not master_df.empty:
            project_options = ["ALL"] + master_df['id'].tolist()
            selected = st.selectbox(
                "Pilih Project:",
                project_options,
                format_func=lambda x: "🌐 SEMUA PROJECT" if x == "ALL" 
                else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}",
                key="global_proj_select"
            )
            st.session_state.global_project_filter = selected
        else:
            st.info("Belum ada project")
    except Exception as e:
        st.error(f"Gagal load project: {e}")
        st.session_state.global_project_filter = "ALL"

    st.markdown("---")

    # 📂 Menu Navigasi
    menu_options = [
        "📊 Dashboard", "📁 Site Tracker", "🧱 Milestones", "📋 Kanban Board",
        "📋 Daily Tasks", "📦 Inventory", "🤖 AI Insights", "🔍 RCA Analysis",
        "💬 Chat & Notif", "📱 Field App", "📽️ Presentation", "📊 Export Report",
        "👥 User Management", "⚙️ Settings"
    ]
    menu = st.sidebar.radio("📂 Navigasi:", menu_options)

    st.markdown("---")

    # Tombol Aksi
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True, key="sidebar_refresh"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        if st.button("📽️ Presentation", use_container_width=True, key="sidebar_presentation"):
            st.session_state.presentation_mode = True
            st.rerun()

# ═══════════════════════════════════════════════
# 🚀 ROUTING
# ═══════════════════════════════════════════════
def main():
    if st.session_state.presentation_mode:
        presentation_page()
        st.stop()

    if menu == "📊 Dashboard":
        dashboard_page()
    elif menu == "📁 Site Tracker":
        project_tracker_page()
    elif menu == "🧱 Milestones":
        milestone_page()
    elif menu == "📋 Kanban Board":
        kanban_page()
    elif menu == "📦 Inventory":
        inventory_page()
    elif menu == "🤖 AI Insights":
        ai_insights_page()
    elif menu == "📊 Export Report":
        export_report_page()
    elif menu == "💬 Chat & Notif":
        chat_notif_page()
    elif menu == "📋 Daily Tasks":
        daily_task_page()
    elif menu == "🔍 RCA Analysis":
        rca_page()
    elif menu == "📽️ Presentation":
        presentation_page()
    elif menu == "📱 Field App":
        field_app_page()
    elif menu == "👥 User Management":
        user_management_page()
    elif menu == "⚙️ Settings":
        settings_page()

if __name__ == "__main__":
    main()
