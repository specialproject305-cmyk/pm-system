import streamlit as st
import pandas as pd
from supabase_db import read_sheet, insert_row, update_row, find_row_by_id, generate_id, today_str, delete_row_by_id

def sync_progress_from_milestones(site_id):
    """Hitung progress dari milestones"""
    ms_df = read_sheet("milestones")
    if ms_df.empty:
        return 0, 'ON_TRACK'
    site_ms = ms_df[ms_df['project_id'] == site_id]
    if site_ms.empty:
        return 0, 'ON_TRACK'

    site_ms['weight'] = pd.to_numeric(site_ms['weight'], errors='coerce').fillna(0)
    total_weight = site_ms['weight'].sum()
    done_weight = site_ms[site_ms['status'] == 'DONE']['weight'].sum()
    progress = round((done_weight / total_weight) * 100, 1) if total_weight > 0 else 0

    delayed = len(site_ms[site_ms['status'] == 'DELAYED'])
    status = 'CRITICAL' if delayed > 3 else ('DELAYED' if delayed > 0 else 'ON_TRACK')

    return progress, status

def project_tracker_page():
    st.title("📁 Site Tracker")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Daftar Site", "➕ Tambah Site", "✏️ Edit Site", "🔗 Detail", "📥 Import CSV"
    ])

    # ─────────────────────────────────────────────────────────────
    # TAB 1: DAFTAR SITE
    # ─────────────────────────────────────────────────────────────
    with tab1:
        st.subheader("Daftar Site")
        df = read_sheet("projects")
        
        if not df.empty:
            if 'progress' in df.columns:
                df['progress'] = pd.to_numeric(df['progress'], errors='coerce').fillna(0)
            
            def color_status(val):
                if val == 'ON_TRACK': return 'background-color: #d4edda; font-weight: bold'
                elif val == 'DELAYED': return 'background-color: #fff3cd; font-weight: bold'
                elif val == 'CRITICAL': return 'background-color: #f8d7da; font-weight: bold'
                return ''
            
            display_cols = ['site_id', 'site_name', 'site_coordinate', 'vendor', 'pm',
                'start_date', 'end_date', 'start_date_actual', 'end_date_actual',
                'status', 'progress']
            display_df = df[[c for c in display_cols if c in df.columns]]
            styled = display_df.style.map(color_status, subset=['status']) if 'status' in df.columns else display_df
            st.dataframe(styled, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Site", len(df))
            col2.metric("On Track", len(df[df['status']=='ON_TRACK']) if 'status' in df.columns else 0)
            col3.metric("Terlambat", len(df[df['status'].isin(['DELAYED','CRITICAL'])]) if 'status' in df.columns else 0)
            
            if st.button("🔄 Sync Progress dari Milestones", use_container_width=True):
                for _, row in df.iterrows():
                    prog, sts = sync_progress_from_milestones(row['id'])
                    ridx = find_row_by_id("projects", row['id'])
                    if ridx:
                        update_row("projects", ridx, {'progress': str(prog), 'status': sts})
                st.cache_data.clear()
                st.success("✅ Semua site di-sync!")
                st.rerun()
        else:
            st.info("📋 Belum ada site.")

    # ─────────────────────────────────────────────────────────────
    # TAB 2: TAMBAH SITE
    # ─────────────────────────────────────────────────────────────
    with tab2:
        st.subheader("Tambah Site Baru")
        with st.form("add_site"):
            site_id = st.text_input("Site ID", placeholder="SITE-001")
            site_name = st.text_input("Site Name", placeholder="Tower Gambir")
            site_coordinate = st.text_input("Koordinat", placeholder="-6.1754, 106.8272")
            vendor = st.text_input("Vendor")
            pm = st.text_input("PM")
            c1, c2 = st.columns(2)
            with c1: start_date = st.date_input("Plan Start")
            with c2: end_date = st.date_input("Plan End")
            
            if st.form_submit_button("💾 Simpan", type="primary", use_container_width=True):
                if not site_name or not site_id:
                    st.error("❌ Site ID dan Site Name wajib diisi!")
                else:
                    # Cek duplikat site_id
                    existing = read_sheet("projects")
                    if not existing.empty and site_id in existing['site_id'].values:
                        st.error(f"❌ Site ID '{site_id}' sudah ada!")
                    else:
                        insert_row("projects", {
                            'id': generate_id(), 'site_id': site_id, 'site_name': site_name,
                            'site_coordinate': site_coordinate, 'vendor': vendor, 'pm': pm,
                            'start_date': start_date.strftime('%Y-%m-%d'),
                            'end_date': end_date.strftime('%Y-%m-%d'),
                            'status': 'ON_TRACK', 'progress': '0'
                        })
                        st.success(f"✅ Site {site_name} ditambahkan!")
                        st.rerun()

    # ─────────────────────────────────────────────────────────────
    # TAB 3: EDIT & HAPUS SITE
    # ─────────────────────────────────────────────────────────────
    with tab3:
        st.subheader("✏️ Edit Data Site")
        df = read_sheet("projects")
        if not df.empty:
            selected = st.selectbox("Pilih Site untuk Edit:", df['id'].tolist(),
                                   format_func=lambda x: f"{df[df['id']==x]['site_id'].values[0]} - {df[df['id']==x]['site_name'].values[0]}")
            if selected:
                site = df[df['id']==selected].iloc[0]
                ridx = find_row_by_id("projects", selected)
                with st.form("edit_site"):
                    new_status = st.selectbox("Status", ["ON_TRACK", "DELAYED", "CRITICAL"],
                                             index=["ON_TRACK", "DELAYED", "CRITICAL"].index(site.get('status','ON_TRACK')) if site.get('status') in ["ON_TRACK", "DELAYED", "CRITICAL"] else 0)
                    new_progress = st.slider("Progress (%)", 0, 100, int(float(site.get('progress',0))) if site.get('progress') else 0)
                    if st.form_submit_button("💾 Update", use_container_width=True):
                        update_row("projects", ridx, {'status': new_status, 'progress': str(new_progress)})
                        st.success("✅ Site diupdate!")
                        st.rerun()

        # 🗑️ BAGIAN HAPUS SITE (DIPISAHKAN AGAR AMAN)
        st.divider()
        st.subheader("🗑️ Hapus Site Permanen")
        st.markdown("⚠️ **Peringatan:** Menghapus site akan menghapus **semua data terkait** (Milestones, Chat, Transaksi Inventory). Tindakan ini **tidak dapat dibatalkan**.")
        
        if not df.empty:
            sel_del = st.selectbox("Pilih Site yang akan dihapus:", df['id'].tolist(),
                                  format_func=lambda x: f"{df[df['id']==x]['site_id'].values[0]} - {df[df['id']==x]['site_name'].values[0]}",
                                  key="del_select")
            
            if sel_del:
                site_del = df[df['id']==sel_del].iloc[0]
                st.info(f"📝 Site terpilih: **{site_del.get('site_name','?')}** (`{site_del.get('site_id','?')}`)")
                
                # Hitung data terkait
                ms_df = read_sheet("milestones")
                chat_df = read_sheet("chat_messages")
                inv_df = read_sheet("inventory_transactions")
                
                ms_count = len(ms_df[ms_df['project_id'] == sel_del]) if not ms_df.empty else 0
                chat_count = len(chat_df[chat_df['site_id'] == sel_del]) if not chat_df.empty else 0
                inv_count = len(inv_df[inv_df['project_id'] == sel_del]) if not inv_df.empty else 0
                
                st.markdown(f"**Data yang akan ikut terhapus:**")
                col_d1, col_d2, col_d3 = st.columns(3)
                col_d1.metric("🧱 Milestones", ms_count)
                col_d2.metric("💬 Chat", chat_count)
                col_d3.metric("📦 Transaksi", inv_count)
                
                confirm_del = st.checkbox("✅ Saya yakin ingin menghapus site ini beserta semua data terkaitnya secara permanen.")
                
                if st.button("🗑️ HAPUS PERMANEN", type="primary", disabled=not confirm_del, use_container_width=True):
                    try:
                        with st.spinner("🔄 Menghapus data terkait & site..."):
                            # 1. Hapus Milestones
                            if ms_count > 0:
                                for mid in ms_df[ms_df['project_id'] == sel_del]['id'].tolist():
                                    delete_row_by_id("milestones", mid)
                            
                            # 2. Hapus Chat Messages
                            if chat_count > 0:
                                for cid in chat_df[chat_df['site_id'] == sel_del]['id'].tolist():
                                    delete_row_by_id("chat_messages", cid)
                                    
                            # 3. Hapus Inventory Transactions
                            if inv_count > 0:
                                for iid in inv_df[inv_df['project_id'] == sel_del]['id'].tolist():
                                    delete_row_by_id("inventory_transactions", iid)
                            
                            # 4. Hapus Site Induk
                            ridx_del = find_row_by_id("projects", sel_del)
                            if ridx_del:
                                delete_row_by_id("projects", sel_del)
                            
                            st.cache_data.clear()
                            st.success("✅ Site & semua data terkait berhasil dihapus permanen!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal menghapus: {str(e)}")
        else:
            st.info("Belum ada site untuk dihapus.")

    # ─────────────────────────────────────────────────────────────
    # TAB 4: DETAIL SITE
    # ─────────────────────────────────────────────────────────────
    with tab4:
        st.subheader("Detail Site & Milestone")
        df = read_sheet("projects")
        if not df.empty:
            selected = st.selectbox("Pilih Site:", df['id'].tolist(),
                                   format_func=lambda x: f"{df[df['id']==x]['site_id'].values[0]} - {df[df['id']==x]['site_name'].values[0]}",
                                   key="detail_select")
            if selected:
                site = df[df['id']==selected].iloc[0]
                col1, col2, col3 = st.columns(3)
                col1.metric("Site ID", site.get('site_id','-'))
                col2.metric("Status", site.get('status','-'))
                col3.metric("Progress", f"{site.get('progress','0')}%")
                
                ms_df = read_sheet("milestones")
                if not ms_df.empty:
                    site_ms = ms_df[ms_df['project_id'] == selected]
                    if not site_ms.empty:
                        st.markdown("**Milestones:**")
                        st.dataframe(site_ms[['name','status','planned_end','material_status']], use_container_width=True)

    # ─────────────────────────────────────────────────────────────
    # TAB 5: IMPORT CSV
    # ─────────────────────────────────────────────────────────────
    with tab5:
        st.subheader("Import Site via CSV")
        template = pd.DataFrame({
            'site_id': ['SITE-001'], 'site_name': ['Tower A'], 'site_coordinate': ['-6.17,106.82'],
            'vendor': ['PT. X'], 'pm': ['Budi'], 'start_date': [today_str()], 'end_date': [today_str()]
        })
        st.download_button("📥 Download Template", template.to_csv(index=False), "template_site.csv", "text/csv")
        
        up = st.file_uploader("Upload CSV", type=['csv'], key="site_csv")
        if up:
            idf = pd.read_csv(up)
            st.dataframe(idf.head())
            if st.button("🚀 Import", type="primary", use_container_width=True):
                count = 0
                skipped = 0
                existing_df = read_sheet("projects")
                
                for _, r in idf.iterrows():
                    site_id = str(r.get('site_id',''))
                    if not existing_df.empty and site_id in existing_df['site_id'].values:
                        skipped += 1
                        continue
                    
                    try:
                        insert_row("projects", {
                            'id': generate_id(), 'site_id': site_id,
                            'site_name': str(r.get('site_name','')), 'site_coordinate': str(r.get('site_coordinate','')),
                            'vendor': str(r.get('vendor','')), 'pm': str(r.get('pm','')),
                            'start_date': str(r.get('start_date', today_str())),
                            'end_date': str(r.get('end_date', today_str())),
                            'status': 'ON_TRACK', 'progress': '0'
                        })
                        count += 1
                    except:
                        pass
                
                st.success(f"✅ {count} site berhasil diimport!")
                if skipped > 0:
                    st.warning(f"⏭️ {skipped} site dilewati (duplikat)")
                st.rerun()

if __name__ == "__main__":
    project_tracker_page()
