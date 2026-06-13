import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from supabase_db import read_sheet, update_row, read_all_sheets, insert_row, generate_id, now_str, notify_update

# ─────────────────────────────────────────────────────────────
# 🎨 LIGHT PROFESSIONAL THEME FOR FIELD APP
# ─────────────────────────────────────────────────────────────
def inject_field_css():
    st.markdown("""
    <style>
        /* === BASE STYLING === */
        .stApp { 
            background: linear-gradient(135deg, #F8FBFF 0%, #F0F7FF 100%);
            color: #1F2937; 
            font-family: 'Segoe UI', 'Inter', sans-serif;
        }
        
        /* === HEADER === */
        .field-header {
            background: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%);
            padding: 20px 25px;
            border-radius: 14px;
            border: 2px solid #1E40AF;
            margin-bottom: 20px;
            color: white;
            box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2);
        }
        
        .field-header h1 {
            margin: 0;
            font-size: 1.8rem;
            font-weight: 900;
            color: white;
        }
        
        .field-header p {
            margin: 5px 0 0 0;
            font-size: 0.9rem;
            color: #E0E7FF;
        }
        
        /* === STATUS CARDS === */
        .status-card {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F9FF 100%);
            padding: 15px;
            border-radius: 12px;
            border: 2px solid #DBEAFE;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .status-card:hover {
            border-color: #3B82F6;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
            transform: translateY(-2px);
        }
        
        .status-card .count {
            font-size: 2.2rem;
            font-weight: 900;
            color: #1F2937;
            line-height: 1;
        }
        
        .status-card .label {
            font-size: 0.8rem;
            color: #6B7280;
            text-transform: uppercase;
            font-weight: 600;
            margin-top: 8px;
            letter-spacing: 0.5px;
        }
        
        .status-card.success { border-left: 4px solid #10B981; }
        .status-card.warning { border-left: 4px solid #FF8C00; }
        .status-card.danger { border-left: 4px solid #DC2626; }
        .status-card.info { border-left: 4px solid #3B82F6; }
        
        /* === TASK CARD === */
        .task-card {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F9FF 100%);
            padding: 16px;
            border-radius: 12px;
            border: 2px solid #DBEAFE;
            margin-bottom: 12px;
            transition: all 0.3s ease;
        }
        
        .task-card:hover {
            border-color: #3B82F6;
            box-shadow: 0 6px 16px rgba(59, 130, 246, 0.15);
            transform: translateY(-2px);
        }
        
        .task-card-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 12px;
        }
        
        .task-name {
            font-size: 1.1rem;
            font-weight: 700;
            color: #1F2937;
        }
        
        .task-status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badge-pending { background: rgba(156, 163, 175, 0.15); color: #4B5563; }
        .badge-ongoing { background: rgba(255, 140, 0, 0.15); color: #D97706; }
        .badge-done { background: rgba(16, 185, 129, 0.15); color: #047857; }
        .badge-delayed { background: rgba(220, 38, 38, 0.15); color: #991B1B; }
        
        .task-meta {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            font-size: 0.85rem;
            color: #6B7280;
            margin-bottom: 12px;
        }
        
        .task-meta-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .task-progress {
            background: #E5E7EB;
            border-radius: 8px;
            height: 6px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .task-progress-bar {
            background: linear-gradient(90deg, #3B82F6, #0EA5E9);
            height: 100%;
            border-radius: 8px;
            transition: width 0.3s ease;
        }
        
        /* === KANBAN COLUMN === */
        .kanban-column {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F9FF 100%);
            border-radius: 12px;
            border: 2px solid #DBEAFE;
            padding: 15px;
            min-height: 400px;
        }
        
        .kanban-column-header {
            font-size: 0.95rem;
            font-weight: 700;
            color: #1F2937;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 2px solid #DBEAFE;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .kanban-count {
            background: #F0F9FF;
            border: 1px solid #DBEAFE;
            color: #1E40AF;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .kanban-card {
            background: #FFFFFF;
            padding: 10px;
            border-radius: 8px;
            border-left: 3px solid #3B82F6;
            margin-bottom: 8px;
            font-size: 0.9rem;
            color: #1F2937;
            font-weight: 500;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }
        
        .kanban-card:hover {
            box-shadow: 0 4px 8px rgba(59, 130, 246, 0.1);
            transform: translateY(-1px);
        }
        
        /* === METRICS DISPLAY === */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        
        .metric-box {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F9FF 100%);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #DBEAFE;
        }
        
        .metric-value {
            font-size: 1.8rem;
            font-weight: 900;
            color: #1F2937;
            line-height: 1;
        }
        
        .metric-label {
            font-size: 0.8rem;
            color: #6B7280;
            font-weight: 600;
            margin-top: 5px;
            text-transform: uppercase;
        }
        
        /* === DIVIDER === */
        .section-divider {
            height: 2px;
            background: linear-gradient(90deg, transparent, #3B82F6, transparent);
            margin: 20px 0;
            border: none;
        }
        
        /* === INFO BOX === */
        .info-box {
            background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
            border-radius: 10px;
            padding: 12px;
            border-left: 4px solid #3B82F6;
            color: #1E40AF;
            font-size: 0.9rem;
        }
        
        .success-box {
            background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
            border-left-color: #10B981;
            color: #047857;
        }
        
        .warning-box {
            background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
            border-left-color: #FF8C00;
            color: #D97706;
        }
        
        .danger-box {
            background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
            border-left-color: #DC2626;
            color: #991B1B;
        }
    </style>
    """, unsafe_allow_html=True)

