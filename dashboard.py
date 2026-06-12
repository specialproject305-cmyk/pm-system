import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from supabase_db import read_all_sheets, read_sheet
import numpy as np

# ─────────────────────────────────────────────────────────────
# 🎨 PROFESSIONAL THEME & ADVANCED UI CSS
# ─────────────────────────────────────────────────────────────
def inject_professional_css():
    st.markdown("""
    <style>
        /* === BASE STYLING === */
        .stApp { 
            background: linear-gradient(135deg, #0B1120 0%, #1A1F3A 100%);
            color: #FFFFFF; 
            font-family: 'Segoe UI', 'Inter', sans-serif;
        }
        
        /* === SIDEBAR === */
        [data-testid="stSidebar"] { 
            background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
            border-right: 2px solid #38BDF8;
        }
        [data-testid="stSidebar"] * { 
            color: #E2E8F0 !important; 
        }
        .stSidebar .stSelectbox > div { 
            background-color: #0F172A; 
            border: 1px solid #334155; 
            color: #FFF !important;
        }
        
        /* === HEADER SECTION === */
        .dashboard-header {
            background: linear-gradient(135deg, #1E3A5F 0%, #0F172A 100%);
            padding: 25px 30px;
            border-radius: 16px;
            border: 2px solid #38BDF8;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px rgba(56, 189, 248, 0.1);
        }
        .dashboard-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 900;
            color: #38BDF8;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .dashboard-header p {
            margin: 8px 0 0 0;
            font-size: 0.95rem;
            color: #CBD5E1;
            font-weight: 500;
        }
        
        /* === KPI CARDS - ENHANCED === */
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .kpi-card {
            background: linear-gradient(135deg, #1E293B 0%, #162A4A 100%);
            border-radius: 14px;
            padding: 20px;
            border: 2px solid #334155;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #38BDF8, #8B5CF6);
        }
        
        .kpi-card:hover {
            transform: translateY(-5px);
            border-color: #38BDF8;
            box-shadow: 0 12px 24px rgba(56, 189, 248, 0.2);
        }
        
        .kpi-icon {
            font-size: 1.8rem;
            margin-bottom: 8px;
        }
        
        .kpi-title {
            font-size: 0.75rem;
            color: #94A3B8;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }
        
        .kpi-value {
            font-size: 2.2rem;
            font-weight: 900;
            color: #FFFFFF;
            margin: 5px 0;
            line-height: 1;
        }
        
        .kpi-sub {
            font-size: 0.8rem;
            color: #64748B;
            margin-top: 8px;
            font-weight: 500;
        }
        
        /* === CHART BOXES === */
        .chart-box {
            background: linear-gradient(135deg, #1E293B 0%, #162A4A 100%);
            border-radius: 14px;
            padding: 20px;
            border: 2px solid #334155;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            transition: border-color 0.3s ease;
        }
        
        .chart-box:hover {
            border-color: #38BDF8;
        }
        
        .chart-box h3 {
            font-size: 1rem !important;
            margin-bottom: 15px !important;
            color: #38BDF8 !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .chart-box h4 {
            font-size: 0.9rem !important;
            color: #CBD5E1 !important;
            margin-bottom: 10px !important;
        }
        
        /* === SECTION DIVIDER === */
        .section-divider {
            height: 2px;
            background: linear-gradient(90deg, transparent, #38BDF8, transparent);
            margin: 30px 0;
            border: none;
        }
        
        /* === DATA TABLE STYLING === */
        .stDataFrame {
            border-radius: 10px;
            overflow: hidden;
        }
        [data-testid="stDataFrame"] {
            background-color: #1E293B !important;
        }
        
        /* === STATUS BADGE === */
        .status-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .status-done { background-color: rgba(16, 185, 129, 0.2); color: #10B981; }
        .status-progress { background-color: rgba(245, 158, 11, 0.2); color: #F59E0B; }
        .status-pending { background-color: rgba(148, 163, 184, 0.2); color: #94A3B8; }
        .status-delayed { background-color: rgba(239, 68, 68, 0.2); color: #EF4444; }
        
        /* === CONTROL PANEL === */
        .control-panel {
            background: linear-gradient(135deg, #1E293B 0%, #162A4A 100%);
            padding: 15px 20px;
            border-radius: 12px;
            border: 1px solid #334155;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .control-panel button {
            background: linear-gradient(135deg, #38BDF8 0%, #0EA5E9 100%);
            border: none;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .control-panel button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(56, 189, 248, 0.3);
        }
        
        /* === METRIC ROW === */
        .metric-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .metric-item {
            background: linear-gradient(135deg, #1E293B 0%, #162A4A 100%);
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #38BDF8;
        }
        
        .metric-item.success { border-left-color: #10B981; }
        .metric-item.warning { border-left-color: #F59E0B; }
        .metric-item.danger { border-left-color: #EF4444; }
        .metric-item.info { border-left-color: #3B82F6; }
        
        .metric-label {
            font-size: 0.8rem;
            color: #94A3B8;
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .metric-value {
            font-size: 1.8rem;
            font-weight: 900;
            color: #FFFFFF;
        }
        
        .metric-percent {
            font-size: 0.85rem;
            color: #CBD5E1;
            margin-top: 5px;
        }
        
        /* === TEXT COLORS === */
        .text-success { color: #10B981 !important; }
        .text-warning { color: #F59E0B !important; }
        .text-danger { color: #EF4444 !important; }
        .text-info { color: #38BDF8 !important; }
        
        /* === PERFORMANCE CARD === */
        .perf-card {
            background: linear-gradient(135deg, #1E293B 0%, #162A4A 100%);
            padding: 15px;
            border-radius: 12px;
            border: 1px solid #334155;
            text-align: center;
        }
        
        .perf-card:hover {
            border-color: #38BDF8;
            box-shadow: 0 4px 12px rgba(56, 189, 248, 0.15);
        }
        
        .perf-card .name {
            font-weight: 700;
            color: #FFFFFF;
            margin-bottom: 10px;
        }
        
        .perf-card .metric {
            font-size: 0.9rem;
            color: #CBD5E1;
            margin: 5px 0;
        }
        
        /* === DELAY CARD === */
        .delay-item {
            background: linear-gradient(135deg, #1E293B 0%, #162A4A 100%);
            padding: 12px;
            border-radius: 8px;
            border-left: 3px solid #EF4444;
            margin-bottom: 10px;
        }
        
        /* === SCROLLBAR === */
        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #0F172A;
        }
        ::-webkit-scrollbar-thumb {
            background: #38BDF8;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #0EA5E9;
        }
    </style>
    """, unsafe_allow_html=True)

