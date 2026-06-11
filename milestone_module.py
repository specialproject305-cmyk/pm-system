import time
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
from supabase_db import (
    read_sheet, insert_row, update_row, delete_row_by_id,
    generate_id, today_str, safe_date_string
)

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

def sync_milestone_to_site(site_id):
    try:
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
    except:
        pass

def check_critical(row, today):
    try:
        if pd.isnull(row.get("planned_end")): return False
        end_date = row["planned_end"]
        if hasattr(end_date, 'date'): end_date = end_date.date()
        return end_date < today and row.get("status") != "DONE"
    except:
        return False

def milestone_page():
    st.title("🧱 Milestone Monitoring")
    
    sites_df = read_sheet("projects")
    ms_df = read_sheet("milestones")
    
    # ===== GLOBAL FILTER (SATU KALI SAJA) =====
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid_sites = sites_df[sites_df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
        sites_df = sites_df[sites_df['id'].isin(valid_sites)]
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)] if not ms_df.empty else ms_df
    
    if sites_df.empty:
        st.warning("⚠️ Tambahkan site dulu!")
        return
    
    # ===== AUTO-DELAY =====
    if not ms_df.empty:
        today = date.today()
        ms_df['planned_end_dt'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
        overdue = ms_df[(ms_df['status'].isin(['PENDING','ONGOING'])) & (ms_df['planned_end_dt'].dt.date < today)]
        if not overdue.empty:
            for _, row in overdue.iterrows():
                update_row('milestones', row['id'], {'status': 'DELAYED'})
            st.cache_data.clear()
            ms_df = read_sheet("milestones")
            # Re-apply filter
            if st.session_state.get('global_project_filter', 'ALL') != "ALL":
                ms_df = ms_df[ms_df['project_id'].isin(valid_sites)] if not ms_df.empty else ms_df
    
    site_options = ["ALL SITE"] + sites_df["id"].tolist()
    selected_site = st.selectbox("Pilih Site:", site_options,
        format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE" 
        else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
    
    is_all = (selected_site == "ALL SITE")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Gantt", "➕ Tambah", "🚀 Template", "✏️ Edit", "📥 Import"])
    
    # ===== TAB 1: GANTT =====
    with tab1:
        if ms_df.empty:
            st.info("Belum ada data.")
        else:
            ms_df["planned_start"] = pd.to_datetime(ms_df["planned_start"], errors="coerce")
            ms_df["planned_end"] = pd.to_datetime(ms_df["planned_end"], errors="coerce")
            
            if is_all:
                grouped = ms_df.groupby("name").agg(
                    start=("planned_start","min"), end=("planned_end","max"),
                    total_sites=("project_id","nunique"),
                    done_count=("status",lambda x:(x=="DONE").sum()),
                    delayed_count=("status",lambda x:(x=="DELAYED").sum())
                ).reset_index().sort_values("start")
                
                def gs(r):
                    if r["delayed_count"]>0: return "DELAYED"
                    elif r["done_count"]==r["total_sites"]: return "DONE"
                    elif r["done_count"]>0: return "ONGOING"
                    return "PENDING"
                grouped["status"] = grouped.apply(gs, axis=1)
                
                fig = px.timeline(grouped, x_start="start", x_end="end", y="name", color="status",
                    color_discrete_map={"PENDING":"#6c757d","ONGOING":"#0d6efd","DONE":"#28a745","DELAYED":"#dc3545"})
                fig.update_yaxes(autorange="reversed")
                fig.update_layout(height=max(500, len(grouped)*35))
                st.plotly_chart(fig, use_container_width=True)
            else:
                site_ms = ms_df[ms_df["project_id"]==selected_site].copy()
                if not site_ms.empty:
                    site_ms = site_ms.sort_values("planned_start")
                    site_ms["is_critical"] = site_ms.apply(lambda r: check_critical(r, today), axis=1)
                    site_ms["display_status"] = site_ms.apply(lambda r: "CRITICAL" if r["is_critical"] else r["status"], axis=1)
                    fig = px.timeline(site_ms, x_start="planned_start", x_end="planned_end", y="name", color="display_status",
                        color_discrete_map={"PENDING":"#6c757d","ONGOING":"#0d6efd","DONE":"#28a745","DELAYED":"#dc3545","CRITICAL":"#ff0000"})
                    fig.update_yaxes(autorange="reversed")
                    fig.update_layout(height=max(400, len(site_ms)*30))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    done = len(site_ms[site_ms["status"]=="DONE"]); total = len(site_ms)
                    if total > 0: st.progress(done/total); st.caption(f"Progress: {(done/total*100):.1f}%")
    
    # ===== TAB 2: TAMBAH =====
    with tab2:
        if is_all: st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            with st.form("add_ms"):
                name = st.text_input("Nama Milestone")
                c1, c2 = st.columns(2)
                with c1: ps = st.date_input("Rencana Mulai", value=datetime.now()); actual_s = st.date_input("Actual Start", value=None)
                with c2: pe = st.date_input("Rencana Selesai", value=datetime.now()+timedelta(days=7)); actual_e = st.date_input("Actual End", value=None)
                assigned = st.text_input("Assigned To"); weight = st.number_input("Bobot %", 0.0, 100.0, 5.0)
                status = st.selectbox("Status", ["PENDING","ONGOING","DONE","DELAYED"])
                delay_reason = st.text_input("Delay Reason", "Tidak Ada")
                
                if st.form_submit_button("💾 Simpan"):
                    if not name: st.error("Nama wajib diisi!")
                    else:
                        insert_row("milestones", {"id":generate_id(),"project_id":selected_site,"name":name,"planned_start":safe_date_string(ps),"planned_end":safe_date_string(pe),"actual_start":safe_date_string(actual_s) if actual_s else None,"actual_end":safe_date_string(actual_e) if actual_e else None,"assigned_to":assigned,"weight":str(weight),"status":status,"delay_reason":delay_reason})
                        sync_milestone_to_site(selected_site)
                        st.success("Berhasil!"); st.rerun()
    
    # ===== TAB 3: TEMPLATE =====
    with tab3:
        if is_all: st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            c1, c2 = st.columns(2)
            with c1: start_date = st.date_input("Tanggal Mulai", value=datetime.now().date())
            with c2: days = st.number_input("Durasi/Task", 1, 30, 3)
            phases = st.multiselect("Fase:", list(TOWER_TEMPLATE.keys()), default=list(TOWER_TEMPLATE.keys()))
            if st.button("🚀 Generate", type="primary"):
                if not phases: st.warning("⚠️ Pilih fase!")
                else:
                    curr = start_date; created = 0
                    for phase in phases:
                        for item in TOWER_TEMPLATE[phase]:
                            insert_row("milestones", {"id":generate_id(),"project_id":selected_site,"name":f"[{phase}] {item['task']}","planned_start":safe_date_string(curr),"planned_end":safe_date_string(curr+timedelta(days=item['sla']-1)),"assigned_to":item['assigned'],"weight":str(round(item['sla']/sum(x['sla'] for p in phases for x in TOWER_TEMPLATE[p])*100,1)),"status":"PENDING","sla_days":str(item['sla'])})
                            curr += timedelta(days=item['sla']); created += 1
                    sync_milestone_to_site(selected_site)
                    st.success(f"✅ {created} milestone!"); st.rerun()
    
    # ===== TAB 4: EDIT =====
    with tab4:
        if is_all: st.warning("⚠️ Pilih site spesifik dulu!")
        else:
            site_ms = ms_df[ms_df["project_id"]==selected_site] if not ms_df.empty else pd.DataFrame()
            if not site_ms.empty:
                sel = st.selectbox("Pilih:", site_ms["id"].tolist(), format_func=lambda x: site_ms[site_ms["id"]==x]["name"].values[0])
                if sel:
                    ms = site_ms[site_ms["id"]==sel].iloc[0]
                    with st.form("edit_ms"):
                        ename = st.text_input("Nama", value=ms.get("name",""))
                        c1, c2 = st.columns(2)
                        with c1: estatus = st.selectbox("Status", ["PENDING","ONGOING","DONE","DELAYED"], index=["PENDING","ONGOING","DONE","DELAYED"].index(ms.get("status","PENDING")) if ms.get("status") in ["PENDING","ONGOING","DONE","DELAYED"] else 0
                        with c2: eweight = st.number_input("Bobot %", 0.0, 100.0, float(ms.get("weight",5) or 5))
                        c3, c4 = st.columns(2)
                        with c3:
                            try: ps_d = pd.to_datetime(ms.get("planned_start")).date()
                            except: ps_d = datetime.now().date()
                            e_ps = st.date_input("Plan Start", value=ps_d)
                        with c4:
                            try: pe_d = pd.to_datetime(ms.get("planned_end")).date()
                            except: pe_d = datetime.now().date()
                            e_pe = st.date_input("Plan End", value=pe_d)
                        c5, c6 = st.columns(2)
                        with c5: e_as = st.date_input("Actual Start", value=None if pd.isna(ms.get("actual_start")) else pd.to_datetime(ms.get("actual_start")).date())
                        with c6: e_ae = st.date_input("Actual End", value=None if pd.isna(ms.get("actual_end")) else pd.to_datetime(ms.get("actual_end")).date())
                        edelay = st.text_input("Delay Reason", value=ms.get("delay_reason",""))
                        
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.form_submit_button("💾 Update"):
                                update_row("milestones", sel, {"name":ename,"status":estatus,"weight":str(eweight),"planned_start":safe_date_string(e_ps),"planned_end":safe_date_string(e_pe),"actual_start":safe_date_string(e_as) if e_as else None,"actual_end":safe_date_string(e_ae) if e_ae else None,"delay_reason":edelay})
                                sync_milestone_to_site(selected_site)
                                st.success("✅ Diupdate!"); st.rerun()
                        with b2:
                            if st.form_submit_button("🗑️ Hapus"):
                                delete_row_by_id("milestones", sel)
                                sync_milestone_to_site(selected_site)
                                st.warning("🗑️ Dihapus!"); st.rerun()
    
    # ===== TAB 5: IMPORT =====
        # ===== TAB 5: IMPORT CSV (MULTI-SITE) =====
    with tab5:
        st.subheader("📥 Import Milestone via CSV (Multi-Site)")
        st.info("💡 Satu file CSV bisa berisi milestone untuk banyak site. Gunakan kolom `site_id` untuk menentukan site tujuan.")
        
        # Template multi-site
        template = pd.DataFrame({
            "site_id": ["SITE-001", "SITE-001", "SITE-002"],
            "name": ["Pondasi", "Erection", "Pondasi"],
            "planned_start": [today_str(), today_str(), today_str()],
            "planned_end": [today_str(), today_str(), today_str()],
            "assigned_to": ["Engineering", "Project", "Engineering"],
            "weight": [10, 15, 10],
            "status": ["PENDING", "PENDING", "PENDING"],
            "delay_reason": ["", "", ""]
        })
        
        st.download_button("📥 Download Template CSV (Multi-Site)", template.to_csv(index=False), "template_milestone_multisite.csv", "text/csv")
        
        st.markdown("---")
        st.caption("Format: `site_id` = ID Site tujuan, kosongkan untuk import ke site yang dipilih di atas")
        
        up_file = st.file_uploader("Upload File CSV", type=["csv"])
        if up_file:
            df_import = pd.read_csv(up_file)
            st.write("Preview Data:")
            st.dataframe(df_import)
            
            # Cek apakah ada kolom site_id
            has_site_id = 'site_id' in df_import.columns
            
            if st.button("🚀 Konfirmasi Import Multi-Site"):
                success_count = 0
                error_rows = []
                
                # Buat mapping site_id → project_id
                site_map = dict(zip(sites_df['site_id'], sites_df['id'])) if not sites_df.empty else {}
                
                for idx, r in df_import.iterrows():
                    try:
                        # Tentukan project_id
                        if has_site_id and pd.notna(r.get('site_id')) and str(r['site_id']).strip() != '':
                            target_site_id = str(r['site_id']).strip()
                            if target_site_id in site_map:
                                project_id = site_map[target_site_id]
                            else:
                                error_rows.append(f"Baris {idx+2}: Site ID '{target_site_id}' tidak ditemukan")
                                continue
                        else:
                            project_id = selected_site if not is_all else None
                        
                        if project_id is None:
                            error_rows.append(f"Baris {idx+2}: Tidak bisa menentukan site tujuan")
                            continue
                        
                        new_id = insert_row("milestones", {
                            "id": generate_id(),
                            "project_id": project_id,
                            "name": str(r.get("name", "")),
                            "planned_start": safe_date_string(r.get("planned_start", today_str())),
                            "planned_end": safe_date_string(r.get("planned_end", today_str())),
                            "actual_start": safe_date_string(r.get("actual_start")) if r.get("actual_start") else None,
                            "actual_end": safe_date_string(r.get("actual_end")) if r.get("actual_end") else None,
                            "assigned_to": str(r.get("assigned_to", "")),
                            "weight": str(r.get("weight", 5)),
                            "status": str(r.get("status", "PENDING")),
                            "delay_reason": str(r.get("delay_reason", ""))
                        })
                        
                        if new_id:
                            success_count += 1
                            # Sync site yang bersangkutan
                            sync_milestone_to_site(project_id)
                        else:
                            error_rows.append(f"Baris {idx+2}: Gagal insert")
                            
                    except Exception as e:
                        error_rows.append(f"Baris {idx+2}: {str(e)[:50]}")
                
                if success_count > 0:
                    st.success(f"✅ Berhasil import {success_count} milestone ke {len(df_import['site_id'].unique()) if has_site_id else 1} site!")
                if error_rows:
                    with st.expander(f"⚠️ {len(error_rows)} error"):
                        for e in error_rows[:20]:
                            st.write(e)
                if success_count > 0:
                    st.cache_data.clear()
                    st.rerun()

if __name__ == "__main__":
    milestone_page()
