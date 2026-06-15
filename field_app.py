import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from supabase_db import read_sheet, update_row, read_all_sheets, insert_row, generate_id, now_str, notify_update
import inspect

def inject_field_css():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%); font-family: 'Inter', sans-serif; }
        .field-header { background: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%); padding: 20px 25px; border-radius: 14px; margin-bottom: 20px; color: white; box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2); }
        .field-header h1 { margin: 0; font-size: 1.8rem; font-weight: 900; color: white; }
        .field-header p { margin: 5px 0 0 0; font-size: 0.9rem; color: #E0E7FF; }
        .status-card { background: white; padding: 15px; border-radius: 12px; border: 2px solid #DBEAFE; text-align: center; }
        .status-card .count { font-size: 2rem; font-weight: 900; color: #1F2937; }
        .status-card .label { font-size: 0.75rem; color: #6B7280; text-transform: uppercase; font-weight: 600; }
        .status-card.success { border-left: 4px solid #10B981; }
        .status-card.warning { border-left: 4px solid #F59E0B; }
        .status-card.danger { border-left: 4px solid #DC2626; }
        .status-card.info { border-left: 4px solid #3B82F6; }
        
        .kanban-column { background: white; border-radius: 12px; border: 2px solid #DBEAFE; padding: 12px; min-height: 400px; }
        .kanban-column-header { font-weight: 700; color: #1F2937; font-size: 0.9rem; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 2px solid #DBEAFE; display: flex; justify-content: space-between; }
        .kanban-card { background: #FFF; padding: 10px; border-radius: 8px; border-left: 4px solid #3B82F6; margin-bottom: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); cursor: pointer; transition: all 0.2s; }
        .kanban-card:hover { box-shadow: 0 4px 8px rgba(59,130,246,0.15); transform: translateY(-2px); }
        .section-divider { height: 2px; background: linear-gradient(90deg, transparent, #3B82F6, transparent); margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

def get_safe_numeric(val):
    try: return int(float(val)) if val else 0
    except: return 0

def field_app_page():
    inject_field_css()
    
    user = st.session_state.get('user', {})
    role = user.get('role', 'engineer')
    
    role_map = {
        'sitac': 'Sitac', 'legal': 'Legal', 'engineering': 'Engineering',
        'procurement': 'Procurement', 'project': 'Project',
        'vendor_mgmt': 'Vendor Management'
    }
    assigned_to = role_map.get(role, role)
    
    if role == 'marketing':
        from marketing_dashboard import marketing_dashboard_page
        marketing_dashboard_page(); st.stop()
    
    try:
        all_data = read_all_sheets()
        ms_df = all_data.get('milestones', pd.DataFrame())
        sites_df = all_data.get('projects', pd.DataFrame())
    except Exception as e:
        st.error(f"⚠️ Error: {e}"); return
    
    if ms_df.empty: st.info("📋 No milestones."); return
    
    ms_df = ms_df[ms_df['assigned_to'] == assigned_to].copy()
    ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    ms_df['progress'] = ms_df['progress'].apply(get_safe_numeric)
    
    total_tasks = len(ms_df)
    done_count = len(ms_df[ms_df['status'] == 'DONE'])
    ongoing_count = len(ms_df[ms_df['status'] == 'ONGOING'])
    pending_count = len(ms_df[ms_df['status'] == 'PENDING'])
    delayed_count = len(ms_df[ms_df['status'] == 'DELAYED'])
    completion_rate = (done_count/total_tasks*100) if total_tasks>0 else 0
    
    # HEADER
    st.markdown(f"""<div class="field-header"><h1>📱 Field Management App</h1><p>👷 {user.get('full_name', assigned_to)} • Role: {assigned_to}</p></div>""", unsafe_allow_html=True)
    
    # QUICK STATS
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.markdown(f'<div class="status-card info"><div class="count">{total_tasks}</div><div class="label">Total</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="status-card success"><div class="count">{done_count}</div><div class="label">Done</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="status-card warning"><div class="count">{ongoing_count}</div><div class="label">Ongoing</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="status-card"><div class="count">{pending_count}</div><div class="label">Pending</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="status-card danger"><div class="count">{delayed_count}</div><div class="label">Delayed</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="status-card"><div class="count">{completion_rate:.0f}%</div><div class="label">Completion</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # SIDEBAR
    with st.sidebar:
        st.markdown(f"### 👷 {assigned_to}")
        if st.button("🚪 Logout", use_container_width=True): st.session_state.clear(); st.session_state['logged_in']=False; st.rerun()
        st.markdown("---")
        st.markdown("### 🔍 Filter")
        if not sites_df.empty:
            master_df = all_data.get('master_projects', pd.DataFrame())
            if not master_df.empty:
                site_master_map = dict(zip(sites_df['id'], sites_df['master_project_id']))
                ms_df['master_project_id'] = ms_df['project_id'].map(site_master_map)
                sel_proj = st.selectbox("🏢 Project:", ['ALL']+sorted(master_df['project_name'].unique()), key="f_proj")
                if sel_proj!='ALL':
                    mids = master_df[master_df['project_name']==sel_proj]['id'].tolist()
                    sids = sites_df[sites_df['master_project_id'].isin(mids)]['id'].tolist()
                    ms_df = ms_df[ms_df['project_id'].isin(sids)]
            if 'pm' in sites_df.columns:
                sel_pm = st.selectbox("👤 PM:", ['ALL']+sorted(sites_df['pm'].dropna().unique()), key="f_pm")
                if sel_pm!='ALL': ms_df = ms_df[ms_df['project_id'].isin(sites_df[sites_df['pm']==sel_pm]['id'])]
            sel_site = st.selectbox("📍 Site:", ['ALL']+sorted(sites_df['site_name'].unique()), key="f_site")
            if sel_site!='ALL': ms_df = ms_df[ms_df['project_id'].isin(sites_df[sites_df['site_name']==sel_site]['id'])]
    
    site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    site_name_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    
    # ===== TABS =====
    tab1, tab2, tab3, tab4 = st.tabs(["📇 Kanban Board", "📍 Site Overview", "📊 Dashboard", "🤖 AI & Issues"])
    
    # ===== TAB 1: KANBAN BOARD (dengan tombol update di tiap task) =====
    with tab1:
        st.subheader("📇 Kanban Board — Klik task untuk update")
        
        if 'selected_task' not in st.session_state:
            st.session_state.selected_task = None
        
        kanban_statuses = ['PENDING', 'ONGOING', 'DONE', 'DELAYED']
        cols = st.columns(4)
        
        for i, status in enumerate(kanban_statuses):
            with cols[i]:
                subset = ms_df[ms_df['status'] == status]
                st.markdown(f"**{status}** ({len(subset)})")
                
                for _, task in subset.iterrows():
                    site_code = site_map.get(task['project_id'], '-')
                    deadline = task['planned_end'].strftime('%d %b') if pd.notna(task['planned_end']) else '-'
                    
                    # Tombol untuk membuka form update
                    btn_label = f"{task['name'][:25]} ({task['progress']}%)"
                    if st.button(btn_label, key=f"kanban_{task['id']}", use_container_width=True):
                        st.session_state.selected_task = task['id']
                        st.rerun()
        
        st.divider()
        
                # ===== POP-UP MODAL =====
        if st.session_state.selected_task:
            task_id = st.session_state.selected_task
            task = ms_df[ms_df['id'] == task_id].iloc[0] if task_id in ms_df['id'].values else None
            
            if task is not None:
                # Overlay background
                st.markdown("""
                <style>
                    .modal-bg { position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; }
                </style>
                <div class="modal-bg"></div>
                """, unsafe_allow_html=True)
                
                # Form di luar HTML
                with st.container():
                    st.markdown(f"### ✏️ Update: {task['name'][:40]}")
                    st.caption(f"📍 {site_map.get(task['project_id'],'-')} | 📅 {task['planned_end'].strftime('%d %b %Y') if pd.notna(task['planned_end']) else '-'}")
                    
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
                    
                    st.markdown("---")
    
    # ===== TAB 2: SITE OVERVIEW (seperti Planning) =====
    with tab2:
        st.subheader("📍 Site Overview")
        
        if not sites_df.empty:
            # Merge data site dengan milestone
            site_stats = []
            for _, site in sites_df.iterrows():
                site_ms = ms_df[ms_df['project_id'] == site['id']]
                total = len(site_ms)
                done = len(site_ms[site_ms['status']=='DONE'])
                delayed = len(site_ms[site_ms['status']=='DELAYED'])
                pct = (done/total*100) if total>0 else 0
                
                site_stats.append({
                    'Site ID': site.get('site_id','-'),
                    'Site Name': site.get('site_name','-'),
                    'PM': site.get('pm','-'),
                    'Vendor': site.get('vendor','-'),
                    'Total Tasks': total,
                    'Done': done,
                    'Delayed': delayed,
                    'Progress': f"{pct:.0f}%"
                })
            
            if site_stats:
                site_df = pd.DataFrame(site_stats)
                
                def color_row(row):
                    try:
                        p = int(row['Progress'].replace('%',''))
                        if p>=80: return ['background:#DCFCE7']*8
                        elif p>=50: return ['background:#FEF3C7']*8
                        elif row['Delayed']>0: return ['background:#FEE2E2']*8
                    except: pass
                    return ['']*8
                
                st.dataframe(site_df.style.apply(color_row, axis=1), use_container_width=True, hide_index=True)
                
                # Chart
                fig = px.bar(site_df, x='Site ID', y=[1]*len(site_df), color='Progress', 
                           color_discrete_sequence=['#10B981'], text='Site Name')
                fig.update_layout(height=300, showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
    
    # ===== TAB 3: DASHBOARD =====
    with tab3:
        st.subheader("📊 Your Performance Dashboard")
        c1, c2 = st.columns(2)
        with c1:
            if not ms_df.empty:
                fig = px.pie(values=ms_df['status'].value_counts().values, names=ms_df['status'].value_counts().index, hole=0.5, height=280)
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            if not ms_df.empty:
                fig2 = px.bar(ms_df.nlargest(10,'progress'), x='name', y='progress', color='progress', height=280)
                fig2.update_layout(showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
    
    # ===== TAB 4: AI & ISSUES =====
    with tab4:
        st.subheader("🤖 AI Forecast & Issues")
        c1, c2 = st.columns(2)
        with c1:
            if completion_rate>=80: st.success("🎯 On Track!")
            elif completion_rate>=50: st.warning("⚠️ Moderate")
            else: st.error("🔴 Needs Attention")
            st.metric("Completion", f"{completion_rate:.1f}%")
        with c2:
            delayed = ms_df[ms_df['status']=='DELAYED']
            if not delayed.empty:
                for _, t in delayed.head(5).iterrows():
                    st.markdown(f"🔴 {t['name'][:30]} — {t.get('delay_reason','?')}")

if __name__ == "__main__":
    field_app_page()
