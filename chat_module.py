import streamlit as st
import pandas as pd
from gsheets_db import read_sheet, insert_row, generate_id, now_str

def check_notifications():
    ms_df = read_sheet("milestones")
    mat_df = read_sheet("materials")
    sites_df = read_sheet("projects")
    
    if not ms_df.empty:
        delayed = ms_df[(ms_df['status'] == 'DELAYED')]
        for _, d in delayed.iterrows():
            insert_row("notifications", {
                'id': generate_id(), 'type': 'MILESTONE_DELAY',
                'title': f"⚠️ {d.get('name','MS')} terlambat",
                'message': f"Milestone '{d.get('name','')}' di site terlambat",
                'site_id': d.get('project_id',''), 'is_read': '0', 'created_at': now_str()
            })
    
    if not mat_df.empty:
        for col in ['current_stock', 'min_stock']:
            if col in mat_df.columns:
                mat_df[col] = pd.to_numeric(mat_df[col], errors='coerce').fillna(0)
        critical = mat_df[mat_df['current_stock'] < mat_df['min_stock']]
        for _, c in critical.iterrows():
            insert_row("notifications", {
                'id': generate_id(), 'type': 'MATERIAL_CRITICAL',
                'title': f"🔴 {c.get('name','Material')} kritis",
                'message': f"Stok {c.get('name','')}: {c.get('current_stock',0)} (min: {c.get('min_stock',0)})",
                'site_id': '', 'is_read': '0', 'created_at': now_str()
            })

def chat_notif_page():
    st.title("💬 Diskusi & Notifikasi")
    
    tab1, tab2 = st.tabs(["💬 Chat Rooms", "🔔 Notifications"])
    
    with tab1:
        st.subheader("🌍 Global Discussion Room")
        
        messages = read_sheet("chat_messages")
        sender = st.text_input("Nama Kamu", value="PM", key="chat_sender")
        
        # Display messages
        if not messages.empty:
            global_msgs = messages[messages['site_id'] == 'GLOBAL']
            for _, msg in global_msgs.tail(30).iterrows():
                with st.chat_message("user"):
                    st.caption(f"**{msg.get('sender','?')}** · {msg.get('created_at','')}")
                    st.write(msg.get('message',''))
        
        # Send message
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
        check_notifications()
        
        notifs = read_sheet("notifications")
        if not notifs.empty:
            unread = notifs[notifs['is_read'] == '0'] if 'is_read' in notifs.columns else pd.DataFrame()
            st.metric("📬 Belum Dibaca", len(unread))
            
            for _, n in notifs.tail(20).iterrows():
                icon = '⚠️' if n.get('type') == 'MILESTONE_DELAY' else '🔴'
                st.markdown(f"{icon} **{n.get('title','')}**")
                st.caption(n.get('message',''))
                st.caption(f"🕐 {n.get('created_at','')}")
                st.markdown("---")
        else:
            st.success("✅ Tidak ada notifikasi.")

if __name__ == "__main__":
    chat_notif_page()