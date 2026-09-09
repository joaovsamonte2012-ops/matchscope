import os
import re
from pathlib import Path

android_dir = Path(os.environ["ANDROID_DIR"])
www = android_dir / "app/src/main/assets/www"
app_js = www / "app.js"
index = www / "index.html"

if not app_js.exists() or not index.exists():
    raise SystemExit("ERRO: arquivos web da aplicacao nao encontrados")

js = app_js.read_text(encoding="utf-8")

# Marca a partida atual para que o chat use uma sala exclusiva por fixtureId.
if "window.__msFixtureId" not in js:
    marker = re.search(r"const\s*\[\s*d\s*,\s*h\s*,\s*a\s*,\s*stats\s*,\s*events\s*,\s*lineups\s*\]\s*=\s*await\s+Promise\.all", js)
    if marker:
        js = js[:marker.start()] + "window.__msFixtureId=String(id);\n      " + js[marker.start():]
    else:
        marker = re.search(r"const\s*\[\s*d\s*,\s*h\s*,\s*a\s*\]\s*=\s*await\s+Promise\.all", js)
        if marker:
            js = js[:marker.start()] + "window.__msFixtureId=String(id);\n      " + js[marker.start():]
        else:
            print("AVISO: nao foi possivel marcar fixtureId automaticamente; chat usara fallback visual.")

app_js.write_text(js, encoding="utf-8")

css = r'''
:root{--ms-green:#17c873;--ms-bg:#101722;--ms-panel:#17212e;--ms-text:#f5f7fa;--ms-muted:#aeb7c2}
.ms-chat-button{position:fixed;right:16px;bottom:22px;z-index:99990;border:0;border-radius:999px;background:var(--ms-green);color:#09120e;font-weight:900;padding:12px 16px;box-shadow:0 8px 28px #0008}
.ms-chat-panel{position:fixed;z-index:99991;left:10px;right:10px;bottom:10px;max-height:72vh;background:var(--ms-bg);border:1px solid #ffffff18;border-radius:18px;box-shadow:0 18px 55px #000c;display:none;overflow:hidden;color:var(--ms-text);font-family:system-ui,sans-serif}
.ms-chat-panel.open{display:flex;flex-direction:column}.ms-chat-head{padding:12px 14px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #ffffff14}.ms-chat-title{font-weight:900}.ms-level-chip{background:#ffffff10;border:1px solid #ffffff18;border-radius:999px;padding:5px 9px;font-size:11px;font-weight:800}.ms-chat-close{background:transparent;border:0;color:#fff;font-size:22px}.ms-xp-wrap{padding:8px 14px 10px;border-bottom:1px solid #ffffff10}.ms-xp-line{display:flex;justify-content:space-between;font-size:10px;color:var(--ms-muted);margin-bottom:5px}.ms-xp-bar{height:6px;background:#ffffff10;border-radius:99px;overflow:hidden}.ms-xp-fill{height:100%;background:var(--ms-green);width:0%;transition:width .25s ease}.ms-chat-list{padding:12px;overflow:auto;min-height:180px;flex:1}.ms-msg{padding:8px 10px;margin-bottom:8px;background:#ffffff08;border-radius:12px}.ms-msg-meta{display:flex;gap:7px;align-items:center;font-size:10px;color:var(--ms-muted);margin-bottom:3px}.ms-msg-name{font-weight:900;color:#fff}.ms-msg-level{font-weight:900;color:var(--ms-green)}.ms-msg-text{font-size:13px;line-height:1.3;word-break:break-word}.ms-chat-compose{display:grid;grid-template-columns:1fr auto;gap:8px;padding:10px;border-top:1px solid #ffffff12}.ms-chat-input{min-width:0;border:1px solid #ffffff18;background:#ffffff0a;color:#fff;border-radius:12px;padding:11px 12px;outline:none}.ms-chat-send{border:0;border-radius:12px;padding:0 14px;background:var(--ms-green);color:#09120e;font-weight:900}.ms-chat-note{font-size:9px;color:var(--ms-muted);padding:0 12px 9px}
.ms-event-decorated{position:relative}.ms-event-icon{display:inline-flex;vertical-align:middle;align-items:center;justify-content:center;margin-right:7px;flex:none}.ms-event-goal{width:14px;height:14px;border-radius:50%;background:#fff;border:2px solid #1c2633;box-shadow:inset 0 0 0 2px #fff,0 0 0 1px #ffffff55}.ms-event-sub{font-size:17px;font-weight:900;color:#58d68d}.ms-event-card-yellow,.ms-event-card-red{width:10px;height:14px;border-radius:2px;box-shadow:0 1px 2px #0007}.ms-event-card-yellow{background:#ffd43b}.ms-event-card-red{background:#ff4d4f}.ms-sub-out{color:#b7bec7!important;font-weight:600!important}.ms-sub-in{color:#fff!important;font-weight:800!important}
'''
(www / "beta-social.css").write_text(css, encoding="utf-8")

