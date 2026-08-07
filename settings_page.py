import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_db import read_sheet, insert_row, update_row, generate_id

def settings_page():
    st.title("⚙️ Settings")
    
    # Load settings
    settings_df = read_sheet("settings")
    if settings_df.empty:
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
    
    # ===== TAB 1: TELEGRAM =====
    with tab1:
        st.subheader("Telegram Bot Configuration")
        st.info("Bot akan mengirim report otomatis ke Telegram Group.")
        
        with st.form("telegram_settings"):
            bot_token = st.text_input("Bot Token", value=str(settings.get("telegram_bot_token", "")),
                                     placeholder="7654321:AAHxJqK...", type="password")
            chat_id = st.text_area("Chat ID (grup/individu)", 
                       value=str(settings.get("telegram_chat_id", "")),
                       placeholder="-123456789 (grup) atau 123456789 (individu)\nPisahkan dengan koma untuk banyak penerima\nContoh: -123456789, 987654321, 11223344",
                       height=80)
            st.caption("💡 Cara dapat Chat ID: chat ke @getidsbot di Telegram")
            
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
                                
                                total = len(sites_df)
                                if not sites_df.empty and 'progress' in sites_df.columns:
                                    sites_df['progress'] = pd.to_numeric(sites_df['progress'], errors='coerce').fillna(0)
                                    avg_prog = sites_df['progress'].mean()
                                else:
                                    avg_prog = 0
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
                                
                                # Kirim ke semua Chat ID
                                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                                chat_ids = [cid.strip() for cid in chat_id.split(',') if cid.strip()]
                                success = 0
                                failed = 0
                                for cid in chat_ids:
                                    res = requests.post(url, data={"chat_id": cid, "text": report, "parse_mode": "Markdown"})
                                    if res.status_code == 200:
                                        success += 1
                                    else:
                                        failed += 1
                                
                                if success > 0:
                                    st.success(f"✅ Text summary sent to {success} recipient(s)!")
                                if failed > 0:
                                    st.error(f"❌ Failed to send to {failed} recipient(s)")
            
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
                                        
                                        # Kirim ke semua Chat ID
                                        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
                                        chat_ids = [cid.strip() for cid in chat_id.split(',') if cid.strip()]
                                        success = 0
                                        failed = 0
                                        
                                        with open(tmp.name, 'rb') as f:
                                            for cid in chat_ids:
                                                files = {'document': ('Daily_Report.pdf', f, 'application/pdf')}
                                                data = {'chat_id': cid, 'caption': f'📊 PM System Daily Report\n📅 {datetime.now().strftime("%d %b %Y")}'}
                                                res = requests.post(url, data=data, files=files)
                                                if res.status_code == 200:
                                                    success += 1
                                                else:
                                                    failed += 1
                                        
                                        if success > 0:
                                            st.success(f"✅ PDF Report sent to {success} recipient(s)!")
                                        if failed > 0:
                                            st.error(f"❌ Failed to send to {failed} recipient(s)")
    
    # ===== TAB 2: REPORT CONFIG =====
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
        st.subheader("📋 Preview Report Format")
        
        preview = """📊 PM System Daily Report
📅 09 May 2026

━━━━━━━━━━━━━━━━━
📈 Progress Summary
• Total Site: 5
• Avg Progress: 67.5%
• On Track: 3 | Delayed: 2

━━━━━━━━━━━━━━━━━
🔴 Critical Alerts
• SITE-002: Progress 25%
• Material: Besi Beton stok 30

━━━━━━━━━━━━━━━━━
🤖 AI Insights
• Health Score: 60%
• Forecast: 15 Jul 2026

━━━━━━━━━━━━━━━━━
📱 Powered by PM System"""
        
        st.code(preview, language=None)

if __name__ == "__main__":
    settings_page()
