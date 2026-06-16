import streamlit as st
import pandas as pd
import io
from datetime import datetime, timezone, timedelta
from supabase_db import read_all_sheets

def export_report_page():
    # ─────────────────────────────────────────────────────────────
    # 📱 PREMIUM CSS FOR METRICS & TABLES
    # ─────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .metric-container {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-val { font-size: 24px; font-weight: 800; margin: 5px 0; }
    .metric-lbl { font-size: 12px; opacity: 0.85; font-weight: 600; }
    @media (max-width: 768px) {
        .stColumn { width: 100% !important; margin-bottom: 10px; }
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Export Report Center")
    st.markdown("Analisis kumulatif operational site, pencapaian milestone, dan audit logistik material sebelum diunduh.")

    # ─────────────────────────────────────────────────────────────
    # 📥 LOAD & CLEAN DATA FROM SUPABASE
    # ─────────────────────────────────────────────────────────────
    try:
        with st.spinner("🔄 Sinkronisasi Basis Data Supabase..."):
            all_data = read_all_sheets()
        projects_df = all_data.get('projects', pd.DataFrame())
        milestones_df = all_data.get('milestones', pd.DataFrame())
        materials_df = all_data.get('materials', pd.DataFrame())
        transactions_df = all_data.get('inventory_transactions', pd.DataFrame())
        master_projects_df = all_data.get('master_projects', pd.DataFrame())
    except Exception as e:
        st.error(f"⚠️ Gagal memuat data: {str(e)[:100]}")
        return

    if projects_df.empty:
        st.info("📋 Database kosong atau tidak terhubung dengan benar.")
        return

    # Data Type Safety Pre-process
    if 'progress' in projects_df.columns:
        projects_df['progress'] = pd.to_numeric(projects_df['progress'], errors='coerce').fillna(0)
    if not milestones_df.empty and 'progress' in milestones_df.columns:
        milestones_df['progress'] = pd.to_numeric(milestones_df['progress'], errors='coerce').fillna(0)
    if not milestones_df.empty and 'weight' in milestones_df.columns:
        milestones_df['weight'] = pd.to_numeric(milestones_df['weight'], errors='coerce').fillna(0)

    # ─────────────────────────────────────────────────────────────
    # 🔍 FILTER PANEL LAYER 1 & 2 (CONNECTED COUPLING)
    # ─────────────────────────────────────────────────────────────
    st.subheader("🔍 Panel Kontrol & Filter Audit")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        master_opts = ["🌍 SEMUA MASTER PROJECT"]
        if not master_projects_df.empty and 'project_name' in master_projects_df.columns:
            master_opts += sorted(master_projects_df['project_name'].dropna().unique().tolist())
        elif 'master_project_id' in projects_df.columns:
            master_opts += sorted(projects_df['master_project_id'].dropna().unique().tolist())
            
        sel_master = st.selectbox("🌐 Pilih Master Project Induk", master_opts, key="exp_master")

    # Step Filtering Berantai Tahap 1
    proj_filtered_step1 = projects_df.copy()
    if sel_master != "🌍 SEMUA MASTER PROJECT":
        if not master_projects_df.empty and 'project_name' in master_projects_df.columns:
            m_ids = master_projects_df[master_projects_df['project_name'] == sel_master]['id'].tolist()
            proj_filtered_step1 = proj_filtered_step1[proj_filtered_step1['master_project_id'].isin(m_ids)]
        else:
            proj_filtered_step1 = proj_filtered_step1[proj_filtered_step1['master_project_id'] == sel_master]

    with col_f2:
        site_opts = ["📍 SEMUA SITE"]
        if not proj_filtered_step1.empty:
            col_site_name = 'site_name' if 'site_name' in proj_filtered_step1.columns else ('name' if 'name' in proj_filtered_step1.columns else 'id')
            site_opts += sorted(proj_filtered_step1[col_site_name].dropna().unique().tolist())
            
        sel_site = st.selectbox("📍 Filter Spesifik Berdasarkan Nama Site", site_opts, key="exp_site_name")

    # Step Filtering Berantai Tahap 2
    final_filtered_proj = proj_filtered_step1.copy()
    if sel_site != "📍 SEMUA SITE":
        col_site_name = 'site_name' if 'site_name' in final_filtered_proj.columns else ('name' if 'name' in final_filtered_proj.columns else 'id')
        final_filtered_proj = final_filtered_proj[final_filtered_proj[col_site_name] == sel_site]

    # Kunci ID Kunci untuk Memotong Tabel Anak
    valid_site_ids = final_filtered_proj['id'].tolist()
    final_filtered_ms = milestones_df[milestones_df['project_id'].isin(valid_site_ids)] if not milestones_df.empty else pd.DataFrame()
    final_filtered_trans = transactions_df[transactions_df['project_id'].isin(valid_site_ids)] if not transactions_df.empty else pd.DataFrame()

    # ─────────────────────────────────────────────────────────────
    # 📈 STATUS AGREGASI UTAMA (METRIC CARDS)
    # ─────────────────────────────────────────────────────────────
    st.markdown("---")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    if sel_master != "🌍 SEMUA MASTER PROJECT":
        count_project = 1
    else:
        count_project = final_filtered_proj['master_project_id'].nunique() if 'master_project_id' in final_filtered_proj.columns else 1
        
    count_site = len(final_filtered_proj)
    count_task = len(final_filtered_ms)
    avg_total_progress = final_filtered_proj['progress'].mean() if 'progress' in final_filtered_proj.columns else 0.0

    with m_col1:
        st.markdown(f'<div class="metric-container"><div class="metric-val">{count_project}</div><div class="metric-lbl">📊 TOTAL MASTER PROJECT</div></div>', unsafe_allow_html=True)
    with m_col2:
        st.markdown(f'<div class="metric-container"><div class="metric-val">{count_site}</div><div class="metric-lbl">📍 TOTAL SITE OPERASIONAL</div></div>', unsafe_allow_html=True)
    with m_col3:
        st.markdown(f'<div class="metric-container"><div class="metric-val">{count_task}</div><div class="metric-lbl">🧱 TOTAL TASK / MILESTONE</div></div>', unsafe_allow_html=True)
    with m_col4:
        st.markdown(f'<div class="metric-container"><div class="metric-val">{avg_total_progress:.1f}%</div><div class="metric-lbl">📈 RATARATA PROGRESS SITE</div></div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────
    # 🧱 TABEL 1: RATA-RATA PROGRESS TIAP-TIAP MILESTONE TASK
    # ─────────────────────────────────────────────────────────────
    st.markdown("### 🧱 Rata-rata Progress Tiap-Tiap Milestone Tasks")
    if not final_filtered_ms.empty and 'name' in final_filtered_ms.columns:
        ms_summary = final_filtered_ms.groupby('name').agg(
            Jumlah_Task=('id', 'count'),
            Ratarata_Bobot_Tugas=('weight', lambda x: f"{x.mean():.1f}%"),
            Ratarata_Progress_Capaian=('progress', lambda x: f"{x.mean():.1f}%")
        ).reset_index()
        
        ms_summary.columns = ["Nama Kategori Milestone / Task Work", "Volume Distribusi Task", "Rata-rata Bobot Kontribusi", "Rata-rata Capaian Progress"]
        st.dataframe(ms_summary, use_container_width=True, hide_index=True)
    else:
        st.info("🧱 Belum ada data pencapaian milestone untuk ruang lingkup filter ini.")

    # ─────────────────────────────────────────────────────────────
    # 📦 TABEL 2: REKONSILIASI MATERIAL KONSOLIDASIAN
    # ─────────────────────────────────────────────────────────────
    st.markdown("### 📦 Rekonsiliasi Tata Kelola & Status Logistik Material")
    if not final_filtered_trans.empty:
        # Deteksi nama kolom teks utama barang
        col_item_desc = 'item_description' if 'item_description' in final_filtered_trans.columns else (
                        'item_name' if 'item_name' in final_filtered_trans.columns else (
                        'item_code' if 'item_code' in final_filtered_trans.columns else final_filtered_trans.columns[0]))
        
        # Deteksi aman kolom angka volume
        col_req = next((c for c in ['qty_requested', 'qty_request', 'request_qty'] if c in final_filtered_trans.columns), None)
        col_rel = next((c for c in ['qty_released', 'release_qty', 'quantity', 'qty'] if c in final_filtered_trans.columns), None)
        col_usd = next((c for c in ['qty_used', 'used_qty', 'qty_pemakaian'] if c in final_filtered_trans.columns), None)
        
        if not col_rel and col_usd: col_rel = col_usd
        if not col_usd and col_rel: col_usd = col_rel

        # Bangun paket grup agregasi dinamis
        agg_dict = {}
        if col_req: 
            agg_dict['Total_Qty_Request'] = (col_req, 'sum')
        
        if col_rel == col_usd and col_rel is not None:
            agg_dict['Total_Qty_Release'] = (col_rel, 'sum')
            agg_dict['Total_Qty_Used'] = (col_rel, 'sum')
        else:
            if col_rel: agg_dict['Total_Qty_Release'] = (col_rel, 'sum')
            if col_usd: agg_dict['Total_Qty_Used'] = (col_usd, 'sum')
        
        # Eksekusi kalkulasi tabel
        try:
            mat_summary = final_filtered_trans.groupby(col_item_desc).agg(**agg_dict).reset_index()
        except Exception:
            mat_summary = final_filtered_trans.groupby(col_item_desc).size().reset_index(name='Total_Transaksi')
            mat_summary['Total_Qty_Request'] = mat_summary['Total_Transaksi']
            mat_summary['Total_Qty_Release'] = mat_summary['Total_Transaksi']
            mat_summary['Total_Qty_Used'] = mat_summary['Total_Transaksi']

        # Antisipasi kolom kosong agar aman diproses matematika
        if 'Total_Qty_Request' not in mat_summary.columns:
            mat_summary['Total_Qty_Request'] = mat_summary['Total_Qty_Release'] if 'Total_Qty_Release' in mat_summary.columns else 0
        if 'Total_Qty_Release' not in mat_summary.columns: mat_summary['Total_Qty_Release'] = 0
        if 'Total_Qty_Used' not in mat_summary.columns: mat_summary['Total_Qty_Used'] = 0
            
        # FORCE CASTING KE NUMERIK KETAT (Mencegah PyArrow Engine Error)
        mat_summary['Total_Qty_Request'] = pd.to_numeric(mat_summary['Total_Qty_Request'], errors='coerce').fillna(0)
        mat_summary['Total_Qty_Release'] = pd.to_numeric(mat_summary['Total_Qty_Release'], errors='coerce').fillna(0)
        mat_summary['Total_Qty_Used'] = pd.to_numeric(mat_summary['Total_Qty_Used'], errors='coerce').fillna(0)
        
        # Eksekusi hitung selisih sisa sediaan
        mat_summary['Balance_Sisa_Qty'] = mat_summary['Total_Qty_Release'] - mat_summary['Total_Qty_Used']
        
        # Logika pembacaan status audit
        status_list = []
        for _, r in mat_summary.iterrows():
            b_val = r.get('Balance_Sisa_Qty', 0)
            if b_val > 0: status_list.append("🟢 SURPLUS / SISA")
            elif b_val < 0: status_list.append("🔴 MINUS / DEFISIT")
            else: status_list.append("🔵 SETTLED / BALANCE")
        mat_summary['Status_Audit_Finansial'] = status_list
        
        # Potong dan bersihkan susunan display table
        final_cols = [col_item_desc, "Total_Qty_Request", "Total_Qty_Release", "Total_Qty_Used", "Balance_Sisa_Qty", "Status_Audit_Finansial"]
        mat_display = mat_summary[final_cols].copy()
        mat_display.columns = ["Deskripsi Material", "Qty Requested", "Qty Released", "Qty Used / Installed", "Balance Qty", "Status Audit Keuangan"]
        
        st.dataframe(mat_display, use_container_width=True, hide_index=True)
    else:
        st.info("📦 Tidak ditemukan mutasi transaksi material (inventory_transactions) pada cakupan site terfilter.")

    # ─────────────────────────────────────────────────────────────
    # 📥 DOWNLOAD BUTTON GENERATOR
    # ─────────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("📥 Unduh Hasil Konsolidasi Data ke File Excel", type="primary", use_container_width=True):
        with st.spinner("🔄 Menyusun arsip multi-sheet xlsx..."):
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    meta_df = pd.DataFrame([
                        ["Waktu Cetak Laporan", datetime.now(timezone(timedelta(hours=7))).strftime('%d/%m/%Y %H:%M WIB')],
                        ["Filter Master Project", sel_master],
                        ["Filter Nama Site", sel_site],
                        ["Total Site Terdampak", count_site]
                    ], columns=["Parameter Audit", "Value"])
                    meta_df.to_excel(writer, sheet_name='Ringkasan_Meta', index=False)
                    
                    if 'ms_summary' in locals() and not ms_summary.empty:
                        ms_summary.to_excel(writer, sheet_name='Summary_Progress_Milestone', index=False)
                    if 'mat_display' in locals() and not mat_display.empty:
                        mat_display.to_excel(writer, sheet_name='Summary_Logistik_Material', index=False)
                        
                output.seek(0)
                site_slug = sel_site.replace(" ", "_") if sel_site != "📍 SEMUA SITE" else "All_Sites"
                st.download_button(
                    label="⬇️ KLIK DI SINI UNTUK SAVE FILE EXCEL",
                    data=output,
                    file_name=f"Audit_Report_{site_slug}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success("✅ File siap diunduh! Klik tombol di atas.")
            except Exception as e:
                st.error(f"❌ Gagal menyusun Excel: {str(e)}")

if __name__ == "__main__":
    export_report_page()
