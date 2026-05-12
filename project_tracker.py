import streamlit as st
import pandas as pd
from supabase_db import read_sheet, insert_row, update_row, find_row_by_id, generate_id, today_str, delete_row_by_id

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
    # ─────────────────────────────────────────────────────────────
    # 📱 MOBILE & UI CSS
    # ─────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .stColumn { width: 100% !important; margin-bottom: 10px; }
        button, input, select, textarea { min-height: 44px !important; font-size: 16px !important; }
        .stTabs [data-baseweb="tab"] { height: 40px; white-space: pre-wrap; }
        .delete-section { border: 2px solid #dc3545; border-radius: 10px; padding: 15px; margin-top: 15px; background: #fff5f5; }
    }
    .delete-section { border: 2px solid #dc3545; border-radius: 10px; padding: 15px; margin-top: 15px; background: #fff5f5; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📁 Site & Project Portfolio")
    
    if 'project_filter' not in st.session_state:
        st.session_state.project_filter = "ALL"

    # Load Master Projects
    try:
        master_df = read_sheet("master_projects")
        master_options = ["ALL"] + master_df["id"].tolist() if not master_df.empty else ["ALL"]
    except:
        master_df = pd.DataFrame()
        master_options = ["ALL"]

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Daftar Site", "🏢 Master Project", "➕ Tambah Site", "📥 Import CSV"
    ])

    # ═══════════════════════════════════════════════════════════════════
    # TAB 1: DAFTAR SITE + FILTER + QUICK EDIT/DELETE (Pengganti Tab Edit)
    # ═══════════════════════════════════════════════════════════════════
    with tab1:
        st.subheader("Daftar Site")
        df = read_sheet("projects")
        
        if not df.empty:
            df['progress'] = pd.to_numeric(df['progress'], errors='coerce').fillna(0)
            
            # 1. Filter Master Project (Global)
            st.markdown("### 🌍 Filter Master Project")
            selected_proj = st.selectbox(
                "Pilih Proyek:", master_options,
                format_func=lambda x: "🌐 SEMUA PROYEK" if x == "ALL" 
                else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}",
                key="global_proj_filter"
            )
            if selected_proj != st.session_state.project_filter:
                st.session_state.project_filter = selected_proj
                st.rerun()

            if st.session_state.project_filter != "ALL" and 'master_project_id' in df.columns:
                df = df[df['master_project_id'] == st.session_state.project_filter]
            
            # 2. Filter Excel-Style
            with st.expander("🔍 Filter Lanjutan (Excel Style)", expanded=True):
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
                    if st.button("🔄 Reset Filter", use_container_width=True): st.rerun()

            filtered_df = df.copy()
            if 'site_category' in df.columns: filtered_df = filtered_df[filtered_df['site_category'].isin(sel_cats)]
            if 'site_type' in df.columns: filtered_df = filtered_df[filtered_df['site_type'].isin(sel_types)]
            if 'vendor' in df.columns: filtered_df = filtered_df[filtered_df['vendor'].isin(sel_vendors)]
            if 'pm' in df.columns: filtered_df = filtered_df[filtered_df['pm'].isin(sel_pms)]
            if 'status' in df.columns: filtered_df = filtered_df[filtered_df['status'].isin(sel_status)]

            def color_status(val):
                if val == 'ON_TRACK': return 'background-color: #d4edda; font-weight: bold'
                elif val == 'DELAYED': return 'background-color: #fff3cd; font-weight: bold'
                elif val == 'CRITICAL': return 'background-color: #f8d7da; font-weight: bold'
                return ''
            
            display_cols = ['site_id', 'site_name', 'site_category', 'site_type', 'vendor', 'pm', 'tower_height', 'site_coordinate', 'status', 'progress']
            display_df = filtered_df[[c for c in display_cols if c in filtered_df.columns]]
            st.dataframe(display_df.style.map(color_status, subset=['status']), use_container_width=True, hide_index=True)
            
            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Site", len(filtered_df))
            col2.metric("On Track", len(filtered_df[filtered_df['status']=='ON_TRACK']) if 'status' in filtered_df.columns else 0)
            col3.metric("Terlambat", len(filtered_df[filtered_df['status'].isin(['DELAYED','CRITICAL'])]) if 'status' in filtered_df.columns else 0)
            
            # 3. QUICK EDIT & DELETE SECTION (Menggantikan Tab Edit)
            st.markdown("### ⚙️ Kelola Site Terpilih")
            st.info("💡 Pilih site dari dropdown di bawah untuk langsung Edit atau Hapus.")
            
            sel_edit_id = st.selectbox(
                "🔍 Pilih Site:", 
                filtered_df['id'].tolist(),
                format_func=lambda x: f"{filtered_df[filtered_df['id']==x]['site_id'].values[0]} - {filtered_df[filtered_df['id']==x]['site_name'].values[0]}",
                key="quick_edit_selector"
            )
            
            if sel_edit_id:
                site = filtered_df[filtered_df['id']==sel_edit_id].iloc[0]
                ridx = find_row_by_id("projects", sel_edit_id)
                
                # FORM EDIT
                with st.form("quick_edit_form"):
                    st.markdown("#### 📝 Edit Data Site")
                    c1, c2 = st.columns(2)
                    with c1:
                        n_stat = st.selectbox("Status", ["ON_TRACK", "DELAYED", "CRITICAL"], index=["ON_TRACK", "DELAYED", "CRITICAL"].index(site.get('status','ON_TRACK')))
                        n_prog = st.slider("Progress (%)", 0, 100, int(float(site.get('progress',0))) if site.get('progress') else 0)
                        n_cat = st.selectbox("Kategori", ["New Site", "Collocation", "Upgrade", "Relocation"], index=["New Site", "Collocation", "Upgrade", "Relocation"].index(site.get('site_category','New Site')))
                        n_type = st.selectbox("Tipe", ["SST", "MP", "Light Pole", "Rooftop", "Indoor"], index=["SST", "MP", "Light Pole", "Rooftop", "Indoor"].index(site.get('site_type','SST')))
                    with c2:
                        try: n_h = float(site.get('tower_height', 45))
                        except: n_h = 45.0
                        n_h_val = st.number_input("Ketinggian (m)", value=n_h)
                        n_coord = st.text_input("Koordinat", value=site.get('site_coordinate',''))
                        n_vend = st.text_input("Vendor", value=site.get('vendor',''))
                        n_pm = st.text_input("PM", value=site.get('pm',''))
                    
                    c3, c4 = st.columns(2)
                    with c3:
                        try: s_def = pd.to_datetime(site.get('start_date')).date()
                        except: s_def = None
                        n_start = st.date_input("Plan Start", value=s_def)
                        n_mpid = st.selectbox("Master Project", master_options, index=master_options.index(site.get('master_project_id')) if site.get('master_project_id') in master_options else 0,
                                              format_func=lambda x: "🌐 SEMUA" if x=="ALL" else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}")
                    with c4:
                        try: e_def = pd.to_datetime(site.get('end_date')).date()
                        except: e_def = None
                        n_end = st.date_input("Plan End", value=e_def)

                    if st.form_submit_button("💾 Update Data", type="primary", use_container_width=True):
                        update_row("projects", ridx, {
                            'status': n_stat, 'progress': str(n_prog), 'site_category': n_cat, 'site_type': n_type,
                            'master_project_id': n_mpid, 'vendor': n_vend, 'pm': n_pm,
                            'tower_height': str(n_h_val), 'site_coordinate': n_coord,
                            'start_date': n_start.strftime('%Y-%m-%d'), 'end_date': n_end.strftime('%Y-%m-%d')
                        })
                        st.toast("✅ Data berhasil diupdate!", icon="✏️")
                        st.rerun()

                # FORM HAPUS (CASCADE)
                st.markdown("---")
                st.markdown('<div class="delete-section">', unsafe_allow_html=True)
                st.markdown("#### 🗑️ Hapus Site Permanen")
                st.warning("⚠️ Tindakan ini **tidak dapat dibatalkan**. Semua milestone, chat, & transaksi terkait akan ikut terhapus.")
                
                # Hitung dampak
                ms_df = read_sheet("milestones")
                chat_df = read_sheet("chat_messages")
                inv_df = read_sheet("inventory_transactions")
                ms_c = len(ms_df[ms_df['project_id']==sel_edit_id]) if not ms_df.empty else 0
                chat_c = len(chat_df[chat_df['site_id']==sel_edit_id]) if not chat_df.empty else 0
                inv_c = len(inv_df[inv_df['project_id']==sel_edit_id]) if not inv_df.empty else 0
                
                st.markdown(f"**Data yang akan terhapus:** 🧱 {ms_c} Milestone | 💬 {chat_c} Chat | 📦 {inv_c} Transaksi")
                
                confirm_del = st.checkbox("✅ Saya yakin ingin menghapus site ini beserta semua data terkaitnya.", key="confirm_del_check")
                
                if st.button("🗑️ HAPUS PERMANEN", type="primary", disabled=not confirm_del, use_container_width=True):
                    try:
                        with st.spinner("🔄 Menghapus data..."):
                            if ms_c > 0:
                                for mid in ms_df[ms_df['project_id']==sel_edit_id]['id'].tolist(): delete_row_by_id("milestones", mid)
                            if chat_c > 0:
                                for cid in chat_df[chat_df['site_id']==sel_edit_id]['id'].tolist(): delete_row_by_id("chat_messages", cid)
                            if inv_c > 0:
                                for iid in inv_df[inv_df['project_id']==sel_edit_id]['id'].tolist(): delete_row_by_id("inventory_transactions", iid)
                            
                            delete_row_by_id("projects", sel_edit_id)
                            st.cache_data.clear()
                            st.success("✅ Site & semua data terkait berhasil dihapus permanen!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal menghapus: {str(e)}")
                st.markdown('</div>', unsafe_allow_html=True)

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

    # ═══════════════════════════════════════════════════════════════════
    # TAB 2: MASTER PROJECT
    # ═══════════════════════════════════════════════════════════════════
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
                    insert_row("master_projects", {'id': generate_id(), 'project_code': p_code, 'project_name': p_name, 'category': p_cat, 'status': p_stat, 'start_date': today_str(), 'end_date': today_str()})
                    st.toast("✅ Master Project disimpan!", icon="🏢")
                    st.rerun()
                else: st.error("❌ Kode & Nama wajib diisi!")
        st.divider()
        if not master_df.empty:
            st.dataframe(master_df[['project_code', 'project_name', 'category', 'status']], use_container_width=True, hide_index=True)

    # ═══════════════════════════════════════════════════════════════════
    # TAB 3: TAMBAH SITE
    # ═══════════════════════════════════════════════════════════════════
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
                        insert_row("projects", {'id': generate_id(), 'master_project_id': m_pid, 'site_id': s_id, 'site_name': s_name, 'site_category': s_cat, 'site_type': s_type, 'site_coordinate': s_coord, 'vendor': vend, 'pm': pm_val, 'tower_height': str(h_val), 'start_date': start_d.strftime('%Y-%m-%d'), 'end_date': end_d.strftime('%Y-%m-%d'), 'status': 'ON_TRACK', 'progress': '0'})
                        st.toast("✅ Site berhasil ditambahkan!", icon="📍")
                        st.rerun()
                    except Exception as e: st.error(f"❌ Gagal simpan: {str(e)}")
                else: st.error("❌ Lengkapi Site ID, Name, dan pilih Master Project!")

    # ═══════════════════════════════════════════════════════════════════
    # TAB 4: IMPORT CSV
    # ═══════════════════════════════════════════════════════════════════
    with tab4:
        st.subheader("📥 Import Site via CSV")
        st.info("ℹ️ Kolom wajib: `master_project_id`, `site_id`, `site_name`")
        template = pd.DataFrame({'master_project_id': ['ID_PROYEK'], 'site_id': ['SITE-001'], 'site_name': ['Tower A'], 'site_category': ['New Site'], 'site_type': ['SST'], 'vendor': ['PT. X'], 'pm': ['Budi'], 'tower_height': [45], 'site_coordinate': ['-6.17,106.82'], 'start_date': [today_str()], 'end_date': [today_str()]})
        st.download_button("📥 Template", template.to_csv(index=False), "template.csv", "text/csv")
        up = st.file_uploader("Upload CSV", type=['csv'], key="site_csv")
        if up:
            idf = pd.read_csv(up)
            st.dataframe(idf.head())
            if st.button("🚀 Import", type="primary", use_container_width=True):
                count = 0
                for _, r in idf.iterrows():
                    try:
                        insert_row("projects", {'id': generate_id(), 'master_project_id': str(r.get('master_project_id','')), 'site_id': str(r.get('site_id','')), 'site_name': str(r.get('site_name','')), 'site_category': str(r.get('site_category','New Site')), 'site_type': str(r.get('site_type','SST')), 'vendor': str(r.get('vendor','')), 'pm': str(r.get('pm','')), 'tower_height': str(r.get('tower_height', 45)), 'site_coordinate': str(r.get('site_coordinate','')), 'start_date': str(r.get('start_date', today_str())), 'end_date': str(r.get('end_date', today_str())), 'status': 'ON_TRACK', 'progress': '0'})
                        count += 1
                    except: pass
                st.toast(f"✅ {count} site berhasil diimport!", icon="📦")
                st.rerun()

if __name__ == "__main__":
    project_tracker_page()
