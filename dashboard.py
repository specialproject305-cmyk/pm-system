import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from supabase_db import read_all_sheets, read_sheet
import time
import json

# ─────────────────────────────────────────────────────────────
# 🎨 THEME CONFIGURATION
# ─────────────────────────────────────────────────────────────

THEMES = {
    "Professional": {
        "primary": "#667eea",
        "secondary": "#764ba2",
        "success": "#28a745",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "info": "#17a2b8",
        "bg": "#f8f9fa"
    },
    "Ocean": {
        "primary": "#1e3c72",
        "secondary": "#2a5298",
        "success": "#00b894",
        "warning": "#fdcb6e",
        "danger": "#d63031",
        "info": "#0984e3",
        "bg": "#dfe6e9"
    },
    "Sunset": {
        "primary": "#fa709a",
        "secondary": "#fee140",
        "success": "#00b894",
        "warning": "#fdcb6e",
        "danger": "#d63031",
        "info": "#74b9ff",
        "bg": "#fff5f5"
    },
    "Dark Mode": {
        "primary": "#a29bfe",
        "secondary": "#6c5ce7",
        "success": "#55efc4",
        "warning": "#ffeaa7",
        "danger": "#ff7675",
        "info": "#74b9ff",
        "bg": "#2d3436"
    }
}

# ─────────────────────────────────────────────────────────────
# 💅 CUSTOM CSS WITH ANIMATIONS
# ─────────────────────────────────────────────────────────────

