import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase_db import read_all_sheets, insert_row, generate_id, now_str, delete_row_by_id

def chat_notif_page():
    st.title("💬 Diskusi & Notifikasi")
    
    # Load semua data sekali di awal
    all_data = read_all_sheets()
    messages = all_data.get('chat_messages', pd.DataFrame())
    notifs = all_data.get('notifications', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    ms_df = all_data.get('milestones', pd.DataFrame())
    mat_df = all_data.get('materials', pd.DataFrame())

    unread = len(notifs[notifs['is_read'] == '0']) if not notifs.empty and 'is_read' in notifs.columns else 0

    # ==========================================
    # 🤖 AUTOMASI SMART REMINDER BOT (1x/Hari)
    # ==========================================
    try:
        today = date.today()
        today_str = today.strftime('%Y-%m-%d')
        
        # 1. Cek apakah bot sudah kirim reminder hari ini
        already_sent_today = False
        if not messages.empty and 'created_at' in messages.columns:
            bot_msgs_today = messages[
                (messages['site_id'] == 'GLOBAL') & 
                (messages['sender'] == 'System Bot') &
                (messages['created_at'].astype(str).str.startswith(today_str))
            ]
            if not bot_msgs_today.empty:
                already_sent_today = True
        
        # 2. Jika belum, scan data & kirim reminder
        if not already_sent_today:
            reminders = []
            
            # A. Cek Deadline Milestone (Status PENDING/ONGOING, sisa 0-2 hari)
            if not ms_df.empty and 'planned_end' in ms_df.columns:
                ms_df['planned_end_dt'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
                site_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
                
                active_ms = ms_df[ms_df['status'].isin(['PENDING', 'ONGOING'])]
                for _, r in active_ms.iterrows():
                    if pd.notna(r.get('planned_end_dt')):
                        days_left = (r['planned_end_dt'].date() - today).days
                        if 0 <= days_left <= 2:
                            site_name = site_map.get(r.get('project_id'), 'Site')
                            pic = r.get('assigned_to', '-')
                            reminders.append(f"🤖 [AUTO] ⏳ **Deadline Mendekati**: {r['name']} di {site_name} (Sisa {days_left} hari). PIC: {pic}")
            
            # B. Cek Stok Material Kritis
            if not mat_df.empty and 'current_stock' in mat_df.columns and 'min_stock' in mat_df.columns:
                mat_df['cur'] = pd.to_numeric(mat_df['current_stock'], errors='coerce').fillna(0)
                mat_df['min'] = pd.to_numeric(mat_df['min_stock'], errors='coerce').fillna(0)
                critical_mat = mat_df[mat_df['cur'] < mat_df['min']]
                for _, r in critical_mat.iterrows():
                    reminders.append(f"🤖 [AUTO] 📦 **Stok Kritis**: {r['name']} (Stok: {int(r['cur'])} < Min: {int(r['min'])}). Segera reorder!")
            
            # C. Kirim ke Global Chat
            if reminders:
                ts = now_str()
                for msg in reminders:
                    insert_row('chat_messages', {
                        'id': generate_id(), 
                        'site_id': 'GLOBAL', 
                        'sender': 'System Bot',
                        'message': msg, 
                        'created_at': ts
                    })
                st.toast(f"🤖 {len(reminders)} Reminder otomatis dikirim ke Global Chat!", icon="🔔")
                
    except Exception:
        pass # Gagal otomatisasi tidak mengganggu UI utama

    # ==========================================
    # 📊 AUTOMASI 2: WEEKLY REPORT BOT (Setiap Senin 1x)
    # ==========================================
    try:
        today = date.today()
        # Cek apakah hari Senin
        if today.weekday() == 0:
            # Tentukan awal minggu ini (Senin)
            week_start = today - timedelta(days=today.weekday())
            week_start_str = week_start.strftime('%Y-%m-%d')
            
            # Cek apakah bot sudah kirim laporan minggu ini
            report_sent_this_week = False
            if not messages.empty and 'created_at' in messages.columns:
                bot_reports = messages[
                    (messages['sender'] == 'Weekly Report Bot') & 
                    (messages['created_at'] >= week_start_str)
                ]
                if not bot_reports.empty:
                    report_sent_this_week = True
            
            # Jika belum, generate & kirim laporan
            if not report_sent_this_week:
                # 1. Hitung Metrik
                total_sites = len(sites_df)
                avg_prog = pd.to_numeric(sites_df.get('progress', pd.Series(dtype=float)), errors='coerce').mean() if 'progress' in sites_df.columns else 0
                on_track = len(sites_df[sites_df['status']=='ON_TRACK']) if 'status' in sites_df.columns else 0
                delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])]) if 'status' in sites_df.columns else 0
                
                # Milestone DONE (cek actual_end 7 hari terakhir, fallback ke total DONE jika kosong)
                recent_done = 0
                if not ms_df.empty:
                    if 'actual_end' in ms_df.columns:
                        ms_df['ae_dt'] = pd.to_datetime(ms_df['actual_end'], errors='coerce')
                        recent_done = len(ms_df[(ms_df['status']=='DONE') & (ms_df['ae_dt'] >= week_start)])
                    if recent_done == 0:
                        recent_done = len(ms_df[ms_df['status']=='DONE'])
                
                # Top Delay Reason
                top_delay = "-"
                if not ms_df.empty and 'delay_reason' in ms_df.columns:
                    delays = ms_df[ms_df['delay_reason'].notna() & (ms_df['delay_reason'] != 'Tidak Ada')]
                    if not delays.empty:
                        top_delay = delays['delay_reason'].value_counts().index[0]
                
                # Material Kritis
                mat_alerts = 0
                if not mat_df.empty and 'current_stock' in mat_df.columns and 'min_stock' in mat_df.columns:
                    mat_df['cur'] = pd.to_numeric(mat_df['current_stock'], errors='coerce').fillna(0)
                    mat_df['min'] = pd.to_numeric(mat_df['min_stock'], errors='coerce').fillna(0)
                    mat_alerts = len(mat_df[mat_df['cur'] < mat_df['min']])
                
                # 2. Format Pesan
                report_msg = f"""🤖 [AUTO] 📊 **LAPORAN MINGGUAN** ({today.strftime('%d %b %Y')})
📁 Total Site: {total_sites} | 🟢 On Track: {on_track} | 🔴 Delayed: {delayed}
📈 Rata-rata Progress: {avg_prog:.1f}%
✅ Milestone Selesai (Minggu Ini): {recent_done}
⚠️ Penyebab Delay Utama: {top_delay}
📦 Material Kritis: {mat_alerts} item
💡 *Rekomendasi: Fokus percepat {delayed} site terlambat & reorder material kritis.*
"""
                # 3. Kirim ke Global Chat
                insert_row('chat_messages', {
                    'id': generate_id(), 
                    'site_id': 'GLOBAL', 
                    'sender': 'Weekly Report Bot',
                    'message': report_msg, 
                    'created_at': now_str()
                })
                st.toast("📊 Laporan mingguan otomatis dikirim ke Global Chat!", icon="📈")
                
    except Exception:
        pass # Gagal generate laporan tidak mengganggu UI
    # ==========================================
    # ==========================================

    # Floating bell notification
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
