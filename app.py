"""Streamlit Translator App — text & audio input, clean multilingual translation."""

import io
import streamlit as st
import speech_recognition as sr
from deep_translator import GoogleTranslator

# --- Supported languages (display_name -> code) ---
LANGUAGES = GoogleTranslator().get_supported_languages(as_dict=True)

# --- Page config ---
st.set_page_config(page_title="Translator", page_icon="🌐", layout="centered")

# --- Custom CSS ---
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 760px;}
    .stTextArea textarea {
        border-radius: 12px; font-size: 1.05rem;
        padding: 1rem; min-height: 140px;
    }
    .stButton > button {
        border-radius: 10px; font-weight: 600; padding: 0.5rem 2rem;
    }
    /* Transcript card */
    .transcript-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-left: 4px solid #4A90D9;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin: 1rem 0;
        font-size: 1.1rem;
        line-height: 1.8;
        color: #1a1a2e;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .transcript-card .label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #4A90D9;
        margin-bottom: 0.5rem;
    }
    .transcript-card .text {
        font-size: 1.15rem;
        white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌐 Translator")

# --- Language selectors (default target: english) ---
lang_names = list(LANGUAGES.keys())
default_tgt = lang_names.index("english") if "english" in lang_names else 0

col1, col_swap, col2 = st.columns([5, 1, 5])
with col1:
    src_lang = st.selectbox("From", ["auto (detect)"] + lang_names, index=0)
with col_swap:
    st.markdown("<br>", unsafe_allow_html=True)
    swap = st.button("⇄", help="Swap languages", use_container_width=True)
with col2:
    tgt_lang = st.selectbox("To", lang_names, index=default_tgt)

if swap and src_lang != "auto (detect)":
    src_lang, tgt_lang = tgt_lang, src_lang

# --- Input tabs: Text / Audio ---
tab_text, tab_audio = st.tabs(["✏️ Text", "🎤 Audio"])

input_text = ""

with tab_text:
    input_text = st.text_area("Enter text", height=160, placeholder="Type or paste text here...")

with tab_audio:
    audio = st.audio_input("Record or upload audio")
    if audio:
        # Transcribe audio using Google free speech recognition
        recognizer = sr.Recognizer()
        audio_bytes = audio.read()
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        with st.spinner("Transcribing audio..."):
            try:
                input_text = recognizer.recognize_google(audio_data)
                st.success("Transcription complete")
                st.markdown(f"**Detected speech:** {input_text}")
            except sr.UnknownValueError:
                st.error("Could not understand the audio. Please try again.")
            except sr.RequestError as e:
                st.error(f"Speech recognition service error: {e}")


def render_transcript(label: str, text: str):
    """Display translated text in a styled card."""
    st.markdown(
        f'<div class="transcript-card">'
        f'<div class="label">{label}</div>'
        f'<div class="text">{text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# --- Translate ---
if st.button("Translate", type="primary", use_container_width=True):
    if input_text and input_text.strip():
        src_code = "auto" if src_lang == "auto (detect)" else LANGUAGES[src_lang]
        tgt_code = LANGUAGES[tgt_lang]
        with st.spinner("Translating..."):
            try:
                result = GoogleTranslator(source=src_code, target=tgt_code).translate(input_text)
                # Show original
                render_transcript("Original", input_text)
                # Show translation in styled card
                render_transcript(f"Translation — {tgt_lang.title()}", result)
            except Exception as e:
                st.error(f"Translation failed: {e}")
    else:
        st.warning("Enter text or record audio first.")
