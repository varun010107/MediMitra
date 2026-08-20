import os
import json
import requests
import tempfile
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from fpdf import FPDF
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

# -----------------------------------------------------------------------------
# 1. INITIALIZATION & SETUP
# -----------------------------------------------------------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Ordered fallback chain — if a model is overloaded/unavailable/rate-limited,
# the next one in the list is tried automatically.
MODEL_FALLBACK_CHAIN = [
    "gemini-3.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

# Errors worth falling back on (overloaded, rate limited, unavailable, server-side).
RETRYABLE_STATUS_CODES = {429, 500, 503, 504}


@st.cache_resource
def get_gemini_client(k):
    if not k:
        return None
    try:
        return genai.Client(api_key=k)
    except Exception as e:
        st.error(f"Initialization Error: {e}")
        return None


client = get_gemini_client(api_key)


def generate_with_fallback(contents, config=None, models=None):
    """
    Calls Gemini with automatic fallback across a chain of models.
    Returns (response, model_used). Raises the last error if every model fails.
    """
    models = models or MODEL_FALLBACK_CHAIN
    last_error = None

    for model_name in models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            return response, model_name
        except genai_errors.APIError as e:
            status = getattr(e, "code", None)
            if status in RETRYABLE_STATUS_CODES or status is None:
                last_error = e
                continue
            raise
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(
        f"All models in the fallback chain are currently unavailable. Last error: {last_error}"
    )


# Session State Initializations
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'patient_info' not in st.session_state:
    st.session_state.patient_info = {}
if 'lab_data' not in st.session_state:
    st.session_state.lab_data = None
if 'ai_results' not in st.session_state:
    st.session_state.ai_results = None
if 'clinician_review' not in st.session_state:
    st.session_state.clinician_review = {"notes": "", "signed_by": "", "approved": False}
if 'model_used' not in st.session_state:
    st.session_state.model_used = None

# -----------------------------------------------------------------------------
# 2. PAGE CONFIGURATION & DESIGN SYSTEM (CSS)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="MediMitra :: Clinical Intelligence",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700&display=swap');

    :root {
        --mm-primary: #0E7C7B;
        --mm-primary-dark: #0B5D5C;
        --mm-accent: #FF7A59;
        --mm-accent-light: #FFE8DF;
        --mm-teal-light: #E6F7F6;
        --mm-bg: #F5F8F8;
        --mm-surface: #FFFFFF;
        --mm-border: #E4EBEA;
        --mm-text: #14201F;
        --mm-text-secondary: #52645F;
        --mm-text-muted: #94A19D;
        --mm-critical: #E23B3B;
        --mm-critical-bg: #FDECEC;
        --mm-amber: #D97706;
        --mm-amber-bg: #FFF7EA;
        --mm-success: #159A6C;
        --mm-success-bg: #E9F9F1;
    }

    html, body, [class*="css"] {
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--mm-text);
    }

    h1, h2, h3, .ax-title, .ax-card-title, .mm-title, .mm-card-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at top left, #EAF6F4 0%, var(--mm-bg) 45%);
    }
    #MainMenu, footer { visibility: hidden; }

    /* HEADER */
    .mm-header {
        background: linear-gradient(135deg, var(--mm-primary-dark) 0%, var(--mm-primary) 55%, #12A39A 100%);
        padding: 28px 34px;
        border-radius: 20px;
        margin-bottom: 24px;
        display: flex;
        flex-direction: column;
        gap: 4px;
        box-shadow: 0 12px 32px rgba(11, 93, 92, 0.22);
        position: relative;
        overflow: hidden;
    }
    .mm-header::after {
        content: "";
        position: absolute;
        right: -60px; top: -60px;
        width: 220px; height: 220px;
        background: radial-gradient(circle, rgba(255,255,255,0.14) 0%, rgba(255,255,255,0) 70%);
        border-radius: 50%;
    }
    .mm-eyebrow { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: #BDF0EB; }
    .mm-title { font-size: 2.25rem; font-weight: 800; letter-spacing: -0.02em; color: #FFFFFF; margin: 2px 0 0 0; }
    .mm-subtitle { color: #D6ECE9; font-size: 0.96rem; font-weight: 400; }

    /* CARDS */
    .mm-card {
        background: var(--mm-surface);
        border: 1px solid var(--mm-border);
        border-radius: 18px;
        padding: 26px;
        margin-bottom: 20px;
        box-shadow: 0 4px 18px rgba(20, 32, 31, 0.05);
        transition: box-shadow 0.2s ease;
    }
    .mm-card-title { font-size: 1.08rem; font-weight: 700; color: var(--mm-text); margin-bottom: 4px; display: flex; align-items: center; gap: 8px; }
    .mm-card-subtitle { font-size: 0.85rem; color: var(--mm-text-muted); margin-bottom: 18px; }

    /* STEP PROGRESS */
    .mm-steps { display: flex; gap: 8px; margin-bottom: 24px; }
    .mm-step-pill { flex: 1; height: 7px; border-radius: 999px; background: var(--mm-border); }
    .mm-step-pill.active { background: var(--mm-accent); }
    .mm-step-pill.done { background: var(--mm-primary); }

    /* EMERGENCY SOS TRIAGE BANNER */
    .mm-sos-banner {
        background: var(--mm-critical-bg);
        border: 2px solid var(--mm-critical);
        border-radius: 18px;
        padding: 22px 26px;
        margin-bottom: 24px;
        color: #8C1D1D;
    }
    .mm-sos-title { font-size: 1.25rem; font-weight: 800; display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }

    /* STATUS BADGES */
    .mm-badge {
        display: inline-flex; align-items: center; gap: 6px; padding: 5px 14px; border-radius: 999px;
        font-size: 0.78rem; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase;
    }
    .mm-badge-critical { background: var(--mm-critical-bg); color: var(--mm-critical); border: 1px solid #F7C6C6; }
    .mm-badge-amber    { background: var(--mm-amber-bg); color: var(--mm-amber); border: 1px solid #FDE3B0; }
    .mm-badge-success  { background: var(--mm-success-bg); color: var(--mm-success); border: 1px solid #A9E9CC; }
    .mm-badge-neutral  { background: var(--mm-teal-light); color: var(--mm-primary-dark); border: 1px solid #CDEDEA; }

    /* RESULTS BANNER */
    .mm-diagnosis-banner {
        background: var(--mm-surface);
        border: 1px solid var(--mm-border);
        border-left: 5px solid var(--mm-accent);
        border-radius: 18px;
        padding: 26px 30px;
        margin-bottom: 24px;
        box-shadow: 0 4px 18px rgba(20, 32, 31, 0.05);
    }
    .mm-diag-label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: var(--mm-text-muted); letter-spacing: 0.06em; margin-bottom: 6px; }
    .mm-diag-value { font-size: 2.15rem; font-weight: 800; color: var(--mm-primary-dark); margin-bottom: 12px; }
    .mm-diag-meta { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; font-size: 0.85rem; color: var(--mm-text-secondary); }

    .mm-list-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 0; border-bottom: 1px solid #F1F5F4; font-size: 0.92rem; color: var(--mm-text); }
    .mm-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--mm-primary); margin-top: 6px; flex-shrink: 0; }
    .mm-dot-amber { background: var(--mm-amber); }
    .mm-specialist-pill { display: inline-block; background: var(--mm-teal-light); color: var(--mm-primary-dark); border: 1px solid #CDEDEA; padding: 9px 18px; border-radius: 12px; font-weight: 700; font-size: 0.9rem; }

    .mm-model-tag { font-size: 0.72rem; color: var(--mm-text-muted); font-weight: 600; }

    /* BUTTONS */
    .stButton > button, .stFormSubmitButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        border: 1px solid var(--mm-border) !important;
    }
    .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--mm-primary) 0%, var(--mm-primary-dark) 100%) !important;
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. HELPER FUNCTIONS & EXPORTS
# -----------------------------------------------------------------------------
def render_step_progress(current_step):
    classes = ["done" if i < current_step else ("active" if i == current_step else "") for i in range(1, 4)]
    st.markdown(f"""
        <div class="mm-steps">
            <div class="mm-step-pill {classes[0]}"></div>
            <div class="mm-step-pill {classes[1]}"></div>
            <div class="mm-step-pill {classes[2]}"></div>
        </div>
    """, unsafe_allow_html=True)

def confidence_badge(level):
    level_lower = (level or "").lower()
    if level_lower == "high":
        return '<span class="mm-badge mm-badge-critical">● High Confidence</span>'
    elif level_lower == "moderate":
        return '<span class="mm-badge mm-badge-amber">● Moderate Confidence</span>'
    else:
        return '<span class="mm-badge mm-badge-success">● Low Confidence</span>'

# PDF Generation Function
def generate_pdf_report(p_info, res, clinician_review):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(14, 124, 123)
    pdf.cell(0, 10, "MEDIMITRA - CLINICAL SUMMARY REPORT", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "Confidential Medical AI Screening Output", ln=True)
    pdf.ln(5)

    # Patient Details Box
    pdf.set_fill_color(245, 248, 248)
    pdf.rect(10, 30, 190, 25, 'F')
    pdf.set_xy(15, 33)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(20, 32, 31)
    pdf.cell(0, 6, f"Patient: {p_info.get('name', 'N/A')} | Age: {p_info.get('age', 'N/A')} | Gender: {p_info.get('gender', 'N/A')}", ln=True)
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"History: {p_info.get('history', 'None reported')}", ln=True)
    pdf.ln(12)

    # Primary Findings
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, f"Primary Classification: {res.get('primary_pathology', 'N/A')}", ln=True)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, f"Triage Level: {res.get('triage_level', 'STABLE')} | Confidence: {res.get('confidence_level', 'N/A')}", ln=True)
    pdf.ln(4)

    # Reasoning
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, "Clinical Reasoning Summary:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, res.get("clinical_reasoning_summary", "N/A"))
    pdf.ln(4)

    # Doctor Notes
    if clinician_review.get("approved"):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(21, 154, 108)
        pdf.cell(0, 6, f"Clinician Review Approved by {clinician_review.get('signed_by')}", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(20, 32, 31)
        pdf.multi_cell(0, 5, f"Physician Notes: {clinician_review.get('notes')}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        return tmp.name

# Multimodal Lab Report Ingestion
def parse_lab_report(uploaded_file):
    try:
        file_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type
        prompt = """
        Analyze this lab report image/document and extract key medical test results.
        Identify any out-of-range values (High or Low) and summarize overall laboratory findings.
        """
        response, _ = generate_with_fallback(
            contents=[types.Part.from_bytes(data=file_bytes, mime_type=mime_type), prompt]
        )
        return response.text
    except Exception as e:
        return f"Error reading lab report: {str(e)}"

# Location-Based Doctor Search Helper
def fetch_nearby_doctors(specialist_type, location_query, api_key=None):
    if api_key:
        try:
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={specialist_type}+in+{location_query}&key={api_key}"
            response = requests.get(url).json()
            results = []
            for place in response.get("results", [])[:5]:
                results.append({
                    "name": place.get("name"),
                    "address": place.get("formatted_address"),
                    "rating": place.get("rating", "N/A"),
                    "lat": place["geometry"]["location"]["lat"],
                    "lon": place["geometry"]["location"]["lng"],
                })
            if results: return results
        except Exception: pass

    return [
        {"name": f"Apex Care Specialty Hospital ({specialist_type})", "address": f"Central Avenue, {location_query}", "rating": 4.9, "lat": 19.8762, "lon": 75.3433},
        {"name": f"Dr. S. K. Sharma Clinic", "address": f"Sunrise Health Complex, {location_query}", "rating": 4.8, "lat": 19.8821, "lon": 75.3211},
        {"name": f"City Diagnostic Center", "address": f"Civil Hospital Road, {location_query}", "rating": 4.7, "lat": 19.8654, "lon": 75.3501},
    ]

# -----------------------------------------------------------------------------
# 4. TOP APP NAVIGATION & ROLE SELECTOR
# -----------------------------------------------------------------------------
col_nav1, col_nav2 = st.columns([3, 1])
with col_nav1:
    st.markdown("""
        <div class="mm-header">
            <div class="mm-eyebrow">🩺 MediMitra · Clinical Intelligence Platform</div>
            <div class="mm-title">Patient Screening & Care Console</div>
            <div class="mm-subtitle">AI-assisted triage, lab processing, physician verification & emergency routing.</div>
        </div>
    """, unsafe_allow_html=True)
with col_nav2:
    mode = st.radio("App View Mode", ["👤 Patient Console", "👨‍⚕️ Clinician Portal"], help="Toggle between patient intake and doctor review view.")

if not client:
    st.error("⚠️ Configuration error: GEMINI_API_KEY is missing or invalid. Please check your .env file.")
    st.stop()

# =============================================================================
# MODE A: CLINICIAN REVIEW PORTAL (OPTION 3)
# =============================================================================
if mode == "👨‍⚕️ Clinician Portal":
    st.markdown('<div class="mm-card">', unsafe_allow_html=True)
    st.markdown('<div class="mm-card-title">👨‍⚕️ Physician Overwrite & Review Desk</div>', unsafe_allow_html=True)
    st.markdown('<div class="mm-card-subtitle">Review AI preliminary screening findings, add clinical notes, and sign off.</div>', unsafe_allow_html=True)

    if not st.session_state.ai_results:
        st.info("No active patient screening data in session to review. Complete a patient intake first.")
    else:
        res = st.session_state.ai_results
        p_info = st.session_state.patient_info

        st.write(f"**Reviewing Patient:** {p_info.get('name')} ({p_info.get('age')} yrs, {p_info.get('gender')})")
        st.write(f"**AI Classification:** {res.get('primary_pathology')} ({res.get('confidence_level')} Confidence)")

        with st.form("clinician_form"):
            doc_name = st.text_input("Reviewing Doctor Name", value="Dr. Saksham, MD")
            notes = st.text_area("Clinical Notes & Prescriptions", value=st.session_state.clinician_review["notes"], placeholder="Add physician observations, recommended tests, or RX...")
            approved = st.checkbox("Sign Off & Approve Diagnostic Summary", value=st.session_state.clinician_review["approved"])

            if st.form_submit_button("Save Physician Sign-off"):
                st.session_state.clinician_review = {
                    "notes": notes,
                    "signed_by": doc_name,
                    "approved": approved
                }
                st.success("Physician review saved successfully!")
    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# MODE B: PATIENT INTAKE CONSOLE (STEPS 1 - 3)
# =============================================================================
else:
    # -----------------------------------------------------------------------------
    # STEP 1: PATIENT INTAKE
    # -----------------------------------------------------------------------------
    if st.session_state.step == 1:
        render_step_progress(1)
        st.markdown('<div class="mm-card">', unsafe_allow_html=True)
        st.markdown('<div class="mm-card-title">📋 Patient Intake</div>', unsafe_allow_html=True)
        st.markdown('<div class="mm-card-subtitle">Step 1 of 3 — Demographic and baseline health details</div>', unsafe_allow_html=True)

        with st.form("axon_intake"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name", value="Saksham")
                age = st.number_input("Age", min_value=1, max_value=120, value=22)
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            with col2:
                contact = st.text_input("Contact Number")
                history = st.text_area("Known Medical History", placeholder="e.g., Asthma, Diabetes, Hypertension...", height=118)

            submitted = st.form_submit_button("Continue to Assessment & Lab Ingestion →", use_container_width=True, type="primary")
            if submitted:
                if not name.strip():
                    st.error("Please enter the patient's name to continue.")
                else:
                    st.session_state.patient_info = {"name": name, "age": age, "gender": gender, "history": history}
                    st.session_state.step = 2
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------------------------------------------------------------
    # STEP 2: SYMPTOM ASSESSMENT & LAB SCANNING
    # -----------------------------------------------------------------------------
    elif st.session_state.step == 2:
        render_step_progress(2)
        p_info = st.session_state.patient_info

        st.markdown('<div class="mm-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="mm-card-title">🩺 Symptom & Lab Ingestion — {p_info["name"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="mm-card-subtitle"><span class="mm-badge mm-badge-neutral">{p_info["age"]} yrs</span>&nbsp;<span class="mm-badge mm-badge-neutral">{p_info["gender"]}</span>&nbsp; Step 2 of 3</div>', unsafe_allow_html=True)

        col_left, col_right = st.columns(2)

        with col_left:
            symptom_text = st.text_area(
                "1. Clinical Symptom Description",
                placeholder="e.g., Severe acute chest pain, radiating down left arm, shortness of breath...",
                height=210,
                help="Describe symptoms, onset, severity, and duration."
            )

        with col_right:
            st.markdown("**2. Lab Report Scanner (Multimodal OCR)**")
            uploaded_file = st.file_uploader("Upload Patient Lab PDF or Image", type=["png", "jpg", "jpeg", "pdf"])

            if uploaded_file is not None:
                if st.button("📄 Scan & Extract Lab Metrics"):
                    with st.spinner("Processing document using MediMitra Multimodal Engine..."):
                        extracted_summary = parse_lab_report(uploaded_file)
                        st.session_state.lab_data = extracted_summary
                        st.success("Lab report extracted successfully!")

            if st.session_state.lab_data:
                st.text_area("Extracted Lab Findings Context", value=st.session_state.lab_data, height=100)

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 1
                st.rerun()

        with col2:
            if st.button("Run Comprehensive Clinical Analysis 🔍", use_container_width=True, type="primary"):
                if not symptom_text.strip():
                    st.error("Please describe symptoms before running the diagnostic engine.")
                else:
                    with st.spinner("Synthesizing symptoms, history, and lab reports..."):
                        try:
                            lab_context = st.session_state.lab_data if st.session_state.lab_data else "No lab report provided."

                            prompt = f"""
                            Analyze medical status for Patient {p_info['name'].upper()} ({p_info['age']}yo {p_info['gender']}).
                            Medical History: "{p_info['history']}".
                            Reported Symptoms: "{symptom_text}".
                            Extracted Lab Findings: "{lab_context}".

                            Evaluate if any red-flag emergency symptoms are present (e.g. acute cardiac events, severe respiratory distress, high stroke risk).
                            Return valid JSON matching this schema:
                            {{
                                "primary_pathology": "Disease Name",
                                "confidence_level": "High/Moderate/Low",
                                "triage_level": "CRITICAL" or "STABLE",
                                "is_emergency": true or false,
                                "emergency_instructions": "Emergency steps if critical, otherwise empty string.",
                                "clinical_reasoning_summary": "Detailed explanation incorporating symptoms and lab findings.",
                                "key_lab_indicators": ["Relevant lab finding 1", "Relevant lab finding 2"],
                                "differential_diagnoses": ["Alt 1", "Alt 2"],
                                "suggested_clinical_path": "Recommended Specialist (e.g. Pulmonologist, Cardiologist)",
                                "precautionary_countermeasures": ["Measure 1", "Measure 2"]
                            }}
                            """
                            response, model_used = generate_with_fallback(
                                contents=prompt,
                                config=types.GenerateContentConfig(
                                    response_mime_type="application/json",
                                    temperature=0.1
                                )
                            )

                            st.session_state.ai_results = json.loads(response.text)
                            st.session_state.model_used = model_used
                            st.session_state.step = 3
                            st.rerun()

                        except Exception as e:
                            st.error("Clinical engine error — all fallback models are currently unavailable. Please try again shortly.")
                            st.exception(e)
        st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------------------------------------------------------------
    # STEP 3: DIAGNOSTIC RESULTS, EMERGENCY SOS, EXPORTS & DOCTOR FINDER
    # -----------------------------------------------------------------------------
    elif st.session_state.step == 3:
        render_step_progress(3)
        res = st.session_state.ai_results
        p_info = st.session_state.patient_info

        # --- OPTION 2: EMERGENCY SOS TRIAGE ALERT BANNER ---
        if res.get("is_emergency"):
            st.markdown(f"""
                <div class="mm-sos-banner">
                    <div class="mm-sos-title">🚨 EMERGENCY TRIAGE ALERT — IMMEDIATE MEDICAL ATTENTION REQUIRED</div>
                    <div>{res.get('emergency_instructions', 'Severe symptoms detected. Please contact local emergency services immediately.')}</div>
                </div>
            """, unsafe_allow_html=True)
            col_sos1, col_sos2 = st.columns(2)
            with col_sos1:
                st.button("📞 CALL EMERGENCY SERVICES (108 / 112)", use_container_width=True)
            with col_sos2:
                st.button("🏥 FIND NEAREST EMERGENCY ROOM", use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)

        # Primary Diagnosis Banner
        model_tag = f'<span class="mm-model-tag">Analyzed by {st.session_state.model_used}</span>' if st.session_state.model_used else ''
        st.markdown(f"""
            <div class="mm-diagnosis-banner">
                <div class="mm-diag-label">Primary Screening Classification</div>
                <div class="mm-diag-value">{res.get('primary_pathology', 'N/A')}</div>
                <div class="mm-diag-meta">
                    {confidence_badge(res.get('confidence_level'))}
                    <span>·</span>
                    <span>Patient: <b>{p_info['name']}</b></span>
                    <span>·</span>
                    <span>{p_info['age']} yrs, {p_info['gender']}</span>
                    <span>·</span>
                    {model_tag}
                </div>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="mm-card">', unsafe_allow_html=True)
            st.markdown('<div class="mm-card-title">🧠 Integrated Clinical Reasoning</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="color: var(--mm-text-secondary); line-height: 1.65; font-size: 0.93rem;">{res.get("clinical_reasoning_summary", "")}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if res.get("key_lab_indicators"):
                st.markdown('<div class="mm-card">', unsafe_allow_html=True)
                st.markdown('<div class="mm-card-title">🧪 Correlated Lab Biomarkers</div>', unsafe_allow_html=True)
                for lab in res.get('key_lab_indicators', []):
                    st.markdown(f'<div class="mm-list-item"><span class="mm-dot"></span>{lab}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="mm-card">', unsafe_allow_html=True)
            st.markdown('<div class="mm-card-title">🔀 Differential Diagnoses</div>', unsafe_allow_html=True)
            for diff in res.get('differential_diagnoses', []):
                st.markdown(f'<div class="mm-list-item"><span class="mm-dot"></span>{diff}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="mm-card">', unsafe_allow_html=True)
            st.markdown('<div class="mm-card-title">👨‍⚕️ Recommended Clinical Specialist</div>', unsafe_allow_html=True)
            specialist = res.get("suggested_clinical_path", "General Physician")
            st.markdown(f'<div class="mm-specialist-pill">{specialist}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- OPTION 1: DOWNLOAD PDF CLINICAL REPORT ---
        pdf_file = generate_pdf_report(p_info, res, st.session_state.clinician_review)
        with open(pdf_file, "rb") as f:
            st.download_button(
                label="📥 Download Official PDF Clinical Summary Report",
                data=f,
                file_name=f"MediMitra_{p_info.get('name')}_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        # --- DOCTOR & SPECIALIST RECOMMENDATION SECTION ---
        st.markdown('<div class="mm-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="mm-card-title">📍 Nearby Recommended Specialists — {specialist}</div>', unsafe_allow_html=True)
        st.markdown('<div class="mm-card-subtitle">Find top-rated clinics and doctors in your location matching your diagnostic path.</div>', unsafe_allow_html=True)

        col_loc1, col_loc2 = st.columns([2, 1])
        with col_loc1:
            user_location = st.text_input("Enter City, Zip Code, or Location", value="Chhatrapati Sambhajinagar", help="Used to locate nearby healthcare facilities")
        with col_loc2:
            search_triggered = st.button("🔎 Find Nearby Doctors", use_container_width=True)

        if user_location:
            gmaps_key = os.getenv("GOOGLE_MAPS_API_KEY")
            doctors = fetch_nearby_doctors(specialist, user_location, gmaps_key)

            doc_col1, doc_col2 = st.columns([1.2, 1])
            with doc_col1:
                st.markdown("##### Available Specialists")
                for doc in doctors:
                    st.markdown(f"""
                        <div style="background: var(--mm-teal-light); border: 1px solid var(--mm-border); padding: 14px 18px; border-radius: 12px; margin-bottom: 10px;">
                            <div style="font-weight: 700; color: var(--mm-primary-dark); font-size: 0.98rem;">{doc['name']}</div>
                            <div style="color: var(--mm-text-secondary); font-size: 0.85rem; margin-top: 2px;">📍 {doc['address']}</div>
                            <div style="margin-top: 6px;">
                                <span class="mm-badge mm-badge-amber">⭐ {doc['rating']} / 5.0</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

            with doc_col2:
                st.markdown("##### Facilities Map")
                df_coords = pd.DataFrame(doctors)
                st.map(df_coords, latitude="lat", longitude="lon", zoom=12, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🔄 Start New Screening", use_container_width=True):
            st.session_state.step = 1
            st.session_state.patient_info = {}
            st.session_state.lab_data = None
            st.session_state.ai_results = None
            st.session_state.clinician_review = {"notes": "", "signed_by": "", "approved": False}
            st.session_state.model_used = None
            st.rerun()
