import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from supabase_db import read_all_sheets

def dashboard_page():
    now = datetime.now()
    
    # ===== HEADER DENGAN JAM =====
    col_header, col_clock = st.columns([3, 1])
    with col_header:
        st.title("🏗️ Site Management Dashboard")
    with col_clock:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                    padding: 15px; border-radius: 10px; text-align: center; color: white;">
            <div style="font-size: 14px;">📅 {now.strftime('%A, %d %B %Y')}</div>
            <div style="font-size: 28px; font-weight: bold;">🕐 {now.strftime('%H:%M:%S')}</div>
            <div style="font-size: 11px;">WIB</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ===== LOAD DATA =====
    all_data = read_all_sheets()
    df = all_data.get('projects', pd.DataFrame())
    materials_df = all_data.get('materials', pd.DataFrame())
    milestones_df = all_data.get('milestones', pd.DataFrame())
    
    if not df.empty:
        if 'progress' in df.columns:
            df['progress'] = pd.to_numeric(df['progress'], errors='coerce').fillna(0)
        df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
        df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')
    
    if not materials_df.empty:
        for c in ['current_stock', 'min_stock']:
            if c in materials_df.columns:
                materials_df[c] = pd.to_numeric(materials_df[c], errors='coerce').fillna(0)

    # ===== TOAST NOTIFICATIONS =====
messages = all_data.get('chat_messages', pd.DataFrame())
notifs = all_data.get('notifications', pd.DataFrame())
milestones_df = all_data.get('milestones', pd.DataFrame())
materials_df = all_data.get('materials', pd.DataFrame())

# 1. Chat baru (30 detik terakhir)
if not messages.empty:
    latest_msg = messages.iloc[-1]
    msg_time = latest_msg.get('created_at', '')
    st.toast(f"💬 {latest_msg.get('sender','')}: {latest_msg.get('message','')[:40]}...", icon="💬")

# 2. Milestone terlambat
if not milestones_df.empty and 'status' in milestones_df.columns:
    delayed = milestones_df[milestones_df['status'] == 'DELAYED']
    if not delayed.empty:
        st.toast(f"⚠️ {len(delayed)} milestone terlambat!", icon="⚠️")

