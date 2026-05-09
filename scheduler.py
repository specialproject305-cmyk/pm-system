import requests
import tempfile
import pandas as pd
from datetime import datetime, timedelta
from supabase_db import read_all_sheets, read_sheet
from report_generator import generate_daily_report

def send_scheduled_report():
    settings_df = read_sheet("settings")
    if settings_df.empty:
        return "No settings"
    
    s = settings_df.iloc[0]
    bot_token = s.get("telegram_bot_token","")
    chat_id = s.get("telegram_chat_id","")
    
    if not bot_token or not chat_id:
        return "Missing config"
    
    all_data = read_all_sheets()
    
    # 1. KIRIM PDF
    pdf = generate_daily_report(all_data)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf.output(tmp.name)
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        with open(tmp.name, 'rb') as f:
            requests.post(url, data={'chat_id': chat_id, 'caption': f'📊 PM System Daily Report\n📅 {datetime.now().strftime("%d %b %Y")}'}, files={'document': f})
    
    # 2. KIRIM TEXT SUMMARY
    sites_df = all_data.get('projects', pd.DataFrame())
    mat_df = all_data.get('materials', pd.DataFrame())
    
    total = len(sites_df)
    avg_prog = sites_df['progress'].mean() if not sites_df.empty else 0
    on_track = len(sites_df[sites_df['status']=='ON_TRACK']) if not sites_df.empty else 0
    delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])]) if not sites_df.empty else 0
    
    text = f"""🔔 *PM System Daily Report*
📅 {datetime.now().strftime('%d %b %Y %H:%M')}

📈 *Summary*
• Sites: {total} | On Track: {on_track} | Delayed: {delayed}
• Avg Progress: {avg_prog:.1f}%
• Health: {round(on_track/total*100) if total>0 else 0}%"""
    
    if not mat_df.empty:
        mat_df['current_stock'] = pd.to_numeric(mat_df['current_stock'], errors='coerce').fillna(0)
        mat_df['min_stock'] = pd.to_numeric(mat_df['min_stock'], errors='coerce').fillna(0)
        crit = mat_df[mat_df['current_stock'] < mat_df['min_stock']]
        if not crit.empty:
            text += f"\n\n🔴 *Critical Materials*: {len(crit)}"
    
    url2 = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url2, data={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    
    return "OK - PDF + Summary sent"

if __name__ == "__main__":
    print(send_scheduled_report())
