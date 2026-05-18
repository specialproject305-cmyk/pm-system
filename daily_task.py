import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from supabase_db import read_all_sheets, update_row

def daily_task_page():
    st.title("📋 Weekly Task Board")
    st.caption("Milestone yang harus di-follow up minggu ini (7 hari ke depan)")
    
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
    week_end = today + timedelta(days=7)
    
    # Filter: milestone yang belum DONE, deadline dalam 7 hari atau sudah overdue
    follow_up = ms_df[
        (ms_df['status'].isin(['PENDING', 'ONGOING', 'DELAYED'])) &
        (ms_df['planned_end'].dt.date <= week_end)
    ].copy()
    
    if follow_up.empty:
        st.success("✅ Tidak ada milestone untuk minggu ini!")
        return
    
    # Merge data
    site_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    site_id_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    master_map = dict(zip(master_df['id'], master_df['project_name'])) if not master_df.empty else {}
    master_id_map = {}
    if not sites_df.empty and 'master_project_id' in sites_df.columns:
        master_id_map = dict(zip(sites_df['id'], sites_df['master_project_id']))
    
    follow_up['site_name'] = follow_up['project_id'].map(site_map).fillna('-')
    follow_up['site_id_code'] = follow_up['project_id'].map(site_id_map).fillna('-')
    follow_up['master_name'] = follow_up['project_id'].map(master_id_map).map(master_map).fillna('-')
    follow_up['deadline_date'] = follow_up['planned_end'].dt.date
    follow_up['days_left'] = (follow_up['deadline_date'] - today).apply(lambda x: x.days if pd.notna(x) else 999)
    
    # Kategori
    def categorize(days_left, status):
        if days_left < 0: return "🔴 OVERDUE"
        elif days_left == 0: return "🟡 TODAY"
        elif days_left <= 2: return "🟠 THIS WEEK"
        elif days_left <= 7: return "🔵 NEXT WEEK"
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
        if pic_list:
            selected_pic = st.multiselect("👤 Filter PIC:", pic_list, default=pic_list[:min(5, len(pic_list))])
            if selected_pic:
                follow_up = follow_up[follow_up['assigned_to'].isin(selected_pic)]
    
    st.divider()
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    overdue = len(follow_up[follow_up['category'] == '🔴 OVERDUE'])
    today_count = len(follow_up[follow_up['category'] == '🟡 TODAY'])
    this_week = len(follow_up[follow_up['category'] == '🟠 THIS WEEK'])
    next_week = len(follow_up[follow_up['category'] == '🔵 NEXT WEEK'])
    
    col1.metric("🔴 OVERDUE", overdue)
    col2.metric("🟡 TODAY", today_count)
    col3.metric("🟠 THIS WEEK", this_week)
    col4.metric("🔵 NEXT WEEK", next_week)
    
    st.divider()
    
    # Tampilkan per kategori
    categories = ['🔴 OVERDUE', '🟡 TODAY', '🟠 THIS WEEK', '🔵 NEXT WEEK']
    cat_colors = {
        '🔴 OVERDUE': '#f8d7da',
        '🟡 TODAY': '#fff3cd',
        '🟠 THIS WEEK': '#ffe0b2',
        '🔵 NEXT WEEK': '#cce5ff'
    }
    
    for cat in categories:
        subset = follow_up[follow_up['category'] == cat]
        if not subset.empty:
            st.markdown(f"### {cat} ({len(subset)} task)")
            
            for _, row in subset.iterrows():
                with st.container():
                    dl_str = row['deadline_date'].strftime('%d %b %Y') if pd.notna(row['deadline_date']) else '-'
                    st.markdown(f"""
                    <div style='background:{cat_colors.get(cat, "#f0f0f0")}; padding:10px; border-radius:8px; margin:5px 0; border-left:4px solid #333;'>
                        <strong>{row['name']}</strong><br>
                        📁 {row['master_name']} | 📍 {row['site_id_code']} - {row['site_name']}<br>
                        👤 PIC: <code>{row.get('assigned_to', '-')}</code> | 📅 Deadline: {dl_str} | ⏰ {row['days_left']} hari
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Quick update
                    col_a, col_b, col_c = st.columns([1, 1, 2])
                    with col_a:
                        if st.button(f"✅ Done", key=f"done_{row['id']}"):
                            update_row('milestones', row['id'], {
                                'status': 'DONE',
                                'actual_end': today.strftime('%Y-%m-%d')
                            })
                            st.rerun()
                    with col_b:
                        if st.button(f"⏳ Delay", key=f"delay_{row['id']}"):
                            update_row('milestones', row['id'], {'status': 'DELAYED'})
                            st.rerun()
    
    # Export CSV
    st.divider()
    export_cols = ['name', 'master_name', 'site_id_code', 'site_name', 'assigned_to', 'deadline_date', 'days_left', 'category', 'status']
    csv = follow_up[[c for c in export_cols if c in follow_up.columns]]
    csv.columns = ['Task', 'Project', 'Site ID', 'Site Name', 'PIC', 'Deadline', 'Days Left', 'Category', 'Status']
    st.download_button("📥 Download Weekly Tasks CSV", csv.to_csv(index=False), f"weekly_tasks_{today}.csv", "text/csv")

if __name__ == "__main__":
    daily_task_page()
