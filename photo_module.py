import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_db import read_sheet, insert_row, generate_id
import streamlit.components.v1 as components
import requests
import json

# ═══════════════════════════════════════
# KONFIGURASI
# ═══════════════════════════════════════
LOCATIONIQ_KEY = "pk.01a381b84c8dc483a561e0ddd24b6e6d"  # Ganti dengan API Key Location IQ
GOOGLE_DRIVE_FOLDER_ID = "1soOsPCQ3yYF_9P-Yc8EIbdQRFvb61KQd"   # Ganti dengan Folder ID Google Drive

def get_gps_location():
    """Dapatkan lokasi GPS dari browser HP"""
    location_html = """
    <script>
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            document.getElementById('lat_result').value = position.coords.latitude;
            document.getElementById('lng_result').value = position.coords.longitude;
            document.getElementById('status').innerText = '✅ Lokasi terdeteksi!';
        }, function(error) {
            document.getElementById('status').innerText = '⚠️ GPS tidak diizinkan. Isi manual.';
        });
    } else {
        document.getElementById('status').innerText = '⚠️ Browser tidak support GPS. Isi manual.';
    }
    </script>
    <div style="text-align:center;padding:10px;">
        <button onclick="navigator.geolocation.getCurrentPosition(function(p){document.getElementById('lat_result').value=p.coords.latitude;document.getElementById('lng_result').value=p.coords.longitude;document.getElementById('status').innerText='✅ Lokasi terdeteksi!';}, function(e){document.getElementById('status').innerText='⚠️ GPS tidak diizinkan';})" 
            style="background:#3B82F6;color:white;border:none;padding:10px 20px;border-radius:8px;font-size:1rem;cursor:pointer;">
            📍 Deteksi Lokasi Saya
        </button>
        <p id="status" style="margin-top:8px;color:#64748B;"></p>
    </div>
    """
    components.html(location_html, height=120)

def get_address_from_locationiq(lat, lng):
    """Dapatkan alamat dari Location IQ"""
    if not lat or not lng: return ''
    try:
        url = f"https://us1.locationiq.com/v1/reverse.php?key={LOCATIONIQ_KEY}&lat={lat}&lon={lng}&format=json"
        res = requests.get(url, timeout=5)
        data = res.json()
        return data.get('display_name', '')
    except:
        return ''

def upload_to_google_drive(file_bytes, file_name):
    """Upload file ke Google Drive via Service Account"""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
        import io
        
        # Baca kredensial dari Streamlit Secrets
        creds_dict = st.secrets.get("drive_service_account", {})
        if not creds_dict:
            return None, None
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=['https://www.googleapis.com/auth/drive.file'])
        
        service = build('drive', 'v3', credentials=credentials)
        
        file_metadata = {
            'name': file_name,
            'parents': [GOOGLE_DRIVE_FOLDER_ID]
        }
        
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='image/jpeg', resumable=True)
        
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        return file.get('id'), file.get('webViewLink')
    except Exception as e:
        st.warning(f"⚠️ Upload ke Drive gagal: {str(e)[:50]}")
        return None, None

