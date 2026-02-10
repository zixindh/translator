"""Chinese ↔ English Translator — text or voice, always outputs English."""

import io
import streamlit as st
import speech_recognition as sr
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Translator", page_icon="🌐", layout="centered")

# --- CSS ---
st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 720px;}
    .stTextArea textarea {
        border-radius: 12px; font-size: 1.05rem;
        padding: 1rem; min-height: 120px;
    }
    .card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-left: 4px solid #4A90D9;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin: 0.8rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .card .label {
        font-size: 0.7rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.08em;
        color: #4A90D9; margin-bottom: 0.4rem;
    }
    .card .text {
        font-size: 1.15rem; line-height: 1.7;
        color: #1a1a2e; white-space: pre-wrap;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌐 Translator")
st.caption("Speak or type in Chinese or English — always outputs English.")


def card(label: str, text: str):
    """Render a styled transcript card."""
    st.markdown(
        f'<div class="card">'
        f'<div class="label">{label}</div>'
        f'<div class="text">{text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def is_chinese(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def translate_to_english(text: str) -> str:
    """Translate to English only if input is Chinese; otherwise pass through."""
    if is_chinese(text):
        return GoogleTranslator(source="zh-CN", target="en").translate(text)
    return text


# --- Input: two tabs, zero extra buttons ---
tab_text, tab_audio = st.tabs(["✏️ Text", "🎤 Voice"])

with tab_text:
    user_input = st.text_area("Enter Chinese or English", height=140,
                              placeholder="Type or paste here...")
    if user_input and user_input.strip():
        with st.spinner("Translating..."):
            try:
                result = translate_to_english(user_input.strip())
                card("Original", user_input.strip())
                card("English", result)
            except Exception as e:
                st.error(f"Translation failed: {e}")

with tab_audio:
    audio = st.audio_input("Tap to record")
    if audio:
        recognizer = sr.Recognizer()
        audio_bytes = audio.read()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio_data = recognizer.record(source)

        with st.spinner("Transcribing & translating..."):
            try:
                # Try Chinese first, fall back to English
                try:
                    spoken = recognizer.recognize_google(audio_data, language="zh-CN")
                except sr.UnknownValueError:
                    spoken = recognizer.recognize_google(audio_data, language="en-US")

                result = translate_to_english(spoken)
                card("You said", spoken)
                card("English", result)
            except sr.UnknownValueError:
                st.error("Couldn't understand the audio. Try again.")
            except sr.RequestError as e:
                st.error(f"Speech service error: {e}")
