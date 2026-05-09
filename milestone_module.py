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
    today_str
)

TOWER_TEMPLATE = {
    "SPK TENANT": ["Hunting dan Survey","Validation","Sosialisasi Warga Radius","Negosiasi Sewa Lahan","Negosiasi IW Radius","Pengajuan Budget IW & SA Lahan","BAK","Legal Proses","Akuisisi","RFC"],
    "APD, BoQ & Material": ["Soil test","APD Pondasi","APD & BoQ Tower full Design Pack","PR Material","PO Material","Produksi Massal","Material RFD","Pengiriman Material"],
    "Implementation": ["Request SPK","Proses Pengadaan vendor","Kick of Meeting (KoM)","Mobilisasi team & Bowplank","Foundation","Curing time","Backfilling","Erection","Pondasi rack ODC","Install ME & Grounding","Pekerjaan Fence","Lanscape","PLN connect","Install pole FO","Laying FO","Terminasi","DC Power Instalation","RFS","RFIN submit"]
}

def sync_milestone_to_site(site_id):
    """Sync progress & status dari milestone ke site"""
    ms_df = read_sheet("milestones")
    if ms_df.empty or "project_id" not in ms_df.columns:
        return
    site_ms = ms_df[ms_df["project_id"] == site_id].copy()
    if site_ms.empty:
        return
    site_ms["weight"] = pd.to_numeric(site_ms["weight"], errors="coerce").fillna(0)
    total_weight = site_ms["weight"].sum()
    done_weight = site_ms[site_ms["status"] == "DONE"]["weight"].sum()
    progress = round((done_weight / total_weight) * 100, 1) if total_weight > 0 else 0
    delayed = len(site_ms[site_ms["status"] == "DELAYED"])
    status = "CRITICAL" if delayed > 3 else ("DELAYED" if delayed > 0 else "ON_TRACK")
    update_row("projects", site_id, {"progress": str(progress), "status": status})

