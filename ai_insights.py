import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase_db import read_all_sheets

def ai_insights_page():
    st.title("🤖 AI-Powered Analytics Center")
    
    all_data = read_all_sheets()
    sites_df = all_data.get('projects', pd.DataFrame())
    ms_df = all_data.get('milestones', pd.DataFrame())
    mat_df = all_data.get('materials', pd.DataFrame())
    
    if sites_df.empty:
        st.warning("⚠️ Belum ada data site.")
        return
    
    if not sites_df.empty and 'progress' in sites_df.columns:
        sites_df['progress'] = pd.to_numeric(sites_df['progress'], errors='coerce').fillna(0)
    if not ms_df.empty:
        for col in ['planned_start', 'planned_end', 'actual_start', 'actual_end']:
            if col in ms_df.columns:
                ms_df[col] = pd.to_datetime(ms_df[col], errors='coerce')
    
    site_options = ["ALL SITE"] + sites_df["id"].tolist()
    selected_site = st.selectbox("🎯 Pilih Site:", site_options,
        format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE" 
        else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
    
    is_all = (selected_site == "ALL SITE")
    if not is_all:
        site_ms = ms_df[ms_df['project_id'] == selected_site] if not ms_df.empty else pd.DataFrame()
        site_name = sites_df[sites_df['id']==selected_site].iloc[0]['site_name']
    else:
        site_ms = ms_df
        site_name = "ALL SITE"
    
    if st.button("🔍 Generate Full Analysis", type="primary"):
        st.divider()
        
        # 1. PROGRESS
        st.header("📈 1. Progress Analysis")
        col_a, col_b = st.columns(2)
        with col_a:
            if not site_ms.empty:
                done = len(site_ms[site_ms['status']=='DONE'])
                total = len(site_ms)
                progress = round((done/total)*100, 1) if total > 0 else 0
                fig = go.Figure(go.Indicator(mode="gauge+number", value=progress, 
                    gauge={'axis': {'range': [0,100]}, 'bar': {'color': "#28a745" if progress>70 else "#ffc107" if progress>40 else "#dc3545"}}))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
                st.metric("Progress", f"{progress}%")
        with col_b:
            if not site_ms.empty:
                delayed = len(site_ms[site_ms['status']=='DELAYED'])
                st.metric("⚠️ Delayed", delayed)
                critical = site_ms[site_ms['status']=='DELAYED']
                if not critical.empty:
                    for _, c in critical.head(5).iterrows():
                        st.markdown(f"- **{c['name']}**")
        
        # 2. PIC PERFORMANCE
        st.divider()
        st.header("👤 2. PIC Performance")
        if not site_ms.empty and 'assigned_to' in site_ms.columns:
            assigned = site_ms[site_ms['assigned_to'].notna() & (site_ms['assigned_to'] != '')]
            if not assigned.empty:
                pic_stats = assigned.groupby('assigned_to').agg(
                    total=('id','count'),
                    done=('status', lambda x: (x=='DONE').sum()),
                    delayed=('status', lambda x: (x=='DELAYED').sum())
                ).reset_index()
                pic_stats['sla_score'] = round((pic_stats['done']/pic_stats['total'])*100, 1)
                
                fig = px.bar(pic_stats, x='assigned_to', y='sla_score', color='sla_score',
                    color_continuous_scale=['#dc3545','#ffc107','#28a745'])
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(pic_stats, use_container_width=True, hide_index=True)
            else:
                st.info("ℹ️ Data assigned_to kosong.")
        else:
            st.info("ℹ️ Kolom assigned_to tidak tersedia.")
        
        # 3. SLA COMPLIANCE
        st.divider()
        st.header("⏱️ 3. SLA Compliance")
        if not site_ms.empty and 'sla_days' in site_ms.columns:
            sla_data = site_ms[site_ms['sla_days'].notna() & (site_ms['sla_days'] != '') & site_ms['actual_end'].notna()]
            if not sla_data.empty:
                sla_data['sla_days_num'] = pd.to_numeric(sla_data['sla_days'], errors='coerce')
                sla_data['actual_duration'] = (pd.to_datetime(sla_data['actual_end']) - pd.to_datetime(sla_data['planned_start'])).dt.days
                sla_data['on_sla'] = sla_data['actual_duration'] <= sla_data['sla_days_num']
                
                on_sla = sla_data['on_sla'].sum()
                breach = len(sla_data) - on_sla
                
                col1, col2 = st.columns(2)
                col1.metric("✅ On SLA", on_sla)
                col2.metric("❌ Breach", breach)
                
                fig = px.pie(values=[on_sla, breach], names=['On SLA','Breach'], 
                    color_discrete_map={'On SLA':'#28a745','Breach':'#dc3545'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ℹ️ Data SLA kosong atau belum ada actual end.")
        else:
            st.info("ℹ️ Kolom sla_days tidak tersedia.")
        
        # 4. EXECUTIVE SUMMARY
        st.divider()
        st.header("📋 4. Executive Summary")
        total_sites = len(sites_df)
        avg_progress = sites_df['progress'].mean() if not sites_df.empty else 0
        on_track = len(sites_df[sites_df['status']=='ON_TRACK']) if not sites_df.empty else 0
        delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])]) if not sites_df.empty else 0
        health = round((on_track/total_sites)*100) if total_sites > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🟢 Health Score", f"{health}%")
        col2.metric("📅 Forecast", (datetime.now() + timedelta(days=int((100-avg_progress)*2))).strftime('%d %b %Y'))
        col3.metric("🎯 KPI", f"{on_track}/{total_sites} On Track")
        
        st.info(f"📊 {total_sites} site | Progress: {avg_progress:.1f}% | On Track: {on_track} | Delayed: {delayed}")

if __name__ == "__main__":
    ai_insights_page()
