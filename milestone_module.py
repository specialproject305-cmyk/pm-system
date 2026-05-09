import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from supabase_db import (
    read_all_sheets,
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
    all_data = read_all_sheets()
    ms_df = all_data.get("milestones", pd.DataFrame())
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
    
    selected_site = st.selectbox("Pilih Site:", sites_df["id"].tolist(),
        format_func=lambda x: f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Gantt", "➕ Tambah", "🚀 Template", "✏️ Edit", "📥 Import"])
    
    # TAB 1: Gantt Chart
    with tab1:
        ms_df = read_sheet("milestones")
        if not ms_df.empty:
            site_ms = ms_df[ms_df["project_id"] == selected_site]
            if not site_ms.empty:
                site_ms = site_ms.copy()
                site_ms["planned_start"] = pd.to_datetime(site_ms["planned_start"], errors="coerce")
                site_ms["planned_end"] = pd.to_datetime(site_ms["planned_end"], errors="coerce")
                
                color_map = {"PENDING":"#6c757d","ONGOING":"#0d6efd","DONE":"#28a745","DELAYED":"#dc3545"}
                fig = px.timeline(site_ms, x_start="planned_start", x_end="planned_end", y="name",
                                color="status", color_discrete_map=color_map)
                fig.update_yaxes(autorange="reversed")
                fig.update_layout(height=max(400, len(site_ms)*30))
                st.plotly_chart(fig, use_container_width=True)
                
                done = len(site_ms[site_ms["status"]=="DONE"])
                total = len(site_ms)
                st.progress(done/total if total>0 else 0)
                st.caption(f"Progress: {(done/total*100):.1f}%" if total>0 else "")
            else:
                st.info("Belum ada milestone.")
    
    # TAB 2: Tambah
    with tab2:
        st.subheader("Tambah Milestone")
        with st.form("add_ms"):
            name = st.text_input("Nama Milestone")
            c1, c2 = st.columns(2)
            with c1: ps = st.date_input("Rencana Mulai")
            with c2: pe = st.date_input("Rencana Selesai")
            weight = st.number_input("Bobot %", 0.0, 100.0, 10.0)
            status = st.selectbox("Status", ["PENDING","ONGOING","DONE","DELAYED"])
            mat_status = st.selectbox("Material", ["Belum Dicek","Lengkap","Tidak Lengkap"])
            
            if st.form_submit_button("💾 Simpan", type="primary"):
                if not name:
                    st.error("❌ Nama wajib diisi!")
                else:
                    insert_row("milestones", {
                        "id": generate_id(), "project_id": selected_site, "name": name,
                        "planned_start": ps.strftime("%Y-%m-%d"), "planned_end": pe.strftime("%Y-%m-%d"),
                        "weight": str(weight), "status": status, "material_status": mat_status
                    })
                    sync_milestone_to_site(selected_site)
                    st.success(f"✅ {name} ditambahkan!")
                    st.rerun()
    
    # TAB 3: Template
    with tab3:
        st.subheader("Auto-Generate Template")
        if st.button("🚀 Generate 37 Task Tower", type="primary"):
            curr = datetime.now().date()
            created = 0
            for phase in TOWER_TEMPLATE:
                for task in TOWER_TEMPLATE[phase]:
                    insert_row("milestones", {
                        "id": generate_id(), "project_id": selected_site,
                        "name": f"[{phase}] {task}",
                        "planned_start": curr.strftime("%Y-%m-%d"),
                        "planned_end": (curr + timedelta(days=3)).strftime("%Y-%m-%d"),
                        "weight": "5", "status": "PENDING", "material_status": "Belum Dicek"
                    })
                    curr += timedelta(days=4)
                    created += 1
            sync_milestone_to_site(selected_site)
            st.success(f"✅ {created} milestone dibuat!")
            st.balloons()
            st.rerun()
    
    # TAB 4: Edit
    with tab4:
        st.subheader("Edit Milestone")
        ms_df = read_sheet("milestones")
        if not ms_df.empty:
            site_ms = ms_df[ms_df["project_id"] == selected_site]
            if not site_ms.empty:
                sel = st.selectbox("Pilih Milestone:", site_ms["id"].tolist(),
                    format_func=lambda x: site_ms[site_ms["id"]==x]["name"].values[0])
                if sel:
                    ms = site_ms[site_ms["id"]==sel].iloc[0]
                    with st.form("edit_ms_form"):
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
                        
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.form_submit_button("💾 Update", type="primary"):
                                update_row("milestones", sel, {
                                    "name": ename,
                                    "planned_start": ps.strftime("%Y-%m-%d"),
                                    "planned_end": pe.strftime("%Y-%m-%d"),
                                    "actual_start": eas.strftime("%Y-%m-%d") if eas else "",
                                    "actual_end": eae.strftime("%Y-%m-%d") if eae else "",
                                    "status": estatus, "weight": str(eweight), "material_status": emat
                                })
                                sync_milestone_to_site(selected_site)
                                st.success("✅ Diupdate!"); st.rerun()
                        with b2:
                            if st.form_submit_button("🗑️ Hapus", type="secondary"):
                                delete_row_by_id("milestones", sel)
                                sync_milestone_to_site(selected_site)
                                st.warning("🗑️ Dihapus!"); st.rerun()
    
    # TAB 5: Import
    with tab5:
        st.subheader("Import CSV Milestone")
        template = pd.DataFrame({"name":["Pondasi"],"planned_start":[today_str()],"planned_end":[today_str()],"weight":[10],"status":["PENDING"],"material_status":["Belum Dicek"]})
        st.download_button("📥 Template", template.to_csv(index=False), "template_ms.csv", "text/csv")
        
        up = st.file_uploader("Upload CSV", type=["csv"], key="ms_csv")
        if up:
            idf = pd.read_csv(up)
            st.dataframe(idf)
            if st.button("🚀 Import", type="primary"):
                count = 0
                for _, r in idf.iterrows():
                    insert_row("milestones", {
                        "id": generate_id(), "project_id": selected_site,
                        "name": str(r.get("name","")),
                        "planned_start": str(r.get("planned_start",today_str())),
                        "planned_end": str(r.get("planned_end",today_str())),
                        "weight": str(r.get("weight",10)),
                        "status": str(r.get("status","PENDING")),
                        "material_status": str(r.get("material_status","Belum Dicek"))
                    })
                    count += 1
                sync_milestone_to_site(selected_site)
                st.success(f"✅ {count} milestone diimport!")
                st.rerun()

if __name__ == "__main__":
    milestone_page()
