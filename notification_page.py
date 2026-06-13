import streamlit as st
import pandas as pd
from supabase_db import read_sheet

def notification_page():
    st.title("🔔 Notifikasi Update")
    
    df = read_sheet("push_notifications")
    
    if df.empty:
        st.info("📋 Belum ada notifikasi.")
        return
    
    df['created_at'] = pd.to_datetime(df['created_at'])
    df = df.sort_values('created_at', ascending=False)
    
    # Filter
    pic_list = ['ALL'] + sorted(df['pic'].dropna().unique().tolist())
    sel_pic = st.selectbox("👷 Filter PIC:", pic_list)
    
    filtered = df.copy()
    if sel_pic != 'ALL':
        filtered = filtered[filtered['pic'] == sel_pic]
    
    for _, row in filtered.head(50).iterrows():
        emoji = {'DONE': '✅', 'ONGOING': '🔄', 'DELAYED': '⚠️', 'PENDING': '📌'}
        em = emoji.get(row['action'], '📋')
        st.markdown(f"{em} **{row['pic']}** {row['action']} — {row['task_name']} ({row['site_name']})")
        st.caption(f"🕐 {row['created_at'].strftime('%d %b %Y, %H:%M')}")
        st.markdown("---")

if __name__ == "__main__":
    notification_page()
