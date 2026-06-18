import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from supabase_db import read_sheet, insert_row, generate_id
import streamlit.components.v1 as components
import requests
import json

# ═══════════════════════════════════════
# KONFIGURASI OPERASIONAL
# ═══════════════════════════════════════
LOCATIONIQ_KEY = "pk.01a381b84c8dc483a561e0ddd24b6e6d"  
GOOGLE_DRIVE_FOLDER_ID = "1soOsPCQ3yYF_9P-Yc8EIbdQRFvb61KQd"   

# ═══════════════════════════════════════
# PRE-PROCESS UTILITIES
# ═══════════════════════════════════════
def get_gps_location():
    """Dapatkan lokasi GPS & Alamat langsung dari Browser HP (Fix Syntax F-String)"""
    
    # Menggunakan double {{ }} agar tidak bertabrakan dengan sistem f-string Python
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
                
                const latInput = parent.document.querySelector('input[aria-label="Latitude"]');
                const lngInput = parent.document.querySelector('input[aria-label="Longitude"]');
                const addrInput = parent.document.querySelector('input[aria-label="📫 Address Detail (Auto-Address)"]');
                
                if(latInput) latInput.value = lat;
                if(lngInput) lngInput.value = lng;
                
                try {{
                    const url = `https://us1.locationiq.com/v1/reverse.php?key={LOCATIONIQ_KEY}&lat=${{lat}}&lon=${{lng}}&format=json`;
                    const response = await fetch(url);
                    const data = await response.json();
                    const address = data.display_name || '';
                    
                    if(addrInput) addrInput.value = address;
                    
                    if(latInput) latInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    if(lngInput) lngInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    if(addrInput) addrInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    
                    status.innerText = '✅ GPS & Alamat Berhasil Disinkronisasi! Silakan isi Catatan & Simpan.';
                    status.style.color = '#059669';
                }} catch (err) {{
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

def get_address_from_locationiq(lat, lng):
    """Fallback function jika dibutuhkan di luar client-side"""
    if not lat or not lng: return ''
    try:
        url = f"https://us1.locationiq.com/v1/reverse.php?key={LOCATIONIQ_KEY}&lat={lat}&lon={lng}&format=json"
        res = requests.get(url, timeout=7)
        data = res.json()
        return data.get('display_name', '')
    except:
        return ''

def upload_to_google_drive(file_bytes, file_name):
    """Upload file ke Google Drive via Service Account & Streamlit Secrets"""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
        import io
        
        creds_dict = st.secrets.get("drive_service_account")
        if not creds_dict:
            return None, None
            
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=['https://www.googleapis.com/auth/drive.file'])
        
        service = build('drive', 'v3', credentials=credentials)
        file_metadata = {'name': file_name, 'parents': [GOOGLE_DRIVE_FOLDER_ID]}
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='image/jpeg', resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        return file.get('id'), file.get('webViewLink')
    except Exception as e:
        st.warning(f"⚠️ Upload ke Drive gagal: {str(e)[:50]}")
        return None, None

# ═══════════════════════════════════════
# MAIN APPLICATION PAGE
# ═══════════════════════════════════════
def photo_page():
    st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 2px solid #DBEAFE; }
        .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; background: #EFF6FF; }
        .upload-divider { height: 1px; background: #DBEAFE; margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📸 Project Photo Evidence")
    st.caption("Foto progress konstruksi tower dengan GPS murni HP & auto-address")
    
    try:
        sites_df = read_sheet("projects")
        ms_df = read_sheet("milestones")
        if sites_df.empty:
            st.info("📋 Belum ada site terdaftar di database."); return
    except Exception as e:
        st.error(f"❌ Gagal muat data Supabase: {e}"); return

    tab1, tab2, tab3 = st.tabs(["📸 Upload Foto Lapangan", "🖼️ Galeri Foto Evidence", "📊 Statistik"])
    
    # ─────────────────────────────────────────────────────────────
    # TAB 1: FORM UPLOAD MANAGEMENT
    # ─────────────────────────────────────────────────────────────
    with tab1:
        st.subheader("📸 Form Pengisian Foto Evidence")
        
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

        st.markdown("### 📍 Lokasi Pengambilan Foto")
        get_gps_location() 

        col_lat, col_lng = st.columns(2)
        with col_lat:
            lat = st.text_input("Latitude", key="lat_input", placeholder="Klik tombol di atas...")
        with col_lng:
            lng = st.text_input("Longitude", key="lng_input", placeholder="Klik tombol di atas...")
        
        address = st.text_input("📫 Address Detail (Auto-Address)", key="addr_input", placeholder="Klik tombol di atas...")
        uploaded_by = st.text_input("👷 Uploaded By PIC Lapangan", value=st.session_state.get('user', {}).get('full_name', 'PIC Vendor'))
        
        tz_wib = timezone(timedelta(hours=7))
        timestamp_now = datetime.now(tz_wib).strftime('%Y-%m-%d %H:%M:%S')
        st.info(f"🕐 Timestamp Laporan: **{timestamp_now} WIB**")
        
        st.markdown('<div class="upload-divider"></div>', unsafe_allow_html=True)

        st.markdown("### 📸 Ambil Foto Evidence Lapangan")
        upload_method = st.radio("Metode Pengambilan:", ["📷 Kamera HP (Live)", "🖼️ Galeri File"], horizontal=True, key="method_upload_tab1")
        photo_file = st.camera_input("Ambil Foto Progres") if upload_method == "📷 Kamera HP (Live)" else st.file_uploader("Pilih File Foto", type=['jpg','jpeg','png'])
        
        if photo_file:
            st.image(photo_file, caption="Preview Foto Evidence", width=350)
            notes = st.text_area("📝 Catatan Progres & Isu Kritis", placeholder="Tulis deskripsi progres nyata...")
            
            if st.button("💾 SIMPAN METADATA & UPLOAD FOTO KE G-DRIVE", type="primary", use_container_width=True, key="btn_submit_tab1"):
                
                # ─── 🛡️ PENGAMAN ULANG SINKRONISASI (FORCE GRAB ST.SESSION_STATE) ───
                # Terkadang variabel lokal 'lat' belum update, tapi di st.session_state sudah masuk.
                final_lat = st.session_state.get('lat_input', lat)
                final_lng = st.session_state.get('lng_input', lng)
                final_address = st.session_state.get('addr_input', address)

                if not final_lat or not final_lng or str(final_lat).strip() == "" or str(final_lng).strip() == "":
                    st.error("❌ GAGAL SIMPAN: Sistem Python mendeteksi sinkronisasi koordinat tertunda. Silakan tunggu 1-2 detik setelah klik tombol GPS sebelum menekan tombol simpan, atau ketik spasi sedikit di kolom Latitude agar sistem terpaksa membaca.")
                    st.stop()
                
                with st.spinner("📤 Sedang memproses file ke Google Drive & Supabase..."):
                    file_bytes = photo_file.read()
                    filename_formatted = f"photo_{timestamp_now.replace(':', '-')}_{site_name}_{uploaded_by}.jpg"
                    drive_id, drive_url = upload_to_google_drive(file_bytes, filename_formatted)
                    
                    photo_id = generate_id()
                    supabase_payload = {
                        'id': photo_id,
                        'project_id': sel_site,
                        'site_name': site_name,
                        'milestone_id': sel_ms if sel_ms else '',
                        'milestone_name': ms_name,
                        'photo_url': drive_url if drive_url else '',
                        'drive_file_id': drive_id if drive_id else photo_id,
                        'latitude': str(final_lat),   # Menggunakan data yang sudah aman
                        'longitude': str(final_lng), # Menggunakan data yang sudah aman
                        'address': final_address if final_address else '',
                        'timestamp_taken': timestamp_now,
                        'uploaded_by': uploaded_by,
                        'notes': notes
                    }
                    
                    try:
                        insert_row("project_photos", supabase_payload)
                        st.success("✅ Foto Evidence & Koordinat Lapangan Berhasil Tersimpan!")
                        st.balloons()
                        st.rerun()
                    except Exception as db_err:
                        st.error(f"❌ Gagal sinkronisasi data ke Supabase: {str(db_err)}")

    # ─────────────────────────────────────────────────────────────
    # TAB 2: GALERI CARD RENDER FIX
    # ─────────────────────────────────────────────────────────────
    with tab2:
        st.subheader("🖼️ Galeri Foto Evidence Lapangan")
        try:
            photos_df = read_sheet("project_photos")
        except:
            photos_df = pd.DataFrame()
        
        if not photos_df.empty:
            opts_site_filter = ['Tampilkan Semua Site'] + sorted(sites_df['id'].tolist())
            site_filter = st.selectbox(
                "Filter Galeri Berdasarkan Site:", 
                opts_site_filter, 
                key="galeri_filter_unique",
                format_func=lambda x: 'Tampilkan Semua Site' if x=='Tampilkan Semua Site' else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}"
            )
            
            filtered = photos_df.copy()
            if site_filter != 'Tampilkan Semua Site': 
                filtered = filtered[filtered['project_id'] == site_filter]
            
            if not filtered.empty:
                filtered = filtered.sort_values(by='timestamp_taken', ascending=False).head(20)
                cols = st.columns(2)
                for i, (_, row) in enumerate(filtered.iterrows()):
                    with cols[i % 2]:
                        ms_n = str(row.get('milestone_name') or 'General Photo')
                        s_n = str(row.get('site_name') or '-')
                        up_b = str(row.get('uploaded_by') or 'PIC')
                        ts_t = str(row.get('timestamp_taken') or '-')
                        lat_v = str(row.get('latitude') or '-')
                        lng_v = str(row.get('longitude') or '-')
                        addr_v = str(row.get('address') or '-')
                        notes_v = str(row.get('notes') or '')
                        photo_url = str(row.get('photo_url') or '')
                        
                        # Konstruksi String Murni Tanpa F-String bersarang yang membocorkan Sintaks HTML
                        card_html = f"""
                        <div style="background-color: #ffffff; border-radius: 12px; padding: 16px; margin: 10px 0; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 5px solid #3B82F6;">
                            <div style="font-weight: 700; color: #1E293B; font-size: 1rem; display: flex; justify-content: space-between;">
                                <span>🏗️ {ms_n[:40]}</span>
                                <span style="font-size: 0.75rem; color: #94A3B8; font-weight: 400;">WIB</span>
                            </div>
                            <div style="font-size: 0.85rem; color: #4B5563; margin: 4px 0 10px 0; font-weight: 600;">📍 {s_n}</div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 0.75rem; color: #6B7280; background-color: #F9FAFB; padding: 8px; border-radius: 6px;">
                                <div>Submited: {ts_t[:16]}</div>
                                <div>👷 PIC: {up_b}</div>
                                <div style="grid-column: span 2; color: #374151; font-family: monospace;">🌐 {lat_v}, {lng_v}</div>
                            </div>
                            <div style="font-size: 0.75rem; color: #6B7280; margin-top: 8px; padding-top: 6px; border-top: 1px solid #E5E7EB;">
                                <strong>📫 Alamat:</strong> {addr_v[:120]}...
                            </div>
                        """
                        if photo_url and photo_url.strip() != "":
                            card_html += f"""
                            <div style="margin-top: 10px; padding-top: 6px; border-top: 1px solid #E5E7EB;">
                                <a href="{photo_url}" target="_blank" style="color: #2563EB; text-decoration: none; font-weight: 700; font-size: 0.8rem;">📎 Buka Foto Asli di Google Drive 🚀</a>
                            </div>
                            """
                        if notes_v and notes_v.strip() != "":
                            card_html += f"""
                            <div style="font-size: 0.75rem; color: #1F2937; background-color: #FEF3C7; border-left: 3px solid #D97706; border-radius: 4px; padding: 6px; margin-top: 8px;">
                                <strong>Catatan:</strong> {notes_v[:150]}
                            </div>
                            """
                        card_html += "</div>"
                        st.markdown(card_html, unsafe_allow_html=True)
            else:
                st.info("ℹ️ Tidak ditemukan foto pada site ini.")
        else:
            st.info("📭 Belum ada data foto evidence.")

    # ─────────────────────────────────────────────────────────────
    # TAB 3: STATISTIK
    # ─────────────────────────────────────────────────────────────
    with tab3:
        st.subheader("📊 Statistik Foto")
        if not photos_df.empty:
            import plotly.express as px
            site_counts = photos_df['site_name'].value_counts().reset_index()
            site_counts.columns = ['Site', 'Jumlah']
            fig = px.bar(site_counts, x='Site', y='Jumlah', color='Jumlah', color_continuous_scale=['#3B82F6','#1E40AF'])
            fig.update_layout(height=300, showlegend=False, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
