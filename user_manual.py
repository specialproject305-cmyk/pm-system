import streamlit as st

def user_manual_page():
    st.markdown("""
    <style>
        .manual-header {
            background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%);
            padding: 24px 30px; border-radius: 14px; margin-bottom: 20px;
            color: white; box-shadow: 0 8px 24px rgba(37,99,235,0.2);
        }
        .manual-header h1 { margin:0; font-size:1.8rem; font-weight:800; }
        .manual-header p { margin:5px 0 0; font-size:0.9rem; opacity:0.9; }
        .section-box {
            background: white; border-radius: 12px; padding: 20px;
            margin-bottom: 16px; border-left: 4px solid #2563EB;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .section-box h3 { color: #2563EB; margin-top:0; font-size:1.1rem; }
        .section-box ul { margin:8px 0 0 20px; color: #475569; }
        .section-box li { margin:4px 0; }
        .step-box {
            background: #F0F9FF; border-radius: 8px; padding: 12px 16px;
            margin: 8px 0; border-left: 3px solid #3B82F6;
        }
        .step-box strong { color: #2563EB; }
        .tip-box {
            background: #FFFBEB; border-radius: 8px; padding: 12px 16px;
            margin: 8px 0; border-left: 3px solid #F59E0B;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="manual-header">
        <h1>📖 User Manual PM System</h1>
        <p>Panduan lengkap penggunaan Project Management System</p>
    </div>
    """, unsafe_allow_html=True)

    # Daftar Isi
    with st.expander("📑 DAFTAR ISI (Klik untuk navigasi)", expanded=True):
        st.markdown("""
        1. [Pengenalan Sistem](#1-pengenalan-sistem)
        2. [Cara Login & Role Pengguna](#2-cara-login--role-pengguna)
        3. [Urutan Pengisian Data](#3-urutan-pengisian-data)
        4. [Dashboard](#4-dashboard)
        5. [Site Tracker](#5-site-tracker)
        6. [Milestone Monitoring](#6-milestone-monitoring)
        7. [Field App (untuk PIC Lapangan)](#7-field-app-untuk-pic-lapangan)
        8. [AI Insights & RCA](#8-ai-insights--rca)
        9. [Chat & Notifikasi](#9-chat--notifikasi)
        10. [Export & Reporting](#10-export--reporting)
        11. [Marketing Module](#11-marketing-module)
        12. [Workforce Management](#12-workforce-management)
        13. [Tips & Best Practice](#13-tips--best-practice)
        """)

    st.divider()

    # 1. Pengenalan Sistem
    st.markdown('<div class="section-box" id="1-pengenalan-sistem">', unsafe_allow_html=True)
    st.markdown("### 1. PENGENALAN SISTEM")
    st.markdown("**PM System** adalah aplikasi manajemen proyek tower/infrastruktur berbasis web yang dirancang untuk:")
    st.markdown("- Memantau progress site & milestone secara real-time")
    st.markdown("- Mengelola tugas tim lapangan (PIC) dengan Field App")
    st.markdown("- Menganalisis performa project dengan AI Insights")
    st.markdown("- Mengelola data marketing, workforce, dan inventory")
    st.markdown("- Menyajikan dashboard eksekutif untuk meeting mingguan")
    st.markdown("</div>", unsafe_allow_html=True)

    # 2. Cara Login
    st.markdown('<div class="section-box" id="2-cara-login--role-pengguna">', unsafe_allow_html=True)
    st.markdown("### 2. CARA LOGIN & ROLE PENGGUNA")
    st.markdown("**URL Akses:** `https://pm-system-xxx.streamlit.app`")
    st.markdown("")
    st.markdown("**Role Pengguna:**")
    st.markdown("| Role | Akses |")
    st.markdown("|------|-------|")
    st.markdown("| **Admin** | Semua fitur + Settings + User Management |")
    st.markdown("| **PM / PMO** | Dashboard, Site Tracker, Milestone, AI, Chat, Export |")
    st.markdown("| **Planning** | Dashboard, Site Tracker, Milestone, Export |")
    st.markdown("| **Marketing** | Marketing Dashboard, Marketing Sites, Chat |")
    st.markdown("| **Viewer** | Dashboard, AI, Chat, Presentation, Export |")
    st.markdown("| **PIC (Sitac, Engineering, Project, dll)** | Field App (hanya task miliknya) |")

    st.markdown('<div class="step-box"><strong>🔐 Cara Login:</strong><br>1. Buka URL di browser<br>2. Masukkan Username & Password<br>3. Pilih mode: Full Dashboard atau Field App<br>4. Klik Login</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 3. Urutan Pengisian Data
    st.markdown('<div class="section-box" id="3-urutan-pengisian-data">', unsafe_allow_html=True)
    st.markdown("### 3. URUTAN PENGISIAN DATA")
    st.markdown("**Untuk memulai project baru, ikuti urutan ini:**")
    st.markdown('<div class="step-box"><strong>Step 1:</strong> Buat Master Project (Site Tracker → Tab Master Project)</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-box"><strong>Step 2:</strong> Tambah Site (Site Tracker → Tab Tambah Site) atau Import CSV</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-box"><strong>Step 3:</strong> Generate Milestone Template (Milestone → Tab Template → Generate)</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-box"><strong>Step 4:</strong> PIC update progress via Field App</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-box"><strong>Step 5:</strong> Monitoring via Dashboard & AI Insights</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 4. Dashboard
    st.markdown('<div class="section-box" id="4-dashboard">', unsafe_allow_html=True)
    st.markdown("### 4. DASHBOARD")
    st.markdown("- **KPI Cards**: Total Site, RFS, On Progress, Pending, Delayed, Avg Progress")
    st.markdown("- **PIC Performance**: Completion rate per PIC (Sitac, Engineering, Project, dll)")
    st.markdown("- **Charts**: Donut status, Site by Category, Vendor Status")
    st.markdown("- **Filter**: By PM, By Vendor, By Region")
    st.markdown("- **Refresh**: Tombol Refresh untuk update data terbaru")
    st.markdown("</div>", unsafe_allow_html=True)

    # 5. Site Tracker
    st.markdown('<div class="section-box" id="5-site-tracker">', unsafe_allow_html=True)
    st.markdown("### 5. SITE TRACKER")
    st.markdown("- **Daftar Site**: Tabel semua site dengan filter & search")
    st.markdown("- **Master Project**: Kelola project induk")
    st.markdown("- **Tambah Site**: Form input site baru (Site ID, Site Name, PM, Vendor, dll)")
    st.markdown("- **Import CSV**: Upload data site massal")
    st.markdown("- **Quick Edit**: Edit status & progress site langsung dari tabel")
    st.markdown("</div>", unsafe_allow_html=True)

    # 6. Milestone
    st.markdown('<div class="section-box" id="6-milestone-monitoring">', unsafe_allow_html=True)
    st.markdown("### 6. MILESTONE MONITORING")
    st.markdown("- **Gantt Chart**: Timeline visual semua milestone")
    st.markdown("- **Auto-Generate Template**: 35+ task tower project dalam 1 klik")
    st.markdown("- **Edit Milestone**: Ubah status, progress, PIC, tanggal aktual")
    st.markdown("- **Import CSV**: Upload milestone massal (multi-site)")
    st.markdown("- **Dependency**: Hubungan antar task (task B mulai setelah task A selesai)")
    st.markdown("</div>", unsafe_allow_html=True)

    # 7. Field App
    st.markdown('<div class="section-box" id="7-field-app-untuk-pic-lapangan">', unsafe_allow_html=True)
    st.markdown("### 7. FIELD APP (UNTUK PIC LAPANGAN)")
    st.markdown("Field App adalah tampilan khusus untuk PIC lapangan (Sitac, Engineering, Project, dll).")
    st.markdown("")
    st.markdown("**Fitur Field App:**")
    st.markdown("- **Kanban Board**: Lihat task dalam 4 kolom (Pending, Ongoing, Done, Delayed)")
    st.markdown("- **Update Task**: Klik ✏️ pada task → form pop-up → ubah status, progress, tanggal")
    st.markdown("- **Site Overview**: Lihat semua site yang terkait")
    st.markdown("- **Dashboard**: Performa personal PIC")
    st.markdown("- **AI & Issues**: Prediksi & daftar masalah")
    st.markdown("")
    st.markdown('<div class="tip-box"><strong>💡 Tips:</strong> Setiap PIC hanya melihat task dengan assigned_to = role mereka. Contoh: Engineering hanya lihat task Engineering.</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 8. AI Insights
    st.markdown('<div class="section-box" id="8-ai-insights--rca">', unsafe_allow_html=True)
    st.markdown("### 8. AI INSIGHTS & RCA")
    st.markdown("- **Progress Analysis**: Planned vs Actual, Delay Prediction")
    st.markdown("- **PIC Performance**: SLA Score per PIC")
    st.markdown("- **SLA Compliance**: On SLA vs Breach SLA")
    st.markdown("- **Delay Reason**: Analisis penyebab keterlambatan")
    st.markdown("- **RCA (Root Cause Analysis)**: 5-Why analysis untuk task delayed")
    st.markdown("</div>", unsafe_allow_html=True)

    # 9. Chat
    st.markdown('<div class="section-box" id="9-chat--notifikasi">', unsafe_allow_html=True)
    st.markdown("### 9. CHAT & NOTIFIKASI")
    st.markdown("- **Global Chat**: Diskusi semua tim")
    st.markdown("- **Notifikasi**: Alert untuk milestone terlambat, material kritis")
    st.markdown("- **Telegram Bot**: Kirim laporan otomatis ke grup Telegram")
    st.markdown("</div>", unsafe_allow_html=True)

    # 10. Export
    st.markdown('<div class="section-box" id="10-export--reporting">', unsafe_allow_html=True)
    st.markdown("### 10. EXPORT & REPORTING")
    st.markdown("- **PDF Report**: Generate laporan per site atau mingguan")
    st.markdown("- **Presentation Mode**: 5-slide ringkas untuk weekly meeting")
    st.markdown("- **Download CSV**: Semua tabel bisa di-export ke CSV")
    st.markdown("</div>", unsafe_allow_html=True)

    # 11. Marketing
    st.markdown('<div class="section-box" id="11-marketing-module">', unsafe_allow_html=True)
    st.markdown("### 11. MARKETING MODULE")
    st.markdown("- **Marketing Sites**: Data site dari tim marketing (tenant, SPK, milestone)")
    st.markdown("- **Marketing Dashboard**: Chart & statistik marketing pipeline")
    st.markdown("- **Import CSV**: Upload data marketing massal")
    st.markdown("</div>", unsafe_allow_html=True)

    # 12. Workforce
    st.markdown('<div class="section-box" id="12-workforce-management">', unsafe_allow_html=True)
    st.markdown("### 12. WORKFORCE MANAGEMENT")
    st.markdown("- **Data Pekerja**: Nama, role, skill, status")
    st.markdown("- **Assignment**: Assign pekerja ke milestone")
    st.markdown("- **Attendance**: Absensi harian (Present/Absent/Leave)")
    st.markdown("- **Utilization**: Utilisasi per pekerja")
    st.markdown("</div>", unsafe_allow_html=True)

    # 13. Tips
    st.markdown('<div class="section-box" id="13-tips--best-practice">', unsafe_allow_html=True)
    st.markdown("### 13. TIPS & BEST PRACTICE")
    st.markdown("1. **Update task setiap hari** setelah pekerjaan selesai")
    st.markdown("2. **Isi Actual Start/End** dengan tanggal sebenarnya")
    st.markdown("3. **Gunakan Field App** untuk update cepat dari HP")
    st.markdown("4. **Generate template milestone** untuk setiap site baru")
    st.markdown("5. **Filter by Project** di sidebar untuk fokus ke project tertentu")
    st.markdown("6. **Gunakan Presentation Mode** untuk weekly meeting")
    st.markdown("7. **Set Telegram Bot** untuk notifikasi otomatis")
    st.markdown("8. **Backup data** secara berkala dengan export CSV")
    st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align:center; color:#64748B; font-size:0.85rem;">
        📖 PM System User Manual • Version 3.0 • © 2026
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    user_manual_page()
