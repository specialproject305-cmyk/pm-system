import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase_db import read_all_sheets, insert_row, generate_id, now_str
from fpdf import FPDF
import tempfile

def generate_ai_pdf(site_name, health_score, avg_progress, on_track, total_sites, delayed, forecast_end, delay_reasons, summary):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, 'AI Analytics Report', 0, 1, 'C')
    pdf.set_font('Helvetica', 'I', 10)
    pdf.cell(0, 5, f'Generated: {datetime.now().strftime("%d %b %Y, %H:%M")}', 0, 1, 'C')
    pdf.cell(0, 5, f'Site: {site_name}', 0, 1, 'C')
    pdf.ln(5)
    
    # Health Score
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, '1. Executive Summary', 0, 1)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f'Health Score: {health_score}%', 0, 1)
    pdf.cell(0, 6, f'Progress: {avg_progress}%', 0, 1)
    pdf.cell(0, 6, f'On Track: {on_track}/{total_sites} sites', 0, 1)
    pdf.cell(0, 6, f'Delayed: {delayed} sites', 0, 1)
    pdf.cell(0, 6, f'Forecast Completion: {forecast_end}', 0, 1)
    pdf.ln(3)
    
    # Delay Analysis
    if delay_reasons:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, '2. Delay Reason Analysis', 0, 1)
        pdf.set_font('Helvetica', '', 10)
        for reason, count in delay_reasons.items():
            pdf.cell(0, 6, f'- {reason}: {count} milestone', 0, 1)
        pdf.ln(3)
    
    # Recommendations
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, '3. Recommendations', 0, 1)
    pdf.set_font('Helvetica', '', 10)
    for line in summary.split('\n'):
        if line.strip():
            pdf.cell(0, 6, line.strip(), 0, 1)
    
    return pdf
    
