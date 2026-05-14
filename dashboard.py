import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase_db import read_all_sheets, read_sheet
import numpy as np

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

def dashboard_page():
    inject_dark_css()
    if 'master_project_filter' not in st.session_state:
        st.session_state.master_project_filter = "ALL"

    try:
        with st.spinner("🔄 Loading..."):
            all_data = read_all_sheets()
        df = all_data.get('projects', pd.DataFrame())
        ms_df = all_data.get('milestones', pd.DataFrame())
        
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

    df['progress'] = get_safe_numeric(df['progress'])
    for col in ['planned_end', 'actual_end']:
        if col in ms_df.columns: ms_df[col] = pd.to_datetime(ms_df[col], errors='coerce')

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
        except:
            pass
        
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"###  Site: {len(df)}")
    st.sidebar.markdown(f"### 🔄 Update: {datetime.now().strftime('%H:%M')}")

    st.markdown("""<div class='header-container'><div class='header-title'><h1>MCP TOWER PROJECT</h1><p>Deployment Dashboard</p></div><div style='display:flex; gap:15px; align-items:center;'><button style='background:#38BDF8; color:#FFFFFF !important; border:none; padding:8px 15px; border-radius:6px; cursor:pointer; font-size:0.8rem;'>📅 Periode: 20 Mei - 20 Jun 2024</button><button style='background:#38BDF8; color:#0F172A !important; border:none; padding:8px 15px; border-radius:6px; cursor:pointer; font-weight:bold; font-size:0.8rem;' onclick='document.location.reload()'>🔄 Refresh</button></div></div>""", unsafe_allow_html=True)

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
        (" RATA-RATA PROGRESS", f"{avg_prog:.1f}%", "Target: 100%", "text-blue")
    ]

    cols = st.columns(6)
    for i, (title, value, sub, color_class) in enumerate(kpis):
        with cols[i]:
            st.markdown(f"""<div class='kpi-card'><div class='kpi-title'>{title}</div><div class='kpi-value'>{value}</div><div class='kpi-sub {color_class}'>{sub}</div></div>""", unsafe_allow_html=True)

        # ─── ROW 1: DONUT CHARTS (FIXED) ───
    col_d1, col_d2, col_d3 = st.columns([1, 1, 1.5])
    
    with col_d1:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#CBD5E1 !important; font-size:0.9rem; margin-bottom:10px; text-align:center;'>PROGRESS OVERVIEW</h3>", unsafe_allow_html=True)
        
        if 'status' in df.columns and not df.empty:
            status_counts = df['status'].dropna().value_counts()
            status_map = {
                'DONE': '#10B981', 'ON_TRACK': '#10B981',
                'ONGOING': '#F59E0B', 
                'PENDING': '#94A3B8', 
                'DELAYED': '#EF4444', 'CRITICAL': '#7F1D1D'
            }
            # Handle NaN avg_prog
            center_val = f"{avg_prog:.0f}%" if not pd.isna(avg_prog) else "0%"
            fig1 = create_donut_chart_safe(status_counts, "", status_map, center_text=center_val)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.markdown("<p style='text-align:center; color:#94A3B8; padding:20px;'>📭 Data status belum tersedia</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_d2:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#CBD5E1 !important; font-size:0.9rem; margin-bottom:10px; text-align:center;'>SITE BY KATEGORI</h3>", unsafe_allow_html=True)
        
        if 'site_category' in df.columns and not df.empty:
            cat_series = df['site_category'].dropna().value_counts()
            cat_map = {
                'New Site': '#3B82F6', 
                'Collocation': '#8B5CF6', 
                'Upgrade': '#F59E0B', 
                'Relocation': '#EF4444',
                'Indoor': '#EC4899'  # Fallback untuk tipe lain
            }
            fig2 = create_donut_chart_safe(cat_series, "", cat_map)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.markdown("<p style='text-align:center; color:#94A3B8; padding:20px;'>ℹ️ Data kategori belum diisi</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_d3:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        if 'vendor' in df.columns:
            group_col, title_bar = 'vendor', "SITE STATUS BY VENDOR"
        elif 'site_category' in df.columns:
            group_col, title_bar = 'site_category', "SITE STATUS BY CATEGORY"
        else:
            group_col, title_bar = 'status', "SITE STATUS"
            
        clean_df = df.dropna(subset=[group_col])
        if not clean_df.empty and 'status' in clean_df.columns:
            pivot = clean_df.groupby(group_col)['status'].value_counts().unstack(fill_value=0)
            
            stack_order = ['DELAYED', 'CRITICAL', 'ONGOING', 'PENDING', 'DONE', 'ON_TRACK']
            available_cats = [c for c in stack_order if c in pivot.columns]
            if not available_cats: available_cats = pivot.columns.tolist()
            stack_colors = ['#EF4444', '#7F1D1D', '#F59E0B', '#94A3B8', '#10B981', '#10B981']
            
            if not pivot.empty:
                fig3 = create_stacked_bar(pivot, group_col, available_cats, stack_colors[:len(available_cats)])
                fig3.update_layout(title=dict(text=title_bar, x=0.5, font=dict(color='#CBD5E1', size=14)))
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.markdown("<p style='text-align:center; color:#94A3B8;'>📭 Tidak ada data</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='text-align:center; color:#94A3B8;'>⚠️ Data vendor/kategori tidak tersedia</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    col_m1, col_m2, col_m3 = st.columns([1.5, 1, 1])
    with col_m1:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#CBD5E1 !important; font-size:1rem; margin-bottom:10px;'>OVERALL MILESTONE PROGRESS</h3>", unsafe_allow_html=True)
        if not ms_df.empty:
            ms_pivot = ms_df.groupby('name')['status'].value_counts().unstack(fill_value=0)
            total_ms = ms_df.groupby('name')['id'].count()
            steps = ['Survey', 'Design', 'Permit', 'Construction', 'Installation', 'Integration', 'RFS']
            avail_steps = [s for s in steps if s in ms_pivot.index]
            if not avail_steps: avail_steps = ms_pivot.index.tolist()[:5]
            for step in avail_steps:
                done = ms_pivot.loc[step].get('DONE', 0)
                total = total_ms.get(step, 1)
                pct = (done/total)*100
                color = '#10B981' if pct >= 80 else ('#F59E0B' if pct >= 40 else '#EF4444')
                st.markdown(f"""<div style='display:flex; align-items:center; margin-bottom:8px;'><div style='width:80px; font-size:0.8rem; color:#FFFFFF !important; font-weight:bold;'>{step}</div><div style='flex:1; height:8px; background:#334155; border-radius:4px; overflow:hidden;'><div style='width:{pct}%; height:100%; background:{color};'></div></div><div style='width:40px; text-align:right; font-size:0.7rem; color:#CBD5E1;'>{pct:.0f}%</div></div>""", unsafe_allow_html=True)
        else:
            st.info("Data milestone kosong.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_m2:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#CBD5E1 !important; font-size:1rem; margin-bottom:10px;'>ISSUE SUMMARY</h3>", unsafe_allow_html=True)
        fig_iss = go.Figure(data=[go.Bar(x=['High', 'Medium', 'Low'], y=[6, 11, 6], marker_color=['#EF4444', '#F59E0B', '#10B981'])])
        fig_iss.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'))
        st.plotly_chart(fig_iss, use_container_width=True)
        st.markdown("<div style='text-align:center; font-size:2rem; font-weight:bold; color:#FFFFFF !important;'>23</div><div style='text-align:center; color:#CBD5E1; font-size:0.8rem;'>TOTAL ISSUE</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_m3:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#CBD5E1 !important; font-size:1rem; margin-bottom:10px;'>RISK MATRIX</h3>", unsafe_allow_html=True)
        risk_data = np.random.randint(0, 5, (5, 5))
        fig_risk = px.imshow(risk_data, text_auto=True, aspect="auto", color_continuous_scale="RdYlGn_r", zmin=0, zmax=10)
        fig_risk.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), coloraxis_showscale=False)
        st.plotly_chart(fig_risk, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    col_t1, col_t2 = st.columns([1.5, 1])
    with col_t1:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#EF4444 !important; font-size:1rem; margin-bottom:10px;'> SITE DELAY (TOP 5)</h3>", unsafe_allow_html=True)
        delay_df = df[df['status'].isin(['DELAYED', 'CRITICAL'])].copy()
        if 'end_date' in delay_df.columns:
            delay_df['end_date_dt'] = pd.to_datetime(delay_df['end_date'], errors='coerce')
            delay_df['delay_days'] = (datetime.now() - delay_df['end_date_dt']).dt.days
            delay_df = delay_df.sort_values('delay_days', ascending=False).head(5)
            st.dataframe(delay_df[['site_id', 'site_name', 'site_category', 'vendor', 'end_date', 'delay_days', 'status']].rename(columns={'end_date':'Target RFS', 'delay_days':'Delay (Hari)'}), use_container_width=True, hide_index=True)
        else:
            st.warning("Kolom 'end_date' tidak ditemukan.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_t2:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#38BDF8 !important; font-size:1rem; margin-bottom:10px;'>TREND PROGRESS</h3>", unsafe_allow_html=True)
        if not ms_df.empty and 'actual_end' in ms_df.columns:
            trend = ms_df.dropna(subset=['actual_end']).sort_values('actual_end')
            if not trend.empty and 'weight' in trend.columns:
                trend['weight'] = pd.to_numeric(trend['weight'], errors='coerce').fillna(0)
                total_w = trend['weight'].sum()
                trend['cum_progress'] = (trend['weight'].cumsum() / total_w * 100) if total_w > 0 else np.linspace(0, 100, len(trend))
            else:
                trend['cum_progress'] = np.linspace(0, 100, len(trend))
            fig_trend = create_scatter_trend(trend, 'actual_end', 'cum_progress', "S-Curve")
        else:
            trend_df = pd.DataFrame({'actual_end': pd.date_range(start=datetime.now()-timedelta(days=60), periods=10), 'cum_progress': np.linspace(20, 80, 10)})
            fig_trend = create_scatter_trend(trend_df, 'actual_end', 'cum_progress', "S-Curve (Simulated)")
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    dashboard_page()
