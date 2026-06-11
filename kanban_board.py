import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from supabase_db import read_sheet, update_row

def kanban_page():
    st.title("📋 Kanban Board")
    
    sites_df = read_sheet("projects")
    ms_df = read_sheet("milestones")
    
    if ms_df.empty:
        st.info("📋 Belum ada milestone.")
        return
    
    # Global filter
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid_sites = sites_df[sites_df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
        sites_df = sites_df[sites_df['id'].isin(valid_sites)]
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)] if not ms_df.empty else ms_df
    
    ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    
    # Filter site
    site_options = ["ALL SITE"] + sites_df["id"].tolist() if not sites_df.empty else ["ALL SITE"]
    selected_site = st.selectbox("🎯 Pilih Site:", site_options,
        format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE" 
        else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
    
    if selected_site != "ALL SITE":
        ms_df = ms_df[ms_df['project_id'] == selected_site]
    
    if ms_df.empty:
        st.info("📋 Tidak ada milestone.")
        return
    
    # Merge site info
    site_id_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    site_name_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    ms_df['site_code'] = ms_df['project_id'].map(site_id_map).fillna('-')
    ms_df['site_name'] = ms_df['project_id'].map(site_name_map).fillna('-')
    ms_df['deadline'] = ms_df['planned_end'].dt.strftime('%d %b %Y')
    
    # KPI
    total = len(ms_df)
    done = len(ms_df[ms_df['status']=='DONE'])
    ongoing = len(ms_df[ms_df['status']=='ONGOING'])
    pending = len(ms_df[ms_df['status']=='PENDING'])
    delayed = len(ms_df[ms_df['status']=='DELAYED'])
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📋 Total", total)
    col2.metric("✅ Done", done)
    col3.metric("🔄 Ongoing", ongoing)
    col4.metric("⏳ Pending", pending)
    col5.metric("🔴 Delayed", delayed)
    
    st.divider()
    
    # Kanban columns
    cols = st.columns(4)
    statuses = ['PENDING', 'ONGOING', 'DONE', 'DELAYED']
    colors = {'PENDING': '#94A3B8', 'ONGOING': '#3B82F6', 'DONE': '#10B981', 'DELAYED': '#EF4444'}
    emojis = {'PENDING': '⏳', 'ONGOING': '🔄', 'DONE': '✅', 'DELAYED': '🔴'}
    
    for i, status in enumerate(statuses):
        with cols[i]:
            st.markdown(f"### {emojis[status]} {status}")
            subset = ms_df[ms_df['status'] == status]
            
            if subset.empty:
                st.caption("— kosong —")
            else:
                for _, task in subset.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div style='background:#1E293B; padding:10px; border-radius:8px; margin:5px 0; border-left:4px solid {colors[status]};'>
                            <strong style='color:white;'>{task['name']}</strong><br>
                            <small style='color:#CBD5E1;'>📍 {task['site_code']}</small><br>
                            <small style='color:#94A3B8;'>📅 {task['deadline']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Quick action
                        if status != 'DONE':
                            if st.button(f"✅ Done", key=f"kanban_done_{task['id']}"):
                                update_row('milestones', task['id'], {
                                    'status': 'DONE',
                                    'actual_end': date.today().strftime('%Y-%m-%d')
                                })
                                st.rerun()
                        if status != 'DELAYED' and status != 'DONE':
                            if st.button(f"⏳ Delay", key=f"kanban_delay_{task['id']}"):
                                update_row('milestones', task['id'], {'status': 'DELAYED'})
                                st.cache_data.clear()
                                st.rerun()
                        st.markdown("---")

if __name__ == "__main__":
    kanban_page()
