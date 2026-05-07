import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from gsheets_db import read_sheet
from fpdf import FPDF
import tempfile

class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, 'Site Management Report', 0, 1, 'C')
        self.set_font('Helvetica', 'I', 9)
        self.cell(0, 5, f'Generated: {datetime.now().strftime("%d %b %Y, %H:%M")}', 0, 1, 'C')
        self.ln(5)

def generate_site_pdf(site_id):
    sites_df = read_sheet("projects")
    ms_df = read_sheet("milestones")
    
    site = sites_df[sites_df['id']==site_id].iloc[0] if not sites_df.empty else None
    if site is None:
        return None
    
    pdf = PDFReport()
    pdf.add_page()
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, f"Site: {site.get('site_id','')} - {site.get('site_name','')}", 0, 1)
    pdf.ln(3)
    
    pdf.set_font('Helvetica', '', 9)
    info = [
        ('Status', site.get('status','-')), ('Progress', f"{site.get('progress','0')}%"),
        ('PM', site.get('pm','-')), ('Vendor', site.get('vendor','-')),
        ('Plan Start', site.get('start_date','-')), ('Plan End', site.get('end_date','-'))
    ]
    for label, value in info:
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(30, 6, label, 0, 0)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 6, str(value), 0, 1)
    
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, 'Milestones:', 0, 1)
    
    site_ms = ms_df[ms_df['project_id']==site_id] if not ms_df.empty else pd.DataFrame()
    if not site_ms.empty:
        pdf.set_font('Helvetica', 'B', 7)
        for col, w in [('name',60),('status',20),('planned_end',25),('material_status',25)]:
            pdf.cell(w, 6, col.upper(), 1, 0, 'C')
        pdf.ln()
        pdf.set_font('Helvetica', '', 7)
        for _, ms in site_ms.iterrows():
            pdf.cell(60, 5, str(ms.get('name',''))[:30], 1, 0)
            pdf.cell(20, 5, str(ms.get('status','')), 1, 0, 'C')
            pdf.cell(25, 5, str(ms.get('planned_end',''))[:10], 1, 0, 'C')
            pdf.cell(25, 5, str(ms.get('material_status','')), 1, 0, 'C')
            pdf.ln()
    
    return pdf

def export_page():
    st.title("📄 Export Report")
    
    sites_df = read_sheet("projects")
    if sites_df.empty:
        st.warning("⚠️ Tambahkan site dulu!")
        return
    
    selected = st.selectbox("Pilih Site:", sites_df['id'].tolist(),
                           format_func=lambda x: f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
    
    if st.button("📄 Generate PDF Report", type="primary"):
        with st.spinner("Generating..."):
            pdf = generate_site_pdf(selected)
            if pdf:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    pdf.output(tmp.name)
                    with open(tmp.name, 'rb') as f:
                        st.download_button("📥 Download PDF", f.read(),
                                          f"report_{datetime.now().strftime('%Y%m%d')}.pdf",
                                          "application/pdf")
                st.success("✅ Report siap download!")

if __name__ == "__main__":
    export_page()