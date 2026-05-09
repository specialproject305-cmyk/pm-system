import requests
from supabase_db import read_sheet, read_all_sheets
from datetime import datetime

def send_daily_report():
    settings = read_sheet("settings").iloc[0]
    
    if str(settings.get("enable_auto_report","false")).lower() != "true":
        return
    
    bot_token = settings.get("telegram_bot_token","")
    chat_id = settings.get("telegram_chat_id","")
    
    if not bot_token or not chat_id:
        return
    
    all_data = read_all_sheets()
    sites_df = all_data.get("projects", pd.DataFrame())
    ms_df = all_data.get("milestones", pd.DataFrame())
    mat_df = all_data.get("materials", pd.DataFrame())
    
    total = len(sites_df)
    avg_prog = sites_df["progress"].mean() if not sites_df.empty else 0
    on_track = len(sites_df[sites_df["status"]=="ON_TRACK"])
    delayed = len(sites_df[sites_df["status"].isin(["DELAYED","CRITICAL"])])
    
    report = f"""📊 *PM System Daily Report*
📅 {datetime.now().strftime('%d %b %Y %H:%M')}

━━━━━━━━━━━━━━━━━
📈 *Progress Summary*
• Total Site: {total}
• Avg Progress: {avg_prog:.1f}%
• On Track: {on_track} | Delayed: {delayed}

━━━━━━━━━━━━━━━━━
🔴 *Critical Alerts*"""

    if not sites_df.empty:
        for _, s in sites_df[sites_df["status"]=="CRITICAL"].head(3).iterrows():
            report += f"\n• {s['site_id']}: {s.get('progress',0)}%"
    
    if not mat_df.empty:
        mat_df["current_stock"] = pd.to_numeric(mat_df["current_stock"],errors="coerce").fillna(0)
        mat_df["min_stock"] = pd.to_numeric(mat_df["min_stock"],errors="coerce").fillna(0)
        critical = mat_df[mat_df["current_stock"] < mat_df["min_stock"]]
        for _, m in critical.head(3).iterrows():
            report += f"\n• Material: {m['name']} stok {m['current_stock']} (min {m['min_stock']})"
    
    report += f"""

━━━━━━━━━━━━━━━━━
🤖 *AI Insights*
• Health Score: {round(on_track/total*100) if total>0 else 0}%
• Forecast: {(datetime.now() + pd.Timedelta(days=int((100-avg_prog)*2))).strftime('%d %b %Y') if avg_prog<100 else 'On Schedule'}

━━━━━━━━━━━━━━━━━
📱 Powered by PM System"""

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": report, "parse_mode": "Markdown"})

if __name__ == "__main__":
    send_daily_report()
    print("Report sent!")