# 3. Material kritis
if not materials_df.empty:
    for c in ['current_stock', 'min_stock']:
        if c in materials_df.columns:
            materials_df[c] = pd.to_numeric(materials_df[c], errors='coerce').fillna(0)
    critical = materials_df[materials_df['current_stock'] < materials_df['min_stock']]
    if not critical.empty:
        st.toast(f"🔴 {len(critical)} material stok kritis!", icon="🔴")
        
    # ===== FILTERS =====
    st.markdown("### 🔍 Filter Data")
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 1])
    
    with col_f1:
        pm_list = df['pm'].dropna().unique().tolist() if not df.empty and 'pm' in df.columns else []
        filter_pm = st.multiselect("👤 Filter PM:", pm_list, default=[], placeholder="Semua PM")
    
    with col_f2:
        vendor_list = df['vendor'].dropna().unique().tolist() if not df.empty and 'vendor' in df.columns else []
        filter_vendor = st.multiselect("🏢 Filter Vendor:", vendor_list, default=[], placeholder="Semua Vendor")
    
    with col_f3:
        date_range = st.date_input("📅 Periode:", value=(date.today() - timedelta(days=30), date.today()), max_value=date.today())
    
    with col_f4:
        st.markdown("<br>", unsafe_allow_html=True)
        apply_filter = st.button("🔄 Terapkan", type="primary", use_container_width=True)
    
    # Filter dataframe
    filtered = df.copy()
    if not filtered.empty:
        if filter_pm:
            filtered = filtered[filtered['pm'].isin(filter_pm)]
        if filter_vendor:
            filtered = filtered[filtered['vendor'].isin(filter_vendor)]
    
    st.markdown("---")
    
    # ===== KPI CARDS =====
    total_sites = len(filtered)
    avg_progress = filtered['progress'].mean() if not filtered.empty else 0
    on_track = len(filtered[filtered['status']=='ON_TRACK']) if not filtered.empty and 'status' in filtered.columns else 0
    delayed_sites = len(filtered[filtered['status'].isin(['DELAYED','CRITICAL'])]) if not filtered.empty and 'status' in filtered.columns else 0
    
    critical_mat = len(materials_df[materials_df['current_stock'] < materials_df['min_stock']]) if not materials_df.empty else 0
    delayed_ms = len(milestones_df[milestones_df['status']=='DELAYED']) if not milestones_df.empty and 'status' in milestones_df.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px; border-radius: 15px; color: white; text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <div style="font-size: 40px;">📁</div>
            <div style="font-size: 36px; font-weight: bold;">{total_sites}</div>
            <div style="font-size: 14px;">Total Site</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        prog_color = '#28a745' if avg_progress >= 70 else ('#ffc107' if avg_progress >= 40 else '#dc3545')
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {prog_color} 0%, #17a2b8 100%);
                    padding: 20px; border-radius: 15px; color: white; text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <div style="font-size: 40px;">📈</div>
            <div style="font-size: 36px; font-weight: bold;">{avg_progress:.1f}%</div>
            <div style="font-size: 14px;">Avg Progress</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 20px; border-radius: 15px; color: white; text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <div style="font-size: 40px;">⚠️</div>
            <div style="font-size: 36px; font-weight: bold;">{delayed_ms}</div>
            <div style="font-size: 14px;">MS Terlambat</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                    padding: 20px; border-radius: 15px; color: white; text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <div style="font-size: 40px;">🔴</div>
            <div style="font-size: 36px; font-weight: bold;">{critical_mat}</div>
            <div style="font-size: 14px;">Mat. Kritis</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Mini Insight Bar
    st.markdown("---")
    col_i1, col_i2, col_i3, col_i4 = st.columns(4)
    col_i1.metric("🟢 On Track", on_track)
    col_i2.metric("🟡 Delayed", delayed_sites)
    col_i3.metric("🔴 Critical", len(filtered[filtered['status']=='CRITICAL']) if not filtered.empty and 'status' in filtered.columns else 0)
    col_i4.metric("📦 Mat. Kritis", critical_mat)
    
    st.markdown("---")
    
    # ===== ROW 1: PROGRESS BAR + S-CURVE =====
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("📊 Progress per Site")
        if not filtered.empty:
            # Tabel dengan progress bar
            table_data = filtered[['site_id', 'site_name', 'status', 'progress', 'pm']].copy()
            table_data = table_data.sort_values('progress', ascending=False)
            
            # Format untuk tampilan
            def progress_bar(val):
                color = '#28a745' if val >= 70 else ('#ffc107' if val >= 40 else '#dc3545')
                return f"""
                <div style="background:#e9ecef; border-radius:10px; height:20px; width:100%;">
                    <div style="background:{color}; width:{val}%; height:100%; border-radius:10px; 
                              text-align:center; color:white; font-weight:bold; font-size:11px;">
                        {val:.0f}%
                    </div>
                </div>
                """
            
            def status_badge(val):
                if val == 'ON_TRACK':
                    return '🟢 On Track'
                elif val == 'DELAYED':
                    return '🟡 Delayed'
                elif val == 'CRITICAL':
                    return '🔴 Critical'
                return val
            
            table_data['Status'] = table_data['status'].apply(status_badge)
            table_data['Progress Bar'] = table_data['progress'].apply(progress_bar)
            
            # Tampilkan sebagai HTML
            st.markdown("""
            <style>
            .site-table { width:100%; border-collapse:collapse; }
            .site-table th { background:#f8f9fa; padding:8px; text-align:left; border-bottom:2px solid #dee2e6; }
            .site-table td { padding:6px 8px; border-bottom:1px solid #f0f0f0; vertical-align:middle; }
            </style>
            """, unsafe_allow_html=True)
            
            html = '<table class="site-table">'
            html += '<tr><th>Site ID</th><th>Site Name</th><th>Status</th><th style="width:40%">Progress</th><th>PM</th></tr>'
            
            for _, row in table_data.head(15).iterrows():
                html += f"<tr>"
                html += f"<td><b>{row['site_id']}</b></td>"
                html += f"<td>{row['site_name']}</td>"
                html += f"<td>{row['Status']}</td>"
                html += f"<td>{row['Progress Bar']}</td>"
                html += f"<td>{row['pm']}</td>"
                html += f"</tr>"
            
            html += '</table>'
            st.markdown(html, unsafe_allow_html=True)
            
            st.caption(f"Menampilkan {min(15, len(filtered))} dari {len(filtered)} site")
        else:
            st.info("📋 Tidak ada data.")
    
    with col_right:
        st.subheader("📈 S-Curve Progress")
        if not filtered.empty:
            total = len(filtered)
            milestones_labels = ['0%', '10%', '25%', '50%', '75%', '90%', '100%']
            values = [0,
                     (len(filtered[filtered['progress']>=10])/total)*100 if total>0 else 0,
                     (len(filtered[filtered['progress']>=25])/total)*100 if total>0 else 0,
                     (len(filtered[filtered['progress']>=50])/total)*100 if total>0 else 0,
                     (len(filtered[filtered['progress']>=75])/total)*100 if total>0 else 0,
                     (len(filtered[filtered['progress']>=90])/total)*100 if total>0 else 0,
                     (len(filtered[filtered['progress']>=100])/total)*100 if total>0 else 0]
            
            fig_sc = go.Figure()
            fig_sc.add_trace(go.Scatter(
                x=milestones_labels, y=values, mode='lines+markers',
                line=dict(color='#667eea', width=3, shape='spline'),
                marker=dict(size=10, color='#764ba2'),
                fill='tozeroy', fillcolor='rgba(102,126,234,0.2)'
            ))
            fig_sc.update_layout(height=350, yaxis=dict(range=[0,105]),
                               plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                               margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_sc, use_container_width=True)
            
            if avg_progress >= 80:
                st.success(f"✅ {on_track/total*100:.0f}% site On Track — Performa bagus!" if total>0 else "")
            elif avg_progress >= 50:
                st.warning(f"⚠️ {on_track/total*100:.0f}% site On Track — Perlu perhatian" if total>0 else "")
            else:
                st.error(f"🔴 {on_track/total*100:.0f}% site On Track — Tindakan diperlukan!" if total>0 else "")
    
    st.markdown("---")
    
    # ===== ROW 2: MATERIAL + WEEKLY =====
    col_left2, col_right2 = st.columns([1, 1])
    
    with col_left2:
        st.subheader("📦 Material: Kebutuhan vs Stok")
        if not materials_df.empty:
            mat_disp = materials_df.head(12).copy()
            fig_mat = go.Figure()
            fig_mat.add_trace(go.Bar(name='Stok Saat Ini', y=mat_disp['name'], x=mat_disp['current_stock'],
                                    orientation='h', marker=dict(color='#28a745')))
            fig_mat.add_trace(go.Bar(name='Stok Minimum', y=mat_disp['name'], x=mat_disp['min_stock'],
                                    orientation='h', marker=dict(color='#dc3545', opacity=0.5)))
            fig_mat.update_layout(height=max(300, len(mat_disp)*35), barmode='group',
                                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                margin=dict(l=10, r=30, t=20, b=10),
                                legend=dict(orientation='h', y=1.02))
            st.plotly_chart(fig_mat, use_container_width=True)
        else:
            st.info("📦 Belum ada material.")
    
    with col_right2:
        st.subheader("📊 Progress per Minggu")
        if not milestones_df.empty and 'planned_end' in milestones_df.columns:
            milestones_df['week'] = pd.to_datetime(milestones_df['planned_end'], errors='coerce').dt.strftime('%Y-W%W')
            weekly = milestones_df.groupby('week').agg(
                ms_done=('status', lambda x: (x=='DONE').sum()),
                ms_delayed=('status', lambda x: (x=='DELAYED').sum())
            ).reset_index().tail(12)
            
            if not weekly.empty:
                fig_w = go.Figure()
                fig_w.add_trace(go.Bar(name='MS Selesai', x=weekly['week'], y=weekly['ms_done'], marker=dict(color='#28a745')))
                fig_w.add_trace(go.Bar(name='MS Terlambat', x=weekly['week'], y=weekly['ms_delayed'], marker=dict(color='#dc3545')))
                fig_w.update_layout(height=350, barmode='group',
                                  plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                  margin=dict(l=10, r=10, t=20, b=10),
                                  legend=dict(orientation='h', y=1.02))
                st.plotly_chart(fig_w, use_container_width=True)
            else:
                st.info("📊 Belum ada data mingguan.")
        else:
            st.info("📊 Belum ada data mingguan.")
    
    st.markdown("---")
    
    # ===== MINI INSIGHTS =====
    st.subheader("🤖 Mini Insights")
    col_m1, col_m2, col_m3 = st.columns(3)
    
    with col_m1:
        with st.container(border=True):
            st.markdown("### ⚠️ Site Perlu Perhatian")
            if not filtered.empty:
                crit = filtered[filtered['status'].isin(['CRITICAL','DELAYED']) | (filtered['progress']<30)]
                if not crit.empty:
                    for _, r in crit.head(3).iterrows():
                        color = '🔴' if r.get('status')=='CRITICAL' else '🟡'
                        st.markdown(f"{color} **{r.get('site_id','?')}** — {r.get('progress',0):.0f}%")
                else:
                    st.success("Semua site aman!")
            else:
                st.success("Semua site aman!")
    
    with col_m2:
        with st.container(border=True):
            st.markdown("### 📦 Top Material Kritis")
            if not materials_df.empty:
                crit2 = materials_df[materials_df['current_stock'] < materials_df['min_stock']]
                if not crit2.empty:
                    for _, r in crit2.head(3).iterrows():
                        gap = r['min_stock'] - r['current_stock']
                        st.markdown(f"🔴 **{r['name']}** — Kurang {gap:.0f}")
                else:
                    st.success("Material cukup!")
            else:
                st.success("Material cukup!")
    
    with col_m3:
        with st.container(border=True):
            st.markdown("### 🎯 Rekomendasi Cepat")
            if delayed_ms > 5:
                st.warning("⚠️ Banyak milestone terlambat")
            if critical_mat > 3:
                st.warning("📦 >3 material kritis")
            if delayed_sites > 0:
                st.error(f"🔴 {delayed_sites} site terlambat")
            if total_sites > 0 and on_track/total_sites >= 0.8:
                st.success("✅ Performa bagus!")

if __name__ == "__main__":
    dashboard_page()
