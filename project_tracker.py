import streamlit as st
import pandas as pd
from supabase_db import read_sheet, insert_row, update_row, find_row_by_id, generate_id, today_str

def sync_progress_from_milestones(site_id):
    ms_df = read_sheet("milestones")
    if ms_df.empty: return 0, 'ON_TRACK'
    site_ms = ms_df[ms_df['project_id'] == site_id]
    if site_ms.empty: return 0, 'ON_TRACK'

    site_ms['weight'] = pd.to_numeric(site_ms['weight'], errors='coerce').fillna(0)
    total_weight = site_ms['weight'].sum()
    done_weight = site_ms[site_ms['status'] == 'DONE']['weight'].sum()
    progress = round((done_weight / total_weight) * 100, 1) if total_weight > 0 else 0

    delayed = len(site_ms[site_ms['status'] == 'DELAYED'])
    status = 'CRITICAL' if delayed > 3 else ('DELAYED' if delayed > 0 else 'ON_TRACK')
    return progress, status

def project_tracker_page():
    st.title("📁 Site & Project Portfolio")
    
    # Session State untuk Filter
    if 'project_filter' not in st.session_state:
        st.session_state.project_filter = "ALL"

    # Load Master Projects (Safe Load)
    try:
        master_df = read_sheet("master_projects")
        project_options = ["ALL"] + master_df["id"].tolist() if not master_df.empty else ["ALL"]
    except Exception:
        master_df = pd.DataFrame()
        project_options = ["ALL"]

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Daftar Site", "🏢 Master Project", "➕ Tambah Site", "✏️ Edit Site", "📥 Import CSV"
    ])

    # ─────────────────────────────────────────────────────────────
    # TAB 1: DAFTAR SITE + FILTER PROYEK
    # ─────────────────────────────────────────────────────────────
    with tab1:
        st.subheader("Daftar Site")
        df = read_sheet("projects")
        
        if not df.empty:
            df['progress'] = pd.to_numeric(df['progress'], errors='coerce').fillna(0)
            
            # 🔍 FILTER BY PROJECT NAME
            st.markdown("### 🔍 Filter Proyek")
            selected_proj = st.selectbox(
                "Pilih Master Project:",
                project_options,
                format_func=lambda x: "🌍 SEMUA PROYEK" if x == "ALL" 
                else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}",
                key="proj_filter_tab1"
            )
            
            if selected_proj != st.session_state.project_filter:
                st.session_state.project_filter = selected_proj
                st.rerun()

            # Apply Filter
            if st.session_state.project_filter != "ALL" and 'master_project_id' in df.columns:
                df = df[df['master_project_id'] == st.session_state.project_filter]
            
            def color_status(val):
                if val == 'ON_TRACK': return 'background-color: #d4edda; font-weight: bold'
                elif val == 'DELAYED': return 'background-color: #fff3cd; font-weight: bold'
                elif val == 'CRITICAL': return 'background-color: #f8d7da; font-weight: bold'
                return ''
            
            display_cols = ['site_id', 'site_name', 'site_coordinate', 'vendor', 'pm', 'status', 'progress']
            display_df = df[[c for c in display_cols if c in df.columns]]
            styled = display_df.style.map(color_status, subset=['status']) if 'status' in df.columns else display_df
            st.dataframe(styled, use_container_width=True, hide_index=True)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Site", len(df))
            col2.metric("On Track", len(df[df['status']=='ON_TRACK']) if 'status' in df.columns else 0)
            col3.metric("Terlambat", len(df[df['status'].isin(['DELAYED','CRITICAL'])]) if 'status' in df.columns else 0)
            
            if st.button("🔄 Sync Progress dari Milestones", use_container_width=True):
                for _, row in df.iterrows():
                    prog, sts = sync_progress_from_milestones(row['id'])
                    ridx = find_row_by_id("projects", row['id'])
                    if ridx: update_row("projects", ridx, {'progress': str(prog), 'status': sts})
                st.cache_data.clear()
                st.success("✅ Progress di-sync!")
                st.rerun()
        else:
            st.info("📋 Belum ada site.")

    # ─────────────────────────────────────────────────────────────
    # TAB 2: MASTER PROJECT MANAGEMENT (FIXED SAVE & NOTIF)
    # ─────────────────────────────────────────────────────────────
    with tab2:
        st.subheader("🏢 Kelola Master Project")
        st.markdown("Tambahkan proyek induk untuk mengelompokkan site secara hierarkis.")
        
        with st.form("add_master_project"):
            c1, c2 = st.columns(2)
            with c1:
                p_code = st.text_input("Kode Proyek", placeholder="PROJ-4G-2026")
                p_name = st.text_input("Nama Proyek", placeholder="Rollout 4G Phase 1")
            with c2:
                p_cat = st.selectbox("Kategori", ["4G Rollout", "5G Upgrade", "Fiber Optic", "General"])
                p_status = st.selectbox("Status", ["ACTIVE", "PLANNING", "COMPLETED", "HOLD"])
            
            # ✅ TOMBOL SIMPAN DENGAN NOTIFIKASI JELAS
            if st.form_submit_button("💾 Simpan Proyek", type="primary", use_container_width=True):
                if not p_code or not p_name:
                    st.error("❌ Kode & Nama Proyek wajib diisi!")
                else:
                    try:
                        insert_row("master_projects", {
                            'id': generate_id(), 'project_code': p_code, 'project_name': p_name,
                            'category': p_cat, 'status': p_status,
                            'start_date': today_str(), 'end_date': today_str()
                        })
                        # ✅ NOTIFIKASI GANDA AGAR PASTI TERLIHAT
                        st.toast("✅ Master Project berhasil disimpan!", icon="🎉")
                        st.success(f"✅ Proyek **{p_name}** ditambahkan ke database!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal menyimpan: {str(e)}")
                        st.info("💡 Pastikan tabel `master_projects` sudah dibuat di Supabase.")

        st.divider()
        st.markdown("**Daftar Master Project:**")
        if not master_df.empty:
            st.dataframe(master_df[['project_code', 'project_name', 'category', 'status']], use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada master project. Silakan tambah di form atas.")

    # ─────────────────────────────────────────────────────────────
    # TAB 3: TAMBAH SITE (LINK KE MASTER PROJECT)
    # ─────────────────────────────────────────────────────────────
    with tab3:
        st.subheader("➕ Tambah Site Baru")
        
        with st.form("add_site"):
            c1, c2 = st.columns(2)
            with c1:
                # ✅ PILIH MASTER PROJECT SAAT TAMBAH SITE
                master_pid = st.selectbox("🔗 Pilih Master Project", project_options, 
                                          format_func=lambda x: "🌍 SEMUA PROYEK" if x == "ALL" 
                                          else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}")
                site_id = st.text_input("Site ID", placeholder="SITE-001")
                site_name = st.text_input("Site Name", placeholder="Tower Gambir")
                site_coordinate = st.text_input("Koordinat", placeholder="-6.1754, 106.8272")
                
            with c2:
                vendor = st.text_input("Vendor")
                pm = st.text_input("PM")
                c3, c4 = st.columns(2)
                with c3: start_date = st.date_input("Plan Start")
                with c4: end_date = st.date_input("Plan End")
            
            if st.form_submit_button("💾 Simpan Site", type="primary", use_container_width=True):
                if not site_name or not site_id:
                    st.error("❌ Site ID dan Site Name wajib diisi!")
                elif master_pid == "ALL":
                    st.error("❌ Pilih Master Project terlebih dahulu!")
                else:
                    try:
                        insert_row("projects", {
                            'id': generate_id(), 'master_project_id': master_pid,
                            'site_id': site_id, 'site_name': site_name,
                            'site_coordinate': site_coordinate, 'vendor': vendor, 'pm': pm,
                            'start_date': start_date.strftime('%Y-%m-%d'),
                            'end_date': end_date.strftime('%Y-%m-%d'),
                            'status': 'ON_TRACK', 'progress': '0'
                        })
                        st.toast("✅ Site berhasil ditambahkan!", icon="📍")
                        st.success(f"✅ Site {site_name} tersimpan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal simpan: {str(e)}")

    # ─────────────────────────────────────────────────────────────
    # TAB 4: EDIT SITE
    # ─────────────────────────────────────────────────────────────
    with tab4:
        st.subheader("✏️ Edit Data Site")
        df = read_sheet("projects")
        if not df.empty:
            # Filter dropdown edit berdasarkan proyek yang aktif
            if st.session_state.project_filter != "ALL":
                df = df[df['master_project_id'] == st.session_state.project_filter]
                
            selected = st.selectbox("Pilih Site:", df['id'].tolist(),
                                   format_func=lambda x: f"{df[df['id']==x]['site_id'].values[0]} - {df[df['id']==x]['site_name'].values[0]}")
            if selected:
                site = df[df['id']==selected].iloc[0]
                ridx = find_row_by_id("projects", selected)
                
                with st.form("edit_site"):
                    new_status = st.selectbox("Status", ["ON_TRACK", "DELAYED", "CRITICAL"],
                                             index=["ON_TRACK", "DELAYED", "CRITICAL"].index(site.get('status','ON_TRACK')) if site.get('status') in ["ON_TRACK", "DELAYED", "CRITICAL"] else 0)
                    new_progress = st.slider("Progress (%)", 0, 100, int(float(site.get('progress',0))) if site.get('progress') else 0)
                    
                    if st.form_submit_button("💾 Update Data", type="primary", use_container_width=True):
                        update_row("projects", ridx, {'status': new_status, 'progress': str(new_progress)})
                        st.toast("✅ Site berhasil diupdate!", icon="✏️")
                        st.success("✅ Data tersimpan!")
                        st.rerun()

    # ─────────────────────────────────────────────────────────────
    # TAB 5: IMPORT CSV
    # ─────────────────────────────────────────────────────────────
    with tab5:
        st.subheader("📥 Import Site via CSV")
        st.info("ℹ️ Gunakan template di bawah. Pastikan kolom `master_project_id` diisi.")
        template = pd.DataFrame({
            'master_project_id': ['ID_PROYEK'], 'site_id': ['SITE-001'], 'site_name': ['Tower A'],
            'vendor': ['PT. X'], 'pm': ['Budi'], 'start_date': [today_str()], 'end_date': [today_str()]
        })
        st.download_button("📥 Template", template.to_csv(index=False), "template.csv", "text/csv")
        
        up = st.file_uploader("Upload CSV", type=['csv'], key="site_csv")
        if up:
            idf = pd.read_csv(up)
            st.dataframe(idf.head())
            if st.button("🚀 Import", type="primary", use_container_width=True):
                count = 0
                for _, r in idf.iterrows():
                    try:
                        insert_row("projects", {
                            'id': generate_id(), 'master_project_id': str(r.get('master_project_id','')),
                            'site_id': str(r.get('site_id','')), 'site_name': str(r.get('site_name','')),
                            'vendor': str(r.get('vendor','')), 'pm': str(r.get('pm','')),
                            'start_date': str(r.get('start_date', today_str())),
                            'end_date': str(r.get('end_date', today_str())),
                            'status': 'ON_TRACK', 'progress': '0'
                        })
                        count += 1
                    except: pass
                st.toast(f"✅ {count} site berhasil diimport!", icon="📦")
                st.success("Import selesai!")
                st.rerun()

if __name__ == "__main__":
    project_tracker_page()
