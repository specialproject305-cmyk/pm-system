import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from supabase_db import read_all_sheets

def presentation_page():
    # Hide sidebar for full-screen
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        .stApp { 
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;
            margin: 0; 
            padding: 20px; 
            min-height: 100vh;
        }
        .stApp > div { padding: 0 !important; }
        section.main > div { padding: 0 !important; }
        
        .slide-title { font-size: 2.5rem; font-weight: 800; text-align: center; color: #38BDF8; margin-bottom: 5px; }
        .slide-subtitle { font-size: 1.1rem; text-align: center; color: #CBD5E1; margin-bottom: 30px; }
        .kpi-big { background: #1E293B; border-radius: 20px; padding: 25px; text-align: center; border: 2px solid #334155; }
        .kpi-big .value { font-size: 2.5rem; font-weight: 800; color: #38BDF8; }
        .kpi-big .label { font-size: 0.9rem; color: #CBD5E1; }
        .alert-red { background: #7F1D1D; border-left: 5px solid #EF4444; padding: 12px; margin: 8px 0; border-radius: 10px; color: white; }
        .alert-yellow { background: #78350F; border-left: 5px solid #F59E0B; padding: 12px; margin: 8px 0; border-radius: 10px; color: white; }
        .footer { text-align: center; color: #64748B; margin-top: 30px; font-size: 0.8rem; }
        
        .stRadio > div { justify-content: center; gap: 5px; }
        .stRadio label { background: #1E293B; padding: 8px 15px; border-radius: 8px; color: white !important; }
        .stRadio label:hover { background: #334155; }
        
        div[data-testid="stDataFrame"] { background: transparent !important; }
        div[data-testid="stDataFrame"] th { background: #1E293B !important; color: #CBD5E1 !important; }
        div[data-testid="stDataFrame"] td { background: transparent !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)
    
    all_data = read_all_sheets()
    sites_df = all_data.get('projects', pd.DataFrame())
    ms_df = all_data.get('milestones', pd.DataFrame())
    mat_df = all_data.get('materials', pd.DataFrame())
    
    if sites_df.empty:
        st.warning("📋 Belum ada data.")
        return
    
    if 'progress' in sites_df.columns:
        sites_df['progress'] = pd.to_numeric(sites_df['progress'], errors='coerce').fillna(0)
    if not ms_df.empty:
        ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    if not mat_df.empty:
        mat_df['current_stock'] = pd.to_numeric(mat_df['current_stock'], errors='coerce').fillna(0)
        mat_df['min_stock'] = pd.to_numeric(mat_df['min_stock'], errors='coerce').fillna(0)
    
    # Navigation
    slide = st.radio("📑 Navigasi Slide:", 
        ["1. Cover", "2. Executive Summary", "3. Progress Overview", "4. Site Status", "5. Critical Alerts", "6. AI Insights"],
        horizontal=True, label_visibility="collapsed")
    
    total = len(sites_df)
    avg_prog = sites_df['progress'].mean()
    on_track = len(sites_df[sites_df['status']=='ON_TRACK'])
    delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])])
    
    # ===== SLIDE 1: COVER =====
    if "1. Cover" in slide:
        st.markdown("""
        <div class="slide-container">
            <div style="text-align:center; padding-top:15%;">
                <h1 style="font-size:4rem; color:#38BDF8; margin:0;">MCP TOWER PROJECT</h1>
                <p style="font-size:1.5rem; color:#CBD5E1;">Deployment Progress Report</p>
                <div style="margin-top:50px;">
                    <p style="font-size:1.2rem; color:#94A3B8;">📅 {}</p>
                    <p style="font-size:1rem; color:#64748B;">Confidential - For Internal Use Only</p>
                </div>
            </div>
            <div class="footer">PM System v2.0</div>
        </div>
        """.format(datetime.now().strftime('%d %B %Y')), unsafe_allow_html=True)
    
    # ===== SLIDE 2: EXECUTIVE SUMMARY =====
    elif "2. Executive" in slide:
        st.markdown('<div class="slide-title">📊 Executive Summary</div>', unsafe_allow_html=True)
        st.markdown('<div class="slide-subtitle">Ringkasan Performa Project</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="kpi-big"><div class="value">{total}</div><div class="label">Total Site</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="kpi-big"><div class="value">{avg_prog:.1f}%</div><div class="label">Avg Progress</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="kpi-big"><div class="value">{on_track}</div><div class="label">On Track</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="kpi-big"><div class="value">{delayed}</div><div class="label">Need Attention</div></div>', unsafe_allow_html=True)
        
        health = round((on_track/total)*100) if total > 0 else 0
        color = '#10B981' if health >= 80 else ('#F59E0B' if health >= 50 else '#EF4444')
        st.markdown(f'<div style="text-align:center; margin-top:30px;"><span style="font-size:1.5rem; color:{color};">🟢</span> <span style="font-size:2rem; font-weight:800;">Health Score: {health}%</span></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="footer">PM System v2.0</div></div>', unsafe_allow_html=True)
    
    # ===== SLIDE 3: PROGRESS OVERVIEW =====
    elif "3. Progress" in slide:
        st.markdown('<div class="slide-title">📈 Progress Overview</div>', unsafe_allow_html=True)
        
        if not sites_df.empty:
            fig = px.bar(sites_df.nlargest(15, 'progress'), y='site_id', x='progress', orientation='h',
                       color='progress', color_continuous_scale=['#EF4444','#F59E0B','#10B981'],
                       title="Top 15 Site Progress")
            fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='white'), xaxis=dict(range=[0,105]))
            st.plotly_chart(fig, use_container_width=True)
        
        if not ms_df.empty:
            site_ms = ms_df[ms_df['status']=='DONE']
            if not site_ms.empty:
                site_ms['month'] = site_ms['planned_end'].dt.to_period('M').astype(str)
                monthly = site_ms.groupby('month').size().reset_index(name='done')
                fig2 = px.line(monthly, x='month', y='done', markers=True, title="Milestone Selesai per Bulan")
                fig2.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
                st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown('<div class="footer">PM System v2.0</div></div>', unsafe_allow_html=True)
    
    # ===== SLIDE 4: SITE STATUS =====
    elif "4. Site" in slide:
        st.markdown('<div class="slide-title">📍 Site Status</div>', unsafe_allow_html=True)
        
        display = sites_df[['site_id','site_name','status','progress','pm','vendor']].copy()
        def color_row(row):
            if row['status'] == 'CRITICAL': return ['background-color:#7F1D1D;color:white']*6
            elif row['status'] == 'DELAYED': return ['background-color:#78350F;color:white']*6
            elif row['status'] == 'ON_TRACK': return ['background-color:#064E3B;color:white']*6
            return ['']*6
        styled = display.style.apply(color_row, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True)
        
        st.markdown('<div class="footer">PM System v2.0</div></div>', unsafe_allow_html=True)
    
    # ===== SLIDE 5: CRITICAL ALERTS =====
    elif "5. Critical" in slide:
        st.markdown('<div class="slide-title">⚠️ Critical Alerts</div>', unsafe_allow_html=True)
        
        # Delayed milestones
        if not ms_df.empty:
            delayed_ms = ms_df[ms_df['status'].isin(['DELAYED','CRITICAL'])]
            if not delayed_ms.empty:
                st.markdown(f"### 🔴 {len(delayed_ms)} Milestone Delayed")
                for _, r in delayed_ms.head(10).iterrows():
                    st.markdown(f'<div class="alert-red"><b>{r["name"]}</b> — Deadline: {r["planned_end"].strftime("%d %b") if pd.notna(r.get("planned_end")) else "?"}</div>', unsafe_allow_html=True)
        
        # Critical materials
        if not mat_df.empty:
            critical_mat = mat_df[mat_df['current_stock'] < mat_df['min_stock']]
            if not critical_mat.empty:
                st.markdown(f"### 📦 {len(critical_mat)} Material Kritis")
                for _, r in critical_mat.head(5).iterrows():
                    st.markdown(f'<div class="alert-yellow"><b>{r["name"]}</b> — Stok: {r["current_stock"]:.0f} (Min: {r["min_stock"]:.0f})</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="footer">PM System v2.0</div></div>', unsafe_allow_html=True)
    
    # ===== SLIDE 6: AI INSIGHTS =====
    elif "6. AI" in slide:
        st.markdown('<div class="slide-title">🤖 AI Insights</div>', unsafe_allow_html=True)
        
        health = round((on_track/total)*100) if total > 0 else 0
        forecast = datetime.now() + timedelta(days=int((100-avg_prog)*3))
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="kpi-big"><div class="value">{health}%</div><div class="label">Health Score</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="kpi-big"><div class="value">{forecast.strftime("%d %b")}</div><div class="label">Forecast Completion</div></div>', unsafe_allow_html=True)
        
        st.markdown("### 💡 Rekomendasi", unsafe_allow_html=True)
        if delayed > 0:
            st.warning(f"⚠️ Prioritaskan {delayed} site yang terlambat")
        if avg_prog < 50:
            st.warning("🚀 Percepat milestone untuk meningkatkan progress")
        if delayed == 0 and avg_prog >= 70:
            st.success("✅ Performa bagus — pertahankan!")
        
        st.markdown('<div class="footer">PM System v2.0</div></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    presentation_page()
