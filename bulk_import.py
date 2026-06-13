import streamlit as st
import pandas as pd
from supabase_db import insert_row, generate_id, today_str

def bulk_import_page():
    st.title("📥 Bulk Import Data")
    st.caption("Import data massal untuk semua tabel. Hanya Admin & PMO.")
    
    # Pilih tabel tujuan
    table = st.selectbox("📂 Pilih Tabel Tujuan:", [
        "projects", "milestones", "materials", "master_projects",
        "marketing_sites", "users", "inventory_transactions"
    ])
    
    # Template per tabel
    templates = {
        "projects": pd.DataFrame({
            "site_id": ["SITE-001"], "site_name": ["Tower A"], "site_category": ["New Site"],
            "site_type": ["SST"], "vendor": ["PT. X"],"spk_vendor": ["SPK-001/VII/2025"], "pm": ["Budi"],
            "tower_height": [45], "site_coordinate": ["-6.17,106.82"],
            "start_date": [today_str()], "end_date": [today_str()],
            "master_project_id": [""], "status": ["ON_TRACK"], "progress": ["0"]
        }),
        "milestones": pd.DataFrame({
            "project_id": [""], "name": ["Pondasi"], "planned_start": [today_str()],
            "planned_end": [today_str()], "assigned_to": ["Engineering"],
            "weight": [10], "status": ["PENDING"], "sla_days": [3], "delay_reason": [""]
        }),
        "materials": pd.DataFrame({
            "code": ["MAT-001"], "name": ["Besi Beton 10mm"], "unit": ["batang"],
            "min_stock": [100], "current_stock": [500], "unit_price": [15000]
        }),
        "master_projects": pd.DataFrame({
            "project_code": ["PRJ-001"], "project_name": ["Rollout Phase 1"],
            "category": ["4G Rollout"], "status": ["ACTIVE"]
        }),
        "marketing_sites": pd.DataFrame({
            "spk_number": ["6644056"], "spk_date": ["2025-10-30"],
            "tenant_index": ["XLSMART"], "spk_status": ["CLOSE"],
            "site_id_tenant": ["JAW-JB-001"], "site_name_tenant": ["Tower A"],
            "lat_nom": ["-6.94531"], "long_nom": ["106.93471"],
            "work_type": ["Collocation"], "tower_height": ["21"],
            "final_antenna_height": ["20"], "azimuth": ["0/130/270"],
            "site_id_bts": ["715070"], "milestone": ["RFS"]
        }),
        "users": pd.DataFrame({
            "username": ["user1"], "password": ["pass123"],
            "role": ["viewer"], "full_name": ["User Satu"]
        }),
        "inventory_transactions": pd.DataFrame({
            "material_id": [""], "transaction_type": ["IN"],
            "quantity": [100], "project_id": [""], "notes": ["Restock"]
        }),
    }
    
    template = templates.get(table, pd.DataFrame())
    
    # Download template
    st.download_button(
        f"📥 Download Template {table}.csv",
        template.to_csv(index=False),
        f"template_{table}.csv",
        "text/csv"
    )
    
    st.markdown("---")
    
    # Upload & Import
    up = st.file_uploader(f"📤 Upload CSV untuk tabel **{table}**", type=["csv"])
    
    if up:
        df_import = pd.read_csv(up)
        st.write(f"Preview ({len(df_import)} rows):")
        st.dataframe(df_import.head(10), use_container_width=True)
        
        if st.button(f"🚀 Import ke {table}", type="primary", use_container_width=True):
            success = 0
            errors = []
            
            for idx, row in df_import.iterrows():
                try:
                    data_dict = row.to_dict()
                    data_dict['id'] = generate_id()
                    
                    # Handle NaN
                    for k, v in data_dict.items():
                        if pd.isna(v):
                            data_dict[k] = ''
                    
                    insert_row(table, data_dict)
                    success += 1
                except Exception as e:
                    errors.append(f"Row {idx+2}: {str(e)[:80]}")
            
            if success > 0:
                st.success(f"✅ {success} rows imported successfully!")
            if errors:
                with st.expander(f"⚠️ {len(errors)} errors"):
                    for e in errors[:20]:
                        st.write(e)
            if success > 0:
                st.cache_data.clear()
                st.rerun()
    
    st.markdown("---")
    st.info("💡 **Tips:** Download template → Isi data di Excel → Save as CSV → Upload kembali")

if __name__ == "__main__":
    bulk_import_page()
