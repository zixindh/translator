# Translator

Live Chinese → English voice translator with AI summarization.

**Live:** [zixin-translator.streamlit.app](https://zixin-translator.streamlit.app)

## Features

- Tap mic, speak Chinese or English — see English in real time
- AI summary of all notes (Gemini 2.5 Flash)
- Export as image (long-press to save on iPhone)

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

Add `GEMINI_API_KEY` to `.streamlit/secrets.toml` or Streamlit Cloud secrets.
