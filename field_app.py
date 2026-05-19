import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from supabase_db import read_sheet, update_row, read_all_sheets

def field_app_page():
    st.title("📱 Field Update App")
    st.caption("Update milestone dari lapangan — lengkap dengan progress & tanggal aktual")
    
    all_data = read_all_sheets()
    ms_df = all_data.get('milestones', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    master_df = all_data.get('master_projects', pd.DataFrame())
    
    # Global filter
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid_sites = sites_df[sites_df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
        sites_df = sites_df[sites_df['id'].isin(valid_sites)]
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)] if not ms_df.empty else ms_df
    
    if ms_df.empty:
        st.info("📋 Belum ada milestone.")
        return
    
    ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    
    # SIDEBAR
    with st.sidebar:
        st.header("⚙️ Filter & Info")
        
        # Filter Project
        if not master_df.empty:
            master_options = ["ALL"] + master_df['id'].tolist()
            selected_master = st.selectbox("🏢 Project:", master_options,
                format_func=lambda x: "🌐 SEMUA" if x == "ALL" 
                else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}")
            if selected_master != "ALL":
                valid_sites2 = sites_df[sites_df['master_project_id'] == selected_master]['id'].tolist()
                ms_df = ms_df[ms_df['project_id'].isin(valid_sites2)]
        
        # Filter PIC
        pic_list = sorted(ms_df['assigned_to'].dropna().unique().tolist()) if 'assigned_to' in ms_df.columns else []
        if pic_list:
            selected_pic = st.selectbox("👷 PIC:", pic_list)
            ms_df = ms_df[ms_df['assigned_to'] == selected_pic]
        
        # Filter Status
        status_options = st.multiselect("📊 Status:", ['PENDING','ONGOING','DELAYED','DONE'], 
                                        default=['PENDING','ONGOING','DELAYED'])
        ms_df = ms_df[ms_df['status'].isin(status_options)]
        
        st.divider()
        st.metric("📋 Total Tasks", len(ms_df))
        st.metric("🔴 Overdue", len(ms_df[ms_df['planned_end'].dt.date < date.today()]) if not ms_df.empty else 0)
    
    if ms_df.empty:
        st.success("✅ Tidak ada task!")
        return
    
    # Merge site info
    site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    site_name_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    ms_df['site_code'] = ms_df['project_id'].map(site_map).fillna('-')
    ms_df['site_name'] = ms_df['project_id'].map(site_name_map).fillna('-')
    ms_df['deadline'] = ms_df['planned_end'].dt.strftime('%d %b %Y')
    ms_df['days_left'] = (ms_df['planned_end'].dt.date - date.today()).apply(lambda x: x.days if pd.notna(x) else 999)
    
    # Tampilkan per site
    sites = ms_df['site_code'].unique()
    
    for site_code in sites:
        site_tasks = ms_df[ms_df['site_code'] == site_code]
        site_name = site_tasks['site_name'].iloc[0]
        
        with st.expander(f"📍 {site_code} - {site_name} ({len(site_tasks)} task)", expanded=True):
            for _, task in site_tasks.iterrows():
                days = task['days_left']
                if days < 0:
                    bg = '#FEE2E2'; border = '#EF4444'
                elif days == 0:
                    bg = '#FEF3C7'; border = '#F59E0B'
                elif task['status'] == 'DONE':
                    bg = '#DCFCE7'; border = '#10B981'
                else:
                    bg = '#F0FDF4'; border = '#10B981'
                
                # Info task
                st.markdown(f"""
                <div style='background:{bg}; padding:12px; border-radius:10px; margin:8px 0; border-left:5px solid {border};'>
                    <strong>{task['name']}</strong><br>
                    📅 Deadline: {task['deadline']} | ⏰ {days} hari | Status: <b>{task['status']}</b>
                </div>
                """, unsafe_allow_html=True)
                
                # Form update
                with st.form(f"update_{task['id']}", clear_on_submit=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        new_status = st.selectbox("Status", ['PENDING','ONGOING','DONE','DELAYED'],
                            index=['PENDING','ONGOING','DONE','DELAYED'].index(task['status']),
                            key=f"status_{task['id']}")
                        new_progress = st.slider("Progress %", 0, 100, 
                            int(float(task.get('progress', 0))) if task.get('progress') else 0,
                            key=f"prog_{task['id']}")
                    with col2:
                        as_default = pd.to_datetime(task.get('actual_start')).date() if pd.notna(task.get('actual_start')) else None
                        new_actual_start = st.date_input("Actual Start", value=as_default, key=f"as_{task['id']}")
                    with col3:
                        ae_default = pd.to_datetime(task.get('actual_end')).date() if pd.notna(task.get('actual_end')) else None
                        new_actual_end = st.date_input("Actual End", value=ae_default, key=f"ae_{task['id']}")
                    
                    if st.form_submit_button("💾 Simpan Update", type="primary", use_container_width=True):
                        update_data = {
                            'status': new_status,
                            'progress': str(new_progress)
                        }
                        if new_actual_start:
                            update_data['actual_start'] = new_actual_start.strftime('%Y-%m-%d')
                        if new_actual_end and new_status == 'DONE':
                            update_data['actual_end'] = new_actual_end.strftime('%Y-%m-%d')
                        elif new_status == 'DONE' and not new_actual_end:
                            update_data['actual_end'] = date.today().strftime('%Y-%m-%d')
                        
                        update_row('milestones', task['id'], update_data)
                        st.success(f"✅ **{task['name']}** berhasil diupdate!")
                        st.toast(f"✅ {task['name']} → {new_status}", icon="🎉")
                        st.rerun()
                
                st.markdown("---")

if __name__ == "__main__":
    field_app_page()
