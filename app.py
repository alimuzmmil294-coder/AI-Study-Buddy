import json
import os
import streamlit as st
from pypdf import PdfReader
from google import genai
from google.genai import types

# Page Configuration
st.set_page_config(
    page_title="AI Study Companion",
    page_icon="📚",
    layout="wide"
)

# Initialize Session State
if "study_data" not in st.session_state:
    st.session_state.study_data = None
if "selected_answers" not in st.session_state:
    st.session_state.selected_answers = {}
if "revealed_flashcards" not in st.session_state:
    st.session_state.revealed_flashcards = set()

# Helper: Extract text from PDF
def extract_text_from_pdf(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    extracted_text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            extracted_text.append(page_text)
    return "\n".join(extracted_text)

# Helper: Generate Study Material via Gemini Flash
def generate_study_material(client: genai.Client, text_content: str) -> dict:
    prompt = f"""
You are an expert academic tutor. Analyze the following study notes/chapter text thoroughly:

{text_content}

Generate:
1. A structured, clear summary containing key takeaways and major themes.
2. Exactly 10 multiple-choice questions (MCQs) testing conceptual understanding. Each MCQ must include:
   - question: The question text
   - options: A list of exactly 4 choices (e.g., ["A) ...", "B) ...", "C) ...", "D) ..."])
   - correct_option: The exact option matching one from the list (e.g., "A) ...")
   - explanation: A concise explanation of why that answer is correct.
3. A set of 8-12 high-yield flashcards with front (term/concept) and back (definition/insight).
"""

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "summary": {"type": "STRING"},
            "mcqs": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "question": {"type": "STRING"},
                        "options": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        },
                        "correct_option": {"type": "STRING"},
                        "explanation": {"type": "STRING"}
                    },
                    "required": ["question", "options", "correct_option", "explanation"]
                }
            },
            "flashcards": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "front": {"type": "STRING"},
                        "back": {"type": "STRING"}
                    },
                    "required": ["front", "back"]
                }
            }
        },
        "required": ["summary", "mcqs", "flashcards"]
    }

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=response_schema,
        temperature=0.3
    )

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=config
    )

    return json.loads(response.text)

# Sidebar: API Key Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_input = st.text_input(
        "Gemini API Key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", "") or st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else "",
        help="Get your key at https://aistudio.google.com/"
    )
    st.caption("Enter your key above or store it as an environment variable `GEMINI_API_KEY`.")

# Main Layout
st.title("📚 AI Study Companion")
st.write("Upload a chapter or lecture notes in PDF format to generate comprehensive summaries, practice quizzes, and revision flashcards.")

uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file is not None:
    if st.button("🚀 Analyze & Generate Study Pack", type="primary", use_container_width=True):
        if not api_key_input:
            st.error("Please provide a valid Gemini API Key in the sidebar.")
        else:
            with st.spinner("Reading PDF and extracting content..."):
                pdf_text = extract_text_from_pdf(uploaded_file)

            if not pdf_text.strip():
                st.error("No readable text found. If this is a scanned PDF, please run OCR first.")
            else:
                with st.spinner("Gemini Flash is generating your summary, quiz, and flashcards..."):
                    try:
                        client = genai.Client(api_key=api_key_input)
                        result = generate_study_material(client, pdf_text)
                        st.session_state.study_data = result
                        st.session_state.selected_answers = {}
                        st.session_state.revealed_flashcards = set()
                        st.success("Study materials generated successfully!")
                    except Exception as e:
                        st.error(f"Error during generation: {e}")

#
