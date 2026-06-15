import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_db import read_sheet, insert_row, generate_id, now_str

def inventory_page():
    st.title("📦 Inventory Management")
    
    tab1, tab2, tab3 = st.tabs(["📋 Daftar Inventory", "➕ Tambah Data", "📥 Import CSV"])
    
    df = read_sheet("inventory_transactions")
    
    # ===== TAB 1: DAFTAR =====
    with tab1:
        if not df.empty:
            st.metric("Total Records", len(df))
            
            # Filter
                        # Filter terintegrasi
            projects_df = read_sheet("projects")
            
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                vendor_list = ['ALL'] + sorted(df['vendor'].dropna().unique().tolist()) if 'vendor' in df.columns else ['ALL']
                sel_vendor = st.selectbox("🏢 Vendor:", vendor_list)
            with col_f2:
                site_list = ['ALL'] + sorted(projects_df['site_name'].dropna().unique().tolist()) if not projects_df.empty else ['ALL']
                sel_site = st.selectbox("📍 Site Name:", site_list)
            with col_f3:
                status_list = ['ALL'] + sorted(df['settle_status'].dropna().unique().tolist()) if 'settle_status' in df.columns else ['ALL']
                sel_status = st.selectbox("📌 Status:", status_list)
            
            filtered = df.copy()
            if sel_vendor != 'ALL': filtered = filtered[filtered['vendor'] == sel_vendor]
            if sel_site != 'ALL': filtered = filtered[filtered['site_name'] == sel_site]
            if sel_status != 'ALL': filtered = filtered[filtered['settle_status'] == sel_status]
            
            display_cols = ['warehouse', 'vendor', 'site_id', 'site_name', 'spk_vendor', 'item_code', 'item_description', 'mr_number', 'mr_transact_date', 'settle_status', 'project_name']
            st.dataframe(filtered[[c for c in display_cols if c in filtered.columns]], use_container_width=True, hide_index=True)
            
            st.download_button("📥 Download CSV", filtered.to_csv(index=False), f"inventory_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        else:
            st.info("📋 Belum ada data inventory.")
    
    # ===== TAB 2: TAMBAH =====
    with tab2:
        st.subheader("➕ Tambah Data Inventory")
        with st.form("add_inventory"):
            c1, c2, c3 = st.columns(3)
            with c1:
                warehouse = st.text_input("Warehouse", value="IO BTS Project")
                subinventory = st.text_input("Subinventory", value="Contractor")
                vendor = st.text_input("Vendor")
            with c2:
                site_id = st.text_input("Site ID")
                site_name = st.text_input("Site Name")
                spk_vendor = st.text_input("SPK Vendor")
            with c3:
                mr_description = st.text_input("MR Description")
                item_code = st.text_input("Item Code")
                item_description = st.text_input("Item Description")
            
            c4, c5, c6 = st.columns(3)
            with c4:
                mr_creation_department = st.text_input("MR Creation Dept", value="FTTH Project")
                mr_pic_department = st.text_input("MR PIC Dept", value="FTTH Project")
                mr_creation_name = st.text_input("MR Creation Name")
            with c5:
                mr_number = st.text_input("MR Number")
                mr_creation_date = st.text_input("MR Creation Date", placeholder="YYYY-MM-DD")
                mr_approve_date = st.text_input("MR Approve Date", placeholder="YYYY-MM-DD")
            with c6:
                nod_no = st.text_input("NOD No")
                nod_date = st.text_input("NOD Date", placeholder="YYYY-MM-DD")
                mr_transact_date = st.text_input("MR Transact Date", placeholder="YYYY-MM-DD")
            
            c7, c8, c9 = st.columns(3)
            with c7:
                settle_status = st.selectbox("Settle Status", ["Settle Done", "Partial", "Pending"])
                status_mr_new = st.selectbox("Status MR", ["DONE", "PARTIAL", "PENDING"])
                project_name = st.text_input("Project Name")
            with c8:
                mr_qty = st.text_input("MR Qty", "1")
                nod_qty = st.text_input("NOD Qty", "1")
                mr_transact_qty = st.text_input("MR Transact Qty", "1")
            with c9:
                issue_qty = st.text_input("Issue Qty", "1")
                return_qty = st.text_input("Return Qty", "0")
                reloc_qty = st.text_input("Reloc Qty", "0")
            
            if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                insert_row("inventory_transactions", {
                    'id': generate_id(),
                    'warehouse': warehouse, 'subinventory': subinventory, 'vendor': vendor,
                    'site_id': site_id, 'site_name': site_name, 'spk_vendor': spk_vendor,
                    'mr_description': mr_description, 'item_code': item_code, 'item_description': item_description,
                    'mr_creation_department': mr_creation_department, 'mr_pic_department': mr_pic_department,
                    'mr_creation_name': mr_creation_name, 'mr_number': mr_number,
                    'mr_creation_date': mr_creation_date, 'mr_approve_date': mr_approve_date,
                    'nod_no': nod_no, 'nod_date': nod_date, 'mr_transact_date': mr_transact_date,
                    'mr_qty': mr_qty, 'nod_qty': nod_qty, 'mr_transact_qty': mr_transact_qty,
                    'issue_qty': issue_qty, 'return_qty': return_qty, 'reloc_qty': reloc_qty,
                    'settle_status': settle_status, 'status_mr_new': status_mr_new, 'project_name': project_name,
                    'aging': '0', 'outstanding': '0', 'issue_transact_qty': '0',
                    'return_transact_qty': '0', 'reloc_transact_qty': '0', 'mr_transact_type_2': 'MATERIAL REQUEST'
                })
                st.success("✅ Data tersimpan!"); st.rerun()
    
    # ===== TAB 3: IMPORT CSV =====
    with tab3:
        st.subheader("📥 Import CSV")
        template = pd.DataFrame({
            'warehouse': ['IO BTS Project'], 'vendor': ['PT. X'], 'site_id': ['13001'],
            'site_name': ['Site A'], 'spk_vendor': ['SPK-001'], 'item_code': ['168188-000-000000'],
            'item_description': ['[POLE][CCTV]'], 'mr_number': ['2549202'],
            'mr_transact_date': ['2025-09-24'], 'settle_status': ['Settle Done'], 'project_name': ['CCTV 750 TITIK']
        })
        st.download_button("📥 Download Template CSV", template.to_csv(index=False), "template_inventory.csv", "text/csv")
        
        up = st.file_uploader("Upload CSV", type=['csv'])
        if up:
            idf = pd.read_csv(up); st.dataframe(idf.head())
            if st.button("🚀 Import", type="primary"):
                count = 0
                for _, r in idf.iterrows():
                    data = r.to_dict()
                    data['id'] = generate_id()
                    # Fill missing columns
                    for col in ['aging','outstanding','issue_transact_qty','return_transact_qty','reloc_transact_qty','mr_transact_type_2']:
                        if col not in data: data[col] = '0'
                    if 'mr_transact_type_2' not in data: data['mr_transact_type_2'] = 'MATERIAL REQUEST'
                    insert_row("inventory_transactions", data)
                    count += 1
                st.success(f"✅ {count} rows imported!"); st.rerun()

if __name__ == "__main__":
    inventory_page()
