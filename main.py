import streamlit as st
from dashboard import dashboard_page
from project_tracker import project_tracker_page
from milestone_module import milestone_page
from inventory_module import inventory_page
from ai_insights import ai_insights_page
from chat_module import chat_notif_page
from export_module import export_page

st.set_page_config(
    page_title="PM System",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"  # Sidebar auto-tutup di HP
)

st.sidebar.title("🏗️ PM System")
st.sidebar.markdown("---")

menu = st.sidebar.radio("Navigasi:", [
    "📊 Dashboard", "📁 Site Tracker", "🧱 Milestones",
    "📦 Inventory", "🤖 AI Insights", "💬 Chat & Notif", "📄 Export Report"
])

st.sidebar.markdown("---")
st.sidebar.info("v2.0 - Google Sheets • Multi-User")

def main():
    if menu == "📊 Dashboard":
        dashboard_page()
    elif menu == "📁 Site Tracker":
        project_tracker_page()
    elif menu == "🧱 Milestones":
        milestone_page()
    elif menu == "📦 Inventory":
        inventory_page()
    elif menu == "🤖 AI Insights":
        ai_insights_page()
    elif menu == "💬 Chat & Notif":
        chat_notif_page()
    elif menu == "📄 Export Report":
        export_page()

if __name__ == "__main__":
    main()

st.markdown("""
<style>
    /* Responsive untuk HP */
    @media (max-width: 768px) {
        .stApp {
            margin: 0;
            padding: 5px;
        }
        .stMarkdown h1 {
            font-size: 20px !important;
        }
        .stMarkdown h2 {
            font-size: 16px !important;
        }
        .stDataFrame {
            font-size: 10px !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 20px !important;
        }
        .stButton button {
            font-size: 12px !important;
            padding: 8px !important;
        }
    }
</style>
""", unsafe_allow_html=True)
