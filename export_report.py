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

    # Step Filtering Berantai Tahap 1 (Saring Project List berdasarkan Master Project)
    proj_filtered_step1 = projects_df.copy()
    if sel_master != "🌍 SEMUA MASTER PROJECT":
        if not master_projects_df.empty and 'project_name' in master_projects_df.columns:
            m_ids = master_projects_df[master_projects_df['project_name'] == sel_master]['id'].tolist()
            proj_filtered_step1 = proj_filtered_step1[proj_filtered_step1['master_project_id'].isin(m_ids)]
        else:
            proj_filtered_step1 = proj_filtered_step1[proj_filtered_step1['master_project_id'] == sel_master]

    with col_f2:
        # 🛠️ FITUR PERMINTAAN UTAMA: FILTER BY SITE NAME
        site_opts = ["📍 SEMUA SITE"]
        if not proj_filtered_step1.empty:
            # Gunakan 'site_name' jika ada, jika tidak ada fallback ke kolom 'name' atau 'id'
            col_site_name = 'site_name' if 'site_name' in proj_filtered_step1.columns else ('name' if 'name' in proj_filtered_step1.columns else 'id')
            site_opts += sorted(proj_filtered_step1[col_site_name].dropna().unique().tolist())
            
        sel_site = st.selectbox("📍 Filter Spesifik Berdasarkan Nama Site", site_opts, key="exp_site_name")

    # Step Filtering Berantai Tahap 2 (Saring Final Data Berdasarkan Nama Site)
    final_filtered_proj = proj_filtered_step1.copy()
    if sel_site != "📍 SEMUA SITE":
        col_site_name = 'site_name' if 'site_name' in final_filtered_proj.columns else ('name' if 'name' in final_filtered_proj.columns else 'id')
        final_filtered_proj = final_filtered_proj[final_filtered_proj[col_site_name] == sel_site]

    # Kunci ID Kunci untuk Memotong Tabel Anak (Milestone & Transaksi)
    valid_site_ids = final_filtered_proj['id'].tolist()
    final_filtered_ms = milestones_df[milestones_df['project_id'].isin(valid_site_ids)] if not milestones_df.empty else pd.DataFrame()
    final_filtered_trans = transactions_df[transactions_df['project_id'].isin(valid_site_ids)] if not transactions_df.empty else pd.DataFrame()

    # ─────────────────────────────────────────────────────────────
    # 📈 STATUS AGREGASI UTAMA (METRIC CARDS)
    # ─────────────────────────────────────────────────────────────
    st.markdown("---")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    # Hitung Jumlah Unik Master Project Terlibat
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
        # Lakukan groupby berdasarkan nama task/milestone dan hitung rata-rata progres beserta bobotnya
        ms_summary = final_filtered_ms.groupby('name').agg(
            Jumlah_Task=('id', 'count'),
            Ratarata_Bobot_Tugas=('weight', lambda x: f"{x.mean():.1f}%"),
            Ratarata_Progress_Capaian=('progress', lambda x: f"{x.mean():.1f}%")
        ).reset_index()
        
        # Rapikan nama kolom display
        ms_summary.columns = ["Nama Kategori Milestone / Task Work", "Volume Distribusi Task", "Rata-rata Bobot Kontribusi", "Rata-rata Capaian Progress"]
        st.dataframe(ms_summary, use_container_width=True, hide_index=True)
    else:
        st.info("🧱 Belum ada data pencapaian milestone untuk ruang lingkup filter ini.")

    # ─────────────────────────────────────────────────────────────
    # 📦 TABEL 2: REKONSILIASI MATERIAL KONSOLIDASIAN (ANTI-ERROR KEYERROR)
    # ─────────────────────────────────────────────────────────────
    st.markdown("### 📦 Rekonsiliasi Tata Kelola & Status Logistik Material")
    if not final_filtered_trans.empty:
        # 1. Deteksi cerdas nama kolom deskripsi/nama barang
        col_item_desc = 'item_description' if 'item_description' in final_filtered_trans.columns else (
                        'item_name' if 'item_name' in final_filtered_trans.columns else (
                        'item_code' if 'item_code' in final_filtered_trans.columns else final_filtered_trans.columns[0]))
        
        # 2. Deteksi dinamis kolom volume kuantitas untuk menghindari KeyError
        col_req = next((c for c in ['qty_requested', 'qty_request', 'request_qty'] if c in final_filtered_trans.columns), None)
        col_rel = next((c for c in ['qty_released', 'release_qty', 'quantity', 'qty'] if c in final_filtered_trans.columns), None)
        col_usd = next((c for c in ['qty_used', 'used_qty', 'qty_pemakaian'] if c in final_filtered_trans.columns), None)
        
        # Fallback jika qty_used tidak ada, pakai kolom release yang sama (atau sebaliknya) agar program tidak crash
        if not col_rel and col_usd: col_rel = col_usd
        if not col_usd and col_rel: col_usd = col_rel
        if not col_rel: 
            # Jika benar-benar tidak ada kolom angka sama sekali, pakai kolom numerik pertama yang tersedia
            numerics = final_filtered_trans.select_dtypes(include=['number']).columns
            col_rel = col_usd = numerics[0] if len(numerics) > 0 else final_filtered_trans.columns[0]

        # 3. Bangun dictionary agregasi secara dinamis hanya jika kolomnya VALID terdeteksi
        # Menggunakan format tuple tunggal standar Pandas lama agar aman di semua versi Pandas (termasuk Python 3.14)
        agg_dict = {}
        if col_req and col_req in final_filtered_trans.columns:
            agg_dict['Total_Qty_Request'] = (col_req, 'sum')
        
        # Antisipasi jika nama kolom release dan used ternyata sama (misal sama-sama merujuk ke 'quantity')
        # Kita bedakan namanya agar Pandas tidak bingung saat mengeksekusi grup
        if col_rel == col_usd:
            agg_dict['Total_Qty_Release'] = (col_rel, 'sum')
            agg_dict['Total_Qty_Used'] = (col_rel, 'sum')
        else:
            if col_rel: agg_dict['Total_Qty_Release'] = (col_rel, 'sum')
            if col_usd: agg_dict['Total_Qty_Used'] = (col_usd, 'sum')
        
        # 4. Eksekusi Groupby dengan aman
        try:
            # Menggunakan sintaks .agg(nama_kolom_baru=(kolom_asal, fungsi)) yang super stabil
            mat_summary = final_filtered_trans.groupby(col_item_desc).agg(**agg_dict).reset_index()
        except Exception as agg_err:
            # Ultimate Fallback jika skema data Supabase benar-benar tidak terduga fungsinya
            st.warning(f"⚠️ Mode kompatibilitas aktif akibat variasi struktur kolom database.")
            mat_summary = final_filtered_trans.groupby(col_item_desc).size().reset_index(name='Total_Transaksi')
            mat_summary['Total_Qty_Request'] = mat_summary['Total_Transaksi']
            mat_summary['Total_Qty_Release'] = mat_summary['Total_Transaksi']
            mat_summary['Total_Qty_Used'] = mat_summary['Total_Transaksi']
            
        # 5. Jika kolom request tidak ada, samakan nilainya dengan release agar tidak kosong
        if 'Total_Qty_Request' not in mat_summary.columns:
            mat_summary['Total_Qty_Request'] = mat_summary['Total_Qty_Release'] if 'Total_Qty_Release' in mat_summary.columns else 0
        if 'Total_Qty_Release' not in mat_summary.columns: mat_summary['Total_Qty_Release'] = 0
        if 'Total_Qty_Used' not in mat_summary.columns: mat_summary['Total_Qty_Used'] = 0
            
        # 6. Kalkulasi hitung status surplus/minus otomatis
        mat_summary['Balance_Sisa_Qty'] = mat_summary['Total_Qty_Release'] - mat_summary['Total_Qty_Used']
        
        def hitung_status_audit(row):
            bal = row.get('Balance_Sisa_Qty', 0)
            if bal > 0: return "🟢 SURPLUS / SISA"
            elif bal < 0: return "🔴 MINUS / DEFISIT"
            else: return "🔵 SETTLED / BALANCE"
            
        mat_summary['Status_Audit_Finansial'] = mat_summary.apply(hitung_status_audit, axis=1)
        
        # Susun ulang & rapikan nama kolom untuk konsumsi Direksi
        final_cols = [col_item_desc, "Total_Qty_Request", "Total_Qty_Release", "Total_Qty_Used", "Balance_Sisa_Qty", "Status_Audit_Finansial"]
        mat_summary_display = mat_summary[final_cols].copy()
        mat_summary_display.columns = ["Deskripsi Material", "Qty Requested", "Qty Released", "Qty Used / Installed", "Balance Qty", "Status Audit Keuangan"]
        
        st.dataframe(mat_summary_display, use_container_width=True, hide_index=True)
    else:
        st.info("📦 Tidak ditemukan mutasi transaksi material (inventory_transactions) pada cakupan site terfilter.")

    # ─────────────────────────────────────────────────────────────
    # 🚀 DOWNLOAD AUTOMATION PROCESS (MULTIPAGE PROFESSIONAL EXCEL)
    # ─────────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("📥 Unduh Hasil Konsolidasi Data ke File Excel", type="primary", use_container_width=True):
        with st.spinner("🔄 Menyusun arsip multi-sheet xlsx..."):
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    workbook = writer.book
                    
                    # Style presets
                    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#1E3A8A', 'font_color': 'white', 'border': 1, 'align': 'center'})
                    num_fmt = workbook.add_format({'num_format': '#,##0', 'border': 1, 'align': 'right'})
                    text_fmt = workbook.add_format({'border': 1, 'align': 'left'})
                    
                    # 1. Sheet Ringkasan KPI & Master Project
                    meta_df = pd.DataFrame([
                        ["Waktu Cetak Laporan", datetime.now(timezone(timedelta(hours=7))).strftime('%d/%m/%Y %H:%M WIB')],
                        ["Filter Master Project", sel_master],
                        ["Filter Nama Site", sel_site],
                        ["Total Site Terdampak", count_site],
                        ["Total Task Terdata", count_task]
                    ], columns=["Parameter Audit", "Value"])
                    meta_df.to_excel(writer, sheet_name='Ringkasan_Meta', index=False)
                    
                    # 2. Sheet Milestone Summary
                    if 'ms_summary' in locals() and not ms_summary.empty:
                        ms_summary.to_excel(writer, sheet_name='Summary_Progress_Milestone', index=False)
                    
                    # 3. Sheet Material Summary
                    if 'mat_summary' in locals() and not mat_summary.empty:
                        mat_summary.to_excel(writer, sheet_name='Summary_Logistik_Material', index=False)
                        
                    # Auto-format column layout
                    for sheet in writer.sheets:
                        ws = writer.sheets[sheet]
                        ws.set_column('A:Z', 22, text_fmt)
                        
                output.seek(0)
                
                # Setup Dynamic File Name
                site_slug = sel_site.replace(" ", "_") if sel_site != "📍 SEMUA SITE" else "All_Sites"
                filename = f"Audit_Report_{site_slug}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                
                st.download_button(
                    label="⬇️ KLIK DI SINI UNTUK SAVE FILE EXCEL",
                    data=output,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success("✅ File siap diunduh! Klik tombol di atas.")
            except Exception as e:
                st.error(f"❌ Gagal menyusun Excel: {str(e)}")

if __name__ == "__main__":
    export_report_page()
