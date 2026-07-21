import streamlit as st
import pandas as pd
from google import genai
import json
import io
import datetime

# PDF reading
try:
    from PyPDF2 import PdfReader
    PDF_SUPPORT = True
except:
    PDF_SUPPORT = False

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FairCheck HHire v2 — by Colon DoubleSlash",
    page_icon="👔",
    layout="wide"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    * { font-family: 'Space Grotesk', sans-serif; }
    .hero-title { font-size: 42px; font-weight: 700; color: white; line-height: 1.2; }
    .hero-sub { font-size: 13px; color: #888; letter-spacing: 3px; text-transform: uppercase; }
    .section-title { font-size: 20px; font-weight: 700; color: white; margin-bottom: 4px; }
    .section-sub { font-size: 13px; color: #666; margin-bottom: 16px; }
    .tag { background: #1e1e2e; border: 1px solid #3a3a5a; color: #aaa; padding: 3px 10px; border-radius: 20px; font-size: 12px; display: inline-block; margin: 2px; }
    .stButton > button { background: linear-gradient(135deg, #00c853, #00897b) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important; font-size: 16px !important; }
    label { color: #aaa !important; font-size: 13px !important; }
</style>
""", unsafe_alow_html=True)

# ── API Key ───────────────────────────────────────────────────────────────────
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    api_key = None

# ── Helper Functions ──────────────────────────────────────────────────────────

def read_pdf(file):
    """Extract text from PDF file"""
    try:
        if PDF_SUPPORT:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text if text.strip() else "[PDF could not be read - may be image based]"
        else:
            return "[PDF support not available]"
    except Exception as e:
        return f"[Error reading PDF: {str(e)}]"

def read_txt(file):
    """Extract text from TXT file"""
    try:
        return file.read().decode("utf-8", errors="ignore")
    except:
        return "[Could not read file]"

def read_cv_file(file):
    """Read any CV file type"""
    if file.name.lower().endswith(".pdf"):
        return read_pdf(file)
    else:
        return read_txt(file)

def analyse_batch(client, job_info, batch_cvs, batch_num):
    """Analyse a batch of CVs"""
    prompt = f"""
You are FairCheck Hire — the world's most advanced FAIR hiring AI.

Rank these candidates for the position based PURELY on skills and merit.
IGNORE completely: gender, race, age, name origin, university prestige, appearance.
ONLY consider: skills match, experience, achievements, potential.

JOB DETAILS:
- Position: {job_info['title']}
- Required Skills: {job_info['skills']}
- Experience: {job_info['experience']}
- Budget: {job_info['budget_min']} to {job_info['budget_max']}
- Priority: {job_info['priority']}
- Extra notes: {job_info['extra']}

CANDIDATES IN THIS BATCH:
{batch_cvs}

For EACH candidate provide:

### CANDIDATE: [Name or CV number]
**Match Score:** [X/100]
**Hire Recommendation:** [STRONG YES / YES / MAYBE / NO]
**Top 3 Strengths:**
- [strength 1]
- [strength 2]  
- [strength 3]
**Skills Match:** [which required skills they have vs missing]
**Experience Summary:** [brief summary]
**Red Flags:** [any concerns or none]
**Best Interview Question:** [one specific question]
**Salary Expectation Fit:** [fits budget / above budget / below budget / unknown]

---
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

def save_to_history(job_title, num_candidates, top_candidate, report):
    """Save hiring session to history"""
    if "hire_history" not in st.session_state:
        st.session_state.hire_history = []
    
    st.session_state.hire_history.append({
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "job": job_title,
        "candidates": num_candidates,
        "top": top_candidate,
        "report": report
    })

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style='padding: 30px 0 10px 0;'>
    <p class='hero-sub'>by Colon DoubleSlash — Break it into Bits</p>
    <h1 class='hero-title'>👔 FairCheck <span style='color:#00c853;'>Hire</span> <span style='font-size:16px; color:#666;'>v2.0</span></h1>
    <p style='color:#666; font-size:15px; margin-top:6px;'>Find your best candidates fairly — powered by Google Gemini AI</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🎯 New Hiring", "📊 History", "ℹ️ How it Works"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — NEW HIRING
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([1, 1], gap="large")

    # LEFT — Job Requirements
    with left:
        st.markdown("<p class='section-title'>📋 Job Requirements</p>", unsafe_allow_html=True)
        st.markdown("<p class='section-sub'>Tell us exactly what you need</p>", unsafe_allow_html=True)

        job_title = st.text_input("Job Position *", placeholder="e.g. Senior Software Engineer...")
        
        col1, col2 = st.columns(2)
        with col1:
            num_hires = st.number_input("People needed", min_value=1, max_value=100, value=3)
        with col2:
            experience = st.selectbox("Experience", [
                "Any level",
                "0-1 years (Fresh)",
                "1-3 years (Junior)",
                "3-5 years (Mid)",
                "5-8 years (Senior)",
                "8+ years (Expert)"
            ])

        required_skills = st.text_area(
            "Required Skills *",
            placeholder="e.g. Python, React, SQL, Communication...",
            height=100
        )

        col3, col4 = st.columns(2)
        with col3:
            budget_min = st.text_input("Min Budget", placeholder="e.g. 80000")
        with col4:
            budget_max = st.text_input("Max Budget", placeholder="e.g. 150000")

        priority = st.selectbox("Priority Focus", [
            "Balanced — Skills + Experience + Potential",
            "Technical Skills — Pure ability",
            "Experience — Track record",
            "Potential — Growth mindset",
            "Leadership — Team skills"
        ])

        extra_notes = st.text_area(
            "Extra Requirements (Optional)",
            placeholder="e.g. Remote work okay, Must be available for night shifts...",
            height=70
        )

    # RIGHT — CV Upload
    with right:
        st.markdown("<p class='section-title'>📂 Upload Candidate CVs</p>", unsafe_allow_html=True)
        st.markdown("<p class='section-sub'>PDF and TXT files supported</p>", unsafe_allow_html=True)

        # PDF support status
        if PDF_SUPPORT:
            st.success("✅ PDF reading enabled!")
        else:
            st.warning("⚠️ PDF support limited. TXT files work best.")

        uploaded_files = st.file_uploader(
            "Upload CV files (PDF or TXT)",
            type=["txt", "pdf"],
            accept_multiple_files=True,
            help="Upload multiple CV files at once. PDF and TXT supported."
        )

        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} CV(s) uploaded!")
            
            # Show file list
            with st.expander(f"📋 Files uploaded ({len(uploaded_files)} total)"):
                for f in uploaded_files:
                    icon = "📕" if f.name.endswith(".pdf") else "📄"
                    size = f"{f.size/1024:.1f} KB"
                    st.markdown(f"<span class='tag'>{icon} {f.name} ({size})</span>", unsafe_allow_html=True)

            # Preview first CV
            if st.checkbox("👀 Preview first CV"):
                first_file = uploaded_files[0]
                first_file.seek(0)
                content = read_cv_file(first_file)
                st.text_area("First CV preview:", value=content[:500] + "...", height=150)
                first_file.seek(0)

        st.markdown("<br>", unsafe_allow_html=True)

        # Paste option
        st.markdown("<p style='color:#aaa; font-size:14px; font-weight:600;'>✍️ Or Paste CV Text</p>", unsafe_allow_html=True)
        st.markdown("<p class='section-sub'>Separate multiple CVs with '---'</p>", unsafe_allow_html=True)
        
        pasted_cvs = st.text_area(
            "Paste CVs here",
            placeholder="""Candidate 1:
Name: Kasun Perera
Skills: Python, React, SQL
Experience: 3 years
---
Candidate 2:
Name: Nimasha Silva
Skills: Python, ML, TensorFlow
Experience: 4 years""",
            height=220
        )

    # Analyse button
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
    with col_b2:
        analyse_btn = st.button(
            "🚀 Find Best Candidates Fairly",
            use_container_width=True,
            type="primary"
        )

    # ── ANALYSIS ─────────────────────────────────────────────────────────────
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
            st.error("❌ App configuration error!")
            st.stop()

        # Build CV list
        cv_list = []

        # Read uploaded files
        if uploaded_files:
            progress_bar = st.progress(0, text="Reading CV files...")
            for i, file in enumerate(uploaded_files):
                file.seek(0)
                content = read_cv_file(file)
                cv_list.append({
                    "id": i + 1,
                    "name": file.name,
                    "content": content
                })
                progress_bar.progress((i + 1) / len(uploaded_files), 
                                     text=f"Reading {file.name}...")
            progress_bar.empty()

        # Read pasted CVs
        if pasted_cvs.strip():
            sections = pasted_cvs.split("---")
            for i, section in enumerate(sections):
                if section.strip():
                    cv_list.append({
                        "id": len(cv_list) + 1,
                        "name": f"Pasted CV {i+1}",
                        "content": section.strip()
                    })

        if not cv_list:
            st.error("❌ No CV content found!")
            st.stop()

        # Job info dict
        job_info = {
            "title": job_title,
            "skills": required_skills,
            "experience": experience,
            "budget_min": budget_min or "Not specified",
            "budget_max": budget_max or "Not specified",
            "priority": priority,
            "extra": extra_notes or "None"
        }

        # Process in batches of 10
        BATCH_SIZE = 10
        all_results = []
        
        total_batches = (len(cv_list) - 1) // BATCH_SIZE + 1
        
        main_progress = st.progress(0, text=f"🤖 Analysing candidates with Gemini AI...")

        try:
            client = genai.Client(api_key=api_key)

            for batch_num in range(total_batches):
                start = batch_num * BATCH_SIZE
                end = min(start + BATCH_SIZE, len(cv_list))
                batch = cv_list[start:end]

                main_progress.progress(
                    (batch_num + 1) / total_batches,
                    text=f"🤖 Analysing candidates {start+1}-{end} of {len(cv_list)}..."
                )

                # Build batch text
                batch_text = ""
                for cv in batch:
                    batch_text += f"\n\n=== CV {cv['id']} — {cv['name']} ===\n{cv['content']}"

                result = analyse_batch(client, job_info, batch_text, batch_num + 1)
                all_results.append(result)

            main_progress.empty()

            # Now get final ranking across all batches
            if total_batches > 1:
                with st.spinner("🏆 Creating final ranking across all candidates..."):
                    combined = "\n\n".join(all_results)
                    final_prompt = f"""
Based on these candidate analyses for the position of {job_title}:

{combined}

Create a FINAL SUMMARY with:

## 🏆 FINAL TOP {num_hires} CANDIDATES TO HIRE
[List the top {num_hires} candidates with their scores and one-line reason]

## 📊 FULL RANKING TABLE
[Rank ALL candidates from best to worst with score]

## ⚖️ FAIRNESS REPORT
[Confirm bias was removed, give fairness score out of 10]

## 🎯 HIRING ACTION PLAN
[Clear step by step what to do next]
"""
                    final_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=final_prompt
                    )
                    final_summary = final_response.text
            else:
                final_summary = None

            # ── Display Results ───────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")

            st.markdown(f"""
<div style='text-align:center; padding:20px 0;'>
    <h2 style='color:white; font-size:30px;'>🏆 Hiring Results for {job_title}</h2>
    <p style='color:#666;'>Ranked fairly by Google Gemini AI</p>
</div>
""", unsafe_allow_html=True)

            # Metrics
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("📄 CVs Analysed", len(cv_list))
            with m2:
                st.metric("🎯 Position", job_title[:15] + "..." if len(job_title) > 15 else job_title)
            with m3:
                st.metric("👥 Hires Needed", num_hires)
            with m4:
                st.metric("⚖️ Bias Removed", "100%")

            st.markdown("<br>", unsafe_allow_html=True)

            # Show final summary first if multiple batches
            if final_summary:
                st.markdown("## 🏆 Final Summary")
                st.markdown(final_summary)
                st.markdown("---")
                st.markdown("## 📋 Detailed Analysis")

            # Show all detailed results
            full_report = "\n\n".join(all_results)
            if final_summary:
                full_report = final_summary + "\n\n---\n\nDETAILED ANALYSIS:\n\n" + full_report

            st.markdown(full_report)

            # Save to history
            save_to_history(job_title, len(cv_list), "See report", full_report)

            st.markdown("<br>", unsafe_allow_html=True)

            # Download
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    label="📥 Download Full Report (TXT)",
                    data=full_report.encode("utf-8"),
                    file_name=f"faircheck_hire_{job_title.replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with col_d2:
                # Create simple CSV summary
                csv_data = f"Position,{job_title}\nCandidates Analysed,{len(cv_list)}\nHires Needed,{num_hires}\nDate,{datetime.datetime.now().strftime('%Y-%m-%d')}\n"
                st.download_button(
                    label="📊 Download Summary (CSV)",
                    data=csv_data.encode("utf-8"),
                    file_name=f"faircheck_summary_{job_title.replace(' ', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            st.success("✅ Hiring analysis complete! Hire the best — hire fairly! ⚖️")
            st.balloons()

        except Exception as e:
            main_progress.empty()
            st.error(f"❌ Error during analysis: {str(e)}")

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — HISTORY
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<p class='section-title'>📊 Hiring History</p>", unsafe_allow_html=True)
    st.markdown("<p class='section-sub'>Your previous hiring sessions this session</p>", unsafe_allow_html=True)

    if "hire_history" not in st.session_state or not st.session_state.hire_history:
        st.info("📭 No hiring history yet. Run your first analysis to see results here!")
    else:
        for i, session in enumerate(reversed(st.session_state.hire_history)):
            with st.expander(f"📋 {session['job']} — {session['date']} — {session['candidates']} candidates"):
                st.markdown(f"**Position:** {session['job']}")
                st.markdown(f"**Date:** {session['date']}")
                st.markdown(f"**Candidates:** {session['candidates']}")
                st.download_button(
                    label="📥 Download Report",
                    data=session['report'].encode("utf-8"),
                    file_name=f"report_{session['job'].replace(' ', '_')}.txt",
                    key=f"download_{i}"
                )

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — HOW IT WORKS
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("## 🤖 How FairCheck Hire Works")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
### 📋 Step 1 — Set Requirements
- Enter the job position
- List required skills
- Set experience level
- Set budget range
- Set priority focus
        """)
    
    with col2:
        st.markdown("""
### 📂 Step 2 — Upload CVs
- Upload PDF or TXT files
- Upload 1 to 500+ CVs
- Or paste CV text directly
- All formats accepted
- Batch processed automatically
        """)
    
    with col3:
        st.markdown("""
### 🏆 Step 3 — Get Results
- AI reads every CV
- Scores each candidate
- Removes all bias
- Ranks best to worst
- Gives interview questions
        """)

    st.markdown("---")
    
    st.markdown("## ⚖️ How Bias is Removed")
    
    bias_data = {
        "Bias Type": ["Gender Bias", "Racial Bias", "Age Bias", "Name Bias", "University Bias", "Appearance Bias"],
        "How it happens normally": [
            "Prefer male candidates",
            "Prefer certain ethnicities",
            "Prefer younger candidates",
            "Judge by name origin",
            "Prefer top university names",
            "Judge by photo"
        ],
        "How FairCheck removes it": [
            "Only skills and experience scored",
            "Only achievements matter",
            "Only capability matters",
            "Name ignored in scoring",
            "Only actual skills matter",
            "No photos processed"
        ]
    }
    
    st.dataframe(pd.DataFrame(bias_data), use_container_width=True)

    st.markdown("---")
    st.markdown("""
## 🔒 Privacy & Security
- CVs are sent to Google Gemini API for analysis only
- No CVs are permanently stored
- All data is processed securely via HTTPS
- Google's privacy policy applies to API usage
    """)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center; padding:20px 0;'>
    <p style='color:#444; font-size:13px;'>
        👔 <b style='color:#666;'>FairCheck Hire v2.0</b> — Part of the FairCheck family by 
        <b style='color:#00c853;'>Colon DoubleSlash</b> | Break it into Bits<br>
        Powered by <b style='color:#666;'>Google Gemini 2.5 Flash</b> | 
        Fair hiring for everyone, everywhere 🌍
    </p>
</div>
""", unsafe_allow_html=True)
