import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase_db import read_sheet

def inject_css():
    st.markdown("""
    <style>
        .inv-header {
            background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
            padding: 20px 28px; border-radius: 16px; margin-bottom: 20px;
            color: white; box-shadow: 0 10px 30px rgba(37,99,235,0.25);
        }
        .inv-header h1 { margin:0; font-size:1.6rem; font-weight:800; }
        .inv-header p { margin:4px 0 0; font-size:0.85rem; opacity:0.9; }
        
        .stat-card {
            background: white; border-radius: 14px; padding: 18px 14px;
            text-align: center; box-shadow: 0 4px 16px rgba(0,0,0,0.06);
            border: 1px solid #E2E8F0; transition: all 0.3s;
        }
        .stat-card:hover { transform: translateY(-4px); box-shadow: 0 12px 30px rgba(0,0,0,0.1); }
        .stat-card .val { font-size: 2rem; font-weight:800; color:#1E40AF; line-height:1; }
        .stat-card .lbl { font-size:0.75rem; color:#64748B; text-transform:uppercase; font-weight:600; margin-top:4px; }
        
        .chart-box {
            background: white; border-radius: 14px; padding: 10px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.06); border:1px solid #E2E8F0;
            margin-bottom: 10px;
        }
        .chart-box h3 { font-size:0.75rem; color:#1E293B; margin:0 0 4px 0; padding-bottom:4px; font-weight:700; border-bottom:1px solid #E2E8F0; }
        
        .filter-bar {
            background: white; border-radius: 12px; padding: 14px 18px;
            margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            border:1px solid #E2E8F0;
        }
    </style>
    """, unsafe_allow_html=True)

