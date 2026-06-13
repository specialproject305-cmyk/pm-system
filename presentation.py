import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import inspect
from supabase_db import read_all_sheets

# ─────────────────────────────────────────────────────────────
# 🎨 PRESENTATION MODE CSS
# ─────────────────────────────────────────────────────────────
def inject_presentation_css():
    st.markdown("""
    <style>
        .stApp {
            margin-left: 0 !important;
            background: linear-gradient(180deg, #E0F2FE 0%, #BAE6FD 50%, #7DD3FC 100%) !important;
            margin: 0;
            padding: 15px;
            min-height: 100vh;
        }
        
        section.main > div {
            padding: 0 !important;
        }
        
        .slide-title {
            font-size: 2.5rem;
            font-weight: 900;
            text-align: center;
            color: #0369A1;
            margin: 20px 0 10px 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .slide-subtitle {
            font-size: 1.1rem;
            text-align: center;
            color: #0284C7;
            margin-bottom: 30px;
            font-weight: 500;
        }
        
        .kpi-big {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F9FF 100%);
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15);
            border: 2px solid #DBEAFE;
            transition: all 0.3s ease;
        }
        
        .kpi-big:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 32px rgba(59, 130, 246, 0.2);
        }
        
        .kpi-big .value {
            font-size: 3rem;
            font-weight: 900;
            color: #0284C7;
            line-height: 1;
        }
        
        .kpi-big .label {
            font-size: 0.95rem;
            color: #64748B;
            margin-top: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .alert-red {
            background: linear-gradient(135deg, #FEE2E2 0%, #FEF2F2 100%);
            border-left: 4px solid #DC2626;
            padding: 12px;
            margin: 8px 0;
            border-radius: 8px;
            color: #7F1D1D;
        }
        
        .alert-yellow {
            background: linear-gradient(135deg, #FEF3C7 0%, #FFFBEB 100%);
            border-left: 4px solid #FF8C00;
            padding: 12px;
            margin: 8px 0;
            border-radius: 8px;
            color: #D97706;
        }
        
        .alert-green {
            background: linear-gradient(135deg, #DCFCE7 0%, #F0FDF4 100%);
            border-left: 4px solid #10B981;
            padding: 12px;
            margin: 8px 0;
            border-radius: 8px;
            color: #047857;
        }
        
        .footer {
            text-align: center;
            color: #0284C7;
            margin-top: 30px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        .stRadio > div {
            justify-content: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .stRadio label {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F9FF 100%);
            padding: 8px 16px;
            border-radius: 20px;
            color: #0369A1 !important;
            font-weight: 600;
            font-size: 0.9rem;
            border: 2px solid #DBEAFE;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
            transition: all 0.2s ease;
        }
        
        .stRadio label:hover {
            background: linear-gradient(135deg, #38BDF8 0%, #0EA5E9 100%);
            color: white !important;
            transform: translateY(-2px);
        }
        
        div[data-testid="stMetricValue"] {
            color: #0284C7;
            font-weight: 900;
        }
    </style>
    """, unsafe_allow_html=True)

