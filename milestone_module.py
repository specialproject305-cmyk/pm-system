import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
@st.cache_data(ttl=60)
def load_milestones():
    return read_sheet("milestones")

from supabase_db import (
    read_all_sheets,
    read_sheet,
    insert_row,
    update_row,
    find_row_by_id,
    delete_row_by_id,
    generate_id,
    today_str
)

TOWER_TEMPLATE = {
    "SPK TENANT": [
        "Hunting dan Survey",
        "Validation",
        "Sosialisasi Warga Radius",
        "Negosiasi Sewa Lahan",
        "Negosiasi IW Radius",
        "Pengajuan Budget IW & SA Lahan",
        "BAK",
        "Legal Proses",
        "Akuisisi",
        "RFC"
    ],

    "APD, BoQ & Material": [
        "Soil test",
        "APD Pondasi",
        "APD & BoQ Tower full Design Pack",
        "PR Material",
        "PO Material",
        "Produksi Massal",
        "Material RFD",
        "Pengiriman Material"
    ],

    "Implementation": [
        "Request SPK",
        "Proses Pengadaan vendor",
        "Kick of Meeting (KoM)",
        "Mobilisasi team & Bowplank",
        "Foundation",
        "Curing time",
        "Backfilling",
        "Erection",
        "Pondasi rack ODC",
        "Install ME & Grounding",
        "Pekerjaan Fence",
        "Lanscape",
        "PLN connect",
        "Install pole FO",
        "Laying FO",
        "Terminasi",
        "DC Power Instalation",
        "RFS",
        "RFIN submit"
    ]
}

def calculate_task_progress(status):

    if status == "DONE":
        return 100

    elif status == "ONGOING":
        return 50

    elif status == "DELAYED":
        return 25

    return 0


def check_dependency(site_ms, dependency_id):

    if not dependency_id:
        return True

    dep = site_ms[
        site_ms["id"] == dependency_id
    ]

    if dep.empty:
        return True

    dep_status = dep.iloc[0]["status"]

    return dep_status == "DONE"


def detect_critical_tasks(site_ms):

    today = datetime.now().date()

    critical_ids = []

    for _, row in site_ms.iterrows():

        try:
            end_date = datetime.strptime(
                str(row["planned_end"])[:10],
                "%Y-%m-%d"
            ).date()

            status = row.get("status", "PENDING")

            if end_date < today and status != "DONE":
                critical_ids.append(row["id"])

        except:
            pass

    return critical_ids
def sync_milestone_to_site(site_id):

    all_data = read_all_sheets()
    ms_df = all_data.get("milestones", pd.DataFrame())

    if ms_df.empty:
        return

    if "project_id" not in ms_df.columns:
        return

    site_ms = ms_df[ms_df["project_id"] == site_id]

    if site_ms.empty:
        return

    site_ms = site_ms.copy()

    site_ms["weight"] = pd.to_numeric(
        site_ms["weight"],
        errors="coerce"
    ).fillna(0)

    total_weight = site_ms["weight"].sum()

    done_weight = site_ms[
        site_ms["status"] == "DONE"
    ]["weight"].sum()

    progress = (
        round((done_weight / total_weight) * 100, 1)
        if total_weight > 0 else 0
    )

    delayed = len(
        site_ms[site_ms["status"] == "DELAYED"]
    )

    status = (
        "CRITICAL"
        if delayed > 3
        else (
            "DELAYED"
            if delayed > 0
            else "ON_TRACK"
        )
    )

    update_row(
        "projects",
        site_id,
        {
            "progress": str(progress),
            "status": status
        }
    )


