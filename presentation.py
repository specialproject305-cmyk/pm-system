import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import inspect
from supabase_db import read_all_sheets

def inject_presentation_css():
    st.markdown("""
    <style>
        .stApp { margin-left: 0 !important; background: linear-gradient(180deg, #E0F2FE 0%, #BAE6FD 50%, #7DD3FC 100%) !important; padding: 10px; min-height: 100vh; }
        section.main > div { padding: 0 !important; }
        .slide-title { font-size: 1.6rem; font-weight: 900; text-align: center; color: #0369A1; margin: 5px 0; text-transform: uppercase; }
        .slide-subtitle { font-size: 0.8rem; text-align: center; color: #0284C7; margin-bottom: 10px; }
        .kpi-box { background: white; border-radius: 10px; padding: 12px; text-align: center; box-shadow: 0 3px 10px rgba(0,0,0,0.08); border: 1px solid #DBEAFE; }
        .kpi-box .val { font-size: 1.6rem; font-weight: 900; color: #0284C7; }
        .kpi-box .lbl { font-size: 0.7rem; color: #64748B; text-transform: uppercase; }
        .alert-r { background: #FEE2E2; border-left: 3px solid #DC2626; padding: 6px 10px; margin: 3px 0; border-radius: 4px; font-size: 0.75rem; }
        .alert-y { background: #FEF3C7; border-left: 3px solid #F59E0B; padding: 6px 10px; margin: 3px 0; border-radius: 4px; font-size: 0.75rem; }
        .alert-g { background: #DCFCE7; border-left: 3px solid #10B981; padding: 6px 10px; margin: 3px 0; border-radius: 4px; font-size: 0.75rem; }
        .footer { text-align: center; color: #0284C7; margin-top: 10px; font-size: 0.7rem; }
        .stRadio > div { justify-content: center; gap: 4px; flex-wrap: wrap; }
        .stRadio label { background: white; padding: 4px 10px; border-radius: 12px; color: #0369A1 !important; font-weight: 600; font-size: 0.7rem; border: 1px solid #DBEAFE; }
        .stRadio label:hover { background: #38BDF8; color: white !important; }
        div[data-testid="stDataFrame"] { font-size: 0.7rem; }
    </style>
    """, unsafe_allow_html=True)

