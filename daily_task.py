import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from supabase_db import read_all_sheets, read_sheet

def daily_task_page():
    st.title("📋 Daily Task Heatmap")
    st.caption("Status Milestone per Site — Klik Site Name untuk detail")

    # 1. Load data
    all_data = read_all_sheets()
    ms_df = all_data.get("milestones", pd.DataFrame())
    sites_df = all_data.get("projects", pd.DataFrame())
    master_df = all_data.get("master_projects", pd.DataFrame())

    if ms_df.empty or sites_df.empty:
        st.info("📭 Belum ada data milestone atau site.")
        return

    # 2. Global filter
    if st.session_state.get("global_project_filter", "ALL") != "ALL":
        valid_sites = (
            sites_df[sites_df.get("master_project_id", "") == st.session_state.global_project_filter]["id"]
            .tolist()
        )
        sites_df = sites_df[sites_df["id"].isin(valid_sites)]
        ms_df = ms_df[ms_df["project_id"].isin(valid_sites)]

    # 3. Filter Baru
    st.markdown("### 🔍 Filter Data")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        sel_project = "ALL"
        if not master_df.empty:
            project_options = ["ALL"] + master_df["id"].tolist()
            sel_project = st.selectbox(
                "🏢 Master Project:",
                project_options,
                format_func=lambda x: "🌐 SEMUA"
                if x == "ALL"
                else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}",
                key="heat_project"
            )

    with col_f2:
        pm_list = ['ALL'] + sorted(sites_df['pm'].dropna().unique().tolist()) if 'pm' in sites_df.columns else ['ALL']
        sel_pm = st.selectbox("👤 PM:", pm_list, key="heat_pm")

    with col_f3:
        vendor_list = ['ALL'] + sorted(sites_df['vendor'].dropna().unique().tolist()) if 'vendor' in sites_df.columns else ['ALL']
        sel_vendor = st.selectbox("🏢 Vendor:", vendor_list, key="heat_vendor")

    with col_f4:
        site_list = ['ALL'] + sorted(sites_df['site_name'].dropna().unique().tolist()) if not sites_df.empty else ['ALL']
        sel_site = st.selectbox("📍 Site Name:", site_list, key="heat_site")

    # Apply filters
    if sel_project != "ALL" and not master_df.empty:
        valid_sites = sites_df[sites_df["master_project_id"] == sel_project]["id"].tolist()
        ms_df = ms_df[ms_df["project_id"].isin(valid_sites)]
        sites_df = sites_df[sites_df["id"].isin(valid_sites)]
    if sel_pm != 'ALL' and 'pm' in sites_df.columns:
        valid_sites = sites_df[sites_df['pm'] == sel_pm]['id'].tolist()
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)]
        sites_df = sites_df[sites_df['id'].isin(valid_sites)]
    if sel_vendor != 'ALL' and 'vendor' in sites_df.columns:
        valid_sites = sites_df[sites_df['vendor'] == sel_vendor]['id'].tolist()
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)]
        sites_df = sites_df[sites_df['id'].isin(valid_sites)]
    if sel_site != 'ALL':
        valid_sites = sites_df[sites_df['site_name'] == sel_site]['id'].tolist()
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)]
        sites_df = sites_df[sites_df['id'].isin(valid_sites)]

    if ms_df.empty:
        st.info("✅ Tidak ada milestone untuk filter ini.")
        return

    # 4. Summary total milestone
    total_ms = len(ms_df)
    done_ms = len(ms_df[ms_df['status'] == 'DONE'])
    delayed_ms = len(ms_df[ms_df['status'].isin(['DELAYED', 'CRITICAL'])])
    ongoing_ms = len(ms_df[ms_df['status'] == 'ONGOING'])
    pending_ms = len(ms_df[ms_df['status'] == 'PENDING'])

    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    col_s1.metric("📋 Total Milestone", total_ms)
    col_s2.metric("✅ Done", done_ms)
    col_s3.metric("🔄 On Going", ongoing_ms)
    col_s4.metric("⏳ Pending", pending_ms)
    col_s5.metric("🔴 Delayed", delayed_ms)

    # 5. Heatmap pivot
    site_map = dict(zip(sites_df["id"], sites_df["site_name"]))
    ms_df["site_name"] = ms_df["project_id"].map(site_map).fillna("-")

    pivot = ms_df.pivot_table(
        index="site_name",
        columns="name",
        values="status",
        aggfunc="first",
    )

    ms_df["planned_start"] = pd.to_datetime(ms_df["planned_start"], errors="coerce")
    milestone_order = ms_df.groupby("name")["planned_start"].min().sort_values().index.tolist()
    ordered_cols = [col for col in milestone_order if col in pivot.columns]
    pivot = pivot[ordered_cols]

    def color_status(val):
        if val == "DONE":
            return "background-color: #DCFCE7; color: #166534; font-weight: bold;"
        elif val == "ONGOING":
            return "background-color: #DBEAFE; color: #1E40AF; font-weight: bold;"
        elif val == "PENDING":
            return "background-color: #F1F5F9; color: #475569;"
        elif val in ("DELAYED", "CRITICAL"):
            return "background-color: #FEE2E2; color: #991B1B; font-weight: bold;"
        return ""

    styled = pivot.style.map(color_status)

    project_label = "Semua Project"
    if sel_project != "ALL" and not master_df.empty:
        match = master_df[master_df['id'] == sel_project]
        if not match.empty:
            project_label = match['project_name'].values[0]

    st.subheader(f"🔥 Heatmap Status Milestone — {project_label}")
    st.markdown("""
    <div style="display:flex; gap:20px; margin-bottom:10px;">
        <span style="background:#DCFCE7; padding:4px 12px; border-radius:4px; color:#166534;">✅ Done</span>
        <span style="background:#DBEAFE; padding:4px 12px; border-radius:4px; color:#1E40AF;">🔄 On Going</span>
        <span style="background:#F1F5F9; padding:4px 12px; border-radius:4px; color:#475569;">⏳ Pending</span>
        <span style="background:#FEE2E2; padding:4px 12px; border-radius:4px; color:#991B1B;">🔴 Delayed</span>
    </div>
    """, unsafe_allow_html=True)

    st.dataframe(styled, use_container_width=True)

    # 6. Detail pop-up ketika site dipilih
    if sel_site != 'ALL':
        st.divider()
        st.subheader(f"🔍 Detail Site: {sel_site}")

        site_id = sites_df[sites_df['site_name'] == sel_site]['id'].values[0]
        site_ms = ms_df[ms_df['project_id'] == site_id].copy()

        if not site_ms.empty:
            # Timeline Plan vs Actual
            site_ms['planned_start'] = pd.to_datetime(site_ms['planned_start'], errors='coerce')
            site_ms['planned_end'] = pd.to_datetime(site_ms['planned_end'], errors='coerce')
            site_ms['actual_start'] = pd.to_datetime(site_ms['actual_start'], errors='coerce')
            site_ms['actual_end'] = pd.to_datetime(site_ms['actual_end'], errors='coerce')

            st.markdown("#### 📅 Timeline Plan vs Actual")
            timeline_data = []
            for _, m in site_ms.iterrows():
                timeline_data.append({
                    'Milestone': m['name'],
                    'Plan Start': m['planned_start'].strftime('%d %b') if pd.notna(m['planned_start']) else '-',
                    'Plan End': m['planned_end'].strftime('%d %b') if pd.notna(m['planned_end']) else '-',
                    'Actual Start': m['actual_start'].strftime('%d %b') if pd.notna(m['actual_start']) else '-',
                    'Actual End': m['actual_end'].strftime('%d %b') if pd.notna(m['actual_end']) else '-',
                    'Status': m['status'],
                    'Delay Reason': m.get('delay_reason', '') if m.get('delay_reason') not in ['', 'Tidak Ada'] else ''
                })
            st.dataframe(pd.DataFrame(timeline_data), use_container_width=True, hide_index=True)

            # Bottleneck Analysis
            st.markdown("#### ⚠️ Bottleneck Analysis")
            delayed_ms = site_ms[site_ms['status'].isin(['DELAYED', 'CRITICAL'])]
            if not delayed_ms.empty:
                for _, m in delayed_ms.iterrows():
                    reason = m.get('delay_reason', 'Tidak diketahui')
                    days_late = (datetime.now() - m['planned_end']).days if pd.notna(m['planned_end']) else 0
                    st.error(f"🔴 **{m['name']}** — {days_late} hari terlambat — Alasan: {reason}")
            else:
                st.success("✅ Tidak ada bottleneck (semua milestone on track)")

            # Tombol Send to Telegram
            st.markdown("#### 📤 Kirim Detail Site ke Telegram")
            telegram_col1, telegram_col2 = st.columns([2, 1])
            with telegram_col1:
                if st.button("📤 Kirim Detail Site ke Telegram", use_container_width=True):
                    # Ambil settings
                    settings_df = read_sheet("settings")
                    if not settings_df.empty:
                        bot_token = settings_df.iloc[0].get('telegram_bot_token', '')
                        chat_id_str = settings_df.iloc[0].get('telegram_chat_id', '')

                        if bot_token and chat_id_str:
                            import requests
                            # Buat pesan
                            msg = f"📋 *Detail Site: {sel_site}*\n"
                            msg += f"━━━━━━━━━━━━━━━━━\n"
                            for _, m in site_ms.iterrows():
                                icon = '✅' if m['status'] == 'DONE' else ('🔄' if m['status'] == 'ONGOING' else ('🔴' if m['status'] in ['DELAYED','CRITICAL'] else '⏳'))
                                msg += f"{icon} {m['name']} — {m['status']}\n"
                                if m.get('delay_reason') not in ['', 'Tidak Ada', None]:
                                    msg += f"   Alasan: {m['delay_reason']}\n"
                            msg += f"━━━━━━━━━━━━━━━━━\n📱 Powered by Soen"

                            # Kirim ke semua chat ID
                            chat_ids = [cid.strip() for cid in chat_id_str.split(',') if cid.strip()]
                            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                            success = 0
                            for cid in chat_ids:
                                res = requests.post(url, data={"chat_id": cid, "text": msg, "parse_mode": "Markdown"})
                                if res.status_code == 200:
                                    success += 1
                            if success > 0:
                                st.success(f"✅ Detail site dikirim ke {success} penerima!")
                            else:
                                st.error("❌ Gagal mengirim")
                        else:
                            st.error("❌ Bot Token atau Chat ID belum diatur di Settings")
                    else:
                        st.error("❌ Settings tidak ditemukan")
            with telegram_col2:
                st.caption("💡 Kirim detail site ke Telegram Group/Individu yang terdaftar di Settings")

if __name__ == "__main__":
    daily_task_page()
