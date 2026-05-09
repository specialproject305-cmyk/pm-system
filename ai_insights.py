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
    
    if sites_df.empty:
        st.warning("⚠️ Belum ada data site.")
        return
    
    # Konversi numerik dan tanggal
    if 'progress' in sites_df.columns:
        sites_df['progress'] = pd.to_numeric(sites_df['progress'], errors='coerce').fillna(0)
    
    if not ms_df.empty:
        date_cols = ['planned_start', 'planned_end', 'actual_start', 'actual_end']
        for col in date_cols:
            if col not in ms_df.columns:
                ms_df[col] = None
            ms_df[col] = pd.to_datetime(ms_df[col], errors='coerce')
    
    # ===== FILTER =====
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        site_options = ["ALL SITE"] + sites_df["id"].tolist()
        selected_site = st.selectbox("🎯 Pilih Site:", site_options,
            format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE" 
            else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
    with col_f2:
        delay_reason_input = st.text_input("🔍 Delay Reason (opsional)", placeholder="Contoh: Material terlambat...")
    
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
        
        # 1. PROGRESS ANALYSIS
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
                total = len(site_ms)
                done = len(site_ms[site_ms['status'] == 'DONE'])
                progress_val = round((done/total)*100, 1) if total > 0 else 0
                predicted_end = datetime.now() + timedelta(days=int((100-progress_val)*2)) if progress_val < 100 else datetime.now()
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=progress_val,
                    title={'text': "Progress %"},
                    gauge={'axis': {'range': [0, 100]},
                           'bar': {'color': "#28a745" if progress_val>70 else "#ffc107" if progress_val>40 else "#dc3545"},
                           'steps': [{'range': [0,40], 'color': "#f8d7da"},
                                     {'range': [40,70], 'color': "#fff3cd"},
                                     {'range': [70,100], 'color': "#d4edda"}]}
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
                st.info(f"📅 Prediksi selesai: **{predicted_end.strftime('%d %b %Y')}**")

        # 2. RESOURCE ANALYSIS
        st.header("👷 2. Resource Analysis")
        col_c, col_d = st.columns(2)
        with col_c:
            st.subheader("Team Utilization")
            if not sites_df.empty and 'pm' in sites_df.columns:
                pm_stats = sites_df.groupby('pm').agg(
                    total_sites=('id', 'count'),
                    avg_progress=('progress', 'mean')
                ).reset_index()
                fig = px.bar(pm_stats, x='pm', y='avg_progress', color='total_sites', title="Progress per PM")
                st.plotly_chart(fig, use_container_width=True)
        
        with col_d:
            st.subheader("Productivity Trend")
            if not site_ms.empty:
                temp_ms = site_ms.dropna(subset=['planned_end']).copy()
                temp_ms['month'] = temp_ms['planned_end'].dt.to_period('M').astype(str)
                monthly_done = temp_ms[temp_ms['status']=='DONE'].groupby('month').size().reset_index(name='done')
                if not monthly_done.empty:
                    fig = px.line(monthly_done, x='month', y='done', markers=True, title="Milestone Selesai per Bulan")
                    st.plotly_chart(fig, use_container_width=True)

        # 3. VENDOR ANALYSIS
        st.header("🏢 3. Vendor Analysis")
        if not sites_df.empty and 'vendor' in sites_df.columns:
            vendor_stats = sites_df.groupby('vendor').agg(
                total_sites=('id', 'count'),
                avg_progress=('progress', 'mean'),
                on_track=('status', lambda x: (x == 'ON_TRACK').sum())
            ).reset_index()
            vendor_stats['SLA Score'] = round((vendor_stats['on_track'] / vendor_stats['total_sites']) * 100, 1)
            
            col_e, col_f = st.columns(2)
            with col_e:
                fig = px.bar(vendor_stats, x='vendor', y='SLA Score', color='total_sites', title="Vendor SLA Score")
                st.plotly_chart(fig, use_container_width=True)
            with col_f:
                st.dataframe(vendor_stats, use_container_width=True, hide_index=True)

        # 4. RISK ANALYSIS
        st.header("⚠️ 4. Risk Analysis")
        col_g, col_h = st.columns(2)
        with col_g:
            risk_data = sites_df.copy()
            risk_data['risk_level'] = risk_data['progress'].apply(lambda x: 'HIGH' if x < 30 else ('MEDIUM' if x < 60 else 'LOW'))
            risk_counts = risk_data['risk_level'].value_counts()
            fig = px.pie(values=risk_counts.values, names=risk_counts.index, title="Risk Heatmap",
                         color=risk_counts.index, color_discrete_map={'HIGH':'#dc3545','MEDIUM':'#ffc107','LOW':'#28a745'})
            st.plotly_chart(fig, use_container_width=True)
        with col_h:
            high_impact = len(sites_df[sites_df['status'].isin(['CRITICAL','DELAYED'])])
            matrix_data = pd.DataFrame({'Category': ['High Impact', 'Others'], 'Count': [high_impact, len(sites_df)-high_impact]})
            fig = px.treemap(matrix_data, path=['Category'], values='Count', color='Category',
                             color_discrete_map={'High Impact':'#dc3545','Others':'#28a745'})
            st.plotly_chart(fig, use_container_width=True)

        # 6. DELAY REASON ANALYSIS
        st.header("🔍 6. Delay Reason Analysis")
        if not site_ms.empty and 'delay_reason' in site_ms.columns:
            delays = site_ms[site_ms['delay_reason'].notna() & (site_ms['delay_reason'] != '')]
            if not delays.empty:
                reason_counts = delays['delay_reason'].value_counts().reset_index()
                reason_counts.columns = ['Reason', 'Count']
                col_i, col_j = st.columns(2)
                with col_i:
                    fig = px.pie(reason_counts, values='Count', names='Reason', title="Distribusi Delay Reason")
                    st.plotly_chart(fig, use_container_width=True)
                with col_j:
                    top_r = reason_counts.iloc[0]['Reason']
                    st.error(f"🔴 Top Delay: {top_r}")

        # 5. EXECUTIVE SUMMARY
        st.header("📋 5. Executive Summary")
        total_sites = len(sites_df)
        avg_progress = sites_df['progress'].mean()
        on_track = len(sites_df[sites_df['status']=='ON_TRACK'])
        delayed_count = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])])
        health_score = round((on_track / total_sites * 100) if total_sites > 0 else 0)
        
        forecast_end = datetime.now() + timedelta(days=int((100-avg_progress)*2))
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Health Score", f"{health_score}%")
        c2.metric("Forecast End", forecast_end.strftime('%d %b %Y'))
        c3.metric("KPI Status", f"{on_track}/{total_sites} On Track")

        summary_text = f"Total sites: {total_sites}. Avg Progress: {avg_progress:.1f}%. Health: {health_score}%."
        
        # EXPORT PDF
        st.divider()
        if st.button("📄 Generate PDF Report"):
            with st.spinner("Generating..."):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(40, 10, f"Report: {site_name}")
                pdf.ln(10)
                pdf.set_font("Arial", '', 12)
                pdf.cell(40, 10, summary_text)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    pdf.output(tmp.name)
                    with open(tmp.name, "rb") as f:
                        st.download_button("Download PDF", f, file_name="Report.pdf")

if __name__ == "__main__":
    ai_insights_page()
