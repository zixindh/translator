"""Streamlit Translator App — fast, clean multilingual translation."""

import streamlit as st
from deep_translator import GoogleTranslator

# --- Supported languages (display_name -> code) ---
LANGUAGES = GoogleTranslator().get_supported_languages(as_dict=True)

# --- Page config ---
st.set_page_config(page_title="Translator", page_icon="🌐", layout="centered")

# --- Custom CSS for modern look ---
st.markdown("""
<style>
    /* Hide default Streamlit clutter */
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 720px;}

    /* Card-style text areas */
    .stTextArea textarea {
        border-radius: 12px;
        font-size: 1.05rem;
        padding: 1rem;
        min-height: 160px;
    }

    /* Primary button styling */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.5rem 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌐 Translator")

# --- Language selectors ---
lang_names = list(LANGUAGES.keys())

col1, col_swap, col2 = st.columns([5, 1, 5])

with col1:
    src_lang = st.selectbox("From", ["auto (detect)"] + lang_names, index=0)
with col_swap:
    st.markdown("<br>", unsafe_allow_html=True)
    swap = st.button("⇄", help="Swap languages", use_container_width=True)
with col2:
    tgt_lang = st.selectbox("To", lang_names, index=lang_names.index("chinese (simplified)") if "chinese (simplified)" in lang_names else 0)

# Handle swap
if swap and src_lang != "auto (detect)":
    src_lang, tgt_lang = tgt_lang, src_lang

# --- Input / output ---
input_text = st.text_area("Enter text", height=180, placeholder="Type or paste text here...")

if st.button("Translate", type="primary", use_container_width=True):
    if input_text.strip():
        src_code = "auto" if src_lang == "auto (detect)" else LANGUAGES[src_lang]
        tgt_code = LANGUAGES[tgt_lang]

        with st.spinner("Translating..."):
            try:
                result = GoogleTranslator(source=src_code, target=tgt_code).translate(input_text)
                st.text_area("Translation", value=result, height=180, disabled=True)
            except Exception as e:
                st.error(f"Translation failed: {e}")
    else:
        st.warning("Please enter some text to translate.")
