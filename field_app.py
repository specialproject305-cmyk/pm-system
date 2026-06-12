import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from supabase_db import read_sheet, update_row, read_all_sheets, insert_row, generate_id, now_str

def field_app_page():
    # ═══════════════════════════════════════
    # AUTO-FILTER BY ROLE
    # ═══════════════════════════════════════
    user = st.session_state.get('user', {})
    role = user.get('role', 'engineer')
    
    role_map = {
        'sitac': 'Sitac', 'legal': 'Legal', 'engineering': 'Engineering',
        'procurement': 'Procurement', 'project': 'Project',
        'vendor_mgmt': 'Vendor Management'
    }
    assigned_to = role_map.get(role, role)
    
    st.title(f"📱 Field App - {assigned_to}")
    
    all_data = read_all_sheets()
    ms_df = all_data.get('milestones', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    messages = all_data.get('chat_messages', pd.DataFrame())
    
    if ms_df.empty:
        st.info("📋 Belum ada milestone.")
        return
    
    # Filter task hanya untuk PIC ini
    ms_df = ms_df[ms_df['assigned_to'] == assigned_to].copy()
    ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    
    # ═══════════════════════════════════════
    # SIDEBAR
    # ═══════════════════════════════════════
    with st.sidebar:
        st.markdown(f"👷 **{user.get('full_name', assigned_to)}**")
        st.markdown(f"Role: **{assigned_to}**")
        st.divider()
        
        if st.button("🚪 Logout", key="field_logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state['logged_in'] = False
            st.rerun()
        
        st.divider()
        st.metric("📋 Task Saya", len(ms_df))
        if not ms_df.empty:
            overdue = len(ms_df[ms_df['planned_end'].dt.date < date.today()])
            st.metric("🔴 Overdue", overdue)
    
    # ═══════════════════════════════════════
    # TABS
    # ═══════════════════════════════════════
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Update Task", "📊 Mini Dashboard", "📋 Kanban", "🤖 AI Insights", "🔍 RCA"])
    
    site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    site_name_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    
    # ===== TAB 1: UPDATE TASK =====
    with tab1:
        if ms_df.empty:
            st.success("✅ Tidak ada task!")
        else:
            for _, task in ms_df.iterrows():
                site_code = site_map.get(task['project_id'], '-')
                deadline = task['planned_end'].strftime('%d %b %Y') if pd.notna(task['planned_end']) else '-'
                days_left = (task['planned_end'].date() - date.today()).days if pd.notna(task['planned_end']) else 999
                
                st.markdown(f"""
                <div style='background:#1E293B; padding:10px; border-radius:8px; margin:5px 0; border-left:4px solid #38BDF8; color:white;'>
                    <strong>{task['name']}</strong><br>
                    📍 {site_code} | 📅 {deadline} | ⏰ {days_left} hari | {task.get('status','?')}
                </div>
                """, unsafe_allow_html=True)
                
                with st.form(f"upd_{task['id']}", clear_on_submit=False):
                    c1, c2 = st.columns(2)
                    with c1:
                        new_status = st.selectbox("Status", ['PENDING','ONGOING','DONE','DELAYED'], key=f"st_{task['id']}")
                        as_d = pd.to_datetime(task.get('actual_start')).date() if pd.notna(task.get('actual_start')) else None
                        new_as = st.date_input("Actual Start", value=as_d, key=f"as_{task['id']}")
                    with c2:
                        cur_p = int(float(task.get('progress',0))) if task.get('progress') else 0
                        new_progress = st.slider("Progress %", 0, 100, cur_p, key=f"pr_{task['id']}")
                        ae_d = pd.to_datetime(task.get('actual_end')).date() if pd.notna(task.get('actual_end')) else None
                        new_ae = st.date_input("Actual End", value=ae_d, key=f"ae_{task['id']}")
                    
                    if st.form_submit_button("💾 Simpan", use_container_width=True):
                        update_data = {'status': new_status, 'progress': str(new_progress)}
                        if new_as: update_data['actual_start'] = new_as.strftime('%Y-%m-%d')
                        if new_ae: update_data['actual_end'] = new_ae.strftime('%Y-%m-%d')
                        update_row('milestones', task['id'], update_data)
                        st.success(f"✅ {task['name']} diupdate!")
                        st.rerun()
                st.markdown("---")
    
    # ===== TAB 2: MINI DASHBOARD =====
    with tab2:
        st.subheader(f"📊 Performa {assigned_to}")
        if not ms_df.empty:
            total = len(ms_df)
            done = len(ms_df[ms_df['status'] == 'DONE'])
            overdue = len(ms_df[ms_df['planned_end'].dt.date < date.today()])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Task", total)
            col2.metric("✅ Done", done)
            col3.metric("🔴 Overdue", overdue)
            
            # Progress chart
            st.bar_chart(ms_df.groupby('status').size())
    
    # ===== TAB 3: KANBAN =====
    with tab3:
        st.subheader(f"📋 Kanban {assigned_to}")
        cols = st.columns(4)
        statuses = ['PENDING', 'ONGOING', 'DONE', 'DELAYED']
        colors = {'PENDING': '#94A3B8', 'ONGOING': '#3B82F6', 'DONE': '#10B981', 'DELAYED': '#EF4444'}
        
        for i, status in enumerate(statuses):
            with cols[i]:
                st.markdown(f"**{status}**")
                subset = ms_df[ms_df['status'] == status]
                for _, t in subset.iterrows():
                    st.markdown(f"<div style='background:#1E293B; padding:5px; margin:2px 0; border-left:3px solid {colors[status]}; color:white; font-size:0.8rem;'>{t['name']}</div>", unsafe_allow_html=True)
    
    # ===== TAB 4: AI INSIGHTS =====
    with tab4:
        st.subheader(f"🤖 AI Insights - {assigned_to}")
        if not ms_df.empty:
            done = len(ms_df[ms_df['status'] == 'DONE'])
            total = len(ms_df)
            st.metric("Completion Rate", f"{(done/total)*100:.1f}%" if total > 0 else "0%")
            st.info("Prediksi: " + ("On Track" if done/total > 0.7 else "Perlu Perhatian"))
    
    # ===== TAB 5: RCA =====
    with tab5:
        st.subheader(f"🔍 RCA - {assigned_to}")
        delayed = ms_df[ms_df['status'] == 'DELAYED']
        if not delayed.empty:
            for _, t in delayed.iterrows():
                st.error(f"{t['name']} - {t.get('delay_reason', 'Tidak diketahui')}")
        else:
            st.success("Tidak ada task delayed!")

if __name__ == "__main__":
    field_app_page()
