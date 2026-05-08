import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

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

    selected_site = st.selectbox(
        "Pilih Site:",
        sites_df["id"].tolist(),

        format_func=lambda x:
        f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - "
        f"{sites_df[sites_df['id']==x]['site_name'].values[0]}"
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
                    "DELAYED": "#dc3545"
                }

                fig = px.timeline(
                    site_ms,
                    x_start="planned_start",
                    x_end="planned_end",
                    y="name",
                    color="status",
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

            if st.form_submit_button(
                "💾 Simpan",
                type="primary"
            ):

                insert_row(
                    "milestones",
                    {
                        "id": generate_id(),
                        "project_id": selected_site,
                        "name": name,
                        "planned_start": ps.strftime("%Y-%m-%d"),
                        "planned_end": pe.strftime("%Y-%m-%d"),
                        "weight": str(weight),
                        "status": status
                    }
                )

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
            ]

            if not site_ms.empty:

                sel = st.selectbox(
                    "Pilih Milestone",
                    site_ms["id"].tolist(),

                    format_func=lambda x:
                    site_ms[
                        site_ms["id"] == x
                    ]["name"].values[0]
                )

                st.write("Selected:", sel)

    # ======================================================
    # TAB 5
    # ======================================================

    with tab5:

        st.subheader("Import CSV")

        st.info("Fitur import siap digunakan.")


if __name__ == "__main__":
    milestone_page()
