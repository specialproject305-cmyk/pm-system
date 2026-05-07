import streamlit as st
import pandas as pd
from supabase_db import read_sheet, insert_row, update_row, find_row_by_id, generate_id, now_str

def inventory_page():
    st.title("📦 Material Inventory Management")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Stock List", "➕ Tambah Material", "📥 Transaksi", "📤 Import CSV"
    ])
    
    with tab1:
        st.subheader("Status Stok Material")
        df = read_sheet("materials")
        
        if not df.empty:
            for col in ['current_stock', 'min_stock', 'unit_price']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            def get_status(row):
                if row['current_stock'] < row['min_stock']:
                    return '🔴 CRITICAL'
                elif row['current_stock'] < row['min_stock'] * 1.5:
                    return '🟡 WARNING'
                return '🟢 SAFE'
            
            df['status'] = df.apply(get_status, axis=1)
            
            display_cols = ['code', 'name', 'unit', 'current_stock', 'min_stock', 'status', 'unit_price']
            st.dataframe(df[[c for c in display_cols if c in df.columns]], use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Material", len(df))
            col2.metric("🔴 Critical", len(df[df['status']=='🔴 CRITICAL']))
            col3.metric("🟡 Warning", len(df[df['status']=='🟡 WARNING']))
        else:
            st.info("📦 Belum ada material.")
    
    with tab2:
        st.subheader("Tambah Material")
        with st.form("add_material"):
            c1, c2 = st.columns(2)
            with c1:
                code = st.text_input("Kode Material", placeholder="MAT-BESI-10")
                name = st.text_input("Nama Material", placeholder="Besi Beton 10mm")
                unit = st.selectbox("Satuan", ["kg","batang","sak","m3","unit","roll","liter"])
            with c2:
                min_stock = st.number_input("Stok Minimum", 0.0, 999999.0, 100.0)
                current_stock = st.number_input("Stok Saat Ini", 0.0, 999999.0, 1000.0)
                unit_price = st.number_input("Harga/Unit (Rp)", 0.0, 99999999.0, 15000.0)
            
            if st.form_submit_button("💾 Simpan", type="primary"):
                if not name or not code:
                    st.error("❌ Kode dan Nama wajib diisi!")
                else:
                    insert_row("materials", {
                        'id': generate_id(), 'code': code, 'name': name, 'unit': unit,
                        'min_stock': str(min_stock), 'current_stock': str(current_stock),
                        'unit_price': str(unit_price)
                    })
                    st.success(f"✅ Material {name} ditambahkan!")
                    st.rerun()
    
    with tab3:
        st.subheader("Catat Transaksi")
        materials_df = read_sheet("materials")
        sites_df = read_sheet("projects")
        
        if materials_df.empty:
            st.warning("⚠️ Tambahkan material dulu!")
        else:
            for col in ['current_stock']:
                if col in materials_df.columns:
                    materials_df[col] = pd.to_numeric(materials_df[col], errors='coerce').fillna(0)
            
            with st.form("add_transaction"):
                mat_choice = st.selectbox("Material:", materials_df['id'].tolist(),
                                         format_func=lambda x: f"{materials_df[materials_df['id']==x]['code'].values[0]} - {materials_df[materials_df['id']==x]['name'].values[0]}")
                trans_type = st.radio("Tipe:", ["IN", "OUT"], horizontal=True)
                quantity = st.number_input("Jumlah", 0.0, 99999.0, 10.0)
                
                site_choice = None
                if trans_type == "OUT" and not sites_df.empty:
                    site_choice = st.selectbox("Untuk Site:", ["Gudang"] + sites_df['id'].tolist(),
                                               format_func=lambda x: "Gudang" if x=="Gudang" else f"{sites_df[sites_df['id']==x]['site_id'].values[0]}")
                
                notes = st.text_area("Catatan")
                
                if st.form_submit_button("📝 Catat", type="primary"):
                    mat_row = materials_df[materials_df['id']==mat_choice].iloc[0]
                    current = mat_row['current_stock']
                    
                    if trans_type == "OUT" and quantity > current:
                        st.error("❌ Stok tidak mencukupi!")
                    else:
                        new_stock = current + quantity if trans_type == "IN" else current - quantity
                        ridx = find_row_by_id("materials", mat_choice)
                        if ridx:
                            update_row("materials", ridx, {'current_stock': str(new_stock)})
                        
                        insert_row("inventory_transactions", {
                            'id': generate_id(), 'material_id': mat_choice,
                            'transaction_type': trans_type, 'quantity': str(quantity),
                            'project_id': site_choice if site_choice and site_choice != "Gudang" else '',
                            'transaction_date': now_str(), 'notes': notes
                        })
                        st.success(f"✅ Stok sekarang: {new_stock}")
                        st.rerun()
        
        st.markdown("---")
        st.subheader("📜 Riwayat Transaksi")
        tx_df = read_sheet("inventory_transactions")
        if not tx_df.empty:
            st.dataframe(tx_df.tail(20), use_container_width=True)
    
    with tab4:
        st.subheader("Import CSV Material")
        template = pd.DataFrame({
            'code': ['MAT-001'], 'name': ['Besi 10mm'], 'unit': ['batang'],
            'min_stock': [100], 'current_stock': [500], 'unit_price': [15000]
        })
        st.download_button("📥 Template", template.to_csv(index=False), "template_mat.csv", "text/csv")
        
        up = st.file_uploader("Upload CSV", type=['csv'], key="mat_csv")
        if up:
            idf = pd.read_csv(up)
            st.dataframe(idf)
            if st.button("🚀 Import", type="primary", key="btn_mat_import"):
                count = 0
                for _, r in idf.iterrows():
                    insert_row("materials", {
                        'id': generate_id(), 'code': str(r.get('code','')),
                        'name': str(r.get('name','')), 'unit': str(r.get('unit','unit')),
                        'min_stock': str(r.get('min_stock',0)), 'current_stock': str(r.get('current_stock',0)),
                        'unit_price': str(r.get('unit_price',0))
                    })
                    count += 1
                st.success(f"✅ {count} material diimport!")
                st.rerun()

if __name__ == "__main__":
    inventory_page()