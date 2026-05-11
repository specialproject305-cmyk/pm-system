import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase_db import read_sheet, update_row, delete_row_by_id

# ─────────────────────────────────────────────────────────────
# 🎨 CSS FOR KANBAN & MOBILE OPTIMIZATION
# ─────────────────────────────────────────────────────────────

def inject_kanban_css():
    st.markdown("""
    <style>
    .kanban-column {
        background-color: #f0f2f6;
        border-radius: 12px;
        padding: 12px;
        min-height: 400px;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .kanban-card {
        background-color: white;
        border-radius: 10px;
        padding: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        border-left: 6px solid #ccc;
        position: relative;
        overflow: hidden;
    }
    .kanban-card:hover { transform: translateY(-4px); box-shadow: 0 6px 20px rgba(0,0,0,0.12); }
    
    /* Status Border Colors */
    .border-pending { border-left-color: #6c757d !important; }
    .border-material { border-left-color: #fd7e14 !important; }
    .border-ongoing { border-left-color: #0d6efd !important; }
    .border-delayed { border-left-color: #dc3545 !important; }
    .border-done { border-left-color: #28a745 !important; }

    /* SLA Badge */
    .sla-badge {
        position: absolute; top: 8px; right: 8px;
        font-size: 0.7rem; font-weight: bold; padding: 2px 6px;
        border-radius: 4px; color: white;
    }
    .sla-ok { background: #28a745; }
    .sla-warn { background: #ffc107; color: #333 !important; }
    .sla-breach { background: #dc3545; }

    .card-title { font-weight: 600; font-size: 0.95rem; margin-bottom: 6px; padding-right: 40px; }
    .card-meta { font-size: 0.8rem; color: #555; display: flex; justify-content: space-between; align-items: center; }
    
    /* Mobile Stack */
    @media (max-width: 768px) {
        .kanban-column { min-height: auto; margin-bottom: 15px; }
        .stColumn { width: 100% !important; }
        .kanban-card { padding: 15px; }
        .card-title { font-size: 1.05rem; }
    }
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 🛠️ HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_sla_info(planned_end, status):
    """Return SLA days left & CSS class."""
    if status == 'DONE': return 0, 'sla-ok'
    if not planned_end or pd.isna(planned_end): return None, ''
    
    end_date = planned_end.date() if hasattr(planned_end, 'date') else pd.to_datetime(planned_end).date()
    days_left = (end_date - datetime.now().date()).days
    
    if days_left < 0: return days_left, 'sla-breach'
    elif days_left <= 2: return days_left, 'sla-warn'
    return days_left, 'sla-ok'

def render_card(task):
    status = task.get('status', 'PENDING')
    border_class = f"border-{status.lower().replace('material_ready', 'material')}"
    
    name = task.get('name', 'No Name')
    assigned = task.get('assigned_to', '-') or '-'
    sla_days = task.get('sla_days', '-')
    planned_end = task.get('planned_end')
    card_id = str(task.get('id'))
    
    days_left, sla_class = get_sla_info(planned_end, status)
    sla_text = f"{days_left}d" if days_left is not None else sla_days
    
    html = f"""
    <div class="kanban-card {border_class}" onclick="document.getElementById('modal-{card_id}').showModal()">
        <div class="sla-badge {sla_class}">{sla_text}</div>
        <div class="card-title">{name}</div>
        <div class="card-meta">
            <span>👤 {assigned}</span>
            <span style="font-size:0.75rem; color:#888;">{task.get('weight','0')}%</span>
        </div>
    </div>
    
    <dialog id="modal-{card_id}" style="border:none; border-radius:12px; padding:0; box-shadow:0 15px 40px rgba(0,0,0,0.25); max-width:95%; width:380px; overflow:hidden;">
        <div style="padding:20px; background:white;">
            <h3 style="margin:0 0 15px 0; font-size:1.1rem;">Update Task</h3>
            <p style="margin:0 0 15px 0; color:#555; font-size:0.95rem;">{name}</p>
            
            <form method="dialog" style="display:flex; flex-direction:column; gap:12px;">
                <label style="font-size:0.85rem; font-weight:500;">Status:</label>
                <select name="status" style="padding:10px; border-radius:8px; border:1px solid #ddd; font-size:0.95rem;">
                    <option value="PENDING" {'selected' if status=='PENDING' else ''}>📋 Planned</option>
                    <option value="MATERIAL_READY" {'selected' if status=='MATERIAL_READY' else ''}>📦 Mat. Ready</option>
                    <option value="ONGOING" {'selected' if status=='ONGOING' else ''}>🚧 In Progress</option>
                    <option value="DELAYED" {'selected' if status=='DELAYED' else ''}>⏳ Waiting</option>
                    <option value="DONE" {'selected' if status=='DONE' else ''}>✅ Done</option>
                </select>
                
                <label style="font-size:0.85rem; font-weight:500;">Actual End (if Done):</label>
                <input type="date" name="actual_end" value="{task.get('actual_end','')[:10] if task.get('actual_end') else ''}" style="padding:10px; border-radius:8px; border:1px solid #ddd; font-size:0.95rem;">
                
                <div style="display:flex; gap:10px; margin-top:15px;">
                    <button value="cancel" style="flex:1; padding:10px; background:#f0f2f6; border:none; border-radius:8px; cursor:pointer; font-weight:500;">Cancel</button>
                    <button value="save" style="flex:1; padding:10px; background:#0d6efd; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:500;">Save</button>
                </div>
            </form>
        </div>
    </dialog>
    """
    return html

# ─────────────────────────────────────────────────────────────
#  MAIN PAGE FUNCTION
# ─────────────────────────────────────────────────────────────

def kanban_page():
    inject_kanban_css()
    st.title("📋 Kanban Board")
    
    sites_df = read_sheet("projects")
    if sites_df.empty:
        st.warning("⚠️ Belum ada data site.")
        return
        
    site_options = ["ALL SITE"] + sites_df["id"].tolist()
    selected_site = st.selectbox(
        "🎯 Pilih Site:", site_options,
        format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE" 
        else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}"
    )
    is_all = (selected_site == "ALL SITE")
    
    ms_df = read_sheet("milestones")
    if ms_df.empty:
        st.info("ℹ️ Belum ada milestone.")
        return
        
    if not is_all:
        ms_df = ms_df[ms_df['project_id'] == selected_site].copy()
    if 'planned_end' in ms_df.columns:
        ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
        
    col_mapping = [
        ('PENDING', '📋 Planned'), ('MATERIAL_READY', '📦 Mat. Ready'),
        ('ONGOING', '🚧 In Progress'), ('DELAYED', '⏳ Waiting'), ('DONE', '✅ Done')
    ]
    
    cols = st.columns(5)
    for i, (status_key, col_name) in enumerate(col_mapping):
        with cols[i]:
            st.markdown(f"<h4 style='text-align:center; margin:0 0 15px 0; color:#333;'>{col_name}</h4>", unsafe_allow_html=True)
            tasks = ms_df[ms_df['status'] == status_key] if 'status' in ms_df.columns else pd.DataFrame()
            if not tasks.empty:
                for _, task in tasks.iterrows():
                    st.markdown(render_card(task), unsafe_allow_html=True)
    
    # Quick Update Section (Mobile Optimized)
    st.divider()
    st.markdown("### ✏️ Quick Update")
    
    if not ms_df.empty:
        ms_df['label'] = ms_df.apply(lambda x: f"{x['name']} ({x.get('status','?')}) - {x.get('assigned_to','?')}", axis=1)
        selected_label = st.selectbox("Pilih Task:", ms_df['label'].tolist(), index=0)
        task_row = ms_df[ms_df['label'] == selected_label].iloc[0]
        
        c1, c2 = st.columns(2)
        with c1:
            new_status = st.selectbox("Status Baru:", ['PENDING', 'MATERIAL_READY', 'ONGOING', 'DELAYED', 'DONE'],
                                      index=['PENDING', 'MATERIAL_READY', 'ONGOING', 'DELAYED', 'DONE'].index(task_row.get('status', 'PENDING')))
        with c2:
            new_actual = st.date_input("Actual End", value=None)
            
        if st.button("💾 Simpan & Sync", type="primary", use_container_width=True):
            update_data = {'status': new_status}
            if new_actual:
                from supabase_db import safe_date_string
                update_data['actual_end'] = safe_date_string(new_actual)
                
            if update_row("milestones", task_row['id'], update_data):
                # Auto Sync Progress
                try:
                    site_ms = read_sheet("milestones")
                    site_ms = site_ms[site_ms['project_id'] == selected_site].copy()
                    site_ms["weight"] = pd.to_numeric(site_ms["weight"], errors="coerce").fillna(0)
                    total_w = site_ms["weight"].sum()
                    done_w = site_ms[site_ms["status"]=="DONE"]["weight"].sum()
                    prog = round((done_w/total_w)*100, 1) if total_w > 0 else 0
                    delayed = len(site_ms[site_ms["status"]=="DELAYED"])
                    sts = "CRITICAL" if delayed > 3 else ("DELAYED" if delayed > 0 else "ON_TRACK")
                    update_row("projects", selected_site, {"progress": str(prog), "status": sts})
                    st.cache_data.clear()
                except: pass
                
                st.success("✅ Updated & Synced!")
                st.rerun()

if __name__ == "__main__":
    kanban_page()
