import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from supabase_db import read_sheet, update_row, read_all_sheets, notify_update

def inject_field_css():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%); font-family: 'Inter', sans-serif; }
        
        /* KANBAN LAYOUT STRUCTURE */
        .kanban-column { 
            background: rgba(255,255,255,0.8); 
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 14px; 
            border: 1px solid rgba(0,0,0,0.06); 
            padding: 14px; 
            min-height: 500px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
            margin-bottom: 20px;
        }
        .kanban-column-header { 
            font-weight: 700; 
            color: #1E293B; 
            font-size: 0.85rem; 
            margin-bottom: 12px; 
            padding-bottom: 10px; 
            border-bottom: 2px solid #E2E8F0; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .kanban-count {
            background: #6366F1; 
            color: white; 
            padding: 2px 10px;
            border-radius: 12px; 
            font-size: 0.7rem; 
            font-weight: 700;
        }
        
        /* CARD CONTAINER MANAGEMENT */
        .card-wrapper {
            position: relative;
            margin-bottom: 10px;
        }
        
        .kanban-card { 
            background: white; 
            padding: 12px; 
            border-radius: 10px; 
            border-left: 4px solid #6366F1; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            transition: all 0.2s ease;
            pointer-events: none; /* Mengabaikan klik agar tembus ke tombol di bawahnya */
        }
        .card-wrapper:hover .kanban-card { 
            transform: translateY(-2px); 
            box-shadow: 0 8px 20px rgba(0,0,0,0.08); 
        }
        
        .kanban-card.pending { border-left-color: #94A3B8; }
        .kanban-card.ongoing { border-left-color: #3B82F6; }
        .kanban-card.done { border-left-color: #10B981; }
        .kanban-card.delayed { border-left-color: #EF4444; }
        
        .card-title { font-weight: 600; color: #1E293B; font-size: 0.85rem; margin-bottom: 4px; line-height: 1.3; }
        .card-meta { font-size: 0.7rem; color: #64748B; margin-top: 2px; }
        .card-progress { height: 4px; background: #E2E8F0; border-radius: 2px; margin-top: 8px; overflow: hidden; }
        .card-progress-bar { height: 100%; border-radius: 2px; }
        
        /* TOMBOL TRANSPARAN DI ATAS KARTU */
        .clickable-overlay button {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100% !important;
            background: transparent !important;
            border: none !important;
            color: transparent !important;
            cursor: pointer !important;
            z-index: 10 !important;
            box-shadow: none !important;
        }
        .clickable-overlay button:hover, .clickable-overlay button:active, .clickable-overlay button:focus {
            background: transparent !important;
            border: none !important;
            color: transparent !important;
            box-shadow: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

@st.dialog("✏️ Update Milestone Task")
def render_update_modal(task, site_code, assigned_to):
    task_id = task['id']
    st.markdown(f"### {task['name'][:40]}")
    st.caption(f"📍 Site Code: {site_code} | 👷 PIC: {assigned_to}")
    
    new_status = st.selectbox(
        "Status", ['PENDING','ONGOING','DONE','DELAYED'],
        index=['PENDING','ONGOING','DONE','DELAYED'].index(task.get('status','PENDING')),
        key=f"st_{task_id}"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        new_progress = st.slider("Progress %", 0, 100, int(task.get('progress', 0)), key=f"pr_{task_id}")
        as_d = pd.to_datetime(task.get('actual_start')).date() if pd.notna(task.get('actual_start')) else None
        new_as = st.date_input("Actual Start", value=as_d, key=f"as_{task_id}")
    with col2:
        ae_d = pd.to_datetime(task.get('actual_end')).date() if pd.notna(task.get('actual_end')) else None
        new_ae = st.date_input("Actual End", value=ae_d, key=f"ae_{task_id}")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Simpan", type="primary", use_container_width=True, key=f"save_{task_id}"):
            update_data = {'status': new_status, 'progress': str(new_progress)}
            if new_as: update_data['actual_start'] = new_as.strftime('%Y-%m-%d')
            if new_ae: update_data['actual_end'] = new_ae.strftime('%Y-%m-%d')
            if new_status == 'DONE' and not new_ae: update_data['actual_end'] = date.today().strftime('%Y-%m-%d')
            
            update_row('milestones', task_id, update_data)
            
            try: notify_update(assigned_to, new_status, task['name'], site_code)
            except: pass
                
            st.cache_data.clear()
            st.session_state.selected_task = None
            st.rerun()
            
    with col_btn2:
        if st.button("❌ Cancel", use_container_width=True, key=f"cancel_{task_id}"):
            st.session_state.selected_task = None
            st.rerun()

def kanban_page():
    inject_field_css()

    st.title("📋 Kanban Board")
    
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
    
    # Global filter
    if st.session_state.get('global_project_filter', 'ALL') != "ALL":
        valid = sites_df[sites_df.get('master_project_id','') == st.session_state.global_project_filter]['id'].tolist()
        sites_df = sites_df[sites_df['id'].isin(valid)]
        ms_df = ms_df[ms_df['project_id'].isin(valid)] if not ms_df.empty else ms_df
    
    # Filter site
    site_list = ['ALL SITE'] + sites_df['id'].tolist() if not sites_df.empty else ['ALL SITE']
    sel_site = st.selectbox("🎯 Site:", site_list, format_func=lambda x: '🌍 ALL' if x=='ALL SITE' else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
    if sel_site != 'ALL SITE': 
        ms_df = ms_df[ms_df['project_id'] == sel_site]
    
    # Filter PIC
    if 'assigned_to' in ms_df.columns:
        pic_list = ['ALL'] + sorted(ms_df['assigned_to'].dropna().unique().tolist())
        sel_pic = st.selectbox("👷 PIC:", pic_list)
        if sel_pic != 'ALL': 
            ms_df = ms_df[ms_df['assigned_to'] == sel_pic]
    
    # Merge & Data Cleaning
    site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    site_name_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    ms_df['site_code'] = ms_df['project_id'].map(site_map).fillna('-')
    ms_df['site_name'] = ms_df['project_id'].map(site_name_map).fillna('-')
    ms_df['progress'] = pd.to_numeric(ms_df['progress'], errors='coerce').fillna(0)
    
    # KPI Section
    total = len(ms_df)
    done = len(ms_df[ms_df['status']=='DONE'])
    delayed = len(ms_df[ms_df['status'].isin(['DELAYED','CRITICAL'])])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 Total Tasks", total)
    col2.metric("✅ Done", done)
    col3.metric("🔴 Delayed", delayed)
    
    st.divider()
    
    # Kanban Configuration Mapping
    statuses = ['PENDING', 'ONGOING', 'DONE', 'DELAYED']
    colors = {'PENDING':'#94A3B8', 'ONGOING':'#3B82F6', 'DONE':'#10B981', 'DELAYED':'#EF4444'}
    css_class = {'PENDING':'pending', 'ONGOING':'ongoing', 'DONE':'done', 'DELAYED':'delayed'}
    
    cols = st.columns(4)
    for i, status in enumerate(statuses):
        with cols[i]:
            subset = ms_df[ms_df['status'] == status]
            count = len(subset)
            
            # Render Header Kolom Kanban
            st.html(f"""
            <div class="kanban-column">
                <div class="kanban-column-header">
                    <span>{status}</span>
                    <span class="kanban-count">{count}</span>
                </div>
            """)
            
            # Render Item Kartu secara aman
            for _, task in subset.iterrows():
                pct = task['progress']
                bar_color = colors.get(status, '#6366F1')
                current_css = css_class.get(status, '')
                assigned_pic = task.get('assigned_to', '-')
                
                # Sediakan Container Relatif
                st.html(f"""
                <div class="card-wrapper">
                    <div class="kanban-card {current_css}">
                        <div class="card-title">{task['name'][:40]}</div>
                        <div class="card-meta">📍 {task['site_code']} | 👷 {assigned_pic}</div>
                        <div class="card-progress">
                            <div class="card-progress-bar" style="width:{pct}%; background:{bar_color};"></div>
                        </div>
                        <div class="card-meta" style="margin-top:4px;">{pct:.0f}%</div>
                    </div>
                    <div class="clickable-overlay">
                """)
                
                # Tombol transparan ditaruh tepat di atas HTML card
                if st.button("", key=f"overlay_btn_{task['id']}", use_container_width=True):
                    st.session_state.selected_task = task['id']
                    st.rerun()
                
                # Tutup wrapper elemen kartu
                st.html("</div></div>")
            
            # Tutup kontainer kolom kanban
            st.html("</div>")
            
    # ===== RENDER DIALOG UPDATE POP-UP =====
    if st.session_state.selected_task:
        task_id = st.session_state.selected_task
        task_row = ms_df[ms_df['id'] == task_id]
        
        if not task_row.empty:
            current_task = task_row.iloc[0]
            current_site_code = site_map.get(current_task['project_id'], '-')
            current_pic = current_task.get('assigned_to', '-')
            
            render_update_modal(current_task, current_site_code, current_pic)

if __name__ == "__main__":
    kanban_page()
