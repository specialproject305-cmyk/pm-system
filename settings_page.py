import streamlit as st
import pandas as pd
from supabase_db import read_sheet, insert_row, update_row, generate_id

def settings_page():
    st.title("⚙️ Settings")
    
    # Load settings
    settings_df = read_sheet("settings")
    if settings_df.empty:
        # Insert default
        insert_row("settings", {
            "id": "settings_1",
            "telegram_bot_token": "",
            "telegram_chat_id": "",
            "report_time": "16:00",
            "enable_auto_report": "false"
        })
        settings_df = read_sheet("settings")
    
    settings = settings_df.iloc[0] if not settings_df.empty else {}
    
    tab1, tab2 = st.tabs(["🔔 Telegram Bot", "📊 Report Config"])
    
    with tab1:
        st.subheader("Telegram Bot Configuration")
        st.info("Bot akan mengirim report otomatis ke Telegram Group.")
        
        with st.form("telegram_settings"):
            bot_token = st.text_input("Bot Token", value=str(settings.get("telegram_bot_token", "")),
                                     placeholder="7654321:AAHxJqK...", type="password")
            chat_id = st.text_input("Chat ID Group", value=str(settings.get("telegram_chat_id", "")),
                                   placeholder="-123456789")
            
            if st.form_submit_button("💾 Save Telegram Settings", type="primary"):
                update_row("settings", "settings_1", {
                    "telegram_bot_token": bot_token,
                    "telegram_chat_id": chat_id
                })
                st.success("✅ Telegram settings saved!")
                st.rerun()
        
        # Test button
        if bot_token and chat_id:
            if st.button("🧪 Test Send Message"):
                import requests
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                data = {"chat_id": chat_id, "text": "✅ PM System: Test message berhasil!\n\nReport otomatis akan dikirim setiap hari pukul 16:00."}
                try:
                    res = requests.post(url, data=data)
                    if res.status_code == 200:
                        st.success("✅ Test message sent! Cek Telegram Group.")
                    else:
                        st.error(f"❌ Failed: {res.text}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with tab2:
        st.subheader("Report Configuration")
        
        with st.form("report_settings"):
            report_time = st.text_input("Jam Kirim Report (24H)", 
                                       value=str(settings.get("report_time", "16:00")),
                                       placeholder="16:00",
                                       help="Format: HH:MM (contoh: 16:00)")
            enable = st.checkbox("Enable Auto Report", 
                                value=str(settings.get("enable_auto_report", "false")).lower() == "true")
            
            if st.form_submit_button("💾 Save Report Config", type="primary"):
                update_row("settings", "settings_1", {
                    "report_time": report_time,
                    "enable_auto_report": str(enable).lower()
                })
                st.success("✅ Report config saved!")
                st.rerun()
        
        st.markdown("---")
        st.subheader("📋 Preview Report")
        st.caption("Ini contoh report yang akan dikirim:")
        
        # Preview
        preview = """
        📊 *PM System Daily Report*
        📅 09 May 2026
        
        ━━━━━━━━━━━━━━━━━
        📈 *Progress Summary*
        • Total Site: 5
        • Avg Progress: 67.5%
        • On Track: 3 | Delayed: 2
        
        ━━━━━━━━━━━━━━━━━
        🔴 *Critical Alerts*
        • SITE-002: Progress 25% (CRITICAL)
        • Material: Besi Beton stok 30 (min 100)
        
        ━━━━━━━━━━━━━━━━━
        🤖 *AI Insights*
        • Health Score: 60%
        • Forecast Completion: 15 Jul 2026
        • Top Delay: Material Terlambat
        
        ━━━━━━━━━━━━━━━━━
        📱 Powered by PM System
        """
        st.markdown(preview)

if __name__ == "__main__":
    settings_page()
