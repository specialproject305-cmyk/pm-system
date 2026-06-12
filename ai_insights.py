import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase_db import read_all_sheets
import numpy as np

# ─────────────────────────────────────────────────────────────
# 🎨 AI INSIGHTS CSS
# ─────────────────────────────────────────────────────────────
def inject_ai_css():
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #F8FBFF 0%, #F0F7FF 100%);
            color: #1F2937;
        }
        
        .ai-header {
            background: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%);
            padding: 30px;
            border-radius: 16px;
            color: white;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px rgba(59, 130, 246, 0.2);
        }
        
        .ai-section {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F9FF 100%);
            border-radius: 14px;
            padding: 20px;
            border: 2px solid #DBEAFE;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.1);
            transition: all 0.3s ease;
        }
        
        .ai-section:hover {
            border-color: #3B82F6;
            box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15);
        }
        
        .ai-section h3 {
            color: #1E40AF !important;
            margin-top: 0 !important;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .insight-box {
            background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
            border-left: 4px solid #3B82F6;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 12px;
            color: #1F2937;
        }
        
        .insight-box.success {
            background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
            border-left-color: #10B981;
            color: #047857;
        }
        
        .insight-box.warning {
            background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
            border-left-color: #FF8C00;
            color: #D97706;
        }
        
        .insight-box.danger {
            background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
            border-left-color: #DC2626;
            color: #991B1B;
        }
        
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
            margin-bottom: 15px;
        }
        
        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            border: 1px solid #DBEAFE;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .metric-card .value {
            font-size: 1.8rem;
            font-weight: 900;
            color: #1F2937;
            line-height: 1;
        }
        
        .metric-card .label {
            font-size: 0.75rem;
            color: #6B7280;
            text-transform: uppercase;
            font-weight: 600;
            margin-top: 8px;
            letter-spacing: 0.5px;
        }
        
        .alert-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-right: 5px;
        }
        
        .alert-danger { background: rgba(220, 38, 38, 0.15); color: #991B1B; }
        .alert-warning { background: rgba(255, 140, 0, 0.15); color: #D97706; }
        .alert-success { background: rgba(16, 185, 129, 0.15); color: #047857; }
    </style>
    """, unsafe_allow_html=True)

def get_safe_numeric(val):
    try:
        return float(val) if val else 0
    except:
        return 0

def ai_insights_page():
    inject_ai_css()
    
    # Header
    st.markdown("""
    <div class="ai-header">
        <h1 style="margin:0; color:white;">🤖 AI-Powered Analytics Center</h1>
        <p style="margin:8px 0 0 0; color:#E0E7FF; font-size:0.95rem;">Advanced insights, predictions & recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        with st.spinner("🔄 Loading data..."):
            all_data = read_all_sheets()
        sites_df = all_data.get('projects', pd.DataFrame())
        ms_df = all_data.get('milestones', pd.DataFrame())
        mat_df = all_data.get('materials', pd.DataFrame())
    except Exception as e:
        st.error(f"⚠️ Error loading data: {e}")
        return

    # Apply global filter
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid_sites = sites_df[sites_df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)] if not ms_df.empty else ms_df
        sites_df = sites_df[sites_df['id'].isin(valid_sites)]
    
    if sites_df.empty:
        st.warning("⚠️ No site data available.")
        return
    
    # Data preparation
    if not sites_df.empty and 'progress' in sites_df.columns:
        sites_df['progress'] = pd.to_numeric(sites_df['progress'], errors='coerce').fillna(0)
    if not ms_df.empty:
        for col in ['planned_start', 'planned_end', 'actual_start', 'actual_end']:
            if col in ms_df.columns:
                ms_df[col] = pd.to_datetime(ms_df[col], errors='coerce')
    
    # ===== SITE SELECTION =====
    col_filter1, col_filter2, col_filter3 = st.columns([2, 1, 1])
    
    with col_filter1:
        site_options = ["📊 ALL SITES"] + sites_df["id"].tolist()
        selected_site = st.selectbox(
            "🎯 Select Analysis Scope:",
            site_options,
            format_func=lambda x: "📊 ALL SITES" if x == "📊 ALL SITES"
            else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}"
        )
    
    with col_filter2:
        analysis_type = st.selectbox("📈 View Type", ["Quick Summary", "Deep Dive", "Comparison"])
    
    with col_filter3:
        st.write("")
        st.write("")
        if st.button("🔍 Generate Analysis", type="primary", use_container_width=True):
            st.session_state['run_analysis'] = True
        else:
            st.session_state['run_analysis'] = False
    
    if not st.session_state.get('run_analysis', True):
        # Show quick overview
        st.markdown('<div class="ai-section">', unsafe_allow_html=True)
        st.markdown('<h3>📊 Quick Overview</h3>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sites", len(sites_df))
        with col2:
            st.metric("Avg Progress", f"{sites_df['progress'].mean():.1f}%")
        with col3:
            st.metric("On Track", len(sites_df[sites_df['status']=='DONE']))
        with col4:
            st.metric("Delayed", len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])]))
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.info("💡 Click 'Generate Analysis' for detailed insights")
        return
    
    # ===== DETERMINE SCOPE =====
    is_all = (selected_site == "📊 ALL SITES")
    if not is_all:
        site_ms = ms_df[ms_df['project_id'] == selected_site] if not ms_df.empty else pd.DataFrame()
        selected_site_data = sites_df[sites_df['id']==selected_site].iloc[0]
        site_name = f"{selected_site_data['site_id']} - {selected_site_data['site_name']}"
    else:
        site_ms = ms_df
        site_name = "ALL SITES"
    
    st.markdown(f"### 📍 Analyzing: {site_name}")
    st.markdown("---")
    
    # ========== SECTION 1: PROGRESS & PERFORMANCE ANALYSIS ==========
    st.markdown('<div class="ai-section"><h3>📈 1. Progress & Performance Analysis</h3>', unsafe_allow_html=True)
    
    col_prog1, col_prog2, col_prog3 = st.columns(3)
    
    with col_prog1:
        if not site_ms.empty:
            done = len(site_ms[site_ms['status']=='DONE'])
            total = len(site_ms)
            progress = round((done/total)*100, 1) if total > 0 else 0
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=progress,
                delta={'reference': 80},
                title={'text': "Overall Progress"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#10B981" if progress > 70 else "#FF8C00" if progress > 40 else "#DC2626"},
                    'steps': [
                        {'range': [0, 30], 'color': "rgba(220, 38, 38, 0.1)"},
                        {'range': [30, 70], 'color': "rgba(255, 140, 0, 0.1)"},
                        {'range': [70, 100], 'color': "rgba(16, 185, 129, 0.1)"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_gauge.update_layout(height=300, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_gauge, use_container_width=True)
    
    with col_prog2:
        col_metric1, col_metric2 = st.columns(2)
        with col_metric1:
            st.metric("📋 Total Tasks", total)
            st.metric("✅ Completed", done)
        with col_metric2:
            st.metric("⚙️ In Progress", len(site_ms[site_ms['status']=='ONGOING']))
            st.metric("⏳ Pending", len(site_ms[site_ms['status']=='PENDING']))
    
    with col_prog3:
        delayed_count = len(site_ms[site_ms['status']=='DELAYED'])
        critical_count = len(site_ms[site_ms['status']=='CRITICAL'])
        
        st.metric("🔴 Delayed", delayed_count, delta=f"{critical_count} critical")
        
        if delayed_count > 0:
            critical = site_ms[site_ms['status']=='DELAYED']
            for idx, (_, c) in enumerate(critical.head(3).iterrows()):
                if idx == 0:
                    st.markdown(f"<div class='alert-badge alert-danger'>⚠️ CRITICAL</div>", unsafe_allow_html=True)
                st.caption(f"• {c['name'][:30]}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ========== SECTION 2: MILESTONE TREND & FORECAST ==========
    st.markdown('<div class="ai-section"><h3>📊 2. Milestone Trend & Completion Forecast</h3>', unsafe_allow_html=True)
    
    col_trend1, col_trend2 = st.columns([1.5, 1])
    
    with col_trend1:
        if not site_ms.empty:
            # Trend analysis
            site_ms_sorted = site_ms.sort_values('progress')
            fig_trend = px.bar(
                site_ms_sorted.head(15),
                x='name',
                y='progress',
                color='status',
                color_discrete_map={
                    'DONE': '#10B981',
                    'ONGOING': '#FF8C00',
                    'PENDING': '#9CA3AF',
                    'DELAYED': '#DC2626'
                },
                labels={'progress': 'Progress %', 'name': 'Milestone'}
            )
            fig_trend.update_layout(
                height=320,
                margin=dict(t=0, b=0, l=0, r=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#1F2937'),
                xaxis_title="",
                yaxis_title="Progress %",
                showlegend=True,
                hovermode='x unified'
            )
            st.plotly_chart(fig_trend, use_container_width=True)
    
    with col_trend2:
        if not site_ms.empty and 'planned_end' in site_ms.columns:
            # Forecast calculation
            avg_progress = site_ms['progress'].mean()
            days_per_5pct = 0.5  # Estimated days per 5% progress
            remaining_progress = 100 - avg_progress
            est_days = (remaining_progress / 5) * days_per_5pct
            
            est_completion = datetime.now() + timedelta(days=int(est_days))
            
            st.markdown(f"""
            <div class="insight-box success">
                <strong>⏰ Estimated Completion</strong><br>
                {est_completion.strftime('%d %b %Y')}<br>
                <small>Based on current progress trend</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Velocity analysis
            velocity = avg_progress / max(1, (datetime.now() - datetime(2024, 1, 1)).days)
            st.markdown(f"""
            <div class="insight-box">
                <strong>📈 Progress Velocity</strong><br>
                {velocity:.2f}% per day<br>
                <small>Historical average</small>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ========== SECTION 3: PIC PERFORMANCE ==========
    st.markdown('<div class="ai-section"><h3>👤 3. PIC Performance & SLA Metrics</h3>', unsafe_allow_html=True)
    
    if not site_ms.empty and 'assigned_to' in site_ms.columns:
        assigned = site_ms[site_ms['assigned_to'].notna() & (site_ms['assigned_to'] != '')]
        if not assigned.empty:
            pic_stats = assigned.groupby('assigned_to').agg(
                total=('id','count'),
                done=('status', lambda x: (x=='DONE').sum()),
                delayed=('status', lambda x: (x=='DELAYED').sum()),
                progress=('progress', lambda x: x.astype(float).mean())
            ).reset_index()
            pic_stats['completion_rate'] = round((pic_stats['done']/pic_stats['total'])*100, 1)
            pic_stats['sla_score'] = round(((pic_stats['done'] + pic_stats['total']*0.5) / pic_stats['total'] * 100), 1)
            pic_stats = pic_stats.sort_values('completion_rate', ascending=False)
            
            col_pic1, col_pic2 = st.columns([1.5, 1])
            
            with col_pic1:
                fig_pic = px.bar(
                    pic_stats,
                    x='assigned_to',
                    y='completion_rate',
                    color='completion_rate',
                    color_continuous_scale=['#DC2626', '#FF8C00', '#3B82F6', '#10B981'],
                    labels={'completion_rate': 'Completion Rate %', 'assigned_to': 'Team Member'}
                )
                fig_pic.update_layout(
                    height=300,
                    margin=dict(t=0, b=0, l=0, r=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#1F2937'),
                    showlegend=False,
                    xaxis_title="",
                    yaxis_title="Completion Rate %"
                )
                st.plotly_chart(fig_pic, use_container_width=True)
            
            with col_pic2:
                # Top performer
                top_performer = pic_stats.iloc[0]
                st.markdown(f"""
                <div class="insight-box success">
                    <strong>🏆 Top Performer</strong><br>
                    {top_performer['assigned_to']}<br>
                    {top_performer['completion_rate']:.1f}% complete
                </div>
                """, unsafe_allow_html=True)
                
                # At risk
                if not pic_stats[pic_stats['completion_rate'] < 50].empty:
                    at_risk = pic_stats[pic_stats['completion_rate'] < 50].iloc[0]
                    st.markdown(f"""
                    <div class="insight-box danger">
                        <strong>⚠️ Needs Support</strong><br>
                        {at_risk['assigned_to']}<br>
                        {at_risk['completion_rate']:.1f}% complete
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("**Detailed Performance Table:**")
            display_df = pic_stats[['assigned_to', 'total', 'done', 'delayed', 'completion_rate', 'sla_score']].copy()
            display_df.columns = ['Team Member', 'Total Tasks', 'Completed', 'Delayed', 'Completion %', 'SLA Score']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ========== SECTION 4: RISK ANALYSIS ==========
    st.markdown('<div class="ai-section"><h3>⚠️ 4. Risk Assessment & Alerts</h3>', unsafe_allow_html=True)
    
    if not site_ms.empty:
        high_risk = site_ms[(site_ms['status'].isin(['DELAYED', 'CRITICAL'])) | 
                            ((site_ms['status']=='PENDING') & (site_ms['progress'] < 10))]
        medium_risk = site_ms[(site_ms['status']=='ONGOING') & (site_ms['progress'] < 40)]
        low_risk = site_ms[~site_ms.index.isin(high_risk.index) & ~site_ms.index.isin(medium_risk.index)]
        
        col_risk1, col_risk2 = st.columns([1.5, 1])
        
        with col_risk1:
            risk_data = {
                'Risk Level': ['🔴 High Risk', '🟡 Medium Risk', '🟢 Low Risk'],
                'Count': [len(high_risk), len(medium_risk), len(low_risk)]
            }
            risk_df = pd.DataFrame(risk_data)
            
            fig_risk = px.pie(
                risk_df,
                values='Count',
                names='Risk Level',
                color='Risk Level',
                color_discrete_map={
                    '🔴 High Risk': '#DC2626',
                    '🟡 Medium Risk': '#FF8C00',
                    '🟢 Low Risk': '#10B981'
                }
            )
            fig_risk.update_layout(
                height=300,
                margin=dict(t=0, b=0, l=0, r=0),
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#1F2937')
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        
        with col_risk2:
            st.markdown(f"""
            <div class="insight-box danger">
                <strong>🔴 High Risk Items: {len(high_risk)}</strong><br>
                Tasks that are delayed or critical
            </div>
            <div class="insight-box warning">
                <strong>🟡 Medium Risk Items: {len(medium_risk)}</strong><br>
                Tasks in progress with low completion
            </div>
            <div class="insight-box success">
                <strong>🟢 Low Risk Items: {len(low_risk)}</strong><br>
                On track or completed tasks
            </div>
            """, unsafe_allow_html=True)
        
        # Critical alerts
        if len(high_risk) > 0:
            st.markdown("**🔴 Critical Tasks Requiring Immediate Action:**")
            for _, task in high_risk.head(5).iterrows():
                days_late = (datetime.now().date() - pd.to_datetime(task.get('planned_end')).date()).days if pd.notna(task.get('planned_end')) else 0
                st.markdown(f"""
                <div class="insight-box danger">
                    <strong>{task['name']}</strong><br>
                    Status: {task['status']} | Progress: {task.get('progress', 0):.0f}% | Days Late: {max(0, days_late)}
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ========== SECTION 5: EXECUTIVE SUMMARY ==========
    st.markdown('<div class="ai-section"><h3>📋 5. Executive Summary & Recommendations</h3>', unsafe_allow_html=True)
    
    total_sites = len(sites_df)
    total_progress = sites_df['progress'].mean() if not sites_df.empty else 0
    on_track = len(sites_df[sites_df['status']=='DONE']) if not sites_df.empty else 0
    delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])]) if not sites_df.empty else 0
    health_score = round((on_track/total_sites)*100) if total_sites > 0 else 0
    
    col_exec1, col_exec2, col_exec3, col_exec4 = st.columns(4)
    
    with col_exec1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{health_score}%</div>
            <div class="label">Health Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_exec2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{total_progress:.1f}%</div>
            <div class="label">Avg Progress</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_exec3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{on_track}/{total_sites}</div>
            <div class="label">On Track</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_exec4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="value">{delayed}</div>
            <div class="label">Delayed Sites</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("**🎯 AI Recommendations:**")
    
    recommendations = []
    
    if health_score >= 80:
        recommendations.append("✅ **Excellent Progress** - Continue current approach and maintain momentum")
    elif health_score >= 60:
        recommendations.append("⚠️ **Moderate Progress** - Review workflows to improve completion rates")
    else:
        recommendations.append("🔴 **Critical Attention Needed** - Escalate delayed items and reallocate resources")
    
    if delayed > 0:
        recommendations.append(f"⏰ **Address {delayed} Delayed Items** - Conduct root cause analysis and implement recovery plan")
    
    if len(medium_risk) > len(high_risk) * 2:
        recommendations.append("📊 **Capacity Planning** - Medium-risk items may become critical; consider resource augmentation")
    
    if total_progress < 50 and (datetime.now() - datetime(2024, 1, 1)).days > 90:
        recommendations.append("📅 **Timeline Review** - Current progress rate may not meet original deadlines; adjust expectations")
    
    for i, rec in enumerate(recommendations, 1):
        st.markdown(f"{i}. {rec}")
    
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    ai_insights_page()
