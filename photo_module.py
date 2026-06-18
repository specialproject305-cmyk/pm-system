import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from supabase_db import read_sheet, insert_row, generate_id
import streamlit.components.v1 as components
import requests
import json
import numpy as np

# ═══════════════════════════════════════
# KONFIGURASI OPERASIONAL
# ═══════════════════════════════════════
LOCATIONIQ_KEY = "pk.01a381b84c8dc483a561e0ddd24b6e6d"  # ✅ API Key Location IQ Anda aktif
GOOGLE_DRIVE_FOLDER_ID = "1soOsPCQ3yYF_9P-Yc8EIbdQRFvb61KQd"   # ✅ Folder ID GDrive Anda

# ═══════════════════════════════════════
# PRE-PROCESS UTILITIES
# ═══════════════════════════════════════
def get_gps_location():
    """Dapatkan lokasi GPS & Alamat langsung dari Browser HP (100% Sinkron)"""
    
    location_html = f"""
    <style>
        #location_btn {{
            background: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%);
            color: white;
            border: none;
            padding: 14px 24px;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3);
            transition: all 0.2s ease;
        }}
        #location_btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(59, 130, 246, 0.4);
        }}
        #location_btn:disabled {{
            background: #94A3B8;
            cursor: not-allowed;
        }}
    </style>
    
    <script>
    async function findMeAndAddress() {{
        const status = document.getElementById('status');
        const btn = document.getElementById('location_btn');
        
        status.innerText = '⌛ 1. Mencari Satelit GPS HP...';
        btn.disabled = true;

        if (navigator.geolocation) {{
            navigator.geolocation.getCurrentPosition(async function(position) {{
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                status.innerText = '⌛ 2. Menghubungkan ke Satelit & LocationIQ...';
                
                // Suntik Koordinat ke Elemen HTML Streamlit
                const latInput = parent.document.querySelector('input[aria-label="Latitude"]');
                const lngInput = parent.document.querySelector('input[aria-label="Longitude"]');
                const addrInput = parent.document.querySelector('input[aria-label="📫 Address Detail (Auto-Address)"]');
                
                if(latInput) latInput.value = lat;
                if(lngInput) lngInput.value = lng;
                
                // Panggil Reverse Geocoding langsung di sisi Client (Browser) agar super cepat
                try {{
                    const url = `https://us1.locationiq.com/v1/reverse.php?key={LOCATIONIQ_KEY}&lat=${{lat}}&lon=${{lng}}&format=json`;
                    const response = await fetch(url);
                    const data = await response.json();
                    const address = data.display_name || '';
                    
                    if(addrInput) addrInput.value = address;
                    
                    // Trigger Event Input secara berurutan agar Streamlit Python Terpaksa Membaca Nilainya
                    if(latInput) latInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    if(lngInput) lngInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    if(addrInput) addrInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    
                    status.innerText = '✅ GPS & Alamat Berhasil Disinkronisasi! Silakan isi Catatan & Simpan.';
                    status.style.color = '#059669';
                }} catch (err) {{
                    // Jika API LocationIQ gagal, koordinat tetap masuk
                    if(latInput) latInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    if(lngInput) lngInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    status.innerText = '✅ GPS Dapat, tapi Alamat Gagal Dimuat. Koordinat Tetap Aman!';
                    status.style.color = '#D97706';
                }}
                
                btn.disabled = false;
            }}, function(error) {{
                status.innerText = '⚠️ Akses GPS ditolak browser HP. Pastikan HTTPS aktif & Izinkan Lokasi.';
                status.style.color = '#DC2626';
                btn.disabled = false;
            }}, {{enableHighAccuracy: true, timeout: 15000}});
        }} else {{
            status.innerText = '⚠️ Browser HP Anda tidak mendukung Geolocation.';
            btn.disabled = false;
        }}
    }}
    </script>
    
    <div style="text-align:center; padding: 5px;">
        <button id="location_btn" onclick="findMeAndAddress()">
            📍 AMBIL GPS & AUTO-ALAMAT (KLIK DI SINI)
        </button>
        <p id="status" style="margin-top:10px; color:#64748B; font-size:0.9rem; font-weight:600;"></p>
    </div>
    """
    components.html(location_html, height=140, scrolling=False)
    </style>
    
    <script>
    function findMe() {
        const status = document.getElementById('status');
        const btn = document.getElementById('location_btn');
        
        status.innerText = '⌛ Mencari satelit GPS...';
        btn.disabled = true;

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                
                // ─── 🚀 FIX: Sinkronisasi nilai ke input text Streamlit di IFrame Induk ───
                parent.document.querySelector('input[aria-label="Latitude"]').value = position.coords.latitude;
                parent.document.querySelector('input[aria-label="Longitude"]').value = position.coords.longitude;
                
                // Trigger event input agar Streamlit mendeteksi perubahan nilai saat rerun
                parent.document.querySelector('input[aria-label="Latitude"]').dispatchEvent(new Event('input', { bubbles: true }));
                parent.document.querySelector('input[aria-label="Longitude"]').dispatchEvent(new Event('input', { bubbles: true }));
                
                status.innerText = '✅ Lokasi terdeteksi & disinkronisasi!';
                status.style.color = '#059669';
                btn.disabled = false;
            }, function(error) {
                status.innerText = '⚠️ GPS ditolak. Aktifkan GPS HP Anda.';
                status.style.color = '#DC2626';
                btn.disabled = false;
            }, {enableHighAccuracy: true, timeout: 10000}); // Akurasi tinggi aktif
        } else {
            status.innerText = '⚠️ Browser tidak support GPS.';
            btn.disabled = false;
        }
    }
    </script>
    
    <div style="text-align:center;padding:10px;">
        <button id="location_btn" onclick="findMe()">
            📍 Deteksi Lokasi Saya (GPS HP)
        </button>
        <p id="status" style="margin-top:10px;color:#64748B;font-size:0.9rem;font-weight:500;"></p>
    </div>
    """
    
    # MENAMBAHKAN IZIN GEOLOCATION KE IFRAME
    components.html(location_html, height=140, scrolling=False)

def get_address_from_locationiq(lat, lng):
    """Dapatkan alamat dari Location IQ (Reverse Geocoding)"""
    if not lat or not lng: return ''
    try:
        # LocationIQ us1 standard API endpoint
        url = f"https://us1.locationiq.com/v1/reverse.php?key={LOCATIONIQ_KEY}&lat={lat}&lon={lng}&format=json"
        res = requests.get(url, timeout=7)
        res.raise_for_status() # Cek apakah ada error HTTP
        data = res.json()
        return data.get('display_name', '')
    except Exception as e:
        st.warning(f"⚠️ Gagal hubungi LocationIQ: {str(e)[:50]}")
        return ''

def upload_to_google_drive(file_bytes, file_name):
    """Upload file ke Google Drive via Service Account & Streamlit Secrets"""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
        import io
        
        # ─── 🛠️ FIX: Validasi Format Secrets Tepat ───
        # Pastikan di secrets tertulis: [drive_service_account]
        creds_dict = st.secrets.get("drive_service_account")
        
        if not creds_dict:
            st.error("❌ Kredensial 'drive_service_account' tidak ditemukan di Streamlit Secrets.")
            return None, None
        
        # Validasi Izin Folder ID
        if not GOOGLE_DRIVE_FOLDER_ID or GOOGLE_DRIVE_FOLDER_ID == "Folder ID Drive Anda":
            st.error("❌ Folder ID Google Drive belum diisi di Konfigurasi kode.")
            return None, None

        # Build credentials
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=['https://www.googleapis.com/auth/drive.file'])
        
        # Build Drive Service v3
        service = build('drive', 'v3', credentials=credentials)
        
        file_metadata = {
            'name': file_name,
            'parents': [GOOGLE_DRIVE_FOLDER_ID] # Masukkan file ke folder tujuan
        }
        
        # Upload media stream
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='image/jpeg', resumable=True)
        
        # Execute create
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        return file.get('id'), file.get('webViewLink')
        
    except Exception as e:
        # Tampilkan error detail untuk debugging di logs
        st.warning(f"⚠️ Upload ke Drive gagal: {str(e)}")
        return None, None

# ═══════════════════════════════════════
# MAIN APPLICATION PAGE
# ═══════════════════════════════════════
def photo_page():
    # CSS Injeksi Premium (Menjaga estetika desain)
    st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 2px solid #DBEAFE; }
        .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; background: #EFF6FF; }
        .upload-divider { height: 1px; background: #DBEAFE; margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📸 Project Photo Evidence")
    st.caption("Foto progress konstruksi tower dengan GPS murni HP & auto-address")
    
    # 📥 Load Data Supabase (Data Safety Handle)
    try:
        sites_df = read_sheet("projects")
        ms_df = read_sheet("milestones")
        
        # Fallback jika data kosong
        if sites_df.empty:
            st.info("📋 Belum ada site terdaftar di database."); return
            
    except Exception as e:
        st.error(f"❌ Gagal muat data Supabase: {e}"); return

    # 📑 UI TABS
    tab1, tab2, tab3 = st.tabs(["📸 Upload Foto Lapangan", "🖼️ Galeri Foto Evidence", "📊 Statistik"])
    
    with tab1:
        st.subheader("📸 Form Pengisian Foto Evidence")
        
        # ─── 🏗️ SELEKSI SITE & MILESTONE ───
        col1, col2 = st.columns(2)
        with col1:
            site_list = sites_df['id'].tolist()
            sel_site = st.selectbox(
                "📍 Pilih Site Tower:", 
                site_list, 
                key="sel_site_unique",
                format_func=lambda x: f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}"
            )
            site_name = sites_df[sites_df['id']==sel_site]['site_name'].values[0]
            
        with col2:
            if not ms_df.empty:
                site_ms = ms_df[ms_df['project_id'] == sel_site]
                if not site_ms.empty:
                    ms_list = site_ms['id'].tolist()
                    sel_ms = st.selectbox(
                        "📋 Pilih Milestone/Task:", 
                        ms_list, 
                        key="sel_ms_unique",
                        format_func=lambda x: site_ms[site_ms['id']==x]['name'].values[0][:50]
                    )
                    ms_name = site_ms[site_ms['id']==sel_ms]['name'].values[0]
                else:
                    st.info("ℹ️ Tidak ada milestone di site ini.")
                    sel_ms = None; ms_name = '-'
            else:
                sel_ms = None; ms_name = '-'
        
        st.markdown('<div class="upload-divider"></div>', unsafe_allow_html=True)

        # ─── 📍 ENGINE GPS & GEOCODING TERPADU (JAVASCRIPT) ───
        st.markdown("### 📍 Lokasi Pengambilan Foto")
        
        # Memanggil fungsi HTML/JS terpadu yang langsung mencari lokasi & alamat di sisi browser
        get_gps_location() 

        # Field Koordinat (Menerima suntikan data aman dari dispatch event JS)
        col_lat, col_lng = st.columns(2)
        with col_lat:
            lat = st.text_input(
                "Latitude", 
                key="lat_input", 
                placeholder="Klik tombol di atas...",
                help="Akan terisi otomatis secara sinkron setelah menekan tombol GPS."
            )
        with col_lng:
            lng = st.text_input(
                "Longitude", 
                key="lng_input", 
                placeholder="Klik tombol di atas...",
                help="Akan terisi otomatis secara sinkron setelah menekan tombol GPS."
            )
        
        # Field Alamat Detail (Satu alur sinkronisasi dengan event trigger JS)
        address = st.text_input(
            "📫 Address Detail (Auto-Address)", 
            key="addr_input", 
            placeholder="Klik tombol di atas...",
            help="Alamat otomatis dari satelit LocationIQ. Anda juga dapat mengedit teks ini manual jika diperlukan."
        )
        
        # ─── 👷 INFORMASI PIC & TIMESTAMPS ───
        uploaded_by = st.text_input(
            "👷 Uploaded By PIC Lapangan", 
            value=st.session_state.get('user', {}).get('full_name', 'PIC Vendor')
        )
        
        # Sinkronisasi Waktu Indonesia Barat (WIB)
        tz_wib = timezone(timedelta(hours=7))
        timestamp_now = datetime.now(tz_wib).strftime('%Y-%m-%d %H:%M:%S')
        st.info(f"🕐 Timestamp Laporan: **{timestamp_now} WIB**")
        
        st.markdown('<div class="upload-divider"></div>', unsafe_allow_html=True)

        # ─── 📸 CAMERA INPUT & MEDIA UPLOADER ───
        st.markdown("### 📸 Ambil Foto Evidence Lapangan")
        upload_method = st.radio("Metode Pengambilan:", ["📷 Kamera HP (Live)", "🖼️ Galeri File"], horizontal=True, key="method_upload_tab1")
        
        photo_file = st.camera_input("Ambil Foto Progres") if upload_method == "📷 Kamera HP (Live)" else st.file_uploader("Pilih File Foto", type=['jpg','jpeg','png'])
        
        if photo_file:
            st.image(photo_file, caption="Preview Foto Evidence", width=350)
            notes = st.text_area("📝 Catatan Progres & Isu Kritis", placeholder="Tulis deskripsi progres nyata atau kendala material di lapangan...")
            
            # ─── 💾 PROSES SIMPAN SINKRON TOTAL ───
            if st.button("💾 SIMPAN METADATA & UPLOAD FOTO KE G-DRIVE", type="primary", use_container_width=True, key="btn_submit_tab1"):
                
                # 🛠️ VALIDASI CRITICAL CRASH PREVENT: Pastikan data text input tidak kosong di sisi Python
                if not lat or not lng or lat.strip() == "" or lng.strip() == "":
                    st.error("❌ GAGAL SIMPAN: Sistem mendeteksi koordinat masih kosong! Silakan klik ulang tombol 'AMBIL GPS & AUTO-ALAMAT' di atas sampai angka muncul stabil di kotak input.")
                    st.stop()
                
                with st.spinner("📤 Sedang memproses file ke Google Drive & Sinkronisasi database Supabase..."):
                    file_bytes = photo_file.read()
                    
                    # 🏭 Langkah 1: Push Binary File ke Google Drive Target Folder
                    filename_formatted = f"photo_{timestamp_now.replace(':', '-')}_{site_name}_{uploaded_by}.jpg"
                    drive_id, drive_url = upload_to_google_drive(file_bytes, filename_formatted)
                    
                    # 🏭 Langkah 2: Build Payload JSON untuk Skema Database `project_photos`
                    photo_id = generate_id()
                    supabase_payload = {
                        'id': photo_id,
                        'project_id': sel_site,
                        'site_name': site_name,
                        'milestone_id': sel_ms if sel_ms else '',
                        'milestone_name': ms_name,
                        'photo_url': drive_url if drive_url else '', # Menyimpan URL WebView Google Drive asli
                        'drive_file_id': drive_id if drive_id else photo_id,
                        'latitude': str(lat),
                        'longitude': str(lng),
                        'address': address if address else '',
                        'timestamp_taken': timestamp_now,
                        'uploaded_by': uploaded_by,
                        'notes': notes
                    }
                    
                    # 🏭 Langkah 3: Eksekusi Injeksi Row ke Supabase DB
                    try:
                        insert_row("project_photos", supabase_payload)
                        
                        # ─── 📦 INTERACTION RESPONSES ───
                        if drive_url:
                            st.success("✅ Foto Evidence & Koordinat Lapangan Berhasil Tersimpan!")
                            st.toast("📸 Berhasil disinkronisasi ke Cloud!", icon="📸")
                            st.balloons()
                            
                            # Bersihkan sisa state cache alamat lama sebelum auto-reload
                            if 'auto_address' in st.session_state: 
                                del st.session_state['auto_address']
                                
                            st.rerun()
                        else:
                            st.warning("⚠️ Metadata tersimpan di database, tetapi file fisik gagal diupload ke Google Drive. Periksa kembali struktur Service Account Anda.")
                            
                    except Exception as db_err:
                        st.error(f"❌ Gagal sinkronisasi data ke Supabase: {str(db_err)}")
    
    # ─────────────────────────────────────────────────────────────
    # TAB 2: GALERI FOTO (INTEGRASI GOOGLE DRIVE LINK)
    # ─────────────────────────────────────────────────────────────
    with tab2:
        st.subheader("🖼️ Galeri Foto Evidence Lapangan")
        photos_df = read_sheet("project_photos")
        
        if not photos_df.empty:
            st.metric("Total Foto Evidence", len(photos_df))
            
            # Filter Site
            opts_site_filter = ['Tampilkan Semua Site'] + sorted(sites_df['id'].tolist())
            site_filter = st.selectbox("Filter Galeri Berdasarkan Site:", opts_site_filter, key="galeri_filter_unique",
                format_func=lambda x: 'Tampilkan Semua Site' if x=='Tampilkan Semua Site' else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
            
            filtered = photos_df.copy()
            if site_filter != 'Tampilkan Semua Site': 
                filtered = filtered[filtered['project_id'] == site_filter]
            
            # Rendering Gallery Cards profesional (Side-by-Side)
            if not filtered.empty:
                # Ambil 20 foto terbaru
                filtered = filtered.sort_values(by='timestamp_taken', ascending=False).head(20)
                
                cols = st.columns(2)
                for i, (_, row) in enumerate(filtered.iterrows()):
                    with cols[i % 2]:
                        # Data Cleaning & Fallbacks
                        ms_n = row.get('milestone_name', 'General Photo') or 'General Photo'
                        s_n = row.get('site_name', '-')
                        up_b = row.get('uploaded_by', 'PIC')
                        ts_t = row.get('timestamp_taken', '-') or '-'
                        lat_v = row.get('latitude', '-') or '-'
                        lng_v = row.get('longitude', '-') or '-'
                        addr_v = row.get('address', '-') or '-'
                        notes_v = row.get('notes', '')
                        photo_url = row.get('photo_url', '')
                        
                        # Premium Card CSS/HTML
                        card_html = f"""
                        <div style="background:white;border-radius:12px;padding:12px;margin:8px 0;box-shadow:0 3px 10px rgba(0,0,0,0.06);border-left:4px solid #3B82F6;transition:transform 0.2s;">
                            <div style="font-weight:700;color:#1E293B;font-size:0.95rem;display:flex;justify-content:space-between;">
                                <span>🏗️ {ms_n[:35]}</span>
                                <span style="font-size:0.75rem;color:#94A3B8;">WIB</span>
                            </div>
                            <div style="font-size:0.85rem;color:#64748B;margin:3px 0 6px 0;font-weight:600;">📍 {s_n}</div>
                            
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;font-size:0.75rem;color:#64748B;margin-top:8px;">
                                <div>🕐 {ts_t[:16]}</div>
                                <div>👷 PIC: {up_b}</div>
                                <div>🌐 {lat_v}, {lng_v}</div>
                            </div>
                            <div style="font-size:0.7rem;color:#94A3B8;margin-top:6px;border-top:1px solid #EFF6FF;padding-top:4px;">📫 {addr_v[:60]}...</div>
                        """
                        
                        # Injeksi Link Drive jika tersedia
                        if photo_url:
                            card_html += f'<div style="margin-top:8px;border-top:1px solid #EFF6FF;padding-top:4px;"><a href="{photo_url}" target="_blank" style="color:#3B82F6;text-decoration:none;font-weight:700;font-size:0.8rem;">📎 Buka Foto di Google Drive 🚀</a></div>'
                        
                        # Injeksi Catatan jika tersedia
                        if notes_v:
                            card_html += f'<div style="font-size:0.75rem;color:#475569;background:#F8FAFC;border-radius:6px;padding:6px;margin-top:8px;">📝 {notes_v[:100]}</div>'
                            
                        card_html += '</div>'
                        st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.info("ℹ️ Tidak ditemukan foto pada site hasil filter galeri saat ini.")
        else:
            st.info("📭 Belum ada foto evidence yang tersimpan di database (project_photos).")

if __name__ == "__main__":
    st.set_page_config(page_title="Project Photo Evidence Center", layout="wide")
    photo_page()
