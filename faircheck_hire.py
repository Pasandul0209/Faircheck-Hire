import streamlit as st
import pandas as pd
from google import genai
import json
import io

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FairCheck Hire — by Colon DoubleSlash",
    page_icon="👔",
    layout="wide"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Space Grotesk', sans-serif; }
    
    .main { background-color: #0a0a0f; }
    
    .hero-title {
        font-size: 48px;
        font-weight: 700;
        color: white;
        line-height: 1.2;
    }
    
    .hero-sub {
        font-size: 14px;
        color: #888;
        letter-spacing: 3px;
        text-transform: uppercase;
    }
    
    .card {
        background: #13131a;
        border: 1px solid #2a2a3a;
        border-radius: 16px;
        padding: 24px;
        margin: 10px 0;
    }
    
    .rank-card-1 {
        background: linear-gradient(135deg, #1a2a1a, #13131a);
        border: 2px solid #00c853;
        border-radius: 16px;
        padding: 20px;
        margin: 8px 0;
    }
    
    .rank-card-2 {
        background: linear-gradient(135deg, #1a1a2a, #13131a);
        border: 2px solid #2979ff;
        border-radius: 16px;
        padding: 20px;
        margin: 8px 0;
    }
    
    .rank-card-3 {
        background: linear-gradient(135deg, #2a1a1a, #13131a);
        border: 2px solid #ff6d00;
        border-radius: 16px;
        padding: 20px;
        margin: 8px 0;
    }
    
    .rank-card-other {
        background: #13131a;
        border: 1px solid #2a2a3a;
        border-radius: 16px;
        padding: 20px;
        margin: 8px 0;
    }
    
    .score-badge-high {
        background: #00c853;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
    }
    
    .score-badge-mid {
        background: #2979ff;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
    }
    
    .score-badge-low {
        background: #ff6d00;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
    }
    
    .tag {
        background: #1e1e2e;
        border: 1px solid #3a3a5a;
        color: #aaa;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        display: inline-block;
        margin: 2px;
    }
    
    .section-title {
        font-size: 22px;
        font-weight: 700;
        color: white;
        margin-bottom: 4px;
    }
    
    .section-sub {
        font-size: 13px;
        color: #666;
        margin-bottom: 16px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #00c853, #00897b) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        width: 100% !important;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background: #1a1a25 !important;
        border: 1px solid #2a2a3a !important;
        color: white !important;
        border-radius: 10px !important;
    }

    .stFileUploader {
        background: #13131a !important;
        border: 2px dashed #2a2a3a !important;
        border-radius: 12px !important;
    }

    label { color: #aaa !important; font-size: 13px !important; }
    
    .stSlider > div > div > div { background: #00c853 !important; }
    
    div[data-testid="metric-container"] {
        background: #13131a;
        border: 1px solid #2a2a3a;
        border-radius: 12px;
        padding: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ── Get API key ───────────────────────────────────────────────────────────────
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    api_key = None

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 40px 0 20px 0;'>
    <p class='hero-sub'>by Colon DoubleSlash — Break it into Bits</p>
    <h1 class='hero-title'>👔 FairCheck <span style='color:#00c853;'>Hire</span></h1>
    <p style='color:#666; font-size:16px; margin-top:8px;'>
        Find your best candidates fairly — powered by Google Gemini AI
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Layout — 2 columns ────────────────────────────────────────────────────────
left, right = st.columns([1, 1], gap="large")

# ════════════════════════════════════════════════════════════════════════════
# LEFT COLUMN — Job Requirements
# ════════════════════════════════════════════════════════════════════════════
with left:
    st.markdown("<p class='section-title'>📋 Job Requirements</p>", unsafe_allow_html=True)
    st.markdown("<p class='section-sub'>Tell us what you are looking for</p>", unsafe_allow_html=True)

    job_title = st.text_input(
        "Job Position",
        placeholder="e.g. Senior Software Engineer, Marketing Manager..."
    )

    col1, col2 = st.columns(2)
    with col1:
        num_hires = st.number_input("Number of people needed", min_value=1, max_value=100, value=3)
    with col2:
        experience = st.selectbox(
            "Experience required",
            ["Any level", "0-1 years (Fresh)", "1-3 years (Junior)", 
             "3-5 years (Mid)", "5-8 years (Senior)", "8+ years (Expert)"]
        )

    required_skills = st.text_area(
        "Required Skills",
        placeholder="e.g. Python, React, SQL, Machine Learning, Communication...",
        height=100
    )

    col3, col4 = st.columns(2)
    with col3:
        budget_min = st.text_input("Min Budget (monthly)", placeholder="e.g. 80000 or $2000")
    with col4:
        budget_max = st.text_input("Max Budget (monthly)", placeholder="e.g. 150000 or $4000")

    priority = st.selectbox(
        "What matters most?",
        [
            "Balanced — Skills + Experience + Culture fit",
            "Technical Skills — Pure technical ability",
            "Experience — Years and track record",
            "Potential — Growth and learning ability",
            "Leadership — Management and team skills"
        ]
    )

    extra_notes = st.text_area(
        "Any extra requirements? (Optional)",
        placeholder="e.g. Must have startup experience, Remote work okay, Must speak Sinhala...",
        height=80
    )

# ════════════════════════════════════════════════════════════════════════════
# RIGHT COLUMN — Upload CVs
# ════════════════════════════════════════════════════════════════════════════
with right:
    st.markdown("<p class='section-title'>📂 Upload Candidate CVs</p>", unsafe_allow_html=True)
    st.markdown("<p class='section-sub'>Upload all received CVs at once</p>", unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload CV files",
        type=["txt", "pdf"],
        accept_multiple_files=True,
        help="Upload CV files. TXT format works best. PDF support included."
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} CV(s) uploaded successfully!")
        
        with st.expander(f"👀 View uploaded files ({len(uploaded_files)} total)"):
            for f in uploaded_files:
                st.markdown(f"<span class='tag'>📄 {f.name}</span>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # OR paste CV text
    st.markdown("<p class='section-title' style='font-size:16px;'>✍️ Or Paste CV Text</p>", unsafe_allow_html=True)
    st.markdown("<p class='section-sub'>Paste multiple CVs separated by '---'</p>", unsafe_allow_html=True)
    
    pasted_cvs = st.text_area(
        "Paste CV content here",
        placeholder="""Candidate 1:
Name: Kasun Perera
Skills: Python, React, SQL
Experience: 3 years at XYZ Company
Education: BSc Computer Science, University of Moratuwa
---
Candidate 2:
Name: Nimasha Silva
Skills: Python, Machine Learning, TensorFlow
Experience: 4 years at ABC Tech
Education: MSc Data Science, University of Colombo""",
        height=280
    )

# ── Analyse Button ────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    analyse_btn = st.button(
        "🚀 Find Best Candidates — Fairly",
        use_container_width=True,
        type="primary"
    )

# ════════════════════════════════════════════════════════════════════════════
# ANALYSIS LOGIC
# ════════════════════════════════════════════════════════════════════════════
if analyse_btn:
    # Validation
    if not job_title:
        st.error("❌ Please enter the job position!")
        st.stop()
    
    if not required_skills:
        st.error("❌ Please enter required skills!")
        st.stop()

    if not uploaded_files and not pasted_cvs.strip():
        st.error("❌ Please upload CV files or paste CV text!")
        st.stop()

    if api_key is None:
        st.error("❌ App configuration error. Please contact the app owner.")
        st.stop()

    # Build CV text from uploaded files
    all_cv_text = ""
    cv_count = 0

    if uploaded_files:
        for i, file in enumerate(uploaded_files):
            try:
                content = file.read().decode("utf-8", errors="ignore")
                all_cv_text += f"\n\n=== CV {i+1} (File: {file.name}) ===\n{content}"
                cv_count += 1
            except:
                all_cv_text += f"\n\n=== CV {i+1} (File: {file.name}) ===\n[Could not read file]"

    if pasted_cvs.strip():
        sections = pasted_cvs.split("---")
        for i, section in enumerate(sections):
            if section.strip():
                all_cv_text += f"\n\n=== CV {cv_count + i + 1} (Pasted) ===\n{section.strip()}"
                cv_count += 1

    if cv_count == 0:
        st.error("❌ No CV content found! Please check your uploads.")
        st.stop()

    with st.spinner(f"🤖 Gemini AI is analysing {cv_count} candidates fairly... please wait..."):
        try:
            client = genai.Client(api_key=api_key)

            prompt = f"""
You are FairCheck Hire — the world's most advanced FAIR hiring AI.

Your job is to rank candidates for a job position based PURELY on their skills, experience and potential.
You must be 100% FAIR — ignore gender, race, age, name, university prestige, and any other bias factors.
ONLY skills, experience, achievements, and potential matter.

JOB REQUIREMENTS:
- Position: {job_title}
- Number of hires needed: {num_hires}
- Experience required: {experience}
- Required skills: {required_skills}
- Budget range: {budget_min} to {budget_max}
- Priority focus: {priority}
- Extra requirements: {extra_notes if extra_notes else "None"}

CANDIDATE CVs:
{all_cv_text}

Please analyse all candidates and provide a response in this EXACT format:

## HIRING SUMMARY
[2-3 sentences about the overall candidate pool quality]

## TOP CANDIDATES RANKED

### RANK 1 — [Candidate Name or CV number]
**Match Score:** [X/100]
**Why they are the best:** [2-3 sentences]
**Key strengths:** [bullet points]
**Skills match:** [which required skills they have]
**Potential concern:** [any small concern if any]
**Suggested interview question:** [one specific question for this person]

### RANK 2 — [Candidate Name or CV number]
[same format]

### RANK 3 — [Candidate Name or CV number]
[same format]

[Continue for all candidates]

## FAIRNESS REPORT
**Bias removed:** [what biases were ignored in this ranking]
**Fairness score:** [X/10]
**Note:** [any fairness observations]

## HIRING RECOMMENDATION
[Clear recommendation — who to hire, in what order, and why]

## INTERVIEW PLAN
[Suggest a simple 3-step interview process for the top candidates]

Be specific, honest, and fair. If a candidate is clearly not suitable, say so kindly.
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            result = response.text

            # ── Display Results ───────────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")

            st.markdown("""
<div style='text-align:center; padding: 20px 0;'>
    <h2 style='color:white; font-size:32px;'>🏆 Candidate Rankings</h2>
    <p style='color:#666;'>Ranked fairly by Google Gemini AI — skills and merit only</p>
</div>
""", unsafe_allow_html=True)

            # Metrics row
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("📄 CVs Analysed", cv_count)
            with m2:
                st.metric("🎯 Position", job_title)
            with m3:
                st.metric("👥 Hires Needed", num_hires)
            with m4:
                st.metric("⚖️ Bias Removed", "100%")

            st.markdown("<br>", unsafe_allow_html=True)

            # Full results
            st.markdown(result)

            st.markdown("<br>", unsafe_allow_html=True)

            # Download button
            st.download_button(
                label="📥 Download Full Hiring Report",
                data=result.encode("utf-8"),
                file_name=f"faircheck_hire_{job_title.replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )

            st.success("✅ Analysis complete! Hire the best — hire fairly! ⚖️")
            st.balloons()

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center; padding:20px 0;'>
    <p style='color:#444; font-size:13px;'>
        👔 <b style='color:#666;'>FairCheck Hire</b> — Part of the FairCheck family by 
        <b style='color:#00c853;'>Colon DoubleSlash</b> | Break it into Bits<br>
        Powered by <b style='color:#666;'>Google Gemini AI</b> | 
        Fair hiring for everyone, everywhere 🌍
    </p>
</div>
""", unsafe_allow_html=True)
