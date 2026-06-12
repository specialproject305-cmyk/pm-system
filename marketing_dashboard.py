import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from supabase_db import read_sheet

def marketing_dashboard_page():
    st.title("📢 Marketing Dashboard")
    st.caption("Overview data site dari tim Marketing")
    
    # Load data
    df = read_sheet("marketing_sites")
    
    if df.empty:
        st.info("📋 Belum ada data marketing site.")
        return
    
    # ===== KPI CARDS =====
    total = len(df)
    rfs = len(df[df['milestone'] == 'RFS']) if 'milestone' in df.columns else 0
    erected = len(df[df['milestone'] == 'Erected']) if 'milestone' in df.columns else 0
    on_progress = len(df[df['milestone'].isin(['On Progress', 'Pending'])]) if 'milestone' in df.columns else 0
    
    tenant_count = df['tenant_name'].nunique() if 'tenant_name' in df.columns else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📢 Total Sites", total)
    col2.metric("✅ RFS", rfs)
    col3.metric("🏗️ Erected", erected)
    col4.metric("🔄 On Progress", on_progress)
    col5.metric("🏢 Tenants", tenant_count)
    
    st.divider()
    
    # ===== CHARTS ROW 1 =====
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📊 By Tenant")
        if 'tenant_name' in df.columns:
            tenant_counts = df['tenant_name'].value_counts().head(10)
            fig = px.bar(x=tenant_counts.index, y=tenant_counts.values, 
                        color=tenant_counts.values, color_continuous_scale='Blues')
            fig.update_layout(height=300, xaxis_title="", yaxis_title="Sites")
            st.plotly_chart(fig, use_container_width=True)
    
    with col_b:
        st.subheader("📌 By Milestone")
        if 'milestone' in df.columns:
            ms_counts = df['milestone'].value_counts()
            fig2 = px.pie(values=ms_counts.values, names=ms_counts.index, hole=0.5,
                         color_discrete_map={'RFS':'#10B981','Erected':'#3B82F6','On Progress':'#F59E0B','Pending':'#9CA3AF','Cancelled':'#EF4444'})
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)
    
    st.divider()
    
    # ===== CHARTS ROW 2 =====
    col_c, col_d = st.columns(2)
    
    with col_c:
        st.subheader("👷 By PIC")
        if 'pic' in df.columns:
            pic_counts = df['pic'].value_counts().head(10)
            fig3 = px.bar(x=pic_counts.index, y=pic_counts.values, orientation='h',
                        color=pic_counts.values, color_continuous_scale='Greens')
            fig3.update_layout(height=350, xaxis_title="Sites", yaxis_title="")
            st.plotly_chart(fig3, use_container_width=True)
    
    with col_d:
        st.subheader("🏗️ By Work Type")
        if 'work_type' in df.columns:
            wt_counts = df['work_type'].value_counts()
            fig4 = px.pie(values=wt_counts.values, names=wt_counts.index, hole=0.5)
            fig4.update_layout(height=300)
            st.plotly_chart(fig4, use_container_width=True)
    
    st.divider()
    
    # ===== TABLE =====
    st.subheader("📋 Data Marketing Sites")
    
    # Filters
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        sel_tenant = st.selectbox("🏢 Tenant:", ['ALL'] + sorted(df['tenant_name'].dropna().unique().tolist()) if 'tenant_name' in df.columns else ['ALL'])
    with col_f2:
        sel_milestone = st.selectbox("📌 Milestone:", ['ALL'] + sorted(df['milestone'].dropna().unique().tolist()) if 'milestone' in df.columns else ['ALL'])
    with col_f3:
        sel_pic = st.selectbox("👷 PIC:", ['ALL'] + sorted(df['pic'].dropna().unique().tolist()) if 'pic' in df.columns else ['ALL'])
    
    filtered = df.copy()
    if sel_tenant != 'ALL': filtered = filtered[filtered['tenant_name'] == sel_tenant]
    if sel_milestone != 'ALL': filtered = filtered[filtered['milestone'] == sel_milestone]
    if sel_pic != 'ALL': filtered = filtered[filtered['pic'] == sel_pic]
    
    display_cols = ['tenant_name', 'pic', 'division', 'site_id_tenant', 'site_name_tenant', 'work_type', 'tower_height', 'milestone', 'mobile_number']
    st.dataframe(filtered[[c for c in display_cols if c in filtered.columns]], use_container_width=True, hide_index=True)
    
    # Export
    st.download_button("📥 Download CSV", filtered.to_csv(index=False), f"marketing_report_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

if __name__ == "__main__":
    marketing_dashboard_page()
