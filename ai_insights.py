import streamlit as st
import pandas as pd
from supabase_db import read_sheet, insert_row, generate_id, now_str

def calculate_risk(site_id):
    ms_df = read_sheet("milestones")
    sites_df = read_sheet("projects")
    
    if ms_df.empty:
        return 0, "Tidak ada data milestone", [], []
    
    site_ms = ms_df[ms_df['project_id'] == site_id]
    if site_ms.empty:
        return 0, "Tidak ada milestone", [], []
    
    delayed = len(site_ms[site_ms['status'] == 'DELAYED'])
    total = len(site_ms)
    done = len(site_ms[site_ms['status'] == 'DONE'])
    
    progress = (done / total * 100) if total > 0 else 0
    delay_factor = min(delayed / total * 100, 100) if total > 0 else 0
    progress_gap = 100 - progress
    
    risk_score = min(round((delay_factor * 0.4) + (progress_gap * 0.35) + (delayed * 5)), 100)
    
    problems = []
    recommendations = []
    
    if delayed > 0:
        problems.append(f"{delayed} milestone terlambat")
        recommendations.append("⚠️ Review jadwal milestone yang terlambat")
    
    if progress < 30:
        problems.append("Progress sangat rendah (<30%)")
        recommendations.append("🚀 Percepat eksekusi milestone awal")
    
    if risk_score > 70:
        recommendations.append("🔴 Tindakan segera diperlukan!")
    elif risk_score > 40:
        recommendations.append("🟡 Perlu perhatian manajemen")
    else:
        recommendations.append("✅ Site dalam kondisi baik")
    
    if risk_score > 50:
        predicted_delay = int(risk_score * 0.15)
        prediction = f"Diprediksi terlambat {predicted_delay} hari"
    else:
        prediction = "Site diprediksi selesai tepat waktu"
    
    return risk_score, prediction, problems, recommendations


def ai_insights_page():
    st.title("🤖 AI Insights & Recommendations")
    
    sites_df = read_sheet("projects")
    if sites_df.empty:
        st.warning("⚠️ Tambahkan site dulu!")
        return
    
    selected = st.selectbox("Pilih Site:", sites_df['id'].tolist(),
                           format_func=lambda x: f"{sites_df[sites_df['id']==x]['site_id'].values[0]} - {sites_df[sites_df['id']==x]['site_name'].values[0]}")
    
    if selected and st.button("🔍 Generate AI Insights", type="primary"):
        with st.spinner("Menganalisis..."):
            risk, prediction, problems, recs = calculate_risk(selected)
            
            col1, col2 = st.columns([1, 2])
            with col1:
                color = '🟢' if risk < 40 else ('🟡' if risk < 70 else '🔴')
                st.metric(f"{color} Risk Score", f"{risk}/100")
                if risk < 40:
                    st.success("Risiko Rendah")
                elif risk < 70:
                    st.warning("Risiko Sedang")
                else:
                    st.error("Risiko Tinggi!")
            
            with col2:
                st.subheader("📋 Ringkasan")
                site = sites_df[sites_df['id']==selected].iloc[0]
                st.info(f"Site: **{site.get('site_id','?')}** | Progress: **{site.get('progress','0')}%** | {prediction}")
            
            st.subheader("🔍 Masalah Terdeteksi")
            if problems:
                for p in problems:
                    st.error(f"• {p}")
            else:
                st.success("✅ Tidak ada masalah")
            
            st.subheader("💡 Rekomendasi")
            for r in recs:
                st.info(r)
            
            st.subheader("🔄 What-If Simulation")
            sim_days = st.slider("Jika milestone dipercepat...", 1, 30, 7)
            sim_risk = max(0, risk - (sim_days * 2))
            st.write(f"Risk Score simulasi: {sim_risk}/100")
            if sim_risk < risk:
                st.success(f"✅ Risiko berkurang {risk - sim_risk} poin!")
            
            insert_row("ai_insights", {
                'id': generate_id(), 'project_id': selected,
                'insight_type': 'FULL_ANALYSIS', 'risk_score': str(risk),
                'description': prediction, 'recommendation': '; '.join(recs),
                'created_at': now_str()
            })

if __name__ == "__main__":
    ai_insights_page()
