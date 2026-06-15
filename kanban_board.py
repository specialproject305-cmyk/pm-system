import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase_db import read_sheet, update_row

def kanban_page():
    st.markdown("""
    <style>
        .kanban-container { display: flex; gap: 12px; }
        .kanban-column {
            flex: 1;
            background: rgba(255,255,255,0.8);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 14px;
            border: 1px solid rgba(0,0,0,0.06);
            padding: 14px;
            min-height: 500px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        }
        .kanban-column-header {
            display: flex; justify-content: space-between; align-items: center;
            padding-bottom: 10px; margin-bottom: 10px;
            border-bottom: 2px solid #E2E8F0;
            font-weight: 700; font-size: 0.85rem; color: #1E293B;
            text-transform: uppercase; letter-spacing: 0.5px;
        }
        .kanban-count {
            background: #6366F1; color: white; padding: 2px 10px;
            border-radius: 12px; font-size: 0.7rem; font-weight: 700;
        }
        .kanban-card {
            background: white; border-radius: 10px; padding: 10px;
            margin-bottom: 6px; border-left: 4px solid #6366F1;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            transition: all 0.2s ease; cursor: pointer;
        }
        .kanban-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,0,0,0.08); }
        .kanban-card.pending { border-left-color: #94A3B8; }
        .kanban-card.ongoing { border-left-color: #3B82F6; }
        .kanban-card.done { border-left-color: #10B981; }
        .kanban-card.delayed { border-left-color: #EF4444; }
        .kanban-card.critical { border-left-color: #991B1B; }
        .card-title { font-weight: 600; color: #1E293B; font-size: 0.85rem; margin-bottom: 4px; }
        .card-meta { font-size: 0.7rem; color: #64748B; }
        .card-progress { height: 4px; background: #E2E8F0; border-radius: 2px; margin-top: 6px; overflow: hidden; }
        .card-progress-bar { height: 100%; border-radius: 2px; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📋 Kanban Board")
    
    sites_df = read_sheet("projects")
    ms_df = read_sheet("milestones")
    
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
    if sel_site != 'ALL SITE': ms_df = ms_df[ms_df['project_id']==sel_site]
    
    # Filter PIC
    if 'assigned_to' in ms_df.columns:
        pic_list = ['ALL'] + sorted(ms_df['assigned_to'].dropna().unique().tolist())
        sel_pic = st.selectbox("👷 PIC:", pic_list)
        if sel_pic != 'ALL': ms_df = ms_df[ms_df['assigned_to']==sel_pic]
    
    # Merge
    site_map = dict(zip(sites_df['id'], sites_df['site_id'])) if not sites_df.empty else {}
    site_name_map = dict(zip(sites_df['id'], sites_df['site_name'])) if not sites_df.empty else {}
    ms_df['site_code'] = ms_df['project_id'].map(site_map).fillna('-')
    ms_df['site_name'] = ms_df['project_id'].map(site_name_map).fillna('-')
    ms_df['progress'] = pd.to_numeric(ms_df['progress'], errors='coerce').fillna(0)
    
    # KPI
    total = len(ms_df)
    done = len(ms_df[ms_df['status']=='DONE'])
    delayed = len(ms_df[ms_df['status'].isin(['DELAYED','CRITICAL'])])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 Total", total)
    col2.metric("✅ Done", done)
    col3.metric("🔴 Delayed", delayed)
    
    st.divider()
    
    # Kanban columns
    statuses = ['PENDING', 'ONGOING', 'DONE', 'DELAYED']
    colors = {'PENDING':'#94A3B8', 'ONGOING':'#3B82F6', 'DONE':'#10B981', 'DELAYED':'#EF4444'}
    css_class = {'PENDING':'pending', 'ONGOING':'ongoing', 'DONE':'done', 'DELAYED':'delayed'}
    
    cols = st.columns(4)
    for i, status in enumerate(statuses):
        with cols[i]:
            subset = ms_df[ms_df['status']==status]
            count = len(subset)
            
            st.markdown(f"""
            <div class="kanban-column">
                <div class="kanban-column-header">
                    <span>{status}</span>
                    <span class="kanban-count">{count}</span>
                </div>
            """, unsafe_allow_html=True)
            
            for _, task in subset.iterrows():
                pct = task['progress']
                bar_color = colors.get(status, '#6366F1')
                
                st.markdown(f"""
                <div class="kanban-card {css_class.get(status, '')}">
                    <div class="card-title">{task['name'][:40]}</div>
                    <div class="card-meta">📍 {task['site_code']} | 👷 {task.get('assigned_to','-')}</div>
                    <div class="card-progress">
                        <div class="card-progress-bar" style="width:{pct}%; background:{bar_color};"></div>
                    </div>
                    <div class="card-meta" style="margin-top:4px;">{pct:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Quick action
                if status != 'DONE':
                    if st.button("✅ Done", key=f"kb_done_{task['id']}"):
                        update_row('milestones', task['id'], {'status':'DONE','progress':'100','actual_end':date.today().strftime('%Y-%m-%d')})
                        st.cache_data.clear(); st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    kanban_page()