def get_safe_numeric(val):
    """Safely convert to numeric"""
    try:
        return int(float(val)) if val else 0
    except:
        return 0

def field_app_page():
    inject_field_css()
    
    # ═══════════════════════════════════════
    # AUTO-FILTER BY ROLE
    # ═══════════════════════════════════════
    user = st.session_state.get('user', {})
    role = user.get('role', 'engineer')
    
    role_map = {
        'sitac': 'Sitac', 'legal': 'Legal', 'engineering': 'Engineering',
        'procurement': 'Procurement', 'project': 'Project',
        'vendor_mgmt': 'Vendor Management'
    }
    assigned_to = role_map.get(role, role)
        
        # Jika role marketing, tampilkan Marketing Dashboard
    if role == 'marketing':
        from marketing_dashboard import marketing_dashboard_page
        marketing_dashboard_page()
        st.stop()
    
    try:
        with st.spinner("🔄 Loading data..."):
            all_data = read_all_sheets()
        ms_df = all_data.get('milestones', pd.DataFrame())
        sites_df = all_data.get('projects', pd.DataFrame())
        messages = all_data.get('chat_messages', pd.DataFrame())
    except Exception as e:
        st.error(f"⚠️ Error loading data: {e}")
        return
    
    if ms_df.empty:
        st.info("📋 No milestones available.")
        return
    
    # Filter task hanya untuk PIC ini
    ms_df = ms_df[ms_df['assigned_to'] == assigned_to].copy()
    ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    ms_df['actual_start'] = pd.to_datetime(ms_df['actual_start'], errors='coerce')
    ms_df['actual_end'] = pd.to_datetime(ms_df['actual_end'], errors='coerce')
    ms_df['progress'] = ms_df['progress'].apply(lambda x: get_safe_numeric(x))
    
    # ═══════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════
    st.markdown(f"""
    <div class="field-header">
        <h1>📱 Field Management App</h1>
        <p>👷 {user.get('full_name', assigned_to)} • Role: {assigned_to}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════
    # QUICK STATS
    # ═══════════════════════════════════════
    total_tasks = len(ms_df)
    done_count = len(ms_df[ms_df['status'] == 'DONE'])
    ongoing_count = len(ms_df[ms_df['status'] == 'ONGOING'])
    pending_count = len(ms_df[ms_df['status'] == 'PENDING'])
    delayed_count = len(ms_df[ms_df['status'] == 'DELAYED'])
    overdue_count = len(ms_df[ms_df['planned_end'].dt.date < date.today()])
    avg_progress = ms_df['progress'].mean() if total_tasks > 0 else 0
    completion_rate = (done_count / total_tasks * 100) if total_tasks > 0 else 0
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown(f"""
        <div class="status-card info">
            <div class="count">{total_tasks}</div>
            <div class="label">Total Tasks</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="status-card success">
            <div class="count">{done_count}</div>
            <div class="label">Completed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="status-card warning">
            <div class="count">{ongoing_count}</div>
            <div class="label">In Progress</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="status-card">
            <div class="count">{pending_count}</div>
            <div class="label">Pending</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="status-card danger">
            <div class="count">{delayed_count}</div>
            <div class="label">Delayed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div class="status-card">
            <div class="count">{completion_rate:.0f}%</div>
            <div class="label">Completion</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # ═══════════════════════════════════════
    # SIDEBAR
    # ═══════════════════════════════════════
        with st.sidebar:
        st.markdown("---")
        st.markdown(f"### 👷 {assigned_to}")
        st.caption(f"👤 {user.get('full_name', 'User')}")
        
        if st.button("🚪 Logout", use_container_width=True, key="field_logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state['logged_in'] = False
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🔍 Filter Tugas")
        
        # Filter by Project
        if not sites_df.empty:
            # Gabung dengan master_projects
            master_df = all_data.get('master_projects', pd.DataFrame())
            if not master_df.empty:
                site_master_map = dict(zip(sites_df['id'], sites_df['master_project_id']))
                ms_df['master_project_id'] = ms_df['project_id'].map(site_master_map)
                project_options = ['ALL'] + sorted(master_df['project_name'].unique().tolist())
                sel_project = st.selectbox("🏢 Project:", project_options, key="field_proj_filter")
                if sel_project != 'ALL':
                    valid_master_ids = master_df[master_df['project_name'] == sel_project]['id'].tolist()
                    valid_site_ids = sites_df[sites_df['master_project_id'].isin(valid_master_ids)]['id'].tolist()
                    ms_df = ms_df[ms_df['project_id'].isin(valid_site_ids)]
        
        # Filter by PM
        if not sites_df.empty and 'pm' in sites_df.columns:
            pm_options = ['ALL'] + sorted(sites_df['pm'].dropna().unique().tolist())
            sel_pm = st.selectbox("👤 PM:", pm_options, key="field_pm_filter")
            if sel_pm != 'ALL':
                valid_site_ids = sites_df[sites_df['pm'] == sel_pm]['id'].tolist()
                ms_df = ms_df[ms_df['project_id'].isin(valid_site_ids)]
        
        # Filter by Site Name
        if not sites_df.empty:
            site_options = ['ALL'] + sorted(sites_df['site_name'].unique().tolist())
            sel_site = st.selectbox("📍 Site:", site_options, key="field_site_filter")
            if sel_site != 'ALL':
                valid_site_ids = sites_df[sites_df['site_name'] == sel_site]['id'].tolist()
                ms_df = ms_df[ms_df['project_id'].isin(valid_site_ids)]
        
        # Recalculate stats after filter
        total_tasks = len(ms_df)
        done_count = len(ms_df[ms_df['status'] == 'DONE'])
        overdue_count = len(ms_df[ms_df['planned_end'] < pd.Timestamp(date.today())])
        avg_progress = ms_df['progress'].apply(get_safe_numeric).mean() if total_tasks > 0 else 0
        
        st.markdown("---")
        st.markdown("### 📊 Quick Summary")
        st.metric("📋 Your Tasks", total_tasks)
        st.metric("✅ Completed", f"{done_count}/{total_tasks}")
        st.metric("🔴 Overdue", overdue_count)
        st.metric("📈 Avg Progress", f"{avg_progress:.0f}%")
    
    # ═══════════════════════════════════════
    # MAIN TABS
    # ═══════════════════════════════════════
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Update Tasks",
        "📊 Dashboard", 
        "📇 Kanban Board",
        "🤖 AI Forecast",
        "🔍 Issues"
    ])
    
    site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    site_name_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    
    # ===== TAB 1: UPDATE TASKS =====
    with tab1:
        st.subheader("📋 Update Your Tasks")
        
        if ms_df.empty:
            st.info("✅ No tasks assigned to you right now!")
        else:
            # Sort by priority: delayed first, then by deadline
            sort_order = {'DELAYED': 0, 'CRITICAL': 1, 'ONGOING': 2, 'PENDING': 3, 'DONE': 4}
            ms_df['sort_key'] = ms_df['status'].map(lambda x: sort_order.get(x, 5))
            ms_sorted = ms_df.sort_values(['sort_key', 'planned_end']).drop('sort_key', axis=1)
            
            for _, task in ms_sorted.iterrows():
                site_code = site_map.get(task['project_id'], '-')
                site_name = site_name_map.get(task['project_id'], '-')
                deadline = task['planned_end'].strftime('%d %b %Y') if pd.notna(task['planned_end']) else '-'
                days_left = (task['planned_end'].date() - date.today()).days if pd.notna(task['planned_end']) else 999
                
                # Determine status styling
                status_badge_class = {
                    'PENDING': 'badge-pending',
                    'ONGOING': 'badge-ongoing',
                    'DONE': 'badge-done',
                    'DELAYED': 'badge-delayed'
                }.get(task.get('status', 'PENDING'), 'badge-pending')
                
                progress_pct = task['progress']
                progress_color = '#10B981' if task['status'] == 'DONE' else '#3B82F6'
                
                # Info box color
                if days_left < 0:
                    info_class = 'danger-box'
                    urgency = f"🔴 {abs(days_left)} days overdue"
                elif days_left == 0:
                    info_class = 'warning-box'
                    urgency = f"⚠️ Due today"
                elif days_left <= 3:
                    info_class = 'warning-box'
                    urgency = f"⚠️ {days_left} days left"
                else:
                    info_class = 'success-box'
                    urgency = f"✅ {days_left} days left"
                
                st.markdown(f"""
                <div class="task-card">
                    <div class="task-card-header">
                        <div class="task-name">{task['name']}</div>
                        <span class="task-status-badge {status_badge_class}">{task.get('status', '?')}</span>
                    </div>
                    <div class="task-meta">
                        <div class="task-meta-item">📍 {site_code} - {site_name}</div>
                        <div class="task-meta-item">📅 {deadline}</div>
                        <div class="task-meta-item">⏱️ {urgency}</div>
                    </div>
                    <div class="task-progress">
                        <div class="task-progress-bar" style="width: {progress_pct}%; background-color: {progress_color};"></div>
                    </div>
                    <div class="info-box {info_class}">Progress: {progress_pct}% • Status: {task.get('status', '?')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.form(f"upd_{task['id']}", clear_on_submit=False):
                    c1, c2, c3 = st.columns(3)
                    
                    with c1:
                        statuses = ['PENDING', 'ONGOING', 'DONE', 'DELAYED']
                        cur_s = task.get('status', 'PENDING')
                        s_idx = statuses.index(cur_s) if cur_s in statuses else 0
                        new_status = st.selectbox("Status", statuses, index=s_idx, key=f"st_{task['id']}")
                    
                    with c2:
                        new_progress = st.slider("Progress %", 0, 100, task['progress'], key=f"pr_{task['id']}")
                    
                    with c3:
                        new_note = st.text_input("Note", value="", placeholder="Add note", key=f"note_{task['id']}")
                    
                    col_dates1, col_dates2 = st.columns(2)
                    
                    with col_dates1:
                        as_d = task['actual_start'].date() if pd.notna(task['actual_start']) else None
                        new_as = st.date_input("Actual Start", value=as_d, key=f"as_{task['id']}")
                    
                    with col_dates2:
                        ae_d = task['actual_end'].date() if pd.notna(task['actual_end']) else None
                        new_ae = st.date_input("Actual End", value=ae_d, key=f"ae_{task['id']}")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.form_submit_button("💾 Save Update", use_container_width=True):
                            update_data = {'status': new_status, 'progress': str(new_progress)}
                            if new_as:
                                update_data['actual_start'] = new_as.strftime('%Y-%m-%d')
                            if new_ae:
                                update_data['actual_end'] = new_ae.strftime('%Y-%m-%d')
                            if new_status == 'DONE' and not new_ae:
                                update_data['actual_end'] = date.today().strftime('%Y-%m-%d')
                            if new_note:
                                update_data['notes'] = new_note
                            
                            update_row('milestones', task['id'], update_data)
                            st.success(f"✅ {task['name']} updated successfully!")
                                                        # Kirim notifikasi
                            site_code = site_map.get(task['project_id'], '-')
                            notify_update(assigned_to, new_status, task['name'], site_code)
                            st.cache_data.clear()
                            st.rerun()
                    
                    with col_btn2:
                        if st.form_submit_button("📌 Mark as Done", use_container_width=True):
                            update_data = {
                                'status': 'DONE',
                                'progress': '100',
                                'actual_end': date.today().strftime('%Y-%m-%d')
                            }
                            update_row('milestones', task['id'], update_data)
                            st.success(f"🎉 {task['name']} completed!")
                            st.cache_data.clear()
                            st.rerun()
                
                st.markdown("---")
    
    # ===== TAB 2: DASHBOARD =====
    with tab2:
        st.subheader("📊 Your Performance Dashboard")
        
        col_metrics1, col_metrics2 = st.columns(2)
        
        with col_metrics1:
            st.markdown('<h4 style="color: #1F2937; margin-top: 0;">📈 Task Status Overview</h4>', unsafe_allow_html=True)
            if not ms_df.empty:
                status_data = ms_df['status'].value_counts()
                fig = px.pie(
                    values=status_data.values,
                    names=status_data.index,
                    hole=0.6,
                    color_discrete_map={
                        'DONE': '#10B981',
                        'ONGOING': '#FF8C00',
                        'PENDING': '#9CA3AF',
                        'DELAYED': '#DC2626'
                    }
                )
                fig.update_layout(
                    height=300,
                    margin=dict(t=0, b=0, l=0, r=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#1F2937', size=10),
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col_metrics2:
            st.markdown('<h4 style="color: #1F2937; margin-top: 0;">📊 Progress Comparison</h4>', unsafe_allow_html=True)
            if not ms_df.empty:
                ms_sorted = ms_df.sort_values('progress', ascending=False).head(10)
                fig = px.bar(
                    ms_sorted,
                    x='name',
                    y='progress',
                    color='progress',
                    color_continuous_scale=['#DC2626', '#FF8C00', '#3B82F6', '#10B981'],
                    labels={'progress': 'Progress %', 'name': 'Task'}
                )
                fig.update_layout(
                    height=300,
                    margin=dict(t=0, b=0, l=0, r=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#1F2937', size=9),
                    xaxis_title="",
                    yaxis_title="Progress %",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        col_metrics3, col_metrics4 = st.columns(2)
        
        with col_metrics3:
            st.markdown('<h4 style="color: #1F2937;">⏱️ Completion Timeline</h4>', unsafe_allow_html=True)
            if not ms_df.empty and 'actual_end' in ms_df.columns:
                completed = ms_df[ms_df['status'] == 'DONE'].copy()
                if not completed.empty:
                    completed['actual_end'] = pd.to_datetime(completed['actual_end'], errors='coerce')
                    completed = completed[pd.notna(completed['actual_end'])].sort_values('actual_end')
                    if not completed.empty:
                        fig = px.line(
                            completed,
                            x='actual_end',
                            y=range(1, len(completed) + 1),
                            markers=True,
                            labels={'actual_end': 'Date', 'y': 'Cumulative Tasks'}
                        )
                        fig.update_layout(
                            height=250,
                            margin=dict(t=0, b=0, l=0, r=0),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#1F2937'),
                            showlegend=False,
                            xaxis_title="",
                            yaxis_title="Completed Tasks"
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        with col_metrics4:
            st.markdown('<h4 style="color: #1F2937;">📋 Metrics Summary</h4>', unsafe_allow_html=True)
            metrics_col1, metrics_col2 = st.columns(2)
            
            with metrics_col1:
                st.metric("Total Tasks", total_tasks)
                st.metric("On Time", total_tasks - overdue_count)
            
            with metrics_col2:
                st.metric("Completion Rate", f"{completion_rate:.1f}%")
                st.metric("Avg Progress", f"{avg_progress:.0f}%")
    
    # ===== TAB 3: KANBAN BOARD =====
    with tab3:
        import inspect  # Taruh di sini atau di baris paling atas file Anda
        st.subheader("📇 Kanban Board View")
        
        kanban_statuses = ['PENDING', 'ONGOING', 'DONE', 'DELAYED']
        kanban_cols = st.columns(4)
        
        for col_idx, status in enumerate(kanban_statuses):
            with kanban_cols[col_idx]:
                subset = ms_df[ms_df['status'] == status]
                count = len(subset)
                
                # Gunakan inspect.cleandoc agar spasi kiri bawaan editor tidak ikut masuk ke string HTML
                header_html = inspect.cleandoc(f"""
                <div class="kanban-column">
                    <div class="kanban-column-header" style="margin-bottom: 12px;">
                        <span style="font-weight: 700; color: #1F2937;">{status}</span>
                        <span class="kanban-count" style="background: #3B82F6; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.8rem; margin-left: 5px; font-weight: bold;">{count}</span>
                    </div>
                    <div class="kanban-cards-container">
                """)
                
                cards_html = ""
                for _, task in subset.iterrows():
                    cards_html += inspect.cleandoc(f"""
                    <div class="kanban-card" style="background: #FFFFFF; padding: 12px; border-radius: 8px; border-left: 4px solid #3B82F6; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-top: 1px solid #E5E7EB; border-right: 1px solid #E5E7EB; border-bottom: 1px solid #E5E7EB;">
                        <div style="font-weight: 600; color: #1F2937; font-size: 0.9rem;">{task["name"]}</div>
                        <div style="font-size: 0.8rem; color: #6B7280; margin-top: 4px;">Prog: {task["progress"]}%</div>
                    </div>
                    """) + "\n"
                
                footer_html = "</div>\n</div>"
                
                # Gabungkan seluruh string yang sudah bersih dari spasi liar di awal baris
                kolom_html = header_html + "\n" + cards_html + footer_html
                
                # Render total html ke streamlit
                st.markdown(kolom_html, unsafe_allow_html=True)
    
    # ===== TAB 4: AI FORECAST =====
    with tab4:
        st.subheader("🤖 AI Forecast & Insights")
        
        col_forecast1, col_forecast2 = st.columns(2)
        
        with col_forecast1:
            st.markdown('<h4 style="color: #1F2937;">📊 Completion Forecast</h4>', unsafe_allow_html=True)
            
            if completion_rate >= 80:
                forecast = "🎯 **On Track** - You're performing excellently!"
                forecast_color = "#10B981"
            elif completion_rate >= 50:
                forecast = "⚠️ **Moderate Progress** - Keep pushing to meet targets"
                forecast_color = "#FF8C00"
            else:
                forecast = "🔴 **Needs Attention** - Consider accelerating progress"
                forecast_color = "#DC2626"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%); 
                        border-radius: 10px; padding: 15px; border-left: 4px solid {forecast_color}; color: #1E40AF;">
                {forecast}
            </div>
            """, unsafe_allow_html=True)
            
            st.metric("Current Completion", f"{completion_rate:.1f}%")
            
            if total_tasks > 0 and done_count < total_tasks:
                remaining_tasks = total_tasks - done_count
                days_until_deadline = (ms_df[ms_df['status'] != 'DONE']['planned_end'].min() - pd.Timestamp(date.today())).days
                if days_until_deadline > 0:
                    tasks_per_day = remaining_tasks / days_until_deadline
                    st.info(f"📈 To finish on time: {tasks_per_day:.1f} tasks/day needed")
        
        with col_forecast2:
            st.markdown('<h4 style="color: #1F2937;">⚠️ Risk Analysis</h4>', unsafe_allow_html=True)
            
            high_risk = ms_df[(ms_df['status'].isin(['DELAYED', 'PENDING'])) & (ms_df['progress'] < 30)]
            medium_risk = ms_df[(ms_df['status'] == 'ONGOING') & (ms_df['progress'] < 50)]
            
            risk_data = {
                'Risk Level': ['🔴 High Risk', '🟡 Medium Risk', '🟢 Low Risk'],
                'Count': [len(high_risk), len(medium_risk), total_tasks - len(high_risk) - len(medium_risk)]
            }
            risk_df = pd.DataFrame(risk_data)
            
            fig = px.bar(
                risk_df,
                x='Risk Level',
                y='Count',
                color='Risk Level',
                color_discrete_map={
                    '🔴 High Risk': '#DC2626',
                    '🟡 Medium Risk': '#FF8C00',
                    '🟢 Low Risk': '#10B981'
                }
            )
            fig.update_layout(
                height=250,
                margin=dict(t=0, b=0, l=0, r=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#1F2937'),
                showlegend=False,
                xaxis_title="",
                yaxis_title="Tasks"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # ===== TAB 5: ISSUES & RCA =====
    with tab5:
        st.subheader("🔍 Issues & Root Cause Analysis")
        
        delayed = ms_df[ms_df['status'] == 'DELAYED'].sort_values('planned_end')
        
        if delayed.empty:
            st.success("✅ No delayed tasks - everything is on track!")
        else:
            for _, task in delayed.iterrows():
                site_code = site_map.get(task['project_id'], '-')
                days_late = (date.today() - task['planned_end'].date()).days
                
                st.markdown(f"""
                <div class="info-box danger-box">
                    <strong>❌ {task['name']}</strong><br>
                    📍 {site_code} | ⏰ {days_late} days overdue<br>
                    📝 Reason: {task.get('delay_reason', 'Not specified')}<br>
                    💡 Mitigation: {task.get('mitigation', 'To be defined')}
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"📋 Details - {task['name']}", expanded=False):
                    detail_col1, detail_col2 = st.columns(2)
                    
                    with detail_col1:
                        st.write(f"**Status**: {task['status']}")
                        st.write(f"**Progress**: {task['progress']}%")
                        st.write(f"**Site**: {site_code}")
                    
                    with detail_col2:
                        st.write(f"**Planned End**: {task['planned_end'].strftime('%d %b %Y')}")
                        st.write(f"**Days Late**: {days_late}")
                        st.write(f"**Priority**: High")

if __name__ == "__main__":
    field_app_page()
