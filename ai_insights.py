import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase_db import read_all_sheets, insert_row, generate_id, now_str
from fpdf import FPDF
import tempfile

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
        delay_reason = st.text_input("🔍 Delay Reason (opsional)", placeholder="Contoh: Material terlambat...")
    
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
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(name='Planned (hari)', x=['Durasi'], y=[done_ms['planned_duration'].mean()], marker_color='#0d6efd'))
                    fig.add_trace(go.Bar(name='Actual (hari)', x=['Durasi'], y=[done_ms['actual_duration'].mean()], marker_color='#dc3545'))
                    fig.update_layout(height=300, barmode='group')
                    st.plotly_chart(fig, use_container_width=True)
                    st.metric("Rata-rata Keterlambatan", f"{done_ms['delay_days'].mean():.1f} hari")
        
        with col_b:
            st.subheader("Delay Prediction")
            if not site_ms.empty:
                total = len(site_ms)
                done = len(site_ms[site_ms['status'] == 'DONE'])
                prog = round((done/total)*100, 1) if total > 0 else 0
                pred_end = datetime.now() + timedelta(days=int((100-prog)*2)) if prog < 100 else datetime.now()
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=prog, title={'text': "Progress %"},
                    gauge={'axis': {'range': [0, 100]},
                           'bar': {'color': "#28a745" if prog>70 else "#ffc107" if prog>40 else "#dc3545"},
                           'steps': [{'range': [0,40], 'color': "#f8d7da"}, {'range': [40,70], 'color': "#fff3cd"}, {'range': [70,100], 'color': "#d4edda"}]}
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
                st.info(f"📅 Prediksi selesai: **{pred_end.strftime('%d %b %Y')}**")

        # 2. RESOURCE ANALYSIS
        st.header("👷 2. Resource Analysis")
        col_c, col_d = st.columns(2)
        with col_c:
            st.subheader("Team Utilization")
            if not sites_df.empty and 'pm' in sites_df.columns:
                pm_stats = sites_df.groupby('pm').agg(total_sites=('id', 'count'), avg_progress=('progress', 'mean')).reset_index()
                fig = px.bar(pm_stats, x='pm', y='avg_progress', color='total_sites', title="Progress per PM")
                st.plotly_chart(fig, use_container_width=True)
        with col_d:
            st.subheader("Productivity Trend")
            if not site_ms.empty:
                t_ms = site_ms.dropna(subset=['planned_end']).copy()
                t_ms['month'] = t_ms['planned_end'].dt.to_period('M').astype(str)
                m_done = t_ms[t_ms['status']=='DONE'].groupby('month').size().reset_index(name='done')
                if not m_done.empty:
                    fig = px.line(m_done, x='month', y='done', markers=True, title="Milestone Selesai")
                    st.plotly_chart(fig, use_container_width=True)

        # 3. VENDOR ANALYSIS
        st.header("🏢 3. Vendor Analysis")
        if not sites_df.empty and 'vendor' in sites_df.columns:
            v_stats = sites_df.groupby('vendor').agg(
                total_sites=('id', 'count'), avg_progress=('progress', 'mean'),
                on_track=('status', lambda x: (x == 'ON_TRACK').sum()),
                delayed=('status', lambda x: (x.isin(['DELAYED', 'CRITICAL'])).sum())
            ).reset_index()
            v_stats['SLA Score'] = round((v_stats['on_track'] / v_stats['total_sites']) * 100, 1)
            col_e, col_f = st.columns(2)
            with col_e:
                fig = px.bar(v_stats, x='vendor', y='SLA Score', color='total_sites', title="Vendor SLA Score")
                st.plotly_chart(fig, use_container_width=True)
            with col_f:
                st.dataframe(v_stats, use_container_width=True, hide_index=True)

        # 5. EXECUTIVE SUMMARY (Kembali ke format visual asli Anda)
        st.header("📋 5. Executive Summary")
        total_s = len(sites_df)
        avg_p = sites_df['progress'].mean() if not sites_df.empty else 0
        on_t = len(sites_df[sites_df['status']=='ON_TRACK'])
        del_s = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])])
        h_score = round((on_t / total_s * 100) if total_s > 0 else 0)
        h_emoji = '🟢' if h_score >= 80 else ('🟡' if h_score >= 50 else '🔴')
        
        f_end = datetime.now() + timedelta(days=int((100-avg_p)*2)) if not is_all and not site_data.empty else datetime.now() + timedelta(days=int((100-avg_p)*2))

        col_i, col_j, col_k = st.columns(3)
        with col_i:
            st.markdown(f'<div style="text-align:center; padding:10px; border-radius:10px; background:#f8f9fa;"><div style="font-size:14px; color:gray;">{h_emoji} Health Score</div><div style="font-size:24px; font-weight:bold;">{h_score}%</div></div>', unsafe_allow_html=True)
        with col_j:
            st.markdown(f'<div style="text-align:center; padding:10px; border-radius:10px; background:#f8f9fa;"><div style="font-size:14px; color:gray;">📅 Forecast</div><div style="font-size:18px; font-weight:bold;">{f_end.strftime("%d %b %Y")}</div></div>', unsafe_allow_html=True)
        with col_k:
            st.markdown(f'<div style="text-align:center; padding:10px; border-radius:10px; background:#f8f9fa;"><div style="font-size:14px; color:gray;">🎯 KPI</div><div style="font-size:18px; font-weight:bold;">{on_t}/{total_s} On Track</div></div>', unsafe_allow_html=True)

        summary = f"Executive Summary - {datetime.now().strftime('%d %B %Y')}\n\n"
        summary += f"- {total_s} site dalam monitoring.\n- Progress rata-rata: {avg_p:.1f}%\n- {on_t} On Track | {del_s} Delayed.\n"
        
        # EXPORT PDF (Dibetulkan agar berfungsi)
        st.divider()
        st.subheader("📥 Export Report")
        if st.button("📄 Generate PDF Report"):
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font('Helvetica', 'B', 16)
                pdf.cell(0, 10, 'AI Analytics Report', 0, 1, 'C')
                pdf.set_font('Helvetica', '', 10)
                pdf.cell(0, 7, f'Site: {site_name}', 0, 1)
                pdf.cell(0, 7, f'Health Score: {h_score}%', 0, 1)
                pdf.cell(0, 7, f'Progress: {avg_p:.1f}%', 0, 1)
                pdf.ln(5)
                pdf.set_font('Helvetica', 'B', 12)
                pdf.cell(0, 10, 'Summary:', 0, 1)
                pdf.set_font('Helvetica', '', 10)
                for line in summary.split('\n'):
                    pdf.cell(0, 6, line, 0, 1)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    pdf.output(tmp.name)
                    with open(tmp.name, 'rb') as f:
                        st.download_button("📥 Download PDF", f.read(), f"Report_{site_name}.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Gagal generate PDF: {e}")

if __name__ == "__main__":
    ai_insights_page()
