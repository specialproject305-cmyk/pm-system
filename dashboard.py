import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase_db import read_all_sheets, read_sheet
import numpy as np
from datetime import datetime, timedelta, date

# ─────────────────────────────────────────────────────────────
# 🎨 DARK THEME & UI CSS (OPTIMIZED CONTRAST)
# ─────────────────────────────────────────────────────────────
def inject_dark_css():
    st.markdown("""
    <style>
        .stApp { background-color: #0B1120; color: #FFFFFF; font-family: 'Inter', sans-serif; }
        
        /* SIDEBAR VISIBILITY FIX */
        [data-testid="stSidebar"] { background-color: #1E293B; border-right: 1px solid #334155; }
        [data-testid="stSidebar"] * { color: #E2E8F0 !important; }
        .stSidebar h1, .stSidebar h2, .stSidebar h3, .stSidebar p, .stSidebar span, .stSidebar div, .stSidebar label { color: #FFFFFF !important; }
        .stSidebar .stSelectbox > div { background-color: #0F172A; border: 1px solid #334155; color: #FFF !important; }
         @media (max-width: 768px) {
            [data-testid="stSidebar"] { display: block !important; }
        }
                [data-testid="stSidebarCollapseButton"] { display: block !important; visibility: visible !important; }
        button[kind="header"] { display: block !important; }
        
        .header-container { display: flex; justify-content: space-between; align-items: center; background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%); padding: 15px 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #334155; }
        .header-title h1 { margin: 0; font-size: 1.5rem; font-weight: 800; color: #38BDF8 !important; letter-spacing: 1px; }
        .header-title p { margin: 0; font-size: 0.8rem; color: #CBD5E1 !important; }
        
        .kpi-card { background-color: #1E293B; border-radius: 12px; padding: 20px; border: 1px solid #334155; height: 100%; display: flex; flex-direction: column; justify-content: center; transition: transform 0.2s; }
        .kpi-card:hover { transform: translateY(-3px); border-color: #38BDF8; }
        .kpi-title { font-size: 0.8rem; color: #CBD5E1 !important; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-value { font-size: 2rem; font-weight: 800; color: #FFFFFF !important; margin: 5px 0; }
        .kpi-sub { font-size: 0.75rem; color: #94A3B8; }
        
        .chart-box { background-color: #1E293B; border-radius: 12px; padding: 15px; border: 1px solid #334155; margin-bottom: 20px; }
        .stDataFrame { border-radius: 10px; overflow: hidden; }
        [data-testid="stDataFrame"] div { background-color: #1E293B; color: #FFFFFF !important; }
        thead th { background-color: #0F172A !important; color: #E2E8F0 !important; border-bottom: 2px solid #38BDF8 !important; }
        
        #MainMenu {visibility: hidden;} 
        .stDecoration {display: none;}
        header[data-testid="stHeader"] { visibility: visible !important; }
        .text-green { color: #10B981 !important; } .text-yellow { color: #F59E0B !important; }
        .text-red { color: #EF4444 !important; } .text-blue { color: #3B82F6 !important; }
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 🧠 HELPER FUNCTIONS (FIXED DONUT CHART)
# ─────────────────────────────────────────────────────────────

def get_safe_numeric(series):
    return pd.to_numeric(series, errors='coerce').fillna(0)

def create_donut_chart_safe(series, title, color_map, center_text=None):
    """
    ✅ Membuat donut chart yang aman dari Series value_counts()
    - Handle data kosong
    - Warna fallback jika kategori tidak ada di map
    - Teks tengah opsional
    """
    if series.empty:
        # Return empty chart dengan pesan
        fig = go.Figure()
        fig.add_annotation(text="📭 Data kosong", x=0.5, y=0.5, showarrow=False, font=dict(color='#94A3B8', size=14))
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0), height=250,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#FFFFFF'),
            title=dict(text=title, x=0.5, font=dict(color='#CBD5E1', size=14)),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False)
        )
        return fig

    # Prepare data: index = labels, values = counts
    labels = series.index.astype(str).tolist()
    values = series.values.tolist()
    
    # Assign colors: pakai dari map, fallback ke abu jika tidak ada
    colors = [color_map.get(label, '#64748B') for label in labels]
    
    fig = px.pie(
        values=values, 
        names=labels, 
        hole=0.7, 
        color=labels,
        color_discrete_map={label: color_map.get(label, '#64748B') for label in labels}
    )
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label', 
        hoverinfo='label+value+percent',
        marker=dict(line=dict(color='#1E293B', width=2)),
        textfont=dict(color='#FFFFFF', size=11)
    )
    
    # Tambahkan teks tengah jika ada (misal: avg progress %)
    if center_text:
        fig.add_annotation(
            text=f"{center_text}", 
            x=0.5, y=0.5, 
            font_size=20, 
            showarrow=False, 
            font_color='#FFFFFF',
            font_weight='bold'
        )
    
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=35, b=0),
        height=250,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#FFFFFF'),
        title=dict(text=title, x=0.5, font=dict(color='#CBD5E1', size=14))
    )
    
    return fig

def create_stacked_bar(df, x_col, categories, colors):
    """✅ FIXED: Menggunakan df.index karena groupby().unstack() menyimpan key di index"""
    fig = go.Figure()
    if df.empty:
        return fig

    x_values = df.index.astype(str)
    
    for i, cat in enumerate(categories):
        if cat in df.columns:
            color = colors[i] if i < len(colors) else '#94A3B8'
            fig.add_trace(go.Bar(x=x_values, y=df[cat], name=cat, marker_color=color, offsetgroup=0, hovertemplate=f"{cat}: %{{y}}<extra></extra>", textfont=dict(color='#FFFFFF')))
        else:
            fig.add_trace(go.Bar(x=x_values, y=[0]*len(x_values), name=cat, marker_color='#334155', opacity=0.3, hovertemplate=f"{cat}: 0<extra></extra>"))
            
    fig.update_layout(barmode='stack', margin=dict(l=0, r=0, t=40, b=0), height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), xaxis=dict(showgrid=False, tickangle=45, tickfont=dict(color='#CBD5E1')), yaxis=dict(showgrid=True, gridcolor='#334155', tickfont=dict(color='#CBD5E1')), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color='#FFFFFF')), bargap=0.2)
    return fig

def create_scatter_trend(df, date_col, value_col, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[date_col], y=df[value_col], mode='markers', name='Progress', marker=dict(color='#10B981', size=8)))
    fig.add_trace(go.Scatter(x=df[date_col], y=df[value_col], mode='lines', name='Trend', line=dict(color='#38BDF8', width=2, dash='dash')))
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), xaxis=dict(showgrid=True, gridcolor='#334155', title="", tickfont=dict(color='#CBD5E1')), yaxis=dict(showgrid=True, gridcolor='#334155', title="%", tickfont=dict(color='#CBD5E1')), title=dict(text=title, x=0.5, font=dict(color='#CBD5E1')), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color='#FFFFFF')))
    return fig

# ─────────────────────────────────────────────────────────────
#  MAIN DASHBOARD FUNCTION
# ─────────────────────────────────────────────────────────────

    if st.query_params.get("refresh") == "true":
        st.cache_data.clear()
        st.query_params.clear()
        st.rerun()

def dashboard_page():
    inject_dark_css()
    if 'master_project_filter' not in st.session_state:
        st.session_state.master_project_filter = "ALL"

    try:
        with st.spinner("🔄 Loading..."):
            all_data = read_all_sheets()
        df = all_data.get('projects', pd.DataFrame())
        materials_df = all_data.get('materials', pd.DataFrame())
        ms_df = all_data.get('milestones', pd.DataFrame())
        milestones_df = all_data.get('milestones', pd.DataFrame()) # Untuk PIC Widget

        # Terapkan Global Filter
        if st.session_state.get('global_project_filter', 'ALL') != "ALL":
            valid_sites = df[df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
            df = df[df['id'].isin(valid_sites)]
            ms_df = ms_df[ms_df['project_id'].isin(valid_sites)]
            milestones_df = milestones_df[milestones_df['project_id'].isin(valid_sites)]

        try:
            mp_df = all_data.get('master_projects', pd.DataFrame())
            master_options = ["🌐 SEMUA PROYEK"] + mp_df["id"].tolist() if not mp_df.empty else ["🌐 SEMUA PROYEK"]
        except:
            master_options = ["🌐 SEMUA PROYEK"]
            
    except Exception as e:
        st.error(f"⚠️ Error loading  {e}")
        return

    if df.empty:
        st.info("📋 Belum ada data site.")
        return

    # Konversi Numerik
    df['progress'] = get_safe_numeric(df['progress'])
    for col in ['planned_end', 'actual_end']:
        if col in ms_df.columns: ms_df[col] = pd.to_datetime(ms_df[col], errors='coerce')

    # Sidebar
    st.sidebar.markdown("<h1 style='color:#38BDF8 !important;'>🏗️ MCP TOWER</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Filter Master Project")
    selected_mp = st.sidebar.selectbox("Pilih Proyek:", master_options, format_func=lambda x: "🌐 SEMUA PROYEK" if x == "🌐 SEMUA PROYEK" else f"{mp_df[mp_df['id']==x]['project_code'].values[0]} - {mp_df[mp_df['id']==x]['project_name'].values[0]}")
    
    if selected_mp != st.session_state.master_project_filter:
        st.session_state.master_project_filter = selected_mp
        st.cache_data.clear()
        st.rerun()
        
    if selected_mp != "🌐 SEMUA PROYEK":
        try:
            target_id = mp_df[mp_df['id'] == selected_mp].iloc[0]['id']
            df = df[df.get('master_project_id', '') == target_id]
            valid_sites = df['id'].tolist()
            ms_df = ms_df[ms_df['project_id'].isin(valid_sites)]
            milestones_df = milestones_df[milestones_df['project_id'].isin(valid_sites)]
        except: pass
        
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"###  Site: {len(df)}")
    st.sidebar.markdown(f"### 🔄 Update: {datetime.now().strftime('%H:%M')}")

    # Header
    st.markdown(f"""
    <div style='text-align:center; background: linear-gradient(90deg, #1E3A5F 0%, #0F172A 100%); padding:10px 20px; border-radius:12px; margin-bottom:10px; border:1px solid #334155;'>
        <h1 style='margin:0; font-size:1.5rem; font-weight:800; color:#38BDF8;'>MCP TOWER PROJECT</h1>
        <p style='margin:2px 0; font-size:0.85rem; color:#CBD5E1;'>Deployment Dashboard</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Refresh & Period
    st.markdown("<div style='background: linear-gradient(90deg, #1E3A5F 10%, #0F172A 90%); padding:10px 15px; border-radius:10px; margin-bottom:15px;'>", unsafe_allow_html=True)
    col_r1, col_r2 = st.columns([1, 2])
    with col_r1:
        if st.button("🔄 Refresh Data", key="refresh_btn", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_r2:
        date_range = st.date_input(
            "📅 Periode",
            value=(date.today() - timedelta(days=30), date.today()),
            max_value=date.today(),
            key="dash_period",
            label_visibility="collapsed"
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # KPI Cards
    total_sites = len(df)
    rfs_count = len(df[df['status']=='DONE'])
    on_prog = len(df[df['status']=='ONGOING'])
    not_start = len(df[df['status']=='PENDING'])
    delay_count = len(df[df['status'].isin(['DELAYED','CRITICAL'])])
    avg_prog = df['progress'].mean()

    kpis = [
        ("📡 TOTAL SITE", total_sites, "Sites", "text-blue"),
        ("🟢 RFS (ON AIR)", rfs_count, f"{rfs_count/total_sites*100:.0f}% dari total" if total_sites > 0 else "0%", "text-green"),
        ("⚙️ ON PROGRESS", on_prog, f"{on_prog/total_sites*100:.0f}% dari total" if total_sites > 0 else "0%", "text-yellow"),
        ("⚪ NOT STARTED", not_start, f"{not_start/total_sites*100:.0f}% dari total" if total_sites > 0 else "0%", "text-gray"),
        ("🔴 DELAY SITE", delay_count, f"{delay_count/total_sites*100:.0f}% dari total" if total_sites > 0 else "0%", "text-red"),
        ("📈 RATA-RATA PROGRESS", f"{avg_prog:.1f}%", "Target: 100%", "text-blue")
    ]

    cols = st.columns(6)
    for i, (title, value, sub, color_class) in enumerate(kpis):
        with cols[i]:
            st.markdown(f"""<div class='kpi-card'><div class='kpi-title'>{title}</div><div class='kpi-value'>{value}</div><div class='kpi-sub {color_class}'>{sub}</div></div>""", unsafe_allow_html=True)

    # ===== PIC PERFORMANCE SNAPSHOT (DITAMBAHKAN DI SINI) =====
    st.markdown("---")
    st.subheader("👷 PIC Performance Snapshot")
    
    if not milestones_df.empty and 'assigned_to' in milestones_df.columns:
        pic_list = ['Sitac', 'Legal', 'Engineering', 'Procurement', 'Project', 'Vendor Management']
        cols_pic = st.columns(len(pic_list))
        
        for i, pic in enumerate(pic_list):
            pic_tasks = milestones_df[milestones_df['assigned_to'] == pic]
            total = len(pic_tasks)
            
            if total > 0:
                done = len(pic_tasks[pic_tasks['status'] == 'DONE'])
                completion_rate = (done / total) * 100
                
                if completion_rate > 80: bg, border = '#DCFCE7', '#10B981'
                elif completion_rate > 50: bg, border = '#FEF3C7', '#F59E0B'
                else: bg, border = '#FEE2E2', '#EF4444'
                
                with cols_pic[i]:
                    st.markdown(f"""
                    <div style="background:{bg}; padding:12px; border-radius:10px; border-left:4px solid {border}; text-align:center;">
                        <strong>{pic}</strong><br>
                        📋 {total} | ✅ {done}<br>
                        📈 {completion_rate:.0f}%
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")
    # =========================================================

    # Donut Charts Row
    col_d1, col_d2, col_d3 = st.columns([1, 1, 1.5])
    # ... (SISA KODE CHART ANDA TETAP ADA DI SINI) ...

    # Site Delay & Trend Row
    col_t1, col_t2 = st.columns([1.5, 1])
    with col_t1:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#EF4444 !important; font-size:1rem; margin-bottom:10px;'>🔴 SITE DELAY (TOP 5)</h3>", unsafe_allow_html=True)
        delay_df = df[df['status'].isin(['DELAYED', 'CRITICAL'])].copy()
        if not delay_df.empty:
            if 'end_date' in delay_df.columns:
                delay_df['end_date_dt'] = pd.to_datetime(delay_df['end_date'], errors='coerce')
                delay_df['delay_days'] = (datetime.now() - delay_df['end_date_dt']).dt.days
                delay_df = delay_df.sort_values('delay_days', ascending=False).head(5)
                st.dataframe(delay_df[['site_id', 'site_name', 'site_category', 'vendor', 'end_date', 'delay_days', 'status']].rename(columns={'end_date':'Target RFS', 'delay_days':'Delay (Hari)'}), use_container_width=True, hide_index=True)
            else:
                st.warning("Kolom 'end_date' tidak ditemukan.")
        else:
            st.success("✅ Tidak ada site delayed!")
        st.markdown("</div>", unsafe_allow_html=True)
        
    # ... (SISA KODE TREND DAN LAINNYA) ...
    dashboard_page()
