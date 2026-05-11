import streamlit as st
import pandas as pd
from datetime import datetime
from supabase_db import read_sheet, update_row, delete_row_by_id

# ─────────────────────────────────────────────────────────────
# 🎨 CSS FOR KANBAN & MOBILE OPTIMIZATION
# ─────────────────────────────────────────────────────────────

def inject_kanban_css():
    st.markdown("""
    <style>
    /* Kanban Board Styles */
    .kanban-column {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        min-height: 400px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    
    .kanban-card {
        background-color: white;
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        border-left: 5px solid #ccc;
    }
    
    .kanban-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.15);
    }
    
    /* Status Colors for Border Left */
    .border-pending { border-left-color: #6c757d !important; } /* Gray - Planned */
    .border-material { border-left-color: #fd7e14 !important; } /* Orange - Mat. Ready */
    .border-ongoing { border-left-color: #0d6efd !important; } /* Blue - In Progress */
    .border-delayed { border-left-color: #dc3545 !important; } /* Red - Waiting */
    .border-done { border-left-color: #28a745 !important; } /* Green - Done */

    /* Card Content */
    .card-title { font-weight: bold; font-size: 0.9rem; margin-bottom: 5px; }
    .card-meta { font-size: 0.75rem; color: #666; display: flex; justify-content: space-between; }
    .card-sla { font-weight: bold; }
    .sla-ok { color: green; }
    .sla-warn { color: orange; }
    .sla-breach { color: red; }

    /* Mobile Optimization for Kanban */
    @media (max-width: 768px) {
        .kanban-column {
            min-height: auto;
            margin-bottom: 20px;
        }
        .stColumn {
            width: 100% !important; /* Stack columns vertically on mobile */
        }
        .kanban-card {
            padding: 15px; /* Larger touch target */
        }
        .card-title { font-size: 1rem; }
    }
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 🛠️ HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def get_status_color(status):
    """Map status to CSS class for border color."""
    mapping = {
        'PENDING': 'border-pending',
        'MATERIAL_READY': 'border-material',
        'ONGOING': 'border-ongoing',
        'DELAYED': 'border-delayed',
        'DONE': 'border-done'
    }
    return mapping.get(status, 'border-pending')

def get_sla_class(planned_end, status):
    """Determine SLA status color."""
    if status == 'DONE':
        return 'sla-ok'
    if not planned_end or pd.isna(planned_end):
        return ''
    
    today = datetime.now().date()
    end_date = planned_end.date() if hasattr(planned_end, 'date') else pd.to_datetime(planned_end).date()
    
    days_left = (end_date - today).days
    
    if days_left < 0:
        return 'sla-breach'
    elif days_left <= 3:
        return 'sla-warn'
    else:
        return 'sla-ok'

def render_card(task):
    """Render a single Kanban card HTML with safe value handling."""
    status = task.get('status', 'PENDING')
    border_class = get_status_color(status)
    
    name = task.get('name', 'No Name')
    assigned = task.get('assigned_to', '-')
    sla_days = task.get('sla_days', '-')
    planned_end = task.get('planned_end')
    
    # Determine SLA Color
    sla_class = get_sla_class(planned_end, status)
    sla_text = f"{sla_days} Days" if sla_days != '-' else '-'
    
    # Create unique key for modal trigger
    card_id = str(task.get('id')) # Pastikan ID adalah string
    
    # Safe handling for actual_end date value
    actual_end_val = task.get('actual_end', '')
    if actual_end_val and pd.notna(actual_end_val):
        # Jika sudah string, ambil 10 karakter pertama (YYYY-MM-DD)
        if isinstance(actual_end_val, str):
            actual_end_str = actual_end_val[:10]
        else:
            # Jika objek datetime, convert ke string
            try:
                actual_end_str = pd.to_datetime(actual_end_val).strftime('%Y-%m-%d')
            except:
                actual_end_str = ''
    else:
        actual_end_str = ''

    html = f"""
    <div class="kanban-card {border_class}" onclick="document.getElementById('modal-{card_id}').showModal()">
        <div class="card-title">{name}</div>
        <div class="card-meta">
            <span>👤 {assigned}</span>
            <span class="card-sla {sla_class}">⏳ {sla_text}</span>
        </div>
    </div>
    
    <!-- Hidden Modal for Editing -->
    <dialog id="modal-{card_id}" style="border:none; border-radius:10px; padding:0; box-shadow:0 10px 25px rgba(0,0,0,0.2); max-width:90%; width:400px;">
        <div style="padding:20px; background:white; border-radius:10px;">
            <h3 style="margin-top:0;">Update Task</h3>
            <p><strong>{name}</strong></p>
            
            <form method="dialog" style="display:flex; flex-direction:column; gap:10px;">
                <label>Status:</label>
                <select name="status" style="padding:10px; border-radius:5px; border:1px solid #ccc;">
                    <option value="PENDING" {'selected' if status=='PENDING' else ''}>📋 Planned</option>
                    <option value="MATERIAL_READY" {'selected' if status=='MATERIAL_READY' else ''}>📦 Material Ready</option>
                    <option value="ONGOING" {'selected' if status=='ONGOING' else ''}>🚧 In Progress</option>
                    <option value="DELAYED" {'selected' if status=='DELAYED' else ''}>⏳ Waiting/Blocked</option>
                    <option value="DONE" {'selected' if status=='DONE' else ''}>✅ Done</option>
                </select>
                
                <label>Actual End Date (if Done):</label>
                <input type="date" name="actual_end" value="{actual_end_str}" style="padding:10px; border-radius:5px; border:1px solid #ccc;">
                
                <div style="display:flex; gap:10px; margin-top:10px;">
                    <button value="cancel" style="flex:1; padding:10px; background:#eee; border:none; border-radius:5px; cursor:pointer;">Cancel</button>
                    <button value="save" style="flex:1; padding:10px; background:#0d6efd; color:white; border:none; border-radius:5px; cursor:pointer;">Save</button>
                </div>
            </form>
        </div>
    </dialog>
    """
    return html

# ─────────────────────────────────────────────────────────────
# 🎯 MAIN PAGE FUNCTION
# ─────────────────────────────────────────────────────────────

def kanban_page():
    inject_kanban_css()
    
    st.title("📋 Kanban Board")
    
    # Filter Site
    sites_df = read_sheet("projects")
    if sites_df.empty:
        st.warning("⚠️ Belum ada data site. Silakan tambah site di Project Tracker.")
        return
        
    site_options = ["ALL SITE"] + sites_df["id"].tolist()
    selected_site = st.selectbox(
        "🎯 Pilih Site:", 
        site_options,
        format_func=lambda x: "🌍 ALL SITE" if x == "ALL SITE" 
        else f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}"
    )
    
    is_all = (selected_site == "ALL SITE")
    
    # Load Milestones
    ms_df = read_sheet("milestones")
    if ms_df.empty:
        st.info("ℹ️ Belum ada milestone. Generate template di menu Milestone Monitoring.")
        return
        
    # Filter by Site
    if not is_all:
        ms_df = ms_df[ms_df['project_id'] == selected_site].copy()
        
    # Convert Dates
    if 'planned_end' in ms_df.columns:
        ms_df['planned_end'] = pd.to_datetime(ms_df['planned_end'], errors='coerce')
        
    # Define Columns Mapping - URUTAN BARU SESUAI PERMINTAAN
    col_mapping = [
        ('PENDING', '📋 Planned'),
        ('MATERIAL_READY', '📦 Mat. Ready'),
        ('ONGOING', '🚧 In Progress'),
        ('DELAYED', '⏳ Waiting'),
        ('DONE', '✅ Done')
    ]
    
    # Render Kanban Columns
    # On Desktop: 5 columns side-by-side. On Mobile: Stacked via CSS.
    cols = st.columns(5)
    
    for i, (status_key, col_name) in enumerate(col_mapping):
        with cols[i]:
            st.markdown(f"<h4 style='text-align:center; border-bottom:2px solid #ddd; padding-bottom:10px;'>{col_name}</h4>", unsafe_allow_html=True)
            
            # Filter tasks for this column
            if 'status' in ms_df.columns:
                tasks = ms_df[ms_df['status'] == status_key]
            else:
                tasks = pd.DataFrame()
                    
            # Render Cards
            if not tasks.empty:
                for _, task in tasks.iterrows():
                    card_html = render_card(task)
                    st.markdown(card_html, unsafe_allow_html=True)
    
    # --- SECTION UNTUK UPDATE STATUS (Mobile Friendly) ---
    st.divider()
    st.markdown("### ✏️ Update Task Status")
    st.info("💡 Pilih task di bawah untuk mengubah statusnya.")
    
    # Select Task to Edit
    if not ms_df.empty:
        # Create a readable label for selectbox
        ms_df['label'] = ms_df.apply(lambda x: f"{x['name']} ({x.get('status','?')}) - {x.get('assigned_to','?')}", axis=1)
        
        selected_task_label = st.selectbox(
            "Pilih Task untuk Update:",
            ms_df['label'].tolist(),
            index=0
        )
        
        # Get original ID from label
        selected_task_row = ms_df[ms_df['label'] == selected_task_label].iloc[0]
        task_id = selected_task_row['id']
        
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            new_status = st.selectbox(
                "Ubah Status Ke:",
                ['PENDING', 'MATERIAL_READY', 'ONGOING', 'DELAYED', 'DONE'],
                index=['PENDING', 'MATERIAL_READY', 'ONGOING', 'DELAYED', 'DONE'].index(selected_task_row.get('status', 'PENDING'))
            )
        with col_e2:
            new_actual_end = st.date_input(
                "Actual End Date (Opsional)",
                value=None,
                help="Isi jika status diubah ke DONE"
            )
            
        if st.button("💾 Simpan Perubahan", type="primary", use_container_width=True):
            update_data = {'status': new_status}
            if new_actual_end:
                from supabase_db import safe_date_string
                update_data['actual_end'] = safe_date_string(new_actual_end)
                
            success = update_row("milestones", task_id, update_data)
            if success:
                st.success("✅ Status berhasil diupdate!")
                st.rerun()
            else:
                st.error("❌ Gagal update status.")

if __name__ == "__main__":
    kanban_page()
