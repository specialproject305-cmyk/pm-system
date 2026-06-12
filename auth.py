import streamlit as st
from supabase_db import supabase

def check_login(username, password):
    try:
        res = supabase.table('users').select('*').eq('username', username).eq('password', password).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
    except:
        pass
    return None

def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center;">
            <h1>🏗️ PM System</h1>
            <p style="color: gray;">Project Management Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Masukkan username")
            password = st.text_input("🔒 Password", type="password", placeholder="Masukkan password")
            submit = st.form_submit_button("🔐 Login", type="primary", use_container_width=True)
            
            if submit:
                user = check_login(username, password)
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = user
                    
                    # AUTO-REDIRECT: PIC ke Field App, Admin/PM/PMO/Planning ke Dashboard
                    pic_roles = ['sitac', 'engineering', 'procurement', 'project', 'vendor_mgmt', 'legal']
                    if user.get('role') in pic_roles:
                        st.session_state['app_mode'] = '📱 Field App'
                    else:
                        st.session_state['app_mode'] = '🏢 Full Dashboard'
                        
                    st.success("✅ Login berhasil!")
                    st.rerun()
                else:
                    st.error("❌ Username atau password salah!")

def check_permission(required_role='viewer'):
    user = st.session_state.get('user', {})
    user_role = user.get('role', 'viewer')
    role_levels = {
        'admin': 5, 'pm': 4, 'pmo': 4, 'planning': 3,
        'marketing': 3,  # ← tambah
        'sitac': 2, 'engineering': 2, 'procurement': 2,
        'project': 2, 'vendor_mgmt': 2, 'legal': 2,
        'viewer': 1
    }
    required_level = role_levels.get(required_role, 1)
    user_level = role_levels.get(user_role, 1)
    return user_level >= required_level

def show_permission_denied():
    st.error("🔒 Anda tidak memiliki akses untuk fitur ini!")