def ai_insights_page():
    st.title("🤖 AI-Powered Analytics Center")
    
    all_data = read_all_sheets()
    sites_df = all_data.get('projects', pd.DataFrame())
    ms_df = all_data.get('milestones', pd.DataFrame())
    mat_df = all_data.get('materials', pd.DataFrame())
    
    if sites_df.empty:
        st.warning("⚠️ Belum ada data site.")
        return
    
    # Konversi numerik
    if not sites_df.empty and 'progress' in sites_df.columns:
        sites_df['progress'] = pd.to_numeric(sites_df['progress'], errors='coerce').fillna(0)
    if not ms_df.empty:
        ms_df['planned_start'] = pd.to_datetime(ms_df['planned_start'], errors='coerce')
        ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
        ms_df['actual_start'] = pd.to_datetime(ms_df['actual_start'], errors='coerce')
        ms_df['actual_end'] = pd.to_datetime(ms_df['actual_end'], errors='coerce')
    
    # ===== FILTER =====
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        site_options = ["ALL SITE"] + sites_df["id"].tolist()
        selected_site = st.selectbox("🎯 Pilih Site:", site_options,
            format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE" 
            else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
    with col_f2:
        delay_reason = st.text_input("🔍 Delay Reason (opsional)", placeholder="Contoh: Material terlambat, Cuaca buruk, Manpower kurang...")
    
    is_all = (selected_site == "ALL SITE")
    
    if not is_all:
        site_data = sites_df[sites_df['id'] == selected_site]
        site_ms = ms_df[ms_df['project_id'] == selected_site] if not ms_df.empty else pd.DataFrame()
        site_name = site_data.iloc[0]['site_name'] if not site_data.empty else "Unknown"
    else:
        site_data = sites_df
        site_ms = ms_df
        site_name = "ALL SITE"
    
    if st.button("🔍 Generate Full Analysis", type="primary"):
        st.divider()
        
        # =============================================
        # 1. PROGRESS ANALYSIS
        # =============================================
        st.header("📈 1. Progress Analysis")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("Planned vs Actual")
            if not site_ms.empty and 'actual_end' in site_ms.columns:
                done_ms = site_ms[site_ms['status'] == 'DONE'].copy()
                if not done_ms.empty:
                    done_ms['planned_duration'] = (done_ms['planned_end'] - done_ms['planned_start']).dt.days
                    done_ms['actual_duration'] = (done_ms['actual_end'] - done_ms['actual_start']).dt.days
                    done_ms['delay_days'] = done_ms['actual_duration'] - done_ms['planned_duration']
                    
                    avg_planned = done_ms['planned_duration'].mean()
                    avg_actual = done_ms['actual_duration'].mean()
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(name='Planned (hari)', x=['Durasi'], y=[avg_planned], marker_color='#0d6efd'))
                    fig.add_trace(go.Bar(name='Actual (hari)', x=['Durasi'], y=[avg_actual], marker_color='#dc3545'))
                    fig.update_layout(height=300, barmode='group')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.metric("Rata-rata Keterlambatan", f"{done_ms['delay_days'].mean():.1f} hari")
        
        with col_b:
            st.subheader("Delay Prediction")
            if not site_ms.empty:
                delayed = len(site_ms[site_ms['status'] == 'DELAYED'])
                total = len(site_ms)
                done = len(site_ms[site_ms['status'] == 'DONE'])
                
                progress = round((done/total)*100, 1) if total > 0 else 0
                predicted_end = datetime.now() + timedelta(days=int((100-progress)*2)) if progress < 100 else datetime.now()
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=progress,
                    title={'text': "Progress %"},
                    gauge={'axis': {'range': [0, 100]},
                           'bar': {'color': "#28a745" if progress>70 else "#ffc107" if progress>40 else "#dc3545"},
                           'steps': [{'range': [0,40], 'color': "#f8d7da"},
                                     {'range': [40,70], 'color': "#fff3cd"},
                                     {'range': [70,100], 'color': "#d4edda"}]}
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
                
                st.info(f"📅 Prediksi selesai: **{predicted_end.strftime('%d %b %Y')}**")
        
        # Delay Reasons
        if delay_reason:
            st.warning(f"🔍 Delay Reason: **{delay_reason}**")
            st.info("💡 Rekomendasi: " + {
                "material": "Prioritaskan pengadaan material. Hubungi supplier alternatif.",
                "cuaca": "Siapkan mitigasi cuaca. Tambah shift saat cuaca baik.",
                "manpower": "Tambah tenaga kerja atau subkontraktor. Evaluasi overtime.",
            }.get(delay_reason.lower().split()[0], "Evaluasi ulang jadwal dan alokasi resource."))
        
        # Critical Path
        st.subheader("🔴 Critical Path")
        if not site_ms.empty:
            critical = site_ms[site_ms['status'].isin(['DELAYED', 'CRITICAL'])]
            if not critical.empty:
                st.error(f"⚠️ {len(critical)} milestone di critical path:")
                for _, c in critical.iterrows():
                    end_date = c['planned_end'].strftime('%d %b') if pd.notna(c.get('planned_end')) else '?'
                    st.markdown(f"- **{c['name']}** (Target: {end_date}) - Status: {c['status']}")
            else:
                st.success("✅ Tidak ada milestone di critical path.")
        
        # Site Ranking
        st.subheader("🏆 Site Ranking")
        if not sites_df.empty:
            ranking = sites_df.sort_values('progress', ascending=False)[['site_id', 'site_name', 'progress', 'status']].head(10)
            
            def color_rank(val):
                if val >= 80: return 'background-color: #d4edda'
                elif val >= 40: return 'background-color: #fff3cd'
                return 'background-color: #f8d7da'
            
            styled = ranking.style.map(color_rank, subset=['progress'])
            st.dataframe(styled, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # =============================================
        # 2. RESOURCE / MANPOWER ANALYSIS
        # =============================================
        st.header("👷 2. Resource Analysis")
        
        col_c, col_d = st.columns(2)
        
        with col_c:
            st.subheader("Team Utilization")
            if not sites_df.empty and 'pm' in sites_df.columns:
                pm_stats = sites_df.groupby('pm').agg(
                    total_sites=('id', 'count'),
                    avg_progress=('progress', 'mean'),
                    delayed=('status', lambda x: (x.isin(['DELAYED','CRITICAL'])).sum())
                ).reset_index()
                
                fig = px.bar(pm_stats, x='pm', y='avg_progress', color='total_sites',
                           title="Progress per PM", labels={'avg_progress':'Avg Progress %'})
                st.plotly_chart(fig, use_container_width=True)
        
        with col_d:
            st.subheader("Productivity Trend")
            if not site_ms.empty:
                site_ms['month'] = site_ms['planned_end'].dt.to_period('M').astype(str)
                monthly_done = site_ms[site_ms['status']=='DONE'].groupby('month').size().reset_index(name='done')
                
                if not monthly_done.empty:
                    fig = px.line(monthly_done, x='month', y='done', markers=True,
                                title="Milestone Selesai per Bulan")
                    st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # =============================================
        # 3. VENDOR ANALYSIS
        # =============================================
        st.header("🏢 3. Vendor Analysis")
        
        if not sites_df.empty and 'vendor' in sites_df.columns:
            vendor_stats = sites_df.groupby('vendor').agg(
                total_sites=('id', 'count'),
                avg_progress=('progress', 'mean'),
                on_track=('status', lambda x: (x=='ON_TRACK').sum()),
                delayed=('status', lambda x: (x.isin(['DELAYED','CRITICAL'])).sum())
            ).reset_index()
            
            vendor_stats['SLA Score'] = round(
                (vendor_stats['on_track'] / vendor_stats['total_sites']) * 100, 1
            )
            
            col_e, col_f = st.columns(2)
            
            with col_e:
                fig = px.bar(vendor_stats, x='vendor', y='SLA Score', color='total_sites',
                           title="Vendor SLA Score", labels={'SLA Score':'SLA Score %'})
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col_f:
                st.dataframe(vendor_stats[['vendor', 'total_sites', 'avg_progress', 'delayed', 'SLA Score']],
                           use_container_width=True, hide_index=True)
        
        st.divider()
        
        # =============================================
        # 4. RISK ANALYSIS
        # =============================================
        st.header("⚠️ 4. Risk Analysis")
        
        col_g, col_h = st.columns(2)
        
        with col_g:
            st.subheader("Risk Heatmap")
            if not sites_df.empty:
                risk_data = sites_df.copy()
                risk_data['risk_level'] = risk_data['progress'].apply(
                    lambda x: 'HIGH' if x < 30 else ('MEDIUM' if x < 60 else 'LOW'))
                
                risk_counts = risk_data['risk_level'].value_counts()
                
                fig = px.pie(values=risk_counts.values, names=risk_counts.index,
                           color=risk_counts.index,
                           color_discrete_map={'HIGH':'#dc3545','MEDIUM':'#ffc107','LOW':'#28a745'})
                st.plotly_chart(fig, use_container_width=True)
        
        with col_h:
            st.subheader("Probability-Impact Matrix")
            if not sites_df.empty:
                high_impact = len(sites_df[sites_df['status'].isin(['CRITICAL','DELAYED'])])
                medium_impact = len(sites_df[sites_df['status']=='DELAYED'])
                low_impact = len(sites_df[sites_df['status']=='ON_TRACK'])
                
                matrix_data = pd.DataFrame({
                    'Category': ['High Impact', 'Medium Impact', 'Low Impact'],
                    'Count': [high_impact, medium_impact, low_impact]
                })
                
                fig = px.treemap(matrix_data, path=['Category'], values='Count',
                               color='Category',
                               color_discrete_map={'High Impact':'#dc3545','Medium Impact':'#ffc107','Low Impact':'#28a745'})
                st.plotly_chart(fig, use_container_width=True)
        
        st.divider()

                # =============================================
        # DELAY REASON ANALYSIS
        # =============================================
        st.header("🔍 6. Delay Reason Analysis")
        
        if not site_ms.empty and 'delay_reason' in site_ms.columns:
            delays = site_ms[site_ms['delay_reason'].notna() & (site_ms['delay_reason'] != '') & (site_ms['delay_reason'] != 'Tidak Ada')]
            
            if not delays.empty:
                reason_counts = delays['delay_reason'].value_counts().reset_index()
                reason_counts.columns = ['Reason', 'Count']
                
                col_i, col_j = st.columns(2)
                
                with col_i:
                    fig = px.pie(reason_counts, values='Count', names='Reason',
                               title="Distribusi Delay Reason",
                               color_discrete_sequence=px.colors.qualitative.Set2)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col_j:
                    # Top reason
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
                delay_detail = delays[['name', 'delay_reason', 'planned_end', 'status']].copy()
                delay_detail['planned_end'] = delay_detail['planned_end'].dt.strftime('%d %b %Y')
                st.dataframe(delay_detail, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Tidak ada delay reason tercatat.")
        
        # =============================================
        # 5. EXECUTIVE SUMMARY
        # =============================================
        st.header("📋 5. Executive Summary")
        
        total_sites = len(sites_df)
        avg_progress = sites_df['progress'].mean() if not sites_df.empty else 0
        on_track = len(sites_df[sites_df['status']=='ON_TRACK']) if not sites_df.empty else 0
        delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])]) if not sites_df.empty else 0
        
        # Health Score
        health_score = round((on_track / total_sites * 100) if total_sites > 0 else 0)
        health_color = '🟢' if health_score >= 80 else ('🟡' if health_score >= 50 else '🔴')
        
        col_i, col_j, col_k = st.columns(3)
        
        with col_i:
            st.markdown(f"""
            <div style="text-align:center; padding:10px; border-radius:10px; background:#f8f9fa;">
            <div style="font-size:14px; color:gray;">{health_color} Health Score</div>
                    <div style="font-size:24px; font-weight:bold;">{health_score}%</div>
                </div>
                """, unsafe_allow_html=True)
            if health_score >= 80: st.success("Excellent")
            elif health_score >= 50: st.warning("Need Attention")
            else: st.error("Critical")
            
        with col_j:
            st.markdown(f"""
                <div style="text-align:center; padding:10px; border-radius:10px; background:#f8f9fa;">
                    <div style="font-size:14px; color:gray;">📅 Forecast</div>
                    <div style="font-size:18px; font-weight:bold;">{forecast_end.strftime('%d %b %Y')}</div>
                </div>
                """, unsafe_allow_html=True)  
            
        with col_k:
            st.markdown(f"""
                <div style="text-align:center; padding:10px; border-radius:10px; background:#f8f9fa;">
                    <div style="font-size:14px; color:gray;">🎯 KPI</div>
                    <div style="font-size:18px; font-weight:bold;">{on_track}/{total_sites} On Track</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Auto-generated summary
        summary = f"""
        **Executive Summary - {datetime.now().strftime('%d %B %Y')}**
        
        📊 **{total_sites}** site dalam monitoring.
        📈 Progress rata-rata: **{avg_progress:.1f}%**
        🟢 **{on_track}** site On Track | 🔴 **{delayed}** site perlu perhatian.
        📅 Prediksi selesai: **{forecast_end.strftime('%d %b %Y')}**
        
        **Top Actions:**
        """
        
        if delayed > 0:
            summary += f"\n⚠️ Prioritaskan {delayed} site yang terlambat."
        if avg_progress < 50:
            summary += "\n🚀 Percepat eksekusi milestone untuk meningkatkan progress."
        if delay_reason:
            summary += f"\n🔍 Delay utama: **{delay_reason}**"
        
               # ===== EXPORT PDF =====
        st.divider()
        st.subheader("📥 Export Report")
        
        if st.button("📄 Generate PDF Report", key="gen_pdf", type="secondary"):
            with st.spinner("Generating PDF..."):
                try:
                    from fpdf import FPDF
                    
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font('Helvetica', 'B', 16)
                    pdf.cell(0, 10, 'AI Analytics Report', 0, 1, 'C')
                    pdf.set_font('Helvetica', '', 10)
                    pdf.cell(0, 6, f'Site: {site_name}', 0, 1)
                    pdf.cell(0, 6, f'Health Score: {health_score}%', 0, 1)
                    pdf.cell(0, 6, f'Progress: {avg_progress:.1f}%', 0, 1)
                    pdf.cell(0, 6, f'On Track: {on_track}/{total_sites}', 0, 1)
                    pdf.ln(5)
                    pdf.set_font('Helvetica', 'B', 12)
                    pdf.cell(0, 8, 'Recommendations:', 0, 1)
                    pdf.set_font('Helvetica', '', 10)
                    for line in summary.split('\n')[:10]:
                        clean = line.replace('**','').replace('*','').strip()
                        if clean:
                            pdf.multi_cell(0, 6, clean)
                    
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                        pdf.output(tmp.name)
                        with open(tmp.name, 'rb') as f:
                            st.download_button(
                                "📥 Download PDF",
                                f.read(),
                                f"AI_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                "application/pdf"
                            )
                    st.success("✅ Klik tombol download di atas!")
                except Exception as e:
                    st.error(f"❌ {e}")

if __name__ == "__main__":
    ai_insights_page()