def get_safe_numeric(series):
    return pd.to_numeric(series, errors='coerce').fillna(0)

def render_kpi_card(icon, title, value, subtitle, color_class):
    """Render a KPI card with proper formatting"""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub {color_class}">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def render_metric_item(label, value, percentage, style_class):
    """Render a metric item"""
    st.markdown(f"""
    <div class="metric-item {style_class}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-percent">{percentage}</div>
    </div>
    """, unsafe_allow_html=True)

def dashboard_page():
    inject_professional_css()
    
    try:
        with st.spinner("🔄 Loading dashboard..."):
            all_data = read_all_sheets()
        df = all_data.get('projects', pd.DataFrame())
        materials_df = all_data.get('materials', pd.DataFrame())
        milestones_df = all_data.get('milestones', pd.DataFrame())
    except Exception as e:
        st.error(f"⚠️ Error loading data: {e}")
        return

    if df.empty:
        st.info("📋 No site data available.")
        return

    # Apply Global Filter
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid_sites = df[df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
        df = df[df['id'].isin(valid_sites)]
        milestones_df = milestones_df[milestones_df['project_id'].isin(valid_sites)] if not milestones_df.empty else milestones_df

    df['progress'] = get_safe_numeric(df['progress'])
    for col in ['planned_end', 'actual_end']:
        if col in milestones_df.columns: 
            milestones_df[col] = pd.to_datetime(milestones_df[col], errors='coerce')

    # ===== HEADER =====
    st.markdown("""
    <div class="dashboard-header">
        <h1>📊 PROJECT MANAGEMENT DASHBOARD</h1>
        <p>Real-time project status, milestones & performance metrics</p>
    </div>
    """, unsafe_allow_html=True)

    # ===== CONTROL PANEL =====
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 2, 1])
    with col_ctrl1:
        if st.button("🔄 Refresh Data", use_container_width=True, key="refresh_btn"):
            st.cache_data.clear()
            st.rerun()
    with col_ctrl2:
        period_dates = st.date_input(
            "📅 Period", 
            value=(date.today() - timedelta(days=30), date.today()), 
            max_value=date.today(), 
            key="dash_period", 
            label_visibility="collapsed"
        )
    with col_ctrl3:
        if st.button("📥 Export Report", use_container_width=True, key="export_btn"):
            st.info("Export feature coming soon")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ===== KPI CARDS =====
    total_sites = len(df)
    rfs_count = len(df[df['status']=='DONE'])
    on_prog = len(df[df['status']=='ONGOING'])
    not_start = len(df[df['status']=='PENDING'])
    delay_count = len(df[df['status'].isin(['DELAYED','CRITICAL'])])
    avg_prog = df['progress'].mean()

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        render_kpi_card("📡", "Total Sites", total_sites, "Active projects", "text-info")
    with col2:
        render_kpi_card("✅", "RFS/On Air", rfs_count, f"{rfs_count/total_sites*100:.0f}% completion", "text-success")
    with col3:
        render_kpi_card("⚙️", "In Progress", on_prog, f"{on_prog/total_sites*100:.0f}% of total", "text-warning")
    with col4:
        render_kpi_card("⏳", "Not Started", not_start, f"{not_start/total_sites*100:.0f}% pending", "text-info")
    with col5:
        render_kpi_card("🔴", "Delayed", delay_count, f"{delay_count/total_sites*100:.0f}% at risk", "text-danger")
    with col6:
        render_kpi_card("📈", "Avg Progress", f"{avg_prog:.1f}%", "Target: 100%", "text-success")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ===== SECTION: STATUS OVERVIEW =====
    st.markdown('<div class="chart-box"><h3>📊 Project Status Distribution</h3>', unsafe_allow_html=True)
    
    col_overview1, col_overview2, col_overview3 = st.columns([1, 1, 1])
    
    with col_overview1:
        if 'status' in df.columns and not df.empty:
            status_counts = df['status'].value_counts()
            fig = px.pie(
                values=status_counts.values, 
                names=status_counts.index, 
                hole=0.6,
                color_discrete_map={
                    'DONE':'#10B981',
                    'ON_TRACK':'#10B981',
                    'ONGOING':'#F59E0B',
                    'PENDING':'#94A3B8',
                    'DELAYED':'#EF4444',
                    'CRITICAL':'#7F1D1D'
                }
            )
            fig.update_layout(
                height=300, 
                margin=dict(t=10,b=10,l=10,r=10), 
                paper_bgcolor='rgba(0,0,0,0)', 
                font=dict(color='#FFFFFF',size=10),
                showlegend=True,
                legend=dict(font=dict(size=9))
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col_overview2:
        if 'site_category' in df.columns and not df.empty:
            cat_counts = df['site_category'].value_counts()
            fig2 = px.pie(
                values=cat_counts.values, 
                names=cat_counts.index, 
                hole=0.6,
                color_discrete_map={
                    'New Site':'#3B82F6',
                    'Collocation':'#8B5CF6',
                    'Upgrade':'#F59E0B',
                    'Relocation':'#EF4444'
                }
            )
            fig2.update_layout(
                height=300, 
                margin=dict(t=10,b=10,l=10,r=10), 
                paper_bgcolor='rgba(0,0,0,0)', 
                font=dict(color='#FFFFFF',size=10),
                showlegend=True,
                legend=dict(font=dict(size=9))
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    with col_overview3:
        if 'vendor' in df.columns and 'status' in df.columns:
            pivot = df.groupby('vendor')['status'].value_counts().unstack(fill_value=0)
            if not pivot.empty:
                fig3 = px.bar(
                    pivot, 
                    x=pivot.index, 
                    y=pivot.columns, 
                    barmode='stack',
                    color_discrete_map={
                        'DONE':'#10B981',
                        'ONGOING':'#F59E0B',
                        'PENDING':'#94A3B8',
                        'DELAYED':'#EF4444'
                    }
                )
                fig3.update_layout(
                    height=300, 
                    margin=dict(t=10,b=10,l=10,r=10), 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#FFFFFF',size=9), 
                    legend=dict(orientation='v', font=dict(size=8)),
                    xaxis_title="",
                    yaxis_title="Count"
                )
                st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ===== SECTION: PIC PERFORMANCE =====
    st.markdown('<div class="chart-box"><h3>👷 PIC Performance Snapshot</h3>', unsafe_allow_html=True)
    
    if not milestones_df.empty and 'assigned_to' in milestones_df.columns:
        pic_list = ['Sitac', 'Legal', 'Engineering', 'Procurement', 'Project', 'Vendor Management']
        cols_pic = st.columns(len(pic_list))
        
        for i, pic in enumerate(pic_list):
            pic_tasks = milestones_df[milestones_df['assigned_to'] == pic]
            total = len(pic_tasks)
            if total > 0:
                done = len(pic_tasks[pic_tasks['status'] == 'DONE'])
                completion_rate = (done / total) * 100
                
                if completion_rate > 80: 
                    color, border, status = '#10B981', '#10B981', '✅ On Track'
                elif completion_rate > 50: 
                    color, border, status = '#F59E0B', '#F59E0B', '⚠️ In Progress'
                else: 
                    color, border, status = '#EF4444', '#EF4444', '❌ At Risk'
                
                with cols_pic[i]:
                    st.markdown(f"""
                    <div class="perf-card" style="border-left: 4px solid {border};">
                        <div class="name">{pic}</div>
                        <div class="metric" style="color: {color};">📊 {completion_rate:.0f}%</div>
                        <div class="metric">📋 {done}/{total} tasks</div>
                        <div class="metric" style="color: {color}; font-weight: 600; margin-top: 8px;">{status}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                with cols_pic[i]:
                    st.markdown(f"""
                    <div class="perf-card" style="border-left: 4px solid #94A3B8;">
                        <div class="name">{pic}</div>
                        <div class="metric" style="color: #94A3B8;">No assignments</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ===== SECTION: CRITICAL SITES & TRENDS =====
    col_critical, col_trend = st.columns([1.5, 1])
    
    with col_critical:
        st.markdown('<div class="chart-box"><h3>🔴 Critical & Delayed Sites</h3>', unsafe_allow_html=True)
        delay_df = df[df['status'].isin(['DELAYED', 'CRITICAL'])].sort_values('progress')
        
        if not delay_df.empty:
            for _, row in delay_df.head(5).iterrows():
                days_overdue = (date.today() - pd.to_datetime(row.get('planned_end')).date()).days if pd.notna(row.get('planned_end')) else 0
                st.markdown(f"""
                <div class="delay-item">
                    <strong style="color: #FFFFFF;">{row.get('site_id', 'N/A')} - {row.get('site_name', 'N/A')}</strong>
                    <div style="color: #CBD5E1; font-size: 0.85rem; margin-top: 5px;">
                        Status: <span style="color: #EF4444;">● {row.get('status', '?')}</span><br>
                        Progress: <span style="color: #38BDF8;">{row.get('progress', 0):.0f}%</span> | 
                        Overdue: <span style="color: #EF4444;">{days_overdue} days</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No delayed sites detected! Great progress!")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_trend:
        st.markdown('<div class="chart-box"><h3>📈 Progress Trend</h3>', unsafe_allow_html=True)
        
        if not df.empty:
            df_sorted = df.sort_values('progress').reset_index(drop=True)
            fig_t = go.Figure()
            fig_t.add_trace(go.Scatter(
                y=df_sorted['progress'].values,
                mode='lines+markers',
                fill='tozeroy',
                line=dict(color='#38BDF8', width=3),
                fillcolor='rgba(56, 189, 248, 0.2)',
                marker=dict(size=6, color='#38BDF8')
            ))
            fig_t.update_layout(
                height=250, 
                margin=dict(t=10,b=10,l=10,r=10),
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#FFFFFF', size=9),
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)', zeroline=False),
                hovermode='x unified'
            )
            st.plotly_chart(fig_t, use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ===== SECTION: DETAILED SITE LIST =====
    st.markdown('<div class="chart-box"><h3>📋 All Sites - Detailed View</h3>', unsafe_allow_html=True)
    
    # Create display dataframe
    display_df = df[[col for col in ['site_id', 'site_name', 'status', 'progress', 'vendor', 'site_category'] if col in df.columns]].copy()
    display_df['progress'] = display_df['progress'].astype(int).astype(str) + '%'
    
    # Sort by status
    status_order = {'CRITICAL': 0, 'DELAYED': 1, 'ONGOING': 2, 'PENDING': 3, 'DONE': 4}
    display_df['status_order'] = display_df['status'].map(lambda x: status_order.get(x, 5))
    display_df = display_df.sort_values('status_order').drop('status_order', axis=1)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ===== SECTION: KEY STATISTICS =====
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-box"><h3>📊 Key Statistics & Insights</h3>', unsafe_allow_html=True)
    
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    with col_stat1:
        completion_rate = (rfs_count / total_sites * 100) if total_sites > 0 else 0
        render_metric_item("Completion Rate", f"{completion_rate:.1f}%", f"{rfs_count}/{total_sites} sites", "success")
    
    with col_stat2:
        on_track_rate = ((on_prog + not_start) / total_sites * 100) if total_sites > 0 else 0
        render_metric_item("On Track Rate", f"{on_track_rate:.1f}%", f"{on_prog + not_start} sites", "warning")
    
    with col_stat3:
        delay_rate = (delay_count / total_sites * 100) if total_sites > 0 else 0
        render_metric_item("Delay Rate", f"{delay_rate:.1f}%", f"{delay_count} sites", "danger")
    
    with col_stat4:
        avg_material = materials_df['quantity'].mean() if not materials_df.empty else 0
        render_metric_item("Avg Materials/Site", f"{avg_material:.0f}", "per project", "info")
    
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    dashboard_page()
