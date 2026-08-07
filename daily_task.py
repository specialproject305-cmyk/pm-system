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

    # 3. Filter Master Project (dropdown)
    if not master_df.empty:
        project_options = ["ALL"] + master_df["id"].tolist()
        sel_project = st.selectbox(
            "🏢 Master Project:",
            project_options,
            format_func=lambda x: "🌐 SEMUA PROJECT"
            if x == "ALL"
            else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}",
        )
        if sel_project != "ALL":
            valid_sites = sites_df[sites_df["master_project_id"] == sel_project]["id"].tolist()
            ms_df = ms_df[ms_df["project_id"].isin(valid_sites)]
            sites_df = sites_df[sites_df["id"].isin(valid_sites)]

    if ms_df.empty:
        st.info("✅ Tidak ada milestone untuk project ini.")
        return

    # 4. Siapkan pivot: baris = site_name, kolom = milestone name, nilai = status
    site_map = dict(zip(sites_df["id"], sites_df["site_name"]))
    ms_df["site_name"] = ms_df["project_id"].map(site_map).fillna("-")

    # Pivot table
    pivot = ms_df.pivot_table(
        index="site_name",
        columns="name",
        values="status",
        aggfunc="first",  # jika ada duplikat, ambil pertama
    )

    # Urutkan kolom milestone berdasarkan planned_start (opsional, agar kronologis)
    ms_df["planned_start"] = pd.to_datetime(ms_df["planned_start"], errors="coerce")
    milestone_order = ms_df.groupby("name")["planned_start"].min().sort_values().index.tolist()
    # Hanya ambil kolom yang ada di pivot
    ordered_cols = [col for col in milestone_order if col in pivot.columns]
    pivot = pivot[ordered_cols]

    # 5. Warna berdasarkan status
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

    # 6. Tampilkan
    project_label = (
        "Semua Project"
        if sel_project == "ALL"
        else f"{master_df[master_df['id']==sel_project]['project_name'].values[0]}"
    )
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
