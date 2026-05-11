"""
dashboard.py - Export & Report Module
Production-ready dengan BytesIO (tanpa temp file)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from supabase_db import read_sheet

# ─────────────────────────────────────────────────────────────
# 📄 PDF GENERATOR (FPDF)
# ─────────────────────────────────────────────────────────────

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    st.warning("⚠️ Library fpdf tidak terinstall. Install dengan: `pip install fpdf`")

class PDFReport(FPDF):
    """Custom PDF Report dengan header."""
    
    def header(self):
        """Header di setiap halaman."""
        # Logo (opsional)
        # self.image('logo.png', 10, 8, 33)
        
        # Judul
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, 'Site Management Report', 0, 1, 'C')
        
        # Subtitle
        self.set_font('Helvetica', 'I', 9)
        generated_time = datetime.now().strftime("%d %b %Y, %H:%M")
        self.cell(0, 5, f'Generated: {generated_time}', 0, 1, 'C')
        
        self.ln(5)
    
    def footer(self):
        """Footer di setiap halaman."""
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


def generate_site_pdf(site_id: str) -> bytes:
    """
    Generate PDF report untuk site tertentu.
    Returns: Bytes PDF (bukan file fisik)
    """
    if not FPDF_AVAILABLE:
        raise ImportError("FPDF library tidak tersedia")
    
    try:
        # Load data
        sites_df = read_sheet("projects")
        ms_df = read_sheet("milestones")
        
        # Cari data site
        if sites_df.empty:
            raise ValueError("Data projects kosong")
        
        site_row = sites_df[sites_df['id'] == site_id]
        
        if site_row.empty:
            raise ValueError(f"Site dengan ID {site_id} tidak ditemukan")
        
        site = site_row.iloc[0]
        
        # Buat PDF
        pdf = PDFReport()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # ── Header Site Info ──
        pdf.set_font('Helvetica', 'B', 12)
        site_name = site.get('site_name', 'N/A')
        site_id_str = site.get('site_id', 'N/A')
        pdf.cell(0, 8, f"Site: {site_id_str} - {site_name}", 0, 1)
        pdf.ln(3)
        
        # ── Detail Info ──
        pdf.set_font('Helvetica', '', 9)
        
        info_fields = [
            ('Status', site.get('status', '-')),
            ('Progress', f"{site.get('progress', '0')}%"),
            ('Project Manager', site.get('pm', '-')),
            ('Vendor', site.get('vendor', '-')),
            ('Plan Start', site.get('start_date', '-')),
            ('Plan End', site.get('end_date', '-'))
        ]
        
        for label, value in info_fields:
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(40, 6, f"{label}:", 0, 0)
            pdf.set_font('Helvetica', '', 9)
            pdf.cell(0, 6, str(value), 0, 1)
        
        pdf.ln(5)
        
        # ── Milestones Table ──
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, 'Milestones:', 0, 1)
        pdf.ln(2)
        
        # Filter milestone untuk site ini
        site_ms = ms_df[ms_df['project_id'] == site_id] if not ms_df.empty else pd.DataFrame()
        
        if not site_ms.empty:
            # Header tabel
            pdf.set_font('Helvetica', 'B', 7)
            columns = [
                ('Name', 70),
                ('Status', 25),
                ('Planned End', 25),
                ('Weight', 15),
                ('Delay Reason', 45)
            ]
            
            # Draw header
            for col_name, width in columns:
                pdf.cell(width, 6, col_name.upper(), 1, 0, 'C')
            pdf.ln()
            
            # Draw rows
            pdf.set_font('Helvetica', '', 7)
            
            for _, ms in site_ms.iterrows():
                # Name (potong jika terlalu panjang)
                name = str(ms.get('name', ''))[:35]
                pdf.cell(70, 5, name, 1, 0)
                
                # Status
                status = str(ms.get('status', ''))
                pdf.cell(25, 5, status, 1, 0, 'C')
                
                # Planned End
                end_date = str(ms.get('planned_end', ''))[:10]
                pdf.cell(25, 5, end_date, 1, 0, 'C')
                
                # Weight
                weight = str(ms.get('weight', '0'))
                pdf.cell(15, 5, f"{weight}%", 1, 0, 'R')
                
                # Delay Reason
                reason = str(ms.get('delay_reason', '-'))[:20]
                pdf.cell(45, 5, reason, 1, 0, 'L')
                
                pdf.ln()
        else:
            pdf.set_font('Helvetica', 'I', 9)
            pdf.cell(0, 6, "Belum ada milestone untuk site ini.", 0, 1)
        
        # ── Summary Section ──
        pdf.ln(5)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, 'Summary:', 0, 1)
        
        if not site_ms.empty:
            total_ms = len(site_ms)
            done_ms = len(site_ms[site_ms['status'] == 'DONE'])
            delayed_ms = len(site_ms[site_ms['status'] == 'DELAYED'])
            
            pdf.set_font('Helvetica', '', 9)
            pdf.cell(0, 6, f"Total Milestones: {total_ms}", 0, 1)
            pdf.cell(0, 6, f"Completed: {done_ms} ({done_ms/total_ms:.1%} if total_ms > 0 else 0)", 0, 1)
            pdf.cell(0, 6, f"Delayed: {delayed_ms}", 0, 1)
        
        # Return PDF sebagai bytes
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        return pdf_bytes
    
    except Exception as e:
        raise Exception(f"Gagal generate PDF: {str(e)}")

# ─────────────────────────────────────────────────────────────
# 📊 EXPORT PAGE
# ─────────────────────────────────────────────────────────────

def export_page():
    """Halaman Export Report."""
    st.title("📄 Export Report")
    st.markdown("Generate dan download report dalam format PDF.")
    
    if not FPDF_AVAILABLE:
        st.error("❌ Library fpdf tidak terinstall.")
        st.info("💡 Install dengan command: `pip install fpdf`")
        st.stop()
    
    # Load data projects
    sites_df = read_sheet("projects")
    
    if sites_df.empty:
        st.warning("⚠️ Tambahkan site dulu di menu Project Tracker!")
        return
    
    # ── Sidebar: Pilih Site ──
    st.sidebar.header("🔍 Filter")
    
    selected = st.sidebar.selectbox(
        "Pilih Site:",
        sites_df['id'].tolist(),
        format_func=lambda x: f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}"
    )
    
    # ── Main Content ──
    st.subheader("Preview Data")
    
    # Tampilkan info site
    site_info = sites_df[sites_df['id'] == selected].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Site ID", site_info.get('site_id', '-'))
    with col2:
        st.metric("Status", site_info.get('status', '-'))
    with col3:
        st.metric("Progress", f"{site_info.get('progress', '0')}%")
    
    st.divider()
    
    # Tombol generate
    if st.button("📄 Generate PDF Report", type="primary", use_container_width=True):
        with st.spinner("🔄 Generating PDF..."):
            try:
                # Generate PDF
                pdf_bytes = generate_site_pdf(selected)
                
                # Siapkan nama file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                site_name = site_info.get('site_id', 'site').replace(' ', '_')
                filename = f"report_{site_name}_{timestamp}.pdf"
                
                # Download button
                st.success("✅ PDF berhasil digenerate!")
                
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
                
                # Info tambahan
                st.info(f"📊 File size: {len(pdf_bytes) / 1024:.1f} KB")
                
            except Exception as e:
                st.error(f"❌ Gagal generate PDF: {str(e)}")
                st.exception(e)  # Tampilkan detail error untuk debugging
    
    # ── Batch Export (Opsional) ──
    st.divider()
    st.subheader("📦 Batch Export (Semua Site)")
    
    if st.button("📦 Generate All Sites Report", type="secondary"):
        st.warning("⚠️ Fitur ini akan generate PDF untuk semua site (makan waktu).")
        
        if st.button("✅ Ya, Generate Semua!"):
            st.info("🔄 Processing... (fitur dalam pengembangan)")

# ─────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    dashboard_page()
