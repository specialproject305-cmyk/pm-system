import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from supabase_db import (
    read_sheet,
    insert_row,
    update_row,
    delete_row_by_id,
    generate_id,
    today_str,
    safe_date_string
)

# ─────────────────────────────────────────────────────────────
# 📋 TOWER TEMPLATE DENGAN SLA & ASSIGNED TO
# ─────────────────────────────────────────────────────────────

TOWER_TEMPLATE = {
    "SPK TENANT": [
        {"task": "Hunting dan Survey", "assigned": "Sitac", "sla": 3},
        {"task": "Validation", "assigned": "Sitac", "sla": 3},
        {"task": "Sosialisasi Warga Radius", "assigned": "Sitac", "sla": 6},
        {"task": "Negosiasi Sewa Lahan", "assigned": "Sitac", "sla": 3},
        {"task": "Negosiasi IW Radius", "assigned": "Sitac", "sla": 3},
        {"task": "Pengajuan Budget IW & SA Lahan", "assigned": "Sitac", "sla": 14},
        {"task": "BAK", "assigned": "Sitac", "sla": 1},
        {"task": "Legal Proses", "assigned": "Legal", "sla": 6},
        {"task": "Akuisisi", "assigned": "Sitac", "sla": 1},
        {"task": "RFC", "assigned": "Sitac", "sla": 1}
    ],
    "APD, BoQ & Material": [
        {"task": "Soil test", "assigned": "Engineering", "sla": 3},
        {"task": "APD Pondasi", "assigned": "Engineering", "sla": 7},
        {"task": "APD & BoQ Tower full Design Pack", "assigned": "Engineering", "sla": 3},
        {"task": "PR Material", "assigned": "Engineering", "sla": 3},
        {"task": "PO Material", "assigned": "Procurement", "sla": 5},
        {"task": "Produksi Massal", "assigned": "Engineering", "sla": 28},
        {"task": "Material RFD", "assigned": "Engineering", "sla": 1},
        {"task": "Pengiriman Material", "assigned": "Engineering", "sla": 4}
    ],
    "Implementation": [
        {"task": "Request SPK", "assigned": "Project", "sla": 1},
        {"task": "Proses Pengadaan vendor", "assigned": "Vendor Management", "sla": 3},
        {"task": "Kick of Meeting (KoM)", "assigned": "Project", "sla": 1},
        {"task": "Mobilisasi team & Bowplank", "assigned": "Project", "sla": 2},
        {"task": "Foundation (galian sd. Pengecoran)", "assigned": "Project", "sla": 7},
        {"task": "Curing time", "assigned": "Project", "sla": 7},
        {"task": "Erection", "assigned": "Project", "sla": 3},
        {"task": "Install ME & Grounding", "assigned": "Project", "sla": 2},
        {"task": "PLN connect process", "assigned": "Project", "sla": 21},
        {"task": "Install pole FO", "assigned": "Project", "sla": 2},
        {"task": "Laying FO", "assigned": "Project", "sla": 3},
        {"task": "Terminasi", "assigned": "Project", "sla": 1},
        {"task": "DC Power Instalation", "assigned": "Project", "sla": 2},
        {"task": "RFS", "assigned": "Project", "sla": 1},
        {"task": "RFIN submit", "assigned": "Project", "sla": 1}
    ]
}

# Total SLA per kategori
CATEGORY_SLA = {
    "SPK TENANT": 41,
    "APD, BoQ & Material": 54,
    "Implementation": 57
}

DELAY_REASONS = ["Tidak Ada", "Material Terlambat", "Cuaca Buruk", "Manpower Kurang", "Vendor Terlambat", "Izin/Tanah", "Desain Berubah", "Force Majeure", "Lainnya"]

