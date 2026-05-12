import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from supabase_db import read_all_sheets, read_sheet
import time
import io

# ─────────────────────────────────────────────────────────────
# 📱 MOBILE FRIENDLY CONFIGURATION
# ─────────────────────────────────────────────────────────────

# Set page config untuk mobile optimization
st.set_page_config(
    page_title="Collocation Dashboard",
    page_icon="👷",
    layout="wide",
    initial_sidebar_state="auto"
)

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
# 💅 CUSTOM CSS - MOBILE FRIENDLY
# ─────────────────────────────────────────────────────────────

def inject_custom_css(theme_name="Professional"):
    theme = THEMES[theme_name]
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {{ 
        font-family: 'Inter', sans-serif;
        -webkit-tap-highlight-color: transparent;
    }}
    
    /* Main container optimization */
    .stApp {{
        background: linear-gradient(135deg, {theme['bg']} 0%, #ffffff 100%);
    }}
    
    /* Hide default Streamlit elements for better mobile view */
    header {{
        background-color: transparent !important;
    }}
    
    /* Block container padding adjustment */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }}
    
    /* Header container responsive */
    .header-container {{
        background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%);
        padding: 1rem;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.15);
        margin-bottom: 1rem;
        animation: slideDown 0.6s ease-out;
    }}
    
    @keyframes slideDown {{
        from {{ opacity: 0; transform: translateY(-30px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .clock-widget {{
        background: rgba(255,255,255,0.15);
        backdrop-filter: blur(10px);
        padding: 12px;
        border-radius: 15px;
        text-align: center;
        color: white;
        border: 1px solid rgba(255,255,255,0.2);
        transition: all 0.3s ease;
    }}
    
    .kpi-card {{
        background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
        transition: all 0.3s ease;
        animation: fadeInUp 0.6s ease-out;
        margin-bottom: 0.75rem;
        cursor: pointer;
    }}
    
    .kpi-card:active {{
        transform: scale(0.98);
    }}
    
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* Button responsive */
    .stButton > button {{
        background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%);
        color: white;
        border: none;
        padding: 0.6rem 1rem;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        font-size: 14px;
    }}
    
    .stButton > button:active {{
        transform: scale(0.97);
    }}
    
    /* Filter container responsive */
    .filter-container {{
        background: white;
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
        animation: slideIn 0.5s ease-out;
    }}
    
    @keyframes slideIn {{
        from {{ opacity: 0; transform: translateX(-15px); }}
        to {{ opacity: 1; transform: translateX(0); }}
    }}
    
    /* Chart container responsive */
    .chart-container {{
        background: white;
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }}
    
    .last-update-badge {{
        background: rgba(255,255,255,0.95);
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        color: {theme['primary']};
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }}
    
    .insight-card {{
        background: white;
        border-left: 4px solid {theme['primary']};
        padding: 0.75rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        font-size: 13px;
    }}
    
    /* Responsive Design - Mobile First */
    @media (max-width: 768px) {{
        .kpi-card {{
            margin-bottom: 0.5rem;
            padding: 0.75rem;
        }}
        
        .kpi-card div[style*="font-size: 48px"] {{
            font-size: 32px !important;
            margin-bottom: 5px !important;
        }}
        
        .kpi-card div[style*="font-size: 42px"] {{
            font-size: 28px !important;
        }}
        
        .kpi-card div[style*="font-size: 14px"] {{
            font-size: 11px !important;
        }}
        
        .header-container h1 {{
            font-size: 1.2rem !important;
        }}
        
        .header-container p {{
            font-size: 0.75rem !important;
            margin-top: 5px !important;
        }}
        
        .clock-widget {{
            padding: 8px 12px !important;
            margin-left: 10px !important;
        }}
        
        .clock-widget div[style*="font-size: 32px"] {{
            font-size: 20px !important;
        }}
        
        .clock-widget div[style*="font-size: 13px"] {{
            font-size: 10px !important;
        }}
        
        .filter-container {{
            padding: 0.75rem !important;
        }}
        
        .chart-container {{
            padding: 0.75rem !important;
        }}
        
        .stMarkdown h3 {{
            font-size: 1rem !important;
            margin-bottom: 0.5rem !important;
        }}
        
        .insight-card h3 {{
            font-size: 0.9rem !important;
        }}
    }}
    
    /* Touch-friendly inputs */
    input, select, textarea {{
        font-size: 16px !important; /* Prevent zoom on focus in iOS */
    }}
    
    /* Sidebar responsive */
    @media (max-width: 768px) {{
        section[data-testid="stSidebar"] {{
            width: 280px !important;
        }}
    }}
    
    /* Improve scrollbar for mobile */
    ::-webkit-scrollbar {{
        width: 4px;
        height: 4px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: #f1f1f1;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {theme['primary']};
        border-radius: 3px;
    }}
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 📊 CHART FUNCTIONS (Responsive)
# ─────────────────────────────────────────────────────────────

def create_interactive_progress_chart(filtered, theme):
    if filtered.empty or 'site_id' not in filtered.columns:
        return None
    
    colors = []
    for _, s in filtered.iterrows():
        st_val = s.get('status', '')
        colors.append(theme['success'] if st_val == 'ON_TRACK' 
                     else (theme['warning'] if st_val == 'DELAYED' else theme['danger']))
    
    hover_col = 'site_name' if 'site_name' in filtered.columns else 'site_id'
    
    # Responsive height calculation
    chart_height = min(400, max(250, len(filtered) * 35))
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=filtered['site_id'],
        x=filtered['progress'],
        orientation='h',
        marker=dict(color=colors, line=dict(color='rgba(0,0,0,0.3)', width=1)),
        text=filtered['progress'].apply(lambda x: f'{x:.1f}%'),
        textposition='outside',
        textfont=dict(size=10),
        hovertext=[f"<b>{filtered[hover_col].iloc[i]}</b><br>Status: {filtered['status'].iloc[i]}<br>PM: {filtered['pm'].iloc[i]}" 
                  for i in range(len(filtered))],
        hovertemplate='<b>%{y}</b><br>%{hovertext}<br>Progress: %{x}%<extra></extra>',
        name='Progress'
    ))
    
    fig.update_layout(
        height=chart_height,
        xaxis=dict(range=[0, 105], title='Progress (%)', gridcolor='rgba(0,0,0,0.1)', title_font=dict(size=12)),
        yaxis=dict(title='Site ID', gridcolor='rgba(0,0,0,0.1)', title_font=dict(size=12), tickfont=dict(size=10)),
        margin=dict(l=5, r=20, t=20, b=5),
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='closest',
        bargap=0.3
    )
    
    return fig

def create_s_curve_with_targets(filtered, theme):
    if filtered.empty or 'progress' not in filtered.columns:
        return None
    
    total = len(filtered)
    m_labels = ['0%', '10%', '25%', '50%', '75%', '90%', '100%']
    thresholds = [0, 10, 25, 50, 75, 90, 100]
    
    actual_values = []
    target_values = [0, 10, 25, 50, 75, 90, 100]
    
    for thresh in thresholds:
        actual = (len(filtered[filtered['progress'] >= thresh]) / total * 100) if total > 0 else 0
        actual_values.append(actual)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=m_labels,
        y=actual_values,
        mode='lines+markers+text',
        name='Actual',
        line=dict(color=theme['primary'], width=3, shape='spline'),
        marker=dict(size=8, color=theme['secondary'], line=dict(color='white', width=1.5)),
        text=[f'{v:.1f}%' for v in actual_values],
        textposition='top center',
        textfont=dict(size=9),
        hovertemplate='<b>Actual</b><br>Cumulative: %{y:.1f}%<extra></extra>'
    ))
    
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
        height=350,
        yaxis=dict(range=[0, 105], title='Cumulative Sites (%)', gridcolor='rgba(0,0,0,0.1)', title_font=dict(size=12)),
        xaxis=dict(title='Progress Threshold', gridcolor='rgba(0,0,0,0.1)', title_font=dict(size=12), tickfont=dict(size=10)),
        margin=dict(l=5, r=5, t=30, b=5),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',
        legend=dict(orientation='h', y=1.08, x=0.5, xanchor='center', font=dict(size=11))
    )
    
    return fig