social_js = r'''
(()=>{
  const BACKEND=localStorage.getItem('ms_beta_backend')||'https://matchscope-kjf9.onrender.com';
  const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const uid=()=>{let v=localStorage.getItem('ms_uid');if(!v){v='u_'+Date.now().toString(36)+Math.random().toString(36).slice(2,9);localStorage.setItem('ms_uid',v)}return v};
  const nick=()=>{let v=localStorage.getItem('ms_nick');if(!v){v='Torcedor '+uid().slice(-4).toUpperCase();localStorage.setItem('ms_nick',v)}return v};
  let profile={level:1,xp:0,currentLevelXp:0,nextLevelXp:40,progress:0};
  let currentFixture=''; let stream=null; let loadedFixture='';

  function fixture(){return String(window.__msFixtureId||document.body?.dataset?.fixtureId||'').trim()}
  function ensureUI(){
    if(document.getElementById('msChatButton'))return;
    document.body.insertAdjacentHTML('beforeend',`<button id="msChatButton" class="ms-chat-button">Chat ao vivo</button><section id="msChatPanel" class="ms-chat-panel"><div class="ms-chat-head"><div><div class="ms-chat-title">Chat da partida</div><div style="font-size:10px;color:#aeb7c2" id="msChatRoom">Aguardando partida</div></div><div style="display:flex;gap:8px;align-items:center"><span id="msLevelChip" class="ms-level-chip">Nv. 1</span><button id="msChatClose" class="ms-chat-close">×</button></div></div><div class="ms-xp-wrap"><div class="ms-xp-line"><span id="msXpText">0 XP</span><span id="msXpNext">40 para o próximo nível</span></div><div class="ms-xp-bar"><div id="msXpFill" class="ms-xp-fill"></div></div></div><div id="msChatList" class="ms-chat-list"></div><div class="ms-chat-compose"><input id="msChatInput" class="ms-chat-input" maxlength="280" placeholder="Comente sobre a partida"><button id="msChatSend" class="ms-chat-send">Enviar</button></div><div class="ms-chat-note">Mensagens repetidas e spam não geram XP.</div></section>`);
    const panel=document.getElementById('msChatPanel');
    document.getElementById('msChatButton').onclick=()=>{panel.classList.add('open');syncFixture(true)};
    document.getElementById('msChatClose').onclick=()=>panel.classList.remove('open');
    document.getElementById('msChatSend').onclick=send;
    document.getElementById('msChatInput').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();send()}});
  }
  function updateProfile(p){profile=p||profile;document.getElementById('msLevelChip').textContent='Nv. '+(profile.level||1);document.getElementById('msXpText').textContent=(profile.xp||0)+' XP';document.getElementById('msXpNext').textContent=(profile.nextLevelXp-(profile.currentLevelXp||0))+' para o próximo nível';document.getElementById('msXpFill').style.width=Math.round((profile.progress||0)*100)+'%'}
  function renderMessage(m){const list=document.getElementById('msChatList');if(!list||document.getElementById('msm_'+m.id))return;const t=new Date(m.createdAt||Date.now()).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});list.insertAdjacentHTML('beforeend',`<div class="ms-msg" id="msm_${esc(m.id)}"><div class="ms-msg-meta"><span class="ms-msg-name">${esc(m.nickname||'Torcedor')}</span><span class="ms-msg-level">Nv. ${Number(m.level||1)}</span><span>${esc(t)}</span></div><div class="ms-msg-text">${esc(m.text||'')}</div></div>`);list.scrollTop=list.scrollHeight}
  async function loadMessages(){if(!currentFixture)return;try{const r=await fetch(`${BACKEND}/chat/messages/${encodeURIComponent(currentFixture)}`);if(!r.ok)return;const j=await r.json();(j.messages||[]).forEach(renderMessage)}catch{}}
  async function loadProfile(){try{const r=await fetch(`${BACKEND}/chat/profile/${encodeURIComponent(uid())}`);if(r.ok){const j=await r.json();updateProfile(j.profile)}}catch{}}
  function connect(){if(stream){stream.close();stream=null}if(!currentFixture)return;try{stream=new EventSource(`${BACKEND}/chat/stream/${encodeURIComponent(currentFixture)}`);stream.addEventListener('message',e=>{try{renderMessage(JSON.parse(e.data))}catch{}})}catch{}}
  async function send(){const input=document.getElementById('msChatInput');const text=(input?.value||'').trim();if(!currentFixture||text.length<2)return;input.disabled=true;try{const r=await fetch(`${BACKEND}/chat/messages/${encodeURIComponent(currentFixture)}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({userId:uid(),nickname:nick(),text})});if(r.ok){const j=await r.json();input.value='';if(j.message)renderMessage(j.message);if(j.profile)updateProfile(j.profile)}}catch{}finally{input.disabled=false;input.focus()}}
  function syncFixture(force=false){const f=fixture();if(!f)return;if(f===currentFixture&&!force)return;currentFixture=f;document.getElementById('msChatRoom').textContent='Sala #'+f;if(loadedFixture!==f){document.getElementById('msChatList').innerHTML='';loadedFixture=f}loadMessages();loadProfile();connect()}

  function icon(kind){const s=document.createElement('span');s.className='ms-event-icon '+kind;if(kind==='ms-event-sub')s.textContent='⇄';return s}
  function decorateEvents(){
    const all=[...document.querySelectorAll('div,li,p,span')];
    for(const el of all){if(el.dataset?.msEventDecorated)return;const txt=(el.textContent||'').trim();if(txt.length<3||txt.length>180)continue;const low=txt.toLocaleLowerCase('pt-BR');let k='';if(/\b(gol|goal)\b/.test(low))k='ms-event-goal';else if(/substit|entra|sai|replacement/.test(low))k='ms-event-sub';else if(/cart[aã]o amarelo|yellow card/.test(low))k='ms-event-card-yellow';else if(/cart[aã]o vermelho|red card/.test(low))k='ms-event-card-red';if(!k)continue;el.dataset.msEventDecorated='1';el.classList.add('ms-event-decorated');el.prepend(icon(k));if(k==='ms-event-sub'){const children=[...el.children].filter(x=>!x.classList.contains('ms-event-icon'));if(children.length>=2){children[0].classList.add('ms-sub-out');children[1].classList.add('ms-sub-in')}else{const parts=el.querySelectorAll('b,strong,span');if(parts[0])parts[0].classList.add('ms-sub-out');if(parts[1])parts[1].classList.add('ms-sub-in')}}}
  }
  ensureUI();loadProfile();setInterval(syncFixture,800);const mo=new MutationObserver(()=>{decorateEvents();syncFixture()});mo.observe(document.documentElement,{subtree:true,childList:true});decorateEvents();
})();
'''
(www / "beta-social.js").write_text(social_js, encoding="utf-8")

html = index.read_text(encoding="utf-8")
if 'beta-social.css' not in html:
    html = html.replace('</head>', '<link rel="stylesheet" href="beta-social.css">\n</head>')
if 'beta-social.js' not in html:
    html = html.replace('</body>', '<script src="beta-social.js"></script>\n</body>')
index.write_text(html, encoding="utf-8")

print("Beta social aplicada: chat por partida, XP/level e simbolos de eventos.")
