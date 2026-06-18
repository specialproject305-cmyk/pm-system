import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_db import read_sheet, insert_row, generate_id

def photo_page():
    st.title("📸 Project Photo Evidence")
    st.caption("Ambil foto progress dengan geotag langsung dari HP")
    
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
        
        col_lat, col_lng = st.columns(2)
        with col_lat: lat = st.text_input("Latitude", placeholder="Auto-detected")
        with col_lng: lng = st.text_input("Longitude", placeholder="Auto-detected")
        address = st.text_input("Address", placeholder="Alamat lengkap")
        
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.info(f"🕐 Timestamp: **{timestamp_now}**")
        
        photo_file = st.camera_input("📸 Ambil Foto Sekarang")
        uploaded_file = st.file_uploader("📁 Atau upload dari galeri", type=['jpg','jpeg','png'])
        
        file_to_upload = photo_file or uploaded_file
        
        if file_to_upload:
            st.image(file_to_upload, caption="Preview", width=300)
            notes = st.text_area("📝 Catatan", placeholder="Deskripsi progress...")
            
            if st.button("💾 Simpan Foto", type="primary", use_container_width=True):
                photo_id = generate_id()
                insert_row("project_photos", {
                    'id': photo_id, 'project_id': sel_site, 'site_name': site_name,
                    'milestone_id': sel_ms if sel_ms else '', 'milestone_name': ms_name,
                    'photo_url': '', 'drive_file_id': photo_id,
                    'latitude': lat, 'longitude': lng, 'address': address,
                    'timestamp_taken': timestamp_now, 'uploaded_by': uploaded_by, 'notes': notes
                })
                st.success("✅ Foto berhasil disimpan!")
                st.toast("📸 Foto tersimpan!", icon="📸")
                st.balloons()
                st.rerun()
    
    with tab2:
        st.subheader("🖼️ Galeri Foto")
        if not photos_df.empty:
            st.metric("Total Foto", len(photos_df))
            for _, row in photos_df.tail(20).iterrows():
                st.markdown(f"""
                <div style="background:white;border-radius:10px;padding:10px;margin:5px 0;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid #3B82F6;">
                    <b>{row.get('site_name','-')}</b> — {row.get('milestone_name','-')[:30]}<br>
                    <small>🕐 {row.get('timestamp_taken','')[:16]} | 👷 {row.get('uploaded_by','-')}</small><br>
                    <small>🌐 {row.get('latitude','')}, {row.get('longitude','')}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📭 Belum ada foto.")

if __name__ == "__main__":
    photo_page()