def milestone_page():
    st.title("🧱 Milestone Monitoring")
    
    sites_df = read_sheet("projects")
    if sites_df.empty:
        st.warning("⚠️ Tambahkan site dulu!")
        return
    
    # All Site option
    site_options = ["ALL SITE"] + sites_df["id"].tolist()
    selected_site = st.selectbox("Pilih Site:", site_options,
        format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE" 
        else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
    
    is_all_site = (selected_site == "ALL SITE")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Gantt", "➕ Tambah", "🚀 Template", "✏️ Edit", "📥 Import"])
    
    # ===== TAB 1: GANTT CHART =====
        # ===== TAB 1: GANTT / SUMMARY =====
    with tab1:
        if is_all_site:
            st.subheader("📊 Gantt Chart - ALL SITE")
            st.caption("Timeline milestone dari semua project")
            
            ms_df = read_sheet("milestones")
            if not ms_df.empty:
                # Group by milestone name (ambil start paling awal & end paling akhir)
                ms_df["planned_start"] = pd.to_datetime(ms_df["planned_start"], errors="coerce")
                ms_df["planned_end"] = pd.to_datetime(ms_df["planned_end"], errors="coerce")
                
                # Group per nama milestone
                grouped = ms_df.groupby("name").agg(
                    start=("planned_start", "min"),
                    end=("planned_end", "max"),
                    total_sites=("project_id", "nunique"),
                    done_count=("status", lambda x: (x == "DONE").sum()),
                    delayed_count=("status", lambda x: (x == "DELAYED").sum()),
                ).reset_index()
                
                grouped = grouped.sort_values("start")
                
                # Warna berdasarkan progress
                def get_status(row):
                    total = row["total_sites"]
                    done = row["done_count"]
                    delayed = row["delayed_count"]
                    if delayed > 0:
                        return "DELAYED"
                    elif done == total:
                        return "DONE"
                    elif done > 0:
                        return "ONGOING"
                    return "PENDING"
                
                grouped["status"] = grouped.apply(get_status, axis=1)
                
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
                    hover_data=["total_sites", "done_count", "delayed_count"],
                    title="Timeline Milestone - Semua Project"
                )
                
                fig.update_yaxes(autorange="reversed")
                
                min_date = grouped["start"].min()
                max_date = grouped["end"].max()
                fig.update_layout(
                    height=max(500, len(grouped) * 35),
                    xaxis_range=[min_date, max_date],
                    xaxis_title="Tanggal",
                    yaxis_title="Milestone"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary stats
                total_ms = len(grouped)
                total_sites_all = ms_df["project_id"].nunique()
                overall_start = min_date.strftime("%d %b %Y") if pd.notna(min_date) else "-"
                overall_end = max_date.strftime("%d %b %Y") if pd.notna(max_date) else "-"
                
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("🌍 Total Site", total_sites_all)
                col_b.metric("📊 Total Milestone Type", total_ms)
                col_c.metric("📅 Total Durasi", f"{overall_start} → {overall_end}")
                
                # Tabel detail
                st.markdown("---")
                st.subheader("📋 Detail per Milestone")
                
                detail_df = grouped.copy()
                detail_df["Start"] = detail_df["start"].dt.strftime("%d %b %Y")
                detail_df["End"] = detail_df["end"].dt.strftime("%d %b %Y")
                detail_df["Durasi (hari)"] = (detail_df["end"] - detail_df["start"]).dt.days
                detail_df["Progress"] = detail_df.apply(
                    lambda r: f"{r['done_count']}/{r['total_sites']} site", axis=1)
                
                display_df = detail_df[["name", "Start", "End", "Durasi (hari)", "Progress", "status"]]
                display_df.columns = ["Milestone", "Mulai", "Selesai", "Durasi (hari)", "Progress", "Status"]
                
                def color_status(val):
                    if val == "DONE": return 'background-color: #d4edda'
                    elif val == "DELAYED": return 'background-color: #f8d7da'
                    elif val == "ONGOING": return 'background-color: #cce5ff'
                    return ''
                
                styled = display_df.style.map(color_status, subset=["Status"])
                st.dataframe(styled, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada milestone.")
        
        else:
            # ... (Gantt per site, tidak berubah)
    
    # ===== TAB 2: TAMBAH MILESTONE =====
    with tab2:
        st.subheader("➕ Tambah Milestone")
        
        if is_all_site:
            st.warning("⚠️ Pilih site spesifik dulu untuk menambah milestone!")
        else:
            # Load existing untuk dependency
            ms_exist = read_sheet("milestones")
            dep_options = ["Tidak Ada"]
            dep_map = {}
            if not ms_exist.empty:
                exist_site = ms_exist[ms_exist["project_id"] == selected_site]
                for _, row in exist_site.iterrows():
                    dep_options.append(row["name"])
                    dep_map[row["name"]] = row["id"]
            
            with st.form("add_ms"):
                name = st.text_input("Nama Milestone", placeholder="Contoh: Pondasi Tower")
                
                c1, c2 = st.columns(2)
                with c1: ps = st.date_input("Rencana Mulai")
                with c2: pe = st.date_input("Rencana Selesai")
                
                c3, c4 = st.columns(2)
                with c3: weight = st.number_input("Bobot %", 0.0, 100.0, 10.0)
                with c4: status = st.selectbox("Status", ["PENDING","ONGOING","DONE","DELAYED"])
                
                mat_status = st.selectbox("Status Material", ["Belum Dicek","Lengkap","Tidak Lengkap"])
                dep_choice = st.selectbox("Dependency", dep_options)
                
                if st.form_submit_button("💾 Simpan", type="primary"):
                    if not name:
                        st.error("❌ Nama wajib diisi!")
                    else:
                        dep_id = dep_map.get(dep_choice, "")
                        insert_row("milestones", {
                            "id": generate_id(),
                            "project_id": selected_site,
                            "name": name,
                            "planned_start": ps.strftime("%Y-%m-%d"),
                            "planned_end": pe.strftime("%Y-%m-%d"),
                            "weight": str(weight),
                            "status": status,
                            "material_status": mat_status,
                            "dependency_id": dep_id
                        })
                        sync_milestone_to_site(selected_site)
                        st.success(f"✅ {name} ditambahkan!")
                        st.rerun()
    
    # ===== TAB 3: TEMPLATE =====
    with tab3:
        st.subheader("🚀 Auto-Generate Template Tower")
        
        if is_all_site:
            st.warning("⚠️ Pilih site spesifik dulu untuk generate template!")
        else:
            st.info("Generate 37 milestone standar tower project (3 fase)")
            
            c1, c2 = st.columns(2)
            with c1: start = st.date_input("Tanggal Mulai", value=datetime.now().date())
            with c2: days = st.number_input("Durasi/Task (hari)", 1, 30, 3)
            
            phases = st.multiselect("Pilih Fase:", list(TOWER_TEMPLATE.keys()), default=list(TOWER_TEMPLATE.keys()))
            
            if st.button("🚀 Generate Milestone", type="primary"):
                if not phases:
                    st.warning("⚠️ Pilih minimal satu fase!")
                else:
                    curr = start
                    created = 0
                    total_tasks = sum(len(TOWER_TEMPLATE[p]) for p in phases)
                    for phase in phases:
                        for task in TOWER_TEMPLATE[phase]:
                            insert_row("milestones", {
                                "id": generate_id(),
                                "project_id": selected_site,
                                "name": f"[{phase}] {task}",
                                "planned_start": curr.strftime("%Y-%m-%d"),
                                "planned_end": (curr + timedelta(days=days-1)).strftime("%Y-%m-%d"),
                                "weight": str(round(100/total_tasks, 1)),
                                "status": "PENDING",
                                "material_status": "Belum Dicek"
                            })
                            curr += timedelta(days=days)
                            created += 1
                    sync_milestone_to_site(selected_site)
                    st.success(f"✅ {created} milestone dibuat!")
                    st.balloons()
                    st.rerun()
    
    # ===== TAB 4: EDIT MILESTONE =====
    with tab4:
        st.subheader("✏️ Edit Milestone")
        
        if is_all_site:
            st.warning("⚠️ Pilih site spesifik dulu untuk edit milestone!")
        else:
            ms_df = read_sheet("milestones")
            if not ms_df.empty:
                site_ms = ms_df[ms_df["project_id"] == selected_site]
                if not site_ms.empty:
                    sel = st.selectbox("Pilih Milestone:", site_ms["id"].tolist(),
                        format_func=lambda x: site_ms[site_ms["id"]==x]["name"].values[0])
                    
                    if sel:
                        ms = site_ms[site_ms["id"]==sel].iloc[0]
                        
                        # Dependency options
                        dep_options = ["Tidak Ada"]
                        dep_map = {}
                        reverse_dep = {}
                        for _, r in site_ms.iterrows():
                            if r["id"] != sel:
                                dep_options.append(r["name"])
                                dep_map[r["name"]] = r["id"]
                                reverse_dep[r["id"]] = r["name"]
                        
                        cur_dep_id = ms.get("dependency_id","")
                        cur_dep_name = reverse_dep.get(cur_dep_id, "Tidak Ada")
                        dep_idx = dep_options.index(cur_dep_name) if cur_dep_name in dep_options else 0
                        
                        with st.form("edit_ms_form"):
                            ename = st.text_input("Nama", value=str(ms.get("name","")))
                            
                            # Plan dates
                            c1, c2 = st.columns(2)
                            with c1:
                                try: ps_d = datetime.strptime(str(ms.get("planned_start",""))[:10],"%Y-%m-%d")
                                except: ps_d = datetime.now()
                                ps = st.date_input("Plan Start", value=ps_d)
                            with c2:
                                try: pe_d = datetime.strptime(str(ms.get("planned_end",""))[:10],"%Y-%m-%d")
                                except: pe_d = datetime.now()
                                pe = st.date_input("Plan End", value=pe_d)
                            
                            # Actual dates
                            c3, c4 = st.columns(2)
                            with c3:
                                av_d = None
                                try: av_d = datetime.strptime(str(ms.get("actual_start",""))[:10],"%Y-%m-%d")
                                except: av_d = None
                                eas = st.date_input("Actual Start", value=av_d)
                            with c4:
                                av2_d = None
                                try: av2_d = datetime.strptime(str(ms.get("actual_end",""))[:10],"%Y-%m-%d")
                                except: av2_d = None
                                eae = st.date_input("Actual End", value=av2_d)
                            
                            # Status, weight, material
                            c5, c6, c7 = st.columns(3)
                            with c5:
                                sl = ["PENDING","ONGOING","DONE","DELAYED"]
                                s_idx = sl.index(ms.get("status","PENDING")) if ms.get("status") in sl else 0
                                estatus = st.selectbox("Status", sl, index=s_idx)
                            with c6:
                                eweight = st.number_input("Bobot %", 0.0, 100.0, float(ms.get("weight",0) or 0))
                            with c7:
                                ml = ["Belum Dicek","Lengkap","Tidak Lengkap"]
                                m_idx = ml.index(ms.get("material_status","Belum Dicek")) if ms.get("material_status") in ml else 0
                                emat = st.selectbox("Material", ml, index=m_idx)
                            
                            # Dependency
                            edep = st.selectbox("Dependency", dep_options, index=dep_idx)
                            
                            # Buttons
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.form_submit_button("💾 Update", type="primary"):
                                    update_row("milestones", sel, {
                                        "name": ename,
                                        "planned_start": ps.strftime("%Y-%m-%d"),
                                        "planned_end": pe.strftime("%Y-%m-%d"),
                                        "actual_start": eas.strftime("%Y-%m-%d") if eas else "",
                                        "actual_end": eae.strftime("%Y-%m-%d") if eae else "",
                                        "status": estatus,
                                        "weight": str(eweight),
                                        "material_status": emat,
                                        "dependency_id": dep_map.get(edep, "")
                                    })
                                    sync_milestone_to_site(selected_site)
                                    st.success("✅ Diupdate!")
                                    st.rerun()
                            with b2:
                                if st.form_submit_button("🗑️ Hapus", type="secondary"):
                                    delete_row_by_id("milestones", sel)
                                    sync_milestone_to_site(selected_site)
                                    st.warning("🗑️ Dihapus!")
                                    st.rerun()
                else:
                    st.info("Belum ada milestone untuk site ini.")
            else:
                st.info("Belum ada milestone.")
    
    # ===== TAB 5: IMPORT CSV =====
    with tab5:
        st.subheader("📥 Import CSV Milestone")
        
        if is_all_site:
            st.warning("⚠️ Pilih site spesifik dulu untuk import!")
        else:
            template = pd.DataFrame({
                "name": ["Pondasi", "Erection", "Finishing"],
                "planned_start": [today_str(), today_str(), today_str()],
                "planned_end": [today_str(), today_str(), today_str()],
                "weight": [30, 40, 30],
                "status": ["PENDING", "PENDING", "PENDING"],
                "material_status": ["Belum Dicek", "Belum Dicek", "Belum Dicek"]
            })
            st.download_button("📥 Download Template CSV", template.to_csv(index=False), "template_milestone.csv", "text/csv")
            
            up = st.file_uploader("Upload CSV", type=["csv"], key="ms_csv")
            if up:
                idf = pd.read_csv(up)
                st.dataframe(idf)
                if st.button("🚀 Import Milestone", type="primary"):
                    count = 0
                    for _, r in idf.iterrows():
                        insert_row("milestones", {
                            "id": generate_id(),
                            "project_id": selected_site,
                            "name": str(r.get("name","")),
                            "planned_start": str(r.get("planned_start", today_str())),
                            "planned_end": str(r.get("planned_end", today_str())),
                            "weight": str(r.get("weight", 10)),
                            "status": str(r.get("status", "PENDING")),
                            "material_status": str(r.get("material_status", "Belum Dicek"))
                        })
                        count += 1
                    sync_milestone_to_site(selected_site)
                    st.success(f"✅ {count} milestone diimport!")
                    st.rerun()

if __name__ == "__main__":
    milestone_page()
