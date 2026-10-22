# AI-Study-Buddy# 📚 AI Study Companion

An interactive web application built with Streamlit and Google Gemini Flash that transforms lecture slides, textbook chapters, or handwritten scanned notes into complete study sets: high-yield summaries, 10 multiple-choice quiz questions, and interactive flashcards.

## Features
- **PDF Ingestion:** Fast on-device text extraction via `pypdf`.
- **Structured LLM Output:** Powered by `gemini-2.5-flash` using native JSON schemas to guarantee 10 valid MCQs and clean flashcard pairs.
- **Interactive Quiz:** Instant answer evaluation, option-level explanations, and live scoring.
- **Toggleable Flashcards:** Quick concept revision with stateful reveal buttons.

## Local Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/study-assistant.git](https://github.com/your-username/study-assistant.git)
   cd study-assistant
