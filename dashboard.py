import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase_db import read_all_sheets, read_sheet
import numpy as np

# ─────────────────────────────────────────────────────────────
# 🎨 DARK THEME & UI CSS (FIXED CONTRAST)
# ─────────────────────────────────────────────────────────────
def inject_dark_css():
    st.markdown("""
    <style>
        /* Main Background & Font */
        .stApp { background-color: #0B1120; color: #FFFFFF; font-family: 'Inter', sans-serif; }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] { background-color: #1E293B; border-right: 1px solid #334155; }
        .stSidebar > div:first-child { padding: 20px; }
        .stSidebar h1 { font-size: 1.2rem; font-weight: bold; color: #38BDF8; }
        .stSidebar button { width: 100%; text-align: left; color: #E2E8F0; background: transparent; border: none; padding: 10px; margin: 5px 0; border-radius: 8px; }
        .stSidebar button:hover { background-color: #334155; color: #FFF; }
        .stSidebar .stSelectbox > div { background-color: #0F172A; border: 1px solid #334155; color: #FFF; }
        
        /* Top Header Bar */
        .header-container {
            display: flex; justify-content: space-between; align-items: center;
            background: linear-gradient(90deg, #1E293B 0%, #0F172A 100%);
            padding: 15px 20px; border-radius: 12px; margin-bottom: 20px;
            border: 1px solid #334155;
        }
        .header-title h1 { margin: 0; font-size: 1.5rem; font-weight: 800; color: #38BDF8; letter-spacing: 1px; }
        .header-title p { margin: 0; font-size: 0.8rem; color: #CBD5E1; }
        
        /* KPI Cards */
        .kpi-card {
            background-color: #1E293B; border-radius: 12px; padding: 20px;
            border: 1px solid #334155; height: 100%; display: flex; flex-direction: column; justify-content: center;
            transition: transform 0.2s;
        }
        .kpi-card:hover { transform: translateY(-3px); border-color: #38BDF8; }
        .kpi-title { font-size: 0.8rem; color: #CBD5E1; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-value { font-size: 2rem; font-weight: 800; color: #FFFFFF; margin: 5px 0; }
        .kpi-sub { font-size: 0.75rem; color: #94A3B8; }
        
        /* Chart Containers */
        .chart-box {
            background-color: #1E293B; border-radius: 12px; padding: 15px;
            border: 1px solid #334155; margin-bottom: 20px;
        }
        
        /* Table Styling */
        .stDataFrame { border-radius: 10px; overflow: hidden; }
        [data-testid="stDataFrame"] div { background-color: #1E293B; color: #FFFFFF; }
        thead th { background-color: #0F172A !important; color: #E2E8F0 !important; border-bottom: 2px solid #38BDF8 !important; }
        
        /* Hide Streamlit Default Elements */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        .stDecoration {display: none;}
        
        /* Metric Colors */
        .text-green { color: #10B981; }
        .text-yellow { color: #F59E0B; }
        .text-red { color: #EF4444; }
        .text-blue { color: #3B82F6; }
        .text-gray { color: #94A3B8; }
        .text-white { color: #FFFFFF; }
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 🧠 HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_safe_numeric(series):
    """Convert to numeric safely"""
    return pd.to_numeric(series, errors='coerce').fillna(0)

def create_donut_chart(df, value_col, title, color_map):
    fig = px.pie(df, values=value_col, names=df.index, title=title, hole=0.7, color=df.index, color_discrete_map=color_map)
    fig.update_traces(textposition='inside', textinfo='percent+label', hoverinfo='label+value', marker=dict(line=dict(color='#1E293B', width=2)), textfont=dict(color='#FFFFFF', size=12))
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=40, b=0),
        height=250,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#FFFFFF'),
        title=dict(text=title, x=0.5, y=0.95, font=dict(size=16, color='#CBD5E1'))
    )
    return fig

def create_stacked_bar(df, x_col, categories, colors):
    fig = go.Figure()
    for i, cat in enumerate(categories):
        if cat in df.columns:
            fig.add_trace(go.Bar(x=df[x_col], y=df[cat], name=cat, marker_color=colors[i], offsetgroup=0, hovertemplate=f"{cat}: %{{y}}<extra></extra>", textfont=dict(color='#FFFFFF')))
    fig.update_layout(
        barmode='stack',
        margin=dict(l=0, r=0, t=40, b=0),
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#FFFFFF'),
        xaxis=dict(showgrid=False, tickangle=45, tickfont=dict(color='#CBD5E1')),
        yaxis=dict(showgrid=True, gridcolor='#334155', tickfont=dict(color='#CBD5E1')),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color='#FFFFFF')),
        bargap=0.2
    )
    return fig

def create_scatter_trend(df, date_col, value_col, title):
    fig = go.Figure()
    # Add dots
    fig.add_trace(go.Scatter(x=df[date_col], y=df[value_col], mode='markers', name='Progress', marker=dict(color='#10B981', size=8)))
    # Add trend line
    fig.add_trace(go.Scatter(x=df[date_col], y=df[value_col], mode='lines', name='Trend', line=dict(color='#38BDF8', width=2, dash='dash')))
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=250,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#FFFFFF'),
        xaxis=dict(showgrid=True, gridcolor='#334155', title="", tickfont=dict(color='#CBD5E1')),
        yaxis=dict(showgrid=True, gridcolor='#334155', title="%", tickfont=dict(color='#CBD5E1')),
        title=dict(text=title, x=0.5, font=dict(color='#CBD5E1')),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color='#FFFFFF'))
    )
    return fig

# ─────────────────────────────────────────────────────────────
# 🚀 MAIN DASHBOARD FUNCTION
# ─────────────────────────────────────────────────────────────

def dashboard_page():
    inject_dark_css()
    
    # Init Session State for Filter
    if 'master_project_filter' not in st.session_state:
        st.session_state.master_project_filter = "ALL"

    # Load Data
    try:
        with st.spinner("🔄 Loading..."):
            all_data = read_all_sheets()
        df = all_data.get('projects', pd.DataFrame())
        ms_df = all_data.get('milestones', pd.DataFrame())
        mat_df = all_data.get('materials', pd.DataFrame())
        
        # Load Master Projects for Filter
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

    # Convert Types
    df['progress'] = get_safe_numeric(df['progress'])
    for col in ['planned_end', 'actual_end']:
        if col in ms_df.columns: ms_df[col] = pd.to_datetime(ms_df[col], errors='coerce')

    # ─── HEADER TOP BAR ───
    st.sidebar.markdown("<h1>🏗️ MCP TOWER</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    # Sidebar Filter
    st.sidebar.markdown("### 🎯 Filter Master Project")
    selected_mp = st.sidebar.selectbox("Pilih Proyek:", master_options, format_func=lambda x: "🌐 SEMUA PROYEK" if x == "🌐 SEMUA PROYEK" 
                                    else f"{mp_df[mp_df['id']==x]['project_code'].values[0]} - {mp_df[mp_df['id']==x]['project_name'].values[0]}")
    
    if selected_mp != st.session_state.master_project_filter:
        st.session_state.master_project_filter = selected_mp
        st.cache_data.clear()
        st.rerun()
        
    # Apply Filter
    if selected_mp != "🌐 SEMUA PROYEK":
        target_id = selected_mp.split(" - ")[0]
        df = df[df['master_project_id'] == target_id]
        valid_sites = df['id'].tolist()
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)]
        
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### 📊 Site: {len(df)}")
    st.sidebar.markdown(f"### 🔄 Last Update: {datetime.now().strftime('%H:%M')}")

    # Header Content
    st.markdown("""
    <div class='header-container'>
        <div class='header-title'>
            <h1>MCP TOWER PROJECT</h1>
            <p>Deployment Dashboard</p>
        </div>
        <div style='display:flex; gap:15px; align-items:center;'>
             <button style='background:#334155; color:#FFFFFF; border:none; padding:8px 15px; border-radius:6px; cursor:pointer; font-size:0.8rem;'>
                 📅 Periode: 20 Mei - 20 Jun 2024
             </button>
             <button style='background:#38BDF8; color:#0F172A; border:none; padding:8px 15px; border-radius:6px; cursor:pointer; font-weight:bold; font-size:0.8rem;' onclick='document.location.reload()'>
                 🔄 Refresh
             </button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ─── KPI CARDS ───
    total_sites = len(df)
    rfs_count = len(df[df['status']=='DONE'])
    on_prog = len(df[df['status']=='ONGOING'])
    not_start = len(df[df['status']=='PENDING'])
    delay_count = len(df[df['status'].isin(['DELAYED','CRITICAL'])])
    avg_prog = df['progress'].mean()

    kpis = [
        ("📡 TOTAL SITE", total_sites, "Sites", "text-blue"),
        ("🟢 RFS (ON AIR)", rfs_count, f"{rfs_count/total_sites*100:.0f}% dari total" if total_sites > 0 else "0% dari total", "text-green"),
        ("⚙️ ON PROGRESS", on_prog, f"{on_prog/total_sites*100:.0f}% dari total" if total_sites > 0 else "0% dari total", "text-yellow"),
        ("⚪ NOT STARTED", not_start, f"{not_start/total_sites*100:.0f}% dari total" if total_sites > 0 else "0% dari total", "text-gray"),
        ("🔴 DELAY SITE", delay_count, f"{delay_count/total_sites*100:.0f}% dari total" if total_sites > 0 else "0% dari total", "text-red"),
        ("📊 RATA-RATA PROGRESS", f"{avg_prog:.1f}%", "Target: 100%", "text-blue")
    ]

    cols = st.columns(6)
    for i, (title, value, sub, color_class) in enumerate(kpis):
        with cols[i]:
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-title'>{title}</div>
                <div class='kpi-value'>{value}</div>
                <div class='kpi-sub {color_class}'>{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    # ─── ROW 1: DONUTS & CATEGORIES ───
    col_d1, col_d2, col_d3 = st.columns([1, 1, 1.5])

    with col_d1:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        # Status Donut
        status_counts = df['status'].value_counts()
        status_map = {'DONE':'#10B981', 'ONGOING':'#F59E0B', 'PENDING':'#94A3B8', 'DELAYED':'#EF4444', 'CRITICAL':'#7F1D1D', 'ON_TRACK':'#10B981'}
        fig1 = create_donut_chart(status_counts, None, "PROGRESS OVERVIEW", status_map)
        # Custom center text
        fig1.add_annotation(dict(text=f'{avg_prog:.0f}%', x=0.5, y=0.5, font_size=24, showarrow=False, font_color='#FFFFFF'))
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_d2:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        # Kategori Donut
        if 'site_category' in df.columns:
            cat_counts = df['site_category'].value_counts()
            cat_map = {'New Site':'#3B82F6', 'Collocation':'#8B5CF6', 'Upgrade':'#F59E0B', 'Relocation':'#EF4444'}
            fig2 = create_donut_chart(cat_counts, None, "SITE BY KATEGORI", cat_map)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.markdown("Data Kategori tidak tersedia.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_d3:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        # Stacked Bar (Cluster/Vendor)
        if 'vendor' in df.columns:
            group_col = 'vendor'
            title_bar = "SITE STATUS BY VENDOR"
        elif 'site_category' in df.columns:
            group_col = 'site_category'
            title_bar = "SITE STATUS BY CATEGORY"
        else:
            group_col = 'status'
            title_bar = "SITE STATUS"
            
        pivot = df.groupby(group_col)['status'].value_counts().unstack(fill_value=0)
        # Define order for stacking
        stack_order = ['DELAYED', 'CRITICAL', 'ONGOING', 'PENDING', 'DONE', 'ON_TRACK']
        available_cats = [c for c in stack_order if c in pivot.columns]
        stack_colors = ['#EF4444', '#7F1D1D', '#F59E0B', '#94A3B8', '#10B981', '#10B981']
        
        fig3 = create_stacked_bar(pivot, group_col, available_cats, stack_colors[:len(available_cats)])
        fig3.update_layout(title=dict(text=title_bar, x=0.5, font=dict(color='#CBD5E1')))
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ─── ROW 2: MILESTONE, ISSUE, RISK ───
    col_m1, col_m2, col_m3 = st.columns([1.5, 1, 1])

    with col_m1:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#CBD5E1; font-size:1rem; margin-bottom:10px;'>OVERALL MILESTONE PROGRESS</h3>", unsafe_allow_html=True)
        if not ms_df.empty:
            ms_pivot = ms_df.groupby('name')['status'].value_counts().unstack(fill_value=0)
            total_ms = ms_df.groupby('name')['id'].count()
            
            steps = ['Survey', 'Design', 'Permit', 'Construction', 'Installation', 'Integration', 'RFS']
            # Simplified for demo based on data availability
            avail_steps = [s for s in steps if s in ms_pivot.index]
            if not avail_steps: avail_steps = ms_pivot.index.tolist()[:5]
            
            # Calculate % done for each step
            step_data = []
            for step in avail_steps:
                if step in ms_pivot.index:
                    done = ms_pivot.loc[step].get('DONE', 0)
                    total = total_ms.get(step, 1)
                    pct = (done/total)*100
                    step_data.append({'step': step, 'pct': pct})
                    
            step_df = pd.DataFrame(step_data)
            
            # Render Step Bar
            for _, row in step_df.iterrows():
                color = '#10B981' if row['pct'] >= 80 else ('#F59E0B' if row['pct'] >= 40 else '#EF4444')
                st.markdown(f"""
                <div style='display:flex; align-items:center; margin-bottom:8px;'>
                    <div style='width:80px; font-size:0.8rem; color:#FFFFFF; font-weight:bold;'>{row['step']}</div>
                    <div style='flex:1; height:8px; background:#334155; border-radius:4px; overflow:hidden;'>
                        <div style='width:{row['pct']}%; height:100%; background:{color};'></div>
                    </div>
                    <div style='width:40px; text-align:right; font-size:0.7rem; color:#CBD5E1;'>{row['pct']:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Data milestone kosong.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_m2:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#CBD5E1; font-size:1rem; margin-bottom:10px;'>ISSUE SUMMARY</h3>", unsafe_allow_html=True)
        # Dummy Data for Demo (Replace with real issue data if available)
        issue_data = {'High': 6, 'Medium': 11, 'Low': 6}
        fig_iss = go.Figure(data=[go.Bar(x=list(issue_data.keys()), y=list(issue_data.values()), marker_color=['#EF4444', '#F59E0B', '#10B981'])])
        fig_iss.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'))
        st.plotly_chart(fig_iss, use_container_width=True)
        st.markdown(f"<div style='text-align:center; font-size:2rem; font-weight:bold; color:#FFFFFF;'>23</div><div style='text-align:center; color:#CBD5E1; font-size:0.8rem;'>TOTAL ISSUE</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_m3:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#CBD5E1; font-size:1rem; margin-bottom:10px;'>RISK MATRIX</h3>", unsafe_allow_html=True)
        # Dummy Heatmap
        risk_data = np.random.randint(0, 5, (5, 5))
        fig_risk = px.imshow(risk_data, text_auto=True, aspect="auto", color_continuous_scale="RdYlGn_r", zmin=0, zmax=10)
        fig_risk.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), coloraxis_showscale=False)
        st.plotly_chart(fig_risk, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ─── ROW 3: DELAY TABLE & TREND ───
    col_t1, col_t2 = st.columns([1.5, 1])

    with col_t1:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#EF4444; font-size:1rem; margin-bottom:10px;'>🔴 SITE DELAY (TOP 5)</h3>", unsafe_allow_html=True)
        
        # Calculate Delay Days
        delay_df = df[df['status'].isin(['DELAYED', 'CRITICAL'])].copy()
        if 'end_date' in delay_df.columns:
            delay_df['end_date_dt'] = pd.to_datetime(delay_df['end_date'], errors='coerce')
            today = datetime.now()
            delay_df['delay_days'] = (today - delay_df['end_date_dt']).dt.days
            delay_df = delay_df.sort_values('delay_days', ascending=False).head(5)
            
            cols_disp = ['site_id', 'site_name', 'site_category', 'vendor', 'end_date', 'delay_days', 'status']
            avail_cols = [c for c in cols_disp if c in delay_df.columns]
            st.dataframe(delay_df[avail_cols].rename(columns={'end_date':'Target RFS', 'delay_days':'Delay (Hari)'}), use_container_width=True, hide_index=True)
        else:
            st.warning("Kolom 'end_date' tidak ditemukan untuk menghitung delay.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_t2:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#38BDF8; font-size:1rem; margin-bottom:10px;'>TREND PROGRESS</h3>", unsafe_allow_html=True)
        # Mock Trend Data based on actuals if available, else placeholder
        if not ms_df.empty and 'actual_end' in ms_df.columns:
            trend = ms_df.dropna(subset=['actual_end']).sort_values('actual_end')
            if not trend.empty and 'weight' in trend.columns:
                # Convert weight to numeric safely
                trend['weight'] = pd.to_numeric(trend['weight'], errors='coerce').fillna(0)
                total_weight = trend['weight'].sum()
                
                if total_weight > 0:
                    trend['cum_progress'] = (trend['weight'].cumsum() / total_weight) * 100
                else:
                    trend['cum_progress'] = np.linspace(0, 100, len(trend))
            else:
                trend['cum_progress'] = np.linspace(0, 100, len(trend))
                
            fig_trend = create_scatter_trend(trend, 'actual_end', 'cum_progress', "S-Curve")
        else:
            dates = pd.date_range(start=datetime.now()-timedelta(days=60), periods=10)
            vals = np.linspace(20, 80, 10)
            trend_df = pd.DataFrame({'actual_end': dates, 'cum_progress': vals})
            fig_trend = create_scatter_trend(trend_df, 'actual_end', 'cum_progress', "S-Curve (Simulated)")
            
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    dashboard_page()
