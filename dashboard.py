import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_db import read_all_sheets

def dashboard_page():
    # ─────────────────────────────────────────────────────────────
    # 🎨 DARK THEME CSS (RINGAN & STABIL)
    # ─────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
        .stApp { background-color: #0B1120; color: #FFFFFF; font-family: 'Inter', sans-serif; }
        [data-testid="stSidebar"] { background-color: #1E293B; border-right: 1px solid #334155; }
        [data-testid="stSidebar"] * { color: #E2E8F0 !important; }
        .kpi-box { background: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 15px; text-align: center; height: 100%; }
        .kpi-val { font-size: 1.8rem; font-weight: 800; color: #38BDF8; margin: 5px 0; }
        .kpi-label { font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; }
        .stDataFrame { border-radius: 10px; overflow: hidden; }
        [data-testid="stDataFrame"] div { background-color: #1E293B; color: #FFFFFF !important; }
        thead th { background-color: #0F172A !important; color: #E2E8F0 !important; }
        #MainMenu, header, .stDecoration { display: none; }
    </style>
    """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────
    # 📥 LOAD DATA (SAFE & SIMPLE)
    # ─────────────────────────────────────────────────────────────
    try:
        all_data = read_all_sheets()
        df = all_data.get('projects', pd.DataFrame())
    except Exception as e:
        st.error(f"⚠️ Gagal memuat  {e}")
        return

    if df.empty:
        st.info("📭 Database masih kosong. Silakan tambahkan site di menu **Project Tracker** terlebih dahulu.")
        return

    # Konversi progress ke angka (aman dari string/NaN)
    df['progress'] = pd.to_numeric(df['progress'], errors='coerce').fillna(0)

    # ─────────────────────────────────────────────────────────────
    # 🧮 HITUNG TOTAL (100% AMAN, TANPA ERROR)
    # ─────────────────────────────────────────────────────────────
    total = len(df)
    status_col = 'status' if 'status' in df.columns else None
    
    done = len(df[df[status_col] == 'DONE']) if status_col else 0
    ongoing = len(df[df[status_col] == 'ONGOING']) if status_col else 0
    pending = len(df[df[status_col] == 'PENDING']) if status_col else 0
    delayed = len(df[df[status_col].isin(['DELAYED', 'CRITICAL'])]) if status_col else 0
    avg_prog = df['progress'].mean()
    if pd.isna(avg_prog): avg_prog = 0.0

    # ─────────────────────────────────────────────────────────────
    # 🖼️ TAMPILAN DASHBOARD (TOTAL + TABEL)
    # ─────────────────────────────────────────────────────────────
    st.markdown("<h2 style='color:#38BDF8;'>📊 Ringkasan Proyek</h2>", unsafe_allow_html=True)
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(f"<div class='kpi-box'><div class='kpi-label'>Total Site</div><div class='kpi-val'>{total}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi-box'><div class='kpi-label'>✅ RFS / DONE</div><div class='kpi-val'>{done}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi-box'><div class='kpi-label'>⚙️ On Progress</div><div class='kpi-val'>{ongoing}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi-box'><div class='kpi-label'>⏸️ Not Started</div><div class='kpi-val'>{pending}</div></div>", unsafe_allow_html=True)
    c5.markdown(f"<div class='kpi-box'><div class='kpi-label'>🔴 Delayed</div><div class='kpi-val'>{delayed}</div></div>", unsafe_allow_html=True)
    c6.markdown(f"<div class='kpi-box'><div class='kpi-label'> Avg Progress</div><div class='kpi-val'>{avg_prog:.1f}%</div></div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("<h3 style='color:#CBD5E1;'>📋 Data Site Lengkap</h3>", unsafe_allow_html=True)
    
    # Pilih kolom yang aman untuk ditampilkan
    safe_cols = ['site_id', 'site_name', 'status', 'progress', 'vendor', 'pm', 'site_category', 'end_date']
    display_cols = [c for c in safe_cols if c in df.columns]
    
    # Sortir: Delayed & Done dulu, agar fokus ke yang penting
    if status_col:
        status_order = {'DELAYED': 0, 'CRITICAL': 1, 'ONGOING': 2, 'PENDING': 3, 'DONE': 4}
        df['sort_key'] = df[status_col].map(status_order).fillna(5)
        df = df.sort_values('sort_key').drop(columns=['sort_key'])
        
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
    
    st.caption(f"🔄 Data terakhir dimuat: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

if __name__ == "__main__":
    dashboard_page()
