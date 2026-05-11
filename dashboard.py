import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from supabase_db import read_all_sheets, read_sheet
import time
import io

# ─────────────────────────────────────────────────────────────
# 🎨 THEME & MOBILE CSS
# ─────────────────────────────────────────────────────────────

THEMES = {
    "Professional": {"primary": "#667eea", "secondary": "#764ba2", "success": "#28a745", "warning": "#ffc107", "danger": "#dc3545", "info": "#17a2b8", "bg": "#f8f9fa"},
    "Ocean": {"primary": "#1e3c72", "secondary": "#2a5298", "success": "#00b894", "warning": "#fdcb6e", "danger": "#d63031", "info": "#0984e3", "bg": "#dfe6e9"},
    "Sunset": {"primary": "#fa709a", "secondary": "#fee140", "success": "#00b894", "warning": "#fdcb6e", "danger": "#d63031", "info": "#74b9ff", "bg": "#fff5f5"},
    "Dark Mode": {"primary": "#a29bfe", "secondary": "#6c5ce7", "success": "#55efc4", "warning": "#ffeaa7", "danger": "#ff7675", "info": "#74b9ff", "bg": "#2d3436"}
}

def inject_custom_css(theme_name="Professional"):
    theme = THEMES[theme_name]
    st.markdown(f"""
    <style>
    /* Global Font */
    * {{ font-family: 'Inter', sans-serif; }}
    
    /* --- MOBILE OPTIMIZATION START --- */
    @media (max-width: 768px) {{
        /* Stack columns vertically on mobile */
        .stColumn {{ width: 100% !important; margin-bottom: 10px; }}
        
        /* Larger touch targets for buttons/inputs */
        button, input, select, textarea {{ min-height: 44px !important; font-size: 16px !important; }}
        
        /* Adjust Header for Mobile */
        .header-container {{ padding: 1rem !important; flex-direction: column !important; text-align: center; }}
        .header-container h1 {{ font-size: 1.5rem !important; white-space: normal !important; }}
        .clock-widget {{ margin-top: 10px; width: 100%; }}
        
        /* KPI Cards Full Width */
        .kpi-card {{ padding: 15px !important; margin-bottom: 10px !important; }}
        .kpi-card div[style*="font-size: 42px"] {{ font-size: 28px !important; }}
        .kpi-card div[style*="font-size: 48px"] {{ font-size: 32px !important; }}
        
        /* Chart Height Adjustment for Mobile */
        .chart-container {{ padding: 10px !important; }}
    }}
    /* --- MOBILE OPTIMIZATION END --- */

    /* Desktop Styles */
    .stApp {{ background: linear-gradient(135deg, {theme['bg']} 0%, #ffffff 100%); }}
    .header-container {{ background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%); padding: 2rem; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.15); margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; }}
    .kpi-card {{ background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%); padding: 25px; border-radius: 20px; color: white; text-align: center; box-shadow: 0 8px 30px rgba(0,0,0,0.12); transition: transform 0.3s; }}
    .kpi-card:hover {{ transform: translateY(-5px); }}
    .chart-container {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 2rem; }}
    .filter-container {{ background: white; padding: 15px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 1rem; }}
    .last-update-badge {{ background: rgba(255,255,255,0.95); padding: 8px 15px; border-radius: 20px; font-size: 12px; font-weight: 600; color: {theme['primary']}; box-shadow: 0 2px 10px rgba(0,0,0,0.1); display: inline-flex; align-items: center; gap: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 📊 CHART FUNCTIONS (Adjusted Height for Mobile)
# ─────────────────────────────────────────────────────────────

def create_interactive_progress_chart(filtered, theme):
    if filtered.empty or 'site_id' not in filtered.columns: return None
    colors = [theme['success'] if s.get('status') == 'ON_TRACK' else (theme['warning'] if s.get('status') == 'DELAYED' else theme['danger']) for _, s in filtered.iterrows()]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=filtered['site_id'], x=filtered['progress'], orientation='h', marker=dict(color=colors), text=filtered['progress'].apply(lambda x: f'{x:.0f}%'), textposition='outside'))
    fig.update_layout(height=max(300, len(filtered)*40), xaxis=dict(range=[0, 105]), margin=dict(l=10, r=10, t=20, b=10), showlegend=False)
    return fig

def create_s_curve_with_targets(filtered, theme):
    if filtered.empty or 'progress' not in filtered.columns: return None
    total = len(filtered)
    m_labels = ['0%', '25%', '50%', '75%', '100%']
    thresholds = [0, 25, 50, 75, 100]
    actual_values = [(len(filtered[filtered['progress'] >= t]) / total * 100) if total > 0 else 0 for t in thresholds]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m_labels, y=actual_values, mode='lines+markers', line=dict(color=theme['primary'], width=3), marker=dict(size=8)))
    fig.update_layout(height=300, yaxis=dict(range=[0, 105]), margin=dict(l=10, r=10, t=20, b=10))
    return fig

def create_material_comparison_chart(materials_df, theme):
    if materials_df.empty or 'name' not in materials_df.columns: return None
    mat_disp = materials_df.head(10).copy() # Show fewer items on mobile
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Stok', y=mat_disp['name'], x=mat_disp['current_stock'], orientation='h', marker=dict(color=theme['success'])))
    if 'min_stock' in mat_disp.columns:
        fig.add_trace(go.Bar(name='Min', y=mat_disp['name'], x=mat_disp['min_stock'], orientation='h', marker=dict(color=theme['danger'], opacity=0.5)))
    fig.update_layout(height=max(300, len(mat_disp)*35), barmode='group', margin=dict(l=10, r=10, t=20, b=10))
    return fig

def export_to_excel(df, materials_df, milestones_df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Projects', index=False)
        materials_df.to_excel(writer, sheet_name='Materials', index=False)
        milestones_df.to_excel(writer, sheet_name='Milestones', index=False)
    output.seek(0)
    return output.getvalue()

# ─────────────────────────────────────────────────────────────
# 🎯 MAIN DASHBOARD FUNCTION
# ─────────────────────────────────────────────────────────────

def dashboard_page():
    if 'theme' not in st.session_state: st.session_state.theme = "Professional"
    if 'last_refresh' not in st.session_state: st.session_state.last_refresh = datetime.now()
    inject_custom_css(st.session_state.theme)
    
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        selected_theme = st.selectbox("🎨 Theme", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme))
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()
        st.divider()
        st.markdown(f"<div class='last-update-badge'>🕐 Update: {st.session_state.last_refresh.strftime('%H:%M')}</div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.session_state.last_refresh = datetime.now()
            st.rerun()

    now = datetime.now()
    
    # Responsive Header
    st.markdown(f"""
    <div class='header-container'>
        <div style='flex: 1;'>
            <h1 style='margin:0; color:white; font-size:2rem;'>👷 Dashboard Project</h1>
            <p style='margin:5px 0 0 0; color:rgba(255,255,255,0.9);'>Real-time Monitoring</p>
        </div>
        <div class='clock-widget' style='background: rgba(255,255,255,0.2); padding: 10px 20px; border-radius: 10px; text-align: center; color: white;'>
            <div style='font-size: 1.2rem; font-weight: bold;'>{now.strftime('%H:%M:%S')}</div>
            <div style='font-size: 0.8rem;'>{now.strftime('%d %b %Y')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        all_data = read_all_sheets()
        st.session_state.last_refresh = datetime.now()
    except Exception as e:
        st.error(f"⚠️ Gagal load data: {str(e)[:50]}")
        return

    df = all_data.get('projects', pd.DataFrame())
    if df.empty: df = read_sheet("projects")
    materials_df = all_data.get('materials', pd.DataFrame())
    milestones_df = all_data.get('milestones', pd.DataFrame())

    # Filters
    st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        pm_list = df['pm'].dropna().unique().tolist() if not df.empty and 'pm' in df.columns else []
        filter_pm = st.multiselect("👤 Filter PM", pm_list, placeholder="Semua PM")
    with col_f2:
        vendor_list = df['vendor'].dropna().unique().tolist() if not df.empty and 'vendor' in df.columns else []
        filter_vendor = st.multiselect("🏢 Filter Vendor", vendor_list, placeholder="Semua Vendor")
    st.markdown("</div>", unsafe_allow_html=True)

    filtered = df.copy()
    if not filtered.empty:
        if filter_pm and 'pm' in filtered.columns: filtered = filtered[filtered['pm'].isin(filter_pm)]
        if filter_vendor and 'vendor' in filtered.columns: filtered = filtered[filtered['vendor'].isin(filter_vendor)]

    # KPI Cards
    total_sites = len(filtered)
    avg_progress = filtered['progress'].mean() if not filtered.empty and 'progress' in filtered.columns else 0
    delayed_sites = len(filtered[filtered['status'].isin(['DELAYED','CRITICAL'])]) if not filtered.empty and 'status' in filtered.columns else 0
    
    theme = THEMES[st.session_state.theme]
    cols = st.columns(4) 
    metrics = [
        ("📁 Total", total_sites, theme['primary']),
        ("📈 Progress", f"{avg_progress:.1f}%", theme['success'] if avg_progress >= 70 else theme['warning']),
        ("⚠️ Delayed", delayed_sites, theme['danger']),
        ("🔴 Critical", len(filtered[filtered['status']=='CRITICAL']) if not filtered.empty and 'status' in filtered.columns else 0, theme['danger'])
    ]
    
    for i, (label, value, color) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
            <div class='kpi-card' style='background: linear-gradient(135deg, {color} 0%, #000 100%);'>
                <div style='font-size: 1.5rem; font-weight: bold;'>{value}</div>
                <div style='font-size: 0.8rem; opacity: 0.9;'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

    # Charts
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("📊 Progress per Site")
        if not filtered.empty:
            fig = create_interactive_progress_chart(filtered, theme)
            if fig: st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("📈 S-Curve")
        if not filtered.empty:
            fig = create_s_curve_with_targets(filtered, theme)
            if fig: st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.subheader("📦 Material Stock")
    if not materials_df.empty:
        fig = create_material_comparison_chart(materials_df, theme)
        if fig: st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    dashboard_page()
