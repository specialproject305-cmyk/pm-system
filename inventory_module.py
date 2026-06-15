import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_db import read_sheet, insert_row, update_row, find_row_by_id, generate_id, now_str

def inventory_page():
    # ─────────────────────────────────────────────────────────────
    # 📱 MOBILE OPTIMIZATION CSS
    # ─────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .stColumn { width: 100% !important; margin-bottom: 10px; }
        button, input, select, textarea { min-height: 44px !important; font-size: 16px !important; }
        .stTabs [data-baseweb="tab-list"] { gap: 2px; }
        .stTabs [data-baseweb="tab"] { height: 40px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 4px 4px 0px 0px; gap: 1px; }
        .stDataFrame { font-size: 0.9rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📦 Material Inventory Management")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Stock List", "➕ Tambah Material", "📥 Transaksi", "📤 Import CSV"
    ])
    
    # ─────────────────────────────────────────────────────────────
    # TAB 1: STOCK LIST
    # ─────────────────────────────────────────────────────────────
    with tab1:
        st.subheader("Status Stok Material")
        
        try:
            df = read_sheet("materials")
        except Exception as e:
            st.error(f"❌ Gagal load data material: {str(e)[:100]}")
            return
        
        if not df.empty:
            # Safe numeric conversion
            for col in ['current_stock', 'min_stock', 'unit_price']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Status indicator logic
            def get_status(row):
                if row['current_stock'] < row['min_stock']:
                    return '🔴 CRITICAL'
                elif row['current_stock'] < row['min_stock'] * 1.5:
                    return '🟡 WARNING'
                return '🟢 SAFE'
            
            df['status'] = df.apply(get_status, axis=1)
            
            # Display columns
            display_cols = ['warehouse', 'vendor', 'site_id', 'site_name', 'spk_vendor', 'item_code', 'item_description', 'mr_number', 'mr_transact_date', 'settle_status', 'project_name']
            available_cols = [c for c in display_cols if c in df.columns]
            
            # Color-coded dataframe
            def color_status(val):
                if 'CRITICAL' in val: return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
                elif 'WARNING' in val: return 'background-color: #fff3cd; color: #856404; font-weight: bold'
                return ''
            
            styled = df[available_cols].style.map(color_status, subset=['status'])
            st.dataframe(styled, use_container_width=True, hide_index=True)
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Material", len(df))
            col2.metric("🔴 Critical", len(df[df['status']=='🔴 CRITICAL']))
            col3.metric("🟡 Warning", len(df[df['status']=='🟡 WARNING']))
            
            # Auto-alert to dashboard (via session state or direct update)
            critical_count = len(df[df['status']=='🔴 CRITICAL'])
            if critical_count > 0:
                st.warning(f"⚠️ {critical_count} material dalam status KRITIS! Cek dashboard untuk alert.")
        else:
            st.info("📦 Belum ada material. Tambahkan di tab 'Tambah Material'.")
    
    # ─────────────────────────────────────────────────────────────
    # TAB 2: TAMBAH MATERIAL
    # ─────────────────────────────────────────────────────────────
    with tab2:
        st.subheader("Tambah Material Baru")
        
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
            
            if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                if not name or not code:
                    st.error("❌ Kode dan Nama wajib diisi!")
                else:
                    try:
                        insert_row("materials", {
                            'id': generate_id(), 
                            'code': code, 
                            'name': name, 
                            'unit': unit,
                            'min_stock': str(min_stock), 
                            'current_stock': str(current_stock),
                            'unit_price': str(unit_price)
                        })
                        st.success(f"✅ Material {name} ditambahkan!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal simpan: {str(e)[:100]}")
    
    # ─────────────────────────────────────────────────────────────
    # TAB 3: TRANSAKSI
    # ─────────────────────────────────────────────────────────────
    with tab3:
        st.subheader("Catat Transaksi Material")
        
        try:
            materials_df = read_sheet("materials")
            sites_df = read_sheet("projects")
        except Exception as e:
            st.error(f"❌ Gagal load data: {str(e)[:100]}")
            return
        
        if materials_df.empty:
            st.warning("⚠️ Tambahkan material dulu di tab 'Tambah Material'!")
        else:
            # Safe numeric conversion
            for col in ['current_stock']:
                if col in materials_df.columns:
                    materials_df[col] = pd.to_numeric(materials_df[col], errors='coerce').fillna(0)
            
            with st.form("add_transaction"):
                # Material selector with readable format
                materials_df['label'] = materials_df.apply(
                    lambda x: f"{x['code']} - {x['name']} ({x['current_stock']} {x['unit']})", 
                    axis=1
                )
                mat_choice = st.selectbox(
                    "Material:", 
                    materials_df['id'].tolist(),
                    format_func=lambda x: materials_df[materials_df['id']==x]['label'].values[0]
                )
                
                trans_type = st.radio("Tipe Transaksi:", ["IN", "OUT"], horizontal=True)
                quantity = st.number_input("Jumlah", 0.0, 99999.0, 10.0)
                
                # Site selector (only for OUT transactions)
                site_choice = None
                if trans_type == "OUT" and not sites_df.empty:
                    site_options = ["Gudang"] + sites_df['id'].tolist()
                    site_choice = st.selectbox(
                        "Untuk Site:", 
                        site_options,
                        format_func=lambda x: "🏭 Gudang" if x=="Gudang" 
                        else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}"
                    )
                
                notes = st.text_area("Catatan (Opsional)", placeholder="Contoh: Untuk proyek Tower A")
                
                if st.form_submit_button("📝 Catat Transaksi", type="primary", use_container_width=True):
                    try:
                        mat_row = materials_df[materials_df['id']==mat_choice].iloc[0]
                        current = float(mat_row['current_stock'])
                        
                        # Validate stock for OUT transactions
                        if trans_type == "OUT" and quantity > current:
                            st.error(f"❌ Stok tidak mencukupi! Tersedia: {current} {mat_row['unit']}")
                        else:
                            # Calculate new stock
                            new_stock = current + quantity if trans_type == "IN" else current - quantity
                            
                            # Update material stock
                            ridx = find_row_by_id("materials", mat_choice)
                            if ridx:
                                update_row("materials", ridx, {'current_stock': str(new_stock)})
                            
                            # Record transaction
                            insert_row("inventory_transactions", {
                                'id': generate_id(), 
                                'material_id': mat_choice,
                                'transaction_type': trans_type, 
                                'quantity': str(quantity),
                                'project_id': site_choice if site_choice and site_choice != "Gudang" else '',
                                'transaction_date': now_str(), 
                                'notes': notes or ''
                            })
                            
                            st.success(f"✅ Transaksi tercatat! Stok sekarang: {new_stock} {mat_row['unit']}")
                            
                            # Trigger dashboard alert if stock becomes critical
                            min_stock = float(mat_row.get('min_stock', 0))
                            if new_stock < min_stock:
                                st.warning(f"⚠️ Stok {mat_row['name']} kini KRITIS! (< {min_stock})")
                            
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal catat transaksi: {str(e)[:100]}")
        
        # Transaction History
        st.markdown("---")
        st.subheader("📜 Riwayat Transaksi")
        
        try:
            tx_df = read_sheet("inventory_transactions")
        except:
            tx_df = pd.DataFrame()
        
        if not tx_df.empty:
            # Format date for display
            if 'transaction_date' in tx_df.columns:
                tx_df['transaction_date'] = pd.to_datetime(
                    tx_df['transaction_date'], errors='coerce'
                ).dt.strftime('%d/%m %H:%M')
            
            # Add material name for readability
            if 'material_id' in tx_df.columns and not materials_df.empty:
                tx_df = tx_df.merge(
                    materials_df[['id', 'code', 'name']], 
                    left_on='material_id', right_on='id', 
                    how='left', suffixes=('', '_mat')
                )
                tx_df['material'] = tx_df.apply(
                    lambda x: f"{x['code']} - {x['name']}" if pd.notna(x.get('code')) else x['material_id'], 
                    axis=1
                )
            
            # Display relevant columns
            display_cols = ['transaction_date', 'material', 'transaction_type', 'quantity', 'notes', 'project_id']
            available_cols = [c for c in display_cols if c in tx_df.columns]
            
            st.dataframe(
                tx_df[available_cols].tail(20), 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "transaction_type": st.column_config.SelectboxColumn(
                        "Tipe", options=["IN", "OUT"], width="small"
                    ),
                    "quantity": st.column_config.NumberColumn("Jumlah", format="%.2f")
                }
            )
        else:
            st.info("Belum ada riwayat transaksi.")
    
    # ─────────────────────────────────────────────────────────────
    # TAB 4: IMPORT CSV
    # ─────────────────────────────────────────────────────────────
    with tab4:
        st.subheader("📥 Import Material via CSV")
        
        # Download template
        template = pd.DataFrame({
            'code': ['MAT-001'], 
            'name': ['Besi 10mm'], 
            'unit': ['batang'],
            'min_stock': [100], 
            'current_stock': [500], 
            'unit_price': [15000]
        })
        st.download_button(
            "📥 Download Template CSV", 
            template.to_csv(index=False), 
            "template_material.csv", 
            "text/csv"
        )
        
        st.markdown("---")
        
        # Upload file
        up = st.file_uploader("Upload File CSV", type=['csv'], key="mat_csv")
        if up:
            try:
                idf = pd.read_csv(up)
                st.markdown("### Preview Data")
                st.dataframe(idf.head(), use_container_width=True)
                
                required_cols = ['code', 'name']
                missing = [c for c in required_cols if c not in idf.columns]
                
                if missing:
                    st.error(f"❌ Kolom wajib tidak ada: {', '.join(missing)}")
                else:
                    st.info(f"ℹ️ Ditemukan {len(idf)} baris data")
                    
                    if st.button("🚀 Konfirmasi Import", type="primary", use_container_width=True):
                        count = 0
                        errors = 0
                        
                        with st.spinner("🔄 Mengimport..."):
                            for idx, r in idf.iterrows():
                                try:
                                    insert_row("materials", {
                                        'id': generate_id(), 
                                        'code': str(r.get('code','')),
                                        'name': str(r.get('name','')), 
                                        'unit': str(r.get('unit','unit')),
                                        'min_stock': str(r.get('min_stock',0)), 
                                        'current_stock': str(r.get('current_stock',0)),
                                        'unit_price': str(r.get('unit_price',0))
                                    })
                                    count += 1
                                except:
                                    errors += 1
                        
                        if count > 0:
                            st.success(f"✅ {count} material berhasil diimport!")
                            if errors > 0:
                                st.warning(f"⚠️ {errors} baris gagal diproses")
                            st.rerun()
                        else:
                            st.error("❌ Tidak ada data yang berhasil diimport")
                            
            except Exception as e:
                st.error(f"❌ Gagal baca file CSV: {str(e)}")

if __name__ == "__main__":
    inventory_page()
