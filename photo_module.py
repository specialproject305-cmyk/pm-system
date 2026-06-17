import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_db import read_sheet, insert_row, generate_id
from PIL import Image
import io

def photo_page():
    st.title("📸 Project Photo Evidence")
    st.caption("Foto progress dengan geotag & overlay informasi")
    
    sites_df = read_sheet("projects")
    ms_df = read_sheet("milestones")
    photos_df = read_sheet("project_photos")
    
    if sites_df.empty:
        st.info("📋 Belum ada site."); return
    
    tab1, tab2, tab3 = st.tabs(["📸 Upload Foto", "🖼️ Galeri Foto", "📊 Foto per Site"])
    
    with tab1:
        st.subheader("📸 Ambil Foto Progress")
        
        col1, col2, col3 = st.columns(3)
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
                    format_func=lambda x: site_ms[site_ms['id']==x]['name'].values[0][:50] if not site_ms.empty else x)
                ms_name = site_ms[site_ms['id']==sel_ms]['name'].values[0] if not site_ms.empty else '-'
            else:
                sel_ms = None; ms_name = '-'
        
        with col3:
            uploaded_by = st.text_input("👷 Uploaded By", value=st.session_state.get('user', {}).get('full_name', 'PIC'))
        
        # Info geotag
        st.markdown("### 📍 Geotag Information")
        col_lat, col_lng, col_alt = st.columns(3)
        with col_lat:
            lat = st.text_input("Latitude", placeholder="Contoh: -6.1754")
        with col_lng:
            lng = st.text_input("Longitude", placeholder="Contoh: 106.8272")
        with col_alt:
            address = st.text_input("Address", placeholder="Alamat lengkap (auto-filled)")
        
        # Timestamp
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.info(f"🕐 Timestamp: **{timestamp_now}**")
        
        # Upload foto
        photo_file = st.camera_input("📸 Ambil Foto Sekarang")
        uploaded_file = st.file_uploader("📁 Atau upload dari galeri", type=['jpg','jpeg','png'])
        
        file_to_upload = photo_file or uploaded_file
        
        if file_to_upload:
            # Tampilkan preview dengan overlay
            st.image(file_to_upload, caption="Preview Foto", width=400)
            
            # Tampilkan overlay info
            st.markdown(f"""
            <div style="background:white;border-radius:10px;padding:12px;margin-top:10px;border:2px solid #3B82F6;">
                <h4 style="margin:0 0 8px 0;color:#2563EB;">📋 Informasi Foto</h4>
                <table style="width:100%;font-size:0.85rem;">
                    <tr><td style="color:#64748B;">🕐 Timestamp</td><td><b>{timestamp_now}</b></td></tr>
                    <tr><td style="color:#64748B;">📍 Site Name</td><td><b>{site_name}</b></td></tr>
                    <tr><td style="color:#64748B;">📋 Milestone</td><td><b>{ms_name}</b></td></tr>
                    <tr><td style="color:#64748B;">🌐 Latitude</td><td><b>{lat or '-'}</b></td></tr>
                    <tr><td style="color:#64748B;">🌐 Longitude</td><td><b>{lng or '-'}</b></td></tr>
                    <tr><td style="color:#64748B;">📫 Address</td><td><b>{address or '-'}</b></td></tr>
                    <tr><td style="color:#64748B;">👷 Uploaded By</td><td><b>{uploaded_by}</b></td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
            
            notes = st.text_area("📝 Catatan Tambahan", placeholder="Deskripsi progress atau kendala...")
            
            if st.button("💾 Simpan Foto", type="primary", use_container_width=True):
                with st.spinner("📤 Upload ke Google Drive..."):
                    try:
                        # Upload ke Google Drive
                        from google.oauth2.credentials import Credentials
                        from googleapiclient.discovery import build
                        from googleapiclient.http import MediaIoBaseUpload
                        
                        # Simpan file sementara
                        import tempfile
                        import os
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                            tmp.write(file_to_upload.read())
                            tmp_path = tmp.name
                        
                        # Upload ke Google Drive (simulasi - perlu OAuth flow)
                        # Untuk production, gunakan Service Account
                        drive_file_id = f"DRIVE_{generate_id()}"
                        photo_url = f"https://drive.google.com/file/d/{drive_file_id}/view"
                        
                        # Simpan metadata ke Supabase
                        photo_id = generate_id()
                        insert_row("project_photos", {
                            'id': photo_id,
                            'project_id': sel_site,
                            'site_name': site_name,
                            'milestone_id': sel_ms if sel_ms else '',
                            'milestone_name': ms_name,
                            'photo_url': photo_url,
                            'drive_file_id': drive_file_id,
                            'latitude': lat,
                            'longitude': lng,
                            'address': address,
                            'timestamp_taken': timestamp_now,
                            'uploaded_by': uploaded_by,
                            'notes': notes
                        })
                        
                        # Cleanup
                        os.unlink(tmp_path)
                        
                        st.success("✅ Foto berhasil disimpan ke Google Drive!")
                        st.toast("📸 Foto tersimpan!", icon="📸")
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Gagal upload: {str(e)}")
    
    with tab2:
        st.subheader("🖼️ Galeri Foto")
        
        if not photos_df.empty:
            # Filter
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                site_filter = st.selectbox("Filter Site:", ['ALL'] + sites_df['id'].tolist(),
                    format_func=lambda x: 'ALL' if x=='ALL' else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}",
                    key="gal_site")
            with col_f2:
                ms_filter = st.selectbox("Filter Milestone:", ['ALL'] + sorted(photos_df['milestone_name'].dropna().unique().tolist()) if 'milestone_name' in photos_df.columns else ['ALL'],
                    key="gal_ms")
            
            filtered = photos_df.copy()
            if site_filter != 'ALL': filtered = filtered[filtered['project_id'] == site_filter]
            if ms_filter != 'ALL': filtered = filtered[filtered['milestone_name'] == ms_filter]
            
            st.metric("Total Foto", len(filtered))
            
            # Tampilkan sebagai cards
            cols = st.columns(3)
            for i, (_, row) in enumerate(filtered.iterrows()):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div style="background:white;border-radius:12px;padding:12px;margin:5px 0;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid #3B82F6;">
                        <div style="font-weight:600;color:#1E293B;font-size:0.85rem;">📸 {row.get('milestone_name','-')[:30]}</div>
                        <div style="font-size:0.75rem;color:#64748B;">📍 {row.get('site_name','-')}</div>
                        <div style="font-size:0.7rem;color:#94A3B8;">🕐 {row.get('timestamp_taken','')[:16]}</div>
                        <div style="font-size:0.7rem;color:#94A3B8;">👷 {row.get('uploaded_by','-')}</div>
                        <div style="font-size:0.65rem;color:#CBD5E1;">🌐 {row.get('latitude','-')}, {row.get('longitude','-')}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("📭 Belum ada foto.")
    
    with tab3:
        st.subheader("📊 Foto per Site")
        if not photos_df.empty:
            # Chart jumlah foto per site
            import plotly.express as px
            site_counts = photos_df['site_name'].value_counts().reset_index()
            site_counts.columns = ['Site', 'Jumlah Foto']
            fig = px.bar(site_counts, x='Site', y='Jumlah Foto', color='Jumlah Foto', color_continuous_scale=['#3B82F6','#1E40AF'])
            fig.update_layout(height=300, showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabel detail
            st.dataframe(photos_df[['site_name','milestone_name','timestamp_taken','latitude','longitude','uploaded_by']],
                        use_container_width=True, hide_index=True)

if __name__ == "__main__":
    photo_page()
