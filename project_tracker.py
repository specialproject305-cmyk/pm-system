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
    # Init session
    if 'project_filter' not in st.session_state:
        st.session_state.project_filter = "ALL"

    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .stColumn { width: 100% !important; margin-bottom: 10px; }
        button, input, select, textarea { min-height: 44px !important; font-size: 16px !important; }
    }
    .delete-section { border: 2px solid #dc3545; border-radius: 10px; padding: 15px; margin-top: 15px; background: #fff5f5; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📁 Site & Project Portfolio")

    try:
        master_df = read_sheet("master_projects")
        master_options = ["ALL"] + master_df["id"].tolist() if not master_df.empty else ["ALL"]
    except:
        master_df = pd.DataFrame()
        master_options = ["ALL"]

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Daftar Site", "🏢 Master Project", "➕ Tambah Site", "📥 Import CSV"])

    # ═══════════════ TAB 1: DAFTAR SITE ═══════════════
    with tab1:
        st.subheader("Daftar Site")
        df = read_sheet("projects")
        
        if not df.empty:
            df['progress'] = pd.to_numeric(df['progress'], errors='coerce').fillna(0)

            # Filter Master Project
            st.markdown("### 🌍 Filter Master Project")
            selected_proj = st.selectbox(
                "Pilih Proyek:", master_options,
                format_func=lambda x: "🌐 SEMUA PROYEK" if x == "ALL" 
                else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}",
                key="global_proj_filter"
            )
            st.session_state.project_filter = selected_proj

            if st.session_state.project_filter != "ALL" and 'master_project_id' in df.columns:
                df = df[df['master_project_id'] == st.session_state.project_filter]

            # Filter Lanjutan
            with st.expander("🔍 Filter Lanjutan", expanded=False):
                f1, f2, f3 = st.columns(3)
                with f1:
                    cats = sorted(df['site_category'].dropna().unique().tolist()) if 'site_category' in df.columns else []
                    sel_cats = st.multiselect("🏷️ Kategori", cats, default=cats, key="fcats")
                with f2:
                    vendors = sorted(df['vendor'].dropna().unique().tolist()) if 'vendor' in df.columns else []
                    sel_vendors = st.multiselect("🏢 Vendor", vendors, default=vendors, key="fvend")
                with f3:
                    sel_status = st.multiselect("🚦 Status", ["ON_TRACK","DELAYED","CRITICAL"], default=["ON_TRACK","DELAYED","CRITICAL"], key="fstat")

            filtered_df = df.copy()
            if sel_cats and 'site_category' in df.columns: filtered_df = filtered_df[filtered_df['site_category'].isin(sel_cats)]
            if sel_vendors and 'vendor' in df.columns: filtered_df = filtered_df[filtered_df['vendor'].isin(sel_vendors)]
            if sel_status and 'status' in df.columns: filtered_df = filtered_df[filtered_df['status'].isin(sel_status)]

            # Tampilkan tabel
            def color_status(val):
                if val == 'ON_TRACK': return 'background-color: #d4edda; font-weight: bold'
                elif val == 'DELAYED': return 'background-color: #fff3cd; font-weight: bold'
                elif val == 'CRITICAL': return 'background-color: #f8d7da; font-weight: bold'
                return ''
            
            display_cols = ['site_id','site_name','site_category','site_type','vendor','pm','tower_height','site_coordinate','status','progress']
            display_df = filtered_df[[c for c in display_cols if c in filtered_df.columns]]
            st.dataframe(display_df.style.map(color_status, subset=['status']), use_container_width=True, hide_index=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Site", len(filtered_df))
            col2.metric("On Track", len(filtered_df[filtered_df['status']=='ON_TRACK']))
            col3.metric("Terlambat", len(filtered_df[filtered_df['status'].isin(['DELAYED','CRITICAL'])]))

            # Sync button
            if st.button("🔄 Sync Progress", use_container_width=True):
                for _, row in filtered_df.iterrows():
                    prog, sts = sync_progress_from_milestones(row['id'])
                    ridx = find_row_by_id("projects", row['id'])
                    if ridx: update_row("projects", ridx, {'progress': str(prog), 'status': sts})
                st.cache_data.clear()
                st.success("✅ Progress di-sync!")
                st.rerun()

            # Quick Edit & Delete
            st.markdown("---")
            st.markdown("### ⚙️ Quick Edit & Delete")
            sel_edit_id = st.selectbox("Pilih Site:", filtered_df['id'].tolist(),
                format_func=lambda x: f"{filtered_df[filtered_df['id']==x]['site_id'].values[0]} - {filtered_df[filtered_df['id']==x]['site_name'].values[0]}")
            
            if sel_edit_id:
                site = filtered_df[filtered_df['id']==sel_edit_id].iloc[0]
                ridx = find_row_by_id("projects", sel_edit_id)
                
                with st.form("quick_edit"):
                    c1, c2 = st.columns(2)
                    with c1:
                        n_stat = st.selectbox("Status", ["ON_TRACK","DELAYED","CRITICAL"], 
                            index=["ON_TRACK","DELAYED","CRITICAL"].index(site.get('status','ON_TRACK')))
                        n_prog = st.slider("Progress", 0, 100, int(float(site.get('progress',0))))
                    with c2:
                        n_pm = st.text_input("PM", value=str(site.get('pm','')))
                        n_vend = st.text_input("Vendor", value=str(site.get('vendor','')))
                    
                    if st.form_submit_button("💾 Update", type="primary", use_container_width=True):
                        update_row("projects", ridx, {'status': n_stat, 'progress': str(n_prog), 'pm': n_pm, 'vendor': n_vend})
                        st.toast("✅ Diupdate!"); st.rerun()

                # Delete section
                st.markdown('<div class="delete-section">', unsafe_allow_html=True)
                st.markdown("#### 🗑️ Hapus Site")
                if st.button("🗑️ HAPUS PERMANEN", type="primary", use_container_width=True):
                    delete_row_by_id("projects", sel_edit_id)
                    st.cache_data.clear()
                    st.warning("🗑️ Dihapus!"); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("📋 Belum ada site.")

    # ═══════════════ TAB 2: MASTER PROJECT ═══════════════
    with tab2:
        st.subheader("🏢 Master Project")
        with st.form("add_master"):
            c1, c2 = st.columns(2)
            with c1:
                p_code = st.text_input("Kode Proyek", placeholder="PROJ-001")
                p_name = st.text_input("Nama Proyek", placeholder="Rollout Phase 1")
            with c2:
                p_cat = st.selectbox("Kategori", ["4G Rollout","5G Upgrade","Fiber Optic","General"])
            if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                if p_code and p_name:
                    insert_row("master_projects", {'id': generate_id(), 'project_code': p_code, 'project_name': p_name, 'category': p_cat, 'status': 'ACTIVE', 'start_date': today_str(), 'end_date': today_str()})
                    st.toast("✅ Disimpan!"); st.rerun()
                else: st.error("❌ Lengkapi!")
        st.divider()
        if not master_df.empty:
            st.dataframe(master_df, use_container_width=True, hide_index=True)

    # ═══════════════ TAB 3: TAMBAH SITE ═══════════════
    with tab3:
        st.subheader("➕ Tambah Site")
        with st.form("add_site"):
            m_pid = st.selectbox("Master Project", master_options[1:] if len(master_options)>1 else ["-"],
                format_func=lambda x: f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}" if x != "-" else "-")
            c1, c2 = st.columns(2)
            with c1:
                s_id = st.text_input("Site ID", placeholder="SITE-001")
                s_name = st.text_input("Site Name", placeholder="Tower Gambir")
                s_cat = st.selectbox("Kategori", ["New Site","Collocation","Upgrade","Relocation"])
            with c2:
                s_coord = st.text_input("Koordinat", placeholder="-6.17,106.82")
                vend = st.text_input("Vendor")
                pm_val = st.text_input("PM")
            if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                if s_id and s_name and m_pid != "-":
                    insert_row("projects", {'id': generate_id(), 'master_project_id': m_pid, 'site_id': s_id, 'site_name': s_name, 'site_category': s_cat, 'site_coordinate': s_coord, 'vendor': vend, 'pm': pm_val, 'status': 'ON_TRACK', 'progress': '0', 'start_date': today_str(), 'end_date': today_str()})
                    st.toast("✅ Site ditambahkan!"); st.rerun()
                else: st.error("❌ Lengkapi!")

    # ═══════════════ TAB 4: IMPORT CSV ═══════════════
    with tab4:
        st.subheader("📥 Import CSV")
        template = pd.DataFrame({'master_project_id':['ID_PROYEK'],'site_id':['SITE-001'],'site_name':['Tower A'],'site_category':['New Site'],'vendor':['PT. X'],'pm':['Budi'],'site_coordinate':['-6.17,106.82'],'start_date':[today_str()],'end_date':[today_str()]})
        st.download_button("📥 Template", template.to_csv(index=False), "template.csv", "text/csv")
        up = st.file_uploader("Upload CSV", type=['csv'])
        if up:
            idf = pd.read_csv(up); st.dataframe(idf)
            if st.button("🚀 Import", type="primary", use_container_width=True):
                count = 0
                for _, r in idf.iterrows():
                    try:
                        insert_row("projects", {'id': generate_id(), 'master_project_id': str(r.get('master_project_id','')), 'site_id': str(r.get('site_id','')), 'site_name': str(r.get('site_name','')), 'site_category': str(r.get('site_category','New Site')), 'vendor': str(r.get('vendor','')), 'pm': str(r.get('pm','')), 'site_coordinate': str(r.get('site_coordinate','')), 'start_date': str(r.get('start_date',today_str())), 'end_date': str(r.get('end_date',today_str())), 'status': 'ON_TRACK', 'progress': '0'})
                        count += 1
                    except: pass
                st.toast(f"✅ {count} site diimport!"); st.rerun()

if __name__ == "__main__":
    project_tracker_page()
