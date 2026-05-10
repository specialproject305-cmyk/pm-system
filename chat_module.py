import streamlit as st
import pandas as pd
from supabase_db import read_all_sheets, insert_row, generate_id, now_str, delete_row_by_id

def chat_notif_page():
    st.title("💬 Diskusi & Notifikasi")
    
    all_data = read_all_sheets()
    messages = all_data.get('chat_messages', pd.DataFrame())
    notifs = all_data.get('notifications', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    
    unread = len(notifs[notifs['is_read'] == '0']) if not notifs.empty and 'is_read' in notifs.columns else 0
    
    # Floating bell
    st.markdown(f"""
    <style>
        .notif-container {{ position: fixed; top: 15px; right: 20px; z-index: 9999; }}
        .notif-bell {{ font-size: 28px; cursor: pointer; animation: {'ring' if unread > 0 else 'none'} 1s ease-in-out infinite; }}
        @keyframes ring {{ 0% {{ transform: rotate(0); }} 10% {{ transform: rotate(15deg); }} 20% {{ transform: rotate(-15deg); }} 30% {{ transform: rotate(10deg); }} 40% {{ transform: rotate(-10deg); }} 50% {{ transform: rotate(0); }} 100% {{ transform: rotate(0); }} }}
        .notif-badge {{ position: absolute; top: -8px; right: -8px; background: #dc3545; color: white; border-radius: 50%; width: 20px; height: 20px; font-size: 11px; text-align: center; line-height: 20px; font-weight: bold; display: {'block' if unread > 0 else 'none'}; }}
    </style>
    <div class="notif-container"><span class="notif-bell">🔔</span><span class="notif-badge">{unread}</span></div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🌍 Global", "📁 Site Chat", "🔔 Notifications"])
    
    # ===== TAB 1: GLOBAL =====
    with tab1:
        st.subheader("🌍 Global Discussion Room")
        sender = st.text_input("Nama Kamu", value="PM", key="global_sender")
        
        if not messages.empty:
            global_msgs = messages[messages['site_id'] == 'GLOBAL'] if 'site_id' in messages.columns else pd.DataFrame()
            for _, msg in global_msgs.tail(30).iterrows():
                with st.chat_message("user"):
                    c1, c2 = st.columns([15, 1])
                    with c1:
                        st.caption(f"**{msg.get('sender','?')}** · {msg.get('created_at','')}")
                        st.write(msg.get('message',''))
                    with c2:
                        if st.button("🗑️", key=f"del_g_{msg.get('id','')}", help="Hapus"):
                            delete_row_by_id('chat_messages', msg.get('id',''))
                            st.rerun()
        
        with st.form("send_global", clear_on_submit=True):
            msg = st.text_input("Pesan...", key="global_input", placeholder="Ketik lalu Enter...")
            if st.form_submit_button("📤 Kirim"):
                if msg:
                    insert_row("chat_messages", {'id': generate_id(), 'site_id': 'GLOBAL', 'sender': sender, 'message': msg, 'created_at': now_str()})
                    st.rerun()
    
    # ===== TAB 2: SITE CHAT =====
    with tab2:
        st.subheader("📁 Site Discussion")
        
        if sites_df.empty:
            st.warning("⚠️ Belum ada site.")
        else:
            site_options = ["ALL SITE"] + sites_df["id"].tolist()
            selected_site = st.selectbox("Pilih Site:", site_options,
                format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE" 
                else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
            
            sender2 = st.text_input("Nama Kamu", value="PM", key="site_sender")
            
            if not messages.empty:
                if selected_site == "ALL SITE":
                    site_msgs = messages[messages['site_id'] != 'GLOBAL']
                else:
                    site_msgs = messages[messages['site_id'] == selected_site]
                
                if not site_msgs.empty:
                    for _, msg in site_msgs.tail(30).iterrows():
                        # Cari site name
                        sname = sites_df[sites_df['id']==msg.get('site_id','')]['site_id'].values[0] if not sites_df.empty and msg.get('site_id','') != '' else ''
                        with st.chat_message("user"):
                            c1, c2 = st.columns([15, 1])
                            with c1:
                                if sname: st.caption(f"📁 {sname}")
                                st.caption(f"**{msg.get('sender','?')}** · {msg.get('created_at','')}")
                                st.write(msg.get('message',''))
                            with c2:
                                if st.button("🗑️", key=f"del_s_{msg.get('id','')}", help="Hapus"):
                                    delete_row_by_id('chat_messages', msg.get('id',''))
                                    st.rerun()
                else:
                    st.info("Belum ada pesan.")
            
            if selected_site != "ALL SITE":
                with st.form("send_site", clear_on_submit=True):
                    msg = st.text_input("Pesan...", key="site_input", placeholder=f"Ketik pesan untuk site ini...")
                    if st.form_submit_button("📤 Kirim ke Site"):
                        if msg:
                            insert_row("chat_messages", {'id': generate_id(), 'site_id': selected_site, 'sender': sender2, 'message': msg, 'created_at': now_str()})
                            st.rerun()
    
    # ===== TAB 3: NOTIF =====
    with tab3:
        st.subheader("🔔 Notifications")
        if not notifs.empty:
            st.metric("📬 Unread", unread)
            for _, n in notifs.tail(20).iterrows():
                bg = '#fff3cd' if n.get('is_read') == '0' else 'transparent'
                icon = '⚠️' if n.get('type') == 'MILESTONE_DELAY' else '🔴' if n.get('type') == 'MATERIAL_CRITICAL' else 'ℹ️'
                st.markdown(f"<div style='background:{bg};padding:8px;border-radius:8px;margin:5px 0;'>{icon} <b>{n.get('title','')}</b><br><span style='font-size:12px;'>{n.get('message','')}</span></div>", unsafe_allow_html=True)
        else:
            st.success("✅ No notifications.")

if __name__ == "__main__":
    chat_notif_page()