def milestone_page():

    st.title("🧱 Milestone Monitoring")

    sites_df = read_sheet("projects")

    if sites_df.empty:
        st.warning("⚠️ Tambahkan site dulu!")
        return

    site_options = ["ALL SITE"] + sites_df["id"].tolist()

    selected_site = st.selectbox(
        "Pilih Site:",
        site_options,
    
        format_func=lambda x:
        "🌐 ALL SITE"
        if x == "ALL SITE"
        else (
            f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - "
            f"{sites_df[sites_df['id']==x]['site_name'].values[0]}"
        )
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Gantt",
        "➕ Tambah",
        "🚀 Template",
        "✏️ Edit",
        "📥 Import"
    ])

    # ======================================================
    # TAB 1
    # ======================================================

    with tab1:

        ms_df = read_sheet("milestones")

        if not ms_df.empty:

            site_ms = ms_df[
                ms_df["project_id"] == selected_site
            ]

            if not site_ms.empty:

                site_ms = site_ms.copy()
                # ==========================================
                # CRITICAL TASK DETECTION
                # ==========================================
                
                today = datetime.now().date()
                
                site_ms["is_critical"] = False
                
                for idx, row in site_ms.iterrows():
                
                    try:
                
                        end_date = pd.to_datetime(
                            row["planned_end"]
                        ).date()
                
                        if (
                            end_date < today
                            and row["status"] != "DONE"
                        ):
                
                            site_ms.at[idx, "is_critical"] = True
                
                    except:
                        pass

                site_ms["planned_start"] = pd.to_datetime(
                    site_ms["planned_start"],
                    errors="coerce"
                )

                site_ms["planned_end"] = pd.to_datetime(
                    site_ms["planned_end"],
                    errors="coerce"
                )

                color_map = {
                    "PENDING": "#6c757d",
                    "ONGOING": "#0d6efd",
                    "DONE": "#28a745",
                    "DELAYED": "#dc3545",
                    "CRITICAL": "#ff0000"
                }
                site_ms["display_status"] = site_ms.apply(
                    lambda row:
                    "CRITICAL"
                    if row["is_critical"]
                    else row["status"],
                    axis=1
                )

                fig = px.timeline(
                    site_ms,
                    x_start="planned_start",
                    x_end="planned_end",
                    y="name",
                    color="display_status",
                    color_discrete_map=color_map
                )

                fig.update_yaxes(
                    autorange="reversed"
                )

                fig.update_layout(
                    height=max(400, len(site_ms) * 30)
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )
                critical_count = len(
                    site_ms[
                        site_ms["is_critical"] == True
                    ]
                )

                if critical_count > 0:
                
                    st.warning(
                        f"⚠️ {critical_count} milestone critical ditemukan"
                    )

            else:
                st.info("Belum ada milestone.")

    # ======================================================
    # TAB 2
    # ======================================================

    with tab2:

        st.subheader("Tambah Milestone")
    
        with st.form("add_ms"):
    
            name = st.text_input("Nama Milestone")
    
            c1, c2 = st.columns(2)
    
            with c1:
                ps = st.date_input("Rencana Mulai")
    
            with c2:
                pe = st.date_input("Rencana Selesai")
    
            weight = st.number_input(
                "Bobot %",
                0.0,
                100.0,
                10.0
            )
    
            status = st.selectbox(
                "Status",
                ["PENDING", "ONGOING", "DONE", "DELAYED"]
            )
    
            # ==========================================
            # DEPENDENCY
            # ==========================================
    
            ms_df = load_milestones()
    
            dependency_options = ["None"]
    
            dependency_map = {}
    
            if not ms_df.empty:
    
                dep_site = ms_df[
                    ms_df["project_id"] == selected_site
                ]
    
                for _, row in dep_site.iterrows():
    
                    dependency_options.append(
                        row["name"]
                    )
    
                    dependency_map[row["name"]] = row["id"]
    
            selected_dependency = st.selectbox(
                "Dependency Task",
                dependency_options
            )
    
            # ==========================================
            # SAVE
            # ==========================================
    
            if st.form_submit_button(
                "💾 Simpan",
                type="primary"
            ):
    
                insert_row(
                    "milestones",
                    {
                        "id": generate_id(),
                        "project_id": selected_site,
    
                        "dependency_id": (
                            dependency_map[selected_dependency]
                            if selected_dependency != "None"
                            else ""
                        ),
    
                        "name": name,
                        "planned_start": ps.strftime("%Y-%m-%d"),
                        "planned_end": pe.strftime("%Y-%m-%d"),
                        "weight": str(weight),
                        "status": status
                    }
                )
    
                st.cache_data.clear()
    
                sync_milestone_to_site(selected_site)
    
                st.success("✅ Berhasil disimpan!")
    
                st.rerun()

    # ======================================================
    # TAB 3
    # ======================================================

    with tab3:

        st.subheader("Auto Generate Template")

        if st.button("🚀 Generate"):

            curr = datetime.now().date()

            for phase in TOWER_TEMPLATE:

                for task in TOWER_TEMPLATE[phase]:

                    insert_row(
                        "milestones",
                        {
                            "id": generate_id(),
                            "project_id": selected_site,
                            "name": f"[{phase}] {task}",
                            "planned_start": curr.strftime("%Y-%m-%d"),
                            "planned_end": (
                                curr + timedelta(days=3)
                            ).strftime("%Y-%m-%d"),
                            "weight": "5",
                            "status": "PENDING"
                        }
                    )

                    curr += timedelta(days=4)

            st.success("✅ Template berhasil dibuat!")
            st.rerun()

    # ======================================================
    # TAB 4
    # ======================================================
    
    with tab4:
    
        st.subheader("Edit Milestone")
    
        ms_df = read_sheet("milestones")
    
        if not ms_df.empty:
    
            site_ms = ms_df[
                ms_df["project_id"] == selected_site
            ].copy()
    
            if not site_ms.empty:
    
                sel = st.selectbox(
                    "Pilih Milestone",
                    site_ms["id"].tolist(),
                    format_func=lambda x:
                    site_ms[
                        site_ms["id"] == x
                    ]["name"].values[0]
                )
    
                if sel:
    
                    ms = site_ms[
                        site_ms["id"] == sel
                    ].iloc[0]
    
                    with st.form("edit_ms_form"):
    
                        ename = st.text_input(
                            "Nama",
                            value=str(ms.get("name", ""))
                        )
    
                        # ==========================================
                        # PLAN DATE
                        # ==========================================
    
                        c1, c2 = st.columns(2)
    
                        with c1:
    
                            try:
                                ps_d = datetime.strptime(
                                    str(ms.get("planned_start", ""))[:10],
                                    "%Y-%m-%d"
                                ).date()
    
                            except:
                                ps_d = datetime.now().date()
    
                            ps = st.date_input(
                                "Plan Start",
                                value=ps_d,
                                key="edit_plan_start"
                            )
    
                        with c2:
    
                            try:
                                pe_d = datetime.strptime(
                                    str(ms.get("planned_end", ""))[:10],
                                    "%Y-%m-%d"
                                ).date()
    
                            except:
                                pe_d = datetime.now().date()
    
                            pe = st.date_input(
                                "Plan End",
                                value=pe_d,
                                key="edit_plan_end"
                            )
    
                        # ==========================================
                        # ACTUAL DATE
                        # ==========================================
    
                        c3, c4 = st.columns(2)
    
                        with c3:
    
                            try:
                                av_d = datetime.strptime(
                                    str(ms.get("actual_start", ""))[:10],
                                    "%Y-%m-%d"
                                ).date()
    
                            except:
                                av_d = datetime.now().date()
    
                            eas = st.date_input(
                                "Actual Start",
                                value=av_d,
                                key="edit_actual_start"
                            )
    
                        with c4:
    
                            try:
                                av2_d = datetime.strptime(
                                    str(ms.get("actual_end", ""))[:10],
                                    "%Y-%m-%d"
                                ).date()
    
                            except:
                                av2_d = datetime.now().date()
    
                            eae = st.date_input(
                                "Actual End",
                                value=av2_d,
                                key="edit_actual_end"
                            )
    
                        # ==========================================
                        # STATUS & WEIGHT
                        # ==========================================
    
                        c5, c6, c7 = st.columns(3)
    
                        with c5:
    
                            status_list = [
                                "PENDING",
                                "ONGOING",
                                "DONE",
                                "DELAYED"
                            ]
    
                            current_status = ms.get(
                                "status",
                                "PENDING"
                            )
    
                            status_index = (
                                status_list.index(current_status)
                                if current_status in status_list
                                else 0
                            )
    
                            estatus = st.selectbox(
                                "Status",
                                status_list,
                                index=status_index
                            )
    
                        with c6:
    
                            eweight = st.number_input(
                                "Bobot %",
                                min_value=0.0,
                                max_value=100.0,
                                value=float(ms.get("weight", 0) or 0)
                            )
    
                        with c7:
    
                            material_list = [
                                "Belum Dicek",
                                "Lengkap",
                                "Tidak Lengkap"
                            ]
    
                            current_material = ms.get(
                                "material_status",
                                "Belum Dicek"
                            )
    
                            material_index = (
                                material_list.index(current_material)
                                if current_material in material_list
                                else 0
                            )
    
                            emat = st.selectbox(
                                "Material",
                                material_list,
                                index=material_index
                            )
                            
                            # ==========================================
                            # DEPENDENCY
                            # ==========================================
                            
                            dependency_options = ["None"]
                            
                            dependency_map = {}
                            
                            reverse_dependency_map = {}
                            
                            for _, row in site_ms.iterrows():
                            
                                if row["id"] != sel:
                            
                                    dependency_options.append(
                                        row["name"]
                                    )
                            
                                    dependency_map[row["name"]] = row["id"]
                            
                                    reverse_dependency_map[row["id"]] = row["name"]
                            
                            current_dependency_id = ms.get(
                                "dependency_id",
                                ""
                            )
                            
                            current_dependency_name = "None"
                            
                            if current_dependency_id in reverse_dependency_map:
                            
                                current_dependency_name = reverse_dependency_map[
                                    current_dependency_id
                                ]
                            
                            dependency_index = (
                                dependency_options.index(current_dependency_name)
                                if current_dependency_name in dependency_options
                                else 0
                            )
                            
                            selected_dependency = st.selectbox(
                                "Dependency Task",
                                dependency_options,
                                index=dependency_index
                            )
    
                        # ==========================================
                        # BUTTON
                        # ==========================================
    
                        b1, b2 = st.columns(2)
    
                        with b1:
    
                            update_btn = st.form_submit_button(
                                "💾 Update",
                                type="primary"
                            )
    
                        with b2:
    
                            delete_btn = st.form_submit_button(
                                "🗑️ Hapus"
                            )
    
                        # ==========================================
                        # UPDATE
                        # ==========================================
    
                        if update_btn:
    
                            update_row(
                                "milestones",
                                sel,
                                {
                                    "name": ename,

                                    "dependency_id": (
                                        dependency_map[selected_dependency]
                                        if selected_dependency != "None"
                                        else ""
                                    ),
                                    "planned_start": ps.strftime("%Y-%m-%d"),
                                    "planned_end": pe.strftime("%Y-%m-%d"),
                                    "actual_start": eas.strftime("%Y-%m-%d"),
                                    "actual_end": eae.strftime("%Y-%m-%d"),
                                    "status": estatus,
                                    "weight": str(eweight),
                                    "material_status": emat
                                }
                            )
                            st.cache_data.clear()
    
                            sync_milestone_to_site(selected_site)
    
                            st.success("✅ Diupdate!")
                            st.rerun()
    
                        # ==========================================
                        # DELETE
                        # ==========================================
    
                        if delete_btn:
    
                            delete_row_by_id(
                                "milestones",
                                sel
                            )
    
                            sync_milestone_to_site(selected_site)
    
                            st.warning("🗑️ Dihapus!")
                            st.rerun()  

    # ======================================================
    # TAB 5
    # ======================================================

    with tab5:

        st.subheader("Import CSV")

        st.info("Fitur import siap digunakan.")


if __name__ == "__main__":
    milestone_page()
