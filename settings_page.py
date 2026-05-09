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
        
                # Test send
        if bot_token and chat_id:
            st.markdown("---")
            st.subheader("🧪 Test Send")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📝 Send Text Summary", use_container_width=True):
                    import requests
                    from supabase_db import read_all_sheets
                    
                    all_data = read_all_sheets()
                    sites_df = all_data.get('projects', pd.DataFrame())
                    mat_df = all_data.get('materials', pd.DataFrame())
                    ms_df = all_data.get('milestones', pd.DataFrame())
                    
                    total = len(sites_df)
                    avg_prog = sites_df['progress'].mean() if not sites_df.empty else 0
                    on_track = len(sites_df[sites_df['status']=='ON_TRACK']) if not sites_df.empty else 0
                    delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])]) if not sites_df.empty else 0
                    
                    report = f"""📊 *PM System Daily Report*
        📅 {datetime.now().strftime('%d %b %Y')}

        ━━━━━━━━━━━━━━━━━
        📈 *Progress Summary*
        • Total Site: {total}
        • Avg Progress: {avg_prog:.1f}%
        • On Track: {on_track} | Delayed: {delayed}

        ━━━━━━━━━━━━━━━━━
        🔴 *Critical Alerts*"""
                    
                    if not sites_df.empty:
                        for _, s in sites_df[sites_df['status']=='CRITICAL'].head(3).iterrows():
                            report += f"\n• {s['site_id']}: {s.get('progress',0):.0f}%"
                    
                    if not mat_df.empty:
                        mat_df['current_stock'] = pd.to_numeric(mat_df['current_stock'], errors='coerce').fillna(0)
                        mat_df['min_stock'] = pd.to_numeric(mat_df['min_stock'], errors='coerce').fillna(0)
                        critical = mat_df[mat_df['current_stock'] < mat_df['min_stock']]
                        for _, m in critical.head(3).iterrows():
                            report += f"\n• {m['name']}: Stok {m['current_stock']:.0f} (min {m['min_stock']:.0f})"
                    
                    report += f"""

        ━━━━━━━━━━━━━━━━━
        🤖 *AI Insights*
        • Health Score: {round(on_track/total*100) if total>0 else 0}%
        • Forecast: {(datetime.now() + pd.Timedelta(days=int((100-avg_prog)*2))).strftime('%d %b %Y') if avg_prog<100 else 'On Schedule'}

        ━━━━━━━━━━━━━━━━━
        📱 Powered by PM System"""
                    
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    res = requests.post(url, data={"chat_id": chat_id, "text": report, "parse_mode": "Markdown"})
                    if res.status_code == 200:
                        st.success("✅ Text summary sent!")
                    else:
                        st.error(f"❌ {res.text}")
            
            with col2:
                if st.button("📄 Send PDF Report", use_container_width=True):
                    import requests
                    import tempfile
                    from report_generator import generate_daily_report
                    from supabase_db import read_all_sheets
                    
                    with st.spinner("Generating PDF..."):
                        all_data = read_all_sheets()
                        pdf = generate_daily_report(all_data)
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                            pdf.output(tmp.name)
                            
                            url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
                            with open(tmp.name, 'rb') as f:
                                files = {'document': ('Daily_Report.pdf', f, 'application/pdf')}
                                data = {'chat_id': chat_id, 'caption': f'📊 PM System Daily Report\n📅 {datetime.now().strftime("%d %b %Y")}'}
                                res = requests.post(url, data=data, files=files)
                            
                            if res.status_code == 200:
                                st.success("✅ PDF Report sent to Telegram!")
                            else:
                                st.error(f"❌ {res.text}")

if __name__ == "__main__":
    settings_page()
