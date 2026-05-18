import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from supabase_db import read_all_sheets, update_row, read_sheet

def daily_task_page():
    st.title("📋 Daily Task Board")
    st.caption("Milestone yang harus di-follow up hari ini & besok")
    
    all_data = read_all_sheets()
    ms_df = all_data.get('milestones', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    master_df = all_data.get('master_projects', pd.DataFrame())
    
    if ms_df.empty:
        st.info("📋 Belum ada milestone.")
        return
    
    # Konversi tanggal
    for col in ['planned_start', 'planned_end']:
        if col in ms_df.columns:
            ms_df[col] = pd.to_datetime(ms_df[col], errors='coerce')
    
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    # Filter: milestone yang belum DONE, deadline hari ini atau besok
    follow_up = ms_df[
        (ms_df['status'].isin(['PENDING', 'ONGOING', 'DELAYED'])) &
        (
            (ms_df['planned_end'].dt.date <= tomorrow) |  # Deadline sudah dekat
            ((ms_df['planned_start'].dt.date <= today) & (ms_df['status'] == 'PENDING'))  # Harusnya sudah mulai
        )
    ].copy()
    
    if follow_up.empty:
        st.success("✅ Tidak ada milestone yang harus di-follow up hari ini atau besok!")
        return

    st.write(f"🔍 Total follow-up: {len(follow_up)} | PENDING: {len(follow_up[follow_up['status']=='PENDING'])} | ONGOING: {len(follow_up[follow_up['status']=='ONGOING'])} | DELAYED: {len(follow_up[follow_up['status']=='DELAYED'])}")
    
    # Merge dengan site & master project
    site_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    site_id_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    master_map = dict(zip(master_df['id'], master_df['project_name'])) if not master_df.empty else {}
    master_id_map = dict(zip(sites_df['id'], sites_df['master_project_id'])) if not sites_df.empty and 'master_project_id' in sites_df.columns else {}
    
    follow_up['site_name'] = follow_up['project_id'].map(site_map)
    follow_up['site_id_code'] = follow_up['project_id'].map(site_id_map)
    follow_up['master_name'] = follow_up['project_id'].map(master_id_map).map(master_map)
    follow_up['deadline_date'] = follow_up['planned_end'].dt.date
    follow_up['days_left'] = (follow_up['deadline_date'] - today).dt.days
    
    # Kategori
    def categorize(days_left, status):
        if days_left < 0: return "🔴 OVERDUE"
        elif days_left == 0: return "🟡 TODAY"
        elif days_left == 1: return "🟢 TOMORROW"
        return "⚪ UPCOMING"
    
    follow_up['category'] = follow_up.apply(lambda r: categorize(r['days_left'], r['status']), axis=1)
    
    # Filter Master Project
    if not master_df.empty:
        master_options = ["ALL"] + master_df['id'].tolist()
        selected_master = st.selectbox("🏢 Filter Project:", master_options,
            format_func=lambda x: "🌐 SEMUA PROYEK" if x == "ALL" 
            else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}")
        
        if selected_master != "ALL":
            valid_sites = sites_df[sites_df['master_project_id'] == selected_master]['id'].tolist()
            follow_up = follow_up[follow_up['project_id'].isin(valid_sites)]
    
    # Filter PIC
    if 'assigned_to' in follow_up.columns:
        pic_list = sorted(follow_up['assigned_to'].dropna().unique().tolist())
        selected_pic = st.multiselect("👤 Filter PIC:", pic_list, default=pic_list[:5] if len(pic_list)>5 else pic_list)
        if selected_pic:
            follow_up = follow_up[follow_up['assigned_to'].isin(selected_pic)]
    
    st.divider()
    
    # KPI Cards
    col1, col2, col3 = st.columns(3)
    overdue = len(follow_up[follow_up['category'] == '🔴 OVERDUE'])
    today_count = len(follow_up[follow_up['category'] == '🟡 TODAY'])
    tomorrow_count = len(follow_up[follow_up['category'] == '🟢 TOMORROW'])
    
    col1.metric("🔴 OVERDUE", overdue)
    col2.metric("🟡 TODAY", today_count)
    col3.metric("🟢 TOMORROW", tomorrow_count)
    
    st.divider()
    
    # Tampilkan per kategori
    categories = ['🔴 OVERDUE', '🟡 TODAY', '🟢 TOMORROW']
    cat_colors = {'🔴 OVERDUE': '#f8d7da', '🟡 TODAY': '#fff3cd', '🟢 TOMORROW': '#d4edda'}
    
    for cat in categories:
        subset = follow_up[follow_up['category'] == cat]
        if not subset.empty:
            st.markdown(f"### {cat} ({len(subset)} task)")
            
            for _, row in subset.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style='background:{cat_colors.get(cat, "#f0f0f0")}; padding:10px; border-radius:8px; margin:5px 0; border-left:4px solid #333;'>
                        <strong>{row['name']}</strong><br>
                        📁 {row.get('master_name', '-')} | 📍 {row.get('site_id_code', '-')} - {row.get('site_name', '-')}<br>
                        👤 PIC: <code>{row.get('assigned_to', '-')}</code> | 📅 Deadline: {row['deadline_date'].strftime('%d %b %Y')} | ⏰ {row['days_left']} hari
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Quick update button
                    col_act1, col_act2, col_act3 = st.columns([1, 1, 2])
                    with col_act1:
                        if st.button(f"✅ Done", key=f"done_{row['id']}"):
                            update_row('milestones', row['id'], {'status': 'DONE', 'actual_end': today.strftime('%Y-%m-%d')})
                            st.rerun()
                    with col_act2:
                        if st.button(f"⏳ Delay", key=f"delay_{row['id']}"):
                            update_row('milestones', row['id'], {'status': 'DELAYED'})
                            st.rerun()
    
    # Export CSV
    st.divider()
    csv = follow_up[['name', 'master_name', 'site_id_code', 'site_name', 'assigned_to', 'deadline_date', 'days_left', 'category', 'status']]
    csv.columns = ['Task', 'Project', 'Site ID', 'Site Name', 'PIC', 'Deadline', 'Days Left', 'Category', 'Status']
    st.download_button("📥 Download Daily Tasks CSV", csv.to_csv(index=False), f"daily_tasks_{today}.csv", "text/csv")

if __name__ == "__main__":
    daily_task_page()
