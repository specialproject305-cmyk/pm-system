"""
supabase_db.py
Database connector untuk Streamlit + Supabase
Deploy-ready untuk Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import logging
from supabase import create_client, Client
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

# ─────────────────────────────────────────────────────────────
# 🔐 KONFIGURASI KONEKSI (Streamlit Cloud + Local Friendly)
# ─────────────────────────────────────────────────────────────

def get_supabase_client() -> Client:
    """
    Inisialisasi client Supabase.
    Support: Streamlit Cloud (via st.secrets) dan Local (via st.secrets atau fallback).
    """
    try:
        # Coba ambil dari Streamlit Secrets (bekerja di Cloud & local jika ada .streamlit/secrets.toml)
        SUPABASE_URL = "https://evwvnjwrsnsjrzoyrsum.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV2d3Zuandyc25zanJ6b3lyc3VtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgxNDY3OTEsImV4cCI6MjA5MzcyMjc5MX0.o2YCZVWLrUy2Zi4Yxsmg2kkakhv4wTQTSzJZcfUks6c"
    except (FileNotFoundError, KeyError, AttributeError):
        # Fallback untuk development local tanpa secrets.toml
        # ⚠️ Hanya untuk testing! Jangan hardcode key di production.
        url = "https://evwvnjwrsnsjrzoyrsum.supabase.co"
        key = st.secrets.get("SUPABASE_KEY", "") if hasattr(st, "secrets") else ""
        
        if not key or key == "":
            st.error("🔐 SUPABASE_KEY tidak ditemukan. Silakan tambahkan di Streamlit Cloud → Secrets.")
            st.stop()
    
    if not url or not key:
        st.error("⚠️ Konfigurasi Supabase tidak lengkap. Cek Secrets.")
        st.stop()
        
    return create_client(url, key)

# Inisialisasi client sekali saat module load
supabase: Client = get_supabase_client()

# ─────────────────────────────────────────────────────────────
# 📝 LOGGING CONFIG
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# 🔄 CACHED READ FUNCTIONS (Performa Optimal)
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner="🔄 Loading data...")
def read_sheet(table_name: str) -> pd.DataFrame:
    """
    Membaca semua data dari tabel Supabase dengan caching 60 detik.
    
    Args:
        table_name: Nama tabel di Supabase
        
    Returns:
        pd.DataFrame: Data dalam format DataFrame, kosong jika error/tabel kosong
    """
    try:
        response = supabase.table(table_name).select("*").execute()
        
        if response.data:
            logger.info(f"✅ Loaded {len(response.data)} rows from '{table_name}'")
            return pd.DataFrame(response.data)
        
        logger.info(f"ℹ️ Tabel '{table_name}' kosong.")
        return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"❌ Failed to read '{table_name}': {str(e)}")
        st.warning(f"⚠️ Gagal memuat data '{table_name}'. Cek koneksi atau konsol untuk detail.")
        return pd.DataFrame()


def read_sheet_no_cache(table_name: str) -> pd.DataFrame:
    """
    Membaca data TANPA caching (untuk data yang harus real-time).
    Gunakan hanya jika benar-benar diperlukan.
    """
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Failed to read '{table_name}' (no cache): {str(e)}")
        return pd.DataFrame()


def read_all_sheets(table_names: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
    """
    Membaca multiple tabel sekaligus.
    
    Args:
        table_names: List nama tabel. Jika None, pakai default.
        
    Returns:
        Dict dengan key=nama_tabel, value=DataFrame
    """
    if table_names is None:
        table_names = [
            'projects', 'milestones', 'materials', 
            'inventory_transactions', 'chat_messages', 
            'notifications', 'ai_insights', 'users'
        ]
    
    result = {}
    for t in table_names:
        result[t] = read_sheet(t)  # Pakai cached version
    return result

# ─────────────────────────────────────────────────────────────
# ✍️ WRITE FUNCTIONS (Dengan Error Handling + Return Value)
# ─────────────────────────────────────────────────────────────

def insert_row(table_name: str, data_dict: Dict[str, Any]) -> Optional[str]:
    """
    Insert satu baris data baru ke tabel.
    
    Args:
        table_name: Nama tabel tujuan
        data_dict: Dictionary dengan key=nama_kolom, value=nilai
        
    Returns:
        str: ID record yang berhasil di-insert, atau None jika gagal
    """
    try:
        # Pastikan id ada jika belum disediakan
        if 'id' not in data_dict:
            data_dict['id'] = generate_id()
        
        response = supabase.table(table_name).insert(data_dict).execute()
        
        if response.data and len(response.data) > 0:
            inserted_id = response.data[0].get('id')
            logger.info(f"✅ Inserted into '{table_name}' with id='{inserted_id}'")
            return inserted_id
        
        logger.warning(f"⚠️ Insert ke '{table_name}' tidak mengembalikan data")
        return None
        
    except Exception as e:
        logger.error(f"❌ Insert failed into '{table_name}': {str(e)}")
        st.error(f"💥 Gagal menyimpan  {str(e)[:100]}")  # Potong agar tidak terlalu panjang
        return None


def update_row(table_name: str, id_value: str, data_dict: Dict[str, Any]) -> bool:
    """
    Update satu baris berdasarkan ID.
    
    Args:
        table_name: Nama tabel
        id_value: ID record yang akan diupdate
        data_dict: Dictionary kolom yang akan diupdate (tanpa id)
        
    Returns:
        bool: True jika sukses, False jika gagal
    """
    try:
        response = supabase.table(table_name).update(data_dict).eq('id', id_value).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"✅ Updated {len(response.data)} row(s) in '{table_name}' id='{id_value}'")
            return True
        
        logger.warning(f"⚠️ Tidak ada baris dengan id='{id_value}' di '{table_name}'")
        return False
        
    except Exception as e:
        logger.error(f"❌ Update failed: {str(e)}")
        st.error(f"💥 Gagal update data: {str(e)[:100]}")
        return False


def delete_row_by_id(table_name: str, id_value: str) -> bool:
    """
    Hapus satu baris berdasarkan ID.
    
    Args:
        table_name: Nama tabel
        id_value: ID record yang akan dihapus
        
    Returns:
        bool: True jika sukses, False jika gagal
    """
    try:
        response = supabase.table(table_name).delete().eq('id', id_value).execute()
        
        # Supabase v2: response.data berisi data yang dihapus (jika ada)
        if response.data is not None:
            logger.info(f"✅ Deleted from '{table_name}' id='{id_value}'")
            return True
        
        logger.warning(f"⚠️ Tidak ada baris dengan id='{id_value}' di '{table_name}'")
        return False
        
    except Exception as e:
        logger.error(f"❌ Delete failed: {str(e)}")
        st.error(f"💥 Gagal hapus  {str(e)[:100]}")
        return False

# ─────────────────────────────────────────────────────────────
# 🔍 HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def find_row_by_id(table_name: str, id_value: str) -> Optional[Dict[str, Any]]:
    """
    Cari satu baris berdasarkan ID.
    
    Returns:
        dict: Data record jika ditemukan, None jika tidak
    """
    try:
        response = supabase.table(table_name).select("*").eq('id', id_value).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
        
    except Exception as e:
        logger.error(f"❌ Find failed: {str(e)}")
        return None


def generate_id() -> str:
    """Generate short unique ID (8 characters from UUID4)."""
    return str(uuid.uuid4())[:8]


def now_str() -> str:
    """Return current datetime as string 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def today_str() -> str:
    """Return current date as string 'YYYY-MM-DD'."""
    return datetime.now().strftime('%Y-%m-%d')


def safe_date_string(date_input) -> Optional[str]:
    """
    Konversi berbagai format input date ke string 'YYYY-MM-DD'.
    Support: datetime.date, datetime.datetime, string, None.
    
    Returns:
        str: Format 'YYYY-MM-DD' atau None jika tidak bisa dikonversi
    """
    if date_input is None:
        return None
    try:
        return pd.to_datetime(date_input).strftime('%Y-%m-%d')
    except Exception:
        logger.warning(f"⚠️ Gagal konversi date: {date_input}")
        return None

# ─────────────────────────────────────────────────────────────
# 🧪 UTILITY: Clear Cache (Untuk Debugging)
# ─────────────────────────────────────────────────────────────

def clear_cache():
    """Hapus semua cache read_sheet. Berguna saat debugging data."""
    read_sheet.clear()
    logger.info("🗑️ Cache database cleared.")
    st.toast("🔄 Cache di-refresh", icon="♻️")
