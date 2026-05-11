"""
supabase_db.py - PRODUCTION READY
Koneksi Streamlit + Supabase dengan error handling lengkap
"""

import streamlit as st
import pandas as pd
import logging
from supabase import create_client, Client
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

# ─────────────────────────────────────────────────────────────
# 🔐 INISIALISASI SUPABASE CLIENT (Fix UnboundLocalError)
# ─────────────────────────────────────────────────────────────

def get_supabase_client() -> Client:
    """
    Inisialisasi client Supabase dengan fallback bertingkat.
    Mencegah UnboundLocalError dengan inisialisasi default.
    """
    # ✅ INISIALISASI DEFAULT (mencegah UnboundLocalError)
    url: Optional[str] = None
    key: Optional[str] = None
    
    # ── Level 1: Coba Streamlit Secrets (untuk Cloud) ──
    if hasattr(st, "secrets") and st.secrets:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        
        if url and key:
            logging.info("✅ Connected via Streamlit Secrets")
            return create_client(url, key)
    
    # ── Level 2: Coba Environment Variables (untuk local dev) ──
    import os
    url = os.getenv("SUPABASE_URL") or url
    key = os.getenv("SUPABASE_KEY") or key
    
    if url and key:
        logging.info("✅ Connected via Environment Variables")
        return create_client(url, key)
    
    # ── Level 3: Fallback Hardcode (HANYA untuk testing!) ──
    # ⚠️ HAPUS bagian ini setelah setup Secrets berhasi
    url = url or "https://evwvnjwrsnsjrzoyrsum.supabase.co"
    key = key or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV2d3Zuandyc25zanJ6b3lyc3VtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgxNDY3OTEsImV4cCI6MjA5MzcyMjc5MX0.o2YCZVWLrUy2Zi4Yxsmg2kkakhv4wTQTSzJZcfUks6c"
    
    logging.warning("⚠️ Using fallback credentials (remove after setup)")
    return create_client(url, key)


# ─────────────────────────────────────────────────────────────
# 🔄 INIT CLIENT (dengan error handling global)
# ─────────────────────────────────────────────────────────────

try:
    supabase: Client = get_supabase_client()
except Exception as e:
    st.error(f"🔥 Fatal Error: Gagal koneksi ke Supabase\n\n`{type(e).__name__}: {str(e)}`")
    st.info("💡 Cek: 1) Streamlit Secrets, 2) Format key, 3) Koneksi internet")
    st.stop()

# ─────────────────────────────────────────────────────────────
# 📝 LOGGING CONFIG
# ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# 🔄 READ FUNCTIONS (dengan caching)
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner="🔄 Loading data...")
def read_sheet(table_name: str) -> pd.DataFrame:
    """Baca semua data dari tabel Supabase dengan caching 60 detik."""
    try:
        response = supabase.table(table_name).select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Read failed '{table_name}': {str(e)}")
        return pd.DataFrame()


def read_sheet_no_cache(table_name: str) -> pd.DataFrame:
    """Baca data TANPA caching (untuk data real-time)."""
    try:
        response = supabase.table(table_name).select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Read failed (no cache) '{table_name}': {str(e)}")
        return pd.DataFrame()


def read_all_sheets(table_names: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
    """Membaca multiple tabel sekaligus."""
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
# ✍️ WRITE FUNCTIONS (dengan return value + error handling)
# ─────────────────────────────────────────────────────────────

def insert_row(table_name: str, data_dict: Dict[str, Any]) -> Optional[str]:
    """Insert satu baris. Returns ID jika sukses, None jika gagal."""
    try:
        if 'id' not in data_dict:
            data_dict['id'] = generate_id()
        
        response = supabase.table(table_name).insert(data_dict).execute()
        
        if response.data and len(response.data) > 0:
            inserted_id = response.data[0].get('id')
            logger.info(f"✅ Inserted '{table_name}' id='{inserted_id}'")
            return inserted_id
        return None
    except Exception as e:
        logger.error(f"❌ Insert failed: {str(e)}")
        st.error(f"💥 Gagal simpan: {str(e)[:100]}")
        return None


def update_row(table_name: str, id_value: str, data_dict: Dict[str, Any]) -> bool:
    """Update satu baris berdasarkan ID. Returns True jika sukses."""
    try:
        response = supabase.table(table_name).update(data_dict).eq('id', id_value).execute()
        success = bool(response.data and len(response.data) > 0)
        if success:
            logger.info(f"✅ Updated '{table_name}' id='{id_value}'")
        return success
    except Exception as e:
        logger.error(f"❌ Update failed: {str(e)}")
        return False


def delete_row_by_id(table_name: str, id_value: str) -> bool:
    """Hapus satu baris berdasarkan ID. Returns True jika sukses."""
    try:
        response = supabase.table(table_name).delete().eq('id', id_value).execute()
        success = response.data is not None
        if success:
            logger.info(f"✅ Deleted '{table_name}' id='{id_value}'")
        return success
    except Exception as e:
        logger.error(f"❌ Delete failed: {str(e)}")
        return False

# ─────────────────────────────────────────────────────────────
# 🔍 HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def find_row_by_id(table_name: str, id_value: str) -> Optional[Dict[str, Any]]:
    """Cari satu baris berdasarkan ID."""
    try:
        response = supabase.table(table_name).select("*").eq('id', id_value).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"❌ Find failed: {str(e)}")
        return None


def generate_id() -> str:
    """Generate short unique ID (8 chars)."""
    return str(uuid.uuid4())[:8]


def now_str() -> str:
    """Current datetime string."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def today_str() -> str:
    """Current date string."""
    return datetime.now().strftime('%Y-%m-%d')


def safe_date_string(date_input) -> Optional[str]:
    """Convert date input to 'YYYY-MM-DD' string."""
    if date_input is None:
        return None
    try:
        return pd.to_datetime(date_input).strftime('%Y-%m-%d')
    except Exception:
        return None


def clear_cache():
    """Clear read_sheet cache (untuk debugging)."""
    read_sheet.clear()
    st.toast("🔄 Cache cleared", icon="♻️")
