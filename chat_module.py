import streamlit as st
import pandas as pd
from supabase_db import read_all_sheets, insert_row, generate_id, now_str

def chat_notif_page():
    st.title("💬 Diskusi & Notifikasi")
    
    tab1, tab2 = st.tabs(["💬 Chat Rooms", "🔔 Notifications"])
    
    all_data = read_all_sheets()
    messages = all_data.get('chat_messages', pd.DataFrame())
    notifs = all_data.get('notifications', pd.DataFrame())
    
    with tab1:
        st.subheader("🌍 Global Discussion Room")
        
        sender = st.text_input("Nama Kamu", value="PM", key="chat_sender")
        
        # Tampilkan pesan
        if not messages.empty:
            global_msgs = messages[messages['site_id'] == 'GLOBAL'] if 'site_id' in messages.columns else messages
            for _, msg in global_msgs.tail(30).iterrows():
                with st.chat_message("user"):
                    st.caption(f"**{msg.get('sender','?')}** · {msg.get('created_at','')}")
                    st.write(msg.get('message',''))
        else:
            st.info("💬 Belum ada pesan. Mulai diskusi!")
        
        # Kirim pesan
        with st.form("send_chat", clear_on_submit=True):
            msg = st.text_input("Ketik pesan...", key="chat_input")
            if st.form_submit_button("📤 Kirim"):
                if msg:
                    insert_row("chat_messages", {
                        'id': generate_id(), 'site_id': 'GLOBAL',
                        'sender': sender, 'message': msg, 'created_at': now_str()
                    })
                    st.rerun()
    
    with tab2:
        st.subheader("🔔 Notifications")
        
        if not notifs.empty:
            unread = notifs[notifs['is_read'] == '0'] if 'is_read' in notifs.columns else pd.DataFrame()
            st.metric("📬 Belum Dibaca", len(unread))
            
            for _, n in notifs.tail(20).iterrows():
                icon = '⚠️' if n.get('type') == 'MILESTONE_DELAY' else '🔴' if n.get('type') == 'MATERIAL_CRITICAL' else 'ℹ️'
                st.markdown(f"{icon} **{n.get('title','')}**")
                st.caption(n.get('message',''))
                st.caption(f"🕐 {n.get('created_at','')}")
                st.markdown("---")
        else:
            st.success("✅ Tidak ada notifikasi.")

if __name__ == "__main__":
    chat_notif_page()
