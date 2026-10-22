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
        model="gemini-2.5-flash",
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

# Render Generated Content
if st.session_state.study_data:
    data = st.session_state.study_data
    tab_summary, tab_quiz, tab_flashcards = st.tabs(["📝 Summary", "🧪 Quiz (10 MCQs)", "🗂️ Flashcards"])

    # Tab 1: Summary
    with tab_summary:
        st.subheader("Document Summary")
        st.markdown(data.get("summary", "No summary generated."))

    # Tab 2: Quiz
    with tab_quiz:
        st.subheader("10-Question Knowledge Check")
        mcqs = data.get("mcqs", [])
        
        score = 0
        all_answered = True

        for idx, item in enumerate(mcqs):
            st.markdown(f"**Question {idx + 1}:** {item['question']}")
            selected = st.radio(
                f"Select an answer for Q{idx + 1}:",
                options=item["options"],
                index=None,
                key=f"mcq_{idx}",
                label_visibility="collapsed"
            )
            st.session_state.selected_answers[idx] = selected

            if selected is None:
                all_answered = False
            else:
                if selected == item["correct_option"]:
                    st.success(f"✅ Correct! {item.get('explanation', '')}")
                    score += 1
                else:
                    st.error(f"❌ Incorrect. Correct answer: **{item['correct_option']}**\n\n_{item.get('explanation', '')}_")

            st.divider()

        if all_answered and len(mcqs) > 0:
            st.metric(label="Final Score", value=f"{score} / {len(mcqs)}")

    # Tab 3: Flashcards
    with tab_flashcards:
        st.subheader("Key Concept Flashcards")
        cards = data.get("flashcards", [])
        
        cols = st.columns(2)
        for idx, card in enumerate(cards):
            col = cols[idx % 2]
            with col:
                with st.container(border=True):
                    st.markdown(f"### 💡 {card['front']}")
                    is_revealed = idx in st.session_state.revealed_flashcards
                    
                    if is_revealed:
                        st.info(f"**Definition / Answer:**\n\n{card['back']}")
                        if st.button("Hide Answer", key=f"hide_{idx}"):
                            st.session_state.revealed_flashcards.remove(idx)
                            st.rerun()
                    else:
                        if st.button("Reveal Answer", key=f"reveal_{idx}"):
                            st.session_state.revealed_flashcards.add(idx)
                            st.rerun()
