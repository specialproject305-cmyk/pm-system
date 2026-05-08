import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from supabase_db import read_all_sheets

def dashboard_page():
    now = datetime.now()
    
    col_header, col_clock = st.columns([3, 1])
    with col_header:
        st.title("🏗️ Site Management Dashboard")
    with col_clock:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                    padding: 15px; border-radius: 10px; text-align: center; color: white;">
            <div style="font-size: 14px;">📅 {now.strftime('%A, %d %B %Y')}</div>
            <div style="font-size: 28px; font-weight: bold;">🕐 {now.strftime('%H:%M:%S')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Load data
    all_data = read_all_sheets()
    df = all_data.get('projects', pd.DataFrame())
    materials_df = all_data.get('materials', pd.DataFrame())
    milestones_df = all_data.get('milestones', pd.DataFrame())
    
    # ===== TOAST NOTIFICATIONS =====
    messages = all_data.get('chat_messages', pd.DataFrame())
    
    if not messages.empty and 'sender' in messages.columns:
        latest_msg = messages.iloc[-1]
        st.toast(f"💬 {latest_msg.get('sender','')}: {str(latest_msg.get('message',''))[:40]}...", icon="💬")
    
    if not milestones_df.empty and 'status' in milestones_df.columns:
        delayed = milestones_df[milestones_df['status'] == 'DELAYED']
        if not delayed.empty:
            st.toast(f"⚠️ {len(delayed)} milestone terlambat!", icon="⚠️")
    
    if not materials_df.empty:
        for c in ['current_stock', 'min_stock']:
            if c in materials_df.columns:
                materials_df[c] = pd.to_numeric(materials_df[c], errors='coerce').fillna(0)
        critical = materials_df[materials_df['current_stock'] < materials_df['min_stock']]
        if not critical.empty:
            st.toast(f"🔴 {len(critical)} material stok kritis!", icon="🔴")
    
    # Konversi numerik
    if not df.empty and 'progress' in df.columns:
        df['progress'] = pd.to_numeric(df['progress'], errors='coerce').fillna(0)
    
    # ===== KPI CARDS =====
    total_sites = len(df)
    avg_progress = df['progress'].mean() if not df.empty else 0
    on_track = len(df[df['status']=='ON_TRACK']) if not df.empty and 'status' in df.columns else 0
    delayed_ms = len(milestones_df[milestones_df['status']=='DELAYED']) if not milestones_df.empty and 'status' in milestones_df.columns else 0
    critical_mat = len(materials_df[materials_df['current_stock'] < materials_df['min_stock']]) if not materials_df.empty else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📁 Total Site", total_sites)
    col2.metric("📈 Avg Progress", f"{avg_progress:.1f}%")
    col3.metric("⚠️ MS Terlambat", delayed_ms)
    col4.metric("🔴 Mat. Kritis", critical_mat)
    
    st.markdown("---")
    
    # ===== PROGRESS TABLE =====
    st.subheader("📊 Progress per Site")
    if not df.empty:
        table_data = df[['site_id', 'site_name', 'status', 'progress', 'pm']].copy()
        table_data = table_data.sort_values('progress', ascending=False)
        
        def status_badge(val):
            if val == 'ON_TRACK': return '🟢 On Track'
            elif val == 'DELAYED': return '🟡 Delayed'
            elif val == 'CRITICAL': return '🔴 Critical'
            return val
        
        def progress_bar(val):
            color = '#28a745' if val >= 70 else ('#ffc107' if val >= 40 else '#dc3545')
            return f"""<div style="background:#e9ecef; border-radius:10px; height:20px; width:100%;">
                <div style="background:{color}; width:{val}%; height:100%; border-radius:10px; text-align:center; color:white; font-weight:bold; font-size:11px;">{val:.0f}%</div></div>"""
        
        table_data['Status'] = table_data['status'].apply(status_badge)
        table_data['Progress Bar'] = table_data['progress'].apply(progress_bar)
        
        html = '<table style="width:100%; border-collapse:collapse;">'
        html += '<tr style="background:#f8f9fa;"><th>Site ID</th><th>Site Name</th><th>Status</th><th style="width:40%">Progress</th><th>PM</th></tr>'
        for _, row in table_data.head(15).iterrows():
            html += f"<tr style='border-bottom:1px solid #f0f0f0;'>"
            html += f"<td><b>{row['site_id']}</b></td><td>{row['site_name']}</td><td>{row['Status']}</td><td>{row['Progress Bar']}</td><td>{row['pm']}</td></tr>"
        html += '</table>'
        st.markdown(html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== MINI INSIGHTS =====
    st.subheader("🤖 Mini Insights")
    col_i1, col_i2, col_i3 = st.columns(3)
    
    with col_i1:
        with st.container(border=True):
            st.markdown("### ⚠️ Site Perlu Perhatian")
            if not df.empty:
                crit_sites = df[df['status'].isin(['CRITICAL','DELAYED']) | (df['progress']<30)]
                if not crit_sites.empty:
                    for _, r in crit_sites.head(3).iterrows():
                        color = '🔴' if r.get('status')=='CRITICAL' else '🟡'
                        st.markdown(f"{color} **{r.get('site_id','?')}** — {r.get('progress',0):.0f}%")
                else:
                    st.success("Semua site aman!")
    
    with col_i2:
        with st.container(border=True):
            st.markdown("### 📦 Material Kritis")
            if not materials_df.empty:
                crit_mat2 = materials_df[materials_df['current_stock'] < materials_df['min_stock']]
                if not crit_mat2.empty:
                    for _, r in crit_mat2.head(3).iterrows():
                        st.markdown(f"🔴 **{r['name']}** — Stok {r['current_stock']}")
                else:
                    st.success("Material aman!")
    
    with col_i3:
        with st.container(border=True):
            st.markdown("### 🎯 Rekomendasi")
            if delayed_ms > 5: st.warning("⚠️ Banyak milestone terlambat")
            if critical_mat > 3: st.warning("📦 >3 material kritis")
            if total_sites > 0 and on_track/total_sites >= 0.8: st.success("✅ Performa bagus!")

if __name__ == "__main__":
    dashboard_page()
