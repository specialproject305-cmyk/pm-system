import pandas as pd
import uuid
from datetime import datetime
import streamlit as st

# ===== DATA DUMMY =====
if "dummy_data" not in st.session_state:
    st.session_state.dummy_data = {
        "projects": pd.DataFrame([
            {"id": "p001", "site_id": "SITE-001", "site_name": "Tower Gambir", "site_coordinate": "-6.1754,106.8272", "vendor": "PT. Mitra A", "start_date": "2026-01-01", "end_date": "2026-06-30", "start_date_actual": "2026-01-05", "end_date_actual": "", "status": "ON_TRACK", "progress": "75", "pm": "Budi"},
            {"id": "p002", "site_id": "SITE-002", "site_name": "Tower Thamrin", "site_coordinate": "-6.1824,106.8234", "vendor": "PT. Karya B", "start_date": "2026-02-01", "end_date": "2026-07-31", "start_date_actual": "", "end_date_actual": "", "status": "DELAYED", "progress": "30", "pm": "Siti"},
            {"id": "p003", "site_id": "SITE-003", "site_name": "Tower Kuningan", "site_coordinate": "-6.2245,106.8156", "vendor": "PT. Mitra A", "start_date": "2026-03-01", "end_date": "2026-08-31", "start_date_actual": "", "end_date_actual": "", "status": "CRITICAL", "progress": "10", "pm": "Andi"},
        ]),
        "milestones": pd.DataFrame([
            {"id": "m001", "project_id": "p001", "name": "Hunting dan Survey", "planned_start": "2026-01-01", "planned_end": "2026-01-15", "actual_start": "2026-01-05", "actual_end": "2026-01-14", "dependency_id": "", "weight": "10", "status": "DONE", "material_status": "Lengkap"},
            {"id": "m002", "project_id": "p001", "name": "Validation", "planned_start": "2026-01-16", "planned_end": "2026-01-30", "actual_start": "2026-01-20", "actual_end": "", "dependency_id": "m001", "weight": "10", "status": "ONGOING", "material_status": "Belum Dicek"},
            {"id": "m003", "project_id": "p002", "name": "Foundation", "planned_start": "2026-02-01", "planned_end": "2026-02-28", "actual_start": "", "actual_end": "", "dependency_id": "", "weight": "20", "status": "DELAYED", "material_status": "Tidak Lengkap"},
        ]),
        "materials": pd.DataFrame([
            {"id": "mat001", "code": "MAT-001", "name": "Besi Beton 10mm", "unit": "batang", "min_stock": "100", "current_stock": "500", "unit_price": "15000"},
            {"id": "mat002", "code": "MAT-002", "name": "Semen Portland", "unit": "sak", "min_stock": "50", "current_stock": "30", "unit_price": "65000"},
            {"id": "mat003", "code": "MAT-003", "name": "Pasir Halus", "unit": "m3", "min_stock": "20", "current_stock": "80", "unit_price": "250000"},
        ]),
        "inventory_transactions": pd.DataFrame([]),
        "chat_messages": pd.DataFrame([]),
        "notifications": pd.DataFrame([]),
        "users": pd.DataFrame([]),
        "ai_insights": pd.DataFrame([]),
    }

# ===== FUNGSI-FUNGSI =====
def read_sheet(sheet_name):
    if sheet_name in st.session_state.dummy_data:
        return st.session_state.dummy_data[sheet_name].copy()
    return pd.DataFrame()

def read_all_sheets():
    result = {}
    for name in ["projects", "milestones", "materials", "inventory_transactions", "chat_messages", "notifications", "users", "ai_insights"]:
        result[name] = st.session_state.dummy_data.get(name, pd.DataFrame()).copy()
    return result

def insert_row(sheet_name, data_dict):
    if sheet_name in st.session_state.dummy_data:
        new_row = pd.DataFrame([data_dict])
        st.session_state.dummy_data[sheet_name] = pd.concat(
            [st.session_state.dummy_data[sheet_name], new_row], ignore_index=True
        )

def update_row(sheet_name, row_index, data_dict):
    pass

def find_row_by_id(sheet_name, id_value):
    return None

def delete_row_by_id(sheet_name, id_value):
    pass

def generate_id():
    return str(uuid.uuid4())[:8]

def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def today_str():
    return datetime.now().strftime('%Y-%m-%d')
