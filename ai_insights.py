import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from datetime import datetime, timedelta

from supabase_db import (
    read_all_sheets,
    insert_row,
    generate_id,
    now_str
)

from fpdf import FPDF
import tempfile


# =========================================================
# PDF GENERATOR
# =========================================================

def generate_ai_pdf(
    site_name,
    health_score,
    avg_progress,
    on_track,
    total_sites,
    delayed,
    forecast_end,
    delay_reasons,
    summary
):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font('Helvetica', 'B', 16)

    pdf.cell(
        0,
        10,
        'AI Analytics Report',
        0,
        1,
        'C'
    )

    pdf.set_font('Helvetica', 'I', 10)

    pdf.cell(
        0,
        5,
        f'Generated: {datetime.now().strftime("%d %b %Y, %H:%M")}',
        0,
        1,
        'C'
    )

    pdf.cell(
        0,
        5,
        f'Site: {site_name}',
        0,
        1,
        'C'
    )

    pdf.ln(5)

    # =========================================
    # EXECUTIVE SUMMARY
    # =========================================

    pdf.set_font('Helvetica', 'B', 14)

    pdf.cell(
        0,
        10,
        '1. Executive Summary',
        0,
        1
    )

    pdf.set_font('Helvetica', '', 10)

    pdf.cell(0, 6, f'Health Score: {health_score}%', 0, 1)
    pdf.cell(0, 6, f'Progress: {avg_progress}%', 0, 1)
    pdf.cell(0, 6, f'On Track: {on_track}/{total_sites} sites', 0, 1)
    pdf.cell(0, 6, f'Delayed: {delayed} sites', 0, 1)
    pdf.cell(0, 6, f'Forecast Completion: {forecast_end}', 0, 1)

    pdf.ln(3)

    # =========================================
    # DELAY ANALYSIS
    # =========================================

    if delay_reasons:

        pdf.set_font('Helvetica', 'B', 14)

        pdf.cell(
            0,
            10,
            '2. Delay Reason Analysis',
            0,
            1
        )

        pdf.set_font('Helvetica', '', 10)

        for reason, count in delay_reasons.items():

            pdf.cell(
                0,
                6,
                f'- {reason}: {count} milestone',
                0,
                1
            )

        pdf.ln(3)

    # =========================================
    # RECOMMENDATION
    # =========================================

    pdf.set_font('Helvetica', 'B', 14)

    pdf.cell(
        0,
        10,
        '3. Recommendations',
        0,
        1
    )

    pdf.set_font('Helvetica', '', 10)

    for line in summary.split('\n'):

        if line.strip():

            pdf.multi_cell(
                0,
                6,
                line.strip()
            )

    return pdf


# =========================================================
# MAIN PAGE
# =========================================================

