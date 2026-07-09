import streamlit as st
import ollama
import PyPDF2

# Prompt template
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

# Function to extract text from PDF
def extract_text(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

# Function to analyze resume using Ollama
def analyze_resume(resume_text):
    prompt = PROMPT.format(resume=resume_text)
    response = ollama.chat(
        model="gemma3:270m",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response["message"]["content"]

# Streamlit UI
st.set_page_config(
    page_title="PRAMOD PAWASE RESUME ANALYZER",
    page_icon="📊",
    layout="wide"
)

st.title("📊 PRAMOD PAWASE RESUME ANALYZER")
st.write("Upload your resume in PDF format, analyze its content and get insights from the data.")

uploaded_file = st.file_uploader("Upload resume", type="pdf")

if uploaded_file:
    with st.spinner("Reading resume profile..."):
        resume = extract_text(uploaded_file)
    st.success("Resume uploaded successfully ✅")

    if st.button("Analyze Resume"):
        with st.spinner("Analyzing resume..."):
            analysis = analyze_resume(resume)
        st.success("Resume analysis completed 🎯")

        st.markdown("### 📑 Analysis Result:")
        st.write(analysis)

        st.download_button(
            label="⬇️ Download Analysis Result",
            data=analysis,
            file_name="analysis_result.txt",
            mime="text/plain"
        )
