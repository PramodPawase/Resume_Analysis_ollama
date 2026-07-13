import streamlit as st
from groq import Groq
import PyPDF2

st.set_page_config(
    page_title="RESUME ANALYZER",
    page_icon="📊",
    layout="wide"
)

# --- Sidebar: user supplies their own Groq API key ---
with st.sidebar:
    st.header("🔑 Groq API Key")
    user_api_key = st.text_input(
        "Enter your Groq API key",
        type="password",
        help="Get a free key at https://console.groq.com/keys"
    )
    st.caption("Used only for this session — not stored anywhere.")

# Falls back to a key in Streamlit secrets if you've set one, otherwise uses the sidebar input
api_key = user_api_key or st.secrets.get("GROQ_API_KEY", "")

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
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

st.title("📊 RESUME ANALYZER")
st.write("Upload your resume in PDF format, analyze its content and get insights from the data.")

if not api_key:
    st.warning("👈 Enter your Groq API key in the sidebar to get started.")
else:
    uploaded_file = st.file_uploader("Upload resume", type="pdf")

    if uploaded_file:
        with st.spinner("Reading resume profile..."):
            resume = extract_text(uploaded_file)
        st.success("Resume uploaded successfully ✅")

        if st.button("Analyze Resume"):
            with st.spinner("Analyzing resume..."):
                try:
                    analysis = analyze_resume(resume, api_key)
                except Exception as e:
                    st.error(f"Something went wrong calling Groq: {e}")
                    st.stop()
            st.success("Resume analysis completed 🎯")
            st.markdown("### 📑 Analysis Result:")
            st.write(analysis)
            st.download_button(
                label="⬇️ Download Analysis Result",
                data=analysis,
                file_name="analysis_result.txt",
                mime="text/plain"
            )
