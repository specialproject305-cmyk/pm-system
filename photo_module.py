import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_db import read_sheet, insert_row, generate_id
import json

def photo_page():
    st.title("📸 Project Photo Evidence")
    st.caption("Ambil foto progress — metadata tersimpan otomatis")
    
    sites_df = read_sheet("projects")
    ms_df = read_sheet("milestones")
    photos_df = read_sheet("project_photos")
    
    if sites_df.empty:
        st.info("📋 Belum ada site."); return
    
    tab1, tab2 = st.tabs(["📸 Upload Foto", "🖼️ Galeri Foto"])
    
    with tab1:
        st.subheader("📸 Ambil Foto Progress")
        
        col1, col2 = st.columns(2)
        with col1:
            site_list = sites_df['id'].tolist()
            sel_site = st.selectbox("📍 Site:", site_list,
                format_func=lambda x: f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
            site_name = sites_df[sites_df['id']==sel_site]['site_name'].values[0]
        
        with col2:
            if not ms_df.empty:
                site_ms = ms_df[ms_df['project_id'] == sel_site]
                ms_list = site_ms['id'].tolist() if not site_ms.empty else []
                sel_ms = st.selectbox("📋 Milestone:", ms_list,
                    format_func=lambda x: site_ms[site_ms['id']==x]['name'].values[0][:40] if not site_ms.empty else x)
                ms_name = site_ms[site_ms['id']==sel_ms]['name'].values[0] if not site_ms.empty else '-'
            else:
                sel_ms = None; ms_name = '-'
        
        uploaded_by = st.text_input("👷 Uploaded By", value=st.session_state.get('user', {}).get('full_name', 'PIC'))
        
        # Geotag - manual input atau auto
        st.markdown("### 📍 Geotag (isi manual atau biarkan kosong)")
        col_lat, col_lng = st.columns(2)
        with col_lat: lat = st.text_input("Latitude", value="", placeholder="Contoh: -6.1754")
        with col_lng: lng = st.text_input("Longitude", value="", placeholder="Contoh: 106.8272")
        address = st.text_input("Address", value="", placeholder="Alamat lengkap (dapat diisi manual)")
        
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.info(f"🕐 Timestamp: **{timestamp_now}**")
        
        # Upload foto
        st.markdown("### 📸 Upload Foto")
        upload_method = st.radio("Pilih metode:", ["📷 Kamera", "🖼️ Galeri HP"], horizontal=True)
        
        if upload_method == "📷 Kamera":
            photo_file = st.camera_input("Ambil Foto", key="camera")
        else:
            photo_file = st.file_uploader("Pilih dari Galeri", type=['jpg','jpeg','png'], key="gallery")
        
        if photo_file:
            st.image(photo_file, caption="Preview Foto", width=350)
            notes = st.text_area("📝 Catatan", placeholder="Deskripsi progress lapangan...")
            
            if st.button("💾 Simpan Foto", type="primary", use_container_width=True):
                with st.spinner("📤 Menyimpan..."):
                    # Simpan metadata ke Supabase
                    photo_id = generate_id()
                    insert_row("project_photos", {
                        'id': photo_id,
                        'project_id': sel_site,
                        'site_name': site_name,
                        'milestone_id': sel_ms if sel_ms else '',
                        'milestone_name': ms_name,
                        'photo_url': '',
                        'drive_file_id': photo_id,
                        'latitude': lat if lat else '',
                        'longitude': lng if lng else '',
                        'address': address if address else '',
                        'timestamp_taken': timestamp_now,
                        'uploaded_by': uploaded_by,
                        'notes': notes
                    })
                    
                    st.success(f"✅ Foto berhasil disimpan!")
                    st.toast("📸 Metadata tersimpan di database!", icon="📸")
                    st.balloons()
                    st.rerun()
    
    with tab2:
        st.subheader("🖼️ Galeri Foto")
        
        # Refresh data
        photos_df = read_sheet("project_photos")
        
        if not photos_df.empty:
            st.metric("Total Foto", len(photos_df))
            
            # Tampilkan sebagai cards
            cols = st.columns(2)
            for i, (_, row) in enumerate(photos_df.tail(20).iterrows()):
                with cols[i % 2]:
                    lat_val = row.get('latitude', '') or '-'
                    lng_val = row.get('longitude', '') or '-'
                    addr_val = row.get('address', '') or '-'
                    
                    st.markdown(f"""
                    <div style="background:white;border-radius:12px;padding:12px;margin:5px 0;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid #3B82F6;">
                        <div style="font-weight:600;color:#1E293B;">📸 {row.get('milestone_name','-')[:30]}</div>
                        <div style="font-size:0.85rem;color:#64748B;">📍 {row.get('site_name','-')}</div>
                        <div style="font-size:0.75rem;color:#94A3B8;">🕐 {row.get('timestamp_taken','')[:16]}</div>
                        <div style="font-size:0.75rem;color:#94A3B8;">👷 {row.get('uploaded_by','-')}</div>
                        <div style="font-size:0.7rem;color:#CBD5E1;">🌐 {lat_val}, {lng_val}</div>
                        <div style="font-size:0.7rem;color:#CBD5E1;">📫 {addr_val[:40]}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("📭 Belum ada foto. Upload foto terlebih dahulu!")

if __name__ == "__main__":
    photo_page()
