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
    
    site_options = ["ALL SITE"] + sites_df["id"].tolist()
    selected_site = st.selectbox("Pilih Site:", site_options,
        format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE" 
        else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
    
    is_all_site = (selected_site == "ALL SITE")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Gantt", "➕ Tambah", "🚀 Template", "✏️ Edit", "📥 Import"])
    
    # ===== TAB 1 =====
    with tab1:
        if is_all_site:
            st.subheader("📊 Gantt Chart - ALL SITE")
            st.caption("Timeline milestone dari semua project")
            
            ms_df = read_sheet("milestones")
            if not ms_df.empty:
                ms_df["planned_start"] = pd.to_datetime(ms_df["planned_start"], errors="coerce")
                ms_df["planned_end"] = pd.to_datetime(ms_df["planned_end"], errors="coerce")
                
                grouped = ms_df.groupby("name").agg(
                    start=("planned_start", "min"),
                    end=("planned_end", "max"),
                    total_sites=("project_id", "nunique"),
                    done_count=("status", lambda x: (x == "DONE").sum()),
                    delayed_count=("status", lambda x: (x == "DELAYED").sum()),
                ).reset_index()
                
                grouped = grouped.sort_values("start")
                
                def get_status(row):
                    if row["delayed_count"] > 0: return "DELAYED"
                    elif row["done_count"] == row["total_sites"]: return "DONE"
                    elif row["done_count"] > 0: return "ONGOING"
                    return "PENDING"
                
                grouped["status"] = grouped.apply(get_status, axis=1)
                
                color_map = {"PENDING":"#6c757d","ONGOING":"#0d6efd","DONE":"#28a745","DELAYED":"#dc3545"}
                
                fig = px.timeline(grouped, x_start="start", x_end="end", y="name",
                                color="status", color_discrete_map=color_map,
                                hover_data=["total_sites","done_count","delayed_count"],
                                title="Timeline Milestone - Semua Project")
                fig.update_yaxes(autorange="reversed")
                
                min_date = grouped["start"].min()
                max_date = grouped["end"].max()
                fig.update_layout(height=max(500, len(grouped)*35), xaxis_range=[min_date, max_date])
                st.plotly_chart(fig, use_container_width=True)
                
                total_sites_all = ms_df["project_id"].nunique()
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("🌍 Total Site", total_sites_all)
                col_b.metric("📊 Total Milestone Type", len(grouped))
                col_c.metric("📅 Durasi", f"{min_date.strftime('%d %b')} → {max_date.strftime('%d %b %Y')}")
            else:
                st.info("Belum ada milestone.")
        else:
            st.subheader("📊 Gantt Chart")
            ms_df = read_sheet("milestones")
            if not ms_df.empty:
                site_ms = ms_df[ms_df["project_id"] == selected_site]
                if not site_ms.empty:
                    site_ms = site_ms.copy()
                    site_ms["planned_start"] = pd.to_datetime(site_ms["planned_start"], errors="coerce")
                    site_ms["planned_end"] = pd.to_datetime(site_ms["planned_end"], errors="coerce")
                    
                    today = datetime.now().date()
                    def is_critical(row):
                        try:
                            end_d = row["planned_end"].date()
                            return end_d < today and row["status"] != "DONE"
                        except: return False
                    
                    site_ms["is_critical"] = site_ms.apply(is_critical, axis=1)
                    site_ms["display_status"] = site_ms.apply(lambda row: "CRITICAL" if row["is_critical"] else row["status"], axis=1)
                    
                    color_map = {"PENDING":"#6c757d","ONGOING":"#0d6efd","DONE":"#28a745","DELAYED":"#dc3545","CRITICAL":"#ff0000"}
                    site_ms = site_ms.sort_values("planned_start")
                    
                    fig = px.timeline(site_ms, x_start="planned_start", x_end="planned_end", y="name",
                                    color="display_status", color_discrete_map=color_map,
                                    title=f"Timeline - {sites_df[sites_df['id']==selected_site]['site_name'].values[0]}")
                    fig.update_yaxes(autorange="reversed")
                    fig.update_layout(height=max(400, len(site_ms)*30))
                                        # ===== TAMBAH DEPENDENCY LINES =====
                    for _, row in site_ms.iterrows():
                        dep_id = row.get("dependency_id", "")
                        if dep_id and str(dep_id) != "" and str(dep_id) != "None":
                            dep_row = site_ms[site_ms["id"] == dep_id]
                            if not dep_row.empty:
                                dep_end = dep_row.iloc[0]["planned_end"]
                                row_start = row["planned_start"]
                                y_dep = dep_row.iloc[0]["name"]
                                y_row = row["name"]
                                
                                # Garis dari ujung milestone A ke awal milestone B
                                fig.add_shape(
                                    type="line",
                                    x0=dep_end, x1=row_start,
                                    y0=y_dep, y1=y_row,
                                    line=dict(color="#ff6b6b", width=1.5, dash="dot"),
                                    layer="below"
                                )
                                
                                # Tambah panah kecil di ujung
                                fig.add_annotation(
                                    x=row_start, y=y_row,
                                    ax=dep_end, ay=y_dep,
                                    xref="x", yref="y",
                                    axref="x", ayref="y",
                                    showarrow=True,
                                    arrowhead=2,
                                    arrowsize=1,
                                    arrowwidth=1.5,
                                    arrowcolor="#ff6b6b"
                                )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    done = len(site_ms[site_ms["status"]=="DONE"])
                    total = len(site_ms)
                    critical = len(site_ms[site_ms["is_critical"]==True])
                    
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Total MS", total)
                    col_b.metric("✅ Done", done)
                    col_c.metric("🔴 Critical", critical)
                    
                    if total > 0:
                        st.progress(done/total)
                        st.caption(f"Progress: {(done/total*100):.1f}%")
                else:
                    st.info("Belum ada milestone.")
            else:
                st.info("Belum ada milestone.")
    
    # ===== TAB 2: TAMBAH =====
    with tab2:
        st.subheader("➕ Tambah Milestone")
        if is_all_site:
            st.warning("⚠️ Pilih site spesifik dulu untuk menambah!")
        else:
            ms_exist = read_sheet("milestones")
            dep_options = ["Tidak Ada"]
            dep_map = {}
            if not ms_exist.empty:
                for _, row in ms_exist[ms_exist["project_id"]==selected_site].iterrows():
                    dep_options.append(row["name"])
                    dep_map[row["name"]] = row["id"]
            
            with st.form("add_ms"):
                name = st.text_input("Nama Milestone")
                c1, c2 = st.columns(2)
                with c1: ps = st.date_input("Rencana Mulai")
                with c2: pe = st.date_input("Rencana Selesai")
                c3, c4 = st.columns(2)
                with c3: weight = st.number_input("Bobot %", 0.0, 100.0, 10.0)
                with c4: status = st.selectbox("Status", ["PENDING","ONGOING","DONE","DELAYED"])
                mat_status = st.selectbox("Material", ["Belum Dicek","Lengkap","Tidak Lengkap"])
                dep_choice = st.selectbox("Dependency", dep_options)
                
                if st.form_submit_button("💾 Simpan", type="primary"):
                    if not name:
                        st.error("❌ Nama wajib diisi!")
                    else:
                        insert_row("milestones", {
                            "id": generate_id(), "project_id": selected_site, "name": name,
                            "planned_start": ps.strftime("%Y-%m-%d"), "planned_end": pe.strftime("%Y-%m-%d"),
                            "weight": str(weight), "status": status, "material_status": mat_status,
                            "dependency_id": dep_map.get(dep_choice, "")
                        })
                        sync_milestone_to_site(selected_site)
                        st.success(f"✅ {name} ditambahkan!")
                        st.rerun()
    
    # ===== TAB 3: TEMPLATE =====
    with tab3:
        st.subheader("🚀 Auto-Generate Template")
        if is_all_site:
            st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            c1, c2 = st.columns(2)
            with c1: start = st.date_input("Tanggal Mulai", value=datetime.now().date())
            with c2: days = st.number_input("Durasi/Task (hari)", 1, 30, 3)
            phases = st.multiselect("Pilih Fase:", list(TOWER_TEMPLATE.keys()), default=list(TOWER_TEMPLATE.keys()))
            
            if st.button("🚀 Generate", type="primary"):
                if not phases:
                    st.warning("⚠️ Pilih minimal satu fase!")
                else:
                    curr = start; created = 0
                    total_tasks = sum(len(TOWER_TEMPLATE[p]) for p in phases)
                    for phase in phases:
                        for task in TOWER_TEMPLATE[phase]:
                            insert_row("milestones", {
                                "id": generate_id(), "project_id": selected_site,
                                "name": f"[{phase}] {task}",
                                "planned_start": curr.strftime("%Y-%m-%d"),
                                "planned_end": (curr+timedelta(days=days-1)).strftime("%Y-%m-%d"),
                                "weight": str(round(100/total_tasks,1)),
                                "status": "PENDING", "material_status": "Belum Dicek"
                            })
                            curr += timedelta(days=days); created += 1
                    sync_milestone_to_site(selected_site)
                    st.success(f"✅ {created} milestone dibuat!")
                    st.balloons(); st.rerun()
    
    # ===== TAB 4: EDIT =====
    with tab4:
        st.subheader("✏️ Edit Milestone")
        if is_all_site:
            st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            ms_df = read_sheet("milestones")
            if not ms_df.empty:
                site_ms = ms_df[ms_df["project_id"]==selected_site]
                if not site_ms.empty:
                    sel = st.selectbox("Pilih:", site_ms["id"].tolist(),
                        format_func=lambda x: site_ms[site_ms["id"]==x]["name"].values[0])
                    if sel:
                        ms = site_ms[site_ms["id"]==sel].iloc[0]
                        
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
                        
                        with st.form("edit_ms"):
                            ename = st.text_input("Nama", value=str(ms.get("name","")))
                            c1, c2 = st.columns(2)
                            with c1:
                                try: ps_d = datetime.strptime(str(ms.get("planned_start",""))[:10],"%Y-%m-%d")
                                except: ps_d = datetime.now()
                                ps = st.date_input("Plan Start", value=ps_d)
                            with c2:
                                try: pe_d = datetime.strptime(str(ms.get("planned_end",""))[:10],"%Y-%m-%d")
                                except: pe_d = datetime.now()
                                pe = st.date_input("Plan End", value=pe_d)
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
                            edep = st.selectbox("Dependency", dep_options, index=dep_idx)
                            
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.form_submit_button("💾 Update", type="primary"):
                                    update_row("milestones", sel, {
                                        "name": ename, "planned_start": ps.strftime("%Y-%m-%d"),
                                        "planned_end": pe.strftime("%Y-%m-%d"),
                                        "actual_start": eas.strftime("%Y-%m-%d") if eas else "",
                                        "actual_end": eae.strftime("%Y-%m-%d") if eae else "",
                                        "status": estatus, "weight": str(eweight), "material_status": emat,
                                        "dependency_id": dep_map.get(edep,"")
                                    })
                                    sync_milestone_to_site(selected_site)
                                    st.success("✅ Diupdate!"); st.rerun()
                            with b2:
                                if st.form_submit_button("🗑️ Hapus", type="secondary"):
                                    delete_row_by_id("milestones", sel)
                                    sync_milestone_to_site(selected_site)
                                    st.warning("🗑️ Dihapus!"); st.rerun()
    
    # ===== TAB 5: IMPORT =====
    with tab5:
        st.subheader("📥 Import CSV")
        if is_all_site:
            st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            template = pd.DataFrame({"name":["Pondasi"],"planned_start":[today_str()],"planned_end":[today_str()],"weight":[10],"status":["PENDING"],"material_status":["Belum Dicek"]})
            st.download_button("📥 Template", template.to_csv(index=False), "template_ms.csv", "text/csv")
            up = st.file_uploader("Upload CSV", type=["csv"], key="ms_csv")
            if up:
                idf = pd.read_csv(up); st.dataframe(idf)
                if st.button("🚀 Import", type="primary"):
                    count = 0
                    for _, r in idf.iterrows():
                        insert_row("milestones", {
                            "id": generate_id(), "project_id": selected_site,
                            "name": str(r.get("name","")), "planned_start": str(r.get("planned_start",today_str())),
                            "planned_end": str(r.get("planned_end",today_str())), "weight": str(r.get("weight",10)),
                            "status": str(r.get("status","PENDING")), "material_status": str(r.get("material_status","Belum Dicek"))
                        })
                        count += 1
                    sync_milestone_to_site(selected_site)
                    st.success(f"✅ {count} milestone diimport!"); st.rerun()

if __name__ == "__main__":
    milestone_page()