def presentation_page():
    inject_presentation_css()
    
    # Load data
    all_data = read_all_sheets()
    sites_df = all_data.get('projects', pd.DataFrame())
    ms_df = all_data.get('milestones', pd.DataFrame())
    mat_df = all_data.get('materials', pd.DataFrame())
    master_df = all_data.get('master_projects', pd.DataFrame())
    marketing_df = all_data.get('marketing_sites', pd.DataFrame())
    
    if sites_df.empty:
        st.warning("📋 No data"); return
    
    # Global filter
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid = sites_df[sites_df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
        sites_df = sites_df[sites_df['id'].isin(valid)]
        ms_df = ms_df[ms_df['project_id'].isin(valid)] if not ms_df.empty else ms_df
    
    # Filters
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
    
    # Numeric
    sites_df['progress'] = pd.to_numeric(sites_df['progress'], errors='coerce').fillna(0)
    if not ms_df.empty: ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    if not mat_df.empty:
        for c in ['current_stock','min_stock']:
            if c in mat_df.columns: mat_df[c] = pd.to_numeric(mat_df[c], errors='coerce').fillna(0)
    
    total = len(sites_df)
    avg_prog = sites_df['progress'].mean()
    rfs = len(sites_df[sites_df['status'].isin(['DONE','ON_TRACK'])])
    delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])])
    pending = len(sites_df[sites_df['status']=='PENDING'])
    health = round((rfs/total)*100) if total>0 else 0
    now_ts = pd.Timestamp.now()
    forecast = now_ts + timedelta(days=int((100-avg_prog)*3))
    
    # Marketing
    mkt_total = len(marketing_df)
    mkt_rfs = len(marketing_df[marketing_df['milestone']=='RFS']) if not marketing_df.empty else 0
    mkt_nego = len(marketing_df[marketing_df['milestone'].isin(['Negosiasi Lahan','RFI'])]) if not marketing_df.empty else 0
    
    # PIC Performance
    pic_stats = pd.DataFrame()
    if not ms_df.empty and 'assigned_to' in ms_df.columns:
        pics = ms_df.groupby('assigned_to').agg(total=('id','count'), done=('status',lambda x:(x=='DONE').sum()), delayed=('status',lambda x:(x.isin(['DELAYED','CRITICAL'])).sum())).reset_index()
        pics['completion'] = round((pics['done']/pics['total'])*100,1)
    
    # Vendor Performance
    ven_stats = pd.DataFrame()
    if 'vendor' in sites_df.columns:
        ven_stats = sites_df.groupby('vendor').agg(total=('id','count'), avg_prog=('progress','mean'), delayed=('status',lambda x:(x.isin(['DELAYED','CRITICAL'])).sum())).reset_index()
        ven_stats['avg_prog'] = ven_stats['avg_prog'].round(1)
    
    # ===== SLIDE NAV =====
    slide = st.radio("", ["1. Executive Summary", "2. Site & PIC Performance", "3. Progress & S-Curve", "4. Alerts & Marketing", "5. Actions & Forecast"], horizontal=True, label_visibility="collapsed")
    
    # ===== SLIDE 1: EXECUTIVE SUMMARY =====
    if "1." in slide:
        st.markdown('<div class="slide-title">📊 Executive Summary</div>', unsafe_allow_html=True)
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.markdown(f'<div class="kpi-box"><div class="val">{total}</div><div class="lbl">Total Site</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi-box"><div class="val">{avg_prog:.0f}%</div><div class="lbl">Avg Progress</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi-box"><div class="val">{rfs}</div><div class="lbl">On Track</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="kpi-box"><div class="val">{delayed}</div><div class="lbl">At Risk</div></div>', unsafe_allow_html=True)
        k5.markdown(f'<div class="kpi-box"><div class="val">{pending}</div><div class="lbl">Pending</div></div>', unsafe_allow_html=True)
        k6.markdown(f'<div class="kpi-box"><div class="val">{health}%</div><div class="lbl">Health</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        c_a, c_b = st.columns(2)
        with c_a:
            st.markdown("**🏢 Vendor Performance**")
            if not ven_stats.empty: st.dataframe(ven_stats, use_container_width=True, hide_index=True)
        with c_b:
            st.markdown("**📢 Marketing Pipeline**")
            m1, m2, m3 = st.columns(3)
            m1.metric("Total", mkt_total); m2.metric("RFS", mkt_rfs); m3.metric("Negosiasi", mkt_nego)
            if not marketing_df.empty and 'tenant_index' in marketing_df.columns:
                for t, c in marketing_df['tenant_index'].value_counts().items():
                    st.caption(f"• {t}: {c} site")
    
    # ===== SLIDE 2: SITE & PIC PERFORMANCE =====
    elif "2." in slide:
        st.markdown('<div class="slide-title">👷 Site & PIC Performance</div>', unsafe_allow_html=True)
        c_a, c_b = st.columns(2)
        with c_a:
            st.markdown("**📍 Site Status**")
            display = sites_df[['site_id','site_name','status','progress','pm']].head(12)
            def cr(row):
                s=row.get('status','')
                if 'CRITICAL' in str(s): return ['background:#FEE2E2']*5
                if 'DELAYED' in str(s): return ['background:#FEF3C7']*5
                if 'DONE' in str(s) or 'ON_TRACK' in str(s): return ['background:#DCFCE7']*5
                return ['']*5
            st.dataframe(display.style.apply(cr,axis=1), use_container_width=True, hide_index=True)
        with c_b:
            st.markdown("**👷 PIC Performance**")
            if not pic_stats.empty:
                for _, r in pic_stats.iterrows():
                    pct = r['completion']
                    clr = '#10B981' if pct>=80 else ('#F59E0B' if pct>=50 else '#DC2626')
                    st.markdown(f"**{r['assigned_to']}**: {r['done']}/{r['total']} done | {pct}%")
                    st.progress(pct/100)
        
        st.markdown("---")
        st.markdown("**📊 Delay Reason Analysis**")
        if not ms_df.empty and 'delay_reason' in ms_df.columns:
            reasons = ms_df[ms_df['delay_reason'].notna() & (ms_df['delay_reason']!='') & (ms_df['delay_reason']!='Tidak Ada')]
            if not reasons.empty:
                rc = reasons['delay_reason'].value_counts()
                fig_r = px.pie(values=rc.values, names=rc.index, hole=0.5, height=200)
                fig_r.update_layout(margin=dict(t=0,b=0), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_r, use_container_width=True)
    
    # ===== SLIDE 3: PROGRESS & S-CURVE =====
    elif "3." in slide:
        st.markdown('<div class="slide-title">📈 Progress & S-Curve</div>', unsafe_allow_html=True)
        c_a, c_b = st.columns([1,1])
        with c_a:
            top10 = sites_df.nlargest(10,'progress')
            fig1 = px.bar(top10, y='site_name', x='progress', orientation='h', color='progress', color_continuous_scale=['#F59E0B','#3B82F6','#10B981'], height=280)
            fig1.update_layout(margin=dict(t=0), paper_bgcolor='rgba(0,0,0,0)', font=dict(size=9))
            st.plotly_chart(fig1, use_container_width=True)
        with c_b:
            if 'status' in sites_df.columns:
                sc = sites_df['status'].value_counts()
                fig2 = px.pie(values=sc.values, names=sc.index, hole=0.5, height=280, color_discrete_map={'DONE':'#10B981','ON_TRACK':'#3B82F6','ONGOING':'#F59E0B','PENDING':'#94A3B8','DELAYED':'#DC2626','CRITICAL':'#991B1B'})
                fig2.update_layout(margin=dict(t=0), paper_bgcolor='rgba(0,0,0,0)', font=dict(size=9))
                st.plotly_chart(fig2, use_container_width=True)
        
        # S-CURVE
        if not ms_df.empty:
            ms_t = ms_df.dropna(subset=['planned_end']).copy()
            if not ms_t.empty:
                ms_t['month'] = ms_t['planned_end'].dt.to_period('M').astype(str)
                monthly = ms_t.groupby('month').size().cumsum().reset_index(name='cumulative')
                fig3 = px.line(monthly, x='month', y='cumulative', title="📈 Cumulative Milestones (S-Curve)", markers=True, height=220)
                fig3.update_layout(margin=dict(t=30), paper_bgcolor='rgba(0,0,0,0)', font=dict(size=9))
                st.plotly_chart(fig3, use_container_width=True)
    
    # ===== SLIDE 4: ALERTS & MARKETING =====
    elif "4." in slide:
        st.markdown('<div class="slide-title">⚠️ Alerts & Marketing</div>', unsafe_allow_html=True)
        c_a, c_b, c_c = st.columns([1,1,1])
        with c_a:
            st.markdown("**🔴 Critical Sites**")
            crit = sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])]
            if not crit.empty:
                for _, r in crit.head(5).iterrows():
                    st.markdown(f'<div class="alert-r"><b>{r["site_id"]}</b> — {r.get("progress",0):.0f}%</div>', unsafe_allow_html=True)
        with c_b:
            st.markdown("**📦 Material Kritis**")
            if not mat_df.empty:
                cm = mat_df[mat_df['current_stock']<mat_df['min_stock']]
                if not cm.empty:
                    for _, r in cm.iterrows():
                        st.markdown(f'<div class="alert-y"><b>{r["name"][:20]}</b><br>Stok: {r["current_stock"]:.0f} (Min: {r["min_stock"]:.0f})</div>', unsafe_allow_html=True)
                else: st.success("Aman")
        with c_c:
            st.markdown("**📢 Marketing**")
            if not marketing_df.empty:
                for _, r in marketing_df.head(6).iterrows():
                    clr = 'alert-g' if r.get('milestone')=='RFS' else ('alert-y' if r.get('milestone') in ['Negosiasi Lahan','RFI'] else 'alert-r')
                    st.markdown(f'<div class="{clr}"><b>{r.get("site_name_tenant","")[:20]}</b><br>{r.get("tenant_index","")} | {r.get("milestone","")}</div>', unsafe_allow_html=True)
    
    # ===== SLIDE 5: ACTIONS & FORECAST =====
    elif "5." in slide:
        st.markdown('<div class="slide-title">📋 Actions & Forecast</div>', unsafe_allow_html=True)
        c_a, c_b = st.columns(2)
        with c_a:
            st.markdown("**🎯 Target Minggu Depan**")
            st.metric("Target RFS", rfs+3, delta="+3")
            st.metric("Target Progress", "75%", delta=f"{75-avg_prog:.0f}%")
            st.metric("Target Critical", "0", delta=f"-{delayed}")
            st.markdown(f'<div class="kpi-box"><div class="val">{forecast.strftime("%d %b")}</div><div class="lbl">Forecast Completion</div></div>', unsafe_allow_html=True)
        with c_b:
            st.markdown("**✅ Action Items**")
            for pic, act, dl in [("PROCUREMENT","Order material kritis","15 Jun"),("OPERASIONAL","Tambah 2 tim","16 Jun"),("LEGAL","Eskalasi izin","14 Jun"),("MARKETING","Follow up negosiasi","15 Jun"),("PMO","Daily tracking critical","Hari ini")]:
                st.markdown(f"• **{pic}**: {act} — 📅 {dl}")
            st.metric("📢 Marketing Target CLOSE", f"{mkt_rfs+5}", delta="+5")
    
    st.markdown(f'<div class="footer">PM System • Weekly Report • {now_ts.strftime("%d %B %Y")}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    presentation_page()
