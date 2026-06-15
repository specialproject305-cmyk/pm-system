import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
from supabase_db import read_sheet, update_row, read_all_sheets, insert_row, generate_id, now_str, notify_update
import inspect

def inject_field_css():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%); font-family: 'Inter', sans-serif; }
        .field-header { background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%); padding: 16px 22px; border-radius: 14px; margin-bottom: 16px; color: white; box-shadow: 0 8px 24px rgba(99,102,241,0.2); }
        .field-header h1 { margin: 0; font-size: 1.5rem; font-weight: 800; }
        .field-header p { margin: 4px 0 0 0; font-size: 0.85rem; opacity: 0.9; }
        
        .kpi-card { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-radius: 12px; padding: 12px 8px; text-align: center; border: 1px solid rgba(0,0,0,0.06); box-shadow: 0 4px 15px rgba(0,0,0,0.04); }
        .kpi-card .val { font-size: 1.5rem; font-weight: 800; color: #6366F1; line-height: 1; }
        .kpi-card .lbl { font-size: 0.65rem; color: #64748B; text-transform: uppercase; font-weight: 600; margin-top: 3px; }
        .kpi-card.green { border-left: 3px solid #10B981; }
        .kpi-card.yellow { border-left: 3px solid #F59E0B; }
        .kpi-card.red { border-left: 3px solid #EF4444; }
        .kpi-card.blue { border-left: 3px solid #6366F1; }
        
        .kanban-column { background: rgba(255,255,255,0.8); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border-radius: 12px; border: 1px solid rgba(0,0,0,0.06); padding: 12px; min-height: 400px; box-shadow: 0 4px 15px rgba(0,0,0,0.04); }
        .kanban-column-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 8px; margin-bottom: 8px; border-bottom: 2px solid #E2E8F0; font-weight: 700; font-size: 0.8rem; color: #1E293B; text-transform: uppercase; }
        .kanban-count { background: #6366F1; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 700; }
        .kanban-card { background: white; border-radius: 8px; padding: 10px; margin-bottom: 6px; border-left: 4px solid #6366F1; box-shadow: 0 2px 6px rgba(0,0,0,0.04); cursor: pointer; transition: all 0.2s; font-size: 0.8rem; }
        .kanban-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.08); }
        .kanban-card.pending { border-left-color: #94A3B8; }
        .kanban-card.ongoing { border-left-color: #3B82F6; }
        .kanban-card.done { border-left-color: #10B981; }
        .kanban-card.delayed { border-left-color: #EF4444; }
        .kanban-card .card-title { font-weight: 600; color: #1E293B; margin-bottom: 3px; }
        .kanban-card .card-meta { font-size: 0.7rem; color: #64748B; }
        .kanban-card .card-progress { height: 4px; background: #E2E8F0; border-radius: 2px; margin-top: 4px; overflow: hidden; }
        .kanban-card .card-progress-bar { height: 100%; border-radius: 2px; }
        
        .section-divider { height: 1px; background: linear-gradient(90deg, transparent, #E2E8F0, transparent); margin: 14px 0; }
        
        /* MODAL POP-UP */
        div[data-testid="stVerticalBlock"] > div:has(.modal-container) {
            position: fixed !important; top: 0 !important; left: 0 !important;
            width: 100vw !important; height: 100vh !important;
            background: rgba(0,0,0,0.5) !important; z-index: 9999 !important;
            display: flex !important; align-items: center !important; justify-content: center !important;
        }
        .modal-container {
            background: white !important; border-radius: 16px !important;
            padding: 24px !important; width: 480px !important; max-width: 90vw !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3) !important;
        }
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
    
    all_data = read_all_sheets()
    ms_df = all_data.get('milestones', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    
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
    st.markdown(f"""<div class="field-header"><h1>📱 Field App</h1><p>👷 {user.get('full_name', assigned_to)} • {assigned_to}</p></div>""", unsafe_allow_html=True)
    
    # 6 KPI CARDS
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.markdown(f'<div class="kpi-card blue"><div class="val">{total_tasks}</div><div class="lbl">Total</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card green"><div class="val">{done_count}</div><div class="lbl">Done</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card yellow"><div class="val">{ongoing_count}</div><div class="lbl">Ongoing</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card"><div class="val">{pending_count}</div><div class="lbl">Pending</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="kpi-card red"><div class="val">{delayed_count}</div><div class="lbl">Delayed</div></div>', unsafe_allow_html=True)
    c6.markdown(f'<div class="kpi-card blue"><div class="val">{completion_rate:.0f}%</div><div class="lbl">Completion</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # SIDEBAR
    with st.sidebar:
        st.markdown(f"### 👷 {assigned_to}")
        if st.button("🚪 Logout", use_container_width=True): st.session_state.clear(); st.session_state['logged_in']=False; st.rerun()
    
    site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    
    # TABS
    tab1, tab2, tab3, tab4 = st.tabs(["📇 Kanban Board", "📍 Site Overview", "📊 Dashboard", "🤖 AI & Issues"])
    
    if 'selected_task' not in st.session_state:
        st.session_state.selected_task = None
    
    # ===== TAB 1: KANBAN BOARD =====
    with tab1:
        st.subheader("📇 Kanban Board — Klik task untuk update")
        
        kanban_statuses = ['PENDING', 'ONGOING', 'DONE', 'DELAYED']
        css_class = {'PENDING':'pending', 'ONGOING':'ongoing', 'DONE':'done', 'DELAYED':'delayed'}
        colors = {'PENDING':'#94A3B8', 'ONGOING':'#3B82F6', 'DONE':'#10B981', 'DELAYED':'#EF4444'}
        cols = st.columns(4)
        
        for i, status in enumerate(kanban_statuses):
            with cols[i]:
                subset = ms_df[ms_df['status'] == status]
                st.markdown(f"""
                <div class="kanban-column">
                    <div class="kanban-column-header"><span>{status}</span><span class="kanban-count">{len(subset)}</span></div>
                """, unsafe_allow_html=True)
                
                for _, task in subset.iterrows():
                    pct = task['progress']
                    st.markdown(f"""
                    <div class="kanban-card {css_class.get(status,'')}">
                        <div class="card-title">{task['name'][:35]}</div>
                        <div class="card-meta">📍 {site_map.get(task['project_id'],'-')} | 👷 {task.get('assigned_to','-')}</div>
                        <div class="card-progress"><div class="card-progress-bar" style="width:{pct}%; background:{colors.get(status,'#6366F1')};"></div></div>
                        <div class="card-meta" style="margin-top:3px;">{pct:.0f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("✏️ Update", key=f"kbtn_{task['id']}"):
                        st.session_state.selected_task = task['id']
                        st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # ===== POP-UP MODAL =====
        if st.session_state.selected_task:
            task_id = st.session_state.selected_task
            task = ms_df[ms_df['id'] == task_id].iloc[0] if task_id in ms_df['id'].values else None
            
            if task is not None:
                st.markdown('<div class="modal-container">', unsafe_allow_html=True)
                st.markdown(f"### ✏️ Update: {task['name'][:40]}")
                st.caption(f"📍 {site_map.get(task['project_id'],'-')}")
                
                with st.form(f"modal_{task_id}", clear_on_submit=False):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_status = st.selectbox("Status", ['PENDING','ONGOING','DONE','DELAYED'],
                            index=['PENDING','ONGOING','DONE','DELAYED'].index(task.get('status','PENDING')))
                        new_progress = st.slider("Progress %", 0, 100, int(task.get('progress',0)))
                    with c2:
                        as_d = pd.to_datetime(task.get('actual_start')).date() if pd.notna(task.get('actual_start')) else None
                        new_as = st.date_input("Actual Start", value=as_d)
                        ae_d = pd.to_datetime(task.get('actual_end')).date() if pd.notna(task.get('actual_end')) else None
                        new_ae = st.date_input("Actual End", value=ae_d)
                    
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                            update_data = {'status': new_status, 'progress': str(new_progress)}
                            if new_as: update_data['actual_start'] = new_as.strftime('%Y-%m-%d')
                            if new_ae: update_data['actual_end'] = new_ae.strftime('%Y-%m-%d')
                            if new_status == 'DONE' and not new_ae: update_data['actual_end'] = date.today().strftime('%Y-%m-%d')
                            update_row('milestones', task_id, update_data)
                            st.cache_data.clear(); st.session_state.selected_task = None; st.rerun()
                    with b2:
                        if st.form_submit_button("❌ Cancel", use_container_width=True):
                            st.session_state.selected_task = None; st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
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
        if completion_rate>=80: st.success("🎯 On Track!")
        elif completion_rate>=50: st.warning("⚠️ Moderate")
        else: st.error("🔴 Needs Attention")
        
        delayed = ms_df[ms_df['status']=='DELAYED']
        if not delayed.empty:
            for _, t in delayed.head(5).iterrows():
                st.markdown(f"🔴 {t['name'][:30]} — {t.get('delay_reason','?')}")

if __name__ == "__main__":
    field_app_page()
