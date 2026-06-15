import streamlit as st
import pandas as pd
from datetime import date, datetime
from supabase_db import read_sheet, insert_row, update_row, delete_row_by_id, generate_id, now_str

def inject_workforce_css():
    """Menyuntikkan gaya desain UI premium ala dashboard modern"""
    st.markdown("""
    <style>
        /* === BACKGROUND & CANVAS === */
        .stApp {
            background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%) !important;
            color: #1E293B;
            font-family: 'Inter', sans-serif;
        }
        
        /* === TABS CUSTOM STYLING === */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 20px !important;
            padding: 8px 20px !important;
            font-weight: 600 !important;
            color: #475569 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%) !important;
            color: white !important;
            border-color: #3B82F6 !important;
            box-shadow: 0 4px 10px rgba(59, 130, 246, 0.25) !important;
        }

        /* === CONTAINER / CARDS === */
        div[data-testid="stContainer"] {
            background: #FFFFFF !important;
            padding: 22px !important;
            border-radius: 16px !important;
            border: 1px solid #E2E8F0 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
            margin-bottom: 15px !important;
        }
        
        /* === PREMIUM METRICS BOX === */
        .metric-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        .metric-card .val {
            font-size: 2rem;
            font-weight: 800;
            color: #1E3A8A;
        }
        .metric-card .lbl {
            font-size: 0.75rem;
            color: #64748B;
            text-transform: uppercase;
            font-weight: 700;
            margin-top: 4px;
        }

        /* === ATTENDANCE CARDS === */
        .attendance-card {
            padding: 15px;
            border-radius: 14px;
            text-align: center;
            margin-bottom: 10px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
            transition: transform 0.2s;
        }
        .attendance-card:hover {
            transform: translateY(-2px);
        }
        
        /* === CUSTOM INPUT COMPONENT === */
        div[data-testid="stForm"] {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 14px !important;
            padding: 20px !important;
        }
    </style>
    """, unsafe_allow_html=True)