def inject_custom_css(theme_name="Professional"):
    theme = THEMES[theme_name]
    
    st.markdown(f"""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles */
    * {{
        font-family: 'Inter', sans-serif;
    }}
    
    .stApp {{
        background: linear-gradient(135deg, {theme['bg']} 0%, #ffffff 100%);
    }}
    
    /* Animated Header */
    .header-container {{
        background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        margin-bottom: 2rem;
        animation: slideDown 0.6s ease-out;
    }}
    
    @keyframes slideDown {{
        from {{ opacity: 0; transform: translateY(-30px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* Enhanced Clock */
    .clock-widget {{
        background: rgba(255,255,255,0.15);
        backdrop-filter: blur(10px);
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        color: white;
        border: 1px solid rgba(255,255,255,0.2);
        transition: transform 0.3s ease;
    }}
    
    .clock-widget:hover {{
        transform: scale(1.05);
    }}
    
    /* Animated KPI Cards */
    .kpi-card {{
        background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%);
        padding: 25px;
        border-radius: 20px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        animation: fadeInUp 0.6s ease-out;
        position: relative;
        overflow: hidden;
    }}
    
    .kpi-card::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        transform: rotate(45deg);
        transition: all 0.6s;
    }}
    
    .kpi-card:hover::before {{
        left: 100%;
    }}
    
    .kpi-card:hover {{
        transform: translateY(-10px) scale(1.02);
        box-shadow: 0 15px 50px rgba(0,0,0,0.2);
    }}
    
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(30px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* Interactive Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%);
        color: white;
        border: none;
        padding: 10px 25px;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }}
    
    /* Filter Container */
    .filter-container {{
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
        animation: slideIn 0.5s ease-out;
    }}
    
    @keyframes slideIn {{
        from {{ opacity: 0; transform: translateX(-20px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}
    
    /* Chart Container */
    .chart-container {{
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
        transition: all 0.3s ease;
    }}
    
    .chart-container:hover {{
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }}
    
    /* Notification Badge */
    .notif-badge {{
        position: fixed;
        top: 20px;
        right: 20px;
        background: {theme['danger']};
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        animation: pulse 2s infinite;
        z-index: 1000;
        cursor: pointer;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
    }}
    
    /* Loading Animation */
    .loading-spinner {{
        border: 4px solid rgba(0,0,0,0.1);
        border-left-color: {theme['primary']};
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }}
    
    @keyframes spin {{
        to {{ transform: rotate(360deg); }}
    }}
    
    /* Insight Cards */
    .insight-card {{
        background: white;
        border-left: 5px solid {theme['primary']};
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }}
    
    .insight-card:hover {{
        transform: translateX(5px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }}
    
    /* Progress Bar Animation */
    .progress-animated {{
        background: linear-gradient(90deg, {theme['success']} 0%, {theme['info']} 100%);
        height: 8px;
        border-radius: 10px;
        animation: progressFill 1.5s ease-out;
    }}
    
    @keyframes progressFill {{
        from {{ width: 0%; }}
    }}
    
    /* Tooltip Enhancement */
    [data-testid="stMetricValue"] {{
        font-size: 2rem;
        font-weight: 700;
        color: {theme['primary']};
    }}
    
    /* Responsive Design */
    @media (max-width: 768px) {{
        .kpi-card {{
            margin-bottom: 15px;
        }}
        .header-container {{
            padding: 1rem;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 🔄 AUTO-REFRESH COMPONENT
# ─────────────────────────────────────────────────────────────

def auto_refresh_component(interval_seconds=60):
    """Auto-refresh dengan countdown timer."""
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div style='color: #666; font-size: 12px;'>
            🕐 Terakhir update: {st.session_state.last_refresh.strftime('%H:%M:%S')}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        auto_refresh = st.toggle("🔄 Auto", value=False, help="Auto refresh setiap 60 detik")
    
    if auto_refresh:
        time.sleep(interval_seconds)
        st.session_state.last_refresh = datetime.now()
        st.rerun()
    
    return auto_refresh

# ─────────────────────────────────────────────────────────────
# 📊 ENHANCED CHART FUNCTIONS
# ─────────────────────────────────────────────────────────────

def create_interactive_progress_chart(filtered, theme):
    """Progress chart dengan drill-down & hover effects."""
    if filtered.empty or 'site_id' not in filtered.columns:
        return None
    
    colors = []
    for _, s in filtered.iterrows():
        st_val = s.get('status', '')
        colors.append(theme['success'] if st_val == 'ON_TRACK' 
                     else (theme['warning'] if st_val == 'DELAYED' else theme['danger']))
    
    hover_col = 'site_name' if 'site_name' in filtered.columns else 'site_id'
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=filtered['site_id'],
        x=filtered['progress'],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='rgba(0,0,0,0.3)', width=1),
            showscale=False
        ),
        text=filtered['progress'].apply(lambda x: f'{x:.1f}%'),
        textposition='outside',
        hovertext=[f"<b>{filtered[hover_col].iloc[i]}</b><br>Status: {filtered['status'].iloc[i]}<br>PM: {filtered['pm'].iloc[i]}" 
                  for i in range(len(filtered))],
        hovertemplate='<b>%{y}</b><br>%{hovertext}<br>Progress: %{x}%<extra></extra>',
        name='Progress'
    ))
    
    fig.update_layout(
        height=max(350, len(filtered)*45),
        xaxis=dict(
            range=[0, 105],
            title='Progress (%)',
            gridcolor='rgba(0,0,0,0.1)',
            zerolinecolor='rgba(0,0,0,0.2)'
        ),
        yaxis=dict(
            title='Site ID',
            gridcolor='rgba(0,0,0,0.1)'
        ),
        margin=dict(l=10, r=30, t=20, b=10),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='closest',
        bargap=0.3
    )
    
    return fig

def create_s_curve_with_targets(filtered, theme):
    """S-Curve dengan target line & interactive annotations."""
    if filtered.empty or 'progress' not in filtered.columns:
        return None
    
    total = len(filtered)
    m_labels = ['0%', '10%', '25%', '50%', '75%', '90%', '100%']
    thresholds = [0, 10, 25, 50, 75, 90, 100]
    
    actual_values = []
    target_values = [0, 10, 25, 50, 75, 90, 100]  # Target ideal
    
    for thresh in thresholds:
        actual = (len(filtered[filtered['progress'] >= thresh]) / total * 100) if total > 0 else 0
        actual_values.append(actual)
    
    fig = go.Figure()
    
    # Actual S-Curve
    fig.add_trace(go.Scatter(
        x=m_labels,
        y=actual_values,
        mode='lines+markers+text',
        name='Actual',
        line=dict(color=theme['primary'], width=4, shape='spline'),
        marker=dict(size=12, color=theme['secondary'], line=dict(color='white', width=2)),
        text=[f'{v:.1f}%' for v in actual_values],
        textposition='top center',
        hovertemplate='<b>Actual</b><br>Cumulative: %{y:.1f}%<extra></extra>'
    ))
    
    # Target Line (dashed)
    fig.add_trace(go.Scatter(
        x=m_labels,
        y=target_values,
        mode='lines',
        name='Target',
        line=dict(color=theme['danger'], width=2, dash='dash'),
        opacity=0.6,
        hovertemplate='<b>Target</b><br>Ideal: %{y}%<extra></extra>'
    ))
    
    fig.update_layout(
        height=400,
        yaxis=dict(
            range=[0, 105],
            title='Cumulative Sites (%)',
            gridcolor='rgba(0,0,0,0.1)',
            zerolinecolor='rgba(0,0,0,0.2)'
        ),
        xaxis=dict(
            title='Progress Threshold',
            gridcolor='rgba(0,0,0,0.1)'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',
        legend=dict(
            orientation='h',
            y=1.05,
            x=0.5,
            xanchor='center'
        )
    )
    
    return fig

def create_material_comparison_chart(materials_df, theme):
    """Material chart dengan alert indicators."""
    if materials_df.empty or 'name' not in materials_df.columns:
        return None
    
    mat_disp = materials_df.head(15).copy()
    
    # Determine colors based on stock status
    bar_colors = []
    for _, row in mat_disp.iterrows():
        current = row.get('current_stock', 0)
        minimum = row.get('min_stock', 0)
        if current < minimum:
            bar_colors.append(theme['danger'])
        elif current < minimum * 1.5:
            bar_colors.append(theme['warning'])
        else:
            bar_colors.append(theme['success'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Stok Saat Ini',
        y=mat_disp['name'],
        x=mat_disp['current_stock'],
        orientation='h',
        marker=dict(color=bar_colors),
        hovertemplate='<b>%{y}</b><br>Stok: %{x}<extra></extra>'
    ))
    
    if 'min_stock' in mat_disp.columns:
        fig.add_trace(go.Bar(
            name='Minimum Required',
            y=mat_disp['name'],
            x=mat_disp['min_stock'],
            orientation='h',
            marker=dict(color='rgba(0,0,0,0.2)'),
            hovertemplate='<b>%{y}</b><br>Minimum: %{x}<extra></extra>'
        ))
    
    fig.update_layout(
        height=max(400, len(mat_disp)*40),
        barmode='group',
        xaxis=dict(
            title='Quantity',
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            title='Material',
            gridcolor='rgba(0,0,0,0.1)'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation='h',
            y=1.02,
            x=0.5,
            xanchor='center'
        ),
        hovermode='closest'
    )
    
    return fig

# ─────────────────────────────────────────────────────────────
# 🎯 MAIN DASHBOARD FUNCTION
# ─────────────────────────────────────────────────────────────

def dashboard_page():
    # Initialize session state
    if 'theme' not in st.session_state:
        st.session_state.theme = "Professional"
    if 'sidebar_expanded' not in st.session_state:
        st.session_state.sidebar_expanded = True
    
    # Inject custom CSS
    inject_custom_css(st.session_state.theme)
    
    # ── SIDEBAR CONTROLS ──
    with st.sidebar:
        st.markdown("### ⚙️ Dashboard Settings")
        
        # Theme Selector
        selected_theme = st.selectbox(
            "🎨 Theme:",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state.theme)
        )
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()
        
        st.divider()
        
        # Auto-refresh
        auto_refresh_component(interval_seconds=60)
        
        st.divider()
        
        # Export Options
        st.markdown("### 📥 Export Data")
        if st.button("📊 Export to Excel", use_container_width=True):
            st.info("Fitur export sedang dikembangkan...")
        
        if st.button("📄 Export to PDF", use_container_width=True):
            st.info("Fitur export sedang dikembangkan...")
        
        st.divider()
        
        # Quick Stats
        st.markdown("### 📊 Quick Stats")
        st.metric("Active Users", "12", "👥")
        st.metric("System Status", "🟢 Online")
    
    # ── MAIN CONTENT ──
    now = datetime.now()
    
    # Enhanced Header
    col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
    
    with col_header1:
        st.markdown(f"""
        <div class='header-container'>
            <h1 style='margin:0; color:white; font-size:2.5rem;'>👷 Dashboard Collocation Project</h1>
            <p style='margin:5px 0 0 0; color:rgba(255,255,255,0.9); font-size:1rem;'>
                Real-time monitoring & analytics
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_header2:
        st.markdown(f"""
        <div class='clock-widget'>
            <div style='font-size: 14px;'>📅 {now.strftime('%A, %d %B %Y')}</div>
            <div style='font-size: 32px; font-weight: bold; margin: 10px 0;'>
                🕐 {now.strftime('%H:%M:%S')}
            </div>
            <div style='font-size: 11px;'>WIB</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_header3:
        # Notification Center
        st.markdown("""
        <div style='text-align: right;'>
            <div style='background: #dc3545; color: white; padding: 10px 15px; 
                        border-radius: 10px; font-weight: 600; cursor: pointer;
                            box-shadow: 0 4px 15px rgba(220,53,69,0.3);'>
                🔔 Notifications
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ── LOAD DATA WITH ERROR HANDLING ──
    try:
        with st.spinner("🔄 Loading data..."):
            all_data = read_all_sheets()
    except Exception as e:
        st.error(f"⚠️ Gagal load data: {str(e)[:100]}")
        all_data = {}
    
    df = all_data.get('projects', pd.DataFrame())
    if df.empty:
        df = read_sheet("projects")
    
    materials_df = all_data.get('materials', pd.DataFrame())
    if materials_df.empty:
        materials_df = read_sheet("materials")
    
    milestones_df = all_data.get('milestones', pd.DataFrame())
    if milestones_df.empty:
        milestones_df = read_sheet("milestones")
    
    # ── TOAST NOTIFICATIONS ──
    messages = all_data.get('chat_messages', pd.DataFrame())
    
    if not messages.empty and 'sender' in messages.columns:
        try:
            latest_msg = messages.iloc[-1]
            st.toast(f"💬 {latest_msg.get('sender','')}: {str(latest_msg.get('message',''))[:50]}...", icon="💬")
        except:
            pass
    
    if not milestones_df.empty and 'status' in milestones_df.columns:
        try:
            delayed = milestones_df[milestones_df['status'] == 'DELAYED']
            if not delayed.empty:
                st.toast(f"⚠️ {len(delayed)} milestone terlambat!", icon="⚠️")
        except:
            pass
    
    # ── DATA PREPROCESSING ──
    if not df.empty:
        if 'progress' in df.columns:
            df['progress'] = pd.to_numeric(df['progress'], errors='coerce').fillna(0)
        for col in ['start_date', 'end_date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    if not materials_df.empty:
        for c in ['current_stock', 'min_stock']:
            if c in materials_df.columns:
                materials_df[c] = pd.to_numeric(materials_df[c], errors='coerce').fillna(0)
    
    # ── FILTERS ──
    st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
    st.markdown("### 🔍 Filter Data")
    
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 1])
    
    with col_f1:
        pm_list = df['pm'].dropna().unique().tolist() if not df.empty and 'pm' in df.columns else []
        filter_pm = st.multiselect("👤 Filter PM:", pm_list, default=[], placeholder="Semua PM")
    
    with col_f2:
        vendor_list = df['vendor'].dropna().unique().tolist() if not df.empty and 'vendor' in df.columns else []
        filter_vendor = st.multiselect("🏢 Filter Vendor:", vendor_list, default=[], placeholder="Semua Vendor")
    
    with col_f3:
        try:
            default_start = date.today() - timedelta(days=30)
            date_range = st.date_input("📅 Periode:", value=(default_start, date.today()), max_value=date.today())
        except:
            date_range = (date.today() - timedelta(days=30), date.today())
    
    with col_f4:
        st.markdown("<br>", unsafe_allow_html=True)
        apply_filter = st.button("🔄 Apply", type="primary", use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Apply filters
    filtered = df.copy()
    if not filtered.empty:
        if filter_pm and 'pm' in filtered.columns:
            filtered = filtered[filtered['pm'].isin(filter_pm)]
        if filter_vendor and 'vendor' in filtered.columns:
            filtered = filtered[filtered['vendor'].isin(filter_vendor)]
    
    st.markdown("---")
    
    # ── KPI CARDS WITH ANIMATIONS ──
    total_sites = len(filtered)
    avg_progress = filtered['progress'].mean() if not filtered.empty and 'progress' in filtered.columns else 0
    
    on_track = len(filtered[filtered['status']=='ON_TRACK']) if not filtered.empty and 'status' in filtered.columns else 0
    delayed_sites = len(filtered[filtered['status'].isin(['DELAYED','CRITICAL'])]) if not filtered.empty and 'status' in filtered.columns else 0
    
    critical_mat = 0
    if not materials_df.empty and 'current_stock' in materials_df.columns and 'min_stock' in materials_df.columns:
        try:
            critical_mat = len(materials_df[materials_df['current_stock'] < materials_df['min_stock']])
        except:
            pass
    
    delayed_ms = len(milestones_df[milestones_df['status']=='DELAYED']) if not milestones_df.empty and 'status' in milestones_df.columns else 0
    
    theme = THEMES[st.session_state.theme]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='kpi-card' style='background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%);'>
            <div style='font-size: 48px; margin-bottom: 10px;'>📁</div>
            <div style='font-size: 42px; font-weight: bold;'>{total_sites}</div>
            <div style='font-size: 14px; opacity: 0.9;'>Total Site</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        prog_color = theme['success'] if avg_progress >= 70 else (theme['warning'] if avg_progress >= 40 else theme['danger'])
        st.markdown(f"""
        <div class='kpi-card' style='background: linear-gradient(135deg, {prog_color} 0%, {theme['info']} 100%);'>
            <div style='font-size: 48px; margin-bottom: 10px;'>📈</div>
            <div style='font-size: 42px; font-weight: bold;'>{avg_progress:.1f}%</div>
            <div style='font-size: 14px; opacity: 0.9;'>Avg Progress</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='kpi-card' style='background: linear-gradient(135deg, {theme['danger']} 0%, #c0392b 100%);'>
            <div style='font-size: 48px; margin-bottom: 10px;'>⚠️</div>
            <div style='font-size: 42px; font-weight: bold;'>{delayed_ms}</div>
            <div style='font-size: 14px; opacity: 0.9;'>MS Terlambat</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='kpi-card' style='background: linear-gradient(135deg, {theme['warning']} 0%, #f39c12 100%);'>
            <div style='font-size: 48px; margin-bottom: 10px;'>🔴</div>
            <div style='font-size: 42px; font-weight: bold;'>{critical_mat}</div>
            <div style='font-size: 14px; opacity: 0.9;'>Mat. Kritis</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ── ROW 1: PROGRESS BAR + S-CURVE ──
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("### 📊 Progress per Site")
        
        if not filtered.empty:
            fig_progress = create_interactive_progress_chart(filtered, theme)
            if fig_progress:
                st.plotly_chart(fig_progress, use_container_width=True)
        else:
            st.info("📋 Tidak ada data.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_right:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("### 📈 S-Curve Progress")
        
        if not filtered.empty:
            fig_scurve = create_s_curve_with_targets(filtered, theme)
            if fig_scurve:
                st.plotly_chart(fig_scurve, use_container_width=True)
        else:
            st.info("📋 Tidak ada data.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ── ROW 2: MATERIAL + WEEKLY ──
    col_left2, col_right2 = st.columns([1, 1])
    
    with col_left2:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("### 📦 Material: Kebutuhan vs Stok")
        
        if not materials_df.empty:
            fig_material = create_material_comparison_chart(materials_df, theme)
            if fig_material:
                st.plotly_chart(fig_material, use_container_width=True)
        else:
            st.info("📋 Tidak ada data material.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_right2:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.markdown("### 📊 Progress per Minggu")
        
        if not milestones_df.empty and 'planned_end' in milestones_df.columns:
            try:
                milestones_df['week'] = pd.to_datetime(milestones_df['planned_end'], errors='coerce').dt.strftime('%Y-W%W')
                weekly = milestones_df.groupby('week').agg(
                    ms_done=('status', lambda x: (x=='DONE').sum()),
                    ms_delayed=('status', lambda x: (x=='DELAYED').sum())
                ).reset_index().tail(12)
                
                if not weekly.empty:
                    fig_weekly = go.Figure()
                    fig_weekly.add_trace(go.Bar(
                        name='MS Selesai',
                        x=weekly['week'],
                        y=weekly['ms_done'],
                        marker=dict(color=theme['success'])
                    ))
                    fig_weekly.add_trace(go.Bar(
                        name='MS Terlambat',
                        x=weekly['week'],
                        y=weekly['ms_delayed'],
                        marker=dict(color=theme['danger'])
                    ))
                    fig_weekly.update_layout(
                        height=350,
                        barmode='group',
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        legend=dict(orientation='h', y=1.02),
                        xaxis=dict(gridcolor='rgba(0,0,0,0.1)'),
                        yaxis=dict(gridcolor='rgba(0,0,0,0.1)')
                    )
                    st.plotly_chart(fig_weekly, use_container_width=True)
            except:
                st.info("ℹ️ Grafik mingguan tidak dapat ditampilkan")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ── MINI INSIGHTS WITH ENHANCED UI ──
    st.markdown("### 🤖 Mini Insights")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    
    with col_m1:
        st.markdown(f"""
        <div class='insight-card' style='border-left-color: {theme['warning']};'>
            <h3 style='margin-top:0; color: {theme['warning']};'>⚠️ Site Perlu Perhatian</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not filtered.empty:
            try:
                crit = filtered[filtered['status'].isin(['CRITICAL','DELAYED']) | (filtered['progress']<30)]
                if not crit.empty:
                    for _, r in crit.head(3).iterrows():
                        color = '🔴' if r.get('status')=='CRITICAL' else '🟡'
                        st.markdown(f"""
                        <div class='insight-card'>
                            {color} **{r.get('site_id','?')}** — {r.get('progress',0):.0f}%
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ Semua site aman!")
            except:
                st.info("ℹ️ Data tidak cukup")
    
    with col_m2:
        st.markdown(f"""
        <div class='insight-card' style='border-left-color: {theme['danger']};'>
            <h3 style='margin-top:0; color: {theme['danger']};'>📦 Top Material Kritis</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if not materials_df.empty:
            try:
                crit2 = materials_df[materials_df['current_stock'] < materials_df['min_stock']]
                if not crit2.empty:
                    for _, r in crit2.head(3).iterrows():
                        gap = r['min_stock'] - r['current_stock']
                        st.markdown(f"""
                        <div class='insight-card'>
                            🔴 **{r['name']}** — Kurang {gap:.0f}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ Material cukup!")
            except:
                st.info("ℹ️ Data material tidak konsisten")
    
    with col_m3:
        st.markdown(f"""
        <div class='insight-card' style='border-left-color: {theme['info']};'>
            <h3 style='margin-top:0; color: {theme['info']};'>🎯 Rekomendasi Cepat</h3>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            if delayed_ms > 5:
                st.markdown("<div class='insight-card'>⚠️ Banyak milestone terlambat</div>", unsafe_allow_html=True)
            if critical_mat > 3:
                st.markdown("<div class='insight-card'>📦 >3 material kritis</div>", unsafe_allow_html=True)
            if delayed_sites > 0:
                st.markdown(f"<div class='insight-card'>🔴 {delayed_sites} site terlambat</div>", unsafe_allow_html=True)
            if total_sites > 0 and on_track/total_sites >= 0.8:
                st.markdown("<div class='insight-card'>✅ Performa bagus!</div>", unsafe_allow_html=True)
        except:
            pass

if __name__ == "__main__":
    dashboard_page()
