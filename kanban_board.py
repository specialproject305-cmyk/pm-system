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
            
            # 1. BUAT KONTEN HEADER KOLOM
            column_html = f"""
            <div class="kanban-column">
                <div class="kanban-column-header">
                    <span>{status}</span>
                    <span class="kanban-count">{count}</span>
                </div>
            """
            
            # 2. GABUNGKAN SELURUH KARTU DI KOLOM INI MENJADI SATU STRING HTML UTUH
            for _, task in subset.iterrows():
                pct = task['progress']
                bar_color = colors.get(status, '#6366F1')
                current_css = css_class.get(status, '')
                assigned_pic = task.get('assigned_to', '-')
                
                column_html += f"""
                <div class="card-wrapper">
                    <div class="kanban-card {current_css}">
                        <div class="card-title">{task['name'][:40]}</div>
                        <div class="card-meta">📍 {task['site_code']} | 👷 {assigned_pic}</div>
                        <div class="card-progress">
                            <div class="card-progress-bar" style="width:{pct}%; background:{bar_color};"></div>
                        </div>
                        <div class="card-meta" style="margin-top:4px;">{pct:.0f}%</div>
                    </div>
                </div>
                """
            
            # Tutup kontainer utama kolom
            column_html += "</div>"
            
            # 3. RENDER SELURUH STRUKTUR KOLOM SECARA BERSAMAAN
            st.html(column_html)
            
            # 4. RENDER ELEMENT TOMBOL TRAP TRANSPARAN SECARA TERPISAH DI BAWAHNYA
            # Penempatan posisi overlay dikunci menggunakan koordinat CSS absolute agar tepat membungkus kartu asli
            for _, task in subset.iterrows():
                if st.button("", key=f"overlay_btn_{task['id']}", use_container_width=True):
                    st.session_state.selected_task = task['id']
                    st.rerun()
            
    # ===== RENDER DIALOG UPDATE POP-UP =====
    if st.session_state.selected_task:
        task_id = st.session_state.selected_task
        task_row = ms_df[ms_df['id'] == task_id]
        
        if not task_row.empty:
            current_task = task_row.iloc[0]
            current_site_code = site_map.get(current_task['project_id'], '-')
            current_pic = current_task.get('assigned_to', '-')
            
            render_update_modal(current_task, current_site_code, current_pic)
