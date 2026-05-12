"""
ai_insights.py - AI-Powered Analytics Center
Versi Stabil (PDF Export Dihapus Sementara)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase_db import read_all_sheets

# ─────────────────────────────────────────────────────────────
# 📊 HELPER FUNCTIONS FOR PIC & SLA ANALYSIS
# ─────────────────────────────────────────────────────────────

def analyze_pic_performance(ms_df):
    if ms_df.empty or 'assigned_to' not in ms_df.columns: 
        return pd.DataFrame()
    
    assigned = ms_df[ms_df['assigned_to'].notna() & (ms_df['assigned_to'] != '')].copy()
    if assigned.empty: 
        return pd.DataFrame()
    
    # Konversi kolom tanggal
    for col in ['planned_start', 'planned_end', 'actual_start', 'actual_end']:
        if col in assigned.columns: 
            assigned[col] = pd.to_datetime(assigned[col], errors='coerce')
            
    # ✅ FIX: Paksa konversi weight ke numerik agar .mean() tidak error
    if 'weight' in assigned.columns:
        assigned['weight'] = pd.to_numeric(assigned['weight'], errors='coerce').fillna(0)
        
    pic_stats = assigned.groupby('assigned_to').agg(
        total_tasks=('id', 'count'), 
        done_tasks=('status', lambda x: (x == 'DONE').sum()),
        delayed_tasks=('status', lambda x: (x.isin(['DELAYED', 'CRITICAL'])).sum()), 
        avg_weight=('weight', 'mean')
    ).reset_index()
    
    pic_stats['sla_score'] = round((pic_stats['done_tasks'] / pic_stats['total_tasks']) * 100, 1).fillna(0)
    
    def calc_avg_delay(group):
        done_with_actual = group[(group['status'] == 'DONE') & (group['actual_end'].notna()) & (group['planned_end'].notna())]
        if done_with_actual.empty: return 0
        delays = (done_with_actual['actual_end'] - done_with_actual['planned_end']).dt.days
        return round(delays.mean(), 1)
        
    pic_stats['avg_delay'] = assigned.groupby('assigned_to').apply(calc_avg_delay).values
    pic_stats['avg_delay'] = pic_stats['avg_delay'].fillna(0)
    return pic_stats

def analyze_sla_compliance(ms_df):
    """Analisis kepatuhan terhadap SLA berdasarkan sla_days vs actual duration."""
    if ms_df.empty or 'sla_days' not in ms_df.columns:
        return None
    
    # Filter yang punya sla_days dan actual_end
    with_sla = ms_df[
        (ms_df['sla_days'].notna()) & 
        (ms_df['sla_days'] != '') &
        (ms_df['actual_end'].notna()) &
        (ms_df['planned_start'].notna())
    ].copy()
    
    if with_sla.empty:
        return None
    
    # Konversi tanggal
    with_sla['planned_start'] = pd.to_datetime(with_sla['planned_start'], errors='coerce')
    with_sla['actual_end'] = pd.to_datetime(with_sla['actual_end'], errors='coerce')
    
    # Hitung actual duration dalam hari
    with_sla['actual_duration'] = (with_sla['actual_end'] - with_sla['planned_start']).dt.days
    with_sla['sla_days_num'] = pd.to_numeric(with_sla['sla_days'], errors='coerce')
    
    # Bandingkan actual vs SLA
    with_sla['is_on_sla'] = with_sla['actual_duration'] <= with_sla['sla_days_num']
    with_sla['delay_days'] = with_sla['actual_duration'] - with_sla['sla_days_num']
    
    # Summary stats
    total = len(with_sla)
    on_sla = len(with_sla[with_sla['is_on_sla']])
    breach = total - on_sla
    
    return {
        'total': total,
        'on_sla': on_sla,
        'breach': breach,
        'on_sla_pct': round((on_sla / total) * 100, 1) if total > 0 else 0,
        'breach_pct': round((breach / total) * 100, 1) if total > 0 else 0,
        'avg_delay': round(with_sla['delay_days'].mean(), 1) if not with_sla.empty else 0,
        'max_delay': int(with_sla['delay_days'].max()) if not with_sla.empty else 0
    }


# ─────────────────────────────────────────────────────────────
# 🎯 MAIN PAGE FUNCTION
# ─────────────────────────────────────────────────────────────
if 'master_project_filter' not in st.session_state:
    st.session_state.master_project_filter = "ALL"

def ai_insights_page():
    st.title("🤖 AI-Powered Analytics Center")
    
    # Load data dengan error handling
    try:
        all_data = read_all_sheets()
    except Exception as e:
        st.error(f"⚠️ Gagal load  {str(e)[:100]}")
        return
    
    sites_df = all_data.get('projects', pd.DataFrame())
    ms_df = all_data.get('milestones', pd.DataFrame())
    mat_df = all_data.get('materials', pd.DataFrame())
    
    if sites_df.empty:
        st.warning("⚠️ Belum ada data site.")
        return
    
    # Safe numeric/date conversion
    if not sites_df.empty and 'progress' in sites_df.columns:
        sites_df['progress'] = pd.to_numeric(sites_df['progress'], errors='coerce').fillna(0)
    
    if not ms_df.empty:
        for col in ['planned_start', 'planned_end', 'actual_start', 'actual_end']:
            if col in ms_df.columns:
                ms_df[col] = pd.to_datetime(ms_df[col], errors='coerce')

    if st.session_state.master_project_filter != "ALL" and not sites_df.empty:
        valid_sites = sites_df[sites_df['master_project_id'] == st.session_state.master_project_filter]['id'].tolist()
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)]
    
    # ===== FILTER =====
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        site_options = ["ALL SITE"] + sites_df["id"].tolist()
        selected_site = st.selectbox(
            "🎯 Pilih Site:", 
            site_options,
            format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE" 
            else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}"
        )
    with col_f2:
        delay_reason_filter = st.text_input(
            "🔍 Filter Delay Reason (opsional)", 
            placeholder="Contoh: Material terlambat, Cuaca buruk..."
        )
    
    is_all = (selected_site == "ALL SITE")
    
    # Filter data berdasarkan site
    if not is_all:
        site_data = sites_df[sites_df['id'] == selected_site]
        site_ms = ms_df[ms_df['project_id'] == selected_site] if not ms_df.empty else pd.DataFrame()
        site_name = site_data.iloc[0]['site_name'] if not site_data.empty else "Unknown"
    else:
        site_data = sites_df
        site_ms = ms_df
        site_name = "ALL SITE"
    
    # Tombol Generate Analysis
    if st.button("🔍 Generate Full Analysis", type="primary"):
        st.divider()
        
        # =============================================
        # 1. PROGRESS ANALYSIS
        # =============================================
        st.header("📈 1. Progress Analysis")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("Planned vs Actual Duration")
            if not site_ms.empty and 'actual_end' in site_ms.columns and 'planned_end' in site_ms.columns:
                done_ms = site_ms[site_ms['status'] == 'DONE'].copy()
                if not done_ms.empty and done_ms['actual_start'].notna().any():
                    done_ms = done_ms.dropna(subset=['actual_start', 'actual_end', 'planned_start', 'planned_end'])
                    
                    if not done_ms.empty:
                        done_ms['planned_duration'] = (done_ms['planned_end'] - done_ms['planned_start']).dt.days
                        done_ms['actual_duration'] = (done_ms['actual_end'] - done_ms['actual_start']).dt.days
                        done_ms['delay_days'] = done_ms['actual_duration'] - done_ms['planned_duration']
                        
                        avg_planned = done_ms['planned_duration'].mean()
                        avg_actual = done_ms['actual_duration'].mean()
                        
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            name='Planned (hari)', 
                            x=['Durasi'], 
                            y=[avg_planned], 
                            marker_color='#0d6efd'
                        ))
                        fig.add_trace(go.Bar(
                            name='Actual (hari)', 
                            x=['Durasi'], 
                            y=[avg_actual], 
                            marker_color='#dc3545'
                        ))
                        fig.update_layout(
                            height=300, 
                            barmode='group',
                            title='Rata-rata Durasi Task',
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        avg_delay = done_ms['delay_days'].mean()
                        st.metric(
                            "Rata-rata Keterlambatan", 
                            f"{avg_delay:+.1f} hari",
                            delta=None if avg_delay <= 0 else f"{avg_delay:.1f} hari terlambat"
                        )
        
        with col_b:
            st.subheader("Progress & Prediction")
            if not site_ms.empty:
                total = len(site_ms)
                done = len(site_ms[site_ms['status'] == 'DONE'])
                progress = round((done/total)*100, 1) if total > 0 else 0
                
                # Prediksi selesai berdasarkan velocity
                if progress < 100 and progress > 0:
                    remaining = 100 - progress
                    predicted_days = int(remaining / 2) # Asumsi 2% per hari
                    predicted_end = datetime.now() + timedelta(days=predicted_days)
                else:
                    predicted_end = datetime.now()
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=progress,
                    title={'text': "Progress %"},
                    delta={'reference': 80, 'increasing': {'color': "#28a745"}},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#28a745" if progress>70 else "#ffc107" if progress>40 else "#dc3545"},
                        'steps': [
                            {'range': [0,40], 'color': "#f8d7da"},
                            {'range': [40,70], 'color': "#fff3cd"},
                            {'range': [70,100], 'color': "#d4edda"}
                        ],
                        'threshold': {
                            'line': {'color': "#dc3545", 'width': 4},
                            'thickness': 0.75,
                            'value': 80
                        }
                    }
                ))
                fig.update_layout(height=300, margin=dict(t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"📅 Prediksi selesai: **{predicted_end.strftime('%d %b %Y')}**")
        
        # Delay Reason Filter
        if delay_reason_filter:
            st.warning(f"🔍 Filter: Delay Reason mengandung **'{delay_reason_filter}'**")
            if not site_ms.empty and 'delay_reason' in site_ms.columns:
                filtered_delays = site_ms[
                    site_ms['delay_reason'].str.contains(delay_reason_filter, case=False, na=False)
                ]
                if not filtered_delays.empty:
                    st.metric("Milestone Terdampak", len(filtered_delays))
        
        # Critical Path
        st.subheader("🔴 Critical Path")
        if not site_ms.empty and 'status' in site_ms.columns:
            critical = site_ms[site_ms['status'].isin(['DELAYED', 'CRITICAL'])]
            if not critical.empty:
                st.error(f"⚠️ {len(critical)} milestone di critical path:")
                for _, c in critical.head(5).iterrows():
                    end_date = c['planned_end'].strftime('%d %b') if pd.notna(c.get('planned_end')) else '?'
                    assigned = c.get('assigned_to', 'N/A')
                    st.markdown(f"- **{c['name']}** | PIC: `{assigned}` | Target: {end_date} | Status: `{c['status']}`")
            else:
                st.success("✅ Tidak ada milestone di critical path.")
        
        # Site Ranking
        st.subheader("🏆 Site Ranking by Progress")
        if not sites_df.empty and 'progress' in sites_df.columns:
            ranking = sites_df.sort_values('progress', ascending=False)[['site_id', 'site_name', 'progress', 'status']].head(10)
            
            def color_rank(val):
                if val >= 80: return 'background-color: #d4edda; color: #155724'
                elif val >= 40: return 'background-color: #fff3cd; color: #856404'
                return 'background-color: #f8d7da; color: #721c24'
            
            styled = ranking.style.map(color_rank, subset=['progress'])
            st.dataframe(styled, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # =============================================
        # 2. PIC ASSIGNMENT PERFORMANCE
        # =============================================
        st.header("👤 2. PIC Assignment Performance")
        st.markdown("*Analisis performa berdasarkan Person In Charge (Assigned To)*")
        
        if not site_ms.empty and 'assigned_to' in site_ms.columns:
            pic_stats = analyze_pic_performance(site_ms)
            
            if not pic_stats.empty:
                col_c, col_d = st.columns(2)
                
                with col_c:
                    st.subheader("SLA Score per PIC")
                    fig = px.bar(
                        pic_stats.sort_values('sla_score', ascending=True),
                        x='sla_score',
                        y='assigned_to',
                        orientation='h',
                        color='sla_score',
                        color_continuous_scale=['#dc3545', '#ffc107', '#28a745'],
                        labels={'sla_score': 'SLA Score (%)', 'assigned_to': 'PIC / Team'},
                        title='Persentase Task On-Time'
                    )
                    fig.update_layout(height=max(300, len(pic_stats)*35), margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(fig, use_container_width=True)
                
                with col_d:
                    st.subheader("Detail Performance")
                    display_df = pic_stats[['assigned_to', 'total_tasks', 'done_tasks', 'sla_score', 'avg_delay']].copy()
                    display_df.columns = ['PIC', 'Total Tasks', 'Done', 'SLA Score %', 'Avg Delay (hari)']
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Insight
                best_pic = pic_stats.loc[pic_stats['sla_score'].idxmax()]
                worst_pic = pic_stats.loc[pic_stats['sla_score'].idxmin()]
                
                col_e, col_f = st.columns(2)
                with col_e:
                    st.success(f"🏆 **Best Performer:** `{best_pic['assigned_to']}` dengan SLA Score **{best_pic['sla_score']}%**")
                with col_f:
                    if worst_pic['sla_score'] < 70:
                        st.warning(f"⚠️ **Perlu Perhatian:** `{worst_pic['assigned_to']}` dengan SLA Score **{worst_pic['sla_score']}%**")
            else:
                st.info("ℹ️ Belum ada data assigned_to yang terisi untuk dianalisis.")
        else:
            st.info("ℹ️ Kolom 'assigned_to' tidak tersedia. Pastikan milestone memiliki PIC yang terisi.")
        
        st.divider()
        
        # =============================================
        # 3. SLA COMPLIANCE ANALYSIS
        # =============================================
        st.header("⏱️ 3. SLA Compliance Analysis")
        st.markdown("*Perbandingan SLA (target) vs Actual Duration*")
        
        if not site_ms.empty and 'sla_days' in site_ms.columns:
            sla_stats = analyze_sla_compliance(site_ms)
            
            if sla_stats:
                # KPI Cards
                col_g, col_h, col_i, col_j = st.columns(4)
                with col_g:
                    st.metric("Total Tasks", sla_stats['total'])
                with col_h:
                    st.metric("✅ On SLA", f"{sla_stats['on_sla']} ({sla_stats['on_sla_pct']}%)")
                with col_i:
                    st.metric("❌ Breach SLA", f"{sla_stats['breach']} ({sla_stats['breach_pct']}%)")
                with col_j:
                    st.metric("Avg Delay", f"{sla_stats['avg_delay']:+.1f} hari")
                
                # Chart: On SLA vs Breach
                fig_pie = px.pie(
                    values=[sla_stats['on_sla'], sla_stats['breach']],
                    names=['On SLA', 'Breach SLA'],
                    color=['On SLA', 'Breach SLA'],
                    color_discrete_map={'On SLA': '#28a745', 'Breach SLA': '#dc3545'},
                    title='Distribusi SLA Compliance'
                )
                fig_pie.update_layout(height=350, margin=dict(t=30, b=10))
                st.plotly_chart(fig_pie, use_container_width=True)
                
                # Top Breach Tasks
                if sla_stats['breach'] > 0:
                    st.subheader("🔴 Top Tasks yang Breach SLA")
                    with_sla = site_ms[
                        (site_ms['sla_days'].notna()) & 
                        (site_ms['actual_end'].notna()) &
                        (site_ms['planned_start'].notna())
                    ].copy()
                    
                    if not with_sla.empty:
                        with_sla['actual_duration'] = (with_sla['actual_end'] - with_sla['planned_start']).dt.days
                        with_sla['sla_days_num'] = pd.to_numeric(with_sla['sla_days'], errors='coerce')
                        with_sla['delay_days'] = with_sla['actual_duration'] - with_sla['sla_days_num']
                        
                        breach_tasks = with_sla[with_sla['delay_days'] > 0].sort_values('delay_days', ascending=False).head(5)
                        
                        for _, task in breach_tasks.iterrows():
                            st.markdown(f"""
                            <div style='background: #f8d7da; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 4px solid #dc3545;'>
                                <strong>{task['name']}</strong><br>
                                SLA: {task['sla_days']} hari | Actual: {task['actual_duration']} hari | 
                                <span style='color: #dc3545; font-weight: bold;'>+{task['delay_days']} hari terlambat</span><br>
                                PIC: `{task.get('assigned_to', 'N/A')}`
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("ℹ️ Belum cukup data dengan SLA + Actual End untuk dianalisis.")
        else:
            st.info("ℹ️ Kolom 'sla_days' tidak tersedia. Pastikan milestone memiliki nilai SLA yang terisi.")
        
        st.divider()
        
        # =============================================
        # 4. DELAY REASON ANALYSIS
        # =============================================
        st.header("🔍 4. Delay Reason Analysis")
        
        if not site_ms.empty and 'delay_reason' in site_ms.columns:
            delays = site_ms[
                site_ms['delay_reason'].notna() & 
                (site_ms['delay_reason'] != '') & 
                (site_ms['delay_reason'] != 'Tidak Ada')
            ]
            
            if not delays.empty:
                reason_counts = delays['delay_reason'].value_counts().reset_index()
                reason_counts.columns = ['Reason', 'Count']
                
                col_k, col_l = st.columns(2)
                
                with col_k:
                    fig = px.pie(
                        reason_counts, 
                        values='Count', 
                        names='Reason',
                        title="Distribusi Delay Reason",
                        color_discrete_sequence=px.colors.qualitative.Set2,
                        hole=0.4
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col_l:
                    top_reason = reason_counts.iloc[0]
                    st.error(f"🔴 **#{1} Delay Reason: {top_reason['Reason']}** ({top_reason['Count']} milestone)")
                    
                    # Rekomendasi per reason
                    recos = {
                        "Material Terlambat": "📦 Prioritaskan procurement. Cari supplier alternatif. Buffer stok 2 minggu.",
                        "Cuaca Buruk": "🌧️ Mitigasi cuaca. Siapkan jadwal alternatif. Tambah shift saat cerah.",
                        "Manpower Kurang": "👷 Tambah subkontraktor. Evaluasi overtime. Training multi-skill.",
                        "Vendor Terlambat": "🏢 SLA penalty. Cari vendor backup. Monitoring mingguan.",
                        "Izin/Tanah": "📋 Eskalasi ke manajemen. Paralel proses dengan negosiasi.",
                        "Desain Berubah": "📐 Freeze design. Tambah buffer contingency 10%.",
                    }
                    
                    if top_reason['Reason'] in recos:
                        st.info(recos[top_reason['Reason']])
                
                # Tabel detail
                st.subheader("Detail Delay per Milestone")
                delay_detail = delays[['name', 'delay_reason', 'planned_end', 'status', 'assigned_to']].copy()
                delay_detail['planned_end'] = delay_detail['planned_end'].dt.strftime('%d %b %Y')
                st.dataframe(delay_detail, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Tidak ada delay reason tercatat.")
        else:
            st.info("ℹ️ Kolom 'delay_reason' tidak tersedia.")
        
        st.divider()
        
        # =============================================
        # 5. RESOURCE & VENDOR ANALYSIS
        # =============================================
        st.header("🏢 5. Resource & Vendor Analysis")
        
        col_m, col_n = st.columns(2)
        
        with col_m:
            st.subheader("Team Utilization")
            if not sites_df.empty and 'pm' in sites_df.columns:
                pm_stats = sites_df.groupby('pm').agg(
                    total_sites=('id', 'count'),
                    avg_progress=('progress', 'mean'),
                    delayed=('status', lambda x: (x.isin(['DELAYED','CRITICAL'])).sum())
                ).reset_index()
                
                fig = px.bar(
                    pm_stats, 
                    x='pm', 
                    y='avg_progress', 
                    color='total_sites',
                    title="Progress per PM",
                    labels={'avg_progress':'Avg Progress %', 'pm': 'Project Manager'},
                    color_continuous_scale='Blues'
                )
                fig.update_layout(height=300, margin=dict(t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)
        
        with col_n:
            st.subheader("Vendor SLA Score")
            if not sites_df.empty and 'vendor' in sites_df.columns and 'status' in sites_df.columns:
                vendor_stats = sites_df.groupby('vendor').agg(
                    total_sites=('id', 'count'),
                    avg_progress=('progress', 'mean'),
                    on_track=('status', lambda x: (x=='ON_TRACK').sum()),
                    delayed=('status', lambda x: (x.isin(['DELAYED','CRITICAL'])).sum())
                ).reset_index()
                
                vendor_stats['SLA Score'] = round(
                    (vendor_stats['on_track'] / vendor_stats['total_sites']) * 100, 1
                ).fillna(0)
                
                fig = px.bar(
                    vendor_stats.sort_values('SLA Score', ascending=True),
                    x='SLA Score',
                    y='vendor',
                    orientation='h',
                    color='SLA Score',
                    color_continuous_scale=['#dc3545', '#ffc107', '#28a745'],
                    title="Vendor Performance"
                )
                fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # =============================================
        # 6. RISK & EXECUTIVE SUMMARY
        # =============================================
        st.header("⚠️ 6. Risk Analysis & Executive Summary")
        
        col_o, col_p = st.columns(2)
        
        with col_o:
            st.subheader("Risk Heatmap")
            if not sites_df.empty and 'progress' in sites_df.columns:
                risk_data = sites_df.copy()
                risk_data['risk_level'] = risk_data['progress'].apply(
                    lambda x: 'HIGH' if x < 30 else ('MEDIUM' if x < 60 else 'LOW')
                )
                
                risk_counts = risk_data['risk_level'].value_counts()
                
                fig = px.pie(
                    values=risk_counts.values, 
                    names=risk_counts.index,
                    color=risk_counts.index,
                    color_discrete_map={'HIGH':'#dc3545','MEDIUM':'#ffc107','LOW':'#28a745'},
                    title='Distribusi Risk Level'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col_p:
            st.subheader("Executive Summary")
            
            total_sites = len(sites_df)
            avg_progress = sites_df['progress'].mean() if not sites_df.empty else 0
            on_track = len(sites_df[sites_df['status']=='ON_TRACK']) if not sites_df.empty else 0
            delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])]) if not sites_df.empty else 0
            
            # Health Score
            health_score = round((on_track / total_sites * 100) if total_sites > 0 else 0)
            health_color = '🟢' if health_score >= 80 else ('🟡' if health_score >= 50 else '🔴')
            
            st.metric(f"{health_color} Health Score", f"{health_score}%")
            
            if health_score >= 80: 
                st.success("✅ Excellent - Pertahankan performa!")
            elif health_score >= 50: 
                st.warning("⚠️ Need Attention - Fokus pada site terlambat")
            else: 
                st.error("🔴 Critical - Perlu intervensi segera")
            
            # Forecast
            forecast_end_str = "Completed"
            if avg_progress < 100:
                forecast_days = int((100 - avg_progress) * 3)
                forecast_end = datetime.now() + timedelta(days=forecast_days)
                forecast_end_str = forecast_end.strftime('%d %b %Y')
                st.metric("📅 Forecast Completion", forecast_end_str)
            
            # Auto-generated summary
            summary_text = f"""
            **Executive Summary - {datetime.now().strftime('%d %B %Y')}**
            
            📊 **{total_sites}** site dalam monitoring.
            📈 Progress rata-rata: **{avg_progress:.1f}%**
            🟢 **{on_track}** site On Track | 🔴 **{delayed}** site perlu perhatian.
            📅 Prediksi selesai: **{forecast_end_str}**
            
            **Top Actions:**
            """
            
            if delayed > 0:
                summary_text += f"\n⚠️ Prioritaskan {delayed} site yang terlambat."
            if avg_progress < 50:
                summary_text += "\n🚀 Percepat eksekusi milestone untuk meningkatkan progress."
            if delay_reason_filter:
                summary_text += f"\n🔍 Fokus pada delay: **{delay_reason_filter}**"
            
            st.markdown(summary_text)
        
        st.divider()
        
        # =============================================
        # INFO EXPORT (PDF Disabled)
        # =============================================
        st.info("🚧 Fitur Export PDF sedang dalam pengembangan untuk meningkatkan stabilitas sistem. Silakan gunakan screenshot browser atau copy-paste data untuk laporan sementara.")

if __name__ == "__main__":
    ai_insights_page()
