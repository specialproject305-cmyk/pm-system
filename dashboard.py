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
        
        /* HEADER */
        .dashboard-header { background: linear-gradient(135deg, #0369A1 0%, #0284C7 100%); padding: 15px 25px; border-radius: 12px; margin-bottom: 15px; text-align: center; }
        .dashboard-header h1 { font-size: 1.5rem; margin: 0; color: #FFF; font-weight: 800; }
        .dashboard-header p { font-size: 0.8rem; margin: 5px 0 0 0; color: #E0F2FE; }
        
        /* SECTION TITLES */
        .section-header {
            font-size: 15px;
            font-weight: 800;
            color: #0F172A;
            text-align: center;
            margin: 25px 0 20px 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* KPI CARDS */
        .kpi-card { background: #FFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 8px; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
        .kpi-icon { font-size: 1.4rem; margin-bottom: 5px; }
        .kpi-title { font-size: 0.65rem; color: #64748B; text-transform: uppercase; font-weight: 700; margin-bottom: 5px; }
        .kpi-value { font-size: 1.5rem; font-weight: 800; color: #0369A1; line-height: 1.1; }
        .kpi-subtitle { font-size: 0.65rem; color: #94A3B8; margin-top: 5px; }
        
        /* CHART BOX */
        .chart-box { background: #FFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
        .chart-box h3 { 
            font-size: 15px !important; 
            text-align: center !important; 
            color: #0F172A !important; 
            font-weight: 700 !important;
            margin-bottom: 15px !important;
            border-bottom: none !important;
        }
        
        /* SECTION DIVIDER */
        .section-divider { height: 1px; background: #E2E8F0; margin: 15px 0; }
        
        /* PROGRESS BAR CUSTOM */
        .metric-item { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
        .metric-label { font-size: 0.8rem; font-weight: 600; }
        .metric-value { font-size: 0.8rem; font-weight: 700; color: #0369A1; }
        .metric-bar-bg { background: #E2E8F0; border-radius: 10px; height: 8px; width: 100%; margin-bottom: 12px; overflow: hidden; }
        .metric-bar-fill { height: 100%; border-radius: 10px; transition: width 0.5s ease; }
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 📊 HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_safe_numeric(series):
    return pd.to_numeric(series, errors='coerce').fillna(0)

def render_kpi_card(icon, title, value, subtitle, color_class=""):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value {color_class}">{value}</div>
        <div class="kpi-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def create_donut_chart(series, title, color_map):
    if series.empty:
        fig = go.Figure()
        fig.update_layout(title=dict(text=f"<b>{title}</b>", x=0.5, font=dict(size=15, color='#0F172A')))
        return fig
    
    labels = series.index.astype(str).tolist()
    values = series.values.tolist()
    colors = [color_map.get(label, '#94A3B8') for label in labels]
    
    fig = px.pie(values=values, names=labels, hole=0.65, color_discrete_sequence=colors)
    fig.update_traces(textinfo='percent', marker=dict(line=dict(color='#FFFFFF', width=2)))
    
    fig.update_layout(
        showlegend=True,
        margin=dict(l=10, r=10, t=50, b=10),
        height=250,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=10),
        title=dict(text=f"<b>{title}</b>", x=0.5, y=0.95, font=dict(color='#0F172A', size=15)),
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5)
    )
    return fig

def create_stacked_bar(df, group_col, categories, colors, title=""):
    fig = go.Figure()
    if df.empty: return fig
    
    for i, cat in enumerate(categories):
        if cat in df.columns:
            fig.add_trace(go.Bar(
                x=df.index.astype(str), y=df[cat], name=cat, 
                marker_color=colors[i] if i < len(colors) else '#94A3B8'
            ))
    
    fig.update_layout(
        barmode='stack',
        height=300,
        margin=dict(l=20, r=20, t=60, b=80),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title=dict(text=f"<b>{title}</b>", x=0.5, y=0.95, font=dict(color='#0F172A', size=15)),
        legend=dict(
            orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5,
            font=dict(size=9), itemwidth=30, itemsizing='constant'
        ),
        xaxis=dict(tickfont=dict(size=10)),
        yaxis=dict(gridcolor='#F1F5F9')
    )
    return fig

def create_progress_chart(df, date_col, value_col, title):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[date_col], y=df[value_col], mode='lines+markers',
        line=dict(color='#0369A1', width=3),
        fill='tozeroy', fillcolor='rgba(3, 105, 161, 0.1)',
        marker=dict(size=6, color='#0284C7')
    ))
    fig.update_layout(
        height=250, margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        title=dict(text=f"<b>{title}</b>", x=0.5, font=dict(color='#0F172A', size=15)),
        xaxis=dict(tickfont=dict(size=9), gridcolor='#F1F5F9'),
        yaxis=dict(tickfont=dict(size=9), gridcolor='#F1F5F9')
    )
    return fig

# ─────────────────────────────────────────────────────────────
# 📱 MAIN DASHBOARD
# ─────────────────────────────────────────────────────────────

def dashboard_page():
    inject_professional_css()
    
    # Load data
    all_data = read_all_sheets()
    df = all_data.get('projects', pd.DataFrame())
    milestones_df = all_data.get('milestones', pd.DataFrame())
    
    if df.empty:
        st.info("📋 No site data available.")
        return
    
    # Filter global
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid_sites = df[df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
        df = df[df['id'].isin(valid_sites)]
        milestones_df = milestones_df[milestones_df['project_id'].isin(valid_sites)] if not milestones_df.empty else milestones_df

    df['progress'] = get_safe_numeric(df['progress'])
    
    # ===== HEADER =====
    st.markdown("""
    <div class="dashboard-header">
        <h1>📊 PROJECT MANAGEMENT DASHBOARD</h1>
        <p>Real-time project status, milestones & performance metrics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filter PM
    c_f1, c_f2, c_f3 = st.columns([1, 1, 1])
    with c_f2:
        pm_list = ['ALL PM'] + sorted(df['pm'].dropna().unique().tolist()) if 'pm' in df.columns else ['ALL']
        selected_pm = st.selectbox("👤 Filter by Project Manager:", pm_list, key="dash_pm_filter", label_visibility="collapsed")
        if selected_pm != 'ALL PM':
            df = df[df['pm'] == selected_pm]

    # ===== KPI SECTION =====
    st.markdown('<div class="section-header">📈 Key Performance Indicators</div>', unsafe_allow_html=True)
    
    total_sites = len(df)
    rfs_count = len(df[df['status']=='DONE'])
    on_prog = len(df[df['status']=='ONGOING'])
    delay_count = len(df[df['status'].isin(['DELAYED','CRITICAL'])])
    avg_prog = df['progress'].mean()
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1: render_kpi_card("📡", "Total Sites", total_sites, "Active projects")
    with col2: render_kpi_card("✅", "RFS Done", rfs_count, f"{rfs_count/total_sites*100:.0f}% Rate" if total_sites > 0 else "0%")
    with col3: render_kpi_card("🏗️", "Ongoing", on_prog, "Under construction")
    with col4: render_kpi_card("🔴", "Critical", delay_count, "Needs attention")
    with col5: render_kpi_card("📊", "Avg Progress", f"{avg_prog:.1f}%", "Overall completion")
    with col6: render_kpi_card("🏆", "Health", f"{round((rfs_count+on_prog)/total_sites*100) if total_sites>0 else 0}%", "Project score")

    # ===== PIC SNAPSHOT =====
    st.markdown('<div class="section-header">👷 PIC Performance Snapshot</div>', unsafe_allow_html=True)
    if not milestones_df.empty and 'assigned_to' in milestones_df.columns:
        pic_list = ['Sitac', 'Legal', 'Engineering', 'Procurement', 'Project', 'Vendor Management']
        cols_pic = st.columns(len(pic_list))
        for i, pic in enumerate(pic_list):
            pic_tasks = milestones_df[milestones_df['assigned_to'] == pic]
            total = len(pic_tasks)
            with cols_pic[i]:
                if total > 0:
                    done = len(pic_tasks[pic_tasks['status'] == 'DONE'])
                    rate = (done / total) * 100
                    color = "#059669" if rate >= 80 else ("#D97706" if rate >= 50 else "#DC2626")
                    st.markdown(f"""
                    <div style="background:#FFF; padding:10px; border-radius:10px; border-top:4px solid {color}; text-align:center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="font-size:0.7rem; font-weight:700; color:#64748B;">{pic}</div>
                        <div style="font-size:1.1rem; font-weight:800; color:{color};">{rate:.0f}%</div>
                        <div style="font-size:0.6rem; color:#94A3B8;">{done}/{total} Done</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ===== CHARTS SECTION =====
    st.markdown('<div class="section-header">📊 Project Analysis & Distribution</div>', unsafe_allow_html=True)
    col_d1, col_d2, col_d3 = st.columns([1, 1, 1.2])
    
    with col_d1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        status_counts = df['status'].value_counts()
        st.plotly_chart(create_donut_chart(status_counts, "Status Distribution", {'DONE':'#059669', 'ONGOING':'#D97706', 'DELAYED':'#DC2626'}), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_d2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        cat_counts = df['site_category'].value_counts()
        st.plotly_chart(create_donut_chart(cat_counts, "Sites by Category", {'New Site':'#0369A1', 'Upgrade':'#7C3AED'}), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_d3:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        group_col = 'vendor' if 'vendor' in df.columns else 'status'
        pivot = df.groupby(group_col)['status'].value_counts().unstack(fill_value=0)
        st.plotly_chart(create_stacked_bar(pivot, group_col, pivot.columns, ['#DC2626','#D97706','#059669','#7C3AED'], "Status by Vendor"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ===== MILESTONES & METRICS =====
    st.markdown('<div class="section-header">🎯 Milestones & Issues Control</div>', unsafe_allow_html=True)
    col_m1, col_m2, col_m3 = st.columns([1.5, 1, 1])
    
    with col_m1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.markdown('<h3>Overall Milestone Progress</h3>', unsafe_allow_html=True)
        steps = ['Survey', 'Design', 'Permit', 'Construction', 'Installation']
        if not milestones_df.empty:
            ms_counts = milestones_df['name'].value_counts()
            for step in steps:
                if step in ms_counts.index:
                    comp = len(milestones_df[(milestones_df['name']==step) & (milestones_df['status']=='DONE')])
                    pct = (comp/ms_counts[step]*100) if ms_counts[step]>0 else 0
                    clr = '#059669' if pct>=80 else '#D97706'
                    st.markdown(f'<div class="metric-item"><span class="metric-label">{step}</span><span class="metric-value">{pct:.0f}%</span></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-bar-bg"><div class="metric-bar-fill" style="width:{pct}%; background:{clr};"></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_m2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        fig_iss = go.Figure(go.Bar(x=['High', 'Med', 'Low'], y=[6, 12, 5], marker_color=['#DC2626','#D97706','#059669']))
        fig_iss.update_layout(height=180, margin=dict(t=40, b=10), title=dict(text="<b>Issue Summary</b>", x=0.5, font=dict(size=15)))
        st.plotly_chart(fig_iss, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_m3:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        fig_risk = px.imshow([[1,2,5],[2,5,8],[5,8,9]], text_auto=True, color_continuous_scale="RdYlGn_r")
        fig_risk.update_layout(height=180, margin=dict(t=40, b=10), coloraxis_showscale=False, title=dict(text="<b>Risk Matrix</b>", x=0.5, font=dict(size=15)))
        st.plotly_chart(fig_risk, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ===== FOOTER =====
    st.markdown(f"""
    <div style='text-align: center; color: #94A3B8; font-size: 0.8rem; margin-top: 30px; padding: 20px; border-top: 1px solid #E2E8F0;'>
        MCP Tower PM Dashboard • {datetime.now().strftime('%d %b %Y | %H:%M')}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    dashboard_page()
