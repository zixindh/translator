"""Minimal Chinese → English translator. Voice or text, English output only."""

import io
import streamlit as st
import speech_recognition as sr
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Translator", page_icon="🌐", layout="centered")

st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 1.5rem; max-width: 600px;}
    h3 {font-size: 1.3rem !important; margin-bottom: 0.2rem !important;}
    .output {
        background: #f8f9fa;
        border-left: 3px solid #4A90D9;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        font-size: 1.1rem;
        line-height: 1.7;
        color: #1a1a2e;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("### 🌐 Translator")

# --- State for conversation history ---
if "history" not in st.session_state:
    st.session_state.history = []


def is_chinese(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def to_english(text: str) -> str:
    """Translate Chinese to English; pass through if already English."""
    if is_chinese(text):
        return GoogleTranslator(source="zh-CN", target="en").translate(text)
    return text


def show_history():
    """Render all past translations."""
    for entry in st.session_state.history:
        st.markdown(f'<div class="output">{entry}</div>', unsafe_allow_html=True)


# --- Voice input (always visible, not a tab) ---
audio = st.audio_input("🎤 Tap to speak", label_visibility="collapsed")
if audio:
    recognizer = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(audio.read())) as src:
        data = recognizer.record(src)
    try:
        # Try Chinese first, fall back to English
        try:
            spoken = recognizer.recognize_google(data, language="zh-CN")
        except sr.UnknownValueError:
            spoken = recognizer.recognize_google(data, language="en-US")
        result = to_english(spoken)
        st.session_state.history.append(result)
    except sr.UnknownValueError:
        st.error("Couldn't catch that. Try again.")
    except sr.RequestError as e:
        st.error(f"Service error: {e}")

# --- Text input ---
text = st.chat_input("Type Chinese or English...")
if text:
    result = to_english(text.strip())
    st.session_state.history.append(result)

# --- Display all results ---
show_history()
