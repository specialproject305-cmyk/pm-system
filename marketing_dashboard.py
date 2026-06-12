import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase_db import read_sheet

def marketing_dashboard_page():
    st.title("📢 Marketing Dashboard")
    
    df = read_sheet("marketing_sites")
    
    if df.empty:
        st.info("📋 Belum ada data marketing site.")
        return
    
    # KPI
    total = len(df)
    rfs = len(df[df['milestone'] == 'RFS']) if 'milestone' in df.columns else 0
    erected = len(df[df['milestone'] == 'Erected']) if 'milestone' in df.columns else 0
    on_progress = len(df[df['milestone'].isin(['On Progress', 'Pending', 'Negosiasi Lahan', 'RFI'])]) if 'milestone' in df.columns else 0
    tenant_count = df['tenant_index'].nunique() if 'tenant_index' in df.columns else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📢 Total Sites", total)
    col2.metric("✅ RFS", rfs)
    col3.metric("🏗️ Erected", erected)
    col4.metric("🔄 On Progress", on_progress)
    col5.metric("🏢 Tenants", tenant_count)
    
    st.divider()
    
    # Charts Row 1
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📊 By Tenant")
        if 'tenant_index' in df.columns:
            tenant_counts = df['tenant_index'].value_counts()
            fig1 = px.bar(x=tenant_counts.index, y=tenant_counts.values, color=tenant_counts.values, color_continuous_scale='Blues')
            fig1.update_layout(height=300)
            st.plotly_chart(fig1, use_container_width=True)
    
    with col_b:
        st.subheader("📌 By Milestone")
        if 'milestone' in df.columns:
            ms_counts = df['milestone'].value_counts()
            fig2 = px.pie(values=ms_counts.values, names=ms_counts.index, hole=0.5)
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)
    
    st.divider()
    
    # Charts Row 2
    col_c, col_d = st.columns(2)
    
    with col_c:
        st.subheader("📋 By SPK Status")
        if 'spk_status' in df.columns:
            spk_counts = df['spk_status'].value_counts()
            fig3 = px.pie(values=spk_counts.values, names=spk_counts.index, hole=0.5,
                         color_discrete_map={'CLOSE':'#10B981','OPEN':'#3B82F6','DROP':'#EF4444'})
            fig3.update_layout(height=300)
            st.plotly_chart(fig3, use_container_width=True)
    
    with col_d:
        st.subheader("🏗️ By Work Type")
        if 'work_type' in df.columns:
            wt_counts = df['work_type'].value_counts()
            fig4 = px.pie(values=wt_counts.values, names=wt_counts.index, hole=0.5)
            fig4.update_layout(height=300)
            st.plotly_chart(fig4, use_container_width=True)
    
    st.divider()
    
    # Table
    st.subheader("📋 Data Marketing Sites")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sel_tenant = st.selectbox("🏢 Tenant:", ['ALL'] + sorted(df['tenant_index'].dropna().unique().tolist()) if 'tenant_index' in df.columns else ['ALL'])
    with col_f2:
        sel_status = st.selectbox("📋 SPK Status:", ['ALL'] + sorted(df['spk_status'].dropna().unique().tolist()) if 'spk_status' in df.columns else ['ALL'])
    
    filtered = df.copy()
    if sel_tenant != 'ALL': filtered = filtered[filtered['tenant_index'] == sel_tenant]
    if sel_status != 'ALL': filtered = filtered[filtered['spk_status'] == sel_status]
    
    display_cols = ['spk_number', 'spk_date', 'tenant_index', 'spk_status', 'site_id_tenant', 'site_name_tenant', 'work_type', 'tower_height', 'milestone']
    st.dataframe(filtered[[c for c in display_cols if c in filtered.columns]], use_container_width=True, hide_index=True)
    
    st.download_button("📥 Download CSV", filtered.to_csv(index=False), f"marketing_report_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

if __name__ == "__main__":
    marketing_dashboard_page()
