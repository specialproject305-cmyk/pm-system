import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from supabase_db import read_sheet, update_row, read_all_sheets, update_row, notify_update

# ─────────────────────────────────────────────────────────────
# ⚡ OPTIMIZED DATA LOADING WITH CACHING (TTL: 2 Minutes)
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner="🔄 Mengambil data terbaru...")
def fetch_cached_data():
    """Mengambil semua data sekaligus dan meng-cache hasilnya selama 2 menit"""
    return read_all_sheets()

# ─────────────────────────────────────────────────────────────
# 🎨 LIGHT COMPACT CSS (Global & Scannable)
# ─────────────────────────────────────────────────────────────
def inject_field_css():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #F8FBFF 0%, #F0F7FF 100%); color: #1F2937; }
        .field-header {
            background: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%);
            padding: 15px 20px; border-radius: 12px; margin-bottom: 20px; color: white;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        }
        .field-header h1 { margin: 0; font-size: 1.6rem; font-weight: 800; color: white; }
        .field-header p { margin: 3px 0 0 0; font-size: 0.85rem; color: #E0E7FF; }
        
        /* Status Card Grid */
        .status-container { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 15px; }
        .status-card {
            flex: 1; min-width: 100px; background: #FFFFFF; padding: 10px; 
            border-radius: 10px; border: 1px solid #DBEAFE; text-align: center;
        }
        .status-card .count { font-size: 1.6rem; font-weight: 800; color: #1F2937; }
        .status-card .label { font-size: 0.7rem; color: #6B7280; text-transform: uppercase; margin-top: 2px; }
        .status-card.success { border-left: 4px solid #10B981; }
        .status-card.warning { border-left: 4px solid #FF8C00; }
        .status-card.danger { border-left: 4px solid #DC2626; }
        .status-card.info { border-left: 4px solid #3B82F6; }
        
        /* Task Cards */
        .task-card {
            background: #FFFFFF; padding: 14px; border-radius: 10px; 
            border: 1px solid #DBEAFE; margin-bottom: 10px;
        }
        .task-card-header { display: flex; justify-content: space-between; align-items: center; }
        .task-name { font-size: 1rem; font-weight: 700; color: #1F2937; }
        .task-meta { display: flex; gap: 12px; font-size: 0.8rem; color: #6B7280; margin: 6px 0; }
        
        .task-progress { background: #E5E7EB; border-radius: 4px; height: 5px; overflow: hidden; margin-bottom: 8px; }
        .task-progress-bar { background: #3B82F6; height: 100%; }
        
        /* Kanban */
        .kanban-col { background: #F3F4F6; padding: 10px; border-radius: 8px; min-height: 300px; }
        .kanban-card { background: #FFFFFF; padding: 8px; border-radius: 6px; margin-bottom: 6px; border-left: 3px solid #3B82F6; font-size: 0.85rem; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

def field_app_page():
    inject_field_css()
    
    # ═══════════════════════════════════════
    # 1. USER & ROLE RESOLUTION
    # ═══════════════════════════════════════
    user = st.session_state.get('user', {})
    role = user.get('role', 'engineer')
    
    if role == 'marketing':
        from marketing_dashboard import marketing_dashboard_page
        marketing_dashboard_page()
        st.stop()
        
    role_map = {
        'sitac': 'Sitac', 'legal': 'Legal', 'engineering': 'Engineering',
        'procurement': 'Procurement', 'project': 'Project', 'vendor_mgmt': 'Vendor Management'
    }
    assigned_to = role_map.get(role, role)
    
    # ═══════════════════════════════════════
    # 2. LIGHTWEIGHT DATA PROCESSING
    # ═══════════════════════════════════════
    all_data = fetch_cached_data()
    ms_df = all_data.get('milestones', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    
    if ms_df.empty:
        st.info("📋 No milestones available.")
        return
    
    # Vectorized conversion (Jauh lebih cepat dari loop baris)
    ms_df = ms_df[ms_df['assigned_to'] == assigned_to].copy()
    ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    ms_df['progress'] = pd.to_numeric(ms_df['progress'], errors='coerce').fillna(0).astype(int)
    
    # ═══════════════════════════════════════
    # 3. SIDEBAR FILTER & MUTASI (PRE-CALCULATED)
    # ═══════════════════════════════════════
    with st.sidebar:
        st.subheader(f"👷 {user.get('full_name', assigned_to)}")
        st.caption(f"Role: {assigned_to}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
            
        st.write("---")
        
        # Mapping Cepat Menggunakan Dictionary Vectorization (Bukan gabung tabel berat)
        site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
        site_name_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
        
        if not sites_df.empty:
            site_options = ['ALL'] + sorted(sites_df['site_name'].unique().tolist())
            sel_site = st.selectbox("📍 Filter Site:", site_options)
            if sel_site != 'ALL':
                valid_ids = sites_df[sites_df['site_name'] == sel_site]['id'].tolist()
                ms_df = ms_df[ms_df['project_id'].isin(valid_ids)]

    # ═══════════════════════════════════════
    # 4. AGGREGATION & METRICS
    # ═══════════════════════════════════════
    total_tasks = len(ms_df)
    status_counts = ms_df['status'].value_counts()
    
    done_count = status_counts.get('DONE', 0)
    ongoing_count = status_counts.get('ONGOING', 0)
    pending_count = status_counts.get('PENDING', 0)
    delayed_count = status_counts.get('DELAYED', 0)
    
    today = pd.Timestamp(date.today())
    overdue_count = len(ms_df[(ms_df['planned_end'] < today) & (ms_df['status'] != 'DONE')]) if total_tasks > 0 else 0
    completion_rate = (done_count / total_tasks * 100) if total_tasks > 0 else 0
    
    # Render UI Header & Stats Cards
    st.markdown(f"""
    <div class="field-header">
        <h1>📱 Field Management App</h1>
        <p>Manajemen penugasan lapangan real-time</p>
    </div>
    <div class="status-container">
        <div class="status-card info"><div class="count">{total_tasks}</div><div class="label">Total Tasks</div></div>
        <div class="status-card success"><div class="count">{done_count}</div><div class="label">Completed</div></div>
        <div class="status-card warning"><div class="count">{ongoing_count}</div><div class="label">Ongoing</div></div>
        <div class="status-card danger"><div class="count">{delayed_count}</div><div class="label">Delayed</div></div>
        <div class="status-card"><div class="count">{overdue_count}</div><div class="label">Overdue</div></div>
        <div class="status-card"><div class="count">{completion_rate:.0f}%</div><div class="label">Done %</div></div>
    </div>
    """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════
    # 5. LIGHTWEIGHT TABS CONFIGURATION
    # ═══════════════════════════════════════
    tab1, tab2, tab3 = st.tabs(["📋 Update Tasks", "📊 Dashboard & Kanban", "🤖 AI Insights"])
    
    # ----- TAB 1: UPDATE TASKS -----
    with tab1:
        if ms_df.empty:
            st.info("✅ Tidak ada tugas aktif untuk Anda.")
        else:
            # Batch render 5 tugas teratas yang butuh tindakan segera (Optimasi RAM)
            ms_df['sort_idx'] = ms_df['status'].map({'DELAYED': 0, 'ONGOING': 1, 'PENDING': 2, 'DONE': 3}).fillna(4)
            display_df = ms_df.sort_values('sort_idx').head(10)
            
            for _, task in display_df.iterrows():
                s_code = site_map.get(task['project_id'], '-')
                s_name = site_name_map.get(task['project_id'], '-')
                deadline_str = task['planned_end'].strftime('%d %b %Y') if pd.notna(task['planned_end']) else '-'
                
                st.markdown(f"""
                <div class="task-card">
                    <div class="task-card-header">
                        <span class="task-name">🔹 {task['name']}</span>
                        <b style="font-size:0.85rem; color:#1E40AF;">{task['status']}</b>
                    </div>
                    <div class="task-meta">
                        <div>📍 {s_code} - {s_name}</div>
                        <div>📅 Target: {deadline_str}</div>
                        <div>📈 Progress: {task['progress']}%</div>
                    </div>
                    <div class="task-progress"><div class="task-progress-bar" style="width: {task['progress']}%;"></div></div>
                </div>
                """, unsafe_allow_html=True)
                
                # Form update diringkas dalam 1 baris horizontal untuk menghemat ruang komponen streamlit
                with st.form(f"f_{task['id']}", clear_on_submit=True):
                    c1, c2, c3 = st.columns([1, 1, 1])
                    with c1:
                        new_status = st.selectbox("Status", ['PENDING', 'ONGOING', 'DONE', 'DELAYED'], index=['PENDING', 'ONGOING', 'DONE', 'DELAYED'].index(task['status']))
                    with c2:
                        new_prog = st.slider("Progress", 0, 100, int(task['progress']))
                    with c3:
                        st.markdown('<p style="margin-bottom:10px;"></p>', unsafe_allow_html=True)
                        submit = st.form_submit_button("⚡ Update Status", use_container_width=True)
                        
                    if submit:
                        upd = {'status': new_status, 'progress': str(new_prog)}
                        if new_status == 'DONE':
                            upd['actual_end'] = date.today().strftime('%Y-%m-%d')
                        update_row('milestones', task['id'], upd)
                        st.cache_data.clear()  # Clear cache agar data langsung ter-refresh
                        st.rerun()

    # ----- TAB 2: DASHBOARD & KANBAN MIX -----
    with tab2:
        col_graph, col_kanban = st.columns([1, 1])
        
        with col_graph:
            if not status_counts.empty:
                fig = px.pie(values=status_counts.values, names=status_counts.index, hole=0.5, height=220)
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        with col_kanban:
            st.markdown("⚡ **Kanban Board** (Quick Row View)")
            k_cols = st.columns(3)
            statuses = ['PENDING', 'ONGOING', 'DONE']
            for i, s in enumerate(statuses):
                with k_cols[i]:
                    st.markdown(f"**{s}**")
                    sub = ms_df[ms_df['status'] == s].head(3)
                    for _, t in sub.iterrows():
                        st.markdown(f'<div class="kanban-card">{t["name"]}</div>', unsafe_allow_html=True)

    # ----- TAB 3: AI INSIGHTS -----
    with tab3:
        st.markdown("### 🤖 Performance Forecast")
        if completion_rate >= 75:
            st.success("🎯 **Status Aman:** Kecepatan pengerjaan sangat baik. Pertahankan performa ini!")
        else:
            st.warning("⚠️ **Perhatian:** Rasio penyelesaian Anda berada di bawah 75%. Prioritaskan task berstatus *Delayed*.")
