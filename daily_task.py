import streamlit as st
import pandas as pd
from supabase_db import read_all_sheets

def daily_task_page():
    st.title("📋 Daily Task Heatmap")
    st.caption("Status Milestone per Site — Dikelompokkan per Master Project")

    # 1. Load data
    all_data = read_all_sheets()
    ms_df = all_data.get("milestones", pd.DataFrame())
    sites_df = all_data.get("projects", pd.DataFrame())
    master_df = all_data.get("master_projects", pd.DataFrame())

    if ms_df.empty or sites_df.empty:
        st.info("📭 Belum ada data milestone atau site.")
        return

    # 2. Global filter (dari sidebar)
    if st.session_state.get("global_project_filter", "ALL") != "ALL":
        valid_sites = (
            sites_df[sites_df.get("master_project_id", "") == st.session_state.global_project_filter]["id"]
            .tolist()
        )
        sites_df = sites_df[sites_df["id"].isin(valid_sites)]
        ms_df = ms_df[ms_df["project_id"].isin(valid_sites)]

    # 3. Filter Baru
    st.markdown("### 🔍 Filter Data")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    # Filter by Master Project
    with col_f1:
        sel_project = "ALL"
        if not master_df.empty:
            project_options = ["ALL"] + master_df["id"].tolist()
            sel_project = st.selectbox(
                "🏢 Master Project:",
                project_options,
                format_func=lambda x: "🌐 SEMUA"
                if x == "ALL"
                else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}",
                key="heat_project"
            )

    # Filter by PM
    with col_f2:
        pm_list = ['ALL'] + sorted(sites_df['pm'].dropna().unique().tolist()) if 'pm' in sites_df.columns else ['ALL']
        sel_pm = st.selectbox("👤 PM:", pm_list, key="heat_pm")

    # Filter by Vendor
    with col_f3:
        vendor_list = ['ALL'] + sorted(sites_df['vendor'].dropna().unique().tolist()) if 'vendor' in sites_df.columns else ['ALL']
        sel_vendor = st.selectbox("🏢 Vendor:", vendor_list, key="heat_vendor")

    # Filter by Site Name
    with col_f4:
        site_list = ['ALL'] + sorted(sites_df['site_name'].dropna().unique().tolist()) if not sites_df.empty else ['ALL']
        sel_site = st.selectbox("📍 Site Name:", site_list, key="heat_site")

    # Apply filters
    if sel_project != "ALL" and not master_df.empty:
        valid_sites = sites_df[sites_df["master_project_id"] == sel_project]["id"].tolist()
        ms_df = ms_df[ms_df["project_id"].isin(valid_sites)]
        sites_df = sites_df[sites_df["id"].isin(valid_sites)]
    if sel_pm != 'ALL' and 'pm' in sites_df.columns:
        valid_sites = sites_df[sites_df['pm'] == sel_pm]['id'].tolist()
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)]
        sites_df = sites_df[sites_df['id'].isin(valid_sites)]
    if sel_vendor != 'ALL' and 'vendor' in sites_df.columns:
        valid_sites = sites_df[sites_df['vendor'] == sel_vendor]['id'].tolist()
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)]
        sites_df = sites_df[sites_df['id'].isin(valid_sites)]
    if sel_site != 'ALL':
        valid_sites = sites_df[sites_df['site_name'] == sel_site]['id'].tolist()
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)]
        sites_df = sites_df[sites_df['id'].isin(valid_sites)]

    if ms_df.empty:
        st.info("✅ Tidak ada milestone untuk filter ini.")
        return

    # 4. Summary total milestone
    total_ms = len(ms_df)
    done_ms = len(ms_df[ms_df['status'] == 'DONE'])
    delayed_ms = len(ms_df[ms_df['status'].isin(['DELAYED', 'CRITICAL'])])
    ongoing_ms = len(ms_df[ms_df['status'] == 'ONGOING'])
    pending_ms = len(ms_df[ms_df['status'] == 'PENDING'])

    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    col_s1.metric("📋 Total Milestone", total_ms)
    col_s2.metric("✅ Done", done_ms)
    col_s3.metric("🔄 On Going", ongoing_ms)
    col_s4.metric("⏳ Pending", pending_ms)
    col_s5.metric("🔴 Delayed", delayed_ms)

    # 5. Siapkan pivot: baris = site_name, kolom = milestone name, nilai = status
    site_map = dict(zip(sites_df["id"], sites_df["site_name"]))
    ms_df["site_name"] = ms_df["project_id"].map(site_map).fillna("-")

    pivot = ms_df.pivot_table(
        index="site_name",
        columns="name",
        values="status",
        aggfunc="first",
    )

    # Urutkan kolom milestone berdasarkan planned_start
    ms_df["planned_start"] = pd.to_datetime(ms_df["planned_start"], errors="coerce")
    milestone_order = ms_df.groupby("name")["planned_start"].min().sort_values().index.tolist()
    ordered_cols = [col for col in milestone_order if col in pivot.columns]
    pivot = pivot[ordered_cols]

    # 6. Warna berdasarkan status
    def color_status(val):
        if val == "DONE":
            return "background-color: #DCFCE7; color: #166534; font-weight: bold;"
        elif val == "ONGOING":
            return "background-color: #DBEAFE; color: #1E40AF; font-weight: bold;"
        elif val == "PENDING":
            return "background-color: #F1F5F9; color: #475569;"
        elif val in ("DELAYED", "CRITICAL"):
            return "background-color: #FEE2E2; color: #991B1B; font-weight: bold;"
        return ""

    styled = pivot.style.map(color_status)

    # 7. Tampilkan
    project_label = "Semua Project"
    if sel_project != "ALL" and not master_df.empty:
        match = master_df[master_df['id'] == sel_project]
        if not match.empty:
            project_label = match['project_name'].values[0]

    st.subheader(f"🔥 Heatmap Status Milestone — {project_label}")

    # Keterangan warna
    st.markdown("""
    <div style="display:flex; gap:20px; margin-bottom:10px;">
        <span style="background:#DCFCE7; padding:4px 12px; border-radius:4px; color:#166534;">✅ Done</span>
        <span style="background:#DBEAFE; padding:4px 12px; border-radius:4px; color:#1E40AF;">🔄 On Going</span>
        <span style="background:#F1F5F9; padding:4px 12px; border-radius:4px; color:#475569;">⏳ Pending</span>
        <span style="background:#FEE2E2; padding:4px 12px; border-radius:4px; color:#991B1B;">🔴 Delayed</span>
    </div>
    """, unsafe_allow_html=True)

    st.dataframe(styled, use_container_width=True)

if __name__ == "__main__":
    daily_task_page()
