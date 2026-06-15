import streamlit as st
import pandas as pd
from datetime import date
from supabase_db import read_sheet, update_row, read_all_sheets, notify_update

def inject_field_css():
    st.markdown("""
    <style>
        /* BASE DESIGN */
        .stApp { background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%); font-family: 'Inter', sans-serif; }
        
        /* KANBAN LAYOUT STRUCTURE */
        .kanban-container { display: flex; gap: 16px; align-items: flex-start; }
        .kanban-column { 
            flex: 1;
            background: rgba(255,255,255,0.9); 
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 16px; 
            border: 1px solid rgba(0,0,0,0.05); 
            padding: 16px; 
            min-height: 600px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.02);
        }
        .kanban-column-header { 
            font-weight: 800; 
            color: #1E293B; 
            font-size: 0.85rem; 
            margin-bottom: 16px; 
            padding-bottom: 12px; 
            border-bottom: 2px solid #F1F5F9; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }
        .kanban-count {
            background: #6366F1; 
            color: white; 
            padding: 2px 10px;
            border-radius: 20px; 
            font-size: 0.75rem; 
            font-weight: 700;
        }
        
        /* CARD MANAGEMENT LINK STYLING */
        .card-link {
            text-decoration: none !important;
            color: inherit !important;
            display: block;
            margin-bottom: 12px;
            transition: all 0.2s ease-in-out;
        }
        
        .kanban-card { 
            background: white; 
            padding: 16px; 
            border-radius: 12px; 
            border-left: 5px solid #6366F1; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            border-top: 1px solid rgba(0,0,0,0.02);
            border-right: 1px solid rgba(0,0,0,0.02);
            border-bottom: 1px solid rgba(0,0,0,0.02);
        }
        
        .card-link:hover .kanban-card { 
            transform: translateY(-3px); 
            box-shadow: 0 12px 24px rgba(99, 102, 241, 0.12); 
        }
        
        /* FIELD APP BORDER COLOR STATUS MATCHING */
        .kanban-card.pending { border-left-color: #6366F1; }
        .kanban-card.ongoing { border-left-color: #3B82F6; }
        .kanban-card.done { border-left-color: #10B981; }
        .kanban-card.delayed { border-left-color: #EF4444; }
        
        .card-title { font-weight: 700; color: #1E293B; font-size: 0.9rem; margin-bottom: 6px; line-height: 1.4; }
        .card-meta { font-size: 0.75rem; color: #64748B; display: flex; align-items: center; gap: 4px; margin-top: 4px; }
        .card-progress { height: 5px; background: #E2E8F0; border-radius: 10px; margin-top: 12px; overflow: hidden; }
        .card-progress-bar { height: 100%; border-radius: 10px; }
        .card-percentage { font-size: 0.7rem; color: #94A3B8; margin-top: 6px; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# POP-UP MODAL FORM EDIT (DIREDIREKSI LEWAT DIALOG FORM)
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
        if st.button("💾 Save Changes", type="primary", use_container_width=True):
            # Skenario Simpan Data
            update_data = {'status': new_status, 'progress': str(new_progress)}
            if new_as: update_data['actual_start'] = new_as.strftime('%Y-%m-%d')
            if new_ae: update_data['actual_end'] = new_ae.strftime('%Y-%m-%d')
            if new_status == 'DONE' and not new_ae: update_data['actual_end'] = date.today().strftime('%Y-%m-%d')
            
            # Update database backend
            update_row('milestones', task_id, update_data)
            
            try: notify_update(assigned_to, new_status, task['name'], site_code)
            except: pass
                
            # Clear cache & bersihkan query string URL untuk menutup modal popup
            st.cache_data.clear()
            st.query_params.clear()
            st.rerun()
            
    with col_btn2:
        if st.button("❌ Cancel", use_container_width=True):
            # Skenario Cancel: Bersihkan query parameter tanpa merubah atau menyimpan data apa pun
            st.query_params.clear()
            st.rerun()

def kanban_page():
    inject_field_css()

    st.title("📋 Kanban Board")
    
    # Deteksi aksi klik via Query Params URL
    query_params = st.query_params
    selected_task_id = query_params.get("edit_task", None)
    
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
    
    # Kanban Visual Layout Configuration
    statuses = ['PENDING', 'ONGOING', 'DONE', 'DELAYED']
    colors = {'PENDING':'#6366F1', 'ONGOING':'#3B82F6', 'DONE':'#10B981', 'DELAYED':'#EF4444'}
    css_class = {'PENDING':'pending', 'ONGOING':'ongoing', 'DONE':'done', 'DELAYED':'delayed'}
    
    cols = st.columns(4)
    for i, status in enumerate(statuses):
        with cols[i]:
            subset = ms_df[ms_df['status'] == status]
            count = len(subset)
            
            # Inisialisasi blok HTML utuh per Kolom
            column_html = f"""
            <div class="kanban-column">
                <div class="kanban-column-header">
                    <span>{status}</span>
                    <span class="kanban-count">{count}</span>
                </div>
            """
            
            # Bangun struktur kartu HTML dengan link internal query parameter (?edit_task=ID)
            for _, task in subset.iterrows():
                pct = task['progress']
                bar_color = colors.get(status, '#6366F1')
                current_css = css_class.get(status, '')
                assigned_pic = task.get('assigned_to', '-')
                
                column_html += f"""
                <a href="?edit_task={task['id']}" target="_self" class="card-link">
                    <div class="kanban-card {current_css}">
                        <div class="card-title">{task['name'][:40]}</div>
                        <div class="card-meta">📍 {task['site_code']} | 👷 {assigned_pic}</div>
                        <div class="card-progress">
                            <div class="card-progress-bar" style="width:{pct}%; background:{bar_color};"></div>
                        </div>
                        <div class="card-percentage">{pct:.0f}%</div>
                    </div>
                </a>
                """
            
            column_html += "</div>"
            
            # Render visual Kanban Column secara aman tanpa kebocoran element tombol
            st.markdown(column_html, unsafe_allow_html=True)
            
    # ===== LOGIKA PEMICU POP-UP MODAL EDIT =====
    if selected_task_id:
        # Cari data baris task berdasarkan id dari parameter URL
        task_row = ms_df[ms_df['id'] == selected_task_id]
        if not task_row.empty:
            current_task = task_row.iloc[0]
            current_site_code = site_map.get(current_task['project_id'], '-')
            current_pic = current_task.get('assigned_to', '-')
            
            # Tampilkan dialog pop-up resmi edit form
            render_update_modal(current_task, current_site_code, current_pic)
