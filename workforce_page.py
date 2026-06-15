import streamlit as st
import pandas as pd
from datetime import date, datetime
from supabase_db import read_sheet, insert_row, update_row, delete_row_by_id, generate_id, now_str

def workforce_page():
    st.title("👷 Workforce Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Data Pekerja", "📋 Assignment", "📅 Attendance", "📊 Utilization"])
    
    wf_df = read_sheet("workforce")
    ms_df = read_sheet("milestones")
    sites_df = read_sheet("projects")
    assign_df = read_sheet("workforce_assignments")
    att_df = read_sheet("workforce_attendance")
    
    # ===== TAB 1: DATA PEKERJA =====
    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            if not wf_df.empty:
                st.metric("Total Workforce", len(wf_df))
                active = len(wf_df[wf_df['status']=='Active'])
                st.metric("✅ Active", active)
                
                # Filter status
                status_filter = st.selectbox("Filter Status:", ['All', 'Active', 'On Leave', 'Inactive'])
                display = wf_df.copy()
                if status_filter != 'All': display = display[display['status']==status_filter]
                st.dataframe(display[['name','role','skill','phone','status']], use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("➕ Tambah Pekerja")
            with st.form("add_worker"):
                name = st.text_input("Nama")
                role = st.selectbox("Role", ["Engineer","Technician","Rigger","Supervisor","Driver","Admin","Other"])
                skill = st.text_input("Skill", placeholder="Sipil, Tower, Fiber Optic")
                phone = st.text_input("Phone")
                email = st.text_input("Email")
                status = st.selectbox("Status", ["Active","On Leave","Inactive"])
                
                if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                    insert_row("workforce", {
                        'id': generate_id(), 'name': name, 'role': role,
                        'skill': skill, 'phone': phone, 'email': email, 'status': status
                    })
                    st.success(f"✅ {name} ditambahkan!"); st.rerun()
    
    # ===== TAB 2: ASSIGNMENT =====
    with tab2:
        st.subheader("📋 Assign Pekerja ke Milestone")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if not wf_df.empty:
                sel_worker = st.selectbox("👷 Pilih Pekerja:", wf_df['id'].tolist(),
                    format_func=lambda x: wf_df[wf_df['id']==x]['name'].values[0])
        with col_b:
            if not ms_df.empty:
                sel_ms = st.selectbox("📌 Pilih Milestone:", ms_df['id'].tolist(),
                    format_func=lambda x: ms_df[ms_df['id']==x]['name'].values[0][:50])
        
        if st.button("✅ Assign", type="primary"):
            insert_row("workforce_assignments", {
                'id': generate_id(), 'workforce_id': sel_worker,
                'milestone_id': sel_ms, 'assigned_date': date.today().strftime('%Y-%m-%d'),
                'status': 'Assigned'
            })
            st.success("✅ Assigned!"); st.rerun()
        
        st.divider()
        st.subheader("📋 Daftar Assignment")
        if not assign_df.empty:
            # Merge data
            wf_map = dict(zip(wf_df['id'], wf_df['name'])) if not wf_df.empty else {}
            ms_map = dict(zip(ms_df['id'], ms_df['name'])) if not ms_df.empty else {}
            assign_df['worker_name'] = assign_df['workforce_id'].map(wf_map)
            assign_df['task_name'] = assign_df['milestone_id'].map(ms_map)
            st.dataframe(assign_df[['worker_name','task_name','assigned_date','status']].tail(20), use_container_width=True, hide_index=True)
    
    # ===== TAB 3: ATTENDANCE =====
    with tab3:
        st.subheader("📅 Attendance Hari Ini")
        today = date.today().strftime('%Y-%m-%d')
        
        if not wf_df.empty:
            cols = st.columns(4)
            for i, (_, w) in enumerate(wf_df.iterrows()):
                with cols[i % 4]:
                    current_status = 'Not Set'
                        if not att_df.empty and 'workforce_id' in att_df.columns and 'date' in att_df.columns:
                            match = att_df[(att_df['workforce_id']==w['id']) & (att_df['date']==today)]
                            if not match.empty:
                                current_status = match['status'].values[0]
                    
                    color = {'Present':'#DCFCE7','Absent':'#FEE2E2','Leave':'#FEF3C7','Not Set':'#F8FAFC'}
                    st.markdown(f"""
                    <div style="background:{color.get(current_status,'#F8FAFC')}; padding:10px; border-radius:10px; text-align:center; margin:3px 0;">
                        <strong>{w['name']}</strong><br>
                        <small>{current_status}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("✅", key=f"p_{w['id']}"): 
                            insert_row("workforce_attendance", {'id':generate_id(),'workforce_id':w['id'],'date':today,'status':'Present'}); st.rerun()
                    with c2:
                        if st.button("❌", key=f"a_{w['id']}"): 
                            insert_row("workforce_attendance", {'id':generate_id(),'workforce_id':w['id'],'date':today,'status':'Absent'}); st.rerun()
                    with c3:
                        if st.button("🏖️", key=f"l_{w['id']}"): 
                            insert_row("workforce_attendance", {'id':generate_id(),'workforce_id':w['id'],'date':today,'status':'Leave'}); st.rerun()
    
    # ===== TAB 4: UTILIZATION =====
    with tab4:
        st.subheader("📊 Utilization Rate")
        
        if not wf_df.empty and not assign_df.empty:
            for _, w in wf_df.iterrows():
                total_assign = len(assign_df[assign_df['workforce_id']==w['id']])
                done_assign = len(assign_df[(assign_df['workforce_id']==w['id']) & (assign_df['status']=='Completed')])
                
                rate = (done_assign/total_assign*100) if total_assign > 0 else 0
                color = '#10B981' if rate>=80 else ('#F59E0B' if rate>=50 else '#EF4444')
                
                st.markdown(f"**{w['name']}** — {w['role']}")
                st.progress(rate/100)
                st.caption(f"{done_assign}/{total_assign} completed • {rate:.0f}%")
        else:
            st.info("Belum ada data assignment.")

if __name__ == "__main__":
    workforce_page()
