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
        section.main > div { padding: 0 !important; }
        
        .slide-title {
            font-size: 2rem;
            font-weight: 900;
            text-align: center;
            color: #0369A1;
            margin: 10px 0 5px 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .slide-subtitle {
            font-size: 0.95rem;
            text-align: center;
            color: #0284C7;
            margin-bottom: 20px;
            font-weight: 500;
        }
        .kpi-big {
            background: linear-gradient(135deg, #FFFFFF 0%, #F5F9FF 100%);
            border-radius: 14px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 6px 18px rgba(59, 130, 246, 0.12);
            border: 2px solid #DBEAFE;
        }
        .kpi-big .value { font-size: 2.2rem; font-weight: 900; color: #0284C7; }
        .kpi-big .label { font-size: 0.8rem; color: #64748B; font-weight: 600; text-transform: uppercase; }
        
        .alert-red { background: #FEE2E2; border-left: 4px solid #DC2626; padding: 8px 12px; margin: 4px 0; border-radius: 6px; color: #7F1D1D; font-size: 0.85rem; }
        .alert-yellow { background: #FEF3C7; border-left: 4px solid #FF8C00; padding: 8px 12px; margin: 4px 0; border-radius: 6px; color: #D97706; font-size: 0.85rem; }
        .alert-green { background: #DCFCE7; border-left: 4px solid #10B981; padding: 8px 12px; margin: 4px 0; border-radius: 6px; color: #047857; font-size: 0.85rem; }
        .footer { text-align: center; color: #0284C7; margin-top: 20px; font-size: 0.75rem; font-weight: 600; }
        
        .stRadio > div { justify-content: center; gap: 6px; flex-wrap: wrap; }
        .stRadio label {
            background: white; padding: 6px 12px; border-radius: 16px; color: #0369A1 !important;
            font-weight: 600; font-size: 0.75rem; border: 1px solid #DBEAFE;
        }
        .stRadio label:hover { background: #38BDF8; color: white !important; }
        div[data-testid="stMetricValue"] { color: #0284C7; font-weight: 900; }
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
        marketing_df = all_data.get('marketing_sites', pd.DataFrame())
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
    
    # ===== FILTERS (Dashboard Integrated) =====
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        pm_list = ['ALL'] + sorted(sites_df['pm'].dropna().unique().tolist()) if 'pm' in sites_df.columns else ['ALL']
        sel_pm = st.selectbox("👤 PM:", pm_list, key="pres_pm")
    with col_f2:
        vendor_list = ['ALL'] + sorted(sites_df['vendor'].dropna().unique().tolist()) if 'vendor' in sites_df.columns else ['ALL']
        sel_vendor = st.selectbox("🏢 Vendor:", vendor_list, key="pres_vendor")
    with col_f3:
        region_list = ['ALL'] + sorted(sites_df['site_category'].dropna().unique().tolist()) if 'site_category' in sites_df.columns else ['ALL']
        sel_region = st.selectbox("📍 Region:", region_list, key="pres_region")
    
    # Apply filters
    if sel_pm != 'ALL': sites_df = sites_df[sites_df['pm'] == sel_pm]
    if sel_vendor != 'ALL': sites_df = sites_df[sites_df['vendor'] == sel_vendor]
    if sel_region != 'ALL': sites_df = sites_df[sites_df['site_category'] == sel_region]
    valid_sites = sites_df['id'].tolist()
    ms_df = ms_df[ms_df['project_id'].isin(valid_sites)] if not ms_df.empty else ms_df
    
    # Numeric conversions
    if 'progress' in sites_df.columns:
        sites_df['progress'] = pd.to_numeric(sites_df['progress'], errors='coerce').fillna(0)
    if not ms_df.empty:
        ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
        ms_df['actual_end'] = pd.to_datetime(ms_df['actual_end'], errors='coerce')
    if not mat_df.empty:
        for c in ['current_stock','min_stock']:
            if c in mat_df.columns: mat_df[c] = pd.to_numeric(mat_df[c], errors='coerce').fillna(0)
    
    # KPIs
    total = len(sites_df)
    avg_prog = sites_df['progress'].mean()
    on_track = len(sites_df[sites_df['status']=='DONE']) + len(sites_df[sites_df['status']=='ON_TRACK'])
    delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])])
    health = round((on_track/total)*100) if total > 0 else 0
    now_ts = pd.Timestamp.now()
    forecast = now_ts + timedelta(days=int((100-avg_prog)*3))
    
    # Marketing KPIs
    mkt_total = len(marketing_df)
    mkt_rfs = len(marketing_df[marketing_df['milestone']=='RFS']) if not marketing_df.empty else 0
    mkt_nego = len(marketing_df[marketing_df['milestone'].isin(['Negosiasi Lahan','RFI'])]) if not marketing_df.empty else 0
    
    # ===== SLIDE NAVIGATION =====
    st.markdown("<div style='text-align: center; margin-bottom: 10px;'>", unsafe_allow_html=True)
    slide = st.radio("", ["🎬 Cover", "📊 Executive Summary", "📈 Progress & S-Curve", "⚠️ Alerts & Marketing", "📋 Actions & Forecast"], horizontal=True, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ===== SLIDE 1: COVER =====
    if "Cover" in slide:
        st.markdown(f"""
        <div style="text-align:center; padding:50px 20px; min-height:70vh; display:flex; flex-direction:column; justify-content:center; align-items:center;">
            <div style="font-size:4rem; margin-bottom:20px;">🏗️</div>
            <h1 style="font-size:3rem; color:#0369A1; margin:0; font-weight:900;">WEEKLY PROJECT REPORT</h1>
            <p style="font-size:1.2rem; color:#0284C7; margin:15px 0 30px 0;">Deployment Progress & Performance</p>
            <div style="background:white; display:inline-block; padding:15px 30px; border-radius:12px; box-shadow:0 6px 18px rgba(59,130,246,0.15);">
                <p style="font-size:1rem; color:#64748B; margin:0;">📅 {now_ts.strftime('%d %B %Y')}</p>
                <p style="font-size:0.8rem; color:#94A3B8; margin:5px 0 0 0;">PM System • Confidential</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ===== SLIDE 2: EXECUTIVE SUMMARY =====
    elif "Summary" in slide:
        st.markdown('<div class="slide-title">📊 Executive Summary</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.markdown(f'<div class="kpi-big"><div class="value">{total}</div><div class="label">Total Sites</div></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="kpi-big"><div class="value">{avg_prog:.0f}%</div><div class="label">Progress</div></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="kpi-big"><div class="value">{on_track}</div><div class="label">On Track</div></div>', unsafe_allow_html=True)
        col4.markdown(f'<div class="kpi-big"><div class="value">{delayed}</div><div class="label">At Risk</div></div>', unsafe_allow_html=True)
        col5.markdown(f'<div class="kpi-big"><div class="value">{health}%</div><div class="label">Health</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Vendor table + Marketing summary
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**🏢 Vendor Performance**")
            if 'vendor' in sites_df.columns:
                vendor_stats = sites_df.groupby('vendor').agg(total=('id','count'), avg_prog=('progress','mean'), delayed=('status', lambda x: (x.isin(['DELAYED','CRITICAL'])).sum())).reset_index()
                vendor_stats['avg_prog'] = vendor_stats['avg_prog'].round(1)
                st.dataframe(vendor_stats, use_container_width=True, hide_index=True)
        with col_b:
            st.markdown("**📢 Marketing Pipeline**")
            st.metric("Total Marketing Sites", mkt_total)
            st.metric("✅ RFS", mkt_rfs)
            st.metric("🔄 Negosiasi/RFI", mkt_nego)
            if not marketing_df.empty and 'tenant_index' in marketing_df.columns:
                tenants = marketing_df['tenant_index'].value_counts().to_dict()
                for t, c in tenants.items():
                    st.caption(f"• {t}: {c} site")
    
    # ===== SLIDE 3: PROGRESS & S-CURVE =====
    elif "Progress" in slide:
        st.markdown('<div class="slide-title">📈 Progress & S-Curve</div>', unsafe_allow_html=True)
        
        col_a, col_b = st.columns([1, 1])
        with col_a:
            if not sites_df.empty:
                top10 = sites_df.nlargest(10, 'progress')
                fig1 = px.bar(top10, y='site_name', x='progress', orientation='h', color='progress', color_continuous_scale=['#FF8C00','#3B82F6','#10B981'])
                fig1.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937', size=9), showlegend=False, margin=dict(t=0))
                st.plotly_chart(fig1, use_container_width=True)
        with col_b:
            if 'status' in sites_df.columns:
                status_counts = sites_df['status'].value_counts()
                fig2 = px.pie(values=status_counts.values, names=status_counts.index, hole=0.5, color_discrete_map={'DONE':'#10B981','ON_TRACK':'#3B82F6','ONGOING':'#FF8C00','PENDING':'#94A3B8','DELAYED':'#DC2626','CRITICAL':'#991B1B'})
                fig2.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937', size=9), showlegend=True, margin=dict(t=0))
                st.plotly_chart(fig2, use_container_width=True)
        
        # S-CURVE (PENTING - TIDAK DIHAPUS)
        if not ms_df.empty and 'planned_end' in ms_df.columns:
            ms_temp = ms_df.dropna(subset=['planned_end']).copy()
            if not ms_temp.empty:
                ms_temp['month'] = ms_temp['planned_end'].dt.to_period('M').astype(str)
                monthly = ms_temp.groupby('month').size().cumsum().reset_index(name='cumulative')
                fig3 = px.line(monthly, x='month', y='cumulative', title="📈 Cumulative Milestones (S-Curve)", markers=True)
                fig3.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#1F2937', size=9), showlegend=False, margin=dict(t=30))
                st.plotly_chart(fig3, use_container_width=True)
    
    # ===== SLIDE 4: ALERTS & MARKETING =====
    elif "Alerts" in slide:
        st.markdown('<div class="slide-title">⚠️ Alerts & Marketing</div>', unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**🔴 Delayed Milestones**")
            if not ms_df.empty:
                delayed_ms = ms_df[ms_df['status'].isin(['DELAYED','CRITICAL'])].sort_values('planned_end')
                if not delayed_ms.empty:
                    for _, r in delayed_ms.head(6).iterrows():
                        days_late = (now_ts - r['planned_end']).days if pd.notna(r.get('planned_end')) else 0
                        st.markdown(f'<div class="alert-red"><b>{r["name"][:35]}</b><br>Late: {days_late}d | Prog: {r.get("progress",0):.0f}%</div>', unsafe_allow_html=True)
                else:
                    st.success("✅ No delayed milestones")
        
        with col_b:
            st.markdown("**📢 Marketing Sites**")
            if not marketing_df.empty:
                for _, r in marketing_df.head(8).iterrows():
                    status_color = 'alert-green' if r.get('milestone') == 'RFS' else ('alert-yellow' if r.get('milestone') in ['Negosiasi Lahan','RFI'] else 'alert-red')
                    st.markdown(f'<div class="{status_color}"><b>{r.get("site_name_tenant","")[:30]}</b><br>{r.get("tenant_index","")} | {r.get("milestone","")}</div>', unsafe_allow_html=True)
            else:
                st.info("No marketing data")
        
        # Material kritis
        st.markdown("**📦 Material Kritis**")
        if not mat_df.empty:
            crit = mat_df[mat_df['current_stock'] < mat_df['min_stock']]
            if not crit.empty:
                cols = st.columns(len(crit))
                for i, (_, r) in enumerate(crit.iterrows()):
                    with cols[i]:
                        st.metric(r['name'][:15], f"{r['current_stock']:.0f}", delta=f"-{r['min_stock']-r['current_stock']:.0f}")
            else:
                st.success("✅ Semua material aman")
    
    # ===== SLIDE 5: ACTIONS & FORECAST =====
    elif "Actions" in slide:
        st.markdown('<div class="slide-title">📋 Actions & Forecast</div>', unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**🎯 Target Minggu Depan**")
            st.metric("Target RFS", f"{on_track + 3}", delta="+3")
            st.metric("Target Progress", "75%", delta=f"{75-avg_prog:.0f}%")
            st.metric("Target Critical", "0", delta=f"-{delayed}")
            
            st.markdown("**📅 Forecast Completion**")
            st.markdown(f'<div class="kpi-big"><div class="value">{forecast.strftime("%d %b")}</div><div class="label">Estimated</div></div>', unsafe_allow_html=True)
        
        with col_b:
            st.markdown("**✅ Action Items**")
            actions = [
                ("PROCUREMENT", "Order material kritis", "15 Jun"),
                ("OPERASIONAL", "Tambah 2 tim", "16 Jun"),
                ("LEGAL", "Eskalasi izin", "14 Jun"),
                ("MARKETING", "Follow up negosiasi", "15 Jun"),
                ("PMO", "Daily tracking critical", "Hari ini"),
            ]
            for pic, action, deadline in actions:
                st.markdown(f"• **{pic}**: {action} — 📅 {deadline}")
            
            st.markdown("**📢 Marketing Target**")
            st.metric("Target CLOSE", f"{mkt_rfs + 5}", delta="+5")

    st.markdown('<div class="footer">PM System • Weekly Report • ' + now_ts.strftime('%d %B %Y') + '</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    presentation_page()
