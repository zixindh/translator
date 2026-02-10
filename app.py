"""Live Chinese → English meeting notes. Streaming transcription via Web Speech API."""

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Translator", page_icon="🌐", layout="centered")

st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 1rem; max-width: 620px;}
</style>
""", unsafe_allow_html=True)

# Entire UI lives in a single client-side HTML component.
# Speech recognition + translation happen in the browser — zero server round-trips.
components.html("""
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }

  .header { display:flex; align-items:center; gap:0.5rem; margin-bottom:1rem; }
  .header h3 { font-size:1.2rem; color:#1a1a2e; }

  #mic {
    width:48px; height:48px; border-radius:50%; border:none;
    background:#eee; color:#666; font-size:1.3rem;
    cursor:pointer; transition:all 0.2s; display:block; margin:0 auto 0.6rem;
  }
  #mic.on {
    background:#ef4444; color:#fff;
    box-shadow: 0 0 0 4px rgba(239,68,68,0.2);
    animation: pulse 1.5s infinite;
  }
  @keyframes pulse {
    0%,100% { box-shadow:0 0 0 4px rgba(239,68,68,0.2); }
    50%     { box-shadow:0 0 0 10px rgba(239,68,68,0.05); }
  }

  #status {
    text-align:center; font-size:0.7rem; color:#aaa;
    margin-bottom:0.8rem; letter-spacing:0.03em;
  }

  /* Live interim text */
  #live {
    color:#999; font-style:italic; font-size:0.95rem;
    padding:0 0.2rem; min-height:1.2rem; margin-bottom:0.4rem;
  }

  /* Finalized entries */
  .line {
    background:#f7f8fa; border-left:3px solid #4A90D9;
    border-radius:6px; padding:0.7rem 1rem; margin:0.35rem 0;
    font-size:1.05rem; line-height:1.6; color:#1a1a2e;
    animation: fadeIn 0.25s ease;
  }
  @keyframes fadeIn {
    from { opacity:0; transform:translateY(3px); }
    to   { opacity:1; transform:translateY(0); }
  }

  #log { max-height:65vh; overflow-y:auto; padding-bottom:0.5rem; }

  /* Export button */
  #exportBtn {
    display:none; margin:0.5rem auto 0; padding:0.4rem 1.2rem;
    background:#4A90D9; color:#fff; border:none; border-radius:6px;
    font-size:0.8rem; font-weight:600; cursor:pointer;
    transition:background 0.2s;
  }
  #exportBtn:hover { background:#3a7bc8; }

  /* Export card rendered offscreen for download */
  .export-card {
    width:560px; padding:2rem 2.5rem; background:#fff;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }
  .export-card .ex-title {
    font-size:1.1rem; font-weight:700; color:#1a1a2e;
    margin-bottom:1.2rem; display:flex; align-items:center; gap:0.4rem;
  }
  .export-card .ex-line {
    background:#f7f8fa; border-left:3px solid #4A90D9;
    border-radius:5px; padding:0.55rem 0.9rem; margin:0.3rem 0;
    font-size:0.95rem; line-height:1.5; color:#1a1a2e;
  }
  .export-card .ex-footer {
    margin-top:1.2rem; text-align:right;
    font-size:0.7rem; color:#aaa; letter-spacing:0.02em;
  }
</style>

<div class="header"><span style="font-size:1.3rem">🌐</span><h3>Translator</h3></div>
<button id="mic" onclick="toggle()">🎤</button>
<div id="status">Tap to start</div>
<div id="live"></div>
<div id="log"></div>
<button id="exportBtn" onclick="exportCard()">Export</button>

<script>
const mic    = document.getElementById('mic');
const status = document.getElementById('status');
const live   = document.getElementById('live');
const log    = document.getElementById('log');
let on = false, rec;

/* Detect Chinese characters */
const hasCN = t => /[\u4e00-\u9fff]/.test(t);

/* Translate Chinese → English via Google free endpoint, MyMemory fallback */
async function toEN(text) {
  if (!hasCN(text)) return text;
  try {
    const r = await fetch(
      `https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=en&dt=t&q=${encodeURIComponent(text)}`
    );
    const d = await r.json();
    return d[0].map(s => s[0]).join('');
  } catch {
    try {
      const r = await fetch(
        `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=zh-CN|en`
      );
      const d = await r.json();
      return d.responseData.translatedText || text;
    } catch { return text; }
  }
}

const exportBtn = document.getElementById('exportBtn');
const lines = [];  /* store all finalized texts */

/* Append a finalized English line */
function addLine(text) {
  lines.push(text);
  const el = document.createElement('div');
  el.className = 'line';
  el.textContent = text;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  exportBtn.style.display = 'block';
}

/* Export as image card */
async function exportCard() {
  /* Build offscreen card */
  const card = document.createElement('div');
  card.className = 'export-card';
  card.innerHTML =
    '<div class="ex-title"><span>🌐</span> Translator</div>' +
    lines.map(l => '<div class="ex-line">' + l + '</div>').join('') +
    '<div class="ex-footer">' + new Date().toLocaleString() + '</div>';
  document.body.appendChild(card);

  /* Render to canvas via html2canvas */
  const script = document.createElement('script');
  script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
  script.onload = async () => {
    const canvas = await html2canvas(card, { scale: 2, backgroundColor: '#ffffff' });
    document.body.removeChild(card);
    const a = document.createElement('a');
    a.download = 'translator-' + Date.now() + '.png';
    a.href = canvas.toDataURL('image/png');
    a.click();
  };
  document.body.appendChild(script);
}

/* Build speech recognition instance */
function makeSR() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { status.textContent = 'Not supported in this browser'; return null; }
  const r = new SR();
  r.continuous = true;
  r.interimResults = true;
  r.lang = 'zh-CN';   /* recognises Chinese; passes through English fine */

  r.onresult = async e => {
    let interim = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const t = e.results[i][0].transcript;
      if (e.results[i].isFinal) {
        live.textContent = '';
        const en = await toEN(t.trim());
        if (en) addLine(en);
      } else {
        interim += t;
      }
    }
    if (interim) live.textContent = interim;
  };

  /* Auto-restart on pause so it keeps listening */
  r.onend = () => { if (on) try { r.start(); } catch {} };
  r.onerror = e => {
    if (e.error === 'no-speech' || e.error === 'aborted') return;
    status.textContent = 'Error: ' + e.error;
  };
  return r;
}

function toggle() {
  if (on) {
    on = false; rec?.stop();
    mic.classList.remove('on');
    status.textContent = 'Tap to start';
    live.textContent = '';
  } else {
    rec = makeSR();
    if (!rec) return;
    on = true; rec.start();
    mic.classList.add('on');
    status.textContent = 'Listening…';
  }
}
</script>
""", height=700)