def workforce_page():
    # Suntikkan gaya CSS baru di awal halaman
    inject_workforce_css()
    
    st.markdown('<h1 style="color:#0F172A; font-weight:800; letter-spacing:-1px;">👷 Workforce Management Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#475569; margin-top:-10px; margin-bottom:25px; font-size:0.95rem;">Manage team allocations, live daily attendance tracking, and capacity utilization analytics.</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Data Pekerja", "📋 Assignment Project", "📅 Live Attendance", "📊 Team Utilization"])
    
    # Load data dari database
    wf_df = read_sheet("workforce")
    ms_df = read_sheet("milestones")
    sites_df = read_sheet("projects")
    assign_df = read_sheet("workforce_assignments")
    att_df = read_sheet("workforce_attendance")
    
    # =========================================================
    # 👥 TAB 1: DATA PEKERJA
    # =========================================================
    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            with st.container():
                st.markdown("<h3 style='margin-top:0; color:#0F172A;'>📋 Manpower Overview</h3>", unsafe_allow_html=True)
                
                if not wf_df.empty:
                    m_a, m_b = st.columns(2)
                    with m_a:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="val">{len(wf_df)}</div>
                            <div class="lbl">Registered Workforce</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with m_b:
                        active = len(wf_df[wf_df['status']=='Active'])
                        st.markdown(f"""
                        <div class="metric-card" style="border-left: 4px solid #10B981;">
                            <div class="val" style="color:#10B981;">{active}</div>
                            <div class="lbl">Active Status</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Filter Bar Terintegrasi
                    status_filter = st.selectbox("🎯 Quick Status Filter:", ['All', 'Active', 'On Leave', 'Inactive'])
                    display = wf_df.copy()
                    if status_filter != 'All': 
                        display = display[display['status'] == status_filter]
                    
                    available_cols = [c for c in ['name', 'role', 'skill', 'phone', 'status'] if c in display.columns]
                    st.dataframe(display[available_cols], use_container_width=True, hide_index=True)
                else:
                    st.info("Belum ada data pekerja terdaftar di database.")
        
        with col2:
            st.subheader("➕ Registrasi Pekerja")
            with st.form("add_worker"):
                name = st.text_input("Nama Lengkap")
                role = st.selectbox("Role / Posisi Utama", ["Engineer", "Technician", "Rigger", "Supervisor", "Driver", "Admin", "Other"])
                skill = st.text_input("Keahlian Spesifik / Sertifikasi", placeholder="Sipil, Tower, FO, K3 Telekomunikasi")
                phone = st.text_input("Nomor Telepon / WhatsApp")
                email = st.text_input("Alamat Email")
                status = st.selectbox("Status Penugasan", ["Active", "On Leave", "Inactive"])
                
                if st.form_submit_button("💾 Simpan Data Manpower", type="primary", use_container_width=True):
                    if name.strip() == "":
                        st.error("Nama wajib diisi!")
                    else:
                        insert_row("workforce", {
                            'id': generate_id(), 'name': name, 'role': role,
                            'skill': skill, 'phone': phone, 'email': email, 'status': status
                        })
                        st.success(f"✅ {name} sukses didaftarkan ke sistem!")
                        st.rerun()
    
    # =========================================================
    # 📋 TAB 2: ASSIGNMENT
    # =========================================================
    with tab2:
        with st.container():
            st.markdown("<h3 style='margin-top:0; color:#0F172A;'>🔗 Alokasi Tim Terarah</h3>", unsafe_allow_html=True)
            
            if not wf_df.empty and not ms_df.empty:
                col_a, col_b = st.columns(2)
                with col_a:
                    sel_worker = st.selectbox(
                        "👷 Pilih Personel Lapangan:", 
                        wf_df['id'].tolist(),
                        format_func=lambda x: wf_df[wf_df['id'] == x]['name'].values[0] if not wf_df[wf_df['id'] == x].empty else str(x)
                    )
                with col_b:
                    sel_ms = st.selectbox(
                        "📌 Hubungkan ke Milestone/Site:", 
                        ms_df['id'].tolist(),
                        format_func=lambda x: str(ms_df[ms_df['id'] == x]['name'].values[0])[:60] if not ms_df[ms_df['id'] == x].empty else str(x)
                    )
            
                if st.button("🚀 Tempatkan Personel ke Proyek", type="primary", use_container_width=True):
                    insert_row("workforce_assignments", {
                        'id': generate_id(), 'workforce_id': sel_worker,
                        'milestone_id': sel_ms, 'assigned_date': date.today().strftime('%Y-%m-%d'),
                        'status': 'Assigned'
                    })
                    st.success("✅ Surat Penugasan Terbit! Data berhasil di-update.")
                    st.rerun()
            else:
                st.warning("Data Pekerja atau Milestone kosong. Penugasan tidak dapat dilakukan.")
        
        with st.container():
            st.markdown("<h4>📋 20 Riwayat Penugasan Terakhir</h4>", unsafe_allow_html=True)
            if not assign_df.empty:
                wf_map = dict(zip(wf_df['id'], wf_df['name'])) if not wf_df.empty else {}
                ms_map = dict(zip(ms_df['id'], ms_df['name'])) if not ms_df.empty else {}
                
                assign_df['worker_name'] = assign_df['workforce_id'].map(wf_map)
                assign_df['task_name'] = assign_df['milestone_id'].map(ms_map)
                
                show_cols = [c for c in ['worker_name', 'task_name', 'assigned_date', 'status'] if c in assign_df.columns]
                st.dataframe(assign_df[show_cols].tail(20), use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada logs aktivitas penugasan lapangan.")
    
    # =========================================================
    # 📅 TAB 3: ATTENDANCE
    # =========================================================
    with tab3:
        today = date.today().strftime('%Y-%m-%d')
        st.markdown(f"""
        <div style="background:#0F172A; padding:15px; border-radius:12px; color:white; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
            <span style="font-size:1.1rem; font-weight:700; padding-left:10px;">📅 Presensi Kehadiran Tim</span>
            <span style="background:#3B82F6; padding:4px 14px; border-radius:20px; font-size:0.85rem; font-weight:700;">Hari Ini: {today}</span>
        </div>
        """, unsafe_allow_html=True)
        
        if not wf_df.empty:
            cols = st.columns(4)
            for i, (_, w) in enumerate(wf_df.iterrows()):
                with cols[i % 4]:
                    current_status = 'Not Set'
                    match_id = None
                    
                    if not att_df.empty and 'workforce_id' in att_df.columns and 'date' in att_df.columns:
                        match = att_df[(att_df['workforce_id'] == w['id']) & (att_df['date'] == today)]
                        if not match.empty:
                            current_status = match['status'].values[0]
                            match_id = match['id'].values[0] if 'id' in match.columns else None
                    
                    bg_color = {'Present': '#DCFCE7', 'Absent': '#FEE2E2', 'Leave': '#FEF3C7', 'Not Set': '#F1F5F9'}.get(current_status, '#F1F5F9')
                    text_color = {'Present': '#15803D', 'Absent': '#B91C1C', 'Leave': '#B45309', 'Not Set': '#475569'}.get(current_status, '#475569')
                    
                    st.markdown(f"""
                    <div class="attendance-card" style="background: #FFFFFF;">
                        <div style="font-weight:700; color:#0F172A; font-size:1rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{w['name']}</div>
                        <div style="color:#64748B; font-size:0.75rem; font-weight:500; margin-bottom:8px;">💼 {w['role']}</div>
                        <span style="background:{bg_color}; color:{text_color}; font-size:0.75rem; font-weight:700; padding:4px 12px; border-radius:12px; display:inline-block; margin-bottom:12px;">
                            {current_status.upper()}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("✅", key=f"p_{w['id']}", help=f"Set {w['name']} Hadir"): 
                            if match_id: update_row("workforce_attendance", match_id, {'status': 'Present'})
                            else: insert_row("workforce_attendance", {'id': generate_id(), 'workforce_id': w['id'], 'date': today, 'status': 'Present'})
                            st.rerun()
                    with c2:
                        if st.button("❌", key=f"a_{w['id']}", help=f"Set {w['name']} Alpa"): 
                            if match_id: update_row("workforce_attendance", match_id, {'status': 'Absent'})
                            else: insert_row("workforce_attendance", {'id': generate_id(), 'workforce_id': w['id'], 'date': today, 'status': 'Absent'})
                            st.rerun()
                    with c3:
                        if st.button("🏖️", key=f"l_{w['id']}", help=f"Set {w['name']} Izin/Cuti"): 
                            if match_id: update_row("workforce_attendance", match_id, {'status': 'Leave'})
                            else: insert_row("workforce_attendance", {'id': generate_id(), 'workforce_id': w['id'], 'date': today, 'status': 'Leave'})
                            st.rerun()
                    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)
        else:
            st.info("Silakan master data pekerja terlebih dahulu.")
            
    # =========================================================
    # 📊 TAB 4: UTILIZATION
    # =========================================================
    with tab4:
        with st.container():
            st.markdown("<h3 style='margin-top:0; color:#0F172A;'>📊 Manpower Resource Utilization Rate</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color:#64748B; font-size:0.85rem; margin-top:-5px;'>Rasio efektivitas penyelesaian target pekerjaan/milestone oleh masing-masing tenaga ahli.</p>", unsafe_allow_html=True)
            st.divider()
            
            if not wf_df.empty and not assign_df.empty:
                for _, w in wf_df.iterrows():
                    total_assign = len(assign_df[assign_df['workforce_id'] == w['id']]) if 'workforce_id' in assign_df.columns else 0
                    done_assign = len(assign_df[(assign_df['workforce_id'] == w['id']) & (assign_df['status'] == 'Completed')]) if total_assign > 0 and 'status' in assign_df.columns else 0
                    
                    rate = (done_assign / total_assign * 100) if total_assign > 0 else 0
                    bar_color = '#10B981' if rate >= 80 else ('#F59E0B' if rate >= 50 else '#EF4444')
                    
                    col_worker, col_bar = st.columns([1, 2])
                    with col_worker:
                        st.markdown(f"<div style='padding-top:5px;'><b>{w['name']}</b><br><small style='color:#64748B;'>{w['role']}</small></div>", unsafe_allow_html=True)
                    with col_bar:
                        st.progress(rate / 100)
                        st.markdown(f"<small style='color:#475569;'>Selesai: <b>{done_assign}</b> dari <b>{total_assign}</b> tugas &bull; Efisiensi: <b style='color:{bar_color};'>{rate:.0f}%</b></small>", unsafe_allow_html=True)
                    st.markdown("<div style='border-bottom: 1px solid #F1F5F9; margin: 10px 0;'></div>", unsafe_allow_html=True)
            else:
                st.info("Belum ada data distribusi proyek aktif untuk kalkulasi beban kerja tim.")

if __name__ == "__main__":
    workforce_page()
