import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from supabase_db import read_sheet, update_row, read_all_sheets, insert_row, generate_id, now_str

def field_app_page():
    st.title("📱 Field Update App")

        # Toggle sidebar
    if "sidebar_expanded" not in st.session_state:
        st.session_state.sidebar_expanded = True
    
    col_title, col_btn = st.columns([4, 1])
    with col_btn:
        if st.button("☰ Menu", use_container_width=True):
            st.session_state.sidebar_expanded = not st.session_state.sidebar_expanded
            st.rerun()
    
    all_data = read_all_sheets()
    ms_df = all_data.get('milestones', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    master_df = all_data.get('master_projects', pd.DataFrame())
    messages = all_data.get('chat_messages', pd.DataFrame())
    
    if ms_df.empty:
        st.info("📋 Belum ada milestone.")
        return
    
    ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    
    # ===== FILTER DI ATAS (HALAMAN UTAMA) =====
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_master = "ALL"
        if not master_df.empty:
            master_options = ["ALL"] + master_df['id'].tolist()
            selected_master = st.selectbox("🏢 Project:", master_options,
                format_func=lambda x: "🌐 SEMUA" if x == "ALL" 
                else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}")
    
    with col2:
        if not sites_df.empty:
            site_options = ["ALL"] + sorted(sites_df['site_name'].unique().tolist())
            selected_site = st.selectbox("📍 Site:", site_options)
        else:
            selected_site = "ALL"
    
    with col3:
        pic_list = sorted(ms_df['assigned_to'].dropna().unique().tolist()) if 'assigned_to' in ms_df.columns else []
        if pic_list:
            selected_pic = st.selectbox("👷 PIC:", ["ALL"] + pic_list)
        else:
            selected_pic = "ALL"
    
    # Apply filter
    if selected_master != "ALL":
        ms_df = ms_df[ms_df['project_id'].isin(
            sites_df[sites_df['master_project_id'] == selected_master]['id'].tolist()
        )]
    if selected_site != "ALL":
        ms_df = ms_df[ms_df['project_id'].isin(
            sites_df[sites_df['site_name'] == selected_site]['id'].tolist()
        )]
    if selected_pic != "ALL":
        ms_df = ms_df[ms_df['assigned_to'] == selected_pic]
    
    # ===== TABS =====
    tab1, tab2, tab3 = st.tabs(["📱 Update Tasks", "💬 Team Chat", "📋 Daily Tasks"])
    
    # ===== TAB 1: UPDATE TASKS =====
    with tab1:
        if ms_df.empty:
            st.success("✅ Tidak ada task!")
        else:
            st.metric("📋 Tasks", len(ms_df))
            
            site_map = dict(zip(sites_df['id'], sites_df['site_id']))
            site_name_map = dict(zip(sites_df['id'], sites_df['site_name']))
            
            for _, task in ms_df.iterrows():
                site_code = site_map.get(task['project_id'], '-')
                site_name = site_name_map.get(task['project_id'], '-')
                deadline = task['planned_end'].strftime('%d %b %Y') if pd.notna(task['planned_end']) else '-'
                days_left = (task['planned_end'].date() - date.today()).days if pd.notna(task['planned_end']) else 999
                
                if days_left < 0: bg, border = '#FEE2E2', '#EF4444'
                elif days_left == 0: bg, border = '#FEF3C7', '#F59E0B'
                elif task['status'] == 'DONE': bg, border = '#DCFCE7', '#10B981'
                else: bg, border = '#F0FDF4', '#10B981'
                
                st.markdown(f"""
                <div style='background:{bg}; padding:10px; border-radius:8px; margin:5px 0; border-left:4px solid {border};'>
                    <strong>{task['name']}</strong><br>
                    📍 {site_code} - {site_name} | 📅 {deadline} | ⏰ {days_left} hari | {task.get('status','?')}
                </div>
                """, unsafe_allow_html=True)
                
                with st.form(f"upd_{task['id']}", clear_on_submit=False):
                    c1, c2 = st.columns(2)
                    with c1:
                        statuses = ['PENDING','ONGOING','DONE','DELAYED']
                        cur_s = task.get('status','PENDING')
                        s_idx = statuses.index(cur_s) if cur_s in statuses else 0
                        new_status = st.selectbox("Status", statuses, index=s_idx, key=f"st_{task['id']}")
                        as_d = pd.to_datetime(task.get('actual_start')).date() if pd.notna(task.get('actual_start')) else None
                        new_as = st.date_input("Actual Start", value=as_d, key=f"as_{task['id']}")
                    with c2:
                        cur_p = int(float(task.get('progress',0))) if task.get('progress') and str(task.get('progress','')).replace('.','').isdigit() else 0
                        new_progress = st.slider("Progress %", 0, 100, cur_p, key=f"pr_{task['id']}")
                        ae_d = pd.to_datetime(task.get('actual_end')).date() if pd.notna(task.get('actual_end')) else None
                        new_ae = st.date_input("Actual End", value=ae_d, key=f"ae_{task['id']}")
                    
                    if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                        update_data = {'status': new_status, 'progress': str(new_progress)}
                        if new_as: update_data['actual_start'] = new_as.strftime('%Y-%m-%d')
                        if new_ae or new_status == 'DONE':
                            update_data['actual_end'] = (new_ae or date.today()).strftime('%Y-%m-%d')
                        update_row('milestones', task['id'], update_data)
                        st.cache_data.clear()
                        st.success(f"✅ {task['name']} diupdate!")
                        st.toast(f"✅ {task['name']} → {new_status}", icon="🎉")
                        st.rerun()
                st.markdown("---")
    
    # ===== TAB 2: CHAT =====
    with tab2:
        st.subheader("💬 Team Chat")
        sender = st.text_input("Nama", value="Engineer", key="field_chat_name")
        
        if not messages.empty:
            global_msgs = messages[messages['site_id'] == 'GLOBAL'] if 'site_id' in messages.columns else pd.DataFrame()
            for _, msg in global_msgs.tail(20).iterrows():
                with st.chat_message("user"):
                    st.caption(f"**{msg.get('sender','?')}** · {msg.get('created_at','')}")
                    st.write(msg.get('message',''))
        
        with st.form("field_chat", clear_on_submit=True):
            msg = st.text_input("Pesan...", key="field_chat_input", placeholder="Ketik pesan...")
            if st.form_submit_button("📤 Kirim"):
                if msg:
                    insert_row("chat_messages", {'id': generate_id(), 'site_id': 'GLOBAL', 'sender': sender, 'message': msg, 'created_at': now_str()})
                    st.rerun()
    
    # ===== TAB 3: DAILY TASKS =====
    with tab3:
        st.subheader("📋 Daily Tasks")
        today = date.today()
        week_end = today + timedelta(days=7)
        follow_up = ms_df[(ms_df['status'].isin(['PENDING','ONGOING','DELAYED'])) & (ms_df['planned_end'].dt.date <= week_end)]
        
        if follow_up.empty:
            st.success("✅ Tidak ada task minggu ini!")
        else:
            for _, task in follow_up.iterrows():
                d = (task['planned_end'].date() - today).days
                icon = '🔴' if d < 0 else ('🟡' if d == 0 else '🟢')
                site_code = site_map.get(task['project_id'], '-') if 'site_map' in dir() else '-'
                st.markdown(f"{icon} **{task['name']}** — {site_code} — {task['planned_end'].strftime('%d %b %Y')} ({d} hari)")
                st.markdown("---")

if __name__ == "__main__":
    field_app_page()
