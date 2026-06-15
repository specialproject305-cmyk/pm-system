import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
from supabase_db import read_sheet, update_row, read_all_sheets, notify_update

def get_safe_numeric(val):
    try: return int(float(val)) if val else 0
    except: return 0

def field_app_page():
    # ── USER & ROLE ──
    user = st.session_state.get('user', {})
    role = user.get('role', 'engineer')
    
    role_map = {
        'sitac': 'Sitac', 'legal': 'Legal', 'engineering': 'Engineering',
        'procurement': 'Procurement', 'project': 'Project',
        'vendor_mgmt': 'Vendor Management', 'planning': 'Planning'
    }
    assigned_to = role_map.get(role, role)
    
    # ── MARKETING REDIRECT ──
    if role == 'marketing':
        from marketing_dashboard import marketing_dashboard_page
        marketing_dashboard_page()
        st.stop()
    
    # ── LOAD DATA ──
    all_data = read_all_sheets()
    ms_df = all_data.get('milestones', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    
    if ms_df.empty:
        st.info("📋 No milestones available.")
        return
    
    # ── FILTER BY ASSIGNED_TO ──
    ms_df = ms_df[ms_df['assigned_to'] == assigned_to].copy()
    ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    ms_df['progress'] = ms_df['progress'].apply(get_safe_numeric)
    
    # ── KPI ──
    total = len(ms_df)
    done = len(ms_df[ms_df['status'] == 'DONE'])
    ongoing = len(ms_df[ms_df['status'] == 'ONGOING'])
    pending = len(ms_df[ms_df['status'] == 'PENDING'])
    delayed = len(ms_df[ms_df['status'] == 'DELAYED'])
    completion_rate = (done / total * 100) if total > 0 else 0
    
    # ── HEADER ──
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#6366F1,#8B5CF6);padding:16px 22px;border-radius:14px;margin-bottom:16px;color:white;box-shadow:0 8px 24px rgba(99,102,241,0.2);">
        <h1 style="margin:0;font-size:1.5rem;font-weight:800;">📱 Field App</h1>
        <p style="margin:4px 0 0;font-size:0.85rem;opacity:0.9;">👷 {user.get('full_name', assigned_to)} • {assigned_to}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ── 6 KPI CARDS ──
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📋 Total", total)
    c2.metric("✅ Done", done)
    c3.metric("🔄 Ongoing", ongoing)
    c4.metric("⏳ Pending", pending)
    c5.metric("🔴 Delayed", delayed)
    c6.metric("📈 Completion", f"{completion_rate:.0f}%")
    
    st.divider()
    
    # ── SIDEBAR ──
    with st.sidebar:
        st.markdown(f"### 👷 {assigned_to}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.session_state['logged_in'] = False
            st.rerun()
    
    # ── SITE MAP ──
    site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    
    # ── SESSION STATE ──
    if 'selected_task' not in st.session_state:
        st.session_state.selected_task = None
    
    # ── TABS ──
    tab1, tab2, tab3, tab4 = st.tabs(["📇 Kanban Board", "📍 Site Overview", "📊 Dashboard", "🤖 AI & Issues"])
    
    # ===== TAB 1: KANBAN =====
    with tab1:
        st.subheader("📇 Kanban Board — Klik ✏️ untuk update")
        
        statuses = ['PENDING', 'ONGOING', 'DONE', 'DELAYED']
        colors = {'PENDING': '#94A3B8', 'ONGOING': '#3B82F6', 'DONE': '#10B981', 'DELAYED': '#EF4444'}
        cols = st.columns(4)
        
        for i, status in enumerate(statuses):
            with cols[i]:
                subset = ms_df[ms_df['status'] == status]
                st.markdown(f"**{status}** ({len(subset)})")
                st.markdown("---")
                
                for _, task in subset.iterrows():
                    pct = task['progress']
                    site_code = site_map.get(task['project_id'], '-')
                    
                    st.markdown(f"""
                    <div style="background:white;padding:8px;border-radius:6px;margin:4px 0;border-left:3px solid {colors.get(status,'#6366F1')};font-size:0.8rem;">
                        <b>{task['name'][:30]}</b><br>
                        <span style="color:#64748B;">📍 {site_code} | {pct:.0f}%</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("✏️ Update", key=f"kbtn_{task['id']}"):
                        st.session_state.selected_task = task['id']
                        st.rerun()
        
        # ── POP-UP UPDATE ──
        if st.session_state.selected_task:
            task_id = st.session_state.selected_task
            task = ms_df[ms_df['id'] == task_id].iloc[0] if task_id in ms_df['id'].values else None
            
            if task is not None:
                st.markdown("---")
                st.markdown(f"### ✏️ Update: {task['name'][:40]}")
                st.caption(f"📍 {site_map.get(task['project_id'],'-')}")
                
                new_status = st.selectbox("Status", ['PENDING','ONGOING','DONE','DELAYED'],
                    index=['PENDING','ONGOING','DONE','DELAYED'].index(task.get('status','PENDING')),
                    key=f"st_{task_id}")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_progress = st.slider("Progress %", 0, 100, int(task.get('progress',0)), key=f"pr_{task_id}")
                    as_d = pd.to_datetime(task.get('actual_start')).date() if pd.notna(task.get('actual_start')) else None
                    new_as = st.date_input("Actual Start", value=as_d, key=f"as_{task_id}")
                with col2:
                    ae_d = pd.to_datetime(task.get('actual_end')).date() if pd.notna(task.get('actual_end')) else None
                    new_ae = st.date_input("Actual End", value=ae_d, key=f"ae_{task_id}")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Simpan", type="primary", use_container_width=True, key=f"save_{task_id}"):
                        update_data = {'status': new_status, 'progress': str(new_progress)}
                        if new_as: update_data['actual_start'] = new_as.strftime('%Y-%m-%d')
                        if new_ae: update_data['actual_end'] = new_ae.strftime('%Y-%m-%d')
                        if new_status == 'DONE' and not new_ae: update_data['actual_end'] = date.today().strftime('%Y-%m-%d')
                        update_row('milestones', task_id, update_data)
                        notify_update(assigned_to, new_status, task['name'], site_map.get(task['project_id'],'-'))
                        st.cache_data.clear()
                        st.session_state.selected_task = None
                        st.rerun()
                with col_btn2:
                    if st.button("❌ Cancel", use_container_width=True, key=f"cancel_{task_id}"):
                        st.session_state.selected_task = None
                        st.rerun()
    
    # ===== TAB 2: SITE OVERVIEW =====
    with tab2:
        st.subheader("📍 Site Overview")
        if not sites_df.empty:
            display = sites_df[['site_id','site_name','pm','vendor','status','progress']].head(20)
            st.dataframe(display, use_container_width=True, hide_index=True)
    
    # ===== TAB 3: DASHBOARD =====
    with tab3:
        st.subheader("📊 Performance")
        if not ms_df.empty:
            fig = px.pie(values=ms_df['status'].value_counts().values, names=ms_df['status'].value_counts().index, hole=0.5, height=280)
            st.plotly_chart(fig, use_container_width=True)
        st.metric("Completion", f"{completion_rate:.1f}%")
    
    # ===== TAB 4: AI & ISSUES =====
    with tab4:
        st.subheader("🤖 AI & Issues")
        if completion_rate >= 80: st.success("🎯 On Track!")
        elif completion_rate >= 50: st.warning("⚠️ Moderate")
        else: st.error("🔴 Needs Attention")
        
        delayed_tasks = ms_df[ms_df['status'] == 'DELAYED']
        if not delayed_tasks.empty:
            for _, t in delayed_tasks.head(5).iterrows():
                st.markdown(f"🔴 {t['name'][:30]} — {t.get('delay_reason','?')}")

if __name__ == "__main__":
    field_app_page()
