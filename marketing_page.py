import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_db import read_sheet, insert_row, update_row, delete_row_by_id, generate_id, now_str

def marketing_page():
    st.title("📢 Marketing Sites")
    st.caption("Data site dari tim Marketing")
    
    # Load data
    df = read_sheet("marketing_sites")
    
    tab1, tab2, tab3 = st.tabs(["📋 Daftar Site", "➕ Tambah Site", "📥 Import CSV"])
    
    # ===== TAB 1: DAFTAR =====
    with tab1:
        if not df.empty:
            st.metric("Total Marketing Sites", len(df))
            
            # Filter
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                tenant_list = ['ALL'] + sorted(df['tenant_name'].dropna().unique().tolist()) if 'tenant_name' in df.columns else ['ALL']
                sel_tenant = st.selectbox("🏢 Tenant:", tenant_list)
            with col_f2:
                milestone_list = ['ALL'] + sorted(df['milestone'].dropna().unique().tolist()) if 'milestone' in df.columns else ['ALL']
                sel_milestone = st.selectbox("📌 Milestone:", milestone_list)
            
            filtered = df.copy()
            if sel_tenant != 'ALL': filtered = filtered[filtered['tenant_name'] == sel_tenant]
            if sel_milestone != 'ALL': filtered = filtered[filtered['milestone'] == sel_milestone]
            
            display_cols = ['spk_number', 'spk_date', 'tenant_index', 'spk_status', 'site_id_tenant', 'site_name_tenant', 'work_type', 'tower_height', 'milestone', 'site_id_bts']
            st.dataframe(filtered[[c for c in display_cols if c in filtered.columns]], use_container_width=True, hide_index=True)
            
            # Export
            st.download_button("📥 Download CSV", filtered.to_csv(index=False), f"marketing_sites_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
        else:
            st.info("📋 Belum ada data marketing site.")
    
    # ===== TAB 2: TAMBAH =====
    with tab2:
        with st.form("add_marketing"):
            col1, col2, col3 = st.columns(3)
            with col1:
                tenant_name = st.text_input("Tenant Name", placeholder="XLSMART")
                pic = st.text_input("PIC", placeholder="Lukman")
                division = st.selectbox("Division", ["Project", "Procurement", "Planning", "Marketing", "Engineering", "Other"])
            with col2:
                mobile_number = st.text_input("Mobile Number")
                site_id_tenant = st.text_input("Site ID Tenant")
                site_name_tenant = st.text_input("Site Name Tenant")
            with col3:
                lat_nom = st.text_input("Lat Nom")
                long_nom = st.text_input("Long Nom")
                work_type = st.selectbox("Work Type", ["B2S", "Collocation", "New Site", "Upgrade"])
            
            col4, col5, col6 = st.columns(3)
            with col4:
                tower_height = st.text_input("Tower Height")
                final_antenna_height = st.text_input("Final Antenna Height")
            with col5:
                azimuth = st.text_input("Azimuth", placeholder="0/130/270")
                site_id_bts = st.text_input("Site ID BTS")
            with col6:
                milestone = st.selectbox("Milestone", ["RFS", "Erected", "On Progress", "Pending", "Cancelled"])
                alamat = st.text_input("Alamat")
            
            if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                coord = f"{lat_nom}, {long_nom}" if lat_nom and long_nom else ""
                insert_row("marketing_sites", {
                    'id': generate_id(),
                    'tenant_name': tenant_name,
                    'pic': pic,
                    'division': division,
                    'mobile_number': mobile_number,
                    'alamat': alamat,
                    'site_id_tenant': site_id_tenant,
                    'site_name_tenant': site_name_tenant,
                    'lat_nom': lat_nom,
                    'long_nom': long_nom,
                    'coord': coord,
                    'work_type': work_type,
                    'tower_height': tower_height,
                    'final_antenna_height': final_antenna_height,
                    'azimuth': azimuth,
                    'site_id_bts': site_id_bts,
                    'milestone': milestone
                })
                st.success(f"✅ {site_name_tenant} berhasil ditambahkan!")
                st.rerun()
    
    # ===== TAB 3: IMPORT CSV =====
    with tab3:
        template = pd.DataFrame({
            'tenant_name': ['XLSMART'],
            'pic': ['Lukman'],
            'division': ['Project'],
            'mobile_number': ['08881853041'],
            'site_id_tenant': ['JAW-JB-SKB-0011'],
            'site_name_tenant': ['AMRIS SUKABUMI'],
            'lat_nom': ['-6.94531'],
            'long_nom': ['106.93471'],
            'work_type': ['Collocation'],
            'tower_height': ['21'],
            'final_antenna_height': ['20'],
            'azimuth': ['0/130/270'],
            'site_id_bts': ['715070'],
            'milestone': ['RFS']
        })
        st.download_button("📥 Download Template CSV", template.to_csv(index=False), "template_marketing.csv", "text/csv")
        
        up = st.file_uploader("Upload CSV", type=['csv'])
        if up:
            idf = pd.read_csv(up)
            st.dataframe(idf.head())
            if st.button("🚀 Import", type="primary"):
                count = 0
                for _, r in idf.iterrows():
                    insert_row("marketing_sites", {
                        'id': generate_id(),
                        'tenant_name': str(r.get('tenant_name', '')),
                        'pic': str(r.get('pic', '')),
                        'division': str(r.get('division', '')),
                        'mobile_number': str(r.get('mobile_number', '')),
                        'site_id_tenant': str(r.get('site_id_tenant', '')),
                        'site_name_tenant': str(r.get('site_name_tenant', '')),
                        'lat_nom': str(r.get('lat_nom', '')),
                        'long_nom': str(r.get('long_nom', '')),
                        'coord': f"{r.get('lat_nom','')}, {r.get('long_nom','')}",
                        'work_type': str(r.get('work_type', '')),
                        'tower_height': str(r.get('tower_height', '')),
                        'final_antenna_height': str(r.get('final_antenna_height', '')),
                        'azimuth': str(r.get('azimuth', '')),
                        'site_id_bts': str(r.get('site_id_bts', '')),
                        'milestone': str(r.get('milestone', ''))
                    })
                    count += 1
                st.success(f"✅ {count} site diimport!")
                st.rerun()

if __name__ == "__main__":
    marketing_page()
