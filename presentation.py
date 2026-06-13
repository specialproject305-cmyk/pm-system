import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import inspect
from supabase_db import read_all_sheets

# ─────────────────────────────────────────────────────────────
# 🎨 RE-ENGINEERED PRESENTATION CSS
# ─────────────────────────────────────────────────────────────
def inject_presentation_css():
    st.markdown("""
    <style>
        /* === BASE CANVAS BACKGROUND === */
        .stApp { 
            background: linear-gradient(135deg, #F8FAFC 0%, #E2E8F0 100%) !important;
            color: #1E293B;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            padding: 15px;
        }
        section.main > div { padding: 0 !important; }
        
        /* === FILTERS ACCENT ROW === */
        div[data-testid="stHorizontalBlock"] {
            background: rgba(255, 255, 255, 0.6);
            padding: 10px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 15px;
        }

        /* === PREMIUM HEADLINE HERO === */
        .slide-title { 
            font-size: 2.2rem; 
            font-weight: 800; 
            text-align: center; 
            color: #0F172A; 
            margin: 15px 0 5px 0; 
            text-transform: uppercase;
            letter-spacing: -0.5px;
        }
        .slide-subtitle { 
            font-size: 0.95rem; 
            text-align: center; 
            color: #475569; 
            margin-bottom: 25px; 
            font-weight: 500;
        }
        
        /* === GRID EXECUTIVE KPI BOX === */
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            margin-bottom: 25px;
        }
        .kpi-box { 
            background: #FFFFFF; 
            border-radius: 14px; 
            padding: 18px 10px; 
            text-align: center; 
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.05);
            border: 1px solid #E2E8F0; 
            transition: transform 0.2s ease;
        }
        .kpi-box:hover { transform: translateY(-3px); }
        .kpi-box .val { font-size: 2.2rem; font-weight: 800; color: #1E3A8A; line-height: 1.1; }
        .kpi-box .lbl { font-size: 0.75rem; color: #64748B; text-transform: uppercase; font-weight: 700; margin-top: 6px; letter-spacing: 0.5px; }
        
        /* === WHITE WRAPPER BLOCK FOR CHARTS & TABLES === */
        .chart-card {
            background: #FFFFFF;
            padding: 20px;
            border-radius: 16px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 15px;
        }
        
        /* === MODERN CLEAN ALERTS === */
        .alert-r { background: #FEF2F2; border-left: 4px solid #EF4444; padding: 10px 14px; margin: 6px 0; border-radius: 8px; font-size: 0.85rem; color: #991B1B; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .alert-y { background: #FFFBEB; border-left: 4px solid #F59E0B; padding: 10px 14px; margin: 6px 0; border-radius: 8px; font-size: 0.85rem; color: #92400E; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .alert-g { background: #F0FDF4; border-left: 4px solid #10B981; padding: 10px 14px; margin: 6px 0; border-radius: 8px; font-size: 0.85rem; color: #166534; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        
        .footer { text-align: center; color: #64748B; margin-top: 30px; font-size: 0.75rem; font-weight: 500; border-top: 1px solid #CBD5E1; padding-top: 15px; }
        
        /* === NAVIGATION RADIO BUTTONS (TAB STYLE) === */
        .stRadio > div { justify-content: center; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
        .stRadio label { 
            background: #FFFFFF !important; 
            padding: 8px 16px !important; 
            border-radius: 25px !important; 
            color: #475569 !important; 
            font-weight: 600 !important; 
            font-size: 0.85rem !important; 
            border: 1px solid #E2E8F0 !important; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
        }
        .stRadio div[data-testid="stMarkdownContainer"] p { color: #475569 !important; font-weight: 600; }
        .stRadio input:checked + label { 
            background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%) !important; 
            color: white !important; 
            border-color: #3B82F6 !important;
            box-shadow: 0 4px 10px rgba(59, 130, 246, 0.25) !important;
        }
        .stRadio input:checked + label p { color: white !important; }
        
        /* === STREAMLIT NATIVE TABLE INHERITANCE === */
        div[data-testid="stDataFrame"] { background: white; border-radius: 8px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

def style_plotly_chart(fig):
    """Fungsi pembantu injection tema grafik agar menyatu dengan background dashboard"""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, Segoe UI, sans-serif", color="#334155"),
        margin=dict(t=30, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    fig.update_xaxes(showgrid=False, color="#64748B")
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9", color="#64748B")
    return fig

def presentation_page():
    inject_presentation_css()
    
    # ═══════════════════════════════════════
    # DATA LOADING & BACKEND LOGIC (UNTOUCHED)
    # ═══════════════════════════════════════
    all_data = read_all_sheets()
    sites_df = all_data.get('projects', pd.DataFrame())
    ms_df = all_data.get('milestones', pd.DataFrame())
    mat_df = all_data.get('materials', pd.DataFrame())
    master_df = all_data.get('master_projects', pd.DataFrame())
    marketing_df = all_data.get('marketing_sites', pd.DataFrame())
    
    if sites_df.empty:
        st.warning("📋 No data available")
        return
    
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid = sites_df[sites_df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
        sites_df = sites_df[sites_df['id'].isin(valid)]
        ms_df = ms_df[ms_df['project_id'].isin(valid)] if not ms_df.empty else ms_df
    
    # Dropdown Filter Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        pm_list = ['ALL PM'] + sorted(sites_df['pm'].dropna().unique().tolist()) if 'pm' in sites_df.columns else ['ALL']
        sel_pm = st.selectbox("👤 PM", pm_list, key="p_pm", label_visibility="collapsed")
    with c2:
        ven_list = ['ALL Vendor'] + sorted(sites_df['vendor'].dropna().unique().tolist()) if 'vendor' in sites_df.columns else ['ALL']
        sel_ven = st.selectbox("🏢 Vendor", ven_list, key="p_ven", label_visibility="collapsed")
    with c3:
        cat_list = ['ALL Region'] + sorted(sites_df['site_category'].dropna().unique().tolist()) if 'site_category' in sites_df.columns else ['ALL']
        sel_cat = st.selectbox("📍 Region", cat_list, key="p_cat", label_visibility="collapsed")
    with c4:
        prj_list = ['ALL Project'] + sorted(master_df['project_name'].unique().tolist()) if not master_df.empty else ['ALL']
        sel_prj = st.selectbox("🏗️ Project", prj_list, key="p_prj", label_visibility="collapsed")
    
    if sel_pm != 'ALL PM': sites_df = sites_df[sites_df['pm'] == sel_pm]
    if sel_ven != 'ALL Vendor': sites_df = sites_df[sites_df['vendor'] == sel_ven]
    if sel_cat != 'ALL Region': sites_df = sites_df[sites_df['site_category'] == sel_cat]
    if sel_prj != 'ALL Project' and not master_df.empty:
        mid = master_df[master_df['project_name']==sel_prj]['id'].values[0]
        sites_df = sites_df[sites_df.get('master_project_id','') == mid]
    
    valid_sites = sites_df['id'].tolist()
    ms_df = ms_df[ms_df['project_id'].isin(valid_sites)] if not ms_df.empty else ms_df
    
    sites_df['progress'] = pd.to_numeric(sites_df['progress'], errors='coerce').fillna(0)
    if not ms_df.empty: ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    if not mat_df.empty:
        for c in ['current_stock','min_stock']:
            if c in mat_df.columns: mat_df[c] = pd.to_numeric(mat_df[c], errors='coerce').fillna(0)
    
    total = len(sites_df)
    avg_prog = sites_df['progress'].mean() if total > 0 else 0
    rfs = len(sites_df[sites_df['status'].isin(['DONE','ON_TRACK'])])
    delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])])
    pending = len(sites_df[sites_df['status']=='PENDING'])
    health = round((rfs/total)*100) if total>0 else 0
    now_ts = pd.Timestamp.now()
    forecast = now_ts + timedelta(days=int((100-avg_prog)*3))
    
    mkt_total = len(marketing_df)
    mkt_rfs = len(marketing_df[marketing_df['milestone']=='RFS']) if not marketing_df.empty else 0
    mkt_nego = len(marketing_df[marketing_df['milestone'].isin(['Negosiasi Lahan','RFI'])]) if not marketing_df.empty else 0
    
    pic_stats = pd.DataFrame()
    if not ms_df.empty and 'assigned_to' in ms_df.columns:
        pic_stats = ms_df.groupby('assigned_to').agg(total=('id','count'), done=('status',lambda x:(x=='DONE').sum()), delayed=('status',lambda x:(x.isin(['DELAYED','CRITICAL'])).sum())).reset_index()
        pic_stats['completion'] = round((pic_stats['done']/pic_stats['total'])*100,1)
    
    ven_stats = pd.DataFrame()
    if 'vendor' in sites_df.columns:
        ven_stats = sites_df.groupby('vendor').agg(total=('id','count'), avg_prog=('progress','mean'), delayed=('status',lambda x:(x.isin(['DELAYED','CRITICAL'])).sum())).reset_index()
        ven_stats['avg_prog'] = ven_stats['avg_prog'].round(1)

    # ===== SLIDE NAVIGATION TAB STYLE =====
    slide = st.radio("", ["1. Executive Summary", "2. Site & PIC Performance", "3. Progress & S-Curve", "4. Alerts & Marketing", "5. Actions & Forecast"], horizontal=True, label_visibility="collapsed")
    
    # ═══════════════════════════════════════
    # 🎬 SLIDE 1: EXECUTIVE SUMMARY
    # ═══════════════════════════════════════
    if "1." in slide:
        st.markdown('<div class="slide-title">📊 Executive Summary</div>', unsafe_allow_html=True)
        st.markdown('<div class="slide-subtitle">Macro KPIs, Vendor Matrices and Commercial Marketing Funnel</div>', unsafe_allow_html=True)
        
        # Render KPI dengan CSS Grid agar full container width
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-box"><div class="val">{total}</div><div class="lbl">Total Site</div></div>
            <div class="kpi-box"><div class="val">{avg_prog:.0f}%</div><div class="lbl">Avg Progress</div></div>
            <div class="kpi-box"><div class="val">{rfs}</div><div class="lbl">On Track</div></div>
            <div class="kpi-box"><div class="val" style="color:#DC2626;">{delayed}</div><div class="lbl">At Risk</div></div>
            <div class="kpi-box"><div class="val" style="color:#D97706;">{pending}</div><div class="lbl">Pending</div></div>
            <div class="kpi-box"><div class="val" style="color:#10B981;">{health}%</div><div class="lbl">Health</div></div>
        </div>
        """, unsafe_allow_html=True)
        
        c_a, c_b = st.columns(2)
        with c_a:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("<h4>🏢 Vendor Performance Leaderboard</h4>", unsafe_allow_html=True)
            if not ven_stats.empty: 
                st.dataframe(ven_stats, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_b:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("<h4>📢 Commercial Marketing Pipeline</h4>", unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Funnel", mkt_total)
            m2.metric("RFS Closed", mkt_rfs)
            m3.metric("Land Nego", mkt_nego)
            
            st.markdown("<div style='margin-top:15px; border-top:1px dashed #E2E8F0; padding-top:10px;'>", unsafe_allow_html=True)
            if not marketing_df.empty and 'tenant_index' in marketing_df.columns:
                for t, c in marketing_df['tenant_index'].value_counts().items():
                    st.caption(f"🔹 **Tenant {t}** account shares: **{c} sites**")
            st.markdown("</div></div>", unsafe_allow_html=True)
            
    # ═══════════════════════════════════════
    # 🏗️ SLIDE 2: SITE & PIC PERFORMANCE
    # ═══════════════════════════════════════
    elif "2." in slide:
        st.markdown('<div class="slide-title">👷 Site & PIC Performance</div>', unsafe_allow_html=True)
        st.markdown('<div class="slide-subtitle">Granular Site Tracking Matrix and Task Delivery Accountability</div>', unsafe_allow_html=True)
        
        c_a, c_b = st.columns(2)
        with c_a:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("<h4>📍 Live Site Matrix Status</h4>", unsafe_allow_html=True)
            display = sites_df[['site_id','site_name','status','progress','pm']].head(12)
            def cr(row):
                s=row.get('status','')
                if 'CRITICAL' in str(s): return ['background:#FEE2E2; color:#991B1B; font-weight:600;']*5
                if 'DELAYED' in str(s): return ['background:#FFFBEB; color:#92400E; font-weight:600;']*5
                if 'DONE' in str(s) or 'ON_TRACK' in str(s): return ['background:#F0FDF4; color:#166534;']*5
                return ['']*5
            st.dataframe(display.style.apply(cr,axis=1), use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_b:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("<h4>👷 Task Ownership Achievement (PIC)</h4>", unsafe_allow_html=True)
            if not pic_stats.empty:
                for _, r in pic_stats.iterrows():
                    pct = r['completion']
                    clr = '#10B981' if pct>=80 else ('#F59E0B' if pct>=50 else '#DC2626')
                    st.markdown(f"<div style='margin-bottom:8px;'><b>{r['assigned_to']}</b> &mdash; <small style='color:#64748B;'>{r['done']}/{r['total']} tasks resolved ({pct}%)</small></div>", unsafe_allow_html=True)
                    st.progress(pct/100)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("<h4>📊 Field Delay Factor Root-Cause Analysis</h4>", unsafe_allow_html=True)
        if not ms_df.empty and 'delay_reason' in ms_df.columns:
            reasons = ms_df[ms_df['delay_reason'].notna() & (ms_df['delay_reason']!='') & (ms_df['delay_reason']!='Tidak Ada')]
            if not reasons.empty:
                rc = reasons['delay_reason'].value_counts()
                fig_r = px.pie(values=rc.values, names=rc.index, hole=0.5, height=220, color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(style_plotly_chart(fig_r), use_container_width=True)
            else:
                st.info("✅ No outstanding field blockers documented.")
        st.markdown('</div>', unsafe_allow_html=True)
            
    # ═══════════════════════════════════════
    # 📈 SLIDE 3: PROGRESS & S-CURVE
    # ═══════════════════════════════════════
    elif "3." in slide:
        st.markdown('<div class="slide-title">📈 Progress & S-Curve</div>', unsafe_allow_html=True)
        st.markdown('<div class="slide-subtitle">Analytical Velocity Trends and Production Curves</div>', unsafe_allow_html=True)
        
        c_a, c_b = st.columns(2)
        with c_a:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("<h4>🏆 Top 10 Advanced Active Sites (%)</h4>", unsafe_allow_html=True)
            top10 = sites_df.nlargest(10,'progress')
            fig1 = px.bar(top10, y='site_name', x='progress', orientation='h', color='progress', color_continuous_scale='Blugrn', height=260)
            fig1.update_layout(coloraxis_showscale=False)
            st.plotly_chart(style_plotly_chart(fig1), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_b:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("<h4>📌 Macroscopic Site Status Distribution</h4>", unsafe_allow_html=True)
            if 'status' in sites_df.columns:
                sc = sites_df['status'].value_counts()
                fig2 = px.pie(values=sc.values, names=sc.index, hole=0.5, height=260, color_discrete_map={'DONE':'#10B981','ON_TRACK':'#3B82F6','ONGOING':'#F59E0B','PENDING':'#94A3B8','DELAYED':'#DC2626','CRITICAL':'#991B1B'})
                st.plotly_chart(style_plotly_chart(fig2), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        if not ms_df.empty:
            ms_t = ms_df.dropna(subset=['planned_end']).copy()
            if not ms_t.empty:
                ms_t['month'] = ms_t['planned_end'].dt.to_period('M').astype(str)
                monthly = ms_t.groupby('month').size().cumsum().reset_index(name='cumulative')
                fig3 = px.line(monthly, x='month', y='cumulative', markers=True, height=240, title="📈 Macro Milestone Accumulation Line (S-Curve)")
                fig3.update_traces(line_color='#1E3A8A', line_width=3, marker=dict(size=8, color='#3B82F6'))
                st.plotly_chart(style_plotly_chart(fig3), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
            
    # ═══════════════════════════════════════
    # ⚠️ SLIDE 4: ALERTS & MARKETING
    # ═══════════════════════════════════════
    elif "4." in slide:
        st.markdown('<div class="slide-title">⚠️ Alerts & Marketing</div>', unsafe_allow_html=True)
        st.markdown('<div class="slide-subtitle">Risk Mitigation Control Room and Supply Chains Logistics</div>', unsafe_allow_html=True)
        
        c_a, c_b, c_c = st.columns(3)
        with c_a:
            st.markdown('<div class="chart-card" style="min-height:380px;">', unsafe_allow_html=True)
            st.markdown("<h4>🚨 Critical Risk Sites</h4>", unsafe_allow_html=True)
            crit = sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])]
            if not crit.empty:
                for _, r in crit.head(5).iterrows():
                    st.markdown(f'<div class="alert-r"><b>{r["site_id"]}</b><br>Linear Progress: {r.get("progress",0):.0f}%</div>', unsafe_allow_html=True)
            else:
                st.success("All sites operating on normal track.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_b:
            st.markdown('<div class="chart-card" style="min-height:380px;">', unsafe_allow_html=True)
            st.markdown("<h4>📦 Material Safety Stock Depletion</h4>", unsafe_allow_html=True)
            if not mat_df.empty:
                cm = mat_df[mat_df['current_stock']<mat_df['min_stock']]
                if not cm.empty:
                    for _, r in cm.head(5).iterrows():
                        st.markdown(f'<div class="alert-y"><b>{r["name"][:22]}</b><br>Stock Level: {r["current_stock"]:.0f} Pcs (Min: {r["min_stock"]:.0f})</div>', unsafe_allow_html=True)
                else: 
                    st.markdown('<div class="alert-g">🛡️ All materials safe above threshold</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_c:
            st.markdown('<div class="chart-card" style="min-height:380px;">', unsafe_allow_html=True)
            st.markdown("<h4>📢 Active Commercial Leases</h4>", unsafe_allow_html=True)
            if not marketing_df.empty:
                for _, r in marketing_df.head(5).iterrows():
                    clr = 'alert-g' if r.get('milestone')=='RFS' else ('alert-y' if r.get('milestone') in ['Negosiasi Lahan','RFI'] else 'alert-r')
                    st.markdown(f'<div class="{clr}"><b>{r.get("site_name_tenant","")[:20]}</b><br>{r.get("tenant_index","")} &bull; {r.get("milestone","")}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    # ═══════════════════════════════════════
    # 📋 SLIDE 5: ACTIONS & FORECAST
    # ═══════════════════════════════════════
    elif "5." in slide:
        st.markdown('<div class="slide-title">📋 Actions & Forecast</div>', unsafe_allow_html=True)
        st.markdown('<div class="slide-subtitle">Predictive Timeline Projections and Departmental Action Orders</div>', unsafe_allow_html=True)
        
        c_a, c_b = st.columns(2)
        with c_a:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown("<h4>🎯 Next-Week Targeted Performance Output</h4>", unsafe_allow_html=True)
            st.metric("Target RFS Accumulation", rfs+3, delta="+3 Build Output")
            st.metric("Target Mean Progress", "75%", delta=f"{75-avg_prog:.1f}% Needed")
            st.metric("Target Critical Mitigation", "0 Active Case", delta=f"-{delayed} Down")
            
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="kpi-box" style="background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%); border:none;">
                <div class="val" style="color:#FFFFFF; font-size:2.5rem;">{forecast.strftime('%d %b %Y')}</div>
                <div class="lbl" style="color:#93C5FD;">Calculated Forecast Completion</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_b:
            st.markdown('<div class="chart-card" style="min-height:435px;">', unsafe_allow_html=True)
            st.markdown("<h4>📋 Executive Directed Action Items</h4>", unsafe_allow_html=True)
            
            # Rendering list item dengan layout flexbox yang elegan
            action_items = [
                ("PROCUREMENT", "Order material kritis akibat stok menipis", "15 Jun"),
                ("OPERASIONAL", "Tambah 2 tim pendukung di regional kritis", "16 Jun"),
                ("LEGAL", "Eskalasi percepatan izin warga & KRK", "14 Jun"),
                ("MARKETING", "Follow up hasil negosiasi harga sewa lahan", "15 Jun"),
                ("PMO", "Daily status tracking khusus site critical", "Hari ini")
            ]
            
            for pic, act, dl in action_items:
                st.markdown(f"""
                <div style="display:flex; justify-content:between; align-items:center; border-bottom:1px solid #F1F5F9; padding:10px 0;">
                    <div style="flex:1;">
                        <span style="background:#E2E8F0; color:#334155; font-size:0.7rem; font-weight:700; padding:3px 8px; border-radius:4px; text-transform:uppercase;">{pic}</span>
                        <div style="font-size:0.85rem; color:#1E293B; margin-top:4px; font-weight:500;">{act}</div>
                    </div>
                    <div style="text-align:right; font-size:0.8rem; color:#64748B; font-weight:600; min-width:70px;">📅 {dl}</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            st.metric("📢 Marketing Target Revenue CLOSE", f"{mkt_rfs+5} Sites", delta="+5 Funnel Up")
            st.markdown('</div>', unsafe_allow_html=True)
            
    # ═══════════════════════════════════════
    # FOOTER LOGO BANNER
    # ═══════════════════════════════════════
    st.markdown(f'<div class="footer">⚡ PM System Executive Workspace • Weekly Master Report • {now_ts.strftime("%d %B %Y")}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    presentation_page()
