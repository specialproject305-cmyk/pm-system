import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from supabase_db import read_sheet, update_row, read_all_sheets, insert_row, generate_id, now_str, delete_row_by_id

def field_app_page():
    st.title("📱 Field App")
    
    all_data = read_all_sheets()
    ms_df = all_data.get('milestones', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    master_df = all_data.get('master_projects', pd.DataFrame())
    messages = all_data.get('chat_messages', pd.DataFrame())
    
    # Global filter
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid_sites = sites_df[sites_df.get('master_project_id', '') == st.session_state.global_project_filter]['id'].tolist()
        sites_df = sites_df[sites_df['id'].isin(valid_sites)]
        ms_df = ms_df[ms_df['project_id'].isin(valid_sites)] if not ms_df.empty else ms_df
    
    # Sidebar
    with st.sidebar:
        # User info & Logout
        user = st.session_state.get('user', {})
        st.markdown(f"👷 **{user.get('full_name', 'Engineer')}**")
        
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state['logged_in'] = False
            st.rerun()
        
        st.divider()
        st.header("⚙️ Filter")
        
        # Filter Project
        if not master_df.empty:
            master_options = ["ALL"] + master_df['id'].tolist()
            selected_master = st.selectbox("🏢 Project:", master_options,
                format_func=lambda x: "🌐 SEMUA" if x == "ALL" 
                else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}")
            if selected_master != "ALL":
                valid_sites2 = sites_df[sites_df['master_project_id'] == selected_master]['id'].tolist()
                ms_df = ms_df[ms_df['project_id'].isin(valid_sites2)]
        
        # Filter PIC
        pic_list = sorted(ms_df['assigned_to'].dropna().unique().tolist()) if 'assigned_to' in ms_df.columns else []
        if pic_list:
            selected_pic = st.selectbox("👷 PIC:", pic_list)
            ms_df = ms_df[ms_df['assigned_to'] == selected_pic]
        else:
            selected_pic = "User"
        
        st.divider()
        st.metric("📋 Tasks", len(ms_df))
    # ===== TAB 1: UPDATE TASKS =====
    with tab1:
        if ms_df.empty:
            st.info("📋 Belum ada task.")
        else:
            site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
            site_name_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
            ms_df['site_code'] = ms_df['project_id'].map(site_map).fillna('-')
            ms_df['site_name'] = ms_df['project_id'].map(site_name_map).fillna('-')
            ms_df['deadline'] = ms_df['planned_end'].dt.strftime('%d %b %Y')
            ms_df['days_left'] = (ms_df['planned_end'].dt.date - date.today()).apply(lambda x: x.days if pd.notna(x) else 999)
            
            st.metric("📋 Tasks", len(ms_df))
            
            for _, task in ms_df.iterrows():
                days = task['days_left']
                if days < 0:
                    bg = '#FEE2E2'; border = '#EF4444'
                elif days == 0:
                    bg = '#FEF3C7'; border = '#F59E0B'
                elif task['status'] == 'DONE':
                    bg = '#DCFCE7'; border = '#10B981'
                else:
                    bg = '#F0FDF4'; border = '#10B981'
                
                st.markdown(f"""
                <div style='background:{bg}; padding:10px; border-radius:8px; margin:5px 0; border-left:4px solid {border};'>
                    <strong>{task['name']}</strong><br>
                    📍 {task['site_code']} - {task['site_name']}<br>
                    📅 {task['deadline']} | ⏰ {days} hari | {task['status']}
                </div>
                """, unsafe_allow_html=True)
                
                with st.form(f"update_{task['id']}", clear_on_submit=False):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        new_status = st.selectbox("Status", ['PENDING','ONGOING','DONE','DELAYED'],
                            index=['PENDING','ONGOING','DONE','DELAYED'].index(task['status']),
                            key=f"st_{task['id']}")
                    with c2:
                        as_d = pd.to_datetime(task.get('actual_start')).date() if pd.notna(task.get('actual_start')) else None
                        new_as = st.date_input("Actual Start", value=as_d, key=f"as_{task['id']}")
                    with c3:
                        ae_d = pd.to_datetime(task.get('actual_end')).date() if pd.notna(task.get('actual_end')) else None
                        new_ae = st.date_input("Actual End", value=ae_d, key=f"ae_{task['id']}")
                    
                    if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                        update_data = {'status': new_status}
                        if new_as: update_data['actual_start'] = new_as.strftime('%Y-%m-%d')
                        if new_ae or new_status == 'DONE':
                            update_data['actual_end'] = (new_ae or date.today()).strftime('%Y-%m-%d')
                        update_row('milestones', task['id'], update_data)
                        st.success(f"✅ {task['name']} diupdate!")
                        st.toast(f"✅ {task['name']} → {new_status}", icon="🎉")
                        st.rerun()
                st.markdown("---")
    
    # ===== TAB 2: CHAT =====
    with tab2:
        st.subheader("💬 Team Chat")
        
        sender = st.text_input("Nama", value=selected_pic if selected_pic != "User" else "Engineer", key="chat_name")
        
        if not messages.empty:
            global_msgs = messages[messages['site_id'] == 'GLOBAL'] if 'site_id' in messages.columns else pd.DataFrame()
            for _, msg in global_msgs.tail(20).iterrows():
                with st.chat_message("user"):
                    st.caption(f"**{msg.get('sender','?')}** · {msg.get('created_at','')}")
                    st.write(msg.get('message',''))
        
        with st.form("send_chat", clear_on_submit=True):
            msg = st.text_input("Pesan...", key="chat_input", placeholder="Ketik pesan...")
            if st.form_submit_button("📤 Kirim"):
                if msg:
                    insert_row("chat_messages", {
                        'id': generate_id(), 'site_id': 'GLOBAL',
                        'sender': sender, 'message': msg, 'created_at': now_str()
                    })
                    st.rerun()
    
    # ===== TAB 3: DAILY TASKS =====
    with tab3:
        st.subheader("📋 Daily Tasks")
        
        today = date.today()
        week_end = today + timedelta(days=7)
        
        follow_up = ms_df[
            (ms_df['status'].isin(['PENDING', 'ONGOING', 'DELAYED'])) &
            (ms_df['planned_end'].dt.date <= week_end)
        ].copy()
        
        if follow_up.empty:
            st.success("✅ Tidak ada task minggu ini!")
        else:
            follow_up['days_left'] = (follow_up['planned_end'].dt.date - today).apply(lambda x: x.days if pd.notna(x) else 999)
            
            for _, task in follow_up.iterrows():
                d = task['days_left']
                icon = '🔴' if d < 0 else ('🟡' if d == 0 else '🟢')
                site_code = site_map.get(task['project_id'], '-')
                st.markdown(f"{icon} **{task['name']}** — {site_code} — {task['deadline']} ({d} hari)")
                st.markdown("---")

if __name__ == "__main__":
    field_app_page()
