import streamlit as st
from supabase import create_client
import pandas as pd
import uuid
from datetime import datetime

SUPABASE_URL = "https://evwvnjwrsnsjrzoyrsum.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV2d3Zuandyc25zanJ6b3lyc3VtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3ODE0Njc5MSwiZXhwIjoyMDkzNzIyNzkxfQ.NOZLzQBzPShzihKgkGgLB76_XDmShNr8c0OxKOF_TQM"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def read_sheet(table_name):
    try:
        res = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except:
        return pd.DataFrame()

def read_all_sheets():
    result = {}
    tables = ['projects', 'milestones', 'materials', 'inventory_transactions', 'chat_messages', 'notifications', 'ai_insights']
    for t in tables:
        result[t] = read_sheet(t)
    return result

def insert_row(table_name, data_dict):
    supabase.table(table_name).insert(data_dict).execute()

def generate_id():
    return str(uuid.uuid4())[:8]

def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def today_str():
    return datetime.now().strftime('%Y-%m-%d')

def update_row(a, b, c): pass
def find_row_by_id(a, b): return None
def delete_row_by_id(a, b): pass
