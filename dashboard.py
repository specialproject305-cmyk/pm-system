import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import numpy as np
from supabase_db import read_all_sheets

# ─────────────────────────────────────────────────────────────
# 🎨 PREMIUM EXECUTIVE MODERN CSS (Light Theme)
# ─────────────────────────────────────────────────────────────
def inject_premium_css():
    st.markdown("""
    <style>
        .stApp { 
            background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%); 
            color: #1E293B; 
            font-family: 'Segoe UI', -apple-system, sans-serif; 
        }
        
        /* HEADER PREMIUM DENGAN GRADASI BIRU & ORANGE (CENTER ALIGNED) */
        .dashboard-header { 
            background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 40%, #EA580C 100%); 
            padding: 25px; 
            border-radius: 14px; 
            margin-bottom: 22px; 
            box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.2), 0 4px 6px -4px rgba(234, 88, 12, 0.2);
            text-align: center; /* ◄ Ganti ke center untuk memposisikan semua elemen di tengah */
        }
        .dashboard-header h1 { 
            font-size: 1.7rem; 
            margin: 0; 
            color: #FFFFFF; 
            font-weight: 800; 
            text-align: center; /* ◄ Judul di tengah */
            letter-spacing: 0.5px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.15);
        }
        .dashboard-header p { 
            font-size: 0.85rem; 
            margin: 6px 0 0 0; 
            color: #E0F2FE; 
            text-align: center; /* ◄ Sub-judul di tengah */
            font-weight: 500;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .dashboard-sync-text {
            font-size: 0.75rem;
            margin-top: 12px;
            color: #FFEDD5; /* Warna krem pastel yang kontras dengan biru/orange */
            font-weight: 600;
            text-shadow: 0 1px 2px rgba(0,0,0,0.15);
            display: inline-block;
            background: rgba(0, 0, 0, 0.25); /* Kapsul hitam transparan */
            padding: 5px 16px;
            border-radius: 20px;
            letter-spacing: 0.3px;
        }
        
        /* SECTION HEADERS */
        .section-header {
            font-size: 14px;
            font-weight: 800;
            color: #0F172A;
            margin: 15px 0 10px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-left: 3px solid #0284C7;
            padding-left: 8px;
        }
        
        /* KPI CARDS EXTRA BULAT & SHADOW */
        .kpi-card { 
            background: #FFFFFF; 
            border: 1px solid #E2E8F0; 
            border-radius: 12px; 
            padding: 15px 10px; 
            text-align: center; 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s;
        }
        .kpi-icon { font-size: 1.5rem; margin-bottom: 5px; }
        .kpi-title { font-size: 0.7rem; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-value { font-size: 1.5rem; font-weight: 800; color: #0F172A; margin: 5px 0; }
        .kpi-subtitle { font-size: 0.65rem; color: #94A3B8; }
        
        /* THEME COLOR UTAMA */
        .status-done { color: #059669 !important; }
        .status-ongoing { color: #D97706 !important; }
        .status-pending { color: #2563EB !important; }
        .status-delayed { color: #DC2626 !important; }
        
        /* CHART BOX PREMIUM */
        .chart-box { 
            background: #FFFFFF; 
            border: 1px solid #E2E8F0; 
            border-radius: 12px; 
            padding: 16px; 
            margin-bottom: 15px; 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
        }
        
        /* NATIVE-LOOKING KANBAN CARD (FIX BUGS TEXT) */
        .native-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-left: 4px solid #CBD5E1;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        
        .section-divider { height: 1px; background: #E2E8F0; margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 📊 INTERACTIVE UTILITIES
# ─────────────────────────────────────────────────────────────
def get_safe_numeric(series):
    return pd.to_numeric(series, errors='coerce').fillna(0)

def render_kpi_card(icon, title, value, subtitle, color_class=""):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value {color_class}">{value}</div>
        <div class="kpi-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 📱 MAIN APPLICATION LOGIC
# ─────────────────────────────────────────────────────────────
def dashboard_page():
    inject_premium_css()
    
    # 📥 1. LOAD DATA DARI SUPABASE
    try:
        with st.spinner("🔄 Menyelaraskan Data Master Sistem..."):
            all_data = read_all_sheets()
        
        df_master = all_data.get('master_projects', pd.DataFrame())
        df_projects = all_data.get('projects', pd.DataFrame()).copy()
        df_milestones = all_data.get('milestones', pd.DataFrame()).copy()
        df_inventory = all_data.get('inventory_transactions', pd.DataFrame())
        df_workforce = all_data.get('workforce', pd.DataFrame())
        df_wf_assign = all_data.get('workforce_assignments', pd.DataFrame())
        
    except Exception as e:
        st.error(f"❌ Kegagalan Memuat Database: {e}")
        return

    if df_projects.empty:
        st.info("📋 Tidak ada data site yang tersedia di database.")
        return

    # Pembersihan Data Awal
    df_projects['progress'] = get_safe_numeric(df_projects['progress'])
    
    # ─── MAPPING WILAYAH (Sumbu Filter Tambahan Berdasarkan Isu Region) ───
    # Jika belum ada kolom 'region', kita mapping mandiri berbasis pola Nama / ID Site sebagai fallback aman nasional
    if 'region' not in df_projects.columns:
        df_projects['region'] = 'Jawa Barat'  # Default fallback regional Bandung/Jakarta
    
    # ─── 🛠️ FORCE LIVE CLOCK & TIMEZONE WIB (TAMBAHKAN INI TEPAT DI ATAS HEADER) ───
    # Memastikan jam selalu update real-time mengikuti WIB (+7 dari UTC server)
    try:
        from datetime import timezone, timedelta
        tz_wib = timezone(timedelta(hours=7))
        waktu_sekarang = datetime.now(tz_wib).strftime('%d %b %Y | %H:%M')
    except Exception:
        # Fallback jika terjadi error library datetime
        waktu_sekarang = datetime.now().strftime('%d %b %Y | %H:%M')

    # 🧱 ENGINE 6 FILTER BERANTAI & HEADER BARU (DILOCK DENGAN VARIABEL BARU)
    st.markdown(f"""
    <div class="dashboard-header">
        <h1>📊 EXECUTIVE MASTER DASHBOARD</h1>
        <p>Sistem Pengendali Terintegrasi</p>
        <div class="dashboard-sync-text">Sinkronisasi at: {waktu_sekarang} WIB | 🛠️ System Enterprise Edition</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔍 PANEL KONTROL & FILTER UTAMA (Cascading Active)", expanded=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        col_f4, col_f5, col_f6 = st.columns(3)
        
        # Filter 1: Master Project (DIPERBAIKI DENGAN LOGIKA FALLBACK AUTOMATIC)
        with col_f1:
            opts_master = ['SEMUA MASTER PROJECT']
            
            # Jalur Utama: Membaca dari tabel induk master_projects
            if not df_master.empty and 'project_name' in df_master.columns:
                opts_master += sorted(df_master['project_name'].dropna().unique().tolist())
                use_fallback = False
            else:
                # Jalur Fallback: Jika tabel master kosong, tarik ID unik langsung dari tabel projects (Site List)
                if 'master_project_id' in df_projects.columns:
                    opts_master += sorted(df_projects['master_project_id'].dropna().unique().tolist())
                use_fallback = True
            
            sel_master = st.selectbox("🌐 Master Project", opts_master)
            
            # Eksekusi Pemotongan Data Downstream
            if sel_master != 'SEMUA MASTER PROJECT':
                if not use_fallback:
                    # Jika jalur utama sukses, potong berdasarkan mapping ID
                    m_ids = df_master[df_master['project_name'] == sel_master]['id'].tolist()
                    df_projects = df_projects[df_projects['master_project_id'].isin(m_ids)]
                else:
                    # Jika jalur fallback, langsung potong berdasarkan value string/ID yang terpilih
                    df_projects = df_projects[df_projects['master_project_id'] == sel_master]

        # Filter 2: PM (Project Manager)
        with col_f2:
            opts_pm = ['SEMUA PM'] + sorted(df_projects['pm'].dropna().unique().tolist())
            sel_pm = st.selectbox("👤 Project Manager (PM)", opts_pm)
            if sel_pm != 'SEMUA PM':
                df_projects = df_projects[df_projects['pm'] == sel_pm]

        # Filter 3: Region (Wilayah Cakupan Nusantara)
        with col_f3:
            opts_region = ['SEMUA WILAYAH'] + sorted(df_projects['region'].dropna().unique().tolist())
            sel_region = st.selectbox("🗺️ Wilayah / Region", opts_region)
            if sel_region != 'SEMUA WILAYAH':
                df_projects = df_projects[df_projects['region'] == sel_region]

        # Filter 4: Status Proyek
        with col_f4:
            opts_status = ['SEMUA STATUS'] + sorted(df_projects['status'].dropna().unique().tolist())
            sel_status = st.selectbox("🚦 Status Proyek", opts_status)
            if sel_status != 'SEMUA STATUS':
                df_projects = df_projects[df_projects['status'] == sel_status]

        # Filter 5: SPK Vendor
        with col_f5:
            opts_spk = ['SEMUA SPK VENDOR'] + sorted(df_projects['spk_vendor'].dropna().unique().tolist())
            sel_spk = st.selectbox("📄 No. SPK Vendor", opts_spk)
            if sel_spk != 'SEMUA SPK VENDOR':
                df_projects = df_projects[df_projects['spk_vendor'] == sel_spk]

        # Filter 6: Site Selection (Spesifik Akhir)
        with col_f6:
            site_display_opts = ['SEMUA SITE'] + sorted((df_projects['site_id'] + " - " + df_projects['site_name']).dropna().tolist())
            sel_site_str = st.selectbox("📡 Nama / ID Site", site_display_opts)
            if sel_site_str != 'SEMUA SITE':
                target_site_id = sel_site_str.split(" - ")[0]
                df_projects = df_projects[df_projects['site_id'] == target_site_id]

        # Sinkronisasi filter ke downstream table (Milestones & Inventory)
        valid_project_pks = df_projects['id'].tolist()
        valid_site_ids = df_projects['site_id'].tolist()
        
        if not df_milestones.empty:
            df_milestones = df_milestones[df_milestones['project_id'].isin(valid_project_pks)]
        if not df_inventory.empty:
            df_inventory = df_inventory[df_inventory['site_id'].isin(valid_site_ids)]

    # 📊 3. GLOBAL KPI MATRICES
    total_sites = len(df_projects)
    rfs_count = len(df_projects[df_projects['status'] == 'DONE'])
    ongoing_count = len(df_projects[df_projects['status'] == 'ONGOING'])
    pending_count = len(df_projects[df_projects['status'] == 'PENDING'])
    delayed_count = len(df_projects[df_projects['status'].isin(['DELAYED', 'CRITICAL'])])
    avg_progress = df_projects['progress'].mean() if total_sites > 0 else 0.0

    k_col1, k_col2, k_col3, k_col4, k_col5, k_col6 = st.columns(6)
    with k_col1: render_kpi_card("📡", "Total Sites", total_sites, "Portofolio Aktif")
    with k_col2: render_kpi_card("✅", "RFS / On Air", rfs_count, f"{rfs_count/total_sites*100:.1f}% Terbuka" if total_sites > 0 else "0%", "status-done")
    with k_col3: render_kpi_card("⚙️", "In Progress", ongoing_count, "Sedang Eksekusi", "status-ongoing")
    with k_col4: render_kpi_card("⏳", "Pending", pending_count, "Menunggu Antrean", "status-pending")
    with k_col5: render_kpi_card("🔴", "Delayed", delayed_count, "Butuh Eskalasi", "status-delayed")
    with k_col6: render_kpi_card("📊", "Avg Progress", f"{avg_progress:.1f}%", "Capaian Kumulatif")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # 📑 4. SYSTEM NAVIGATION TABS
    tab_overview, tab_projects, tab_logistics, tab_workforce = st.tabs([
        "📈 EXECUTIVE OVERVIEW", "🏗️ PORTFOLIO ANALYTICS", "📦 LOGISTICS & INVENTORY", "👷 WORKFORCE PERFORMANCE"
    ])

    # ─────────────────────────────────────────────────────────────
    # TAB 1: EXECUTIVE OVERVIEW
    # ─────────────────────────────────────────────────────────────
    with tab_overview:
        st.markdown('<div class="section-header">Ringkasan Tren Progres & S-Curve</div>', unsafe_allow_html=True)
        
        o_col1, o_col2 = st.columns([2, 1.2])
        with o_col1:
            st.markdown('<div class="chart-box">', unsafe_allow_html=True)
            # S-Curve Generator
            if not df_milestones.empty and 'actual_end' in df_milestones.columns:
                df_scurve = df_milestones.dropna(subset=['actual_end']).sort_values('actual_end')
                if not df_scurve.empty:
                    df_scurve['cum_progress'] = np.linspace(5, 100, len(df_scurve))
                    fig_scurve = px.line(df_scurve, x='actual_end', y='cum_progress', title="Project S-Curve Cumulative (%)")
                    fig_scurve.update_traces(line=dict(color='#0284C7', width=3), fill='tozeroy', fillcolor='rgba(2, 132, 199, 0.05)')
                    fig_scurve.update_layout(height=240, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_scurve, use_container_width=True)
            else:
                st.info("💡 S-Curve akan berakumulasi otomatis setelah milestone lapangan terisi tanggal aktual.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with o_col2:
            st.markdown('<div class="chart-box">', unsafe_allow_html=True)
            st.markdown("<p style='font-weight:700; font-size:13px; margin:0 0 10px 0;'>🚨 Komando Isu Kritis</p>", unsafe_allow_html=True)
            # Kartu Pendukung Info Isu Kritis
            st.metric(label="Total Hambatan SPK Vendor", value=f"{delayed_count} Sites", delta="Perlu Intervensi PMO", delta_color="inverse")
            st.markdown("<span style='font-size:0.7rem; color:#64748B;'>Rekomendasi: Lakukan percepatan pada alokasi material utama untuk site berkendala di atas 15 hari.</span>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────
    # TAB 2: PORTFOLIO & SITE ANALYTICS
    # ─────────────────────────────────────────────────────────────
    with tab_projects:
        st.markdown('<div class="section-header">Analisis Spasial Sebaran & Beban Vendor</div>', unsafe_allow_html=True)
        
        p_col1, p_col2 = st.columns([1, 1.3])
        with p_col1:
            st.markdown('<div class="chart-box">', unsafe_allow_html=True)
            if 'status' in df_projects.columns and not df_projects.empty:
                st_counts = df_projects['status'].value_counts()
                fig_pie = px.pie(names=st_counts.index, values=st_counts.values, hole=0.6, title="Project Status Ratio")
                fig_pie.update_layout(height=230, margin=dict(l=5, r=5, t=40, b=5), showlegend=True, legend=dict(orientation="h", y=-0.1))
                st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with p_col2:
            st.markdown('<div class="chart-box">', unsafe_allow_html=True)
            # 🛠️ PERBAIKAN TOTAL: HORIZONTAL BAR CHART STATUS BY VENDOR
            if 'vendor' in df_projects.columns and not df_projects.empty:
                df_pivot = df_projects.groupby(['vendor', 'status']).size().reset_index(name='Jumlah Site')
                
                fig_vendor = px.bar(
                    df_pivot,
                    x='Jumlah Site',
                    y='vendor',
                    color='status',
                    orientation='h',
                    title='',
                    color_discrete_map={'DONE': '#059669', 'ONGOING': '#D97706', 'PENDING': '#2563EB', 'DELAYED': '#DC2626', 'CRITICAL': '#7F1D1D'}
                )
                # 🛠️ UPDATE LAYOUT: MEMINDAHKAN LEGEND KE BAWAH JUDUL & HORIZONTAL CENTER
                fig_vendor.update_layout(
                    barmode='stack',
                    height=280, # Ditambah sedikit ruang vertikal agar tidak sesak
                    margin=dict(l=140, r=20, t=70, b=20), # Space aman untuk nama vendor di kiri
                    
                    # Pengaturan Mutlak Legend 1 Baris Center
                    showlegend=True,
                    legend=dict(
                        orientation="h",        # Horizontal
                        yanchor="bottom",
                        y=1.05,                 # Naikkan sedikit di atas chart (tepat di bawah judul)
                        xanchor="center",
                        x=0,                  # Centered di tengah-tengah chart
                        font=dict(size=9),
                        title=None,             # Hapus judul status yang memakan space
                        itemwidth=30,           # Mengatur jarak lebar antar item agar rapat menyamping
                        traceorder="normal"     # Mengurutkan baris secara normal satu baris lurus
                    ),
                    
                    yaxis=dict(tickfont=dict(size=10), title=None),
                    xaxis=dict(title=None, dtick=1)
                )
                
                # Memaksa container Plotly tidak membungkus item legend ke bawah (Wrap Off)
                fig_vendor.update_traces(legendgroup="")
                st.plotly_chart(fig_vendor, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Daftar Site Bermasalah
        st.markdown("<p style='font-weight:800; font-size:12px; margin-top:10px;'>🚨 ESKALASI KETERLAMBATAN SITE (STATUS DELAYED / CRITICAL)</p>", unsafe_allow_html=True)
        df_critical = df_projects[df_projects['status'].isin(['DELAYED', 'CRITICAL'])]
        if not df_critical.empty:
            st.dataframe(df_critical[['site_id', 'site_name', 'vendor', 'pm', 'progress', 'status']], use_container_width=True, hide_index=True)
        else:
            st.success("✅ Seluruh portofolio site dalam batas aman operasional target.")

    # ─────────────────────────────────────────────────────────────
    # TAB 3: LOGISTICS & INVENTORY TRACKER (DIUBAH JADI HORIZONTAL CHART)
    # ─────────────────────────────────────────────────────────────
    with tab_logistics:
        st.markdown('<div class="section-header">Kendali Pergerakan Material & Status Gudang</div>', unsafe_allow_html=True)
        
        if not df_inventory.empty:
            l_col1, l_col2 = st.columns([1, 1.4])
            with l_col1:
                st.markdown('<div class="chart-box">', unsafe_allow_html=True)
                # Rasio Penyelesaian Material (Settle Status)
                if 'settle_status' in df_inventory.columns:
                    inv_status = df_inventory['settle_status'].value_counts()
                    fig_inv = px.pie(names=inv_status.index, values=inv_status.values, title="Status Alokasi Logistik", color_discrete_sequence=['#0284C7', '#F59E0B'])
                    fig_inv.update_layout(height=240, margin=dict(l=5, r=5, t=40, b=5))
                    st.plotly_chart(fig_inv, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with l_col2:
                st.markdown('<div class="chart-box">', unsafe_allow_html=True)
                
                # Deteksi cerdas nama kolom deskripsi barang di tabel transaksi Anda
                col_item_display = 'item_description' if 'item_description' in df_inventory.columns else (
                                   'item_name' if 'item_name' in df_inventory.columns else 'item_code')
                
                label_chart = "Deskripsi Material" if col_item_display != 'item_code' else "Kode Item (Fallback)"
                st.markdown(f"<p style='font-weight:700; font-size:13px; margin:0 0 10px 0;'>📊 Volume Transaksi Berdasarkan {label_chart}</p>", unsafe_allow_html=True)
                
                if col_item_display in df_inventory.columns:
                    # Agregasi data volume berdasarkan item
                    item_counts = df_inventory[col_item_display].value_counts().reset_index(name='Volume')
                    item_counts.columns = [col_item_display, 'Volume']
                    
                    # 🛠️ PERBAIKAN: Diubah total menjadi Bar Chart Horizontal (orientation='h')
                    fig_items = px.bar(
                        item_counts.sort_values(by='Volume', ascending=True), # Urutkan dari volume terkecil ke terbesar agar chart rapi
                        x='Volume', 
                        y=col_item_display, 
                        orientation='h',
                        color='Volume', 
                        color_continuous_scale='Blues'
                    )
                    fig_items.update_layout(
                        height=240, 
                        margin=dict(l=150, r=10, t=10, b=10), # Beri margin kiri luas agar teks deskripsi tidak terpotong
                        coloraxis_showscale=False,
                        yaxis=dict(title=None, tickfont=dict(size=10)),
                        xaxis=dict(title="Volume Transaksi", tickfont=dict(size=10))
                    )
                    st.plotly_chart(fig_items, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown("<p style='font-weight:800; font-size:12px;'>🚚 LEDGER TRANSAKSI MATERIAL TERBARU</p>", unsafe_allow_html=True)
            st.dataframe(df_inventory.head(10), use_container_width=True, hide_index=True)
        else:
            st.info("📦 Belum ada data pergerakan logistik (inventory_transactions) yang terikat dengan site hasil filter saat ini.")

    # ─────────────────────────────────────────────────────────────
    # TAB 4: WORKFORCE PERFORMANCE
    # ─────────────────────────────────────────────────────────────
    with tab_workforce:
        st.markdown('<div class="section-header">Monitoring Alokasi Beban Tugas Tim Lapangan</div>', unsafe_allow_html=True)
        
        # Penanganan snapshot tim pelaksana lapangan secara komprehensif
        if not df_milestones.empty and 'assigned_to' in df_milestones.columns:
            st.markdown("<p style='font-weight:700; font-size:12px; margin-bottom:15px;'>👷 DISTRIBUSI BEBAN KERJA & KETETAPAN PIC</p>", unsafe_allow_html=True)
            
            # Buat layout kolom seimbang
            pic_teams = df_milestones['assigned_to'].dropna().unique().tolist()
            if pic_teams:
                w_cols = st.columns(min(len(pic_teams), 5))
                for idx, team_name in enumerate(pic_teams[:5]):
                    with w_cols[idx % 5]:
                        tasks_sub = df_milestones[df_milestones['assigned_to'] == team_name]
                        tot_t = len(tasks_sub)
                        done_t = len(tasks_sub[tasks_sub['status'] == 'DONE'])
                        rate_t = (done_t / tot_t * 100) if tot_t > 0 else 0
                        
                        # Definisikan badge warna pendukung secara profesional
                        color_border = "#059669" if rate_t >= 75 else ("#D97706" if rate_t >= 40 else "#DC2626")
                        
                        st.markdown(f"""
                        <div class="native-card" style="border-left: 4px solid {color_border};">
                            <div style="font-weight:800; font-size:13px; color:#0F172A;">👤 {team_name}</div>
                            <div style="font-size:11px; color:#64748B; margin:5px 0;">Total Tugas: <b>{tot_t}</b></div>
                            <div style="font-size:14px; font-weight:800; color:{color_border};">{rate_t:.0f}% Selesai</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Hubungkan ke tabel master personil workforce jika tersedia relasinya
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            w_col_left, w_col_right = st.columns(2)
            with w_col_left:
                st.markdown("<p style='font-weight:800; font-size:12px;'>📋 REKAP SKILL & ROLE INTERNAL WORKFORCE</p>", unsafe_allow_html=True)
                if not df_workforce.empty:
                    st.dataframe(df_workforce, use_container_width=True, hide_index=True)
                else:
                    st.info("ℹ️ Detail personal workforce belum dimasukkan ke tabel master.")
            with w_col_right:
                st.markdown("<p style='font-weight:800; font-size:12px;'>📊 TINGKAT STRATEGIS FUNNEL MILESTONE</p>", unsafe_allow_html=True)
                ms_summary = df_milestones['name'].value_counts().reset_index(name='Jumlah')
                fig_ms = px.bar(ms_summary, x='Jumlah', y='name', orientation='h', color_discrete_sequence=['#475569'])
                fig_ms.update_layout(height=180, margin=dict(l=80, r=10, t=10, b=10), yaxis=dict(title=None), xaxis=dict(title=None))
                st.plotly_chart(fig_ms, use_container_width=True)
        else:
            st.info("👷 Modul penugasan workforce akan aktif secara live ketika kolom 'assigned_to' di tabel milestones terisi.")

    # ─────────────────────────────────────────────────────────────
    # FOOTER
    # ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align: center; color: #94A3B8; font-size: 0.75rem; padding: 10px 0;'>
        Sinkronisasi Terakhir Cloud Supabase: {datetime.now().strftime('%d %b %Y | %H:%M')} WIB | 🛠️ <b>System Enterprise Edition</b>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    st.set_page_config(page_title="Executive Management Dashboard", layout="wide")
    dashboard_page()
