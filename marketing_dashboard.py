import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from supabase_db import read_sheet

def inject_marketing_css():
    """Menyuntikkan gaya visual profesional bertema clean-light korporat"""
    st.markdown("""
    <style>
        /* === BASE BACKGROUND & FONT === */
        .stApp { 
            background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
            color: #1E293B;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }
        
        /* === PREMIUM HERO HEADER === */
        .marketing-header {
            background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
            padding: 24px 30px;
            border-radius: 16px;
            margin-bottom: 25px;
            color: white;
            box-shadow: 0 10px 25px rgba(30, 58, 138, 0.15);
            border-left: 6px solid #3B82F6;
        }
        .marketing-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 800;
            color: white !important;
            letter-spacing: -0.5px;
        }
        .marketing-header p {
            margin: 6px 0 0 0;
            font-size: 0.95rem;
            color: #93C5FD;
        }
        
        /* === MODERN KPI CARD DESIGN (RESPONSIVE GRID) === */
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
            margin-bottom: 20px;
        }
        .kpi-box {
            background: #FFFFFF;
            padding: 15px 10px;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        .kpi-box:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            border-color: #3B82F6;
        }
        .kpi-val {
            font-size: 1.8rem;
            font-weight: 800;
            color: #0F172A;
            line-height: 1.1;
        }
        .kpi-lbl {
            font-size: 0.7rem;
            color: #64748B;
            text-transform: uppercase;
            font-weight: 700;
            margin-top: 6px;
            letter-spacing: 0.5px;
        }
        
        /* === KPI ACCENT BORDERS === */
        .kpi-total { border-top: 4px solid #475569; }
        .kpi-spk { border-top: 4px solid #0EA5E9; }
        .kpi-rfs { border-top: 4px solid #10B981; }
        .kpi-erected { border-top: 4px solid #8B5CF6; }
        .kpi-progress { border-top: 4px solid #F59E0B; }
        .kpi-tenant { border-top: 4px solid #3B82F6; }

        /* === CHART CARD WRAPPER === */
        .chart-card {
            background: #FFFFFF;
            padding: 20px;
            border-radius: 14px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }
    </style>
    """, unsafe_allow_html=True)

