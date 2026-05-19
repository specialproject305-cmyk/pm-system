import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from supabase_db import read_all_sheets

def presentation_page():
    # CSS Biru Cerah
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none; }
        .stApp { margin-left: 0 !important; }
        .stApp { 
            background: linear-gradient(180deg, #E0F2FE 0%, #BAE6FD 50%, #7DD3FC 100%) !important;
            margin: 0; padding: 15px; min-height: 100vh;
        }
        section.main > div { padding: 0 !important; }
        
        .slide-title { font-size: 2.2rem; font-weight: 800; text-align: center; color: #0369A1; margin-bottom: 5px; }
        .slide-subtitle { font-size: 1rem; text-align: center; color: #0284C7; margin-bottom: 20px; }
        .kpi-big { background: white; border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        .kpi-big .value { font-size: 2.2rem; font-weight: 800; color: #0284C7; }
        .kpi-big .label { font-size: 0.85rem; color: #64748B; }
        .alert-red { background: #FEE2E2; border-left: 4px solid #EF4444; padding: 10px; margin: 6px 0; border-radius: 8px; }
        .alert-yellow { background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 10px; margin: 6px 0; border-radius: 8px; }
        .footer { text-align: center; color: #94A3B8; margin-top: 20px; font-size: 0.75rem; }
        
        .stRadio > div { justify-content: center; gap: 8px; flex-wrap: wrap; }
        .stRadio label { background: white; padding: 6px 14px; border-radius: 20px; color: #0369A1 !important; font-weight: 600; font-size: 0.8rem; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
        .stRadio label:hover { background: #38BDF8; color: white !important; }
        
        .stButton button { background: #0284C7; color: white; border-radius: 10px; }
        div[data-testid="stMetricValue"] { color: #0369A1; }
    </style>
    """, unsafe_allow_html=True)
    
    all_data = read_all_sheets()
    sites_df = all_data.get('projects', pd.DataFrame())
    ms_df = all_data.get('milestones', pd.DataFrame())
    mat_df = all_data.get('materials', pd.DataFrame())
    master_df = all_data.get('master_projects', pd.DataFrame())
    
    if sites_df.empty:
        st.warning("📋 Belum ada data.")
        return
    
    if 'progress' in sites_df.columns:
        sites_df['progress'] = pd.to_numeric(sites_df['progress'], errors='coerce').fillna(0)
    if not ms_df.empty:
        ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
        ms_df['actual_end'] = pd.to_datetime(ms_df['actual_end'], errors='coerce')
    if not mat_df.empty:
        for c in ['current_stock','min_stock']:
            if c in mat_df.columns: mat_df[c] = pd.to_numeric(mat_df[c], errors='coerce').fillna(0)
    
    total = len(sites_df)
    avg_prog = sites_df['progress'].mean()
    on_track = len(sites_df[sites_df['status']=='ON_TRACK'])
    delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])])
    health = round((on_track/total)*100) if total > 0 else 0
    forecast = datetime.now() + timedelta(days=int((100-avg_prog)*3))
    
    slide = st.radio("📑", ["1. Cover","2. Summary","3. Progress","4. Site Status","5. Alerts","6. Insights"], horizontal=True, label_visibility="collapsed")
    
    # ===== SLIDE 1: COVER =====
    if "1. Cover" in slide:
        st.markdown(f"""
        <div style="text-align:center; padding-top:12%;">
            <div style="font-size:5rem;">🏗️</div>
            <h1 style="font-size:3.5rem; color:#0369A1; margin:0;">MCP TOWER</h1>
            <p style="font-size:1.3rem; color:#0284C7;">Deployment Progress Report</p>
            <div style="margin-top:40px; background:white; display:inline-block; padding:12px 30px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.08);">
                <p style="font-size:1rem; color:#64748B; margin:0;">📅 {datetime.now().strftime('%d %B %Y')}</p>
            </div>
        </div>
        <div class="footer">PM System v2.0 • Confidential</div>
        """, unsafe_allow_html=True)
    
    # ===== SLIDE 2: EXECUTIVE SUMMARY =====
    elif "2. Summary" in slide:
        st.markdown('<div class="slide-title">📊 Executive Summary</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(f'<div class="kpi-big"><div class="value">{total}</div><div class="label">Total Site</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="kpi-big"><div class="value">{avg_prog:.1f}%</div><div class="label">Avg Progress</div></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="kpi-big"><div class="value">{on_track}</div><div class="label">On Track</div></div>', unsafe_allow_html=True)
        col4.markdown(f'<div class="kpi-big"><div class="value">{delayed}</div><div class="label">Need Attention</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gauge chart
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number", value=health,
            title={'text': "Health Score", 'font': {'size': 20, 'color': '#0369A1'}},
            gauge={'axis': {'range': [0,100]}, 'bar': {'color': "#0284C7"},
                   'steps': [{'range':[0,40],'color':'#FEE2E2'},{'range':[40,70],'color':'#FEF3C7'},{'range':[70,100],'color':'#DCFCE7'}]}
        ))
        fig_g.update_layout(height=250, margin=dict(t=30,b=10), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_g, use_container_width=True)
        
        st.markdown(f'<div class="footer">Forecast: {forecast.strftime("%d %b %Y")}</div>', unsafe_allow_html=True)
    
    # ===== SLIDE 3: PROGRESS =====
    elif "3. Progress" in slide:
        st.markdown('<div class="slide-title">📈 Progress Overview</div>', unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            top10 = sites_df.nlargest(10, 'progress')
            fig1 = px.bar(top10, y='site_id', x='progress', orientation='h',
                        color='progress', color_continuous_scale=['#F59E0B','#38BDF8','#0284C7'],
                        title="Top 10 Progress")
            fig1.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig1, use_container_width=True)
        
        with col_b:
            # Status pie
            if 'status' in sites_df.columns:
                status_counts = sites_df['status'].value_counts()
                fig2 = px.pie(values=status_counts.values, names=status_counts.index,
                            color_discrete_map={'ON_TRACK':'#10B981','DELAYED':'#F59E0B','CRITICAL':'#EF4444','PENDING':'#94A3B8'})
                fig2.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig2, use_container_width=True)
        
        # S-Curve
        if not ms_df.empty:
            ms_df['month'] = ms_df['planned_end'].dt.to_period('M').astype(str)
            monthly = ms_df.groupby('month').size().cumsum().reset_index(name='cumulative')
            fig3 = px.area(monthly, x='month', y='cumulative', title="Cumulative Milestone (S-Curve)")
            fig3.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig3, use_container_width=True)
    
    # ===== SLIDE 4: SITE STATUS =====
    elif "4. Site" in slide:
        st.markdown('<div class="slide-title">📍 Site Status</div>', unsafe_allow_html=True)
        
        display = sites_df[['site_id','site_name','status','progress','pm']].head(20)
        def color_row(row):
            if row['status'] == 'CRITICAL': return ['background-color:#FEE2E2']*5
            elif row['status'] == 'DELAYED': return ['background-color:#FEF3C7']*5
            elif row['status'] == 'ON_TRACK': return ['background-color:#DCFCE7']*5
            return ['']*5
        styled = display.style.apply(color_row, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("🟢 On Track", on_track)
        col_b.metric("🟡 Delayed", len(sites_df[sites_df['status']=='DELAYED']))
        col_c.metric("🔴 Critical", len(sites_df[sites_df['status']=='CRITICAL']))
    
    # ===== SLIDE 5: ALERTS =====
    elif "5. Alerts" in slide:
        st.markdown('<div class="slide-title">⚠️ Critical Alerts</div>', unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            if not ms_df.empty:
                delayed_ms = ms_df[ms_df['status'].isin(['DELAYED','CRITICAL'])]
                st.markdown(f"### 🔴 {len(delayed_ms)} Delayed Milestones")
                for _, r in delayed_ms.head(8).iterrows():
                    st.markdown(f'<div class="alert-red"><b>{r["name"]}</b><br><small>📅 {r["planned_end"].strftime("%d %b") if pd.notna(r.get("planned_end")) else "?"}</small></div>', unsafe_allow_html=True)
        
        with col_b:
            if not mat_df.empty:
                critical = mat_df[mat_df['current_stock'] < mat_df['min_stock']]
                st.markdown(f"### 📦 {len(critical)} Critical Materials")
                for _, r in critical.head(5).iterrows():
                    st.markdown(f'<div class="alert-yellow"><b>{r["name"]}</b><br><small>Stok: {r["current_stock"]:.0f} (Min: {r["min_stock"]:.0f})</small></div>', unsafe_allow_html=True)
            
            if not ms_df.empty:
                pending_count = len(ms_df[ms_df['status']=='PENDING'])
                st.info(f"📋 {pending_count} milestone masih PENDING")
    
    # ===== SLIDE 6: INSIGHTS =====
    elif "6. Insights" in slide:
        st.markdown('<div class="slide-title">🤖 AI Insights</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="kpi-big"><div class="value">{health}%</div><div class="label">Health Score</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="kpi-big"><div class="value">{forecast.strftime("%d %b")}</div><div class="label">Forecast</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Delay reason analysis
        if not ms_df.empty and 'delay_reason' in ms_df.columns:
            reasons = ms_df[ms_df['delay_reason'].notna() & (ms_df['delay_reason']!='') & (ms_df['delay_reason']!='Tidak Ada')]
            if not reasons.empty:
                fig_r = px.pie(reasons, names='delay_reason', title="Delay Reasons")
                fig_r.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_r, use_container_width=True)
        
        st.markdown("### 💡 Top Recommendations")
        if delayed > 0:
            st.warning(f"⚠️ Prioritaskan {delayed} site terlambat")
        if avg_prog < 50:
            st.warning("🚀 Percepat milestone awal")
        if health >= 80:
            st.success("✅ Performa excellent — pertahankan!")
        
        st.markdown('<div class="footer">PM System v2.0 • AI-Powered Analytics</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    presentation_page()
