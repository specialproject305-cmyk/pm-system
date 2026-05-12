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
from kanban_board import kanban_page
from export_report import export_report_page

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
        "📊 Dashboard", "📁 Site Tracker", "🧱 Milestones","📋 Kanban Board",
        "📦 Inventory", "🤖 AI Insights", "💬 Chat & Notif", "📊 Export Report"
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
    # Pastikan variabel 'menu' sudah didefinisikan sebelumnya (biasanya dari st.sidebar.radio)
    # Jika belum ada, tambahkan ini di atas fungsi main atau di dalam main sebelum if-else:
    # menu = st.sidebar.radio("Navigasi", [...])

    if menu == "📊 Dashboard": 
        dashboard_page()
        
    elif menu == "📁 Site Tracker":
        # Asumsi fungsi check_permission dan show_permission_denied sudah ada di auth.py atau sejenisnya
        if 'check_permission' in globals() and check_permission('editor'): 
            project_tracker_page()
        else: 
            # Fallback jika fungsi permission belum diimplementasikan penuh, langsung tampilkan halaman
            try:
                project_tracker_page()
            except NameError:
                st.warning("Fitur permission belum aktif. Menampilkan halaman Project Tracker.")
                project_tracker_page()

    elif menu == "🧱 Milestones":
        if 'check_permission' in globals() and check_permission('editor'): 
            milestone_page()
        else: 
            try:
                milestone_page()
            except NameError:
                st.warning("Fitur permission belum aktif. Menampilkan halaman Milestone.")
                milestone_page()

    elif menu == "📋 Kanban Board":
        # ✅ FIX: Isi blok kode untuk Kanban Board
        kanban_page() 

    elif menu == "📦 Inventory":
        # Asumsi inventory_page() sudah ada di inventory_module.py
        if 'check_permission' in globals() and check_permission('editor'): 
            try:
                from inventory_module import inventory_page
                inventory_page()
            except ImportError:
                st.info("Modul Inventory belum dibuat. Fitur ini akan segera hadir.")
        else: 
            st.info("Modul Inventory belum dibuat. Fitur ini akan segera hadir.")

    elif menu == "🤖 AI Insights": 
        ai_insights_page()
        
    elif menu == "💬 Chat & Notif": 
        chat_notif_page()
        
    elif menu == "📄 Export Report": 
        # Asumsi export_page() ada di dashboard.py atau module terpisah
        try:
            from dashboard import export_page # Atau sesuaikan importnya
            export_page()
        except ImportError:
            st.info("Halaman Export Report sedang dikembangkan.")

    elif menu == "⚙️ Settings":
        if 'check_permission' in globals() and check_permission('admin'): 
            try:
                from settings_page import settings_page
                settings_page()
            except ImportError:
                st.info("Halaman Settings sedang dikembangkan.")
        else: 
            st.info("Halaman Settings sedang dikembangkan.")

    else:
        st.error("Menu tidak dikenali.")

    elif menu == "📊 Export Report":
        export_report_page()
    
if __name__ == "__main__":
    main()