def create_material_comparison_chart(materials_df, theme):
    if materials_df.empty or 'name' not in materials_df.columns:
        return None
    
    mat_disp = materials_df.head(15).copy()
    
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
    
    # Responsive height
    chart_height = min(450, max(300, len(mat_disp) * 30))
    
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
        height=chart_height,
        barmode='group',
        xaxis=dict(title='Quantity', gridcolor='rgba(0,0,0,0.1)', title_font=dict(size=12)),
        yaxis=dict(title='Material', gridcolor='rgba(0,0,0,0.1)', title_font=dict(size=12), tickfont=dict(size=10)),
        margin=dict(l=5, r=5, t=20, b=5),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', y=1.05, x=0.5, xanchor='center', font=dict(size=11)),
        hovermode='closest'
    )
    
    return fig

# ─────────────────────────────────────────────────────────────
# 💾 EXPORT FUNCTIONS
# ─────────────────────────────────────────────────────────────

def export_to_excel(df, materials_df, milestones_df):
    """Export data ke Excel dengan multiple sheets."""
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
    # Initialize session state
    if 'theme' not in st.session_state:
        st.session_state.theme = "Professional"
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    # Inject custom CSS
    inject_custom_css(st.session_state.theme)
    
    # ── MOBILE SIDEBAR CONTROLS ──
        # ── SIDEBAR CONTROLS ──
    with st.sidebar:
        st.markdown("### 🏢 Portfolio Filter")
        
        # Load Master Projects
        try:
            master_df = read_sheet("master_projects")
            master_options = ["ALL"] + master_df["id"].tolist() if not master_df.empty else ["ALL"]
        except:
            master_options = ["ALL"]

        selected_master = st.selectbox(
            "Pilih Proyek:",
            master_options,
            index=master_options.index(st.session_state.get('master_project_filter', "ALL")),
            format_func=lambda x: "🌍 SEMUA PROYEK" if x == "ALL" 
            else f"{master_df[master_df['id']==x]['project_code'].values[0]} - {master_df[master_df['id']==x]['project_name'].values[0]}" if not master_df.empty else x
        )
        
        if selected_master != st.session_state.get('master_project_filter', "ALL"):
            st.session_state.master_project_filter = selected_master
            st.cache_data.clear()
            st.rerun()

        st.divider()
        st.markdown("### ⚙️ Dashboard Settings")
        # ... (kode tema & refresh tetap sama) ...
        
        # Auto-refresh with timestamp
        st.markdown("### 🔄 Auto Refresh")
        auto_refresh = st.toggle("Aktifkan", value=False, help="Auto refresh setiap 60 detik")
        
        if auto_refresh:
            time.sleep(60)
            st.session_state.last_refresh = datetime.now()
            st.rerun()
        
        # Display last update time
        st.markdown("---")
        st.markdown("### ⏰ Last Update")
        st.markdown(f"""
        <div class='last-update-badge'>
            <span>🕐</span>
            <span>{st.session_state.last_refresh.strftime('%d/%m/%Y %H:%M:%S')}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Export Options
        st.markdown("### 📥 Export Data")
        
        # Button Export Excel
        if st.button("📊 Export to Excel", use_container_width=True):
            try:
                # Load data untuk export
                all_data = read_all_sheets()
                df_export = all_data.get('projects', pd.DataFrame())
                materials_export = all_data.get('materials', pd.DataFrame())
                milestones_export = all_data.get('milestones', pd.DataFrame())
                
                excel_data = export_to_excel(df_export, materials_export, milestones_export)
                
                st.download_button(
                    label="⬇️ Download Excel",
                    data=excel_data,
                    file_name=f"dashboard_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                st.success("✅ File Excel siap download!")
                
            except Exception as e:
                st.error(f"❌ Gagal export: {str(e)[:100]}")

            # Filter Data berdasarkan Master Project
        if st.session_state.master_project_filter != "ALL" and not df.empty:
            df = df[df['master_project_id'] == st.session_state.master_project_filter]
            
            # Filter child tables juga (Milestones & Inventory)
            if not milestones_df.empty:
                # Ambil list site_id yang termasuk proyek ini
                valid_sites = df['id'].tolist()
                milestones_df = milestones_df[milestones_df['project_id'].isin(valid_sites)]
                
            if not materials_df.empty:
                materials_df = materials_df[materials_df['project_id'].isin(valid_sites)]
        
        # Button Export PDF (placeholder)
        if st.button("📄 Export to PDF", use_container_width=True):
            st.info("🚧 Fitur PDF export sedang dikembangkan. Gunakan Excel export untuk saat ini.")
        
        st.divider()
        
        # Quick Stats
        st.markdown("### 📊 Quick Stats")
        st.metric("Active Users", "12", "👥")
        st.metric("System Status", "🟢 Online")
        
        # Manual Refresh Button
        st.divider()
        if st.button("🔄 Refresh Data Sekarang", use_container_width=True, type="primary"):
            st.session_state.last_refresh = datetime.now()
            st.cache_data.clear()
            st.success("✅ Data berhasil di-refresh!")
            st.rerun()
    
    # ── MAIN CONTENT ──
    now = datetime.now()
    
    # Enhanced Header - Mobile Friendly
    st.markdown(f"""
    <div class='header-container' style='display: flex; justify-content: space-between; align-items: center; padding: 1rem;'>
        <div style='flex: 1;'>
            <h1 style='margin:0; color: #ffffff; font-size: 1.3rem; font-weight:700;'>
                👷 Collocation Project
            </h1>
            <p style='margin:5px 0 0 0; color: rgba(255,255,255,0.95); font-size: 0.8rem; font-weight:500;'>
                Real-time monitoring
            </p>
        </div>
        <div class='clock-widget' style='background: rgba(255,255,255,0.25); padding: 10px 15px; border-radius: 12px; text-align: center; backdrop-filter: blur(10px); margin-left: 10px;'>
            <div style='color: #ffffff; font-size: 11px; font-weight: 600; margin-bottom: 3px;'>
                📅 {now.strftime('%d/%m/%Y')}
            </div>
            <div style='color: #ffffff; font-size: 20px; font-weight: 700; line-height: 1;'>
                🕐 {now.strftime('%H:%M')}
            </div>
            <div style='color: rgba(255,255,255,0.9); font-size: 9px; margin-top: 2px; font-weight: 500;'>
                WIB
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
    
    # ── LOAD DATA WITH TIMESTAMP UPDATE ──
    try:
        with st.spinner("🔄 Loading data..."):
            all_data = read_all_sheets()
            # Update timestamp setelah data berhasil di-load
            st.session_state.last_refresh = datetime.now()
            st.session_state.data_loaded = True
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
    
    # ── FILTERS (Mobile friendly - stacked on mobile) ──
    st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
    st.markdown("### 🔍 Filter Data")
    
    # Responsive column layout
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        pm_list = df['pm'].dropna().unique().tolist() if not df.empty and 'pm' in df.columns else []
        filter_pm = st.multiselect("👤 PM:", pm_list, default=[], placeholder="Semua PM")
    
    with col_f2:
        vendor_list = df['vendor'].dropna().unique().tolist() if not df.empty and 'vendor' in df.columns else []
        filter_vendor = st.multiselect("🏢 Vendor:", vendor_list, default=[], placeholder="Semua Vendor")
    
    # Date filter on new row
    try:
        default_start = date.today() - timedelta(days=30)
        date_range = st.date_input("📅 Periode:", value=(default_start, date.today()), max_value=date.today())
    except:
        date_range = (date.today() - timedelta(days=30), date.today())
    
    # Apply button
    apply_filter = st.button("🔄 Terapkan Filter", type="primary", use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Apply filters
    filtered = df.copy()
    if not filtered.empty:
        if filter_pm and 'pm' in filtered.columns:
            filtered = filtered[filtered['pm'].isin(filter_pm)]
        if filter_vendor and 'vendor' in filtered.columns:
            filtered = filtered[filtered['vendor'].isin(filter_vendor)]
    
    st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
    
    # ── KPI CARDS (2x2 grid for mobile) ──
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
    
    # 2x2 grid for mobile
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class='kpi-card' style='background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%);'>
            <div style='font-size: 32px; margin-bottom: 5px;'>📁</div>
            <div style='font-size: 28px; font-weight: bold;'>{total_sites}</div>
            <div style='font-size: 11px; opacity: 0.9;'>Total Site</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        prog_color = theme['success'] if avg_progress >= 70 else (theme['warning'] if avg_progress >= 40 else theme['danger'])
        st.markdown(f"""
        <div class='kpi-card' style='background: linear-gradient(135deg, {prog_color} 0%, {theme['info']} 100%);'>
            <div style='font-size: 32px; margin-bottom: 5px;'>📈</div>
            <div style='font-size: 28px; font-weight: bold;'>{avg_progress:.1f}%</div>
            <div style='font-size: 11px; opacity: 0.9;'>Avg Progress</div>
        </div>
        """, unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown(f"""
        <div class='kpi-card' style='background: linear-gradient(135deg, {theme['danger']} 0%, #c0392b 100%);'>
            <div style='font-size: 32px; margin-bottom: 5px;'>⚠️</div>
            <div style='font-size: 28px; font-weight: bold;'>{delayed_ms}</div>
            <div style='font-size: 11px; opacity: 0.9;'>MS Terlambat</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='kpi-card' style='background: linear-gradient(135deg, {theme['warning']} 0%, #f39c12 100%);'>
            <div style='font-size: 32px; margin-bottom: 5px;'>🔴</div>
            <div style='font-size: 28px; font-weight: bold;'>{critical_mat}</div>
            <div style='font-size: 11px; opacity: 0.9;'>Mat. Kritis</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
    
    # ── ROW 1: PROGRESS BAR + S-CURVE (Stacked on mobile) ──
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("### 📊 Progress per Site")
    
    if not filtered.empty:
        fig_progress = create_interactive_progress_chart(filtered, theme)
        if fig_progress:
            st.plotly_chart(fig_progress, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("📋 Tidak ada data.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("### 📈 S-Curve Progress")
    
    if not filtered.empty:
        fig_scurve = create_s_curve_with_targets(filtered, theme)
        if fig_scurve:
            st.plotly_chart(fig_scurve, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("📋 Tidak ada data.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
    
    # ── ROW 2: MATERIAL + WEEKLY (Stacked on mobile) ──
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    st.markdown("### 📦 Material: Kebutuhan vs Stok")
    
    if not materials_df.empty:
        fig_material = create_material_comparison_chart(materials_df, theme)
        if fig_material:
            st.plotly_chart(fig_material, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("📋 Tidak ada data material.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
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
                    height=300,
                    barmode='group',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation='h', y=1.08, font=dict(size=10)),
                    xaxis=dict(gridcolor='rgba(0,0,0,0.1)', tickangle=45),
                    yaxis=dict(gridcolor='rgba(0,0,0,0.1)'),
                    margin=dict(l=5, r=5, t=30, b=50)
                )
                st.plotly_chart(fig_weekly, use_container_width=True, config={'displayModeBar': False})
        except:
            st.info("ℹ️ Grafik mingguan tidak dapat ditampilkan")
    else:
        st.info("📋 Tidak ada data milestone.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 0.5rem 0;'>", unsafe_allow_html=True)
    
    # ── MINI INSIGHTS (Stacked on mobile) ──
    st.markdown("### 🤖 Mini Insights")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown(f"""
        <div class='insight-card' style='border-left-color: {theme['warning']};'>
            <strong style='color: {theme['warning']};'>⚠️ Site Perlu Perhatian</strong>
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
            <strong style='color: {theme['danger']};'>📦 Material Kritis</strong>
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
    
    # Third insight on new row
    st.markdown(f"""
    <div class='insight-card' style='border-left-color: {theme['info']}; margin-top: 0.5rem;'>
        <strong style='color: {theme['info']};'>🎯 Rekomendasi Cepat</strong>
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
