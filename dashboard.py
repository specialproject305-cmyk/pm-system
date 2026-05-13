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
        .stSidebar button { width: 100%; text-align: left; color: #FFFFFF !important; background: transparent; border: none; padding: 10px; margin: 5px 0; border-radius: 8px; }
        .stSidebar button:hover { background-color: #334155; color: #FFF !important; }
        
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
        
        #MainMenu {visibility: hidden;} header {visibility: hidden;} .stDecoration {display: none;}
        .text-green { color: #10B981 !important; } .text-yellow { color: #F59E0B !important; }
        .text-red { color: #EF4444 !important; } .text-blue { color: #3B82F6 !important; }
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 🧠 HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_safe_numeric(series):
    return pd.to_numeric(series, errors='coerce').fillna(0)

def create_donut_chart(df, value_col, title, color_map):
    fig = px.pie(df, values=value_col, names=df.index, title=title, hole=0.7, color=df.index, color_discrete_map=color_map)
    fig.update_traces(textposition='inside', textinfo='percent+label', hoverinfo='label+value', marker=dict(line=dict(color='#1E293B', width=2)), textfont=dict(color='#FFFFFF', size=12))
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=40, b=0), height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), title=dict(text=title, x=0.5, y=0.95, font=dict(size=16, color='#CBD5E1')))
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
        
    if selected_mp != " SEMUA PROYEK":
        target_id = selected_mp.split(" - ")[0]
        df = df[df['master_project_id'] == target_id]
        valid_sites = df['id'].tolist()
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)]
        
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"###  Site: {len(df)}")
    st.sidebar.markdown(f"### 🔄 Update: {datetime.now().strftime('%H:%M')}")

    st.markdown("""<div class='header-container'><div class='header-title'><h1>MCP TOWER PROJECT</h1><p>Deployment Dashboard</p></div><div style='display:flex; gap:15px; align-items:center;'><button style='background:#334155; color:#FFFFFF !important; border:none; padding:8px 15px; border-radius:6px; cursor:pointer; font-size:0.8rem;'>📅 Periode: 20 Mei - 20 Jun 2024</button><button style='background:#38BDF8; color:#0F172A !important; border:none; padding:8px 15px; border-radius:6px; cursor:pointer; font-weight:bold; font-size:0.8rem;' onclick='document.location.reload()'>🔄 Refresh</button></div></div>""", unsafe_allow_html=True)

    total_sites = len(df)
    rfs_count = len(df[df['status']=='DONE'])
    on_prog = len(df[df['status']=='ONGOING'])
    not_start = len(df[df['status']=='PENDING'])
    delay_count = len(df[df['status'].isin(['DELAYED','CRITICAL'])])
    avg_prog = df['progress'].mean()

        # ─── KPI CARDS (WITH NaN HANDLING) ───
    total_sites = len(df)
    
    # Handle empty dataframe
    if total_sites == 0:
        rfs_count = 0
        on_prog = 0
        not_start = 0
        delay_count = 0
        avg_prog = 0.0
    else:
        rfs_count = len(df[df['status']=='DONE']) if 'status' in df.columns else 0
        on_prog = len(df[df['status']=='ONGOING']) if 'status' in df.columns else 0
        not_start = len(df[df['status']=='PENDING']) if 'status' in df.columns else 0
        delay_count = len(df[df['status'].isin(['DELAYED','CRITICAL'])]) if 'status' in df.columns else 0
        avg_prog = df['progress'].mean() if 'progress' in df.columns else 0.0
        # Handle NaN
        if pd.isna(avg_prog):
            avg_prog = 0.0

    kpis = [
        ("📡 TOTAL SITE", total_sites, "Sites", "text-blue"),
        ("🟢 RFS (ON AIR)", rfs_count, f"{(rfs_count/total_sites*100):.0f}% dari total" if total_sites > 0 else "0% dari total", "text-green"),
        ("⚙️ ON PROGRESS", on_prog, f"{(on_prog/total_sites*100):.0f}% dari total" if total_sites > 0 else "0% dari total", "text-yellow"),
        ("⚪ NOT STARTED", not_start, f"{(not_start/total_sites*100):.0f}% dari total" if total_sites > 0 else "0% dari total", "text-gray"),
        ("🔴 DELAY SITE", delay_count, f"{(delay_count/total_sites*100):.0f}% dari total" if total_sites > 0 else "0% dari total", "text-red"),
        ("📊 RATA-RATA PROGRESS", f"{avg_prog:.1f}%", "Target: 100%", "text-blue")
    ]

    cols = st.columns(6)
    for i, (title, value, sub, color_class) in enumerate(kpis):
        with cols[i]:
            st.markdown(f"""<div class='kpi-card'><div class='kpi-title'>{title}</div><div class='kpi-value'>{value}</div><div class='kpi-sub {color_class}'>{sub}</div></div>""", unsafe_allow_html=True)

    # ─── ROW 1: DONUTS & CATEGORIES ───
    col_d1, col_d2, col_d3 = st.columns([1, 1, 1.5])
    
    with col_d1:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#CBD5E1 !important; font-size:0.9rem; margin-bottom:10px;'>PROGRESS OVERVIEW</h3>", unsafe_allow_html=True)
        
        if total_sites == 0 or 'status' not in df.columns:
            st.info("📭 Belum ada data status site. Silakan tambahkan site di menu Project Tracker.")
        else:
            status_counts = df['status'].value_counts()
            if status_counts.empty:
                st.info("📭 Data status masih kosong.")
            else:
                status_map = {'DONE':'#10B981', 'ONGOING':'#F59E0B', 'PENDING':'#94A3B8', 'DELAYED':'#EF4444', 'CRITICAL':'#7F1D1D', 'ON_TRACK':'#10B981'}
                fig1 = create_donut_chart(status_counts, None, "", status_map)
                if not pd.isna(avg_prog):
                    fig1.add_annotation(dict(text=f'{avg_prog:.0f}%', x=0.5, y=0.5, font_size=24, showarrow=False, font_color='#FFFFFF'))
                st.plotly_chart(fig1, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_d2:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#CBD5E1 !important; font-size:0.9rem; margin-bottom:10px;'>SITE BY KATEGORI</h3>", unsafe_allow_html=True)
        
        if 'site_category' not in df.columns:
            st.warning("⚠️ Kolom 'site_category' tidak tersedia di database.")
        elif df.empty:
            st.info("📭 Belum ada data site.")
        else:
            cat_counts = df['site_category'].dropna().value_counts()
            if cat_counts.empty:
                st.info("ℹ️ Data kategori belum diisi. Update site di menu Project Tracker.")
            else:
                cat_map = {'New Site':'#3B82F6', 'Collocation':'#8B5CF6', 'Upgrade':'#F59E0B', 'Relocation':'#EF4444'}
                fig2 = create_donut_chart(cat_counts, None, "", cat_map)
                st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_d3:
        st.markdown("<div class='chart-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#CBD5E1 !important; font-size:0.9rem; margin-bottom:10px;'>SITE STATUS BY VENDOR</h3>", unsafe_allow_html=True)
        
        if df.empty:
            st.info("📭 Belum ada data untuk ditampilkan.")
        elif 'vendor' not in df.columns and 'site_category' not in df.columns:
            st.warning("⚠️ Kolom 'vendor' atau 'site_category' tidak tersedia.")
        else:
            if 'vendor' in df.columns:
                group_col = 'vendor'
                title_bar = "SITE STATUS BY VENDOR"
            else:
                group_col = 'site_category'
                title_bar = "SITE STATUS BY CATEGORY"
                
            clean_df = df.dropna(subset=[group_col])
            if clean_df.empty or 'status' not in clean_df.columns:
                st.info("ℹ️ Data status atau vendor masih kosong.")
            else:
                pivot = clean_df.groupby(group_col)['status'].value_counts().unstack(fill_value=0)
                
                stack_order = ['DELAYED', 'CRITICAL', 'ONGOING', 'PENDING', 'DONE', 'ON_TRACK']
                available_cats = [c for c in stack_order if c in pivot.columns]
                if not available_cats: 
                    available_cats = pivot.columns.tolist()
                
                stack_colors = ['#EF4444', '#7F1D1D', '#F59E0B', '#94A3B8', '#10B981', '#10B981']
                
                if not pivot.empty:
                    fig3 = create_stacked_bar(pivot, group_col, available_cats, stack_colors[:len(available_cats)])
                    fig3.update_layout(title=dict(text=title_bar, x=0.5, font=dict(color='#CBD5E1')))
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info("📭 Tidak ada data untuk ditampilkan.")
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    dashboard_page()
