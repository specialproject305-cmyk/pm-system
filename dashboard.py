import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from supabase_db import read_all_sheets
import numpy as np

# ─────────────────────────────────────────────────────────────
# 🎨 PROFESSIONAL LIGHT THEME CSS
# ─────────────────────────────────────────────────────────────
def inject_professional_css():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%); color: #1E293B; font-family: 'Segoe UI', sans-serif; }
        
        /* HEADER - lebih kecil */
        .dashboard-header { background: linear-gradient(135deg, #0369A1 0%, #0284C7 100%); padding: 12px 20px; border-radius: 10px; margin-bottom: 12px; }
        .dashboard-header h1 { font-size: 1.3rem; margin: 0; color: #FFF; }
        .dashboard-header p { font-size: 0.7rem; margin: 3px 0 0 0; color: #E0F2FE; }
        
        /* KPI CARDS - lebih kecil */
        .kpi-card { background: #FFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 6px; text-align: center; }
        .kpi-icon { font-size: 1.2rem; margin-bottom: 3px; }
        .kpi-title { font-size: 0.6rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 3px; }
        .kpi-value { font-size: 1.3rem; font-weight: 800; color: #0369A1; margin: 2px 0; line-height: 1; }
        .kpi-subtitle { font-size: 0.6rem; color: #94A3B8; }
        .status-done { color: #059669 !important; }
        .status-ongoing { color: #D97706 !important; }
        .status-pending { color: #7C3AED !important; }
        .status-delayed { color: #DC2626 !important; }
        
        /* CHART BOX - lebih kecil */
        .chart-box { background: #FFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px; margin-bottom: 10px; }
        .chart-box h3 { font-size: 0.7rem; margin: 0 0 6px 0; padding-bottom: 4px; border-bottom: 2px solid #0369A1; }
        
        /* SECTION DIVIDER */
        .section-divider { height: 0.5px; background: #E2E8F0; margin: 5px 0; }
        
        /* BUTTON */
        .stButton > button { font-size: 0.7rem !important; padding: 5px 12px !important; border-radius: 6px !important; }
        
        /* METRIC */
        .metric-item { padding: 6px 10px; border-radius: 6px; margin-bottom: 4px; }
        .metric-label { font-size: 0.7rem; }
        .metric-value { font-size: 0.8rem; }
        .metric-bar { height: 4px; margin-top: 4px; }
        
        /* TABLE */
        thead th { font-size: 0.65rem !important; padding: 4px 8px !important; }
        tbody td { font-size: 0.7rem !important; padding: 3px 8px !important; }
        
        /* SIDEBAR */
                /* SIDEBAR - keep main.py styling */
        [data-testid="stSidebar"] {
            /* inherit from main.py */
        }
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 📊 HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_safe_numeric(series):
    """Safely convert series to numeric"""
    return pd.to_numeric(series, errors='coerce').fillna(0)

def render_kpi_card(icon, title, value, subtitle, color_class="text-info"):
    """Render a single KPI card"""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtitle {color_class}">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def create_donut_chart(series, title, color_map):
    """Create a professional donut chart"""
    if series.empty:
        fig = go.Figure()
        fig.add_annotation(text="📭 No data", x=0.5, y=0.5, showarrow=False, 
                          font=dict(color='#94A3B8', size=14))
        fig.update_layout(height=200, margin=dict(l=0, r=0, t=30, b=0),
                         paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig
    
    labels = series.index.astype(str).tolist()
    values = series.values.tolist()
    colors = [color_map.get(label, '#94A3B8') for label in labels]
    
    fig = px.pie(values=values, names=labels, hole=0.65,
                color_discrete_sequence=colors)
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hoverinfo='label+value+percent',
        marker=dict(line=dict(color='#FFFFFF', width=2)),
        textfont=dict(color='#FFFFFF', size=11)
    )
    
    fig.update_layout(
        showlegend=True,
        margin=dict(l=0, r=0, t=35, b=0),
        height=200,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#475569', size=11),
        title=dict(text=title, x=0.5, font=dict(color='#0F172A', size=13, family='Arial, sans-serif'))
    )
    
    return fig

def create_stacked_bar(df, group_col, categories, colors, title=""):
    """Create a professional stacked bar chart"""
    fig = go.Figure()
    
    if df.empty:
        return fig
    
    x_values = df.index.astype(str)
    
    for i, cat in enumerate(categories):
        if cat in df.columns:
            color = colors[i] if i < len(colors) else '#94A3B8'
            fig.add_trace(go.Bar(
                x=x_values, y=df[cat], name=cat, marker_color=color,
                hovertemplate=f"<b>{cat}</b><br>%{{x}}: %{{y}}<extra></extra>",
                textfont=dict(color='#FFFFFF')
            ))
    
    fig.update_layout(
        barmode='stack',
        margin=dict(l=0, r=0, t=40, b=0),
        height=220,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#475569'),
        xaxis=dict(showgrid=False, linecolor='#E2E8F0'),
        yaxis=dict(showgrid=True, gridcolor='#E2E8F0', linecolor='#E2E8F0'),
        title=dict(text=title, x=0.5, font=dict(color='#0F172A', size=13)),
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_progress_chart(df, date_col, value_col, title):
    """Create a professional scatter/trend chart"""
    if df.empty:
        df = pd.DataFrame({
            date_col: pd.date_range(start=datetime.now()-timedelta(days=30), periods=10),
            value_col: np.linspace(20, 80, 10)
        })
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df[date_col], y=df[value_col],
        mode='lines+markers',
        name='Progress',
        line=dict(color='#0369A1', width=3),
        marker=dict(size=8, color='#0284C7', line=dict(color='#FFFFFF', width=2)),
        fill='tozeroy',
        fillcolor='rgba(3, 105, 161, 0.1)',
        hovertemplate='<b>%{x|%d %b}</b><br>Progress: %{y:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=200,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#475569'),
        xaxis=dict(showgrid=True, gridcolor='#E2E8F0', linecolor='#E2E8F0'),
        yaxis=dict(showgrid=True, gridcolor='#E2E8F0', linecolor='#E2E8F0'),
        title=dict(text=title, x=0.5, font=dict(color='#0F172A', size=13)),
        hovermode='x unified'
    )
    
    return fig

# ─────────────────────────────────────────────────────────────
# 📱 MAIN DASHBOARD
# ─────────────────────────────────────────────────────────────

def dashboard_page():
    """Main dashboard page with professional layout"""
    inject_professional_css()
    
    # Load data
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
    
    # Apply filters
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
            st.info("✨ Export feature coming soon")
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ===== FILTER BY PM =====
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        pm_list = ['ALL'] + sorted(df['pm'].dropna().unique().tolist()) if 'pm' in df.columns else ['ALL']
        selected_pm = st.selectbox("👤 Filter by PM:", pm_list, key="dash_pm_filter")
        if selected_pm != 'ALL':
            df = df[df['pm'] == selected_pm]
            valid_sites = df['id'].tolist()
            milestones_df = milestones_df[milestones_df['project_id'].isin(valid_sites)] if not milestones_df.empty else milestones_df
    
    # ===== KPI SECTION =====
    st.markdown('<h2 style="color: #0F172A; font-size: 1.1rem; margin-bottom: 16px;">📈 KEY PERFORMANCE INDICATORS</h2>', unsafe_allow_html=True)
    
    total_sites = len(df)
    rfs_count = len(df[df['status']=='DONE'])
    on_prog = len(df[df['status']=='ONGOING'])
    not_start = len(df[df['status']=='PENDING'])
    delay_count = len(df[df['status'].isin(['DELAYED','CRITICAL'])])
    avg_prog = df['progress'].mean()
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        render_kpi_card("📡", "Total Sites", total_sites, "Active projects")
    with col2:
        render_kpi_card("✅", "RFS/On Air", rfs_count, f"{rfs_count/total_sites*100:.0f}% complete" if total_sites > 0 else "0%", "status-done")
    with col3:
        render_kpi_card("⚙️", "In Progress", on_prog, f"{on_prog/total_sites*100:.0f}% of total" if total_sites > 0 else "0%", "status-ongoing")
    with col4:
        render_kpi_card("⏳", "Pending", not_start, f"{not_start/total_sites*100:.0f}% of total" if total_sites > 0 else "0%", "status-pending")
    with col5:
        render_kpi_card("🔴", "Delayed", delay_count, f"{delay_count/total_sites*100:.0f}% of total" if total_sites > 0 else "0%", "status-delayed")
    with col6:
        render_kpi_card("📊", "Avg Progress", f"{avg_prog:.1f}%", "Overall completion")
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # ===== PIC PERFORMANCE SNAPSHOT =====
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown('<h2 style="color: #0F172A; font-size: 1.1rem; margin-bottom: 16px;">👷 PIC PERFORMANCE SNAPSHOT</h2>', unsafe_allow_html=True)
    
    if not milestones_df.empty and 'assigned_to' in milestones_df.columns:
        pic_list = ['Sitac', 'Legal', 'Engineering', 'Procurement', 'Project', 'Vendor Management']
        cols_pic = st.columns(len(pic_list))
        
        for i, pic in enumerate(pic_list):
            pic_tasks = milestones_df[milestones_df['assigned_to'] == pic]
            total = len(pic_tasks)
            
            with cols_pic[i]:
                if total > 0:
                    done = len(pic_tasks[pic_tasks['status'] == 'DONE'])
                    delayed = len(pic_tasks[pic_tasks['status'].isin(['DELAYED', 'CRITICAL'])])
                    completion_rate = (done / total) * 100
                    
                    if completion_rate >= 80:
                        bg = 'linear-gradient(135deg, #ECFDF5, #D1FAE5)'
                        border = '#059669'
                        icon = '🟢'
                    elif completion_rate >= 50:
                        bg = 'linear-gradient(135deg, #FFFBEB, #FEF3C7)'
                        border = '#D97706'
                        icon = '🟡'
                    else:
                        bg = 'linear-gradient(135deg, #FEF2F2, #FEE2E2)'
                        border = '#DC2626'
                        icon = '🔴'
                    
                    st.markdown(f"""
                    <div style="background:{bg}; padding:14px; border-radius:12px; border-left:4px solid {border}; text-align:center; margin:2px;">
                        <div style="font-size:1.2rem; font-weight:800; color:#1E293B;">{icon} {pic}</div>
                        <div style="font-size:0.85rem; color:#64748B; margin:6px 0;">
                            📋 {total} | ✅ {done} | 🔴 {delayed}
                        </div>
                        <div style="font-size:1.1rem; font-weight:700; color:{border};">{completion_rate:.0f}%</div>
                        <div style="font-size:0.7rem; color:#94A3B8;">Completion Rate</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background:#F8FAFC; padding:14px; border-radius:12px; text-align:center; border:1px solid #E2E8F0;">
                        <div style="font-size:1rem; color:#94A3B8;">⚪ {pic}</div>
                        <div style="font-size:0.8rem; color:#CBD5E1;">No tasks</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # ===== CHARTS SECTION =====
    st.markdown('<h2 style="color: #0F172A; font-size: 1.1rem; margin-bottom: 16px;">📊 PROJECT ANALYSIS</h2>', unsafe_allow_html=True)
    
    col_d1, col_d2, col_d3 = st.columns([1, 1, 1.2])
    
    # Status Distribution
    with col_d1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        if 'status' in df.columns and not df.empty:
            status_counts = df['status'].dropna().value_counts()
            status_colors = {
                'DONE': '#059669', 'ON_TRACK': '#059669',
                'ONGOING': '#D97706',
                'PENDING': '#7C3AED',
                'DELAYED': '#DC2626', 'CRITICAL': '#7F1D1D'
            }
            fig1 = create_donut_chart(status_counts, "Project Status Distribution", status_colors)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.markdown("<p style='text-align:center; color:#94A3B8;'>📭 Data status unavailable</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Category Distribution
    with col_d2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        if 'site_category' in df.columns and not df.empty:
            cat_series = df['site_category'].dropna().value_counts()
            cat_colors = {
                'New Site': '#0369A1', 'Collocation': '#7C3AED',
                'Upgrade': '#D97706', 'Relocation': '#DC2626',
                'Indoor': '#EC4899'
            }
            fig2 = create_donut_chart(cat_series, "Sites by Category", cat_colors)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.markdown("<p style='text-align:center; color:#94A3B8;'>ℹ️ Category data unavailable</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Status by Group
    with col_d3:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        if 'vendor' in df.columns:
            group_col, chart_title = 'vendor', "Status by Vendor"
        elif 'site_category' in df.columns:
            group_col, chart_title = 'site_category', "Status by Category"
        else:
            group_col, chart_title = 'status', "Project Status"
        
        clean_df = df.dropna(subset=[group_col])
        if not clean_df.empty and 'status' in clean_df.columns:
            pivot = clean_df.groupby(group_col)['status'].value_counts().unstack(fill_value=0)
            stack_order = ['CRITICAL', 'DELAYED', 'ONGOING', 'PENDING', 'DONE']
            available = [s for s in stack_order if s in pivot.columns]
            if not available:
                available = pivot.columns.tolist()[:5]
            colors = ['#DC2626', '#EF4444', '#D97706', '#7C3AED', '#059669']
            
            # 1. Generate dasar chart
            fig3 = create_stacked_bar(pivot, group_col, available, colors[:len(available)], chart_title)
            
            # 2. ✨ OPTIMASI UKURAN LEGENDA: Diperkecil 50% & Didorong ke Bawah
            fig3.update_layout(
                title={
                    'text': f"<b>{chart_title}</b>",
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'size': 15, 'color': '#0F172A'}
                },
                legend={
                    'orientation': "h",        # Horizontal layout
                    'yanchor': "top",          # Jangkar di atas kotak legenda
                    'y': -0.22,                # Didorong lebih bawah lagi (-0.22) agar menjauh dari nama vendor
                    'xanchor': "center",
                    'x': 0.5,
                    'font': {'size': 9},       # 🌟 DIPERKECIL: Ukuran teks legenda menjadi 9px (Sangat minimalis)
                    'itemwidth': 30,           # 🌟 DIPERKECIL: Lebar maksimum area item ikon warna
                    'itemsizing': 'constant',  # Memastikan ukuran simbol konisten kecil
                    'traceorder': 'normal'
                },
                margin={
                    't': 40,
                    'b': 110,                  # 🌟 RUANG TAMBAHAN: Jarak bawah dinaikkan ke 110px agar aman
                    'l': 50,
                    'r': 50
                },
                hovermode="x unified",
                barmode="stack"
            )
            
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.markdown("<p style='text-align:center; color:#94A3B8;'>📭 No data available</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # ===== MILESTONES & METRICS =====
    st.markdown('<h2 style="color: #0F172A; font-size: 1.1rem; margin-bottom: 16px;">🎯 MILESTONES & METRICS</h2>', unsafe_allow_html=True)
    
    col_m1, col_m2, col_m3 = st.columns([1.5, 1, 1])
    
    # Milestone Progress
    with col_m1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.markdown('<h3>📍 Overall Milestone Progress</h3>', unsafe_allow_html=True)
        if not milestones_df.empty:
            milestone_steps = ['Survey', 'Design', 'Permit', 'Construction', 'Installation', 'Integration', 'RFS']
            ms_counts = milestones_df['name'].value_counts()
            
            for step in milestone_steps[:5]:
                if step in ms_counts.index:
                    total = ms_counts[step]
                    completed = len(milestones_df[(milestones_df['name'] == step) & (milestones_df['status'] == 'DONE')])
                    pct = (completed / total * 100) if total > 0 else 0
                    color = '#059669' if pct >= 80 else ('#D97706' if pct >= 40 else '#DC2626')
                    
                    st.markdown(f"""
                    <div class="metric-item">
                        <div class="metric-label">{step}</div>
                        <div class="metric-value">{pct:.0f}%</div>
                    </div>
                    <div class="metric-bar">
                        <div class="metric-bar-fill" style="width: {pct}%; background: {color};"></div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("📊 Milestone data unavailable")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Issue Summary
    with col_m2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.markdown('<h3>⚠️ Issue Summary</h3>', unsafe_allow_html=True)
        fig_issues = go.Figure(data=[
            go.Bar(x=['🔴 High', '🟠 Medium', '🟡 Low'],
                   y=[6, 11, 6],
                   marker_color=['#DC2626', '#D97706', '#059669'],
                   text=[6, 11, 6],
                   textposition='auto',
                   hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>')
        ])
        fig_issues.update_layout(
            showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=150,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#475569'),
            xaxis=dict(showgrid=False, linecolor='#E2E8F0'),
            yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
        )
        st.plotly_chart(fig_issues, use_container_width=True)
        st.markdown('<div style="text-align:center; font-size:1.8rem; font-weight:bold; color:#0369A1;">23</div><div style="text-align:center; color:#94A3B8; font-size:0.85rem;">Total Issues</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Risk Assessment
    with col_m3:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.markdown('<h3>📋 Risk Matrix</h3>', unsafe_allow_html=True)
        risk_matrix = np.array([
            [0, 1, 2, 3],
            [1, 2, 3, 4],
            [2, 3, 4, 5],
            [3, 4, 5, 6]
        ])
        fig_risk = px.imshow(risk_matrix, text_auto=True, aspect="auto",
                             color_continuous_scale="RdYlGn_r", zmin=0, zmax=10,
                             labels=dict(x="Impact", y="Probability"))
        fig_risk.update_layout(
            margin=dict(l=0, r=0, t=10, b=0), height=150,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#475569'),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_risk, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # ===== DETAILED TABLES =====
    st.markdown('<h2 style="color: #0F172A; font-size: 1.1rem; margin-bottom: 16px;">📋 SITE DETAILS</h2>', unsafe_allow_html=True)
    
    col_t1, col_t2 = st.columns([1.5, 1])
    
    # Delayed Sites Table
    with col_t1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.markdown('<h3>🔴 Top Delayed Sites</h3>', unsafe_allow_html=True)
        delay_df = df[df['status'].isin(['DELAYED', 'CRITICAL'])].copy()
        if not delay_df.empty and 'end_date' in delay_df.columns:
            delay_df['end_date'] = pd.to_datetime(delay_df['end_date'], errors='coerce')
            delay_df['delay_days'] = (datetime.now() - delay_df['end_date']).dt.days
            delay_df = delay_df.sort_values('delay_days', ascending=False).head(5)
            
            display_cols = ['site_id', 'site_name', 'status', 'delay_days']
            if 'site_category' in delay_df.columns:
                display_cols.insert(2, 'site_category')
            
            display_df = delay_df[display_cols].rename(columns={
                'site_id': 'Site ID',
                'site_name': 'Site Name',
                'site_category': 'Category',
                'status': 'Status',
                'delay_days': 'Delay (Days)'
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("✅ No delayed sites")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Progress Trend
    with col_t2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.markdown('<h3>📈 Progress Trend</h3>', unsafe_allow_html=True)
        if not milestones_df.empty and 'actual_end' in milestones_df.columns:
            trend = milestones_df.dropna(subset=['actual_end']).sort_values('actual_end').tail(20)
            if not trend.empty:
                if 'weight' in trend.columns:
                    trend['weight'] = pd.to_numeric(trend['weight'], errors='coerce').fillna(1)
                    total_weight = trend['weight'].sum()
                    trend['cum_progress'] = (trend['weight'].cumsum() / total_weight * 100) if total_weight > 0 else np.linspace(0, 100, len(trend))
                else:
                    trend['cum_progress'] = np.linspace(20, 100, len(trend))
                
                fig_trend = create_progress_chart(trend, 'actual_end', 'cum_progress', "Project S-Curve")
                st.plotly_chart(fig_trend, use_container_width=True)
        else:
            trend_data = pd.DataFrame({
                'date': pd.date_range(start=datetime.now()-timedelta(days=60), periods=10),
                'progress': np.linspace(20, 85, 10)
            })
            fig_trend = create_progress_chart(trend_data, 'date', 'progress', "Progress Trend (Sample)")
            st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align: center; color: #94A3B8; font-size: 0.85rem; padding: 16px 0;'>
        Last updated: {datetime.now().strftime('%d %b %Y | %H:%M')} | 
        <strong style='color: #0369A1;'>MCP Tower Project Management</strong>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    dashboard_page()