# ═══════════════════════════════════════
# MAIN PAGE
# ═══════════════════════════════════════
def photo_page():
    st.title("📸 Project Photo Evidence")
    st.caption("Foto progress dengan GPS & auto-address")
    
    sites_df = read_sheet("projects")
    ms_df = read_sheet("milestones")
    photos_df = read_sheet("project_photos")
    
    if sites_df.empty:
        st.info("📋 Belum ada site."); return
    
    tab1, tab2, tab3 = st.tabs(["📸 Upload Foto", "🖼️ Galeri Foto", "📊 Statistik"])
    
    with tab1:
        st.subheader("📸 Upload Foto Progress")
        
        # Site & Milestone
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
                    format_func=lambda x: site_ms[site_ms['id']==x]['name'].values[0][:50] if not site_ms.empty else x)
                ms_name = site_ms[site_ms['id']==sel_ms]['name'].values[0] if not site_ms.empty else '-'
            else:
                sel_ms = None; ms_name = '-'
        
        # GPS Location
        st.markdown("### 📍 Lokasi Foto")
        get_gps_location()
        
        col_lat, col_lng = st.columns(2)
        with col_lat:
            lat = st.text_input("Latitude", key="lat_input", placeholder="Auto dari GPS...")
        with col_lng:
            lng = st.text_input("Longitude", key="lng_input", placeholder="Auto dari GPS...")
        
        # Tombol cari alamat
        if st.button("📫 Cari Alamat (Location IQ)", use_container_width=True):
            if lat and lng:
                with st.spinner("🔍 Mencari alamat..."):
                    addr = get_address_from_locationiq(lat, lng)
                    if addr:
                        st.session_state['auto_address'] = addr
                        st.success(f"📍 {addr[:100]}...")
                    else:
                        st.error("Gagal mencari alamat")
        
        address = st.text_input("📫 Address", value=st.session_state.get('auto_address', ''), placeholder="Auto dari Location IQ...")
        uploaded_by = st.text_input("👷 Uploaded By", value=st.session_state.get('user', {}).get('full_name', 'PIC'))
        timestamp_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        st.info(f"🕐 Timestamp: **{timestamp_now}**")
        
        # Upload foto
        st.markdown("### 📸 Foto")
        upload_method = st.radio("Metode:", ["📷 Kamera", "🖼️ Galeri HP"], horizontal=True)
        photo_file = st.camera_input("Ambil Foto") if upload_method == "📷 Kamera" else st.file_uploader("Pilih Foto", type=['jpg','jpeg','png'])
        
        if photo_file:
            st.image(photo_file, caption="Preview", width=350)
            notes = st.text_area("📝 Catatan Lapangan", placeholder="Deskripsi progress...")
            
            if st.button("💾 Simpan & Upload", type="primary", use_container_width=True):
                with st.spinner("📤 Menyimpan..."):
                    file_bytes = photo_file.read()
                    
                    # Upload ke Google Drive
                    drive_id, drive_url = upload_to_google_drive(file_bytes, f"photo_{timestamp_now}_{site_name}.jpg")
                    
                    # Simpan ke Supabase
                    photo_id = generate_id()
                    insert_row("project_photos", {
                        'id': photo_id,
                        'project_id': sel_site,
                        'site_name': site_name,
                        'milestone_id': sel_ms if sel_ms else '',
                        'milestone_name': ms_name,
                        'photo_url': drive_url if drive_url else '',
                        'drive_file_id': drive_id if drive_id else photo_id,
                        'latitude': lat if lat else '',
                        'longitude': lng if lng else '',
                        'address': address if address else '',
                        'timestamp_taken': timestamp_now,
                        'uploaded_by': uploaded_by,
                        'notes': notes
                    })
                    
                    if drive_url:
                        st.success(f"✅ Foto tersimpan di Google Drive!")
                        st.markdown(f"[📎 Buka Foto]({drive_url})")
                    else:
                        st.success("✅ Metadata tersimpan (Drive upload skipped)")
                    st.toast("📸 Foto berhasil disimpan!", icon="📸")
                    st.balloons()
                    st.rerun()
    
    with tab2:
        st.subheader("🖼️ Galeri Foto")
        photos_df = read_sheet("project_photos")
        
        if not photos_df.empty:
            st.metric("Total Foto", len(photos_df))
            
            # Filter
            site_filter = st.selectbox("Filter Site:", ['ALL'] + sites_df['id'].tolist(),
                format_func=lambda x: 'ALL' if x=='ALL' else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
            
            filtered = photos_df.copy()
            if site_filter != 'ALL': filtered = filtered[filtered['project_id'] == site_filter]
            
            cols = st.columns(2)
            for i, (_, row) in enumerate(filtered.tail(20).iterrows()):
                with cols[i % 2]:
                    lat_val = row.get('latitude','') or '-'
                    lng_val = row.get('longitude','') or '-'
                    addr_val = row.get('address','') or '-'
                    photo_url = row.get('photo_url','')
                    
                    card_html = f"""
                    <div style="background:white;border-radius:12px;padding:12px;margin:5px 0;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-left:4px solid #3B82F6;">
                        <div style="font-weight:600;color:#1E293B;">📸 {row.get('milestone_name','-')[:30]}</div>
                        <div style="font-size:0.85rem;color:#64748B;">📍 {row.get('site_name','-')}</div>
                        <div style="font-size:0.75rem;color:#94A3B8;">🕐 {row.get('timestamp_taken','')[:16]}</div>
                        <div style="font-size:0.75rem;color:#94A3B8;">👷 {row.get('uploaded_by','-')}</div>
                        <div style="font-size:0.7rem;color:#CBD5E1;">🌐 {lat_val}, {lng_val}</div>
                        <div style="font-size:0.7rem;color:#CBD5E1;">📫 {addr_val[:50]}</div>
                    """
                    if photo_url:
                        card_html += f'<a href="{photo_url}" target="_blank" style="color:#3B82F6;font-size:0.8rem;">📎 Lihat Foto di Drive</a>'
                    card_html += '</div>'
                    
                    st.markdown(card_html, unsafe_allow_html=True)
        else:
            st.info("📭 Belum ada foto.")
    
    with tab3:
        st.subheader("📊 Statistik Foto")
        if not photos_df.empty:
            import plotly.express as px
            site_counts = photos_df['site_name'].value_counts().reset_index()
            site_counts.columns = ['Site', 'Jumlah']
            fig = px.bar(site_counts, x='Site', y='Jumlah', color='Jumlah', color_continuous_scale=['#3B82F6','#1E40AF'])
            fig.update_layout(height=300, showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    photo_page()
