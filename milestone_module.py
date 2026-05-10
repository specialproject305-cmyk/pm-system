import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
# Import diperbaiki agar sinkron dengan file supabase_db.py yang baru
from supabase_db import (
    read_sheet,
    insert_row,
    update_row,
    delete_row_by_id,
    generate_id,
    today_str,
    now_str
)

TOWER_TEMPLATE = {
    "SPK TENANT": ["Hunting dan Survey","Validation","Sosialisasi Warga Radius","Negosiasi Sewa Lahan","Negosiasi IW Radius","Pengajuan Budget IW & SA Lahan","BAK","Legal Proses","Akuisisi","RFC"],
    "APD, BoQ & Material": ["Soil test","APD Pondasi","APD & BoQ Tower full Design Pack","PR Material","PO Material","Produksi Massal","Material RFD","Pengiriman Material"],
    "Implementation": ["Request SPK","Proses Pengadaan vendor","Kick of Meeting (KoM)","Mobilisasi team & Bowplank","Foundation","Curing time","Backfilling","Erection","Pondasi rack ODC","Install ME & Grounding","Pekerjaan Fence","Lanscape","PLN connect","Install pole FO","Laying FO","Terminasi","DC Power Instalation","RFS","RFIN submit"]
}

DELAY_REASONS = ["Tidak Ada","Material Terlambat","Cuaca Buruk","Manpower Kurang","Vendor Terlambat","Izin/Tanah","Desain Berubah","Force Majeure","Lainnya"]

def sync_milestone_to_site(site_id):
    # Mengambil data terbaru untuk menghitung progress site
    ms_df = read_sheet("milestones")
    if ms_df.empty or "project_id" not in ms_df.columns: return
    
    site_ms = ms_df[ms_df["project_id"]==site_id].copy()
    if site_ms.empty: return
    
    site_ms["weight"] = pd.to_numeric(site_ms["weight"], errors="coerce").fillna(0)
    total_weight = site_ms["weight"].sum()
    done_weight = site_ms[site_ms["status"]=="DONE"]["weight"].sum()
    
    progress = round((done_weight/total_weight)*100, 1) if total_weight > 0 else 0
    delayed = len(site_ms[site_ms["status"]=="DELAYED"])
    
    status = "CRITICAL" if delayed > 3 else ("DELAYED" if delayed > 0 else "ON_TRACK")
    update_row("projects", site_id, {"progress": str(progress), "status": status})

