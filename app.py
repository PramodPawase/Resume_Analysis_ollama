import re
from datetime import datetime

import streamlit as st
from groq import Groq          # SDK import only — never shown to the user
import PyPDF2
from fpdf import FPDF          # pip install fpdf2

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Resume Analyzer",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 5rem;
    max-width: 1100px;
}

/* ---------- Header banner ---------- */
.app-header {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    padding: 2.2rem 2rem;
    border-radius: 16px;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 8px 24px rgba(79, 70, 229, 0.25);
}
.app-header h1 {
    font-family: 'Poppins', sans-serif;
    color: #ffffff;
    font-size: 2.3rem;
    font-weight: 700;
    margin-bottom: 0.4rem;
}
.app-header p {
    color: #e6e2ff;
    font-size: 1.05rem;
    margin: 0;
}

/* ---------- Card container ---------- */
.custom-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 1.6rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    margin-bottom: 1.4rem;
}

/* ---------- Buttons ---------- */
.stButton>button, .stDownloadButton>button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.4rem;
    font-weight: 600;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stButton>button:hover, .stDownloadButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(124, 58, 237, 0.35);
    color: white;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: #f8f7ff;
    border-right: 1px solid #e5e7eb;
}

/* ---------- Footer ---------- */
.app-footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background: #ffffff;
    border-top: 1px solid #e5e7eb;
    text-align: center;
    padding: 0.6rem 0;
    font-size: 0.85rem;
    color: #6b7280;
    z-index: 100;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="app-header">
    <h1>📊 Resume Analyzer</h1>
    <p>Upload your resume and get an instant AI-powered ATS score, strengths, gaps &amp; interview prep.</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR — API KEY
# ============================================================
with st.sidebar:
    st.header("🔑 API Key")
    user_api_key = st.text_input(
        "Enter your API key",
        type="password",
        help="Your key is used only for this session and is never stored."
    )
    st.caption("Used only for this session — not stored anywhere.")

# Falls back to a key in Streamlit secrets if you've set one, otherwise uses the sidebar input
api_key = user_api_key or st.secrets.get("API_KEY", "")

PROMPT = """
You are an experienced HR Manager and ATS Resume Expert.
Analyze the following resume carefully.
Provide the output in the following format:
1. ATS Score (Out of 100)
2. Resume Summary
3. Strengths
4. Weaknesses
5. Missing Skills
6. Improvements suggestion
7. Suitable job role
8. Five interview questions with answers
Resume:
{resume}
"""


# ============================================================
# HELPERS
# ============================================================
def extract_text(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text


def analyze_resume(resume_text, api_key):
    client = Groq(api_key=api_key)
    prompt = PROMPT.format(resume=resume_text)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


HEADING_RE = re.compile(r'^\s*\d+\.\s+.+')


class ReportPDF(FPDF):
    """A4 report with a thin border frame plus a running header/footer."""

    def header(self):
        # border frame on every page
        self.set_draw_color(79, 70, 229)
        self.set_line_width(0.6)
        self.rect(6, 6, self.w - 12, self.h - 12)

        if self.page_no() > 1:
            self.set_y(10)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(79, 70, 229)
            self.cell(0, 8, "Resume Analysis Report", align="C")
            self.ln(12)
            self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-16)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(
            0, 10,
            f"Page {self.page_no()}  |  Generated on {datetime.now().strftime('%d %b %Y')}",
            align="C"
        )


def write_rich_line(pdf, text, size=11):
    """Write a line, rendering **bold** markdown segments in bold."""
    pdf.set_font("Helvetica", "", size)
    segments = re.split(r'(\*\*.*?\*\*)', text)
    for seg in segments:
        if not seg:
            continue
        if seg.startswith('**') and seg.endswith('**'):
            pdf.set_font("Helvetica", "B", size)
            pdf.write(6, seg[2:-2])
            pdf.set_font("Helvetica", "", size)
        else:
            pdf.write(6, seg)
    pdf.ln(7)


def generate_pdf(analysis_text: str) -> bytes:
    """Turn the raw AI analysis text into a nicely formatted PDF report."""
    pdf = ReportPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.set_margins(18, 18, 18)
    pdf.add_page()

    # Title block
    pdf.set_fill_color(79, 70, 229)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 16, "Resume Analysis Report", ln=1, align="C", fill=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(
        0, 9,
        f"Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
        ln=1, align="C", fill=True
    )
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    for raw_line in analysis_text.split("\n"):
        line = raw_line.strip()
        if not line:
            pdf.ln(3)
            continue

        clean_line = line.replace("**", "")

        if HEADING_RE.match(clean_line):
            # section heading: rule + bold larger colored text
            pdf.ln(3)
            y = pdf.get_y()
            pdf.set_draw_color(79, 70, 229)
            pdf.set_line_width(0.4)
            pdf.line(18, y, pdf.w - 18, y)
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(55, 48, 163)
            pdf.multi_cell(0, 8, clean_line)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(1)
        elif line.startswith(("-", "*", "•")):
            bullet_text = line.lstrip("-*• ").strip()
            pdf.set_x(24)
            write_rich_line(pdf, f"•  {bullet_text}", size=11)
        else:
            write_rich_line(pdf, clean_line, size=11)

    return bytes(pdf.output())


# ============================================================
# MAIN APP
# ============================================================
if not api_key:
    st.warning("👈 Enter your API key in the sidebar to get started.")
else:
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload resume (PDF)", type="pdf")

    if uploaded_file:
        with st.spinner("Reading resume profile..."):
            resume = extract_text(uploaded_file)
        st.success("Resume uploaded successfully ✅")

        if st.button("Analyze Resume"):
            with st.spinner("Analyzing resume..."):
                try:
                    analysis = analyze_resume(resume, api_key)
                except Exception as e:
                    st.error(f"Something went wrong during analysis: {e}")
                    st.stop()

            st.success("Resume analysis completed 🎯")
            st.markdown("### 📑 Analysis Result")
            st.write(analysis)

            with st.spinner("Preparing your PDF report..."):
                pdf_bytes = generate_pdf(analysis)

            st.download_button(
                label="⬇️ Download Analysis Report (PDF)",
                data=pdf_bytes,
                file_name="resume_analysis_report.pdf",
                mime="application/pdf"
            )
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="app-footer">
    Made with ❤️ using Streamlit &nbsp;•&nbsp; © 2026 Resume Analyzer
</div>
""", unsafe_allow_html=True)
