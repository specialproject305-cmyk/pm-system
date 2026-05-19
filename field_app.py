import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from supabase_db import read_sheet, update_row, read_all_sheets

def field_app_page():
    st.title("📱 Field Update App")
    st.caption("Update milestone dari lapangan — cepat & simpel")
    
    all_data = read_all_sheets()
    ms_df = all_data.get('milestones', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    
    # Global filter
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid_sites = sites_df[sites_df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
        sites_df = sites_df[sites_df['id'].isin(valid_sites)]
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)] if not ms_df.empty else ms_df
    
    if ms_df.empty:
        st.info("📋 Belum ada milestone.")
        return
    
    ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    
    pic_list = sorted(ms_df['assigned_to'].dropna().unique().tolist()) if 'assigned_to' in ms_df.columns else []
    if not pic_list:
        st.warning("⚠️ Tidak ada PIC terdaftar.")
        return
    
    selected_pic = st.selectbox("👷 Pilih PIC:", pic_list)
    
    my_tasks = ms_df[
        (ms_df['assigned_to'] == selected_pic) &
        (ms_df['status'].isin(['PENDING', 'ONGOING', 'DELAYED']))
    ].copy()
    
    if my_tasks.empty:
        st.success(f"✅ Tidak ada task pending untuk {selected_pic}!")
        return
    
    site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    site_name_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    my_tasks['site_code'] = my_tasks['project_id'].map(site_map).fillna('-')
    my_tasks['site_name'] = my_tasks['project_id'].map(site_name_map).fillna('-')
    my_tasks['deadline'] = my_tasks['planned_end'].dt.strftime('%d %b %Y')
    my_tasks['days_left'] = (my_tasks['planned_end'].dt.date - date.today()).apply(lambda x: x.days if pd.notna(x) else 999)
    
    total = len(my_tasks)
    overdue = len(my_tasks[my_tasks['days_left'] < 0])
    today_count = len(my_tasks[my_tasks['days_left'] == 0])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 My Tasks", total)
    col2.metric("🔴 Overdue", overdue)
    col3.metric("🟡 Today", today_count)
    
    st.divider()
    
    sites = my_tasks['site_code'].unique()
    
    for site_code in sites:
        site_tasks = my_tasks[my_tasks['site_code'] == site_code]
        site_name = site_tasks['site_name'].iloc[0]
        
        with st.expander(f"📍 {site_code} - {site_name} ({len(site_tasks)} task)", expanded=True):
            for _, task in site_tasks.iterrows():
                days = task['days_left']
                if days < 0:
                    bg = '#FEE2E2'; border = '#EF4444'
                elif days == 0:
                    bg = '#FEF3C7'; border = '#F59E0B'
                else:
                    bg = '#F0FDF4'; border = '#10B981'
                
                st.markdown(f"""
                <div style='background:{bg}; padding:12px; border-radius:10px; margin:8px 0; border-left:5px solid {border};'>
                    <strong>{task['name']}</strong><br>
                    📅 Deadline: {task['deadline']} | ⏰ {days} hari | Status: {task['status']}
                </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button(f"✅ Done", key=f"done_{task['id']}"):
                        update_row('milestones', task['id'], {
                            'status': 'DONE',
                            'actual_end': date.today().strftime('%Y-%m-%d')
                        })
                        st.rerun()
                with col_b:
                    if st.button(f"🔄 Ongoing", key=f"ongoing_{task['id']}"):
                        update_row('milestones', task['id'], {
                            'status': 'ONGOING',
                            'actual_start': date.today().strftime('%Y-%m-%d')
                        })
                        st.rerun()
                with col_c:
                    if st.button(f"⏳ Delay", key=f"delay_{task['id']}"):
                        update_row('milestones', task['id'], {'status': 'DELAYED'})
                        st.rerun()

if __name__ == "__main__":
    field_app_page()
