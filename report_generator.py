import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF
import tempfile
import os

class FullReportPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, 'PM System - Daily Report', 0, 1, 'C')
        self.set_font('Helvetica', 'I', 9)
        self.cell(0, 5, f'Generated: {datetime.now().strftime("%d %b %Y, %H:%M")}', 0, 1, 'C')
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 7)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')
    
    def section_title(self, title):
        self.set_font('Helvetica', 'B', 13)
        self.set_fill_color(30, 60, 114)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, f'  {title}', 0, 1, 'L', True)
        self.set_text_color(0, 0, 0)
        self.ln(3)

def generate_daily_report(all_data):
    pdf = FullReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    sites_df = all_data.get('projects', pd.DataFrame())
    ms_df = all_data.get('milestones', pd.DataFrame())
    mat_df = all_data.get('materials', pd.DataFrame())
    insights_df = all_data.get('ai_insights', pd.DataFrame())
    
    # Konversi
    if not sites_df.empty and 'progress' in sites_df.columns:
        sites_df['progress'] = pd.to_numeric(sites_df['progress'], errors='coerce').fillna(0)
    if not mat_df.empty:
        for c in ['current_stock', 'min_stock']:
            if c in mat_df.columns:
                mat_df[c] = pd.to_numeric(mat_df[c], errors='coerce').fillna(0)
    
    # ===== 1. EXECUTIVE SUMMARY =====
    pdf.section_title('1. EXECUTIVE SUMMARY')
    
    total = len(sites_df)
    avg_prog = sites_df['progress'].mean() if not sites_df.empty else 0
    on_track = len(sites_df[sites_df['status']=='ON_TRACK']) if not sites_df.empty else 0
    delayed = len(sites_df[sites_df['status'].isin(['DELAYED','CRITICAL'])]) if not sites_df.empty else 0
    health_score = round((on_track/total)*100) if total > 0 else 0
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, f'Total Site: {total}', 0, 1)
    pdf.cell(0, 6, f'Avg Progress: {avg_prog:.1f}%', 0, 1)
    pdf.cell(0, 6, f'On Track: {on_track} | Delayed: {delayed}', 0, 1)
    pdf.cell(0, 6, f'Health Score: {health_score}%', 0, 1)
    
    forecast = datetime.now() + timedelta(days=int((100-avg_prog)*2))
    pdf.cell(0, 6, f'Forecast Completion: {forecast.strftime("%d %b %Y")}', 0, 1)
    pdf.ln(3)
    
    # ===== 2. SITE PROGRESS =====
    pdf.section_title('2. SITE PROGRESS')
    
    if not sites_df.empty:
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(30, 6, 'Site ID', 1, 0, 'C', True)
        pdf.cell(45, 6, 'Site Name', 1, 0, 'C', True)
        pdf.cell(20, 6, 'Status', 1, 0, 'C', True)
        pdf.cell(20, 6, 'Progress', 1, 0, 'C', True)
        pdf.cell(25, 6, 'PM', 1, 0, 'C', True)
        pdf.ln()
        
        pdf.set_font('Helvetica', '', 7)
        for _, s in sites_df.head(20).iterrows():
            pdf.cell(30, 5, str(s.get('site_id',''))[:12], 1, 0)
            pdf.cell(45, 5, str(s.get('site_name',''))[:22], 1, 0)
            pdf.cell(20, 5, str(s.get('status','')), 1, 0, 'C')
            pdf.cell(20, 5, f"{s.get('progress',0):.0f}%", 1, 0, 'C')
            pdf.cell(25, 5, str(s.get('pm',''))[:12], 1, 0)
            pdf.ln()
    pdf.ln(3)
    
    # ===== 3. MILESTONE STATUS =====
    pdf.section_title('3. MILESTONE STATUS')
    
    if not ms_df.empty:
        total_ms = len(ms_df)
        done_ms = len(ms_df[ms_df['status']=='DONE'])
        delayed_ms = len(ms_df[ms_df['status']=='DELAYED'])
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, f'Total Milestones: {total_ms}', 0, 1)
        pdf.cell(0, 6, f'Done: {done_ms} ({round(done_ms/total_ms*100,1) if total_ms>0 else 0}%)', 0, 1)
        pdf.cell(0, 6, f'Delayed: {delayed_ms}', 0, 1)
        pdf.ln(2)
        
        # Delay reasons
        if 'delay_reason' in ms_df.columns:
            delays = ms_df[ms_df['delay_reason'].notna() & (ms_df['delay_reason']!='') & (ms_df['delay_reason']!='Tidak Ada')]
            if not delays.empty:
                pdf.set_font('Helvetica', 'B', 9)
                pdf.cell(0, 6, 'Delay Reasons:', 0, 1)
                pdf.set_font('Helvetica', '', 8)
                for reason, count in delays['delay_reason'].value_counts().items():
                    pdf.cell(0, 5, f'  - {reason}: {count} milestone', 0, 1)
    pdf.ln(3)
    
    # ===== 4. MATERIAL STATUS =====
    pdf.section_title('4. MATERIAL STATUS')
    
    if not mat_df.empty:
        critical = mat_df[mat_df['current_stock'] < mat_df['min_stock']]
        warning = mat_df[(mat_df['current_stock'] >= mat_df['min_stock']) & 
                        (mat_df['current_stock'] < mat_df['min_stock'] * 1.5)]
        safe = mat_df[mat_df['current_stock'] >= mat_df['min_stock'] * 1.5]
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, f'Critical: {len(critical)} | Warning: {len(warning)} | Safe: {len(safe)}', 0, 1)
        pdf.ln(2)
        
        if not critical.empty:
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(0, 6, 'Critical Materials:', 0, 1)
            pdf.set_font('Helvetica', '', 8)
            for _, m in critical.iterrows():
                gap = m['min_stock'] - m['current_stock']
                pdf.cell(0, 5, f'  - {m["name"]}: Stok {m["current_stock"]} (Min: {m["min_stock"]}, Kurang: {gap:.0f})', 0, 1)
    pdf.ln(3)
    
    # ===== 5. AI INSIGHTS =====
    pdf.section_title('5. AI INSIGHTS')
    
    if not insights_df.empty:
        latest = insights_df.iloc[-1]
        pdf.set_font('Helvetica', '', 9)
        pdf.multi_cell(0, 5, str(latest.get('description', 'No insights yet.')))
        pdf.ln(2)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 6, 'Recommendations:', 0, 1)
        pdf.set_font('Helvetica', '', 8)
        for rec in str(latest.get('recommendation', '')).split(';'):
            if rec.strip():
                pdf.cell(0, 5, f'  • {rec.strip()}', 0, 1)
    
    # ===== 6. CRITICAL ALERTS =====
    pdf.section_title('6. CRITICAL ALERTS')
    
    alerts = []
    if not sites_df.empty:
        for _, s in sites_df[sites_df['status']=='CRITICAL'].iterrows():
            alerts.append(f'Site {s["site_id"]}: Progress {s["progress"]:.0f}%')
    if not mat_df.empty:
        for _, m in critical.iterrows():
            alerts.append(f'Material {m["name"]}: Stok {m["current_stock"]} (Min: {m["min_stock"]})')
    if not ms_df.empty:
        cr = len(ms_df[ms_df['status']=='DELAYED'])
        if cr > 0:
            alerts.append(f'{cr} milestone delayed')
    
    if alerts:
        pdf.set_font('Helvetica', '', 9)
        for a in alerts:
            pdf.cell(0, 5, f'  ⚠ {a}', 0, 1)
    else:
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 5, 'No critical alerts.', 0, 1)
    
    return pdf
