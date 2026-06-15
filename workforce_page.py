import streamlit as st
import pandas as pd
from datetime import date, datetime
from supabase_db import read_sheet, insert_row, update_row, delete_row_by_id, generate_id, now_str

def workforce_page():
    st.title("👷 Workforce Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Data Pekerja", "📋 Assignment", "📅 Attendance", "📊 Utilization"])
    
    # Membaca data dari tabel Supabase
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
            if not wf_df.empty:
                m_a, m_b = st.columns(2)
                with m_a:
                    st.metric("Total Workforce", len(wf_df))
                with m_b:
                    active = len(wf_df[wf_df['status']=='Active'])
                    st.metric("✅ Active Workers", active)
                
                st.divider()
                # Filter status pekerja
                status_filter = st.selectbox("Filter Status Pekerja:", ['All', 'Active', 'On Leave', 'Inactive'])
                display = wf_df.copy()
                if status_filter != 'All': 
                    display = display[display['status'] == status_filter]
                
                # Menampilkan kolom data utama pekerja
                available_cols = [c for c in ['name', 'role', 'skill', 'phone', 'status'] if c in display.columns]
                st.dataframe(display[available_cols], use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada data pekerja di database.")
        
        with col2:
            st.subheader("➕ Tambah Pekerja")
            with st.form("add_worker"):
                name = st.text_input("Nama Lengkap")
                role = st.selectbox("Role / Posisi", ["Engineer", "Technician", "Rigger", "Supervisor", "Driver", "Admin", "Other"])
                skill = st.text_input("Keahlian Spesifik", placeholder="Sipil, Tower, Fiber Optic")
                phone = st.text_input("Nomor Telepon/WA")
                email = st.text_input("Email")
                status = st.selectbox("Status Awal", ["Active", "On Leave", "Inactive"])
                
                if st.form_submit_button("💾 Simpan Data", type="primary", use_container_width=True):
                    if name.strip() == "":
                        st.error("Nama tidak boleh kosong!")
                    else:
                        insert_row("workforce", {
                            'id': generate_id(), 'name': name, 'role': role,
                            'skill': skill, 'phone': phone, 'email': email, 'status': status
                        })
                        st.success(f"✅ {name} berhasil ditambahkan!")
                        st.rerun()
    
    # =========================================================
    # 📋 TAB 2: ASSIGNMENT
    # =========================================================
    with tab2:
        st.subheader("📋 Assign Pekerja ke Milestone")
        
        if not wf_df.empty and not ms_df.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                sel_worker = st.selectbox(
                    "👷 Pilih Pekerja:", 
                    wf_df['id'].tolist(),
                    format_func=lambda x: wf_df[wf_df['id'] == x]['name'].values[0] if not wf_df[wf_df['id'] == x].empty else str(x)
                )
            with col_b:
                sel_ms = st.selectbox(
                    "📌 Pilih Milestone:", 
                    ms_df['id'].tolist(),
                    format_func=lambda x: str(ms_df[ms_df['id'] == x]['name'].values[0])[:50] if not ms_df[ms_df['id'] == x].empty else str(x)
                )
        
            if st.button("✅ Lakukan Assignment", type="primary"):
                insert_row("workforce_assignments", {
                    'id': generate_id(), 
                    'workforce_id': sel_worker,
                    'milestone_id': sel_ms, 
                    'assigned_date': date.today().strftime('%Y-%m-%d'),
                    'status': 'Assigned'
                })
                st.success("✅ Pekerja berhasil ditugaskan ke milestone!"); 
                st.rerun()
        else:
            st.warning("Pastikan data Pekerja dan data Milestone sudah terisi untuk melakukan assignment.")
        
        st.divider()
        st.subheader("📋 Daftar Assignment Aktif")
        if not assign_df.empty:
            wf_map = dict(zip(wf_df['id'], wf_df['name'])) if not wf_df.empty else {}
            ms_map = dict(zip(ms_df['id'], ms_df['name'])) if not ms_df.empty else {}
            
            assign_df['worker_name'] = assign_df['workforce_id'].map(wf_map)
            assign_df['task_name'] = assign_df['milestone_id'].map(ms_map)
            
            show_cols = [c for c in ['worker_name', 'task_name', 'assigned_date', 'status'] if c in assign_df.columns]
            st.dataframe(assign_df[show_cols].tail(20), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada riwayat penugasan tim.")
    
    # =========================================================
    # 📅 TAB 3: ATTENDANCE
    # =========================================================
    with tab3:
        st.subheader("📅 Log Absensi Mandiri Hari Ini")
        today = date.today().strftime('%Y-%m-%d')
        st.info(f"Tanggal Operasional: **{today}**")
        
        if not wf_df.empty:
            cols = st.columns(4)
            for i, (_, w) in enumerate(wf_df.iterrows()):
                with cols[i % 4]:
                    current_status = 'Not Set'
                    match_id = None
                    
                    # 🛠️ FIXED PERBAIKAN INDENTASI & LOGIKA PENCARIAN ABSENSI
                    if not att_df.empty and 'workforce_id' in att_df.columns and 'date' in att_df.columns:
                        match = att_df[(att_df['workforce_id'] == w['id']) & (att_df['date'] == today)]
                        if not match.empty:
                            current_status = match['status'].values[0]
                            match_id = match['id'].values[0] if 'id' in match.columns else None
                    
                    # Visualisasi Warna Card Absensi
                    color = {'Present': '#DCFCE7', 'Absent': '#FEE2E2', 'Leave': '#FEF3C7', 'Not Set': '#F8FAFC'}
                    st.markdown(f"""
                    <div style="background:{color.get(current_status, '#F8FAFC')}; padding:12px; border-radius:10px; text-align:center; margin:5px 0; border:1px solid #E2E8F0;">
                        <strong style="color:#1E293B;">{w['name']}</strong><br>
                        <small style="color:#64748B;">{w['role']}</small><br>
                        <span style="font-size:0.8rem; font-weight:bold; margin-top:4px; display:inline-block; color:#0F172A;">Status: {current_status}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Sistem Aksi Tombol Absensi (Logika Upsert Mengamankan Data Ganda)
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("✅", key=f"p_{w['id']}", help="Set Hadir"): 
                            if match_id:
                                update_row("workforce_attendance", match_id, {'status': 'Present'})
                            else:
                                insert_row("workforce_attendance", {'id': generate_id(), 'workforce_id': w['id'], 'date': today, 'status': 'Present'})
                            st.rerun()
                    with c2:
                        if st.button("❌", key=f"a_{w['id']}", help="Set Alpa/Tidak Hadir"): 
                            if match_id:
                                update_row("workforce_attendance", match_id, {'status': 'Absent'})
                            else:
                                insert_row("workforce_attendance", {'id': generate_id(), 'workforce_id': w['id'], 'date': today, 'status': 'Absent'})
                            st.rerun()
                    with c3:
                        if st.button("🏖️", key=f"l_{w['id']}", help="Set Cuti/Izin"): 
                            if match_id:
                                update_row("workforce_attendance", match_id, {'status': 'Leave'})
                            else:
                                insert_row("workforce_attendance", {'id': generate_id(), 'workforce_id': w['id'], 'date': today, 'status': 'Leave'})
                            st.rerun()
        else:
            st.info("Silakan daftarkan pekerja terlebih dahulu di Tab Data Pekerja.")
            
    # =========================================================
    # 📊 TAB 4: UTILIZATION
    # =========================================================
    with tab4:
        st.subheader("📊 Team Performance & Utilization Rate")
        
        if not wf_df.empty and not assign_df.empty:
            for _, w in wf_df.iterrows():
                total_assign = len(assign_df[assign_df['workforce_id'] == w['id']]) if 'workforce_id' in assign_df.columns else 0
                
                if total_assign > 0 and 'status' in assign_df.columns:
                    done_assign = len(assign_df[(assign_df['workforce_id'] == w['id']) & (assign_df['status'] == 'Completed')])
                else:
                    done_assign = 0
                
                rate = (done_assign / total_assign * 100) if total_assign > 0 else 0
                
                # Menampilkan bar utilitas pekerja
                st.markdown(f"**{w['name']}** — <small style='color:#475569;'>{w['role']}</small>", unsafe_allow_html=True)
                st.progress(rate / 100)
                st.caption(f"Hasil Kerja: {done_assign}/{total_assign} Milestone Selesai • **Persentase: {rate:.0f}%**")
                st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
        else:
            st.info("Data performa/utilization belum tersedia karena belum ada aktivitas penugasan proyek.")

if __name__ == "__main__":
    workforce_page()
