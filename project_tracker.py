import streamlit as st
import pandas as pd
from supabase_db import read_sheet, insert_row, update_row, find_row_by_id, generate_id, today_str

def sync_progress_from_milestones(site_id):
    """Hitung progress dari milestones"""
    ms_df = read_sheet("milestones")
    if ms_df.empty:
        return 0, 'ON_TRACK'
    
    site_ms = ms_df[ms_df['project_id'] == site_id]
    if site_ms.empty:
        return 0, 'ON_TRACK'
    
    site_ms['weight'] = pd.to_numeric(site_ms['weight'], errors='coerce').fillna(0)
    total_weight = site_ms['weight'].sum()
    done_weight = site_ms[site_ms['status'] == 'DONE']['weight'].sum()
    progress = round((done_weight / total_weight) * 100, 1) if total_weight > 0 else 0
    
    delayed = len(site_ms[site_ms['status'] == 'DELAYED'])
    status = 'CRITICAL' if delayed > 3 else ('DELAYED' if delayed > 0 else 'ON_TRACK')
    
    return progress, status

def project_tracker_page():
    st.title("📁 Site Tracker")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Daftar Site", "➕ Tambah Site", "✏️ Edit Site", "🔗 Detail", "📥 Import CSV"
    ])
    
    with tab1:
        st.subheader("Daftar Site")
        df = read_sheet("projects")
        
        if not df.empty:
            if 'progress' in df.columns:
                df['progress'] = pd.to_numeric(df['progress'], errors='coerce').fillna(0)
            
            def color_status(val):
                if val == 'ON_TRACK': return 'background-color: #d4edda; font-weight: bold'
                elif val == 'DELAYED': return 'background-color: #fff3cd; font-weight: bold'
                elif val == 'CRITICAL': return 'background-color: #f8d7da; font-weight: bold'
                return ''
            
            display_cols = ['site_id', 'site_name', 'site_coordinate', 'vendor', 'status', 'progress', 'pm']
            display_df = df[[c for c in display_cols if c in df.columns]]
            styled = display_df.style.map(color_status, subset=['status']) if 'status' in df.columns else display_df
            st.dataframe(styled, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Site", len(df))
            col2.metric("On Track", len(df[df['status']=='ON_TRACK']) if 'status' in df.columns else 0)
            col3.metric("Terlambat", len(df[df['status'].isin(['DELAYED','CRITICAL'])]) if 'status' in df.columns else 0)
            
            # Sync button
            if st.button("🔄 Sync Progress dari Milestones"):
                for _, row in df.iterrows():
                    prog, sts = sync_progress_from_milestones(row['id'])
                    ridx = find_row_by_id("projects", row['id'])
                    if ridx:
                        update_row("projects", ridx, {'progress': str(prog), 'status': sts})
                st.success("✅ Semua site di-sync!")
                st.rerun()
        else:
            st.info("📋 Belum ada site.")
    
    with tab2:
        st.subheader("Tambah Site")
        with st.form("add_site"):
            site_id = st.text_input("Site ID", placeholder="SITE-001")
            site_name = st.text_input("Site Name", placeholder="Tower Gambir")
            site_coordinate = st.text_input("Koordinat", placeholder="-6.1754, 106.8272")
            vendor = st.text_input("Vendor")
            pm = st.text_input("PM")
            c1, c2 = st.columns(2)
            with c1: start_date = st.date_input("Plan Start")
            with c2: end_date = st.date_input("Plan End")
            
            if st.form_submit_button("💾 Simpan", type="primary"):
                if not site_name or not site_id:
                    st.error("❌ Site ID dan Site Name wajib diisi!")
                else:
                    insert_row("projects", {
                        'id': generate_id(), 'site_id': site_id, 'site_name': site_name,
                        'site_coordinate': site_coordinate, 'vendor': vendor, 'pm': pm,
                        'start_date': start_date.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d'),
                        'status': 'ON_TRACK', 'progress': '0'
                    })
                    st.success(f"✅ Site {site_name} ditambahkan!")
                    st.rerun()
    
    with tab3:
        st.subheader("Edit Site")
        df = read_sheet("projects")
        if not df.empty:
            selected = st.selectbox("Pilih Site:", df['id'].tolist(),
                                   format_func=lambda x: f"{df[df['id']==x]['site_id'].values[0]} - {df[df['id']==x]['site_name'].values[0]}" if 'site_id' in df.columns else x)
            if selected:
                site = df[df['id']==selected].iloc[0]
                ridx = find_row_by_id("projects", selected)
                with st.form("edit_site"):
                    new_status = st.selectbox("Status", ["ON_TRACK","DELAYED","CRITICAL"],
                                             index=["ON_TRACK","DELAYED","CRITICAL"].index(site.get('status','ON_TRACK')) if site.get('status') in ["ON_TRACK","DELAYED","CRITICAL"] else 0)
                    new_progress = st.slider("Progress", 0, 100, int(float(site.get('progress',0))) if site.get('progress') else 0)
                    if st.form_submit_button("💾 Update"):
                        update_row("projects", ridx, {'status': new_status, 'progress': str(new_progress)})
                        st.success("✅ Site diupdate!")
                        st.rerun()
    
    with tab4:
        st.subheader("Detail Site & Milestone")
        df = read_sheet("projects")
        if not df.empty:
            selected = st.selectbox("Pilih Site:", df['id'].tolist(),
                                   format_func=lambda x: f"{df[df['id']==x]['site_id'].values[0]} - {df[df['id']==x]['site_name'].values[0]}" if 'site_id' in df.columns else x,
                                   key="detail_select")
            if selected:
                site = df[df['id']==selected].iloc[0]
                col1, col2, col3 = st.columns(3)
                col1.metric("Site ID", site.get('site_id','-'))
                col2.metric("Status", site.get('status','-'))
                col3.metric("Progress", f"{site.get('progress','0')}%")
                
                ms_df = read_sheet("milestones")
                if not ms_df.empty:
                    site_ms = ms_df[ms_df['project_id'] == selected]
                    if not site_ms.empty:
                        st.markdown("**Milestones:**")
                        st.dataframe(site_ms[['name','status','planned_end','material_status']], use_container_width=True)
    
    with tab5:
        st.subheader("Import CSV")
        template = pd.DataFrame({
            'site_id': ['SITE-001'], 'site_name': ['Tower A'], 'site_coordinate': ['-6.17,106.82'],
            'vendor': ['PT. X'], 'pm': ['Budi'], 'start_date': [today_str()], 'end_date': [today_str()]
        })
        st.download_button("📥 Download Template", template.to_csv(index=False), "template_site.csv", "text/csv")
        
        up = st.file_uploader("Upload CSV", type=['csv'])
        if up:
            idf = pd.read_csv(up)
            st.dataframe(idf)
            if st.button("🚀 Import", type="primary"):
                count = 0
                for _, r in idf.iterrows():
                    insert_row("projects", {
                        'id': generate_id(), 'site_id': str(r.get('site_id','')),
                        'site_name': str(r.get('site_name','')), 'site_coordinate': str(r.get('site_coordinate','')),
                        'vendor': str(r.get('vendor','')), 'pm': str(r.get('pm','')),
                        'start_date': str(r.get('start_date', today_str())),
                        'end_date': str(r.get('end_date', today_str())),
                        'status': 'ON_TRACK', 'progress': '0'
                    })
                    count += 1
                st.success(f"✅ {count} site diimport!")
                st.rerun()

if __name__ == "__main__":
    project_tracker_page()