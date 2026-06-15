import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase_db import read_sheet, read_all_sheets

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
    
    # ===== LOAD SEMUA DATA UTAMA & MASTER RELASI =====
    try:
        try:
            all_data = read_all_sheets()
            df = all_data.get('inventory_transactions', pd.DataFrame())
            sites_df = all_data.get('projects', pd.DataFrame())
            master_df = all_data.get('master_projects', pd.DataFrame())
        except:
            df = read_sheet("inventory_transactions")
            sites_df = read_sheet("projects")
            master_df = read_sheet("master_projects")
    except Exception as e:
        st.error(f"⚠️ Error loading data: {e}")
        return
    
    if df.empty:
        st.info("📋 Belum ada data inventory."); return
    
    # Konversi numerik awal
    for col in ['mr_qty','nod_qty','issue_qty','return_qty','reloc_qty','mr_transact_qty']:
        if col in df.columns: 
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    # ===== INTEGRASI RE-MAPPING SINKRONISASI TABEL RELASI =====
    # Pastikan data transaksi mengacu ke data master project asli
    if not sites_df.empty and 'project_id' in df.columns:
        # Relasikan project_id transaksi ke site master info
        site_code_map = dict(zip(sites_df['id'], sites_df['site_id']))
        site_name_map = dict(zip(sites_df['id'], sites_df['site_name']))
        spk_vendor_map = dict(zip(sites_df['id'], sites_df['spk_vendor'])) if 'spk_vendor' in sites_df.columns else {}
        master_proj_id_map = dict(zip(sites_df['id'], sites_df['master_project_id'])) if 'master_project_id' in sites_df.columns else {}
        
        df['site_id'] = df['project_id'].map(site_code_map).fillna(df.get('site_id', '-'))
        df['site_name'] = df['project_id'].map(site_name_map).fillna(df.get('site_name', '-'))
        
        # Integrasi SPK Vendor langsung dari tabel master project jika ada
        if spk_vendor_map:
            df['spk_vendor'] = df['project_id'].map(spk_vendor_map).fillna(df.get('spk_vendor', '-'))
            
        # Integrasi Nama Master Project (By Project)
        if master_proj_id_map and not master_df.empty:
            master_name_map = dict(zip(master_df['id'], master_df['project_name']))
            df['master_project_name'] = df['project_id'].map(master_proj_id_map).map(master_name_map).fillna(df.get('project_name', '-'))
        else:
            df['master_project_name'] = df.get('project_name', '-')
    else:
        df['master_project_name'] = df.get('project_name', '-')

    # ===== FILTER BAR INTEGRASI MULTI-TABEL =====
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        vendors = ['ALL'] + sorted(df['vendor'].dropna().unique().tolist()) if 'vendor' in df.columns else ['ALL']
        sel_vendor = st.selectbox("🏢 Vendor", vendors, key="inv_f_vendor")
    
    # 1. Filter Berantai untuk Master Project Name
    sub_df = df.copy()
    if sel_vendor != 'ALL':
        sub_df = sub_df[sub_df['vendor'] == sel_vendor]
        
    with c2:
        master_projects = ['ALL'] + sorted(sub_df['master_project_name'].dropna().unique().tolist())
        sel_project = st.selectbox("📁 Master Project", master_projects, key="inv_f_project")
        
    # 2. Filter Berantai untuk Site Name (Terintegrasi tabel projects)
    if sel_project != 'ALL':
        sub_df = sub_df[sub_df['master_project_name'] == sel_project]
        
    with c3:
        site_list = ['ALL'] + sorted(sub_df['site_name'].dropna().unique().tolist())
        sel_site = st.selectbox("📍 Site Name", site_list, key="inv_f_site")
        
    # 3. Filter Berantai untuk Nomor SPK Vendor (Terintegrasi tabel projects)
    if sel_site != 'ALL':
        sub_df = sub_df[sub_df['site_name'] == sel_site]
        
    with c4:
        spk_list = ['ALL'] + sorted(sub_df['spk_vendor'].dropna().unique().tolist()) if 'spk_vendor' in sub_df.columns else ['ALL']
        sel_spk = st.selectbox("📄 SPK Vendor", spk_list, key="inv_f_spk")
    
    with c5:
        st.markdown("<div style='padding-top:24px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Reset Filter", use_container_width=True, key="inv_reset_filter_core"):
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== APPLY FINAL FILTER KE DATASET TRANSAKSI =====
    filtered = df.copy()
    if sel_vendor != 'ALL': filtered = filtered[filtered['vendor'] == sel_vendor]
    if sel_project != 'ALL': filtered = filtered[filtered['master_project_name'] == sel_project]
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
        if 'vendor' in filtered.columns and not filtered.empty:
            vendor_counts = filtered['vendor'].value_counts().head(10).reset_index()
            vendor_counts.columns = ['Vendor', 'Count']
            fig1 = px.bar(vendor_counts, x='Vendor', y='Count', color='Count', color_continuous_scale=['#3B82F6','#1E40AF'])
            fig1.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig1, use_container_width=True, key="chart_vendor_bar_v2")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_b:
        st.markdown('<div class="chart-box"><h3>📌 By Settle Status</h3>', unsafe_allow_html=True)
        if 'settle_status' in filtered.columns and not filtered.empty:
            status_counts = filtered['settle_status'].value_counts()
            fig2 = px.pie(values=status_counts.values, names=status_counts.index, hole=0.5, color_discrete_map={'Settle Done':'#10B981','Partial':'#F59E0B','Pending':'#EF4444'})
            fig2.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig2, use_container_width=True, key="chart_settle_pie_v2")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== CHARTS ROW 2 =====
    col_c, col_d = st.columns(2)
    
    with col_c:
        st.markdown('<div class="chart-box"><h3>📈 By Status MR</h3>', unsafe_allow_html=True)
        if 'status_mr_new' in filtered.columns and not filtered.empty:
            mr_counts = filtered['status_mr_new'].value_counts()
            fig3 = px.pie(values=mr_counts.values, names=mr_counts.index, hole=0.5, color_discrete_map={'DONE':'#10B981','PARTIAL':'#F59E0B','PENDING':'#94A3B8'})
            fig3.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig3, use_container_width=True, key="chart_mr_status_pie_v2")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_d:
        st.markdown('<div class="chart-box"><h3>📊 Top Items</h3>', unsafe_allow_html=True)
        if 'item_description' in filtered.columns and not filtered.empty:
            item_counts = filtered['item_description'].value_counts().head(8).reset_index()
            item_counts.columns = ['Item', 'Count']
            fig4 = px.bar(item_counts, y='Item', x='Count', orientation='h', color='Count', color_continuous_scale=['#3B82F6','#1E40AF'])
            fig4.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig4, use_container_width=True, key="chart_top_items_bar_v2")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== TABLE DATA DISPLAY =====
    st.divider()
    st.subheader("📋 Recent Transactions")
    # Memasukkan master_project_name ke kolom visualisasi tabel agar sinkron
    filtered['project_name'] = filtered['master_project_name']
    display_cols = ['warehouse', 'vendor', 'site_id', 'site_name', 'spk_vendor', 'item_description', 'mr_number', 'mr_transact_date', 'settle_status', 'project_name']
    st.dataframe(filtered[[c for c in display_cols if c in filtered.columns]].head(20), use_container_width=True, hide_index=True)
    
    st.download_button(
        "📥 Download Filtered CSV", 
        filtered.to_csv(index=False), 
        f"inventory_report_{datetime.now().strftime('%Y%m%d')}.csv", 
        "text/csv",
        key="inv_download_csv_final"
    )

if __name__ == "__main__":
    inventory_dashboard_page()
