import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from supabase_db import read_sheet, update_row, read_all_sheets, notify_update

# ─────────────────────────────────────────────────────────────
# ⚡ CORE OPTIMIZATION: PERFORMANCE-BASED GLOBAL CACHING
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner="🔄 Sinkronisasi basis data nasional...")
def load_optimized_master_data():
    """
    Mengambil seluruh data dari Supabase sekaligus.
    Mencegah aplikasi melakukan hit API berulang ke database pada setiap interaksi user.
    """
    return read_all_sheets()

# ─────────────────────────────────────────────────────────────
# 🎨 HIGH-PERFORMANCE STYLE SHEET (Scannable UI)
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
        
        /* Kanban Lane Custom Style */
        .kanban-col { background: #F3F4F6; padding: 12px; border-radius: 8px; min-height: 400px; }
        .kanban-card { 
            background: #FFFFFF; padding: 10px; border-radius: 6px; 
            margin-bottom: 8px; border-left: 4px solid #3B82F6; 
            font-size: 0.85rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
        }
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
    # 2. SPEED OPTIMIZED DATA JOINING
    # ═══════════════════════════════════════
    all_data = load_optimized_master_data()
    ms_df = all_data.get('milestones', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    
    if ms_df.empty:
        st.info("📋 Tidak ada data penugasan (milestone) yang tersedia.")
        return
    
    # Memfilter data awal berdasarkan penugasan role saat ini
    ms_df = ms_df[ms_df['assigned_to'] == assigned_to].copy()
    ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    ms_df['progress'] = pd.to_numeric(ms_df['progress'], errors='coerce').fillna(0).astype(int)
    
    # Mencegah perlambatan dari pemrosesan gabungan tabel (Merge/Join) berskala besar.
    # Menggunakan O(1) Fast Dictionary Mapping untuk transfer metadata lokasi.
    site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    site_name_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    site_region_map = dict(zip(sites_df['id'], sites_df['region'])) if not sites_df.empty else {}
    site_prov_map = dict(zip(sites_df['id'], sites_df['provinsi'])) if not sites_df.empty else {}
    
    ms_df['site_id'] = ms_df['project_id'].map(site_map)
    ms_df['site_name'] = ms_df['project_id'].map(site_name_map)
    ms_df['region'] = ms_df['project_id'].map(site_region_map)
    ms_df['provinsi'] = ms_df['project_id'].map(site_prov_map)

    # ═══════════════════════════════════════
    # 3. SIDEBAR FILTERS (KEMBALI KE ASLI & LENGKAP)
    # ═══════════════════════════════════════
    with st.sidebar:
        st.subheader(f"👷 {user.get('full_name', assigned_to)}")
        st.caption(f"Role: {assigned_to}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
            
        st.write("---")
        st.markdown("🔍 **Panel Pencarian & Filter**")
        
        # Fitur Pencarian Kata Kunci Komplit
        search_query = st.text_input("📝 Cari Berdasarkan Task / Site ID:", "").strip().lower()
        if search_query:
            ms_df = ms_df[
                ms_df['name'].str.lower().str.contains(search_query, na=False) | 
                ms_df['site_id'].str.lower().str.contains(search_query, na=False) |
                ms_df['site_name'].str.lower().str.contains(search_query, na=False)
            ]

        # Fitur Filter Wilayah Tingkat Region
        if 'region' in ms_df.columns and not ms_df['region'].dropna().empty:
            region_options = ['ALL'] + sorted(ms_df['region'].dropna().unique().tolist())
            sel_region = st.selectbox("🌐 Wilayah / Region:", region_options)
            if sel_region != 'ALL':
                ms_df = ms_df[ms_df['region'] == sel_region]
                
        # Fitur Filter Wilayah Tingkat Provinsi
        if 'provinsi' in ms_df.columns and not ms_df['provinsi'].dropna().empty:
            prov_options = ['ALL'] + sorted(ms_df['provinsi'].dropna().unique().tolist())
            sel_prov = st.selectbox("🗺️ Provinsi:", prov_options)
            if sel_prov != 'ALL':
                ms_df = ms_df[ms_df['provinsi'] == sel_prov]

        # Fitur Filter Nama Site Spesifik
        if not ms_df.empty:
            site_options = ['ALL'] + sorted(ms_df['site_name'].dropna().unique().tolist())
            sel_site = st.selectbox("📍 Pilih Site Spesifik:", site_options)
            if sel_site != 'ALL':
                ms_df = ms_df[ms_df['site_name'] == sel_site]

    # ═══════════════════════════════════════
    # 4. DATA AGGREGATION & METRICS CARD
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
    
    # Menggambar Header Utama & Modul Status Finansial/Progress
    st.markdown(f"""
    <div class="field-header">
        <h1>📱 Field Management App</h1>
        <p>Manajemen penugasan lapangan real-time (Infrastruktur Nasional)</p>
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
    # 5. SEMUA TAB FITUR ASLI DIKEMBALIKAN PENUH
    # ═══════════════════════════════════════
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Update Tasks", "🗂️ Kanban Board", "📊 Analytics Dashboard", "🤖 AI Insights"])
    
    # ─────────────────────────────────────────────────────────
    # TAB 1: UPDATE TASKS (Fitur Utama Pengisian Form Lapangan)
    # ─────────────────────────────────────────────────────────
    with tab1:
        if ms_df.empty:
            st.info("💡 Tidak ada tugas yang cocok dengan kombinasi filter Anda.")
        else:
            # Mengurutkan task bermasalah (Delayed/Ongoing) paling atas agar mendapat prioritas eksekusi
            ms_df['sort_idx'] = ms_df['status'].map({'DELAYED': 0, 'ONGOING': 1, 'PENDING': 2, 'DONE': 3}).fillna(4)
            display_df = ms_df.sort_values('sort_idx')
            
            for _, task in display_df.iterrows():
                s_code = task['site_id'] if pd.notna(task['site_id']) else '-'
                s_name = task['site_name'] if pd.notna(task['site_name']) else '-'
                deadline_str = task['planned_end'].strftime('%d %b %Y') if pd.notna(task['planned_end']) else '-'
                
                st.markdown(f"""
                <div class="task-card">
                    <div class="task-card-header">
                        <span class="task-name">🔹 {task['name']}</span>
                        <b style="font-size:0.85rem; color:#1E40AF;">{task['status']}</b>
                    </div>
                    <div class="task-meta">
                        <div>📍 {s_code} - {s_name} ({task['provinsi'] or 'Nasional'})</div>
                        <div>📅 Target: {deadline_str}</div>
                        <div>📈 Progress: {task['progress']}%</div>
                    </div>
                    <div class="task-progress"><div class="task-progress-bar" style="width: {task['progress']}%;"></div></div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.form(f"f_{task['id']}", clear_on_submit=True):
                    c1, c2, c3 = st.columns([1, 1, 1])
                    with c1:
                        new_status = st.selectbox("Ubah Status", ['PENDING', 'ONGOING', 'DONE', 'DELAYED'], index=['PENDING', 'ONGOING', 'DONE', 'DELAYED'].index(task['status']))
                    with c2:
                        new_prog = st.slider("Ubah Progress", 0, 100, int(task['progress']))
                    with c3:
                        st.markdown('<p style="margin-bottom:10px;"></p>', unsafe_allow_html=True)
                        submit = st.form_submit_button("⚡ Simpan Perubahan", use_container_width=True)
                        
                    if submit:
                        upd = {'status': new_status, 'progress': str(new_prog)}
                        if new_status == 'DONE':
                            upd['actual_end'] = date.today().strftime('%Y-%m-%d')
                        update_row('milestones', task['id'], upd)
                        st.cache_data.clear()  # Reset cache otomatis agar data terbaru langsung terekam
                        st.rerun()

    # ─────────────────────────────────────────────────────────
    # TAB 2: KANBAN BOARD (Visualisasi Progress Kolom Terpisah)
    # ─────────────────────────────────────────────────────────
    with tab2:
        st.markdown("### 🗂️ Papan Kerja Kontrol Tugas")
        kanban_statuses = ['PENDING', 'ONGOING', 'DONE', 'DELAYED']
        k_columns = st.columns(4)
        
        for idx, status_key in enumerate(kanban_statuses):
            with k_columns[idx]:
                st.markdown(f"### **{status_key}**")
                filtered_kb = ms_df[ms_df['status'] == status_key]
                
                # Membungkus wadah kanban
                st.markdown('<div class="kanban-col">', unsafe_allow_html=True)
                if filtered_kb.empty:
                    st.caption("Kosong")
                else:
                    for _, k_task in filtered_kb.iterrows():
                        st.markdown(f"""
                        <div class="kanban-card">
                            <b>{k_task['name']}</b><br/>
                            <span style="font-size:11px; color:#6B7280;">📍 {k_task['site_id'] or '-'}</span>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────
    # TAB 3: ANALYTICS DASHBOARD (Modul Grafik & Statistik)
    # ─────────────────────────────────────────────────────────
    with tab3:
        st.markdown("### 📊 Analisis Beban & Distribusi Kerja Lapangan")
        if not status_counts.empty:
            c_left, c_right = st.columns(2)
            
            with c_left:
                fig_pie = px.pie(values=status_counts.values, names=status_counts.index, hole=0.4, height=300, title="Proporsi Status")
                fig_pie.update_layout(margin=dict(t=40, b=10, l=10, r=10))
                st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
                
            with c_right:
                fig_bar = px.bar(x=status_counts.index, y=status_counts.values, labels={'x':'Status', 'y':'Jumlah'}, title="Jumlah Tugas Berdasarkan Status", color=status_counts.index)
                fig_bar.update_layout(margin=dict(t=40, b=10, l=10, r=10), showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Tidak ada data statistik untuk divisualisasikan.")

    # ─────────────────────────────────────────────────────────
    # TAB 4: AI INSIGHTS (Pelaporan Performa Otomatis)
    # ─────────────────────────────────────────────────────────
    with tab4:
        st.markdown("### 🤖 Prediksi & Rekomendasi Lapangan")
        if completion_rate >= 75:
            st.success(f"🎯 **Performa Optimal:** Rasio penyelesaian Anda berada di angka **{completion_rate:.1f}%**. Seluruh pengerjaan infrastruktur nasional berjalan sesuai timeline proyek.")
        else:
            st.warning(f"⚠️ **Peringatan Deviasi:** Rasio penyelesaian baru mencapai **{completion_rate:.1f}%**. Direkomendasikan untuk segera memprioritaskan penyelesaian {delayed_count} task berstatus *Delayed* guna mencegah terjadinya penalti keterlambatan site.")
