import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from supabase_db import read_all_sheets, insert_row, generate_id, now_str

def rca_page():
    st.title("🔍 Root Cause Analysis (RCA)")
    st.caption("Analisis akar masalah keterlambatan berdasarkan metode 5-Why & Fishbone")
    
    all_data = read_all_sheets()
    ms_df = all_data.get('milestones', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    master_df = all_data.get('master_projects', pd.DataFrame())
    milestones_df = all_data.get('milestones', pd.DataFrame())

    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid_sites = df[df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
        df = df[df['id'].isin(valid_sites)]
        milestones_df = milestones_df[milestones_df['project_id'].isin(valid_sites)] if not milestones_df.empty else milestones_df
    
    if ms_df.empty:
        st.info("📋 Belum ada milestone.")
        return
    
    # Filter Project
    if not master_df.empty:
        master_options = ["ALL"] + master_df['id'].tolist()
        selected_master = st.selectbox("🏢 Filter Project:", master_options,
            format_func=lambda x: "🌐 SEMUA PROYEK" if x == "ALL" 
            else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}")
        if selected_master != "ALL":
            valid_sites = sites_df[sites_df['master_project_id'] == selected_master]['id'].tolist()
            ms_df = ms_df[ms_df['project_id'].isin(valid_sites)]

        # Filter Project
        # Filter Project
    if not master_df.empty:
        master_options = ["ALL"] + master_df['id'].tolist()
        selected_master = st.selectbox("🏢 Filter Project:", master_options,
            format_func=lambda x: "🌐 SEMUA PROYEK" if x == "ALL" 
            else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}")
        if selected_master != "ALL":
            valid_sites = sites_df[sites_df['master_project_id'] == selected_master]['id'].tolist()
            ms_df = ms_df[ms_df['project_id'].isin(valid_sites)]
    
    # Filter: hanya milestone DELAYED/CRITICAL
    delayed_ms = ms_df[ms_df['status'].isin(['DELAYED', 'CRITICAL'])].copy()
    
    if delayed_ms.empty:
        st.success("✅ Tidak ada milestone delayed — RCA tidak diperlukan!")
        return
    
    # Filter Site
    site_options = ["ALL SITE"] + delayed_ms['project_id'].unique().tolist()
    selected_site = st.selectbox("🎯 Filter Site:", site_options,
        format_func=lambda x: "ALL SITE" if x == "ALL SITE" 
        else f"{sites_df[sites_df['id']==x]['site_id'].values[0]}" if x in sites_df['id'].values else x)
    
    if selected_site != "ALL SITE":
        delayed_ms = delayed_ms[delayed_ms['project_id'] == selected_site]
    
    if delayed_ms.empty:
        st.success("✅ Tidak ada milestone delayed — RCA tidak diperlukan!")
        return
    
    # Merge data
    site_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    site_id_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    delayed_ms['site_name'] = delayed_ms['project_id'].map(site_map)
    delayed_ms['site_id_code'] = delayed_ms['project_id'].map(site_id_map)
    
    # Konversi tanggal
    delayed_ms['planned_end'] = pd.to_datetime(delayed_ms['planned_end'], errors='coerce')
    delayed_ms['delay_days'] = (datetime.now() - delayed_ms['planned_end']).dt.days
    
    st.divider()
    
    # ===== 1. FISHBONE DIAGRAM (Cause-Effect) =====
    st.header("🐟 1. Fishbone Diagram — Kategori Penyebab")
    
    if 'delay_reason' in delayed_ms.columns:
        reasons = delayed_ms[delayed_ms['delay_reason'].notna() & (delayed_ms['delay_reason'] != '') & (delayed_ms['delay_reason'] != 'Tidak Ada')]
        
        if not reasons.empty:
            # Kategorisasi
            categories = {
                "📦 Material": ['Material Terlambat'],
                "🌧️ Environment": ['Cuaca Buruk', 'Force Majeure'],
                "👷 Manpower": ['Manpower Kurang'],
                "🏢 Vendor": ['Vendor Terlambat'],
                "📋 Administrasi": ['Izin/Tanah'],
                "📐 Desain": ['Desain Berubah'],
                "❓ Lainnya": ['Lainnya']
            }
            
            # Hitung per kategori
            cat_counts = {}
            for cat, keywords in categories.items():
                count = 0
                for kw in keywords:
                    count += len(reasons[reasons['delay_reason'].str.contains(kw, case=False, na=False)])
                cat_counts[cat] = count
            
            # Buat Fishbone sederhana dengan bar chart horizontal
            cat_df = pd.DataFrame(list(cat_counts.items()), columns=['Kategori', 'Jumlah'])
            cat_df = cat_df[cat_df['Jumlah'] > 0].sort_values('Jumlah', ascending=True)
            
            if not cat_df.empty:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    fig = px.bar(cat_df, x='Jumlah', y='Kategori', orientation='h',
                               color='Jumlah', color_continuous_scale=['#ffc107', '#dc3545'],
                               title="Distribusi Kategori Penyebab")
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("📊 Detail per Kategori")
                    for _, row in cat_df.iterrows():
                        st.markdown(f"**{row['Kategori']}**: {row['Jumlah']} kejadian")
                    
                    # Top category
                    top_cat = cat_df.iloc[-1]
                    st.error(f"🔴 **Penyebab Utama: {top_cat['Kategori']}** — {top_cat['Jumlah']} milestone")
    else:
        st.info("ℹ️ Data delay_reason belum tersedia.")
    
    st.divider()
    
    # ===== 2. 5-WHY ANALYSIS =====
    st.header("❓ 2. 5-Why Analysis — Drill Down Akar Masalah")
    
    # Top 5 delayed milestones
    top_delayed = delayed_ms.nlargest(5, 'delay_days')
    
    for idx, (_, row) in enumerate(top_delayed.iterrows()):
        with st.expander(f"{idx+1}. {row['name']} — {row.get('site_id_code','?')} ({row['delay_days']} hari terlambat)", expanded=(idx==0)):
            st.markdown(f"**Task:** {row['name']}")
            st.markdown(f"**Site:** {row.get('site_id_code','?')} - {row.get('site_name','?')}")
            st.markdown(f"**PIC:** `{row.get('assigned_to','?')}`")
            st.markdown(f"**Delay Reason:** {row.get('delay_reason','Tidak diketahui')}")
            st.markdown(f"**Deadline:** {row['planned_end'].strftime('%d %b %Y') if pd.notna(row['planned_end']) else '?'}")
            
            # Auto 5-Why berdasarkan delay_reason
            st.markdown("---")
            st.markdown("**🤖 Auto 5-Why Analysis:**")
            
            reason = row.get('delay_reason', '')
            
            why_map = {
                "Material Terlambat": [
                    "1️⃣ **Kenapa?** Material terlambat datang",
                    "2️⃣ **Kenapa?** Supplier tidak ready stock",
                    "3️⃣ **Kenapa?** PO dibuat mendadak",
                    "4️⃣ **Kenapa?** Forecasting kebutuhan tidak akurat",
                    "5️⃣ **Kenapa?** Tidak ada buffer time dalam perencanaan procurement",
                    "💡 **Akar Masalah:** Perencanaan procurement tanpa buffer → **Solusi:** Tambah lead time 2 minggu + safety stock"
                ],
                "Cuaca Buruk": [
                    "1️⃣ **Kenapa?** Pekerjaan terhenti karena hujan",
                    "2️⃣ **Kenapa?** Tidak ada mitigasi cuaca",
                    "3️⃣ **Kenapa?** Jadwal tidak memperhitungkan musim hujan",
                    "4️⃣ **Kenapa?** Perencanaan hanya pakai kalender standar",
                    "5️⃣ **Kenapa?** Tidak ada data historis cuaca dalam planning",
                    "💡 **Akar Masalah:** Perencanaan tanpa data cuaca → **Solusi:** Integrasi data cuaca + jadwal alternatif indoor"
                ],
                "Manpower Kurang": [
                    "1️⃣ **Kenapa?** Tim tidak cukup orang",
                    "2️⃣ **Kenapa?** Subkontraktor tidak available",
                    "3️⃣ **Kenapa?** Kontrak subkon ditandatangani terlambat",
                    "4️⃣ **Kenapa?** Proses procurement vendor lama",
                    "5️⃣ **Kenapa?** Tidak ada vendor framework agreement",
                    "💡 **Akar Masalah:** Vendor management reaktif → **Solusi:** Framework agreement + vendor pool"
                ],
                "Vendor Terlambat": [
                    "1️⃣ **Kenapa?** Vendor tidak deliver tepat waktu",
                    "2️⃣ **Kenapa?** SLA tidak enforced",
                    "3️⃣ **Kenapa?** Tidak ada penalty clause",
                    "4️⃣ **Kenapa?** Kontrak tidak detail",
                    "5️⃣ **Kenapa?** Template kontrak standar tidak ada",
                    "💡 **Akar Masalah:** Kontrak tanpa SLA enforcement → **Solusi:** Standardisasi kontrak + penalty + monitoring dashboard"
                ],
                "Izin/Tanah": [
                    "1️⃣ **Kenapa?** Izin belum keluar",
                    "2️⃣ **Kenapa?** Dokumen tidak lengkap",
                    "3️⃣ **Kenapa?** Persyaratan berubah",
                    "4️⃣ **Kenapa?** Tidak ada komunikasi proaktif dengan regulator",
                    "5️⃣ **Kenapa?** Tidak ada PIC khusus untuk perizinan",
                    "💡 **Akar Masalah:** Manajemen perizinan tidak dedicated → **Solusi:** Tunjuk PIC izin + tracker dokumen"
                ],
            }
            
            default_why = [
                "1️⃣ **Kenapa?** Task terlambat",
                "2️⃣ **Kenapa?** Ada hambatan dalam eksekusi",
                "3️⃣ **Kenapa?** Resource tidak optimal",
                "4️⃣ **Kenapa?** Perencanaan tidak memperhitungkan risiko",
                "5️⃣ **Kenapa?** Tidak ada contingency plan",
                "💡 **Akar Masalah:** Perencanaan tanpa mitigasi risiko → **Solusi:** Tambah risk assessment + contingency buffer"
            ]
            
            whys = why_map.get(reason, default_why)
            for why in whys:
                st.markdown(why)
            
            # RCA Notes (bisa diedit user)
            st.markdown("---")
            rca_note = st.text_area("📝 Catatan RCA (opsional)", key=f"rca_{row['id']}", 
                                    placeholder="Tulis temuan RCA-mu di sini...")
            if st.button("💾 Simpan RCA", key=f"save_rca_{row['id']}"):
                insert_row("ai_insights", {
                    'id': generate_id(),
                    'project_id': row['project_id'],
                    'insight_type': 'RCA',
                    'risk_score': str(row['delay_days']),
                    'description': f"RCA: {row['name']} - {reason}",
                    'recommendation': rca_note if rca_note else whys[-1],
                    'created_at': now_str()
                })
                st.success("✅ RCA disimpan!")
    
    st.divider()
    
    # ===== 3. TREND ANALYSIS =====
    st.header("📈 3. Trend Keterlambatan")
    
    if not delayed_ms.empty:
        delayed_ms['month'] = delayed_ms['planned_end'].dt.to_period('M').astype(str)
        trend = delayed_ms.groupby('month').agg(
            total_delayed=('id', 'count'),
            avg_delay=('delay_days', 'mean')
        ).reset_index()
        
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(trend, x='month', y='total_delayed', 
                        title="Jumlah Milestone Delayed per Bulan",
                        color='total_delayed', color_continuous_scale='Reds')
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.line(trend, x='month', y='avg_delay', markers=True,
                         title="Rata-rata Hari Keterlambatan per Bulan")
            st.plotly_chart(fig2, use_container_width=True)
    
    st.divider()
    
    # ===== 4. REKOMENDASI =====
    st.header("💡 4. RCA Recommendations")
    
    recos = []
    
    # Analisis otomatis
    if 'delay_reason' in delayed_ms.columns:
        top_reasons = delayed_ms['delay_reason'].value_counts().head(3)
        for reason, count in top_reasons.items():
            if reason and reason != 'Tidak Ada':
                recos.append(f"🔴 **{reason}** ({count} kejadian) — Investigasi akar masalah di area ini")
    
    if 'assigned_to' in delayed_ms.columns:
        top_pic = delayed_ms['assigned_to'].value_counts().head(3)
        for pic, count in top_pic.items():
            if pic:
                recos.append(f"👤 **PIC {pic}** ({count} task delayed) — Evaluasi workload & capacity")
    
    if recos:
        for r in recos:
            st.markdown(r)
    else:
        st.success("✅ Tidak ada rekomendasi spesifik — data perlu dilengkapi.")
    
    # Export
    st.divider()
    csv = delayed_ms[['name', 'site_id_code', 'site_name', 'assigned_to', 'delay_reason', 'delay_days', 'planned_end']]
    csv.columns = ['Task', 'Site ID', 'Site Name', 'PIC', 'Delay Reason', 'Delay Days', 'Deadline']
    st.download_button("📥 Download RCA Data CSV", csv.to_csv(index=False), f"rca_report_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

if __name__ == "__main__":
    rca_page()