def presentation_page():
    inject_presentation_css()
    
    try:
        with st.spinner("📊 Loading presentation..."):
            all_data = read_all_sheets()
        sites_df = all_data.get('projects', pd.DataFrame())
        ms_df = all_data.get('milestones', pd.DataFrame())
        mat_df = all_data.get('materials', pd.DataFrame())
        master_df = all_data.get('master_projects', pd.DataFrame())
    except Exception as e:
        st.error(f"⚠️ Error loading data: {e}")
        return

    # ===== GLOBAL FILTER =====
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid_sites = sites_df[sites_df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
        sites_df = sites_df[sites_df['id'].isin(valid_sites)]
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)] if not ms_df.empty else ms_df
    
    if sites_df.empty:
        st.warning("📋 No data available.")
        return
    
    # 🛠️ SINKRONISASI TIPE DATA (FIX SAFETY)
    if 'progress' in sites_df.columns:
        sites_df['progress'] = pd.to_numeric(sites_df['progress'], errors='coerce').fillna(0)
    if not ms_df.empty:
        ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
        ms_df['actual_end'] = pd.to_datetime(ms_df['actual_end'], errors='coerce')
    if not mat_df.empty:
        for c in ['current_stock','min_stock']:
            if c in mat_df.columns:
                mat_df[c] = pd.to_numeric(mat_df[c], errors='coerce').fillna(0)
    
    # Calculate KPIs
    total = len(sites_df)
    avg_prog = sites_df['progress'].mean() if 'progress' in sites_df.columns else 0
    on_track = len(sites_df[sites_df['status']=='DONE']) if 'status' in sites_df.columns else 0
    delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])]) if 'status' in sites_df.columns else 0
    health = round((on_track/total)*100) if total > 0 else 0
    
    # Ambil waktu sekarang berbasis Pandas Timestamp agar satu tipe data saat kalkulasi matematika
    now_timestamp = pd.Timestamp.now()
    forecast = now_timestamp + timedelta(days=int((100-avg_prog)*3))
    
    # ===== SLIDE NAVIGATION =====
    st.markdown("<div style='text-align: center; margin-bottom: 15px;'>", unsafe_allow_html=True)
    slide = st.radio("", [
        "🎬 Cover Slide",
        "📊 Executive Summary",
        "📈 Progress Overview",
        "🗺️ Site Status",
        "⚠️ Critical Alerts",
        "🤖 AI Insights",
        "📋 Action Items"
    ], horizontal=True, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ===== SLIDE 1: COVER =====
    if "Cover" in slide:
        # Gunakan inspect.cleandoc agar string HTML bersih total dari spasi liar penulisan Python
        cover_html = inspect.cleandoc(f"""
        <div style="text-align:center; padding:60px 20px; min-height:75vh; display:flex; flex-direction:column; justify-content:center; align-items:center;">
            <div style="font-size:5rem; margin-bottom:30px;">🏗️</div>
            <h1 style="font-size:4rem; color:#0369A1; margin:0; font-weight:900; line-height:1.2;">PROJECT DASHBOARD</h1>
            <p style="font-size:1.5rem; color:#0284C7; margin:20px 0 40px 0; font-weight:500;">Deployment & Progress Report</p>
            <div style="background:white; display:inline-block; padding:20px 40px; border-radius:14px; box-shadow:0 8px 24px rgba(59, 130, 246, 0.2); border:2px solid #DBEAFE;">
                <p style="font-size:1.1rem; color:#64748B; margin:0; font-weight:600;">📅 {now_timestamp.strftime('%d %B %Y')}</p>
                <p style="font-size:0.9rem; color:#94A3B8; margin:8px 0 0 0;">Real-time Status Report • PM System v3.0</p>
            </div>
        </div>
        <div class="footer">Confidential • Internal Use Only</div>
        """)
        st.markdown(cover_html, unsafe_allow_html=True)
    
    # ===== SLIDE 2: EXECUTIVE SUMMARY =====
    elif "Summary" in slide:
        st.markdown('<div class="slide-title">📊 Executive Summary</div>', unsafe_allow_html=True)
        st.markdown('<div class="slide-subtitle">Key Performance Indicators & Project Health</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="kpi-big"><div class="value">{total}</div><div class="label">Total Sites</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="kpi-big"><div class="value">{avg_prog:.1f}%</div><div class="label">Avg Progress</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="kpi-big"><div class="value">{on_track}</div><div class="label">On Track</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="kpi-big"><div class="value">{delayed}</div><div class="label">At Risk</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gauge chart
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health,
            title={'text': "🏆 Project Health Score", 'font': {'size': 24, 'color': '#0369A1'}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#0284C7", 'thickness': 0.15},
                'steps': [
                    {'range': [0, 33], 'color': "rgba(220, 38, 38, 0.1)"},
                    {'range': [33, 66], 'color': "rgba(255, 140, 0, 0.1)"},
                    {'range': [66, 100], 'color': "rgba(16, 185, 129, 0.1)"}
                ]
            }
        ))
        fig_g.update_layout(height=300, margin=dict(t=30,b=30), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#0369A1'))
        st.plotly_chart(fig_g, use_container_width=True)
        
        st.markdown(f'<div class="footer">Forecast Completion: {forecast.strftime("%d %B %Y")} • {health}% Health</div>', unsafe_allow_html=True)
    
    # ===== SLIDE 3: PROGRESS OVERVIEW =====
    elif "Progress" in slide:
        st.markdown('<div class="slide-title">📈 Progress Overview</div>', unsafe_allow_html=True)
        st.markdown('<div class="slide-subtitle">Milestone Completion & Trend Analysis</div>', unsafe_allow_html=True)
        
        col_a, col_b = st.columns([1.2, 1])
        
        with col_a:
            if not sites_df.empty and 'site_name' in sites_df.columns:
                top12 = sites_df.nlargest(min(12, len(sites_df)), 'progress')
                fig1 = px.bar(
                    top12,
                    y='site_name',
                    x='progress',
                    orientation='h',
                    color='progress',
                    color_continuous_scale=['#FF8C00', '#3B82F6', '#0284C7', '#10B981'],
                    labels={'progress': 'Progress %', 'site_name': 'Site'},
                    title="Top 12 Sites by Progress"
                )
                fig1.update_layout(
                    height=380, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#1F2937', size=10), showlegend=False, xaxis_title="Progress %", yaxis_title=""
                )
                st.plotly_chart(fig1, use_container_width=True)
        
        with col_b:
            if 'status' in sites_df.columns:
                status_counts = sites_df['status'].value_counts()
                fig2 = px.pie(
                    values=status_counts.values, names=status_counts.index, title="Site Status Distribution",
                    color_discrete_map={'DONE': '#10B981', 'ON_TRACK': '#3B82F6', 'ONGOING': '#FF8C00', 'PENDING': '#94A3B8', 'DELAYED': '#DC2626', 'CRITICAL': '#991B1B'}
                )
                fig2.update_layout(height=380, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937', size=10), showlegend=True)
                st.plotly_chart(fig2, use_container_width=True)
        
        # S-Curve Fix (Gunakan penanganan copy eksplisit untuk menghindari SettingWithCopyWarning)
        if not ms_df.empty and 'planned_end' in ms_df.columns:
            st.markdown("<br>", unsafe_allow_html=True)
            ms_df_temp = ms_df.dropna(subset=['planned_end']).copy()
            if not ms_df_temp.empty:
                ms_df_temp['month'] = ms_df_temp['planned_end'].dt.to_period('M').astype(str)
                monthly = ms_df_temp.groupby('month').size().cumsum().reset_index(name='cumulative')
                fig3 = px.line(
                    monthly, x='month', y='cumulative', title="Cumulative Milestones (S-Curve)",
                    markers=True, labels={'month': 'Month', 'cumulative': 'Cumulative Tasks'}
                )
                fig3.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937'), showlegend=False)
                st.plotly_chart(fig3, use_container_width=True)
    
    # ===== SLIDE 4: SITE STATUS =====
    elif "Site" in slide:
        st.markdown('<div class="slide-title">🗺️ Site Status Matrix</div>', unsafe_allow_html=True)
        st.markdown('<div class="slide-subtitle">Detailed Site-by-Site Analysis</div>', unsafe_allow_html=True)
        
        display_cols = [col for col in ['site_id', 'site_name', 'status', 'progress', 'pm'] if col in sites_df.columns]
        display_df = sites_df[display_cols].head(15).copy()
        
        def color_row(row):
            status = row.get('status', '')
            if status == 'CRITICAL': return ['background-color: #FEE2E2; color: #7F1D1D;']*len(row)
            elif status == 'DELAYED': return ['background-color: #FEF3C7; color: #D97706;']*len(row)
            elif status == 'DONE': return ['background-color: #DCFCE7; color: #047857;']*len(row)
            elif status in ['ON_TRACK', 'ONGOING']: return ['background-color: #DBEAFE; color: #0369A1;']*len(row)
            return ['']*len(row)
        
        styled_df = display_df.style.apply(color_row, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("🟢 On Track", on_track)
        col_s2.metric("🟡 Delayed", len(sites_df[sites_df['status']=='DELAYED']) if 'status' in sites_df.columns else 0)
        col_s3.metric("🔴 Critical", len(sites_df[sites_df['status']=='CRITICAL']) if 'status' in sites_df.columns else 0)
    
    # ===== SLIDE 5: CRITICAL ALERTS =====
    elif "Alerts" in slide:
        st.markdown('<div class="slide-title">⚠️ Critical Alerts & Issues</div>', unsafe_allow_html=True)
        st.markdown('<div class="slide-subtitle">Immediate Action Required</div>', unsafe_allow_html=True)
        
        col_alerts1, col_alerts2 = st.columns(2)
        
        with col_alerts1:
            st.markdown("### 🔴 Delayed Milestones")
            if not ms_df.empty:
                delayed_ms = ms_df[ms_df['status'].isin(['DELAYED','CRITICAL'])].sort_values('planned_end')
                if not delayed_ms.empty:
                    for _, r in delayed_ms.head(6).iterrows():
                        # FIX SAFETY: Hitung hari terlambat menggunakan perbandingan sesama objek Pandas Timestamp
                        if pd.notna(r.get('planned_end')):
                            days_late = (now_timestamp - r['planned_end']).days
                            days_late = max(0, days_late)
                        else:
                            days_late = 0
                            
                        alert_html = inspect.cleandoc(f"""
                        <div class="alert-red">
                            <strong>{r['name'][:40]}</strong><br>
                            Status: {r['status']} | Days Late: {days_late} | Progress: {r.get('progress', 0):.0f}%
                        </div>
                        """)
                        st.markdown(alert_html, unsafe_allow_html=True)
                else:
                    st.success("✅ No delayed milestones")
        
        with col_alerts2:
            st.markdown("### 📦 Resource Issues")
            if not mat_df.empty and 'current_stock' in mat_df.columns and 'min_stock' in mat_df.columns:
                critical_mat = mat_df[mat_df['current_stock'] < mat_df['min_stock']]
                if not critical_mat.empty:
                    for _, r in critical_mat.head(6).iterrows():
                        mat_html = inspect.cleandoc(f"""
                        <div class="alert-yellow">
                            <strong>{r['name'][:40]}</strong><br>
                            Stock: {r['current_stock']:.0f} (Min: {r['min_stock']:.0f})
                        </div>
                        """)
                        st.markdown(mat_html, unsafe_allow_html=True)
                else:
                    st.markdown('<div class="alert-green">✅ All materials in stock</div>', unsafe_allow_html=True)
            
            if not ms_df.empty and 'status' in ms_df.columns:
                pending_count = len(ms_df[ms_df['status']=='PENDING'])
                if pending_count > 0:
                    pending_html = inspect.cleandoc(f"""
                    <div class="alert-yellow">
                        <strong>⏳ {pending_count} Pending Milestones</strong><br>
                        Awaiting approval or initiation
                    </div>
                    """)
                    st.markdown(pending_html, unsafe_allow_html=True)
    
    # ===== SLIDE 6: AI INSIGHTS =====
    elif "Insights" in slide:
        st.markdown('<div class="slide-title">🤖 AI-Powered Insights</div>', unsafe_allow_html=True)
        st.markdown('<div class="slide-subtitle">Predictive Analysis & Recommendations</div>', unsafe_allow_html=True)
        
        col_ai1, col_ai2 = st.columns(2)
        with col_ai1:
            st.markdown(f'<div class="kpi-big"><div class="value">{health}%</div><div class="label">Health Score</div></div>', unsafe_allow_html=True)
        with col_ai2:
            st.markdown(f'<div class="kpi-big"><div class="value">{forecast.strftime("%d %b")}</div><div class="label">Estimated Completion</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 💡 Strategic Recommendations")
        
        recommendations = []
        if health >= 80: recommendations.append("✅ **Excellent Execution** - Maintain current pace and continue momentum")
        elif health >= 60: recommendations.append("⚠️ **Moderate Performance** - Review and optimize key processes")
        else: recommendations.append("🔴 **Critical Intervention Needed** - Escalate and reallocate resources")
        
        if delayed > 0: recommendations.append(f"📅 **Address Delays** - Immediate action on {delayed} delayed sites required")
        
        recommendations.append("📊 **Timeline On Track** - Expected to meet macro project deadline" if avg_prog >= 40 else "⏰ **Timeline Reassessment** - Review potential bottleneck risks")
        
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"**{i}.** {rec}")
    
    # ===== SLIDE 7: ACTION ITEMS =====
    elif "Action" in slide:
        st.markdown('<div class="slide-title">📋 Action Items & Next Steps</div>', unsafe_allow_html=True)
        st.markdown('<div class="slide-subtitle">Prioritized Tasks for Project Success</div>', unsafe_allow_html=True)
        
        actions = [
            ("🔴 IMMEDIATE", "Resolve 5+ delayed sites", "This week"),
            ("🟠 HIGH", "Optimize resource allocation", "Next 2 weeks"),
            ("🟡 MEDIUM", "Complete pending approvals", "Next 3 weeks"),
            ("🟢 LOW", "Performance review meeting", "Next month"),
        ]
        
        for priority, action, timeline in actions:
            col_action1, col_action2 = st.columns([1, 1.5])
            with col_action1:
                st.markdown(f"<strong>{priority}</strong><br>{action}", unsafe_allow_html=True)
            with col_action2:
                st.markdown(f"<small>📅 {timeline}</small>", unsafe_allow_html=True)
            st.divider()
        
        st.markdown("""
        ### 📞 Contact & Support
        - **Project Manager**: projects@company.com
        - **Technical Lead**: tech@company.com
        """)
    
    st.markdown('<div class="footer">PM System v3.0 • AI-Powered Dashboard • © 2026</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    presentation_page()
