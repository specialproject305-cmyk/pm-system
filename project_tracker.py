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
    
    # Pastikan session state filter ada
    if 'master_project_filter' not in st.session_state:
        st.session_state.master_project_filter = "ALL"

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Daftar Site", "🏢 Master Project", "➕ Tambah Site", "✏️ Edit Site", "📥 Import CSV"
    ])

    # ─────────────────────────────────────────────────────────────
    # TAB 1: DAFTAR SITE (DENGAN FILTER EXCEL STYLE)
    # ─────────────────────────────────────────────────────────────
    with tab1:
        st.subheader("Daftar Site")
        
        # 1. Load Data
        df = read_sheet("projects")
        
        if not df.empty:
            df['progress'] = pd.to_numeric(df['progress'], errors='coerce').fillna(0)
            
            # 2. Apply Global Master Project Filter (Dari Sidebar)
            if st.session_state.master_project_filter != "ALL" and 'master_project_id' in df.columns:
                df = df[df['master_project_id'] == st.session_state.master_project_filter]
            
            # 3. EXCEL-LIKE FILTERS (Panel Filter Lanjutan)
            with st.expander("🔍 Filter Lanjutan (Excel Style)", expanded=False):
                st.markdown("Pilih kriteria untuk menyaring data tabel di bawah:")
                f_col1, f_col2, f_col3 = st.columns(3)
                
                with f_col1:
                    # Filter Kategori
                    cats = sorted(df['site_category'].dropna().unique().tolist()) if 'site_category' in df.columns else []
                    selected_cats = st.multiselect("🏷️ Kategori", options=cats, default=cats)
                    
                    # Filter Tipe
                    types = sorted(df['site_type'].dropna().unique().tolist()) if 'site_type' in df.columns else []
                    selected_types = st.multiselect(" Tipe Site", options=types, default=types)

                with f_col2:
                    # Filter Vendor
                    vendors = sorted(df['vendor'].dropna().unique().tolist()) if 'vendor' in df.columns else []
                    selected_vendors = st.multiselect("🏢 Vendor", options=vendors, default=vendors)

                    # Filter PM
                    pms = sorted(df['pm'].dropna().unique().tolist()) if 'pm' in df.columns else []
                    selected_pms = st.multiselect("👤 PM", options=pms, default=pms)

                with f_col3:
                    # Filter Status
                    statuses = ["ON_TRACK", "DELAYED", "CRITICAL"]
                    selected_status = st.multiselect("🚦 Status", options=statuses, default=statuses)

                    # Tombol Reset
                    if st.button("🔄 Reset Filter", use_container_width=True):
                        st.rerun()

            # 4. Apply Logic Filter
            filtered_df = df.copy()
            if 'site_category' in df.columns: filtered_df = filtered_df[filtered_df['site_category'].isin(selected_cats)]
            if 'site_type' in df.columns: filtered_df = filtered_df[filtered_df['site_type'].isin(selected_types)]
            if 'vendor' in df.columns: filtered_df = filtered_df[filtered_df['vendor'].isin(selected_vendors)]
            if 'pm' in df.columns: filtered_df = filtered_df[filtered_df['pm'].isin(selected_pms)]
            if 'status' in df.columns: filtered_df = filtered_df[filtered_df['status'].isin(selected_status)]

            # 5. Tampilkan Tabel (Bisa di-sort klik header)
            def color_status(val):
                if val == 'ON_TRACK': return 'background-color: #d4edda; font-weight: bold'
                elif val == 'DELAYED': return 'background-color: #fff3cd; font-weight: bold'
                elif val == 'CRITICAL': return 'background-color: #f8d7da; font-weight: bold'
                return ''
            
            display_cols = ['site_id', 'site_name', 'site_category', 'site_type', 'vendor', 'pm', 'tower_height', 'status', 'progress']
            display_df = filtered_df[[c for c in display_cols if c in filtered_df.columns]]
            
            # Styling
            styled_df = display_df.style.map(color_status, subset=['status']) if 'status' in display_df.columns else display_df
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Metrics
            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Site (Filtered)", len(filtered_df))
            col2.metric("On Track", len(filtered_df[filtered_df['status']=='ON_TRACK']) if 'status' in filtered_df.columns else 0)
            col3.metric("Terlambat", len(filtered_df[filtered_df['status'].isin(['DELAYED','CRITICAL'])]) if 'status' in filtered_df.columns else 0)
            
            # Sync Button
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
    # TAB 2: MASTER PROJECT
    # ─────────────────────────────────────────────────────────────
    with tab2:
        st.subheader("🏢 Kelola Master Project")
        master_df = read_sheet("master_projects")
        
        with st.form("add_master_project"):
            c1, c2 = st.columns(2)
            with c1:
                p_code = st.text_input("Kode Proyek", placeholder="PROJ-4G-2026")
                p_name = st.text_input("Nama Proyek", placeholder="Rollout 4G Phase 1")
            with c2:
                p_cat = st.selectbox("Kategori Proyek", ["4G Rollout", "5G Upgrade", "Fiber Optic", "General"])
                p_status = st.selectbox("Status Proyek", ["ACTIVE", "PLANNING", "COMPLETED", "HOLD"])
            
            if st.form_submit_button("💾 Simpan Proyek", type="primary", use_container_width=True):
                if p_code and p_name:
                    insert_row("master_projects", {
                        'id': generate_id(), 'project_code': p_code, 'project_name': p_name,
                        'category': p_cat, 'status': p_status,
                        'start_date': today_str(), 'end_date': today_str()
                    })
                    st.success("✅ Master Project ditambahkan!")
                    st.rerun()

        st.divider()
        st.markdown("**Daftar Master Project Aktif:**")
        if not master_df.empty:
            st.dataframe(master_df[['project_code', 'project_name', 'category', 'status']], use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────
    # TAB 3: TAMBAH SITE
    # ─────────────────────────────────────────────────────────────
    with tab3:
        st.subheader("➕ Tambah Site Baru")
        
        master_df = read_sheet("master_projects")
        master_options = [""] + master_df["id"].tolist() if not master_df.empty else [""]
        
        with st.form("add_site"):
            c1, c2 = st.columns(2)
            with c1:
                master_pid = st.selectbox("🔗 Pilih Master Project", master_options, 
                                          format_func=lambda x: f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}" if x and not master_df.empty else "Tidak ada proyek")
                site_id = st.text_input("Site ID", placeholder="SITE-001")
                site_name = st.text_input("Site Name", placeholder="Tower Gambir")
                site_category = st.selectbox("Kategori Site", ["New Site", "Collocation", "Upgrade", "Relocation"])
                site_type = st.selectbox("Tipe Site", ["SST", "MP", "Light Pole", "Rooftop", "Indoor"])
                
            with c2:
                tower_height = st.number_input("Ketinggian Tower (m)", 0.0, 120.0, 45.0)
                vendor = st.text_input("Vendor")
                pm = st.text_input("PM")
                lat = st.text_input("Latitude", placeholder="-6.1754")
                lon = st.text_input("Longitude", placeholder="106.8272")
                
            c3, c4 = st.columns(2)
            with c3: start_date = st.date_input("Plan Start")
            with c4: end_date = st.date_input("Plan End")
            
            if st.form_submit_button("💾 Simpan Site", type="primary", use_container_width=True):
                if not site_name or not site_id or not master_pid:
                    st.error("❌ Master Project, Site ID & Name wajib diisi!")
                else:
                    try:
                        insert_row("projects", {
                            'id': generate_id(), 'master_project_id': master_pid,
                            'site_id': site_id, 'site_name': site_name,
                            'site_category': site_category, 'site_type': site_type,
                            'tower_height': str(tower_height), 'latitude': lat, 'longitude': lon,
                            'vendor': vendor, 'pm': pm,
                            'start_date': start_date.strftime('%Y-%m-%d'), 'end_date': end_date.strftime('%Y-%m-%d'),
                            'status': 'ON_TRACK', 'progress': '0'
                        })
                        st.success(f"✅ Site {site_name} berhasil ditambahkan!")
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
            # Filter dropdown berdasarkan Master Project yang aktif
            if st.session_state.master_project_filter != "ALL":
                df = df[df['master_project_id'] == st.session_state.master_project_filter]

            selected = st.selectbox("Pilih Site untuk Edit:", df['id'].tolist(),
                                   format_func=lambda x: f"{df[df['id']==x]['site_id'].values[0]} - {df[df['id']==x]['site_name'].values[0]}")
            if selected:
                site = df[df['id']==selected].iloc[0]
                ridx = find_row_by_id("projects", selected)
                
                with st.form("edit_site"):
                    new_status = st.selectbox("Status", ["ON_TRACK", "DELAYED", "CRITICAL"],
                                             index=["ON_TRACK", "DELAYED", "CRITICAL"].index(site.get('status','ON_TRACK')) if site.get('status') in ["ON_TRACK", "DELAYED", "CRITICAL"] else 0)
                    new_progress = st.slider("Progress (%)", 0, 100, int(float(site.get('progress',0))) if site.get('progress') else 0)
                    new_cat = st.selectbox("Kategori", ["New Site", "Collocation", "Upgrade", "Relocation"], index=["New Site", "Collocation", "Upgrade", "Relocation"].index(site.get('site_category','New Site')))
                    new_type = st.selectbox("Tipe", ["SST", "MP", "Light Pole", "Rooftop", "Indoor"], index=["SST", "MP", "Light Pole", "Rooftop", "Indoor"].index(site.get('site_type','SST')))
                    
                    try:
                        h_val = site.get('tower_height')
                        new_height_val = float(h_val) if pd.notna(h_val) and str(h_val).strip() not in ['', 'None', 'nan'] else 45.0
                    except (ValueError, TypeError):
                        new_height_val = 45.0
                    new_height = st.number_input("Ketinggian (m)", value=new_height_val)
                    
                    if st.form_submit_button("💾 Update Data", type="primary", use_container_width=True):
                        update_row("projects", ridx, {
                            'status': new_status, 'progress': str(new_progress),
                            'site_category': new_cat, 'site_type': new_type,
                            'tower_height': str(new_height)
                        })
                        st.success("✅ Site berhasil diupdate!")
                        st.rerun()

    # ─────────────────────────────────────────────────────────────
    # TAB 5: IMPORT CSV
    # ─────────────────────────────────────────────────────────────
    with tab5:
        st.subheader("📥 Import Site via CSV")
        st.info("ℹ️ Gunakan template di bawah.")
        template = pd.DataFrame({
            'master_project_id': ['ID_PROYEK'], 'site_id': ['SITE-001'], 'site_name': ['Tower A'],
            'site_category': ['New Site'], 'site_type': ['SST'], 'tower_height': [45],
            'vendor': ['PT. X'], 'pm': ['Budi']
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
                            'tower_height': str(r.get('tower_height', 45)), 'vendor': str(r.get('vendor','')), 'pm': str(r.get('pm','')),
                            'status': 'ON_TRACK', 'progress': '0'
                        })
                        count += 1
                    except: pass
                st.success(f"✅ {count} site berhasil diimport!")
                st.rerun()

if __name__ == "__main__":
    project_tracker_page()