def milestone_page():
    st.title("🧱 Milestone Monitoring")
    
    # Load data awal
    sites_df = read_sheet("projects")
    if sites_df.empty: 
        st.warning("⚠️ Tambahkan site dulu di menu Project Tracker!")
        return
    
    # Sidebar/Filter Site
    site_options = ["ALL SITE"] + sites_df["id"].tolist()
    selected_site = st.selectbox(
        "Pilih Site:", 
        site_options,
        format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE" 
        else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}"
    )
    
    is_all = (selected_site == "ALL SITE")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Gantt", "➕ Tambah", "🚀 Template", "✏️ Edit", "📥 Import"])
    
    # ===== TAB 1: GANTT CHART =====
    with tab1:
        ms_df = read_sheet("milestones")
        if ms_df.empty:
            st.info("Belum ada data milestone.")
        else:
            ms_df["planned_start"] = pd.to_datetime(ms_df["planned_start"], errors="coerce")
            ms_df["planned_end"] = pd.to_datetime(ms_df["planned_end"], errors="coerce")
            
            if is_all:
                st.subheader("📊 Gantt Chart - ALL SITE")
                grouped = ms_df.groupby("name").agg(
                    start=("planned_start", "min"),
                    end=("planned_end", "max"),
                    total_sites=("project_id", "nunique"),
                    done_count=("status", lambda x: (x == "DONE").sum()),
                    delayed_count=("status", lambda x: (x == "DELAYED").sum())
                ).reset_index()
                
                grouped = grouped.sort_values("start")
                def get_status(r):
                    if r["delayed_count"] > 0: return "DELAYED"
                    elif r["done_count"] == r["total_sites"]: return "DONE"
                    elif r["done_count"] > 0: return "ONGOING"
                    return "PENDING"
                
                grouped["status"] = grouped.apply(get_status, axis=1)
                color_map = {"PENDING": "#6c757d", "ONGOING": "#0d6efd", "DONE": "#28a745", "DELAYED": "#dc3545"}
                
                fig = px.timeline(grouped, x_start="start", x_end="end", y="name", color="status", color_discrete_map=color_map)
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)
            else:
                site_ms = ms_df[ms_df["project_id"] == selected_site].copy()
                if not site_ms.empty:
                    site_ms = site_ms.sort_values("planned_start")
                    today = datetime.now().date()
                    site_ms["is_critical"] = site_ms.apply(lambda r: r["planned_end"].date() < today and r["status"] != "DONE" if pd.notnull(r["planned_end"]) else False, axis=1)
                    site_ms["display_status"] = site_ms.apply(lambda r: "CRITICAL" if r["is_critical"] else r["status"], axis=1)
                    
                    color_map = {"PENDING": "#6c757d", "ONGOING": "#0d6efd", "DONE": "#28a745", "DELAYED": "#dc3545", "CRITICAL": "#ff0000"}
                    fig = px.timeline(site_ms, x_start="planned_start", x_end="planned_end", y="name", color="display_status", color_discrete_map=color_map)
                    fig.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    done = len(site_ms[site_ms["status"] == "DONE"])
                    total = len(site_ms)
                    st.progress(done/total if total > 0 else 0)

    # ===== TAB 2: TAMBAH MANUAL =====
    with tab2:
        if is_all: st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            with st.form("add_ms"):
                name = st.text_input("Nama Milestone")
                c1, c2 = st.columns(2)
                ps = c1.date_input("Rencana Mulai")
                pe = c2.date_input("Rencana Selesai")
                weight = st.number_input("Bobot %", 0.0, 100.0, 5.0)
                status = st.selectbox("Status", ["PENDING", "ONGOING", "DONE", "DELAYED"])
                if st.form_submit_button("💾 Simpan"):
                    insert_row("milestones", {
                        "id": generate_id(), "project_id": selected_site, "name": name,
                        "planned_start": ps.strftime("%Y-%m-%d"), "planned_end": pe.strftime("%Y-%m-%d"),
                        "weight": str(weight), "status": status
                    })
                    sync_milestone_to_site(selected_site)
                    st.success("Berhasil ditambah!"); st.rerun()

    # ===== TAB 3: TEMPLATE TOWER (Fitur Andalan Kamu) =====
    with tab3:
        if is_all: st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            st.subheader("🚀 Auto-Generate Template Tower")
            c1, c2 = st.columns(2)
            start_date = c1.date_input("Tanggal Mulai Project", value=datetime.now().date())
            duration = c2.number_input("Durasi rata-rata per task (hari)", 1, 30, 3)
            phases = st.multiselect("Pilih Fase:", list(TOWER_TEMPLATE.keys()), default=list(TOWER_TEMPLATE.keys()))
            
            if st.button("🚀 Generate Semua Task"):
                curr = start_date
                total_tasks = sum(len(TOWER_TEMPLATE[p]) for p in phases)
                for phase in phases:
                    for task in TOWER_TEMPLATE[phase]:
                        insert_row("milestones", {
                            "id": generate_id(),
                            "project_id": selected_site,
                            "name": f"[{phase}] {task}",
                            "planned_start": curr.strftime("%Y-%m-%d"),
                            "planned_end": (curr + timedelta(days=duration-1)).strftime("%Y-%m-%d"),
                            "weight": str(round(100/total_tasks, 1)),
                            "status": "PENDING"
                        })
                        curr += timedelta(days=duration)
                sync_milestone_to_site(selected_site)
                st.success("Template Berhasil di-generate!"); st.rerun()

    # ===== TAB 4: EDIT & DELETE =====
    with tab4:
        if is_all: st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            ms_df = read_sheet("milestones")
            site_ms = ms_df[ms_df["project_id"] == selected_site]
            if not site_ms.empty:
                sel_id = st.selectbox("Pilih Milestone:", site_ms["id"].tolist(), 
                                      format_func=lambda x: site_ms[site_ms["id"]==x]["name"].values[0])
                ms_data = site_ms[site_ms["id"] == sel_id].iloc[0]
                with st.form("edit_form"):
                    enama = st.text_input("Nama", value=ms_data["name"])
                    estatus = st.selectbox("Status", ["PENDING", "ONGOING", "DONE", "DELAYED"], 
                                           index=["PENDING", "ONGOING", "DONE", "DELAYED"].index(ms_data["status"]))
                    if st.form_submit_button("Update"):
                        update_row("milestones", sel_id, {"name": enama, "status": estatus})
                        sync_milestone_to_site(selected_site)
                        st.success("Updated!"); st.rerun()
                if st.button("🗑️ Hapus Milestone"):
                    delete_row_by_id("milestones", sel_id)
                    sync_milestone_to_site(selected_site)
                    st.warning("Terhapus!"); st.rerun()

    # ===== TAB 5: IMPORT CSV (Fitur yang Kamu Minta) =====
    with tab5:
        if is_all: st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            st.subheader("📥 Import Milestone via CSV")
            # Sediakan template download agar user tidak salah format
            template_df = pd.DataFrame({
                "name": ["Pondasi", "Erection"],
                "planned_start": [today_str(), today_str()],
                "planned_end": [today_str(), today_str()],
                "weight": [10, 15],
                "status": ["PENDING", "PENDING"]
            })
            st.download_button("📥 Download Template CSV", template_df.to_csv(index=False), "template.csv")
            
            up_file = st.file_uploader("Upload File CSV Kamu", type=["csv"])
            if up_file:
                df_import = pd.read_csv(up_file)
                st.write("Preview Data:")
                st.dataframe(df_import)
                if st.button("🚀 Konfirmasi Import"):
                    for _, r in df_import.iterrows():
                        insert_row("milestones", {
                            "id": generate_id(),
                            "project_id": selected_site,
                            "name": str(r["name"]),
                            "planned_start": str(r["planned_start"]),
                            "planned_end": str(r["planned_end"]),
                            "weight": str(r["weight"]),
                            "status": str(r["status"])
                        })
                    sync_milestone_to_site(selected_site)
                    st.success(f"Berhasil mengimport {len(df_import)} task!"); st.rerun()

if __name__ == "__main__":
    milestone_page()
