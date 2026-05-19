import streamlit as st
import pandas as pd
from supabase_db import read_sheet, insert_row, update_row, delete_row_by_id, generate_id

def user_management_page():
    st.title("👥 User Management")
    st.caption("Kelola user, password, role, dan akses")
    
    users_df = read_sheet("users")
    
    tab1, tab2 = st.tabs(["📋 Daftar User", "➕ Tambah User"])
    
    with tab1:
        if not users_df.empty:
            st.dataframe(users_df[['username', 'role', 'full_name']], use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("✏️ Edit / Hapus User")
            sel_user = st.selectbox("Pilih User:", users_df['id'].tolist(),
                format_func=lambda x: f"{users_df[users_df['id']==x]['username'].values[0]} ({users_df[users_df['id']==x]['role'].values[0]})")
            
            if sel_user:
                u = users_df[users_df['id']==sel_user].iloc[0]
                with st.form("edit_user"):
                    e_username = st.text_input("Username", value=u['username'])
                    e_password = st.text_input("Password", value=u['password'], type="password")
                    e_fullname = st.text_input("Nama Lengkap", value=u.get('full_name',''))
                    e_role = st.selectbox("Role", ["admin", "editor", "viewer", "engineer"], 
                        index=["admin","editor","viewer","engineer"].index(u.get('role','viewer')) if u.get('role') in ["admin","editor","viewer","engineer"] else 0)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Update"):
                            update_row("users", sel_user, {
                                'username': e_username, 'password': e_password,
                                'full_name': e_fullname, 'role': e_role
                            })
                            st.success("✅ Updated!"); st.rerun()
                    with col2:
                        if st.form_submit_button("🗑️ Hapus", type="secondary"):
                            delete_row_by_id("users", sel_user)
                            st.warning("🗑️ Deleted!"); st.rerun()
    
    with tab2:
        with st.form("add_user"):
            st.subheader("➕ Tambah User Baru")
            n_username = st.text_input("Username")
            n_password = st.text_input("Password", type="password")
            n_fullname = st.text_input("Nama Lengkap")
            n_role = st.selectbox("Role", ["admin", "editor", "viewer", "engineer"],
                help="admin=Full | editor=CRUD | viewer=Read | engineer=Field App")
            
            st.markdown("---")
            st.markdown("**🔑 Role Access:**")
            st.markdown("""
            - **admin**: Semua akses + Settings + User Management
            - **editor**: Dashboard, CRUD, AI, Chat, Daily Tasks, Field App
            - **viewer**: Dashboard, AI Insights, Chat, Presentation
            - **engineer**: Dashboard, Field App, Daily Tasks, Chat (mode simpel)
            """)
            
            if st.form_submit_button("💾 Tambah User", type="primary"):
                if n_username and n_password:
                    insert_row("users", {
                        'id': generate_id(),
                        'username': n_username,
                        'password': n_password,
                        'full_name': n_fullname,
                        'role': n_role
                    })
                    st.success(f"✅ User {n_username} ditambahkan!"); st.rerun()
                else:
                    st.error("❌ Username & password wajib!")

if __name__ == "__main__":
    user_management_page()
