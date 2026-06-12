import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from supabase_db import read_all_sheets, read_sheet
import numpy as np

# ─────────────────────────────────────────────────────────────
# 🎨 DARK THEME & UI CSS
# ─────────────────────────────────────────────────────────────
def inject_dark_css():
    st.markdown("""
    <style>
        .stApp { background-color: #0B1120; color: #FFFFFF; font-family: 'Inter', sans-serif; }
        [data-testid="stSidebar"] { background-color: #1E293B; border-right: 1px solid #334155; }
        [data-testid="stSidebar"] * { color: #E2E8F0 !important; }
        .stSidebar h1, .stSidebar h2, .stSidebar h3, .stSidebar p, .stSidebar span, .stSidebar div, .stSidebar label { color: #FFFFFF !important; }
        .stSidebar .stSelectbox > div { background-color: #0F172A; border: 1px solid #334155; color: #FFF !important; }
        @media (max-width: 768px) { [data-testid="stSidebar"] { display: block !important; } }
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

def get_safe_numeric(series):
    return pd.to_numeric(series, errors='coerce').fillna(0)

def dashboard_page():
    inject_dark_css()
    
    try:
        with st.spinner("🔄 Loading..."):
            all_data = read_all_sheets()
        df = all_data.get('projects', pd.DataFrame())
        materials_df = all_data.get('materials', pd.DataFrame())
        milestones_df = all_data.get('milestones', pd.DataFrame())
    except Exception as e:
        st.error(f"⚠️ Error loading: {e}")
        return

    if df.empty:
        st.info("📋 Belum ada data site.")
        return

    # Apply Global Filter
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid_sites = df[df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
        df = df[df['id'].isin(valid_sites)]
        milestones_df = milestones_df[milestones_df['project_id'].isin(valid_sites)] if not milestones_df.empty else milestones_df

    df['progress'] = get_safe_numeric(df['progress'])
    for col in ['planned_end', 'actual_end']:
        if col in milestones_df.columns: milestones_df[col] = pd.to_datetime(milestones_df[col], errors='coerce')

    # ===== HEADER =====
    st.markdown(f"""
    <div style='text-align:center; background: linear-gradient(90deg, #1E3A5F 0%, #0F172A 100%); padding:10px 20px; border-radius:12px; margin-bottom:10px; border:1px solid #334155;'>
        <h1 style='margin:0; font-size:1.5rem; font-weight:800; color:#38BDF8;'>MCP TOWER PROJECT</h1>
        <p style='margin:2px 0; font-size:0.85rem; color:#CBD5E1;'>Deployment Dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    # ===== REFRESH & PERIOD =====
    st.markdown("<div style='background: linear-gradient(90deg, #1E3A5F 10%, #0F172A 90%); padding:10px 15px; border-radius:10px; margin-bottom:15px;'>", unsafe_allow_html=True)
    col_r1, col_r2 = st.columns([1, 2])
    with col_r1:
        if st.button("🔄 Refresh Data", key="refresh_btn", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_r2:
        st.date_input("📅 Periode", value=(date.today() - timedelta(days=30), date.today()), max_value=date.today(), key="dash_period", label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    # ===== KPI CARDS =====
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

    # ===== PIC PERFORMANCE SNAPSHOT =====
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
                    st.markdown(f"""<div style="background:{bg}; padding:12px; border-radius:10px; border-left:4px solid {border}; text-align:center;"><strong>{pic}</strong><br>📋 {total} | ✅ {done}<br>📈 {completion_rate:.0f}%</div>""", unsafe_allow_html=True)

    # ===== DONUT CHARTS ROW =====
    st.markdown("---")
    col_d1, col_d2, col_d3 = st.columns([1, 1, 1.5])
    
    with col_d1:
        st.markdown("<div class='chart-box'><h3 style='color:#CBD5E1; text-align:center;'>PROGRESS OVERVIEW</h3>", unsafe_allow_html=True)
        if 'status' in df.columns and not df.empty:
            status_counts = df['status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, hole=0.6, color_discrete_map={'DONE':'#10B981','ON_TRACK':'#10B981','ONGOING':'#F59E0B','PENDING':'#94A3B8','DELAYED':'#EF4444','CRITICAL':'#7F1D1D'})
            fig.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_d2:
        st.markdown("<div class='chart-box'><h3 style='color:#CBD5E1; text-align:center;'>SITE BY KATEGORI</h3>", unsafe_allow_html=True)
        if 'site_category' in df.columns and not df.empty:
            cat_counts = df['site_category'].value_counts()
            fig2 = px.pie(values=cat_counts.values, names=cat_counts.index, hole=0.6, color_discrete_map={'New Site':'#3B82F6','Collocation':'#8B5CF6','Upgrade':'#F59E0B','Relocation':'#EF4444'})
            fig2.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_d3:
        st.markdown("<div class='chart-box'><h3 style='color:#CBD5E1; text-align:center;'>SITE STATUS BY VENDOR</h3>", unsafe_allow_html=True)
        if 'vendor' in df.columns and 'status' in df.columns:
            pivot = df.groupby('vendor')['status'].value_counts().unstack(fill_value=0)
            if not pivot.empty:
                fig3 = px.bar(pivot, x=pivot.index, y=pivot.columns, title="", barmode='stack')
                fig3.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'), legend=dict(orientation='h', y=1.1))
                st.plotly_chart(fig3, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ===== SITE DELAY & TREND =====
    st.markdown("---")
    col_t1, col_t2 = st.columns([1.5, 1])
    with col_t1:
        st.markdown("<div class='chart-box'><h3 style='color:#EF4444;'>🔴 SITE DELAY (TOP 5)</h3>", unsafe_allow_html=True)
        delay_df = df[df['status'].isin(['DELAYED', 'CRITICAL'])].head(5)
        if not delay_df.empty:
            st.dataframe(delay_df[['site_id', 'site_name', 'status', 'progress']], use_container_width=True, hide_index=True)
        else:
            st.success("✅ Tidak ada site delayed!")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_t2:
        st.markdown("<div class='chart-box'><h3 style='color:#38BDF8;'>📈 TREND PROGRESS</h3>", unsafe_allow_html=True)
        if not df.empty:
            df_sorted = df.sort_values('progress')
            fig_t = px.line(df_sorted, y='progress', markers=True)
            fig_t.update_layout(height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#FFFFFF'))
            st.plotly_chart(fig_t, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    dashboard_page()