def inventory_dashboard_page():
    inject_css()
    st.markdown('<div class="inv-header"><h1>📦 Inventory Dashboard</h1><p>Real-time inventory analytics & monitoring</p></div>', unsafe_allow_html=True)
    
    df = read_sheet("inventory_transactions")
    
    if df.empty:
        st.info("📋 Belum ada data inventory."); return
    
    # Numeric conversion
    for col in ['mr_qty','nod_qty','issue_qty','return_qty','reloc_qty','mr_transact_qty']:
        if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # ===== FILTER BAR (Terintegrasi dengan sistem) =====
    # Load data dari tabel lain untuk filter
    projects_df = read_sheet("projects")
    
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        # Vendor dari tabel inventory
        vendors = ['ALL'] + sorted(df['vendor'].dropna().unique().tolist()) if 'vendor' in df.columns else ['ALL']
        sel_vendor = st.selectbox("🏢 Vendor", vendors)
    
    with c2:
        # Project Name dari tabel inventory
        projects = ['ALL'] + sorted(df['project_name'].dropna().unique().tolist()) if 'project_name' in df.columns else ['ALL']
        sel_project = st.selectbox("📁 Project", projects)
    
    with c3:
        # Site Name dari tabel projects (terintegrasi)
        site_list = ['ALL'] + sorted(projects_df['site_name'].dropna().unique().tolist()) if not projects_df.empty else ['ALL']
        sel_site = st.selectbox("📍 Site Name", site_list)
    
    with c4:
        # SPK Vendor dari tabel inventory
        spk_list = ['ALL'] + sorted(df['spk_vendor'].dropna().unique().tolist()) if 'spk_vendor' in df.columns else ['ALL']
        sel_spk = st.selectbox("📄 SPK Vendor", spk_list)
    
    with c5:
        if st.button("🔄 Reset Filter", use_container_width=True): st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Apply filters
    filtered = df.copy()
    if sel_vendor != 'ALL': filtered = filtered[filtered['vendor'] == sel_vendor]
    if sel_project != 'ALL': filtered = filtered[filtered['project_name'] == sel_project]
    if sel_site != 'ALL': filtered = filtered[filtered['site_name'] == sel_site]
    if sel_spk != 'ALL': filtered = filtered[filtered['spk_vendor'] == sel_spk]
    
    # ===== KPI CARDS =====
    total_records = len(filtered)
    total_mr = filtered['mr_number'].nunique() if 'mr_number' in filtered.columns else 0
    total_qty = filtered['mr_qty'].sum() if 'mr_qty' in filtered.columns else 0
    total_issue = filtered['issue_qty'].sum() if 'issue_qty' in filtered.columns else 0
    settle_done = len(filtered[filtered['settle_status']=='Settle Done']) if 'settle_status' in filtered.columns else 0
    settle_rate = (settle_done/total_records*100) if total_records>0 else 0
    
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.markdown(f'<div class="stat-card"><div class="val">{total_records}</div><div class="lbl">Total Records</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="stat-card"><div class="val">{total_mr}</div><div class="lbl">Unique MR</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="stat-card"><div class="val">{total_qty:.0f}</div><div class="lbl">Total Qty</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="stat-card"><div class="val">{total_issue:.0f}</div><div class="lbl">Issued</div></div>', unsafe_allow_html=True)
    k5.markdown(f'<div class="stat-card"><div class="val">{settle_done}</div><div class="lbl">Settle Done</div></div>', unsafe_allow_html=True)
    k6.markdown(f'<div class="stat-card"><div class="val">{settle_rate:.0f}%</div><div class="lbl">Settle Rate</div></div>', unsafe_allow_html=True)
    
    st.divider()
    
    # ===== CHARTS ROW 1 =====
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown('<div class="chart-box"><h3>📊 By Vendor</h3>', unsafe_allow_html=True)
        if 'vendor' in filtered.columns:
            vendor_counts = filtered['vendor'].value_counts().head(10)
            fig1 = px.bar(x=vendor_counts.index, y=vendor_counts.values, color=vendor_counts.values, color_continuous_scale=['#3B82F6','#1E40AF'])
            fig1.update_layout(height=300, margin=dict(t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_b:
        st.markdown('<div class="chart-box"><h3>📌 By Settle Status</h3>', unsafe_allow_html=True)
        if 'settle_status' in filtered.columns:
            status_counts = filtered['settle_status'].value_counts()
            fig2 = px.pie(values=status_counts.values, names=status_counts.index, hole=0.5, color_discrete_map={'Settle Done':'#10B981','Partial':'#F59E0B','Pending':'#EF4444'})
            fig2.update_layout(height=300, margin=dict(t=0,b=0), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== CHARTS ROW 2 =====
    col_c, col_d = st.columns(2)
    
    with col_c:
        st.markdown('<div class="chart-box"><h3>📈 By Status MR</h3>', unsafe_allow_html=True)
        if 'status_mr_new' in filtered.columns:
            mr_counts = filtered['status_mr_new'].value_counts()
            fig3 = px.pie(values=mr_counts.values, names=mr_counts.index, hole=0.5, color_discrete_map={'DONE':'#10B981','PARTIAL':'#F59E0B','PENDING':'#94A3B8'})
            fig3.update_layout(height=300, margin=dict(t=0,b=0), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_d:
        st.markdown('<div class="chart-box"><h3>📊 Top Items</h3>', unsafe_allow_html=True)
        if 'item_description' in filtered.columns:
            item_counts = filtered['item_description'].value_counts().head(8)
            fig4 = px.bar(y=item_counts.index, x=item_counts.values, orientation='h', color=item_counts.values, color_continuous_scale=['#3B82F6','#1E40AF'])
            fig4.update_layout(height=300, margin=dict(t=0,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== TABLE =====
    st.divider()
    st.subheader("📋 Recent Transactions")
    display_cols = ['warehouse','vendor','site_id','site_name','item_description','mr_number','mr_transact_date','settle_status','project_name']
    st.dataframe(filtered[[c for c in display_cols if c in filtered.columns]].head(20), use_container_width=True, hide_index=True)
    
    st.download_button("📥 Download Filtered CSV", filtered.to_csv(index=False), f"inventory_report_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

if __name__ == "__main__":
    inventory_dashboard_page()
