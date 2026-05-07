import psycopg2
import psycopg2.extras
import pandas as pd
import uuid
from datetime import datetime
import streamlit as st

# GANTI PASSWORD KAMU!
DB_URL = "postgresql://postgres:specialproject_305@db.ewvnjwrssnjsrzoysrum.supabase.co:5432/postgres"

def get_conn():
    return psycopg2.connect(DB_URL)

def read_sheet(table_name):
    try:
        conn = get_conn()
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()

def read_all_sheets():
    result = {}
    tables = ['projects', 'milestones', 'materials', 'inventory_transactions', 'chat_messages', 'notifications', 'ai_insights']
    for t in tables:
        result[t] = read_sheet(t)
    return result

def insert_row(table_name, data_dict):
    conn = get_conn()
    cur = conn.cursor()
    columns = ', '.join(data_dict.keys())
    placeholders = ', '.join(['%s'] * len(data_dict))
    values = list(data_dict.values())
    cur.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
    conn.commit()
    conn.close()

def update_row(table_name, row_index, data_dict):
    pass

def find_row_by_id(table_name, id_value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name} WHERE id = %s", (id_value,))
    row = cur.fetchone()
    conn.close()
    return row

def delete_row_by_id(table_name, id_value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table_name} WHERE id = %s", (id_value,))
    conn.commit()
    conn.close()

def generate_id():
    return str(uuid.uuid4())[:8]

def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def today_str():
    return datetime.now().strftime('%Y-%m-%d')

