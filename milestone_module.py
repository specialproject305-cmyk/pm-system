"""
milestone.py - Milestone Monitoring Module
Production-ready dengan error handling lengkap
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from typing import Optional
from supabase_db import (
    read_sheet,
    read_sheet_no_cache,
    insert_row,
    update_row,
    delete_row_by_id,
    generate_id,
    today_str,
    safe_date_string
)

# ─────────────────────────────────────────────────────────────
# 📋 KONSTANTA
# ─────────────────────────────────────────────────────────────

TOWER_TEMPLATE = {
    "SPK TENANT": ["Hunting dan Survey", "Validation", "Sosialisasi Warga Radius", "Negosiasi Sewa Lahan", "Negosiasi IW Radius", "Pengajuan Budget IW & SA Lahan", "BAK", "Legal Proses", "Akuisisi", "RFC"],
    "APD, BoQ & Material": ["Soil test", "APD Pondasi", "APD & BoQ Tower full Design Pack", "PR Material", "PO Material", "Produksi Massal", "Material RFD", "Pengiriman Material"],
    "Implementation": ["Request SPK", "Proses Pengadaan vendor", "Kick of Meeting (KoM)", "Mobilisasi team & Bowplank", "Foundation", "Curing time", "Backfilling", "Erection", "Pondasi rack ODC", "Install ME & Grounding", "Pekerjaan Fence", "Lanscape", "PLN connect", "Install pole FO", "Laying FO", "Terminasi", "DC Power Instalation", "RFS", "RFIN submit"]
}

DELAY_REASONS = ["Tidak Ada", "Material Terlambat", "Cuaca Buruk", "Manpower Kurang", "Vendor Terlambat", "Izin/Tanah", "Desain Berubah", "Force Majeure", "Lainnya"]

# ─────────────────────────────────────────────────────────────
# 🔄 HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def sync_milestone_to_site(site_id: str) -> bool:
    """
    Hitung ulang progress dan status site berdasarkan milestone.
    Returns: True jika sukses update
    """
    try:
        # Baca data milestone terbaru (no cache untuk data real-time)
        ms_df = read_sheet_no_cache("milestones")
        
        if ms_df.empty or "project_id" not in ms_df.columns:
            return False
        
        # Filter milestone untuk site ini
        site_ms = ms_df[ms_df["project_id"] == site_id].copy()
        if site_ms.empty:
            return False
        
        # Hitung weighted progress
        site_ms["weight"] = pd.to_numeric(site_ms["weight"], errors="coerce").fillna(0)
        total_weight = site_ms["weight"].sum()
        done_weight = site_ms[site_ms["status"] == "DONE"]["weight"].sum()
        
        progress = round((done_weight / total_weight) * 100, 1) if total_weight > 0 else 0
        
        # Hitung jumlah delayed
        delayed_count = len(site_ms[site_ms["status"] == "DELAYED"])
        
        # Tentukan status
        if delayed_count > 3:
            status = "CRITICAL"
        elif delayed_count > 0:
            status = "DELAYED"
        else:
            status = "ON_TRACK"
        
        # Update data project
        success = update_row("projects", site_id, {
            "progress": str(progress),
            "status": status
        })
        
        if success:
            st.toast(f"📊 Progress site updated: {progress}% ({status})", icon="✅")
        
        return success
        
    except Exception as e:
        st.error(f"❌ Gagal sync milestone: {str(e)[:100]}")
        return False


def check_critical_date(row: pd.Series, today: datetime.date) -> bool:
    """
    Cek apakah milestone critical (lewat deadline tapi belum DONE).
    Fungsi terpisah untuk menghindari lambda error.
    """
    try:
        if pd.isnull(row.get("planned_end")):
            return False
        
        end_date = row["planned_end"]
        # Handle jika end_date adalah string
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date).date()
        elif hasattr(end_date, 'date'):
            end_date = end_date.date()
        
        return end_date < today and row.get("status") != "DONE"
    
    except Exception:
        return False

# ─────────────────────────────────────────────────────────────
# 📊 MAIN PAGE FUNCTION
# ─────────────────────────────────────────────────────────────

def milestone_page():
    """Halaman utama Milestone Monitoring."""
    st.title("🧱 Milestone Monitoring")
    
    # ── Load Data Projects ──
    sites_df = read_sheet("projects")
    
    if sites_df.empty:
        st.warning("⚠️ Tambahkan site dulu di menu Project Tracker!")
        return
    
    # ── Sidebar: Filter Site ──
    st.sidebar.header("🔍 Filter")
    
    site_options = ["ALL SITE"] + sites_df["id"].tolist()
    selected_site = st.sidebar.selectbox(
        "Pilih Site:",
        site_options,
        format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE"
        else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}"
    )
    
    is_all = (selected_site == "ALL SITE")
    
    # ── Tabs ──
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Gantt", "➕ Tambah", "🚀 Template", "✏️ Edit", "📥 Import"])
    
    # ════════════════════════════════════════════════════════
    # TAB 1: GANTT CHART
    # ════════════════════════════════════════════════════════
    with tab1:
        ms_df = read_sheet("milestones")
        
        if ms_df.empty:
            st.info("ℹ️ Belum ada data milestone.")
        else:
            # Konversi tanggal
            ms_df["planned_start"] = pd.to_datetime(ms_df["planned_start"], errors="coerce")
            ms_df["planned_end"] = pd.to_datetime(ms_df["planned_end"], errors="coerce")
            
            if is_all:
                # Tampilan ALL SITE
                st.subheader("📊 Gantt Chart - ALL SITE")
                
                # Group by milestone name
                grouped = ms_df.groupby("name").agg(
                    start=("planned_start", "min"),
                    end=("planned_end", "max"),
                    total_sites=("project_id", "nunique"),
                    done_count=("status", lambda x: (x == "DONE").sum()),
                    delayed_count=("status", lambda x: (x == "DELAYED").sum())
                ).reset_index()
                
                grouped = grouped.sort_values("start")
                
                # Tentukan status agregat
                def get_aggregate_status(r):
                    if r["delayed_count"] > 0:
                        return "DELAYED"
                    elif r["done_count"] == r["total_sites"]:
                        return "DONE"
                    elif r["done_count"] > 0:
                        return "ONGOING"
                    return "PENDING"
                
                grouped["status"] = grouped.apply(get_aggregate_status, axis=1)
                
                # Plot Gantt
                color_map = {
                    "PENDING": "#6c757d",
                    "ONGOING": "#0d6efd",
                    "DONE": "#28a745",
                    "DELAYED": "#dc3545"
                }
                
                fig = px.timeline(
                    grouped,
                    x_start="start",
                    x_end="end",
                    y="name",
                    color="status",
                    color_discrete_map=color_map,
                    hover_data=["total_sites", "done_count", "delayed_count"]
                )
                fig.update_yaxes(autorange="reversed")
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                # Tampilan single site
                site_ms = ms_df[ms_df["project_id"] == selected_site].copy()
                
                if site_ms.empty:
                    st.info("ℹ️ Site ini belum punya milestone.")
                else:
                    site_ms = site_ms.sort_values("planned_start")
                    today = datetime.now().date()
                    
                    # Tandai critical milestones
                    site_ms["is_critical"] = site_ms.apply(
                        lambda r: check_critical_date(r, today), axis=1
                    )
                    site_ms["display_status"] = site_ms.apply(
                        lambda r: "CRITICAL" if r["is_critical"] else r["status"], axis=1
                    )
                    
                    # Plot Gantt
                    color_map = {
                        "PENDING": "#6c757d",
                        "ONGOING": "#0d6efd",
                        "DONE": "#28a745",
                        "DELAYED": "#dc3545",
                        "CRITICAL": "#ff0000"
                    }
                    
                    fig = px.timeline(
                        site_ms,
                        x_start="planned_start",
                        x_end="planned_end",
                        y="name",
                        color="display_status",
                        color_discrete_map=color_map,
                        hover_data=["status", "weight"]
                    )
                    fig.update_yaxes(autorange="reversed")
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Progress bar
                    done = len(site_ms[site_ms["status"] == "DONE"])
                    total = len(site_ms)
                    progress_pct = done / total if total > 0 else 0
                    
                    st.metric("Progress", f"{done}/{total} tasks ({progress_pct:.1%})")
                    st.progress(progress_pct)
                    
                    # Summary stats
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("DONE", len(site_ms[site_ms["status"]=="DONE"]))
                    with col2:
                        st.metric("ONGOING", len(site_ms[site_ms["status"]=="ONGOING"]))
                    with col3:
                        st.metric("DELAYED", len(site_ms[site_ms["status"]=="DELAYED"]))
                    with col4:
                        st.metric("CRITICAL", len(site_ms[site_ms["is_critical"]==True]))
    
    # ════════════════════════════════════════════════════════
    # TAB 2: TAMBAH MANUAL
    # ════════════════════════════════════════════════════════
    with tab2:
        if is_all:
            st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            with st.form("add_milestone_form", clear_on_submit=False):
                st.subheader("➕ Tambah Milestone Baru")
                
                name = st.text_input("Nama Milestone *", placeholder="Contoh: Foundation")
                
                col1, col2 = st.columns(2)
                with col1:
                    ps = st.date_input("Rencana Mulai *", value=datetime.now())
                with col2:
                    pe = st.date_input("Rencana Selesai *", value=datetime.now() + timedelta(days=7))
                
                weight = st.number_input("Bobot (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.5)
                
                status = st.selectbox(
                    "Status",
                    ["PENDING", "ONGOING", "DONE", "DELAYED"],
                    index=0
                )
                
                reason = st.text_input("Alasan Delay (jika ada)", placeholder="Opsional")
                
                submitted = st.form_submit_button("💾 Simpan Milestone", type="primary", use_container_width=True)
                
                if submitted:
                    # Validasi
                    if not name or not name.strip():
                        st.error("❌ Nama milestone wajib diisi!")
                    elif ps > pe:
                        st.error("❌ Tanggal mulai tidak boleh lebih dari tanggal selesai!")
                    else:
                        # Insert ke database
                        new_id = insert_row("milestones", {
                            "id": generate_id(),
                            "project_id": selected_site,
                            "name": name.strip(),
                            "planned_start": safe_date_string(ps),
                            "planned_end": safe_date_string(pe),
                            "weight": str(weight),
                            "status": status,
                            "delay_reason": reason.strip() if reason else "Tidak Ada"
                        })
                        
                        if new_id:
                            # Sync progress site
                            sync_milestone_to_site(selected_site)
                            st.success(f"✅ Milestone berhasil ditambahkan!")
                            st.rerun()
                        else:
                            st.error("❌ Gagal menyimpan. Cek konsol untuk detail.")
    
    # ════════════════════════════════════════════════════════
    # TAB 3: TEMPLATE TOWER
    # ════════════════════════════════════════════════════════
    with tab3:
        if is_all:
            st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            st.subheader("🚀 Auto-Generate Template Tower")
            st.markdown("Generate milestone otomatis berdasarkan template standar proyek tower.")
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Tanggal Mulai Project",
                    value=datetime.now().date()
                )
            with col2:
                duration = st.number_input(
                    "Durasi rata-rata per task (hari)",
                    min_value=1,
                    max_value=30,
                    value=3,
                    step=1
                )
            
            phases = st.multiselect(
                "Pilih Fase yang Ingin Digenerate:",
                list(TOWER_TEMPLATE.keys()),
                default=list(TOWER_TEMPLATE.keys())
            )
            
            if st.button("🚀 Generate Semua Task", type="primary", use_container_width=True):
                if not phases:
                    st.warning("⚠️ Pilih minimal satu fase!")
                else:
                    # Hitung total tasks
                    total_tasks = sum(len(TOWER_TEMPLATE[p]) for p in phases)
                    
                    with st.spinner(f"🔄 Menggenerate {total_tasks} milestone..."):
                        curr_date = start_date
                        success_count = 0
                        
                        for phase in phases:
                            for task in TOWER_TEMPLATE[phase]:
                                # Hitung bobot per task
                                task_weight = round(100 / total_tasks, 1)
                                
                                # Insert milestone
                                new_id = insert_row("milestones", {
                                    "id": generate_id(),
                                    "project_id": selected_site,
                                    "name": f"[{phase}] {task}",
                                    "planned_start": safe_date_string(curr_date),
                                    "planned_end": safe_date_string(curr_date + timedelta(days=duration-1)),
                                    "weight": str(task_weight),
                                    "status": "PENDING",
                                    "delay_reason": "Tidak Ada"
                                })
                                
                                if new_id:
                                    success_count += 1
                                
                                # Increment tanggal untuk task berikutnya
                                curr_date += timedelta(days=duration)
                        
                        # Sync progress
                        sync_milestone_to_site(selected_site)
                        
                        if success_count > 0:
                            st.success(f"✅ Berhasil generate {success_count} milestone!")
                            st.rerun()
                        else:
                            st.error("❌ Gagal generate milestone.")
    
    # ════════════════════════════════════════════════════════
    # TAB 4: EDIT & DELETE
    # ════════════════════════════════════════════════════════
    with tab4:
        if is_all:
            st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            st.subheader("✏️ Edit / Hapus Milestone")
            
            ms_df = read_sheet("milestones")
            site_ms = ms_df[ms_df["project_id"] == selected_site] if not ms_df.empty else pd.DataFrame()
            
            if site_ms.empty:
                st.info("ℹ️ Belum ada milestone untuk site ini.")
            else:
                # Pilih milestone
                sel_id = st.selectbox(
                    "Pilih Milestone:",
                    site_ms["id"].tolist(),
                    format_func=lambda x: site_ms[site_ms["id"]==x]["name"].values[0]
                )
                
                # Ambil data milestone yang dipilih
                ms_data = site_ms[site_ms["id"] == sel_id].iloc[0]
                
                # Form edit
                with st.form("edit_milestone_form"):
                    st.markdown("### Edit Data")
                    
                    ename = st.text_input("Nama", value=ms_data.get("name", ""))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        estatus = st.selectbox(
                            "Status",
                            ["PENDING", "ONGOING", "DONE", "DELAYED"],
                            index=["PENDING", "ONGOING", "DONE", "DELAYED"].index(ms_data.get("status", "PENDING"))
                        )
                    with col2:
                        eweight = st.number_input(
                            "Bobot (%)",
                            value=float(ms_data.get("weight", 5)),
                            min_value=0.0,
                            max_value=100.0
                        )
                    
                    ereason = st.text_input(
                        "Alasan Delay",
                        value=ms_data.get("delay_reason", "Tidak Ada")
                    )
                    
                    submitted = st.form_submit_button("💾 Update Data", type="primary")
                    
                    if submitted:
                        success = update_row("milestones", sel_id, {
                            "name": ename.strip(),
                            "status": estatus,
                            "weight": str(eweight),
                            "delay_reason": ereason.strip()
                        })
                        
                        if success:
                            sync_milestone_to_site(selected_site)
                            st.success("✅ Data berhasil diupdate!")
                            st.rerun()
                        else:
                            st.error("❌ Gagal update data.")
                
                # Tombol hapus
                st.divider()
                st.markdown("### 🗑️ Zona Berbahaya")
                
                if st.button("🗑️ Hapus Milestone Ini", type="secondary"):
                    st.warning("⚠️ Apakah Anda yakin? Tindakan ini tidak bisa dibatalkan.")
                    
                    if st.button("✅ Ya, Hapus Sekarang!", type="primary"):
                        success = delete_row_by_id("milestones", sel_id)
                        
                        if success:
                            sync_milestone_to_site(selected_site)
                            st.success("✅ Milestone berhasil dihapus!")
                            st.rerun()
                        else:
                            st.error("❌ Gagal menghapus milestone.")
    
    # ════════════════════════════════════════════════════════
    # TAB 5: IMPORT CSV
    # ════════════════════════════════════════════════════════
    with tab5:
        if is_all:
            st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            st.subheader("📥 Import Milestone dari CSV")
            st.markdown("Upload file CSV dengan format yang sesuai.")
            
            # Download template
            template_df = pd.DataFrame({
                "name": ["Pondasi", "Erection", "Install ME"],
                "planned_start": [today_str(), today_str(), today_str()],
                "planned_end": [today_str(), today_str(), today_str()],
                "weight": [10.0, 15.0, 20.0],
                "status": ["PENDING", "PENDING", "PENDING"],
                "delay_reason": ["Tidak Ada", "Tidak Ada", "Tidak Ada"]
            })
            
            csv_template = template_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Template CSV",
                data=csv_template,
                file_name="template_milestone.csv",
                mime="text/csv"
            )
            
            st.divider()
            
            # Upload file
            uploaded_file = st.file_uploader("📤 Upload File CSV", type=["csv"])
            
            if uploaded_file:
                try:
                    df_import = pd.read_csv(uploaded_file)
                    
                    st.markdown("### Preview Data")
                    st.dataframe(df_import.head(), use_container_width=True)
                    
                    # Validasi kolom
                    required_cols = ["name", "planned_start", "planned_end", "weight", "status"]
                    missing_cols = [col for col in required_cols if col not in df_import.columns]
                    
                    if missing_cols:
                        st.error(f"❌ Kolom wajib tidak ada: {', '.join(missing_cols)}")
                    else:
                        st.info(f"ℹ️ Ditemukan {len(df_import)} baris data")
                        
                        if st.button("🚀 Konfirmasi Import", type="primary"):
                            success_count = 0
                            error_count = 0
                            
                            with st.spinner("🔄 Mengimport data..."):
                                for idx, row in df_import.iterrows():
                                    try:
                                        new_id = insert_row("milestones", {
                                            "id": generate_id(),
                                            "project_id": selected_site,
                                            "name": str(row["name"]),
                                            "planned_start": safe_date_string(row["planned_start"]),
                                            "planned_end": safe_date_string(row["planned_end"]),
                                            "weight": str(row["weight"]),
                                            "status": str(row["status"]),
                                            "delay_reason": str(row.get("delay_reason", "Tidak Ada"))
                                        })
                                        
                                        if new_id:
                                            success_count += 1
                                        else:
                                            error_count += 1
                                    
                                    except Exception as e:
                                        error_count += 1
                                        st.error(f"Baris {idx+1} error: {str(e)[:50]}")
                            
                            # Sync progress
                            sync_milestone_to_site(selected_site)
                            
                            # Summary
                            st.success(f"✅ Import selesai!")
                            st.metric("Berhasil", success_count)
                            st.metric("Gagal", error_count)
                            
                            if success_count > 0:
                                st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Gagal baca file CSV: {str(e)}")

# ─────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    milestone_page()
