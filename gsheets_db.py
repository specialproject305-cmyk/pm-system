import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import uuid
from datetime import datetime
import streamlit as st

@st.cache_resource
def get_gsheet_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # DEBUG: Cek apakah file ada
    import os
    if os.path.exists("credentials.json"):
        st.success("✅ File credentials.json ditemukan")
    else:
        st.error("❌ File credentials.json TIDAK ditemukan")
        # Coba pakai service_account.json
        if os.path.exists("service_account.json"):
            st.warning("⚠️ Pakai service_account.json")
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
            return gspread.authorize(creds)
    
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    return gspread.authorize(creds)
    ]
    # Baca dari file credentials.json
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    return gspread.authorize(creds)

def get_sheet(sheet_name):
    client = get_gsheet_client()
    spreadsheet = client.open("PM_Database")
    return spreadsheet.worksheet(sheet_name)

@st.cache_data(ttl=60)
def read_all_sheets():
    result = {}
    sheet_names = ['projects', 'milestones', 'materials', 'inventory_transactions', 
                   'chat_messages', 'notifications', 'users', 'ai_insights']
    try:
        client = get_gsheet_client()
        spreadsheet = client.open("PM_Database")
        for name in sheet_names:
            try:
                ws = spreadsheet.worksheet(name)
                data = ws.get_all_records()
                result[name] = pd.DataFrame(data) if data else pd.DataFrame()
            except:
                result[name] = pd.DataFrame()
    except Exception as e:
        st.error(f"Error: {e}")
        for name in sheet_names:
            result[name] = pd.DataFrame()
    return result

@st.cache_data(ttl=60)
def read_sheet(sheet_name):
    try:
        sheet = get_sheet(sheet_name)
        data = sheet.get_all_records()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        st.error(f"Error membaca {sheet_name}: {e}")
        return pd.DataFrame()

def insert_row(sheet_name, data_dict):
    sheet = get_sheet(sheet_name)
    headers = sheet.row_values(1)
    row = [str(data_dict.get(h, '')) for h in headers]
    sheet.append_row(row)
    st.cache_data.clear()

def update_row(sheet_name, row_index, data_dict):
    sheet = get_sheet(sheet_name)
    headers = sheet.row_values(1)
    for col_idx, header in enumerate(headers, start=1):
        if header in data_dict:
            sheet.update_cell(row_index, col_idx, str(data_dict[header]))
    st.cache_data.clear()

def find_row_by_id(sheet_name, id_value):
    sheet = get_sheet(sheet_name)
    try:
        ids = sheet.col_values(1)
        row_idx = ids.index(str(id_value)) + 1
        return row_idx
    except ValueError:
        return None

def delete_row_by_id(sheet_name, id_value):
    row_idx = find_row_by_id(sheet_name, id_value)
    if row_idx:
        sheet = get_sheet(sheet_name)
        headers = sheet.row_values(1)
        empty = [''] * len(headers)
        sheet.update(f'A{row_idx}:{chr(64+len(headers))}{row_idx}', [empty])
    st.cache_data.clear()

def generate_id():
    return str(uuid.uuid4())[:8]

def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def today_str():
    return datetime.now().strftime('%Y-%m-%d')
