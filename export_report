import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
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
    st.markdown("Unduh laporan proyek dalam format Excel terstruktur, siap untuk meeting & arsip.")

    # ─────────────────────────────────────────────────────────────
    # 📥 LOAD & CLEAN DATA
    # ─────────────────────────────────────────────────────────────
    try:
        with st.spinner("🔄 Memuat data..."):
            all_data = read_all_sheets()
        projects_df = all_data.get('projects', pd.DataFrame())
        milestones_df = all_data.get('milestones', pd.DataFrame())
        materials_df = all_data.get('materials', pd.DataFrame())
        transactions_df = all_data.get('inventory_transactions', pd.DataFrame())
    except Exception as e:
        st.error(f"⚠️ Gagal memuat data: {str(e)[:100]}")
        return

    if projects_df.empty:
        st.info("📋 Belum ada data untuk diekspor. Silakan tambahkan site terlebih dahulu di Project Tracker.")
        return

    # Safe type conversion
    if 'progress' in projects_df.columns:
        projects_df['progress'] = pd.to_numeric(projects_df['progress'], errors='coerce').fillna(0)
    
    date_cols = ['planned_start', 'planned_end', 'actual_start', 'actual_end', 'transaction_date']
    for df in [milestones_df, transactions_df]:
        if not df.empty:
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

    # ─────────────────────────────────────────────────────────────
    # 🔍 FILTER PANEL
    # ─────────────────────────────────────────────────────────────
    st.subheader("🔍 Filter Laporan")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        master_opts = ["🌍 SEMUA PROYEK"]
        if 'master_project_id' in projects_df.columns:
            master_ids = projects_df['master_project_id'].dropna().unique().tolist()
            if master_ids:
                # Ambil nama proyek jika tersedia, fallback ke ID
                try:
                    mp_df = all_data.get('master_projects', pd.DataFrame())
                    master_opts = ["🌍 SEMUA PROYEK"] + [
                        f"{mp_df[mp_df['id']==mid]['project_code'].values[0]} - {mp_df[mp_df['id']==mid]['project_name'].values[0]}" 
                        for mid in master_ids if mid in mp_df['id'].values
                    ]
                except:
                    master_opts = ["🌍 SEMUA PROYEK"] + master_ids
        
        sel_master = st.selectbox("Master Project", master_opts, key="exp_master")
        
    with col_f2:
        default_start = datetime.now() - timedelta(days=30)
        date_range = st.date_input("Periode Data", value=(default_start, datetime.now().date()), key="exp_date")
        
    with col_f3:
        status_opts = projects_df['status'].dropna().unique().tolist() if 'status' in projects_df.columns else []
        sel_status = st.multiselect("Status Site", status_opts, default=status_opts, key="exp_status")

    # ─────────────────────────────────────────────────────────────
    # 🧠 APPLY FILTERS
    # ─────────────────────────────────────────────────────────────
    filtered_proj = projects_df.copy()
    
    # Filter Master Project
    if sel_master != "🌍 SEMUA PROYEK" and 'master_project_id' in filtered_proj.columns:
        # Extract ID from display string if needed
        target_id = sel_master.split(" - ")[0] if " - " in sel_master else sel_master
        filtered_proj = filtered_proj[filtered_proj['master_project_id'] == target_id]
        
    # Filter Status
    if sel_status:
        filtered_proj = filtered_proj[filtered_proj['status'].isin(sel_status)]
        
    # Get valid site IDs for child tables
    valid_site_ids = filtered_proj['id'].tolist()
    
    filtered_ms = milestones_df[milestones_df['project_id'].isin(valid_site_ids)] if not milestones_df.empty else pd.DataFrame()
    filtered_trans = transactions_df[transactions_df['project_id'].isin(valid_site_ids)] if not transactions_df.empty else pd.DataFrame()
    
    # Date filter for milestones/transactions if applicable
    if not filtered_ms.empty and 'planned_end' in filtered_ms.columns:
        start_dt, end_dt = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        filtered_ms = filtered_ms[
            (filtered_ms['planned_end'] >= start_dt) & 
            (filtered_ms['planned_end'] <= end_dt) | 
            filtered_ms['planned_end'].isna()
        ]

    # ─────────────────────────────────────────────────────────────
    # 📑 REPORT TYPE SELECTION
    # ─────────────────────────────────────────────────────────────
    st.subheader("📑 Pilih Jenis Laporan")
    report_type = st.radio(
        "Jenis Laporan:",
        ["📈 Executive Summary", "🧱 Detail Milestone", "📦 Inventory & Transaksi", "📋 Custom Export"],
        horizontal=True,
        key="exp_type"
    )

    # ─────────────────────────────────────────────────────────────
    # 👁️ PREVIEW SECTION
    # ─────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("👁️ Preview Data (Sampel)")
    
    tab_prev1, tab_prev2, tab_prev3 = st.tabs(["Site Overview", "Milestones", "Inventory"])
    with tab_prev1:
        st.dataframe(filtered_proj.head(5), use_container_width=True, hide_index=True)
        st.caption(f"Menampilkan 5 dari {len(filtered_proj)} baris")
    with tab_prev2:
        if not filtered_ms.empty:
            st.dataframe(filtered_ms[['name', 'status', 'planned_start', 'planned_end', 'assigned_to']].head(5), use_container_width=True, hide_index=True)
        else:
            st.info("Tidak ada milestone dalam filter.")
    with tab_prev3:
        if not materials_df.empty:
            st.dataframe(materials_df[['name', 'current_stock', 'min_stock', 'unit']].head(5), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data material.")

    # ─────────────────────────────────────────────────────────────
    # 🚀 GENERATE & DOWNLOAD
    # ─────────────────────────────────────────────────────────────
    st.divider()
    if st.button(" Generate & Download Excel", type="primary", use_container_width=True):
        with st.spinner("🔄 Menyusun laporan multi-sheet..."):
            try:
                output = io.BytesIO()
                
                # Gunakan xlsxwriter untuk formatting profesional
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    workbook = writer.book
                    
                    # Format Styles
                    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#2E75B6', 'font_color': 'white', 'border': 1, 'align': 'center'})
                    date_fmt = workbook.add_format({'num_format': 'dd/mm/yyyy'})
                    pct_fmt = workbook.add_format({'num_format': '0.0%"'})
                    currency_fmt = workbook.add_format({'num_format': '#,##0'})
                    
                    # 1. SHEET: METADATA (Filter & Timestamp)
                    meta_data = pd.DataFrame([
                        ["Export Date", datetime.now().strftime('%d/%m/%Y %H:%M')],
                        ["Filter Master Project", sel_master],
                        ["Filter Periode", f"{date_range[0]} s/d {date_range[1]}"],
                        ["Filter Status", ", ".join(sel_status) if sel_status else "Semua"],
                        ["Total Site", len(filtered_proj)],
                        ["Total Milestone", len(filtered_ms)],
                    ], columns=["Parameter", "Value"])
                    meta_data.to_excel(writer, sheet_name='Metadata', index=False)
                    
                    # 2. SHEET: EXECUTIVE SUMMARY
                    if report_type == "📈 Executive Summary":
                        kpi_data = {
                            "KPI": ["Total Site", "On Track", "Delayed", "Critical", "Avg Progress %"],
                            "Value": [
                                len(filtered_proj),
                                len(filtered_proj[filtered_proj['status']=='ON_TRACK']),
                                len(filtered_proj[filtered_proj['status']=='DELAYED']),
                                len(filtered_proj[filtered_proj['status']=='CRITICAL']),
                                f"{filtered_proj['progress'].mean():.1f}%" if 'progress' in filtered_proj.columns else "0%"
                            ]
                        }
                        pd.DataFrame(kpi_data).to_excel(writer, sheet_name='Executive_Summary', index=False)
                        filtered_proj.to_excel(writer, sheet_name='Site_Overview', index=False)
                        
                    # 3. SHEET: MILESTONE DETAIL
                    elif report_type == "🧱 Detail Milestone":
                        ms_export = filtered_ms.copy()
                        # Format tanggal agar rapi di Excel
                        for col in ['planned_start', 'planned_end', 'actual_start', 'actual_end']:
                            if col in ms_export.columns:
                                ms_export[col] = ms_export[col].dt.strftime('%d/%m/%Y')
                        ms_export.to_excel(writer, sheet_name='Milestone_Detail', index=False)
                        
                    # 4. SHEET: INVENTORY
                    elif report_type == "📦 Inventory & Transaksi":
                        if not materials_df.empty:
                            materials_df.to_excel(writer, sheet_name='Stock_Level', index=False)
                        if not filtered_trans.empty:
                            trans_export = filtered_trans.copy()
                            if 'transaction_date' in trans_export.columns:
                                trans_export['transaction_date'] = trans_export['transaction_date'].dt.strftime('%d/%m/%Y %H:%M')
                            trans_export.to_excel(writer, sheet_name='Transaction_Log', index=False)
                            
                    # 5. SHEET: CUSTOM EXPORT
                    elif report_type == "📋 Custom Export":
                        filtered_proj.to_excel(writer, sheet_name='Projects', index=False)
                        if not filtered_ms.empty:
                            filtered_ms.to_excel(writer, sheet_name='Milestones', index=False)
                        if not materials_df.empty:
                            materials_df.to_excel(writer, sheet_name='Materials', index=False)

                    # Apply formatting to all sheets
                    for sheet_name in writer.sheets:
                        worksheet = writer.sheets[sheet_name]
                        # Set column widths
                        worksheet.set_column('A:Z', 15)
                        # Apply header format
                        for col_num, value in enumerate(pd.read_excel(output, sheet_name=sheet_name, nrows=0).columns.values):
                            worksheet.write(0, col_num, value, header_fmt)

                output.seek(0)
                
                # Download Button
                safe_name = report_type.replace("📈 ", "").replace("🧱 ", "").replace("📦 ", "").replace("📋 ", "").replace(" ", "_")
                filename = f"Laporan_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                
                st.download_button(
                    label="⬇️ Download File Excel",
                    data=output,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success("✅ Laporan berhasil disusun! Klik tombol di atas untuk mengunduh.")
                
            except Exception as e:
                st.error(f"❌ Gagal generate laporan: {str(e)}")
                st.info("💡 Pastikan library `xlsxwriter` terinstall. Jika error, coba restart runtime.")

if __name__ == "__main__":
    export_report_page()
