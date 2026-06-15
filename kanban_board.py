import streamlit as st
import pandas as pd
from datetime import date
from supabase_db import read_sheet, update_row, read_all_sheets, notify_update

def inject_field_css():
    st.markdown("""
    <style>
        /* BASE DESIGN */
        .stApp { background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%); font-family: 'Inter', sans-serif; }
        
        /* Menghilangkan border default bawaan tombol asli streamlit agar menyatu dengan container */
        div.stButton > button {
            border: none !important;
            background-color: transparent !important;
            padding: 0px !important;
            color: #1E293B !important;
            text-align: left !important;
            font-weight: 700 !important;
            font-size: 0.9rem !important;
            width: 100% !important;
            box-shadow: none !important;
        }
        div.stButton > button:hover {
            color: #2563EB !important;
            background-color: transparent !important;
            border: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

# POP-UP MODAL FORM EDIT NATIVE VIA @ST.DIALOG
@st.dialog("✏️ Update Milestone Task")
def render_update_modal(task, site_code, assigned_to):
    task_id = task['id']
    st.markdown(f"### {task['name']}")
    st.caption(f"📍 Site Code: {site_code} | 👷 PIC: {assigned_to}")
    st.divider()
    
    # Form input fields
    new_status = st.selectbox(
        "Status Task", ['PENDING','ONGOING','DONE','DELAYED'],
        index=['PENDING','ONGOING','DONE','DELAYED'].index(task.get('status','PENDING'))
    )
    
    col1, col2 = st.columns(2)
    with col1:
        new_progress = st.slider("Progress (%)", 0, 100, int(task.get('progress', 0)))
        as_d = pd.to_datetime(task.get('actual_start')).date() if pd.notna(task.get('actual_start')) else None
        new_as = st.date_input("Actual Start Date", value=as_d)
    with col2:
        ae_d = pd.to_datetime(task.get('actual_end')).date() if pd.notna(task.get('actual_end')) else None
        new_ae = st.date_input("Actual End Date", value=ae_d)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("💾 Save Changes", type="primary", use_container_width=True, key=f"modal_save_{task_id}"):
            # Skenario Simpan Data
            update_data = {'status': new_status, 'progress': str(new_progress)}
            if new_as: update_data['actual_start'] = new_as.strftime('%Y-%m-%d')
            if new_ae: update_data['actual_end'] = new_ae.strftime('%Y-%m-%d')
            if new_status == 'DONE' and not new_ae: update_data['actual_end'] = date.today().strftime('%Y-%m-%d')
            
            # Update ke database backend
            update_row('milestones', task_id, update_data)
            
            try: notify_update(assigned_to, new_status, task['name'], site_code)
            except: pass
                
            # Reset state dan keluar dari modal popup
            st.cache_data.clear()
            st.session_state.selected_task = None
            st.rerun()
            
    with col_btn2:
        if st.button("❌ Cancel", use_container_width=True, key=f"modal_cancel_{task_id}"):
            # Skenario Cancel: Keluar dari modal tanpa menyimpan data
            st.session_state.selected_task = None
            st.rerun()

def kanban_page():
    inject_field_css()

    st.title("📋 Kanban Board")
    
    # State managemen penanda task mana yang sedang diedit
    if 'selected_task' not in st.session_state:
        st.session_state.selected_task = None
    
    try:
        try:
            all_data = read_all_sheets()
            sites_df = all_data.get('projects', pd.DataFrame())
            ms_df = all_data.get('milestones', pd.DataFrame())
        except:
            sites_df = read_sheet("projects")
            ms_df = read_sheet("milestones")
    except Exception as e:
        st.error(f"⚠️ Error loading data: {e}"); return
        
    if ms_df.empty:
        st.info("📋 Belum ada milestone."); return
    
    # Global filter project
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid = sites_df[sites_df.get('master_project_id','') == st.session_state.global_project_filter]['id'].tolist()
        sites_df = sites_df[sites_df['id'].isin(valid)]
        ms_df = ms_df[ms_df['project_id'].isin(valid)] if not ms_df.empty else ms_df
    
    # Filter site selector
    site_list = ['ALL SITE'] + sites_df['id'].tolist() if not sites_df.empty else ['ALL SITE']
    sel_site = st.selectbox("🎯 Site:", site_list, format_func=lambda x: '🌍 ALL' if x=='ALL SITE' else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
    if sel_site != 'ALL SITE': 
        ms_df = ms_df[ms_df['project_id'] == sel_site]
    
    # Filter PIC selector
    if 'assigned_to' in ms_df.columns:
        pic_list = ['ALL'] + sorted(ms_df['assigned_to'].dropna().unique().tolist())
        sel_pic = st.selectbox("👷 PIC:", pic_list)
        if sel_pic != 'ALL': 
            ms_df = ms_df[ms_df['assigned_to'] == sel_pic]
    
    # Data Mapping Transformation
    site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    site_name_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    ms_df['site_code'] = ms_df['project_id'].map(site_map).fillna('-')
    ms_df['site_name'] = ms_df['project_id'].map(site_name_map).fillna('-')
    ms_df['progress'] = pd.to_numeric(ms_df['progress'], errors='coerce').fillna(0)
    
    # Metrics Area
    total = len(ms_df)
    done = len(ms_df[ms_df['status']=='DONE'])
    delayed = len(ms_df[ms_df['status'].isin(['DELAYED','CRITICAL'])])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 Total Tasks", total)
    col2.metric("✅ Done", done)
    col3.metric("🔴 Delayed", delayed)
    
    st.divider()
    
    # Kanban Column Status Mapping
    statuses = ['PENDING', 'ONGOING', 'DONE', 'DELAYED']
    colors = {'PENDING':'#2563EB', 'ONGOING':'#3B82F6', 'DONE':'#10B981', 'DELAYED':'#EF4444'}
    
    cols = st.columns(4)
    for i, status in enumerate(statuses):
        with cols[i]:
            # Judul header kolom status
            subset = ms_df[ms_df['status'] == status]
            st.markdown(f"### {status} ` {len(subset)} `")
            
            # Looping render masing-masing kartu menggunakan container ber-border native
            for _, task in subset.iterrows():
                pct = task['progress']
                bar_color = colors.get(status, '#2563EB')
                assigned_pic = task.get('assigned_to', '-')
                
                # Menggunakan Container Ber-border resmi dari Streamlit
                with st.container(border=True):
                    # Judul task yang bertindak sebagai tombol klik pemicu modal form edit
                    if st.button(task['name'][:40], key=f"btn_task_{task['id']}", use_container_width=True):
                        st.session_state.selected_task = task['id']
                        st.rerun()
                    
                    # Metadata isi info di dalam kartu
                    st.caption(f"📍 {task['site_code']} | 👷 {assigned_pic}")
                    st.progress(int(pct)/100)
                    st.caption(f"{pct:.0f}% Complete")
            
    # ===== LOGIKA PEMICU POP-UP MODAL EDIT =====
    if st.session_state.selected_task:
        task_id = st.session_state.selected_task
        task_row = ms_df[ms_df['id'] == task_id]
        if not task_row.empty:
            current_task = task_row.iloc[0]
            current_site_code = site_map.get(current_task['project_id'], '-')
            current_pic = current_task.get('assigned_to', '-')
            
            # Panggil fungsi dialog form edit modal
            render_update_modal(current_task, current_site_code, current_pic)

if __name__ == "__main__":
    kanban_page()
