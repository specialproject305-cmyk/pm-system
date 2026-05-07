import streamlit as st
from supabase import create_client
import pandas as pd
import uuid
from datetime import datetime

SUPABASE_URL = "https://ewvnjwrssnjsrzoysrum.supabase.co"
SUPABASE_KEY = "YeyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV2d3Zuandyc25zanJ6b3lyc3VtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgxNDY3OTEsImV4cCI6MjA5MzcyMjc5MX0.o2YCZVWLrUy2Zi4Yxsmg2kkakhv4wTQTSzJZcfUks6c"  # GANTI dengan anon key dari Settings → API

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
