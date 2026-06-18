import streamlit as st

# ==========================================================
# CORE MODULES
# ==========================================================
from auth import login_page
from bulk_import import bulk_import_page
from workforce_page import workforce_page
from user_manual import user_manual_page
from inventory_dashboard import inventory_dashboard_page
from photo_module import photo_page


# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="PM System",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# CSS LOAD
# ==========================================================
st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg,#F8FAFC 0%,#E2E8F0 100%);
    color:#1E293B;
}

[data-testid="stSidebar"]{
    background: linear-gradient(
        180deg,
        #1E3A5F 0%,
        #2563EB 40%,
        #F59E0B 100%
    ) !important;
}

[data-testid="stSidebar"] *{
    color:#E2E8F0 !important;
}

</style>
""", unsafe_allow_html=True)


# ==========================================================
# CACHE FUNCTIONS
# ==========================================================
@st.cache_data(ttl=300, show_spinner=False)
def get_master_projects():
    from supabase_db import read_sheet
    return read_sheet("master_projects")


# ==========================================================
# SESSION INIT
# ==========================================================
DEFAULT_STATES = {
    "presentation_mode": False,
    "global_project_filter": "ALL",
    "logged_in": False,
}

for key, value in DEFAULT_STATES.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==========================================================
# LOGIN CHECK
# ==========================================================
if not st.session_state.logged_in:
    login_page()
    st.stop()


# ==========================================================
# USER INFO
# ==========================================================
user = st.session_state.get("user", {})
role = user.get("role", "viewer")
app_mode = st.session_state.get(
    "app_mode",
    "🏢 Full Dashboard"
)

# ==========================================================
# AUTO FIELD APP
# ==========================================================
PIC_ROLES = {
    "sitac",
    "engineering",
    "procurement",
    "project",
    "vendor_mgmt",
    "legal"
}

if role in PIC_ROLES or app_mode == "📱 Field App":
    from field_app import field_app_page

    field_app_page()
    st.stop()


# ==========================================================
# SIDEBAR
# ==========================================================
with st.sidebar:

    st.title("🏗️ PM System")

    st.markdown(
        f"👤 **{user.get('full_name', user.get('username', 'User'))}**"
    )

    st.markdown("---")

    # ======================================================
    # PROJECT FILTER
    # ======================================================
    if role in ["admin", "pm", "pmo", "planning"]:

        st.markdown("### 🏢 Filter Project")

        try:

            master_df = get_master_projects()

            if not master_df.empty:

                project_map = {
                    row.id:
                    f"{row.project_code} - {row.project_name}"
                    for row in master_df.itertuples(index=False)
                }

                project_options = [
                    "ALL",
                    *project_map.keys()
                ]

                selected = st.selectbox(
                    "Pilih Project",
                    project_options,
                    format_func=lambda x:
                    "🌐 SEMUA PROJECT"
                    if x == "ALL"
                    else project_map.get(x, str(x)),
                    key="global_proj_select"
                )

                st.session_state.global_project_filter = selected

        except Exception as e:
            st.error("Gagal memuat master project")
            st.exception(e)

        st.markdown("---")

    # ======================================================
    # MENU BY ROLE
    # ======================================================
    ROLE_MENU = {

        "admin": [
            "📊 Dashboard",
            "📦 Inventory Dashboard",
            "📁 Site Tracker",
            "🧱 Milestones",
            "👷 Workforce",
            "📋 Kanban Board",
            "📋 Daily Tasks",
            "📦 Inventory",
            "🤖 AI Insights",
            "🔍 RCA Analysis",
            "💬 Chat & Notif",
            "📱 Field App",
            "📸 Photo Evidence",
            "📽️ Presentation",
            "📊 Export Report",
            "📢 Marketing Sites",
            "📢 Marketing Dashboard",
            "🔔 Notifications",
            "📖 User Manual",
            "👥 User Management",
            "⚙️ Settings",
            "📥 Bulk Import"
        ],

        "pm": [
            "📊 Dashboard",
            "📦 Inventory Dashboard",
            "📁 Site Tracker",
            "🧱 Milestones",
            "👷 Workforce",
            "📋 Kanban Board",
            "📋 Daily Tasks",
            "📦 Inventory",
            "🤖 AI Insights",
            "🔍 RCA Analysis",
            "💬 Chat & Notif",
            "📱 Field App",
            "📸 Photo Evidence",
            "📽️ Presentation",
            "📊 Export Report",
            "📢 Marketing Sites",
            "📢 Marketing Dashboard",
            "🔔 Notifications",
            "📖 User Manual"
        ],

        "pmo": [
            "📊 Dashboard",
            "📦 Inventory Dashboard",
            "📁 Site Tracker",
            "🧱 Milestones",
            "👷 Workforce",
            "📋 Kanban Board",
            "📋 Daily Tasks",
            "📦 Inventory",
            "🤖 AI Insights",
            "🔍 RCA Analysis",
            "💬 Chat & Notif",
            "📱 Field App",
            "📸 Photo Evidence",
            "📽️ Presentation",
            "📊 Export Report",
            "📢 Marketing Sites",
            "📢 Marketing Dashboard",
            "🔔 Notifications",
            "📖 User Manual"
        ],

        "planning": [
            "📊 Dashboard",
            "📦 Inventory Dashboard",
            "📁 Site Tracker",
            "🧱 Milestones",
            "📊 Export Report",
            "🔔 Notifications",
            "📖 User Manual"
        ],

        "marketing": [
            "📊 Dashboard",
            "📢 Marketing Dashboard",
            "📢 Marketing Sites",
            "💬 Chat & Notif",
            "🔔 Notifications",
            "📖 User Manual"
        ],

        "viewer": [
            "📊 Dashboard",
            "📦 Inventory Dashboard",
            "📢 Marketing Dashboard",
            "📁 Site Tracker",
            "📊 Export Report",
            "📖 User Manual"
        ]
    }

    menu_options = ROLE_MENU.get(
        role,
        ROLE_MENU["viewer"]
    )

    menu = st.radio(
        "📂 Navigasi",
        menu_options
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "🔄 Refresh",
            use_container_width=True
        ):
            st.cache_data.clear()
            st.rerun()

    with col2:
        if st.button(
            "📽️ Presentation",
            use_container_width=True
        ):
            st.session_state.presentation_mode = True
            st.rerun()

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):
        st.session_state.clear()
        st.session_state.logged_in = False
        st.rerun()


# ==========================================================
# PRESENTATION MODE
# ==========================================================
if st.session_state.presentation_mode:
    from presentation import presentation_page
    presentation_page()
    st.stop()


# ==========================================================
# ROUTING MAP
# ==========================================================
ROUTES = {

    "📊 Dashboard":
        ("dashboard", "dashboard_page"),

    "📁 Site Tracker":
        ("project_tracker", "project_tracker_page"),

    "🧱 Milestones":
        ("milestone_module", "milestone_page"),

    "📋 Kanban Board":
        ("kanban_board", "kanban_page"),

    "📦 Inventory":
        ("inventory_module", "inventory_page"),

    "🤖 AI Insights":
        ("ai_insights", "ai_insights_page"),

    "📊 Export Report":
        ("export_report", "export_report_page"),

    "💬 Chat & Notif":
        ("chat_module", "chat_notif_page"),

    "📋 Daily Tasks":
        ("daily_task", "daily_task_page"),

    "🔍 RCA Analysis":
        ("rca_page", "rca_page"),

    "📽️ Presentation":
        ("presentation", "presentation_page"),

    "📱 Field App":
        ("field_app", "field_app_page"),

    "👥 User Management":
        ("user_management", "user_management_page"),

    "⚙️ Settings":
        ("settings_page", "settings_page"),

    "📢 Marketing Sites":
        ("marketing_page", "marketing_page"),

    "📢 Marketing Dashboard":
        ("marketing_dashboard", "marketing_dashboard_page"),

    "🔔 Notifications":
        ("notification_page", "notification_page")
}


# ==========================================================
# ROUTER
# ==========================================================
if menu == "📥 Bulk Import":
    bulk_import_page()

elif menu == "👷 Workforce":
    workforce_page()

elif menu == "📖 User Manual":
    user_manual_page()

elif menu == "📦 Inventory Dashboard":
    inventory_dashboard_page()

elif menu == "📸 Photo Evidence": 
    photo_page()

else:

    module_name, function_name = ROUTES[menu]

    module = __import__(
        module_name,
        fromlist=[function_name]
    )

    getattr(
        module,
        function_name
    )()