# ─────────────────────────────────────────────────────────────
# 🔄 HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
# 🔄 AUTO-SCHEDULE SHIFTING HELPER
# ─────────────────────────────────────────────────────────────
def cascade_schedule_shift(site_id, new_planned_end, delay_days):
    """Otomatis geser jadwal task berikutnya jika ada keterlambatan."""
    if delay_days <= 0 or not new_planned_end:
        return 0
    
    try:
        ms_df = read_sheet("milestones")
        if ms_df.empty: 
            return 0
            
        # Konversi tanggal
        ms_df['ps_dt'] = pd.to_datetime(ms_df['planned_start'], errors='coerce')
        ms_df['pe_dt'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
        ref_date = pd.to_datetime(new_planned_end)
        
        # Filter: task di site yang sama, dijadwalkan SETELAH task yang delay, dan belum DONE
        future_tasks = ms_df[
            (ms_df['project_id'] == site_id) & 
            (ms_df['ps_dt'] > ref_date) & 
            (ms_df['status'] != 'DONE')
        ]
        
        shifted_count = 0
        for _, t in future_tasks.iterrows():
            new_ps = t['ps_dt'] + timedelta(days=delay_days)
            new_pe = t['pe_dt'] + timedelta(days=delay_days)
            
            update_row("milestones", t['id'], {
                "planned_start": safe_date_string(new_ps),
                "planned_end": safe_date_string(new_pe)
            })
            shifted_count += 1
            
        return shifted_count
    except Exception as e:
        st.warning(f"⚠️ Gagal shift jadwal otomatis: {e}")
        return 0

def sync_milestone_to_site(site_id):
    """Hitung ulang progress dan status site berdasarkan milestone."""
    try:
        ms_df = read_sheet("milestones")
        if ms_df.empty or "project_id" not in ms_df.columns: 
            return
        
        site_ms = ms_df[ms_df["project_id"]==site_id].copy()
        if site_ms.empty: 
            return
        
        site_ms["weight"] = pd.to_numeric(site_ms["weight"], errors="coerce").fillna(0)
        total_weight = site_ms["weight"].sum()
        done_weight = site_ms[site_ms["status"]=="DONE"]["weight"].sum()
        
        progress = round((done_weight/total_weight)*100, 1) if total_weight > 0 else 0
        delayed = len(site_ms[site_ms["status"]=="DELAYED"])
        
        status = "CRITICAL" if delayed > 3 else ("DELAYED" if delayed > 0 else "ON_TRACK")
        update_row("projects", site_id, {"progress": str(progress), "status": status})
    except Exception as e:
        st.error(f"❌ Gagal sync: {str(e)[:50]}")

def check_critical(row, today):
    """Cek apakah milestone critical."""
    try:
        if pd.isnull(row.get("planned_end")):
            return False
        end_date = row["planned_end"]
        if hasattr(end_date, 'date'):
            end_date = end_date.date()
        return end_date < today and row.get("status") != "DONE"
    except:
        return False

# ─────────────────────────────────────────────────────────────
# 📊 MAIN PAGE FUNCTION
# ─────────────────────────────────────────────────────────────

def milestone_page():
    st.title("🧱 Milestone Monitoring")
    
    sites_df = read_sheet("projects")
    if sites_df.empty: 
        st.warning("⚠️ Tambahkan site dulu di menu Project Tracker!")
        return
    
    # Sidebar Filter Site
    site_options = ["ALL SITE"] + sites_df["id"].tolist()
    selected_site = st.selectbox(
        "Pilih Site:", 
        site_options,
        format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE" 
        else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}"
    )
    
    is_all = (selected_site == "ALL SITE")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Gantt", "➕ Tambah", "🚀 Template", "✏️ Edit", "📥 Import"])
    
    # ════════════════════════════════════════════════════════
    # TAB 1: GANTT CHART
    # ════════════════════════════════════════════════════════
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
                    site_ms["is_critical"] = site_ms.apply(lambda r: check_critical(r, today), axis=1)
                    site_ms["display_status"] = site_ms.apply(lambda r: "CRITICAL" if r["is_critical"] else r["status"], axis=1)
                    
                    color_map = {"PENDING": "#6c757d", "ONGOING": "#0d6efd", "DONE": "#28a745", "DELAYED": "#dc3545", "CRITICAL": "#ff0000"}
                    fig = px.timeline(site_ms, x_start="planned_start", x_end="planned_end", y="name", color="display_status", color_discrete_map=color_map)
                    fig.update_yaxes(autorange="reversed")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    done = len(site_ms[site_ms["status"] == "DONE"])
                    total = len(site_ms)
                    st.progress(done/total if total > 0 else 0)

    # ════════════════════════════════════════════════════════
    # TAB 2: TAMBAH MANUAL (dengan Actual Date)
    # ════════════════════════════════════════════════════════
    with tab2:
        if is_all: 
            st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            with st.form("add_ms"):
                st.subheader("➕ Tambah Milestone Baru")
                
                name = st.text_input("Nama Milestone")
                
                col1, col2 = st.columns(2)
                with col1:
                    ps = st.date_input("Rencana Mulai", value=datetime.now())
                    actual_s = st.date_input("Actual Start (Opsional)", value=None)
                with col2:
                    pe = st.date_input("Rencana Selesai", value=datetime.now() + timedelta(days=7))
                    actual_e = st.date_input("Actual End (Opsional)", value=None)
                
                c3, c4 = st.columns(2)
                with c3:
                    assigned = st.text_input("Assigned To", placeholder="Contoh: Sitac, Engineering")
                with c4:
                    weight = st.number_input("Bobot %", 0.0, 100.0, 5.0)
                
                status = st.selectbox("Status", ["PENDING", "ONGOING", "DONE", "DELAYED"])
                delay_reason = st.text_input("Alasan Delay (jika ada)", placeholder="Tidak Ada")
                
                if st.form_submit_button("💾 Simpan"):
                    if not name:
                        st.error("Nama milestone wajib diisi!")
                    else:
                        new_id = insert_row("milestones", {
                            "id": generate_id(),
                            "project_id": selected_site,
                            "name": name,
                            "planned_start": safe_date_string(ps),
                            "planned_end": safe_date_string(pe),
                            "actual_start": safe_date_string(actual_s) if actual_s else None,
                            "actual_end": safe_date_string(actual_e) if actual_e else None,
                            "assigned_to": assigned,
                            "weight": str(weight),
                            "status": status,
                            "delay_reason": delay_reason if delay_reason else "Tidak Ada"
                        })
                        if new_id:
                            sync_milestone_to_site(selected_site)
                            st.success("Berhasil ditambah!")
                            st.rerun()
                        else:
                            st.error("Gagal menyimpan!")

    # ════════════════════════════════════════════════════════
    # TAB 3: TEMPLATE OTOMATIS BERDASARKAN SLA
    # ════════════════════════════════════════════════════════
    with tab3:
        if is_all: 
            st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            st.subheader("🚀 Auto-Generate Template Tower dengan SLA")
            st.markdown("**Total Durasi:** SPK TENANT (41 hari) + APD & Material (54 hari) + Implementation (57 hari) = **152 hari**")
            
            c1, c2 = st.columns(2)
            with c1:
                start_date = st.date_input("Tanggal Mulai Project", value=datetime.now().date())
            with c2:
                show_preview = st.checkbox("📋 Tampilkan Preview", value=True)
            
            phases = st.multiselect(
                "Pilih Fase:",
                list(TOWER_TEMPLATE.keys()),
                default=list(TOWER_TEMPLATE.keys()),
                help="Pilih fase yang ingin digenerate"
            )
            
            if show_preview and phases:
                st.markdown("### 📊 Preview Task & SLA")
                preview_data = []
                for phase in phases:
                    for item in TOWER_TEMPLATE[phase]:
                        preview_data.append({
                            "Fase": phase,
                            "Task": item["task"],
                            "Assigned To": item["assigned"],
                            "SLA (Hari)": item["sla"]
                        })
                
                preview_df = pd.DataFrame(preview_data)
                st.dataframe(preview_df, use_container_width=True)
                
                total_sla = preview_df["SLA (Hari)"].sum()
                st.info(f"📅 **Total Durasi:** {total_sla} hari kerja")
            
            if st.button("🚀 Generate Semua Task Otomatis", type="primary"):
                if not phases:
                    st.warning("⚠️ Pilih minimal satu fase!")
                else:
                    curr_date = start_date
                    success_count = 0
                    
                    with st.spinner(f"🔄 Menggenerate milestone berdasarkan SLA..."):
                        for phase in phases:
                            for item in TOWER_TEMPLATE[phase]:
                                sla_days = item["sla"]
                                end_date = curr_date + timedelta(days=sla_days-1)
                                
                                # Hitung bobot berdasarkan SLA
                                total_sla_all = sum(item["sla"] for p in phases for item in TOWER_TEMPLATE[p])
                                weight = round((item["sla"] / total_sla_all) * 100, 1)
                                
                                new_id = insert_row("milestones", {
                                    "id": generate_id(),
                                    "project_id": selected_site,
                                    "name": f"[{phase}] {item['task']}",
                                    "planned_start": safe_date_string(curr_date),
                                    "planned_end": safe_date_string(end_date),
                                    "actual_start": None,
                                    "actual_end": None,
                                    "assigned_to": item["assigned"],
                                    "weight": str(weight),
                                    "status": "PENDING",
                                    "delay_reason": "Tidak Ada",
                                    "sla_days": str(sla_days)
                                })
                                
                                if new_id:
                                    success_count += 1
                                
                                # Tanggal mulai task berikutnya = hari setelah task ini selesai
                                curr_date = end_date + timedelta(days=1)
                        
                        sync_milestone_to_site(selected_site)
                        if success_count > 0:
                            st.success(f"✅ Berhasil generate {success_count} milestone dengan perhitungan SLA!")
                            st.rerun()

    # ════════════════════════════════════════════════════════
    # TAB 4: EDIT (dengan Actual Start & End)
    # ════════════════════════════════════════════════════════
    with tab4:
        if is_all: 
            st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            st.subheader("✏️ Edit Milestone")
            
            ms_df = read_sheet("milestones")
            site_ms = ms_df[ms_df["project_id"] == selected_site] if not ms_df.empty else pd.DataFrame()
            
            if not site_ms.empty:
                sel_id = st.selectbox(
                    "Pilih Milestone:",
                    site_ms["id"].tolist(),
                    format_func=lambda x: site_ms[site_ms["id"]==x]["name"].values[0]
                )
                
                ms_data = site_ms[site_ms["id"] == sel_id].iloc[0]
                
                with st.form("edit_form"):
                    st.markdown("### 📝 Edit Data Milestone")
                    
                    ename = st.text_input("Nama", value=ms_data.get("name", ""))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        estatus = st.selectbox(
                            "Status",
                            ["PENDING", "ONGOING", "DONE", "DELAYED"],
                            index=["PENDING", "ONGOING", "DONE", "DELAYED"].index(ms_data.get("status", "PENDING"))
                        )
                        eassigned = st.text_input(
                            "Assigned To",
                            value=ms_data.get("assigned_to", "")
                        )
                    with col2:
                        eweight = st.number_input(
                            "Bobot (%)",
                            value=float(ms_data.get("weight", 5)) if ms_data.get("weight") else 5.0,
                            min_value=0.0,
                            max_value=100.0
                        )
                        esla = st.text_input(
                            "SLA (Hari)",
                            value=ms_data.get("sla_days", "")
                        )
                    
                    st.markdown("---")
                    st.markdown("### 📅 Timeline")
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        # Planned dates
                        try:
                            ps_default = pd.to_datetime(ms_data.get("planned_start")).date() if pd.notna(ms_data.get("planned_start")) else datetime.now().date()
                        except:
                            ps_default = datetime.now().date()
                        
                        try:
                            pe_default = pd.to_datetime(ms_data.get("planned_end")).date() if pd.notna(ms_data.get("planned_end")) else datetime.now().date() + timedelta(days=7)
                        except:
                            pe_default = datetime.now().date() + timedelta(days=7)
                        
                        eplanned_start = st.date_input("Planned Start", value=ps_default)
                        eplanned_end = st.date_input("Planned End", value=pe_default)
                    
                    with col4:
                        # Actual dates
                        try:
                            as_default = pd.to_datetime(ms_data.get("actual_start")).date() if pd.notna(ms_data.get("actual_start")) else None
                        except:
                            as_default = None
                        
                        try:
                            ae_default = pd.to_datetime(ms_data.get("actual_end")).date() if pd.notna(ms_data.get("actual_end")) else None
                        except:
                            ae_default = None
                        
                        eactual_start = st.date_input("Actual Start (Opsional)", value=as_default)
                        eactual_end = st.date_input("Actual End (Opsional)", value=ae_default)
                    
                    st.markdown("---")
                    edelay_reason = st.text_input(
                        "Alasan Delay",
                        value=ms_data.get("delay_reason", "Tidak Ada")
                    )
                    
                    submitted = st.form_submit_button("💾 Update Data", type="primary")
                    
                    # Ganti bagian if submitted: di TAB 4 dengan kode ini:

                    if submitted:
                        try:
                            # Siapkan data update
                            update_data = {
                                "name": ename,
                                "status": estatus,
                                "weight": str(eweight),
                                "assigned_to": eassigned,
                                "sla_days": esla,
                                "planned_start": safe_date_string(eplanned_start),
                                "planned_end": safe_date_string(eplanned_end),
                                "actual_start": safe_date_string(eactual_start) if eactual_start else None,
                                "actual_end": safe_date_string(eactual_end) if eactual_end else None,
                                "delay_reason": edelay_reason
                            }
                            
                            # Eksekusi update
                            success = update_row("milestones", sel_id, update_data)
                            
                            if success:
                                # ✅ Tampilkan notifikasi ganda (toast + success) agar lebih terlihat
                                st.toast("✅ Milestone berhasil diupdate!", icon="🎉")
                                st.success("✅ Data berhasil diupdate!")
                                
                                # Auto-sync progress site
                                sync_milestone_to_site(selected_site)
                                
                                # Clear cache agar data fresh
                                st.cache_data.clear()
                                
                                # Beri jeda kecil agar user lihat notifikasi sebelum rerun
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ Gagal update: Database tidak merespon")
                                st.info("💡 Cek koneksi internet atau permission database")
                                
                        except Exception as e:
                            st.error(f"💥 Error: {str(e)[:100]}")
                            st.exception(e)  # Tampilkan detail error untuk debugging
                
                # Tombol hapus
                st.divider()
                if st.button("🗑️ Hapus Milestone", type="secondary"):
                    if st.checkbox("✅ Ya, saya yakin ingin menghapus"):
                        success = delete_row_by_id("milestones", sel_id)
                        if success:
                            sync_milestone_to_site(selected_site)
                            st.warning("Milestone dihapus!")
                            st.rerun()

    # ════════════════════════════════════════════════════════
    # TAB 5: IMPORT CSV
    # ════════════════════════════════════════════════════════
    with tab5:
        if is_all: 
            st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            st.subheader("📥 Import Milestone via CSV")
            
            template_df = pd.DataFrame({
                "name": ["Pondasi", "Erection"],
                "planned_start": [today_str(), today_str()],
                "planned_end": [today_str(), today_str()],
                "actual_start": ["", ""],
                "actual_end": ["", ""],
                "assigned_to": ["Engineering", "Project"],
                "weight": [10, 15],
                "status": ["PENDING", "PENDING"],
                "delay_reason": ["Tidak Ada", "Tidak Ada"]
            })
            
            st.download_button(
                "📥 Download Template CSV",
                template_df.to_csv(index=False),
                "template_milestone.csv",
                "text/csv"
            )
            
            up_file = st.file_uploader("Upload File CSV", type=["csv"])
            if up_file:
                df_import = pd.read_csv(up_file)
                st.write("Preview Data:")
                st.dataframe(df_import)
                
                if st.button("🚀 Konfirmasi Import"):
                    success_count = 0
                    for _, r in df_import.iterrows():
                        new_id = insert_row("milestones", {
                            "id": generate_id(),
                            "project_id": selected_site,
                            "name": str(r["name"]),
                            "planned_start": safe_date_string(r.get("planned_start", today_str())),
                            "planned_end": safe_date_string(r.get("planned_end", today_str())),
                            "actual_start": safe_date_string(r.get("actual_start")) if r.get("actual_start") else None,
                            "actual_end": safe_date_string(r.get("actual_end")) if r.get("actual_end") else None,
                            "assigned_to": str(r.get("assigned_to", "")),
                            "weight": str(r.get("weight", 5)),
                            "status": str(r.get("status", "PENDING")),
                            "delay_reason": str(r.get("delay_reason", "Tidak Ada"))
                        })
                        if new_id:
                            success_count += 1
                    
                    sync_milestone_to_site(selected_site)
                    if success_count > 0:
                        st.success(f"Berhasil import {success_count} task!")
                        st.rerun()

if __name__ == "__main__":
    milestone_page()
