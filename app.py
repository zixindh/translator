"""Live Chinese → English meeting notes. Streaming transcription via Web Speech API.
   Summarization via OpenRouter free model (client-side)."""

import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Translator", page_icon="🌐", layout="centered")

st.markdown("""
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 1rem; max-width: 620px;}
</style>
""", unsafe_allow_html=True)

# Pass API key from secrets into the JS component
API_KEY = st.secrets.get("OPENROUTER_API_KEY", os.environ.get("OPENROUTER_API_KEY", ""))

components.html(f"""
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}

  .wrap {{ display:flex; flex-direction:column; height:640px; }}

  .bar {{
    display:flex; align-items:center; justify-content:space-between;
    padding:0 0.2rem 0.6rem; flex-shrink:0;
  }}
  .bar h3 {{ font-size:1.15rem; color:#1a1a2e; display:flex; align-items:center; gap:0.4rem; }}
  .actions {{ display:flex; gap:0.3rem; }}
  .actions button {{
    display:none; background:none; border:none; cursor:pointer;
    color:#999; transition:color 0.2s; padding:4px;
  }}
  .actions button:hover {{ color:#4A90D9; }}
  .actions button svg {{ width:20px; height:20px; }}

  #log {{ flex:1; overflow-y:auto; padding:0 0.2rem 0.5rem; }}

  .line {{
    background:#f7f8fa; border-left:3px solid #4A90D9;
    border-radius:0; padding:0.5rem 0.9rem; margin:0;
    font-size:1.05rem; line-height:1.6; color:#1a1a2e;
    animation: fadeIn 0.25s ease;
  }}
  @keyframes fadeIn {{
    from {{ opacity:0; transform:translateY(3px); }}
    to   {{ opacity:1; transform:translateY(0); }}
  }}

  .summary {{
    background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
    border-left:3px solid #6366f1;
    padding:0.7rem 1rem; margin:0.5rem 0 0.3rem;
    font-size:0.95rem; line-height:1.6; color:#1e1b4b;
    border-radius:6px;
  }}
  .summary .s-label {{
    font-size:0.65rem; font-weight:700; text-transform:uppercase;
    letter-spacing:0.06em; color:#6366f1; margin-bottom:0.3rem;
  }}

  #live {{
    color:#999; font-style:italic; font-size:0.95rem;
    padding:0 0.2rem; min-height:1rem; flex-shrink:0;
  }}

  .bottom {{ flex-shrink:0; text-align:center; padding:0.6rem 0 2.5rem; }}
  #mic {{
    width:52px; height:52px; border-radius:50%; border:none;
    background:#eee; cursor:pointer; transition:all 0.2s;
    display:inline-flex; align-items:center; justify-content:center;
  }}
  #mic svg {{ width:22px; height:22px; fill:#666; }}
  #mic.on {{
    background:#ef4444;
    box-shadow: 0 0 0 4px rgba(239,68,68,0.2);
    animation: pulse 1.5s infinite;
  }}
  #mic.on svg {{ fill:#fff; }}
  @keyframes pulse {{
    0%,100% {{ box-shadow:0 0 0 4px rgba(239,68,68,0.2); }}
    50%     {{ box-shadow:0 0 0 10px rgba(239,68,68,0.05); }}
  }}
  #status {{ font-size:0.65rem; color:#aaa; margin-top:0.3rem; letter-spacing:0.03em; }}

  .export-card {{
    width:560px; padding:2rem 2.5rem; background:#fff;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }}
  .export-card .ex-title {{
    font-size:1.1rem; font-weight:700; color:#1a1a2e;
    margin-bottom:1rem; display:flex; align-items:center; gap:0.4rem;
  }}
  .export-card .ex-line {{
    background:#f7f8fa; border-left:3px solid #4A90D9;
    border-radius:0; padding:0.45rem 0.9rem; margin:0;
    font-size:0.95rem; line-height:1.5; color:#1a1a2e;
  }}
  .export-card .ex-summary {{
    background:#eef2ff; border-left:3px solid #6366f1;
    border-radius:4px; padding:0.6rem 0.9rem; margin:0.6rem 0 0;
    font-size:0.9rem; line-height:1.5; color:#1e1b4b;
  }}
  .export-card .ex-footer {{
    margin-top:1rem; text-align:right; font-size:0.7rem; color:#aaa;
  }}
</style>

<div class="wrap">
  <div class="bar">
    <h3><span>🌐</span> Translator</h3>
    <div class="actions">
      <button id="sumBtn" onclick="doSummarize()" title="Summarize">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8z"/>
        </svg>
      </button>
      <button id="exportBtn" onclick="exportCard()" title="Export as image">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
      </button>
    </div>
  </div>

  <div id="log"></div>
  <div id="live"></div>

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
const API_KEY = "{API_KEY}";
const mic    = document.getElementById('mic');
const status = document.getElementById('status');
const live   = document.getElementById('live');
const log    = document.getElementById('log');
const exportBtn = document.getElementById('exportBtn');
const sumBtn = document.getElementById('sumBtn');
let on = false, rec;
const lines = [];
let summaryText = '';

const hasCN = t => /[\u4e00-\u9fff]/.test(t);

async function toEN(text) {{
  if (!hasCN(text)) return text;
  try {{
    const r = await fetch(
      `https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=en&dt=t&q=${{encodeURIComponent(text)}}`
    );
    const d = await r.json();
    return d[0].map(s => s[0]).join('');
  }} catch {{
    try {{
      const r = await fetch(
        `https://api.mymemory.translated.net/get?q=${{encodeURIComponent(text)}}&langpair=zh-CN|en`
      );
      const d = await r.json();
      return d.responseData.translatedText || text;
    }} catch {{ return text; }}
  }}
}}

function showBtns() {{
  exportBtn.style.display = 'block';
  sumBtn.style.display = 'block';
}}

function addLine(text) {{
  lines.push(text);
  const el = document.createElement('div');
  el.className = 'line';
  el.textContent = text;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  showBtns();
}}

function showSummary(text) {{
  const old = log.querySelector('.summary');
  if (old) old.remove();
  const el = document.createElement('div');
  el.className = 'summary';
  el.innerHTML = '<div class="s-label">Summary</div>' + text;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
}}

/* Summarize directly via OpenRouter API from client */
async function doSummarize() {{
  if (!lines.length) return;
  sumBtn.style.opacity = '0.4';
  sumBtn.style.pointerEvents = 'none';
  status.textContent = 'Summarizing…';

  const models = ["google/gemma-3-27b-it:free", "google/gemma-3n-e4b-it:free"];
  const body = {{
    messages: [
      {{ role: "system", content: "Summarize the following meeting notes concisely. Keep full context and key points. Be brief and clear. Output only the summary, no preamble." }},
      {{ role: "user", content: lines.join('\\n') }}
    ],
    max_tokens: 512
  }};

  for (const model of models) {{
    try {{
      const r = await fetch("https://openrouter.ai/api/v1/chat/completions", {{
        method: "POST",
        headers: {{ "Authorization": "Bearer " + API_KEY, "Content-Type": "application/json" }},
        body: JSON.stringify({{ ...body, model }})
      }});
      const d = await r.json();
      if (d.choices && d.choices[0]) {{
        summaryText = d.choices[0].message.content.trim();
        showSummary(summaryText);
        sumBtn.style.opacity = '1';
        sumBtn.style.pointerEvents = 'auto';
        status.textContent = on ? 'Listening…' : 'Tap to start';
        return;
      }}
    }} catch(e) {{ continue; }}
  }}

  showSummary('Could not generate summary.');
  sumBtn.style.opacity = '1';
  sumBtn.style.pointerEvents = 'auto';
  status.textContent = on ? 'Listening…' : 'Tap to start';
}}

/* Export */
async function exportCard() {{
  const card = document.createElement('div');
  card.className = 'export-card';
  let inner = '<div class="ex-title"><span>🌐</span> Translator</div>' +
    lines.map(l => '<div class="ex-line">' + l + '</div>').join('');
  if (summaryText) inner += '<div class="ex-summary"><b>Summary:</b> ' + summaryText + '</div>';
  inner += '<div class="ex-footer">' + new Date().toLocaleString() + '</div>';
  card.innerHTML = inner;
  document.body.appendChild(card);

  if (!window.html2canvas) {{
    await new Promise(resolve => {{
      const s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
      s.onload = resolve;
      document.body.appendChild(s);
    }});
  }}

  const canvas = await html2canvas(card, {{ scale: 2, backgroundColor: '#fff' }});
  document.body.removeChild(card);
  const dataUrl = canvas.toDataURL('image/png');

  const w = window.open('', '_blank');
  w.document.write(
    '<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width">' +
    '<title>Translator Export</title>' +
    '<style>body{{margin:0;display:flex;justify-content:center;align-items:start;' +
    'min-height:100vh;background:#f0f0f0;padding:1rem;}}' +
    'img{{max-width:100%;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.1);}}' +
    'p{{text-align:center;color:#999;font:0.75rem -apple-system,sans-serif;margin-top:0.8rem;}}</style>' +
    '</head><body><div><img src="' + dataUrl + '"/>' +
    '<p>Long-press image to save to Photos</p></div></body></html>'
  );
  w.document.close();
}}

/* Speech recognition */
function makeSR() {{
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {{ status.textContent = 'Not supported in this browser'; return null; }}
  const r = new SR();
  r.continuous = true;
  r.interimResults = true;
  r.lang = 'zh-CN';

  r.onresult = async e => {{
    let interim = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {{
      const t = e.results[i][0].transcript;
      if (e.results[i].isFinal) {{
        live.textContent = '';
        const en = await toEN(t.trim());
        if (en) addLine(en);
      }} else {{
        interim += t;
      }}
    }}
    if (interim) live.textContent = interim;
  }};

  r.onend = () => {{ if (on) try {{ r.start(); }} catch {{}} }};
  r.onerror = e => {{
    if (e.error === 'no-speech' || e.error === 'aborted') return;
    status.textContent = 'Error: ' + e.error;
  }};
  return r;
}}

function toggle() {{
  if (on) {{
    on = false; rec?.stop();
    mic.classList.remove('on');
    status.textContent = 'Tap to start';
    live.textContent = '';
  }} else {{
    rec = makeSR();
    if (!rec) return;
    on = true; rec.start();
    mic.classList.add('on');
    status.textContent = 'Listening…';
  }}
}}
</script>
""", height=700)
