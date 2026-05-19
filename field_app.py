import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from supabase_db import read_sheet, update_row, read_all_sheets

def field_app_page():
    st.title("📱 Field Update App")
    
    all_data = read_all_sheets()
    ms_df = all_data.get('milestones', pd.DataFrame())
    sites_df = all_data.get('projects', pd.DataFrame())
    master_df = all_data.get('master_projects', pd.DataFrame())
    
    if ms_df.empty:
        st.info("📋 Belum ada milestone.")
        return
    
    # Salin dataframe asli untuk proses filtering agar tidak merusak data utama
    ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
    filtered_df = ms_df.copy()
    
    # Sidebar
    with st.sidebar:
        user = st.session_state.get('user', {})
        st.markdown(f"👷 **{user.get('full_name', 'Engineer')}**")
        
        if st.button("🚪 Logout", key="field_logout_btn", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state['logged_in'] = False
            st.rerun()
        
        st.divider()
        st.header("⚙️ Filter")
        
        # 1. Filter Project (Master Project)
        selected_master = "ALL"
        if not master_df.empty:
            master_options = ["ALL"] + master_df['id'].tolist()
            
            # Ambil dictionary helper agar format_func berjalan lebih cepat dan aman
            project_code_map = dict(zip(master_df['id'], master_df['project_code']))
            project_name_map = dict(zip(master_df['id'], master_df['project_name']))
            
            selected_master = st.selectbox(
                "🏢 Project:", 
                master_options,
                format_func=lambda x: "🌐 SEMUA PROJECT" if x == "ALL" else f"{project_code_map.get(x, '')} - {project_name_map.get(x, '')}"
            )
            
            if selected_master != "ALL":
                valid_project_ids = sites_df[sites_df['master_project_id'] == selected_master]['id'].tolist()
                filtered_df = filtered_df[filtered_df['project_id'].isin(valid_project_ids)]
        
        # 2. Filter Site (pakai site_name)
        if not sites_df.empty:
            # Dropdown site dinamis menyesuaikan project yang dipilih agar UI/UX lebih clean
            if selected_master != "ALL":
                available_sites = sites_df[sites_df['master_project_id'] == selected_master]['site_name'].unique().tolist()
            else:
                available_sites = sites_df['site_name'].unique().tolist()
                
            site_options = ["ALL"] + available_sites
            selected_site = st.selectbox("📍 Site:", site_options)
            
            if selected_site != "ALL":
                valid_site_ids = sites_df[sites_df['site_name'] == selected_site]['id'].tolist()
                filtered_df = filtered_df[filtered_df['project_id'].isin(valid_site_ids)]
        
        # 3. Filter PIC (Mengambil dari dataframe yang sudah terfilter sebelumnya)
        pic_list = sorted(filtered_df['assigned_to'].dropna().unique().tolist()) if 'assigned_to' in filtered_df.columns else []
        if pic_list:
            # Tambahkan opsi ALL agar PIC bisa di-reset kembali
            pic_options = ["ALL"] + pic_list
            selected_pic = st.selectbox("👷 PIC:", pic_options)
            if selected_pic != "ALL":
                filtered_df = filtered_df[filtered_df['assigned_to'] == selected_pic]
        
        st.divider()
        st.metric("📋 Tasks", len(filtered_df))
    
    # Main content menggunakan filtered_df
    if filtered_df.empty:
        st.success("✅ Tidak ada task!")
        return
    
    site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    site_name_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    
    for _, task in filtered_df.iterrows():
        site_code = site_map.get(task['project_id'], '-')
        site_name = site_name_map.get(task['project_id'], '-')
        deadline = task['planned_end'].strftime('%d %b %Y') if pd.notna(task['planned_end']) else '-'
        days_left = (task['planned_end'].date() - date.today()).days if pd.notna(task['planned_end']) else 999
        
        if days_left < 0: bg, border = '#FEE2E2', '#EF4444'
        elif days_left == 0: bg, border = '#FEF3C7', '#F59E0B'
        elif task['status'] == 'DONE': bg, border = '#DCFCE7', '#10B981'
        else: bg, border = '#F0FDF4', '#10B981'
        
        st.markdown(f"""
        <div style='background:{bg}; padding:10px; border-radius:8px; margin:5px 0; border-left:4px solid {border};'>
            <strong>{task['name']}</strong><br>
            📍 {site_code} - {site_name}<br>
            📅 {deadline} | ⏰ {days_left} hari | {task.get('status','?')}
        </div>
        """, unsafe_allow_html=True)
        
        with st.form(f"upd_{task['id']}", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                statuses = ['PENDING','ONGOING','DONE','DELAYED']
                cur_status = task.get('status','PENDING')
                s_idx = statuses.index(cur_status) if cur_status in statuses else 0
                new_status = st.selectbox("Status", statuses, index=s_idx, key=f"st_{task['id']}")
                
                as_d = pd.to_datetime(task.get('actual_start')).date() if pd.notna(task.get('actual_start')) else None
                new_as = st.date_input("Actual Start", value=as_d, key=f"as_{task['id']}")
            with c2:
                cur_prog = int(float(task.get('progress',0))) if task.get('progress') and str(task.get('progress','')).replace('.','').isdigit() else 0
                new_progress = st.slider("Progress %", 0, 100, cur_prog, key=f"pr_{task['id']}")
                
                ae_d = pd.to_datetime(task.get('actual_end')).date() if pd.notna(task.get('actual_end')) else None
                new_ae = st.date_input("Actual End", value=ae_d, key=f"ae_{task['id']}")
            
            if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                update_data = {'status': new_status, 'progress': str(new_progress)}
                if new_as: update_data['actual_start'] = new_as.strftime('%Y-%m-%d')
                if new_ae or new_status == 'DONE':
                    update_data['actual_end'] = (new_ae or date.today()).strftime('%Y-%m-%d')
                update_row('milestones', task['id'], update_data)
                st.success(f"✅ {task['name']} diupdate!")
                st.toast(f"✅ {task['name']} → {new_status}", icon="🎉")
                st.rerun()
        st.markdown("---")

if __name__ == "__main__":
    field_app_page()
