import streamlit as st
import pandas as pd
from supabase_db import read_sheet, insert_row, update_row, find_row_by_id, generate_id, today_str

def sync_progress_from_milestones(site_id):
    """Hitung progress dari milestones"""
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
    
    if 'project_filter' not in st.session_state:
        st.session_state.project_filter = "ALL"

    # Load Master Projects (Aman jika tabel belum ada)
    try:
        master_df = read_sheet("master_projects")
        master_options = ["ALL"] + master_df["id"].tolist() if not master_df.empty else ["ALL"]
    except Exception:
        master_df = pd.DataFrame()
        master_options = ["ALL"]

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Daftar Site", "🏢 Master Project", "➕ Tambah Site", "✏️ Edit Site", "📥 Import CSV"
    ])

    # ─────────────────────────────────────────────────────────────
    # TAB 1: DAFTAR SITE + FILTER MASTER PROJECT + EXCEL STYLE
    # ─────────────────────────────────────────────────────────────
    with tab1:
        st.subheader("Daftar Site")
        df = read_sheet("projects")
        
        if not df.empty:
            df['progress'] = pd.to_numeric(df['progress'], errors='coerce').fillna(0)
            
            # 1️⃣ FILTER MASTER PROJECT (GLOBAL)
            st.markdown("### 🌍 Filter Master Project")
            selected_proj = st.selectbox(
                "Pilih Proyek:",
                master_options,
                format_func=lambda x: "🌐 SEMUA PROYEK" if x == "ALL" 
                else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}",
                key="global_proj_filter"
            )
            if selected_proj != st.session_state.project_filter:
                st.session_state.project_filter = selected_proj
                st.rerun()

            # Apply Global Filter
            if st.session_state.project_filter != "ALL" and 'master_project_id' in df.columns:
                df = df[df['master_project_id'] == st.session_state.project_filter]
            
            # 2️⃣ FILTER EXCEL-STYLE (DIKEMBALIKAN UTUH)
            with st.expander("🔍 Filter Lanjutan (Excel Style)", expanded=True):
                st.markdown("Pilih kriteria untuk menyaring tabel di bawah:")
                f_c1, f_c2, f_c3 = st.columns(3)
                
                with f_c1:
                    cats = sorted(df['site_category'].dropna().unique().tolist()) if 'site_category' in df.columns else []
                    sel_cats = st.multiselect("🏷️ Kategori", options=cats, default=cats)
                    
                    types = sorted(df['site_type'].dropna().unique().tolist()) if 'site_type' in df.columns else []
                    sel_types = st.multiselect("📐 Tipe Site", options=types, default=types)
                    
                with f_c2:
                    vendors = sorted(df['vendor'].dropna().unique().tolist()) if 'vendor' in df.columns else []
                    sel_vendors = st.multiselect("🏢 Vendor", options=vendors, default=vendors)
                    
                    pms = sorted(df['pm'].dropna().unique().tolist()) if 'pm' in df.columns else []
                    sel_pms = st.multiselect("👤 PM", options=pms, default=pms)
                    
                with f_c3:
                    statuses = ["ON_TRACK", "DELAYED", "CRITICAL"]
                    sel_status = st.multiselect("🚦 Status", options=statuses, default=statuses)
                    
                    if st.button("🔄 Reset Filter", use_container_width=True):
                        st.rerun()

            # Apply Excel Filters
            filtered_df = df.copy()
            if 'site_category' in df.columns: filtered_df = filtered_df[filtered_df['site_category'].isin(sel_cats)]
            if 'site_type' in df.columns: filtered_df = filtered_df[filtered_df['site_type'].isin(sel_types)]
            if 'vendor' in df.columns: filtered_df = filtered_df[filtered_df['vendor'].isin(sel_vendors)]
            if 'pm' in df.columns: filtered_df = filtered_df[filtered_df['pm'].isin(sel_pms)]
            if 'status' in df.columns: filtered_df = filtered_df[filtered_df['status'].isin(sel_status)]

            # Tampilkan Tabel
            def color_status(val):
                if val == 'ON_TRACK': return 'background-color: #d4edda; font-weight: bold'
                elif val == 'DELAYED': return 'background-color: #fff3cd; font-weight: bold'
                elif val == 'CRITICAL': return 'background-color: #f8d7da; font-weight: bold'
                return ''
            
            display_cols = ['site_id', 'site_name', 'site_category', 'site_type', 'vendor', 'pm', 'tower_height', 'site_coordinate', 'status', 'progress']
            display_df = filtered_df[[c for c in display_cols if c in filtered_df.columns]]
            st.dataframe(display_df.style.map(color_status, subset=['status']), use_container_width=True, hide_index=True)
            
            # Metrics
            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Site", len(filtered_df))
            col2.metric("On Track", len(filtered_df[filtered_df['status']=='ON_TRACK']) if 'status' in filtered_df.columns else 0)
            col3.metric("Terlambat", len(filtered_df[filtered_df['status'].isin(['DELAYED','CRITICAL'])]) if 'status' in filtered_df.columns else 0)
            
            if st.button("🔄 Sync Progress dari Milestones", use_container_width=True):
                for _, row in filtered_df.iterrows():
                    prog, sts = sync_progress_from_milestones(row['id'])
                    ridx = find_row_by_id("projects", row['id'])
                    if ridx: update_row("projects", ridx, {'progress': str(prog), 'status': sts})
                st.cache_data.clear()
                st.success("✅ Progress di-sync!")
                st.rerun()
        else:
            st.info("📋 Belum ada site.")

    # ─────────────────────────────────────────────────────────────
    # TAB 2: MASTER PROJECT MANAGEMENT
    # ─────────────────────────────────────────────────────────────
    with tab2:
        st.subheader("🏢 Kelola Master Project")
        with st.form("add_master_project"):
            c1, c2 = st.columns(2)
            with c1:
                p_code = st.text_input("Kode Proyek", placeholder="PROJ-4G-2026")
                p_name = st.text_input("Nama Proyek", placeholder="Rollout Phase 1")
            with c2:
                p_cat = st.selectbox("Kategori", ["4G Rollout", "5G Upgrade", "Fiber Optic", "General"])
                p_stat = st.selectbox("Status", ["ACTIVE", "PLANNING", "COMPLETED", "HOLD"])
            
            if st.form_submit_button("💾 Simpan Proyek", type="primary", use_container_width=True):
                if p_code and p_name:
                    insert_row("master_projects", {
                        'id': generate_id(), 'project_code': p_code, 'project_name': p_name,
                        'category': p_cat, 'status': p_stat,
                        'start_date': today_str(), 'end_date': today_str()
                    })
                    st.toast("✅ Master Project berhasil disimpan!", icon="🏢")
                    st.rerun()
                else:
                    st.error("❌ Kode & Nama Proyek wajib diisi!")

        st.divider()
        st.markdown("**Daftar Master Project:**")
        if not master_df.empty:
            st.dataframe(master_df[['project_code', 'project_name', 'category', 'status']], use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────
    # TAB 3: TAMBAH SITE
    # ─────────────────────────────────────────────────────────────
    with tab3:
        st.subheader("➕ Tambah Site Baru")
        with st.form("add_site"):
            c1, c2 = st.columns(2)
            with c1:
                m_pid = st.selectbox("🔗 Pilih Master Project", master_options[1:] if len(master_options)>1 else ["Belum ada proyek"], 
                                     format_func=lambda x: f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}" if x and not master_df.empty else x)
                s_id = st.text_input("Site ID", placeholder="SITE-001")
                s_name = st.text_input("Site Name", placeholder="Tower Gambir")
                s_cat = st.selectbox("Kategori Site", ["New Site", "Collocation", "Upgrade", "Relocation"])
                s_type = st.selectbox("Tipe Site", ["SST", "MP", "Light Pole", "Rooftop", "Indoor"])
            with c2:
                s_coord = st.text_input("Koordinat", placeholder="-6.1754, 106.8272")
                vend = st.text_input("Vendor")
                pm_val = st.text_input("PM")
                h_val = st.number_input("Ketinggian Tower (m)", 0.0, 120.0, 45.0)
                c3, c4 = st.columns(2)
                with c3: start_d = st.date_input("Plan Start")
                with c4: end_d = st.date_input("Plan End")
            
            if st.form_submit_button("💾 Simpan Site", type="primary", use_container_width=True):
                if s_name and s_id and m_pid != "Belum ada proyek":
                    try:
                        insert_row("projects", {
                            'id': generate_id(), 'master_project_id': m_pid,
                            'site_id': s_id, 'site_name': s_name,
                            'site_category': s_cat, 'site_type': s_type,
                            'site_coordinate': s_coord, 'vendor': vend, 'pm': pm_val,
                            'tower_height': str(h_val),
                            'start_date': start_d.strftime('%Y-%m-%d'), 'end_date': end_d.strftime('%Y-%m-%d'),
                            'status': 'ON_TRACK', 'progress': '0'
                        })
                        st.toast("✅ Site berhasil ditambahkan!", icon="📍")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal simpan: {str(e)}")
                else:
                    st.error("❌ Lengkapi Site ID, Name, dan pilih Master Project!")

    # ─────────────────────────────────────────────────────────────
    # TAB 4: EDIT SITE (LENGKAP DENGAN SEMUA KOLOM YANG DIMINTA)
    # ─────────────────────────────────────────────────────────────
    with tab4:
        st.subheader("✏️ Edit Data Site")
        df = read_sheet("projects")
        if not df.empty:
            if st.session_state.project_filter != "ALL":
                df = df[df['master_project_id'] == st.session_state.project_filter]
                
            sel_id = st.selectbox("Pilih Site untuk Edit:", df['id'].tolist(),
                                  format_func=lambda x: f"{df[df['id']==x]['site_id'].values[0]} - {df[df['id']==x]['site_name'].values[0]}")
            if sel_id:
                site = df[df['id']==sel_id].iloc[0]
                ridx = find_row_by_id("projects", sel_id)
                
                with st.form("edit_site"):
                    st.markdown("#### 📊 Status & Progress")
                    c1, c2 = st.columns(2)
                    with c1:
                        n_stat = st.selectbox("Status", ["ON_TRACK", "DELAYED", "CRITICAL"],
                                             index=["ON_TRACK", "DELAYED", "CRITICAL"].index(site.get('status','ON_TRACK')))
                        n_prog = st.slider("Progress (%)", 0, 100, int(float(site.get('progress',0))) if site.get('progress') else 0)
                    with c2:
                        n_cat = st.selectbox("Kategori", ["New Site", "Collocation", "Upgrade", "Relocation"], 
                                            index=["New Site", "Collocation", "Upgrade", "Relocation"].index(site.get('site_category','New Site')))
                        n_type = st.selectbox("Tipe Site", ["SST", "MP", "Light Pole", "Rooftop", "Indoor"], 
                                             index=["SST", "MP", "Light Pole", "Rooftop", "Indoor"].index(site.get('site_type','SST')))

                    st.markdown("#### 🏗️ Detail Proyek & Lokasi")
                    c3, c4 = st.columns(2)
                    with c3:
                        safe_mpid = site.get('master_project_id')
                        m_idx = master_options.index(safe_mpid) if safe_mpid in master_options else 0
                        n_mpid = st.selectbox("Master Project", master_options, index=m_idx,
                                              format_func=lambda x: "🌐 SEMUA" if x=="ALL" 
                                              else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}")
                        n_vend = st.text_input("Vendor", value=site.get('vendor',''))
                        n_pm = st.text_input("PM", value=site.get('pm',''))
                    with c4:
                        try: n_h = float(site.get('tower_height', 45))
                        except: n_h = 45.0
                        n_h_val = st.number_input("Ketinggian (m)", value=n_h)
                        n_coord = st.text_input("Koordinat", value=site.get('site_coordinate',''))

                    st.markdown("#### 📅 Timeline")
                    c5, c6 = st.columns(2)
                    with c5:
                        try: s_def = pd.to_datetime(site.get('start_date')).date()
                        except: s_def = None
                        n_start = st.date_input("Plan Start", value=s_def)
                    with c6:
                        try: e_def = pd.to_datetime(site.get('end_date')).date()
                        except: e_def = None
                        n_end = st.date_input("Plan End", value=e_def)

                    if st.form_submit_button("💾 Update Data", type="primary", use_container_width=True):
                        update_row("projects", ridx, {
                            'status': n_stat, 'progress': str(n_prog),
                            'site_category': n_cat, 'site_type': n_type,
                            'master_project_id': n_mpid, 'vendor': n_vend, 'pm': n_pm,
                            'tower_height': str(n_h_val), 'site_coordinate': n_coord,
                            'start_date': n_start.strftime('%Y-%m-%d'), 'end_date': n_end.strftime('%Y-%m-%d')
                        })
                        st.toast("✅ Data berhasil diupdate!", icon="✏️")
                        st.rerun()
        else:
            st.info("Belum ada data site.")

    # ─────────────────────────────────────────────────────────────
    # TAB 5: IMPORT CSV
    # ─────────────────────────────────────────────────────────────
    with tab5:
        st.subheader("📥 Import Site via CSV")
        st.info("ℹ️ Kolom wajib: `master_project_id`, `site_id`, `site_name`")
        template = pd.DataFrame({
            'master_project_id': ['ID_PROYEK'], 'site_id': ['SITE-001'], 'site_name': ['Tower A'],
            'site_category': ['New Site'], 'site_type': ['SST'], 'vendor': ['PT. X'], 'pm': ['Budi'],
            'tower_height': [45], 'site_coordinate': ['-6.17,106.82'], 'start_date': [today_str()], 'end_date': [today_str()]
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
                            'site_category': str(r.get('site_category','New Site')), 'site_type': str(r.get('site_type','SST')),
                            'vendor': str(r.get('vendor','')), 'pm': str(r.get('pm','')),
                            'tower_height': str(r.get('tower_height', 45)), 'site_coordinate': str(r.get('site_coordinate','')),
                            'start_date': str(r.get('start_date', today_str())), 'end_date': str(r.get('end_date', today_str())),
                            'status': 'ON_TRACK', 'progress': '0'
                        })
                        count += 1
                    except: pass
                st.toast(f"✅ {count} site berhasil diimport!", icon="📦")
                st.rerun()

if __name__ == "__main__":
    project_tracker_page()