def style_plotly_chart(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, Segoe UI, sans-serif", color="#334155"),
        margin=dict(t=30, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    fig.update_xaxes(showgrid=False, color="#64748B")
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9", color="#64748B")
    return fig

def marketing_dashboard_page():
    inject_marketing_css()
    
    # ═══════════════════════════════════════
    # DATA LOADING & INITIAL PARSING
    # ═══════════════════════════════════════
    df = read_sheet("marketing_sites")
    
    if df.empty:
        st.info("📋 Belum ada data marketing site.")
        return

    # Buat salinan kolom tanggal bertipe datetime untuk kebutuhan filter tahun
    if 'spk_date' in df.columns:
        df['spk_date_parsed'] = pd.to_datetime(df['spk_date'], errors='coerce')
        df['spk_year'] = df['spk_date_parsed'].dt.year.fillna('No Year').astype(str)
    else:
        df['spk_year'] = 'No Year'

    # Master data untuk KPI Unik global (tidak terpengaruh filter)
    absolute_total_spk = df['spk_number'].nunique() if 'spk_number' in df.columns else 0
    absolute_total_tenant = df['tenant_index'].nunique() if 'tenant_index' in df.columns else 0
        
    # ═══════════════════════════════════════
    # GLOBAL SIDEBAR FILTERS (UPGRADED)
    # ═══════════════════════════════════════
    with st.sidebar:
        st.markdown("<h3 style='margin-bottom:0;'>🎯 Filter Kontrol</h3>", unsafe_allow_html=True)
        st.caption("Filter ini mengontrol seluruh matriks & grafik")
        st.markdown("---")
        
        # 1. Filter Kontrol Baru: Year
        years_list = sorted(df['spk_year'].unique().tolist())
        if 'No Year' in years_list:
            years_list.remove('No Year')
            years_list.append('No Year')
        sel_year = st.selectbox("📅 Pilih Tahun SPK:", ['ALL'] + years_list)
        
        # 2. Filter Kontrol: Tenant
        sel_tenant = st.selectbox(
            "🏢 Pilih Tenant:", 
            ['ALL'] + sorted(df['tenant_index'].dropna().unique().tolist()) if 'tenant_index' in df.columns else ['ALL']
        )
        
        # 3. Filter Kontrol: SPK Status
        sel_status = st.selectbox(
            "📋 Pilih SPK Status:", 
            ['ALL'] + sorted(df['spk_status'].dropna().unique().tolist()) if 'spk_status' in df.columns else ['ALL']
        )
        
        # 4. Filter Kontrol Baru: SPK Number (Free Text Search)
        sel_spk_num = st.text_input("🔍 Cari Nomor SPK:", value="", placeholder="Ketik nomor SPK...")
        
        st.markdown("---")
        
        # Penanganan Filter Data Global
        filtered = df.copy()
        if sel_year != 'ALL': 
            filtered = filtered[filtered['spk_year'] == sel_year]
        if sel_tenant != 'ALL': 
            filtered = filtered[filtered['tenant_index'] == sel_tenant]
        if sel_status != 'ALL': 
            filtered = filtered[filtered['spk_status'] == sel_status]
        if sel_spk_num.strip() != "": 
            filtered = filtered[filtered['spk_number'].astype(str).str.contains(sel_spk_num, case=False, na=False)]
        
        st.download_button(
            label="📥 Export Report (CSV)", 
            data=filtered.to_csv(index=False), 
            file_name=f"marketing_report_{datetime.now().strftime('%Y%m%d')}.csv", 
            mime="text/csv",
            use_container_width=True
        )

    # ═══════════════════════════════════════
    # HEADER BANNER
    # ═══════════════════════════════════════
    st.markdown(f"""
    <div class="marketing-header">
        <h1>📢 Marketing Dashboard Intel</h1>
        <p>Real-time monitoring analitik site, akuisisi tenant, dan pipeline status SPK • {datetime.now().strftime('%d %B %Y')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════
    # METRICS ROW (6 METRICS - RESPONSIVE CONTAINER)
    # ═══════════════════════════════════════
    total_sites_filtered = len(filtered)
    rfs_count = len(filtered[filtered['milestone'] == 'RFS']) if 'milestone' in filtered.columns else 0
    erected_count = len(filtered[filtered['milestone'] == 'Erected']) if 'milestone' in filtered.columns else 0
    on_progress = len(filtered[filtered['milestone'].isin(['On Progress', 'Pending', 'Negosiasi Lahan', 'RFI'])]) if 'milestone' in filtered.columns else 0
    
    # Render menggunakan kontainer CSS Grid agar muat 6 kolom dengan seimbang dan tidak sempit
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-box kpi-total"><div class="kpi-val">{total_sites_filtered}</div><div class="kpi-lbl">📢 Total Sites</div></div>
        <div class="kpi-box kpi-spk"><div class="kpi-val">{absolute_total_spk}</div><div class="kpi-lbl">📄 Total SPK</div></div>
        <div class="kpi-box kpi-tenant"><div class="kpi-val">{absolute_total_tenant}</div><div class="kpi-lbl">🏢 Total Tenant</div></div>
        <div class="kpi-box kpi-rfs"><div class="kpi-val">{rfs_count}</div><div class="kpi-lbl">✅ RFS Done</div></div>
        <div class="kpi-box kpi-erected"><div class="kpi-val">{erected_count}</div><div class="kpi-lbl">🏗️ Erected</div></div>
        <div class="kpi-box kpi-progress"><div class="kpi-val">{on_progress}</div><div class="kpi-lbl">🔄 In Pipeline</div></div>
    </div>
    """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════
    # CHARTS ROW 1
    # ═══════════════════════════════════════
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.subheader("📊 Site Distribution by Tenant")
        if 'tenant_index' in filtered.columns and not filtered.empty:
            tenant_counts = filtered['tenant_index'].value_counts()
            fig1 = px.bar(
                x=tenant_counts.index, 
                y=tenant_counts.values, 
                color=tenant_counts.values, 
                color_continuous_scale='Blugrn',
                labels={'x': 'Tenant', 'y': 'Jumlah Site'}
            )
            fig1.update_layout(height=300, coloraxis_showscale=False)
            st.plotly_chart(style_plotly_chart(fig1), use_container_width=True)
        else:
            st.caption("Tidak ada data untuk filter ini.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_b:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.subheader("📌 Project Milestone Breakdown")
        if 'milestone' in filtered.columns and not filtered.empty:
            ms_counts = filtered['milestone'].value_counts()
            fig2 = px.pie(
                values=ms_counts.values, 
                names=ms_counts.index, 
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            fig2.update_layout(height=300)
            st.plotly_chart(style_plotly_chart(fig2), use_container_width=True)
        else:
            st.caption("Tidak ada data untuk filter ini.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ═══════════════════════════════════════
    # CHARTS ROW 2
    # ═══════════════════════════════════════
    col_c, col_d = st.columns(2)
    
    with col_c:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.subheader("💼 SPK Document Status")
        if 'spk_status' in filtered.columns and not filtered.empty:
            spk_counts = filtered['spk_status'].value_counts()
            fig3 = px.pie(
                values=spk_counts.values, 
                names=spk_counts.index, 
                hole=0.5,
                color=spk_counts.index,
                color_discrete_map={'CLOSE':'#10B981','OPEN':'#3B82F6','DROP':'#EF4444'}
            )
            fig3.update_traces(textposition='inside', textinfo='percent+label')
            fig3.update_layout(height=300)
            st.plotly_chart(style_plotly_chart(fig3), use_container_width=True)
        else:
            st.caption("Tidak ada data untuk filter ini.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_d:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.subheader("🏗️ Job Share by Work Type")
        if 'work_type' in filtered.columns and not filtered.empty:
            wt_counts = filtered['work_type'].value_counts()
            fig4 = px.pie(
                values=wt_counts.values, 
                names=wt_counts.index, 
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig4.update_traces(textposition='inside', textinfo='percent+label')
            fig4.update_layout(height=300)
            st.plotly_chart(style_plotly_chart(fig4), use_container_width=True)
        else:
            st.caption("Tidak ada data untuk filter ini.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ═══════════════════════════════════════
    # INTERACTIVE DATA TABLE
    # ═══════════════════════════════════════
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.subheader("📋 Granular Marketing Sites Data Explorer")
    st.caption("Tabel di bawah ini otomatis ter-filter secara real-time berdasarkan input kontrol Anda.")
    
    display_cols = ['spk_number', 'spk_date', 'tenant_index', 'spk_status', 'site_id_tenant', 'site_name_tenant', 'work_type', 'tower_height', 'milestone']
    valid_cols = [c for c in display_cols if c in filtered.columns]
    
    df_display = filtered[valid_cols].copy()
    
    # Sinkronisasi tipe data aman sebelum dikirim ke komponen visual
    if 'spk_date' in df_display.columns:
        df_display['spk_date'] = pd.to_datetime(df_display['spk_date'], errors='coerce')
    if 'tower_height' in df_display.columns:
        df_display['tower_height'] = pd.to_numeric(df_display['tower_height'], errors='coerce')
    
    st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=True,
        disabled=True, 
        column_config={
            "spk_number": st.column_config.TextColumn("Nomor SPK"),
            "spk_date": st.column_config.DateColumn("Tanggal SPK", format="DD/MM/YYYY"),
            "tenant_index": st.column_config.TextColumn("Tenant ID"),
            "spk_status": st.column_config.TextColumn("Status"),
            "site_id_tenant": st.column_config.TextColumn("ID Site Tenant"),
            "site_name_tenant": st.column_config.TextColumn("Nama Site"),
            "work_type": st.column_config.TextColumn("Tipe Kerja"),
            "tower_height": st.column_config.NumberColumn("Tinggi (m)", format="%d m"),
            "milestone": st.column_config.TextColumn("Milestone")
        }
    )
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    marketing_dashboard_page()
