import streamlit as st
import pandas as pd
import io
from datetime import datetime, timezone, timedelta
from supabase_db import read_all_sheets

def export_report_page():
    # ─────────────────────────────────────────────────────────────
    # 📱 MOBILE OPTIMIZATION CSS
    # ─────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .stColumn { width: 100% !important; margin-bottom: 10px; }
        button, input, select, textarea { min-height: 44px !important; font-size: 16px !important; }
        .report-type-selector div[role="radiogroup"] { flex-direction: column !important; gap: 8px; }
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Export Report Center")
    st.markdown("Unduh laporan proyek dalam format Excel terstruktur tingkat tinggi, siap untuk audit & meeting direksi.")

    # ─────────────────────────────────────────────────────────────
    # 📥 LOAD & CLEAN DATA
    # ─────────────────────────────────────────────────────────────
    try:
        with st.spinner("🔄 Memuat database terintegrasi..."):
            all_data = read_all_sheets()
        projects_df = all_data.get('projects', pd.DataFrame())
        milestones_df = all_data.get('milestones', pd.DataFrame())
        materials_df = all_data.get('materials', pd.DataFrame())
        transactions_df = all_data.get('inventory_transactions', pd.DataFrame())
        master_projects_df = all_data.get('master_projects', pd.DataFrame())
    except Exception as e:
        st.error(f"⚠️ Gagal memuat data dari Supabase: {str(e)[:100]}")
        return

    if projects_df.empty:
        st.info("📋 Belum ada data untuk diekspor. Silakan hubungkan database atau tambahkan site terlebih dahulu.")
        return

    # Pembersihan & Konversi Tipe Data Dasar
    if 'progress' in projects_df.columns:
        projects_df['progress'] = pd.to_numeric(projects_df['progress'], errors='coerce').fillna(0)
    
    date_cols = ['planned_start', 'planned_end', 'actual_start', 'actual_end', 'transaction_date']
    for df in [milestones_df, transactions_df, projects_df]:
        if not df.empty:
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

    # ─────────────────────────────────────────────────────────────
    # 🔍 FILTER PANEL (6 FILTER BERANTAI / CONNECTED FILTERING)
    # ─────────────────────────────────────────────────────────────
    st.subheader("🔍 Filter Cakupan Laporan Audit")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        master_opts = ["🌍 SEMUA MASTER PROJECT"]
        if not master_projects_df.empty and 'project_name' in master_projects_df.columns:
            master_opts += sorted(master_projects_df['project_name'].dropna().unique().tolist())
        elif 'master_project_id' in projects_df.columns:
            master_opts += sorted(projects_df['master_project_id'].dropna().unique().tolist())
            
        sel_master = st.selectbox("Master Project Induk", master_opts, key="exp_master")
        
    with col_f2:
        # Default rentang 30 hari ke belakang hingga hari ini
        default_start = datetime.now().date() - timedelta(days=30)
        date_range = st.date_input("Periode Target Selesai", value=(default_start, datetime.now().date()), key="exp_date")
        
    with col_f3:
        status_opts = projects_df['status'].dropna().unique().tolist() if 'status' in projects_df.columns else ['ON_TRACK', 'DELAYED', 'CRITICAL', 'DONE']
        sel_status = st.multiselect("Filter Status Operasional Site", status_opts, default=status_opts, key="exp_status")

    # ─────────────────────────────────────────────────────────────
    # 🧠 PROCESS FILTER INDUK & ANAK TABEL
    # ─────────────────────────────────────────────────────────────
    filtered_proj = projects_df.copy()
    
    # Eksekusi Filter Master Project
    if sel_master != "🌍 SEMUA MASTER PROJECT":
        if not master_projects_df.empty and 'project_name' in master_projects_df.columns:
            m_ids = master_projects_df[master_projects_df['project_name'] == sel_master]['id'].tolist()
            filtered_proj = filtered_proj[filtered_proj['master_project_id'].isin(m_ids)]
        else:
            filtered_proj = filtered_proj[filtered_proj['master_project_id'] == sel_master]
        
    # Eksekusi Filter Status
    if sel_status:
        filtered_proj = filtered_proj[filtered_proj['status'].isin(sel_status)]
        
    # Kunci ID Site yang Valid Hasil Filter untuk Memotong Tabel Transaksi & Milestone
    valid_site_ids = filtered_proj['id'].tolist()
    
    filtered_ms = milestones_df[milestones_df['project_id'].isin(valid_site_ids)] if not milestones_df.empty else pd.DataFrame()
    filtered_trans = transactions_df[transactions_df['project_id'].isin(valid_site_ids)] if not transactions_df.empty else pd.DataFrame()
    
    # Filter Rentang Tanggal Target Kerja (Milestones)
    if not filtered_ms.empty and 'planned_end' in filtered_ms.columns and len(date_range) == 2:
        start_dt, end_dt = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        filtered_ms = filtered_ms[(filtered_ms['planned_end'] >= start_dt) & (filtered_ms['planned_end'] <= end_dt)]

    # ─────────────────────────────────────────────────────────────
    # 📑 SELEKSI JENIS LAPORAN (PENAMBAHAN FITUR AUDIT INTEGRASI UTUH)
    # ─────────────────────────────────────────────────────────────
    st.subheader("📑 Pilih Jenis Laporan Ekspor")
    report_type = st.radio(
        "Format Output Dokumen:",
        ["📋 Comprehensive Project Audit Report (Rekomendasi Manajerial)", "📈 Executive Summary Overview", "🧱 Detail Kemajuan Milestone Tasks", "📦 Logistik & Transaksi Gudang Lapangan"],
        horizontal=True,
        key="exp_type"
    )

    # ─────────────────────────────────────────────────────────────
    # 👁️ PREVIEW DATA SAMPEL BEFORE DOWNLOAD
    # ─────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 👁️ Preview Data Terkait (Sampel 5 Baris)")
    tab_prev1, tab_prev2, tab_prev3 = st.tabs(["📌 Ringkasan Site Terfilter", "🧱 Rencana Kerja / Task", "📦 Transaksi Material Terkait"])
    
    with tab_prev1:
        st.dataframe(filtered_proj.head(5), use_container_width=True, hide_index=True)
        st.caption(f"Menampilkan 5 dari total {len(filtered_proj)} site aktif hasil filter saat ini.")
    with tab_prev2:
        if not filtered_ms.empty:
            st.dataframe(filtered_ms[['project_id', 'name', 'weight', 'progress', 'assigned_to', 'planned_end']].head(5), use_container_width=True, hide_index=True)
        else:
            st.info("Tidak ada task kerja/milestone yang jatuh pada periode tanggal yang dipilih.")
    with tab_prev3:
        if not filtered_trans.empty:
            st.dataframe(filtered_trans.head(5), use_container_width=True, hide_index=True)
        else:
            st.info("Tidak ditemukan data riwayat pengeluaran barang/logistik untuk site terfilter saat ini.")

    # ─────────────────────────────────────────────────────────────
    # 🚀 ENGINE GENERATOR AUTOMATION (XLSXWRITER PRESET)
    # ─────────────────────────────────────────────────────────────
    st.divider()
    if st.button("🚀 Bangun & Download Laporan Excel", type="primary", use_container_width=True):
        with st.spinner("🔄 Memproses penyatuan tabel silang & injeksi formula audit..."):
            try:
                output = io.BytesIO()
                
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    workbook = writer.book
                    
                    # 🎉 PRESET STYLING PREMIUM LAYOUT EXCEL
                    header_fmt = workbook.add_format({
                        'bold': True, 'bg_color': '#1E40AF', 'font_color': 'white', 
                        'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 11
                    })
                    sub_header_fmt = workbook.add_format({
                        'bold': True, 'bg_color': '#3B82F6', 'font_color': 'white', 
                        'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 10
                    })
                    meta_title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#1E40AF'})
                    meta_cell_label = workbook.add_format({'bold': True, 'bg_color': '#F3F4F6', 'border': 1})
                    meta_cell_val = workbook.add_format({'border': 1})
                    
                    # Format data reguler
                    num_fmt = workbook.add_format({'num_format': '#,##0', 'border': 1, 'align': 'right'})
                    pct_fmt = workbook.add_format({'num_format': '0.0%', 'border': 1, 'align': 'right'})
                    text_fmt = workbook.add_format({'border': 1, 'align': 'left'})
                    center_fmt = workbook.add_format({'border': 1, 'align': 'center'})
                    
                    # Highlight Conditional Rules Color Pastel
                    surplus_fmt = workbook.add_format({'bg_color': '#DCFCE7', 'font_color': '#15803D', 'border': 1, 'align': 'center', 'bold': True})
                    minus_fmt = workbook.add_format({'bg_color': '#FEE2E2', 'font_color': '#B91C1C', 'border': 1, 'align': 'center', 'bold': True})
                    settled_fmt = workbook.add_format({'bg_color': '#EFF6FF', 'font_color': '#1D4ED8', 'border': 1, 'align': 'center'})

                    # ⏳ AMBIL WAKTU LIVE WIB FOR REPORT TIME
                    tz_wib = timezone(timedelta(hours=7))
                    waktu_cetak = datetime.now(tz_wib).strftime('%d/%m/%Y %H:%M')

                    # ─────────────────────────────────────────────────────────
                    # 📑 STRATEGI 1: PEMBUATAN LAPORAN UTUH (COMPREHENSIVE AUDIT)
                    # ─────────────────────────────────────────────────────────
                    if "Comprehensive" in report_type:
                        audit_rows = []
                        
                        # Looping menyisir baris per baris secara berantai untuk menjamin keutuhan data
                        for _, site in filtered_proj.iterrows():
                            sid = site['id']
                            sname = site.get('site_name', 'N/A')
                            sstatus = site.get('status', 'N/A')
                            sprogress = site.get('progress', 0) / 100.0
                            sregion = site.get('region', 'N/A')
                            svendor = site.get('vendor_name', 'N/A')
                            
                            # Cari nama master project induknya
                            m_name = "N/A"
                            if not master_projects_df.empty and 'master_project_id' in site:
                                match_mp = master_projects_df[master_projects_df['id'] == site['master_project_id']]
                                if not match_mp.empty:
                                    m_name = match_mp['project_name'].values[0]

                            # 1. Tarik semua anak task (milestones) milik site ini
                            site_ms = filtered_ms[filtered_ms['project_id'] == sid] if not filtered_ms.empty else pd.DataFrame()
                            # 2. Tarik semua mutasi logistik material milik site ini
                            site_trans = filtered_trans[filtered_trans['project_id'] == sid] if not filtered_trans.empty else pd.DataFrame()
                            
                            max_loop = max(len(site_ms), len(site_trans), 1)
                            
                            # Satukan data secara baris sejajar (Flat Table Grid) agar mudah di-Pivot Direksi
                            for i in range(max_loop):
                                row_data = {
                                    "Master Project": m_name,
                                    "Site ID": sid,
                                    "Nama Site": sname,
                                    "Wilayah Region": sregion,
                                    "Vendor Pelaksana": svendor,
                                    "Status Utama Site": sstatus,
                                    "Total Progress Site": sprogress,
                                    
                                    # Data Bagian Task Kerja (Milestones)
                                    "Nama Task Kerja": "N/A",
                                    "Bobot Tugas": 0.0,
                                    "Capaian Task": 0.0,
                                    "PIC Lapangan": "N/A",
                                    
                                    # Data Bagian Logistik & Keuangan Material
                                    "Kode Barang": "N/A",
                                    "Deskripsi Material": "N/A",
                                    "Qty Released": 0.0,
                                    "Qty Used / Installed": 0.0,
                                    "Balance Qty": 0.0,
                                    "Status Audit Finansial": "NO MATERIAL"
                                }
                                
                                # Isi Kolom Task jika datanya ada
                                if i < len(site_ms):
                                    ms_row = site_ms.iloc[i]
                                    row_data["Nama Task Kerja"] = ms_row.get('name', 'N/A')
                                    row_data["Bobot Tugas"] = (ms_row.get('weight', 0) if ms_row.get('weight') is not None else 0) / 100.0
                                    row_data["Capaian Task"] = (ms_row.get('progress', 0) if ms_row.get('progress') is not None else 0) / 100.0
                                    row_data["PIC Lapangan"] = ms_row.get('assigned_to', 'N/A')
                                    
                                # Isi Kolom Logistik jika datanya ada & hitung SURPLUS/MINUS otomatis
                                if i < len(site_trans):
                                    trans_row = site_trans.iloc[i]
                                    qty_rel = float(trans_row.get('qty_released', 0) if trans_row.get('qty_released') is not None else 0)
                                    qty_used = float(trans_row.get('qty_used', 0) if trans_row.get('qty_used') is not None else trans_row.get('quantity', 0)) # Fallback support
                                    balance = qty_rel - qty_used
                                    
                                    # Logika bisnis penentuan status sisa barang di lapangan
                                    if balance > 0:
                                        status_audit = "SURPLUS / SISA"
                                    elif balance < 0:
                                        status_audit = "MINUS / DEFISIT"
                                    else:
                                        status_audit = "SETTLED / BALANCE"
                                        
                                    row_data["Kode Barang"] = trans_row.get('item_code', 'N/A')
                                    row_data["Deskripsi Material"] = trans_row.get('item_description', trans_row.get('item_name', 'N/A'))
                                    row_data["Qty Released"] = qty_rel
                                    row_data["Qty Used / Installed"] = qty_used
                                    row_data["Balance Qty"] = balance
                                    row_data["Status Audit Finansial"] = status_audit
                                    
                                audit_rows.append(row_data)
                                
                        df_audit_final = pd.DataFrame(audit_rows)
                        
                        # Urutkan berdasarkan Master Project dan Site ID agar rapi struktural
                        if not df_audit_final.empty:
                            df_audit_final = df_audit_final.sort_values(by=['Master Project', 'Site ID']).reset_index(drop=True)
                        
                        # 🏭 Tulis ke Sheet Utama
                        sheet_name = "Comprehensive_Audit"
                        df_audit_final.to_excel(writer, sheet_name=sheet_name, index=False)
                        worksheet = writer.sheets[sheet_name]
                        
                        # Berikan Desain Judul Laporan di Atas Grid Tabel
                        worksheet.freeze_panes(1, 0) # Freeze baris header pertama agar saat di-scroll ke bawah tetap kelihatan
                        
                        # Lakukan auto-formatting warna dan lebar kolom cerdas
                        for col_num, col_name in enumerate(df_audit_final.columns):
                            worksheet.write(0, col_num, col_name, header_fmt)
                            
                            # Atur format data spesifik per tipe kolom
                            if col_name in ["Total Progress Site", "Bobot Tugas", "Capaian Task"]:
                                worksheet.set_column(col_num, col_num, 15, pct_fmt)
                            elif col_name in ["Qty Released", "Qty Used / Installed", "Balance Qty"]:
                                worksheet.set_column(col_num, col_num, 16, num_fmt)
                            elif col_name in ["Site ID", "Status Utama Site", "Kode Barang"]:
                                worksheet.set_column(col_num, col_num, 15, center_fmt)
                            else:
                                worksheet.set_column(col_num, col_num, 22, text_fmt)
                                
                        # Inject Conditional Formatting untuk Kolom Status Audit Keuangan Material (Kolom Terakhir)
                        status_col_idx = df_audit_final.columns.get_loc("Status Audit Finansial")
                        worksheet.conditional_format(1, status_col_idx, len(df_audit_final), status_col_idx, {
                            'type': 'cell', 'criteria': 'equal to', 'value': '"SURPLUS / SISA"', 'format': surplus_fmt
                        })
                        worksheet.conditional_format(1, status_col_idx, len(df_audit_final), status_col_idx, {
                            'type': 'cell', 'criteria': 'equal to', 'value': '"MINUS / DEFISIT"', 'format': minus_fmt
                        })
                        worksheet.conditional_format(1, status_col_idx, len(df_audit_final), status_col_idx, {
                            'type': 'cell', 'criteria': 'equal to', 'value': '"SETTLED / BALANCE"', 'format': settled_fmt
                        })

                    # ─────────────────────────────────────────────────────────
                    # 📑 STRATEGI 2: HANDLING OPSI LAPORAN LAINNYA (FALLBACKS)
                    # ─────────────────────────────────────────────────────────
                    else:
                        if "Executive" in report_type:
                            kpi_data = pd.DataFrame({
                                "Indikator Audit Manajemen": ["Total Site Terfilter", "Site Status ON TRACK", "Site Status DELAYED", "Site Status CRITICAL", "Site Status DONE"],
                                "Nilai Kuantitas": [
                                    len(filtered_proj),
                                    len(filtered_proj[filtered_proj['status']=='ON_TRACK']) if 'status' in filtered_proj.columns else 0,
                                    len(filtered_proj[filtered_proj['status']=='DELAYED']) if 'status' in filtered_proj.columns else 0,
                                    len(filtered_proj[filtered_proj['status']=='CRITICAL']) if 'status' in filtered_proj.columns else 0,
                                    len(filtered_proj[filtered_proj['status']=='DONE']) if 'status' in filtered_proj.columns else 0
                                ]
                            })
                            kpi_data.to_excel(writer, sheet_name='Ringkasan_KPI_Utama', index=False)
                            filtered_proj.to_excel(writer, sheet_name='Data_Daftar_Site', index=False)
                            
                        elif "Milestone" in report_type:
                            if not filtered_ms.empty:
                                ms_export = filtered_ms.copy()
                                for col in ['planned_start', 'planned_end', 'actual_start', 'actual_end']:
                                    if col in ms_export.columns:
                                        ms_export[col] = ms_export[col].dt.strftime('%d/%m/%Y')
                                ms_export.to_excel(writer, sheet_name='Detail_Progress_Task', index=False)
                            else:
                                pd.DataFrame([["Status", "Tidak ada data pada periode ini"]]).to_excel(writer, sheet_name='Detail_Progress_Task', index=False)
                                
                        elif "Logistik" in report_type:
                            if not filtered_trans.empty:
                                trans_export = filtered_trans.copy()
                                if 'transaction_date' in trans_export.columns:
                                    trans_export['transaction_date'] = trans_export['transaction_date'].dt.strftime('%d/%m/%Y %H:%M')
                                trans_export.to_excel(writer, sheet_name='Riwayat_Mutasi_Material', index=False)
                            else:
                                pd.DataFrame([["Status", "Belum ada transaksi logistik gudang"]]).to_excel(writer, sheet_name='Riwayat_Mutasi_Material', index=False)

                    # ─────────────────────────────────────────────────────────
                    # 📑 STRATEGI 3: INJEKSI COVER METADATA (AUDIT LOG IDENTIFICATION)
                    # ─────────────────────────────────────────────────────────
                    meta_rows = [
                        ["Nama Dokumen Laporan", report_type],
                        ["Waktu Ekstraksi Data (WIB)", waktu_cetak],
                        ["Filter Ruang Lingkup", sel_master],
                        ["Filter Parameter Status", ", ".join(sel_status) if sel_status else "Seluruh Status Active"],
                        ["Total Cakupan Volume Site", len(filtered_proj)],
                        ["Mesin Pemroses", "Enterprise Report Engine v2.6"],
                        ["Otorisasi Status Database", "SUPABASE CLOUD LIVE CONNECTION"]
                    ]
                    df_meta = pd.DataFrame(meta_rows, columns=["Parameter Audit", "Nilai / Keterangan Dokumen"])
                    df_meta.to_excel(writer, sheet_name='Log_Metadata_Sistem', index=False)
                    
                    # Desain eksklusif untuk Sheet Metadata
                    meta_sheet = writer.sheets['Log_Metadata_Sistem']
                    meta_sheet.set_column('A:A', 28, meta_cell_label)
                    meta_sheet.set_column('B:B', 55, meta_cell_val)
                    meta_sheet.write(0, 0, "Parameter Audit", sub_header_fmt)
                    meta_sheet.write(0, 1, "Nilai / Keterangan Dokumen", sub_header_fmt)

                    # Pastikan standar lebar kolom global aman di semua sheet pendukung
                    for s_name in writer.sheets:
                        if s_name != sheet_name and s_name != 'Log_Metadata_Sistem':
                            ws = writer.sheets[s_name]
                            ws.set_column('A:Z', 16)

                output.seek(0)
                
                # 📦 KOMPILASI NAMA FILE PREMIUM DAN EXPORT BUTTON STREAMLIT
                clean_name = "Comprehensive_Audit" if "Comprehensive" in report_type else "Standard_Report"
                file_final_name = f"Laporan_{clean_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                
                st.download_button(
                    label="📥 AMBIL FILE EXCEL HASIL AUDIT INTEGRASI UTUH",
                    data=output,
                    file_name=file_final_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success("🎯 Konfigurasi Laporan Berhasil Disusun! Silakan klik tombol di atas untuk mengunduh dokumen.")
                
            except Exception as e:
                st.error(f"❌ Kompilasi Gagal: {str(e)}")
                st.info("💡 Solusi: Pastikan file `dashboard.py` Anda tidak sedang membuka koneksi file eksternal atau restart aplikasi Streamlit Anda.")

if __name__ == "__main__":
    export_report_page()
