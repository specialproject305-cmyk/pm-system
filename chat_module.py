import streamlit as st
import pandas as pd
from supabase_db import read_all_sheets, insert_row, generate_id, now_str

def chat_notif_page():
    st.title("💬 Diskusi & Notifikasi")
    
    all_data = read_all_sheets()
    messages = all_data.get('chat_messages', pd.DataFrame())
    notifs = all_data.get('notifications', pd.DataFrame())
    
    # Hitung unread
    unread = len(notifs[notifs['is_read'] == '0']) if not notifs.empty and 'is_read' in notifs.columns else 0
    
    # Floating Notification Bell
    st.markdown(f"""
    <style>
        .notif-container {{
            position: fixed;
            top: 15px;
            right: 20px;
            z-index: 9999;
        }}
        .notif-bell {{
            font-size: 28px;
            cursor: pointer;
            animation: {'ring' if unread > 0 else 'none'} 1s ease-in-out infinite;
            text-decoration: none;
        }}
        @keyframes ring {{
            0% {{ transform: rotate(0); }}
            10% {{ transform: rotate(15deg); }}
            20% {{ transform: rotate(-15deg); }}
            30% {{ transform: rotate(10deg); }}
            40% {{ transform: rotate(-10deg); }}
            50% {{ transform: rotate(0); }}
            100% {{ transform: rotate(0); }}
        }}
        .notif-badge {{
            position: absolute;
            top: -8px;
            right: -8px;
            background: #dc3545;
            color: white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            font-size: 11px;
            text-align: center;
            line-height: 20px;
            font-weight: bold;
            display: {'block' if unread > 0 else 'none'};
        }}
        .notif-toast {{
            position: fixed;
            top: 60px;
            right: 20px;
            z-index: 9998;
            background: white;
            border-left: 4px solid #dc3545;
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            max-width: 300px;
            font-size: 13px;
            animation: slideIn 0.3s ease;
        }}
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        /* Mobile responsive */
        @media (max-width: 768px) {{
            .notif-container {{
                top: 10px;
                right: 10px;
            }}
            .notif-bell {{
                font-size: 24px;
            }}
            .notif-toast {{
                top: 50px;
                right: 10px;
                max-width: 250px;
                font-size: 11px;
            }}
        }}
    </style>
    
    <div class="notif-container">
        <span class="notif-bell" title="Notifikasi">🔔</span>
        <span class="notif-badge">{unread}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Tampilkan toast notifikasi terbaru
    if unread > 0 and not notifs.empty:
        latest = notifs[notifs['is_read'] == '0'].iloc[-1] if len(notifs[notifs['is_read'] == '0']) > 0 else None
        if latest is not None:
            icon = '⚠️' if latest.get('type') == 'MILESTONE_DELAY' else '🔴' if latest.get('type') == 'MATERIAL_CRITICAL' else 'ℹ️'
            st.markdown(f"""
            <div class="notif-toast">
                {icon} <b>{latest.get('title', '')}</b><br>
                <span style="font-size:11px;">{latest.get('message', '')}</span>
            </div>
            """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["💬 Chat Rooms", "🔔 Notifications"])
    
    with tab1:
        st.subheader("🌍 Global Discussion Room")
        
        sender = st.text_input("Nama Kamu", value="PM", key="chat_sender")
        
        if not messages.empty:
            global_msgs = messages[messages['site_id'] == 'GLOBAL'] if 'site_id' in messages.columns else messages
            for _, msg in global_msgs.tail(30).iterrows():
                with st.chat_message("user"):
                    st.caption(f"**{msg.get('sender','?')}** · {msg.get('created_at','')}")
                    st.write(msg.get('message',''))
        else:
            st.info("💬 Belum ada pesan. Mulai diskusi!")
        
        with st.form("send_chat", clear_on_submit=True):
            msg = st.text_input("Ketik pesan...", key="chat_input", placeholder="Tulis lalu Enter...")
            if st.form_submit_button("📤 Kirim"):
                if msg:
                    insert_row("chat_messages", {
                        'id': generate_id(), 'site_id': 'GLOBAL',
                        'sender': sender, 'message': msg, 'created_at': now_str()
                    })
                    st.rerun()
    
    with tab2:
        st.subheader("🔔 Notification Center")
        
        if not notifs.empty:
            st.metric("📬 Belum Dibaca", unread)
            
            if unread > 0:
                if st.button("✅ Tandai Semua Dibaca"):
                    # Update via Supabase
                    pass
            
            for _, n in notifs.tail(20).iterrows():
                is_unread = n.get('is_read') == '0'
                bg = '#fff3cd' if is_unread else 'transparent'
                icon = '⚠️' if n.get('type') == 'MILESTONE_DELAY' else '🔴' if n.get('type') == 'MATERIAL_CRITICAL' else 'ℹ️'
                
                st.markdown(f"""
                <div style="background:{bg}; padding:8px; border-radius:8px; margin:5px 0;">
                    {icon} <b>{n.get('title','')}</b><br>
                    <span style="font-size:12px;">{n.get('message','')}</span><br>
                    <span style="font-size:10px; color:gray;">🕐 {n.get('created_at','')}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ Tidak ada notifikasi.")

if __name__ == "__main__":
    chat_notif_page()
