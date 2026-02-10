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

  /* Layout: header top, log middle, mic bottom */
  .wrap { display:flex; flex-direction:column; height:92vh; }

  /* Header with title left, export icon right */
  .bar {
    display:flex; align-items:center; justify-content:space-between;
    padding:0 0.2rem 0.6rem; flex-shrink:0;
  }
  .bar h3 { font-size:1.15rem; color:#1a1a2e; display:flex; align-items:center; gap:0.4rem; }
  #exportBtn {
    display:none; background:none; border:none; cursor:pointer;
    color:#999; transition:color 0.2s; padding:4px;
  }
  #exportBtn:hover { color:#4A90D9; }
  #exportBtn svg { width:20px; height:20px; }

  /* Scrollable log area */
  #log { flex:1; overflow-y:auto; padding:0 0.2rem 0.5rem; }

  /* Finalized entries */
  .line {
    background:#f7f8fa; border-left:3px solid #4A90D9;
    border-radius:0; padding:0.5rem 0.9rem; margin:0;
    font-size:1.05rem; line-height:1.6; color:#1a1a2e;
    animation: fadeIn 0.25s ease;
  }
  @keyframes fadeIn {
    from { opacity:0; transform:translateY(3px); }
    to   { opacity:1; transform:translateY(0); }
  }

  /* Live interim text */
  #live {
    color:#999; font-style:italic; font-size:0.95rem;
    padding:0 0.2rem; min-height:1rem; flex-shrink:0;
  }

  /* Bottom mic area */
  .bottom { flex-shrink:0; text-align:center; padding:0.6rem 0 0.3rem; }
  #mic {
    width:52px; height:52px; border-radius:50%; border:none;
    background:#eee; cursor:pointer; transition:all 0.2s;
    display:inline-flex; align-items:center; justify-content:center;
  }
  #mic svg { width:22px; height:22px; fill:#666; }
  #mic.on {
    background:#ef4444;
    box-shadow: 0 0 0 4px rgba(239,68,68,0.2);
    animation: pulse 1.5s infinite;
  }
  #mic.on svg { fill:#fff; }
  @keyframes pulse {
    0%,100% { box-shadow:0 0 0 4px rgba(239,68,68,0.2); }
    50%     { box-shadow:0 0 0 10px rgba(239,68,68,0.05); }
  }
  #status { font-size:0.65rem; color:#aaa; margin-top:0.3rem; letter-spacing:0.03em; }

  /* Export card (offscreen for image render) */
  .export-card {
    width:560px; padding:2rem 2.5rem; background:#fff;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }
  .export-card .ex-title {
    font-size:1.1rem; font-weight:700; color:#1a1a2e;
    margin-bottom:1rem; display:flex; align-items:center; gap:0.4rem;
  }
  .export-card .ex-line {
    background:#f7f8fa; border-left:3px solid #4A90D9;
    border-radius:0; padding:0.45rem 0.9rem; margin:0;
    font-size:0.95rem; line-height:1.5; color:#1a1a2e;
  }
  .export-card .ex-footer {
    margin-top:1rem; text-align:right;
    font-size:0.7rem; color:#aaa;
  }
</style>

<div class="wrap">
  <!-- Top bar: title + export -->
  <div class="bar">
    <h3><span>🌐</span> Translator</h3>
    <button id="exportBtn" onclick="exportCard()" title="Export as image">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
    </button>
  </div>

  <!-- Scrollable transcript log -->
  <div id="log"></div>
  <div id="live"></div>

  <!-- Bottom mic -->
  <div class="bottom">
    <button id="mic" onclick="toggle()">
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 14a3 3 0 003-3V5a3 3 0 00-6 0v6a3 3 0 003 3z"/>
        <path d="M19 11a7 7 0 01-14 0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        <line x1="12" y1="18" x2="12" y2="22" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>
    <div id="status">Tap to start</div>
  </div>
</div>

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

/* Export as image — uses Web Share API on iPhone (saves to Photos), file download on desktop */
async function exportCard() {
  const card = document.createElement('div');
  card.className = 'export-card';
  card.innerHTML =
    '<div class="ex-title"><span>🌐</span> Translator</div>' +
    lines.map(l => '<div class="ex-line">' + l + '</div>').join('') +
    '<div class="ex-footer">' + new Date().toLocaleString() + '</div>';
  document.body.appendChild(card);

  /* Load html2canvas if not already loaded */
  if (!window.html2canvas) {
    await new Promise(resolve => {
      const s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
      s.onload = resolve;
      document.body.appendChild(s);
    });
  }

  const canvas = await html2canvas(card, { scale: 2, backgroundColor: '#fff' });
  document.body.removeChild(card);

  /* Convert canvas to blob */
  const blob = await new Promise(r => canvas.toBlob(r, 'image/png'));
  const file = new File([blob], 'translator.png', { type: 'image/png' });

  /* iPhone/mobile: Web Share API opens share sheet → Save Image */
  if (navigator.canShare && navigator.canShare({ files: [file] })) {
    try { await navigator.share({ files: [file] }); return; } catch {}
  }

  /* Desktop fallback: direct download */
  const a = document.createElement('a');
  a.download = 'translator-' + Date.now() + '.png';
  a.href = URL.createObjectURL(blob);
  a.click();
  URL.revokeObjectURL(a.href);
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