def ai_insights_page():

    st.title("🤖 AI-Powered Analytics Center")

    all_data = read_all_sheets()

    sites_df = all_data.get(
        'projects',
        pd.DataFrame()
    )

    ms_df = all_data.get(
        'milestones',
        pd.DataFrame()
    )

    mat_df = all_data.get(
        'materials',
        pd.DataFrame()
    )

    # =====================================================
    # VALIDATION
    # =====================================================

    if sites_df.empty:

        st.warning("⚠️ Belum ada data site.")

        return

    # =====================================================
    # CLEAN DATA
    # =====================================================

    if (
        not sites_df.empty
        and 'progress' in sites_df.columns
    ):

        sites_df['progress'] = pd.to_numeric(
            sites_df['progress'],
            errors='coerce'
        ).fillna(0)

    if not ms_df.empty:

        date_cols = [
            'planned_start',
            'planned_end',
            'actual_start',
            'actual_end'
        ]

        for col in date_cols:

            if col not in ms_df.columns:
                ms_df[col] = None

            ms_df[col] = pd.to_datetime(
                ms_df[col],
                errors='coerce'
            )

    # =====================================================
    # FILTER
    # =====================================================

    col_f1, col_f2 = st.columns(2)

    with col_f1:

        site_options = (
            ["ALL SITE"]
            + sites_df["id"].tolist()
        )

        selected_site = st.selectbox(
            "🎯 Pilih Site:",
            site_options,

            format_func=lambda x:
            "🌍 ALL SITE"
            if x == "ALL SITE"
            else (
                f"{sites_df[sites_df['id']==x]['site_id'].values[0]}"
                f" - "
                f"{sites_df[sites_df['id']==x]['site_name'].values[0]}"
            )
        )

    with col_f2:

        delay_reason = st.text_input(
            "🔍 Delay Reason",
            placeholder="Contoh: Material terlambat"
        )

    # =====================================================
    # FILTERING DATA
    # =====================================================

    is_all = (
        selected_site == "ALL SITE"
    )

    if not is_all:

        site_data = sites_df[
            sites_df['id'] == selected_site
        ]

        site_ms = ms_df[
            ms_df['project_id'] == selected_site
        ] if not ms_df.empty else pd.DataFrame()

        site_name = (
            site_data.iloc[0]['site_name']
            if not site_data.empty
            else "Unknown"
        )

    else:

        site_data = sites_df

        site_ms = ms_df

        site_name = "ALL SITE"

    # =====================================================
    # BUTTON ANALYSIS
    # =====================================================

    if st.button(
        "🔍 Generate Full Analysis",
        type="primary"
    ):

        st.divider()

        # =================================================
        # 1. PROGRESS ANALYSIS
        # =================================================

        st.header("📈 1. Progress Analysis")

        col_a, col_b = st.columns(2)

        # =============================================
        # PLANNED VS ACTUAL
        # =============================================

        with col_a:

            st.subheader("Planned vs Actual")

            if (
                not site_ms.empty
                and 'actual_end' in site_ms.columns
            ):

                done_ms = site_ms[
                    site_ms['status'] == 'DONE'
                ].copy()

                if not done_ms.empty:

                    done_ms['planned_duration'] = (
                        done_ms['planned_end']
                        - done_ms['planned_start']
                    ).dt.days

                    done_ms['actual_duration'] = (
                        done_ms['actual_end']
                        - done_ms['actual_start']
                    ).dt.days

                    done_ms['delay_days'] = (
                        done_ms['actual_duration']
                        - done_ms['planned_duration']
                    )

                    avg_planned = (
                        done_ms['planned_duration'].mean()
                    )

                    avg_actual = (
                        done_ms['actual_duration'].mean()
                    )

                    fig = go.Figure()

                    fig.add_trace(
                        go.Bar(
                            name='Planned',
                            x=['Durasi'],
                            y=[avg_planned]
                        )
                    )

                    fig.add_trace(
                        go.Bar(
                            name='Actual',
                            x=['Durasi'],
                            y=[avg_actual]
                        )
                    )

                    fig.update_layout(
                        height=300,
                        barmode='group'
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                    st.metric(
                        "Rata-rata Keterlambatan",
                        f"{done_ms['delay_days'].mean():.1f} hari"
                    )

        # =============================================
        # PROGRESS GAUGE
        # =============================================

        with col_b:

            st.subheader("Delay Prediction")

            if not site_ms.empty:

                total = len(site_ms)

                done = len(
                    site_ms[
                        site_ms['status'] == 'DONE'
                    ]
                )

                progress = (
                    round((done / total) * 100, 1)
                    if total > 0
                    else 0
                )

                predicted_end = (
                    datetime.now()
                    + timedelta(days=int((100 - progress) * 2))
                )

                fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=progress,
                        title={'text': "Progress %"},
                        gauge={
                            'axis': {'range': [0, 100]}
                        }
                    )
                )

                fig.update_layout(height=300)

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

                st.info(
                    f"📅 Prediksi selesai: "
                    f"**{predicted_end.strftime('%d %b %Y')}**"
                )

        st.divider()

        # =================================================
        # 2. CRITICAL PATH
        # =================================================

        st.header("🔴 Critical Path")

        if not site_ms.empty:

            critical = site_ms[
                site_ms['status'].isin(
                    ['DELAYED', 'CRITICAL']
                )
            ]

            if not critical.empty:

                st.error(
                    f"⚠️ {len(critical)} milestone critical"
                )

                for _, c in critical.iterrows():

                    end_date = (
                        c['planned_end'].strftime('%d %b')
                        if pd.notna(c.get('planned_end'))
                        else '?'
                    )

                    st.markdown(
                        f"- **{c['name']}** "
                        f"(Target: {end_date}) "
                        f"- Status: {c['status']}"
                    )

            else:

                st.success(
                    "✅ Tidak ada critical path."
                )

        st.divider()

        # =================================================
        # 3. SITE RANKING
        # =================================================

        st.header("🏆 Site Ranking")

        if not sites_df.empty:

            ranking = (
                sites_df
                .sort_values(
                    'progress',
                    ascending=False
                )[
                    [
                        'site_id',
                        'site_name',
                        'progress',
                        'status'
                    ]
                ]
                .head(10)
            )

            st.dataframe(
                ranking,
                use_container_width=True,
                hide_index=True
            )

        st.divider()

        # =================================================
        # 4. EXECUTIVE SUMMARY
        # =================================================

        st.header("📋 Executive Summary")

        total_sites = len(sites_df)

        avg_progress = (
            sites_df['progress'].mean()
            if not sites_df.empty
            else 0
        )

        on_track = len(
            sites_df[
                sites_df['status'] == 'ON_TRACK'
            ]
        )

        delayed = len(
            sites_df[
                sites_df['status'].isin(
                    ['DELAYED', 'CRITICAL']
                )
            ]
        )

        health_score = round(
            (on_track / total_sites) * 100,
            1
        ) if total_sites > 0 else 0

        # =============================================
        # FORECAST
        # =============================================

        if not is_all:

            if not site_data.empty:

                forecast_end = (
                    datetime.now()
                    + timedelta(
                        days=int(
                            (
                                100
                                - site_data.iloc[0]['progress']
                            ) * 2
                        )
                    )
                )

            else:

                forecast_end = datetime.now()

        else:

            forecast_end = (
                datetime.now()
                + timedelta(
                    days=int(
                        (100 - avg_progress) * 2
                    )
                )
            )

        # =============================================
        # SUMMARY TEXT
        # =============================================

        summary = f"""
Executive Summary

Total Site: {total_sites}
Average Progress: {avg_progress:.1f}%
On Track: {on_track}
Delayed: {delayed}

Forecast Completion:
{forecast_end.strftime('%d %b %Y')}
"""

        st.info(summary)

        st.divider()

        # =================================================
        # PDF EXPORT
        # =================================================

        st.subheader("📥 Export Report")

        if st.button(
            "📄 Generate PDF Report",
            key="gen_pdf"
        ):

            with st.spinner(
                "Generating PDF..."
            ):

                try:

                    pdf = generate_ai_pdf(
                        site_name=site_name,
                        health_score=health_score,
                        avg_progress=round(avg_progress, 1),
                        on_track=on_track,
                        total_sites=total_sites,
                        delayed=delayed,
                        forecast_end=forecast_end.strftime('%d %b %Y'),
                        delay_reasons={},
                        summary=summary
                    )

                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix='.pdf'
                    ) as tmp:

                        pdf.output(tmp.name)

                        with open(
                            tmp.name,
                            'rb'
                        ) as f:

                            st.download_button(
                                "📥 Download PDF",
                                f.read(),
                                file_name=(
                                    f"AI_Report_"
                                    f"{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                                ),
                                mime="application/pdf"
                            )

                    st.success(
                        "✅ PDF berhasil dibuat!"
                    )

                except Exception as e:

                    st.error(f"❌ {e}")


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    ai_insights_page()
