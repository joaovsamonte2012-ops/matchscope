import os
from pathlib import Path

root=Path(os.environ['ANDROID_DIR'])/'app/src/main/assets/www'
index=root/'index.html'
if not index.exists(): raise SystemExit('index.html nao encontrado')

css=r'''
#msPixelAvatar25{width:min(310px,82vw);height:390px;margin:8px auto 12px;position:relative;display:flex;align-items:flex-end;justify-content:center;filter:drop-shadow(0 12px 18px #0009)}
#msPixelAvatar25 .pa-stage{position:absolute;left:10%;right:10%;bottom:5px;height:30px;border-radius:50%;background:radial-gradient(ellipse,#1c8fff88 0,#074b9d66 45%,transparent 72%);box-shadow:0 0 22px #168cff88}
#msPixelAvatar25 svg{width:100%;height:100%;overflow:visible;image-rendering:pixelated;shape-rendering:crispEdges;animation:paIdle 1.9s steps(4,end) infinite;transform-origin:50% 88%}
#msPixelAvatar25 .pa-arm{transform-origin:111px 171px;animation:paArm 2.6s steps(4,end) infinite}
#msPixelAvatar25 .pa-cape{animation:paCape 1.5s steps(3,end) infinite;transform-origin:132px 155px}
#msPixelAvatar25 .pa-glow{animation:paGlow 1s steps(2,end) infinite}
#msPixelAvatar25 [data-equip]{display:none}.ms-eq-weapon #msEqWeapon,.ms-eq-cape #msEqCape,.ms-eq-armor #msEqArmor,.ms-eq-boots #msEqBoots,.ms-eq-head #msEqHead,.ms-eq-aura #msEqAura{display:block}
@keyframes paIdle{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
@keyframes paArm{0%,100%{transform:rotate(0)}50%{transform:rotate(-4deg)}}
@keyframes paCape{0%,100%{transform:skewX(0)}50%{transform:skewX(3deg)}}
@keyframes paGlow{0%,100%{opacity:.55}50%{opacity:1}}
.ms-pixel-badge25{position:absolute;top:8px;right:8px;padding:5px 8px;border-radius:9px;background:#07182ddd;border:1px solid #28a8ff66;color:#7dd3fc;font:800 9px/1 system-ui;letter-spacing:.08em}
'''

js=r'''(()=>{'use strict';
const KEY='ms_pixel_equipment_v25';
let eq={weapon:false,cape:false,armor:false,boots:false,head:false,aura:false};try{eq={...eq,...JSON.parse(localStorage.getItem(KEY)||'{}')}}catch(e){}
function avatar(){return `<div id="msPixelAvatar25"><div class="pa-stage"></div><div class="ms-pixel-badge25">PIXEL AVATAR</div><svg viewBox="0 0 240 390" aria-label="Personagem pixel art animado"><defs><filter id="g25"><feGaussianBlur stdDeviation="3"/></filter></defs><g id="msEqAura" data-equip="aura" class="pa-glow"><ellipse cx="120" cy="345" rx="82" ry="26" fill="none" stroke="#20a7ff" stroke-width="5" opacity=".7"/><ellipse cx="120" cy="345" rx="65" ry="18" fill="none" stroke="#67e8f9" stroke-width="2"/></g><g class="pa-cape" id="msEqCape" data-equip="cape"><path d="M139 151 L190 190 L180 326 L139 292 Z" fill="#0759c7" stroke="#f5b82e" stroke-width="5"/><path d="M145 171 L179 196 L169 303" fill="none" stroke="#2196ff" stroke-width="6"/></g><g><rect x="91" y="80" width="58" height="61" rx="9" fill="#d89062"/><path d="M88 92 L94 68 L105 75 L113 59 L122 70 L133 57 L138 72 L154 66 L151 99 L143 88 L132 94 L120 83 L108 96 Z" fill="#5a2a19"/><rect x="100" y="101" width="12" height="5" fill="#171717"/><rect x="133" y="101" width="12" height="5" fill="#171717"/><rect x="111" y="119" width="30" height="18" fill="#4b2519"/><rect x="105" y="126" width="42" height="10" fill="#4b2519"/></g><g id="baseBody"><rect x="83" y="145" width="75" height="93" rx="8" fill="#f4f6f8" stroke="#c9d2df" stroke-width="4"/><rect x="83" y="145" width="75" height="14" fill="#16263c"/><rect x="113" y="165" width="16" height="16" rx="3" fill="#13263d"/><path d="M83 157 L62 173 L69 216 L87 207 Z" fill="#d89062"/><path d="M158 157 L178 173 L171 216 L154 207 Z" fill="#d89062"/><rect x="57" y="204" width="20" height="14" fill="#172338"/><rect x="165" y="204" width="20" height="14" fill="#172338"/><path d="M88 235 L119 235 L114 293 L79 293 Z" fill="#202838"/><path d="M119 235 L153 235 L162 293 L125 293 Z" fill="#202838"/><path d="M79 293 L113 293 L109 340 L82 340 Z" fill="#d89062"/><path d="M126 293 L162 293 L157 340 L130 340 Z" fill="#d89062"/><rect x="81" y="319" width="29" height="22" fill="#f4f6f8"/><rect x="130" y="319" width="29" height="22" fill="#f4f6f8"/><path d="M74 337 L112 337 L116 357 L70 357 Z" fill="#f3f4f6" stroke="#16263c" stroke-width="6"/><path d="M126 337 L164 337 L171 357 L124 357 Z" fill="#f3f4f6" stroke="#16263c" stroke-width="6"/></g><g id="msEqArmor" data-equip="armor"><path d="M79 148 L101 137 L120 151 L140 137 L162 149 L153 238 L87 238 Z" fill="#0758bd" stroke="#f2b92f" stroke-width="6"/><path d="M92 153 L72 160 L64 184 L86 191 L98 168 Z" fill="#e4a92e" stroke="#ffd86a" stroke-width="4"/><path d="M149 153 L169 160 L178 184 L156 191 L144 168 Z" fill="#e4a92e" stroke="#ffd86a" stroke-width="4"/><path d="M106 170 L120 160 L134 170 L128 198 L120 207 L112 198 Z" fill="#f0b62d"/></g><g id="msEqBoots" data-equip="boots"><path d="M76 302 L112 302 L111 350 L68 350 L74 327 Z" fill="#d89c20" stroke="#ffd45c" stroke-width="5"/><path d="M127 302 L163 302 L171 350 L125 350 Z" fill="#d89c20" stroke="#ffd45c" stroke-width="5"/></g><g id="msEqHead" data-equip="head"><path d="M88 93 L94 67 L120 54 L148 68 L153 98 L142 88 L132 96 L120 83 L107 96 Z" fill="#1555a4" stroke="#f2b72e" stroke-width="5"/><path d="M104 72 L120 60 L136 72 L132 84 L108 84 Z" fill="#e5aa27"/></g><g class="pa-arm" id="msEqWeapon" data-equip="weapon"><path d="M66 214 L52 235 L38 316" stroke="#d9f8ff" stroke-width="10"/><path d="M66 214 L52 235 L38 316" stroke="#16a7ff" stroke-width="5"/><path d="M52 224 L35 215" stroke="#f2b72e" stroke-width="8"/><circle cx="54" cy="224" r="7" fill="#ffd65a"/><g class="pa-glow" filter="url(#g25)"><path d="M51 236 L38 316" stroke="#22aaff" stroke-width="12" opacity=".55"/></g></g></svg></div>`}
function apply(){const a=document.getElementById('msPixelAvatar25');if(!a)return;['weapon','cape','armor','boots','head','aura'].forEach(k=>a.classList.toggle('ms-eq-'+k,!!eq[k]))}
function classify(t){t=t.toLowerCase();if(/espada|cajado|arma|lâmina|lamina|machado/.test(t))return'weapon';if(/capa|manto/.test(t))return'cape';if(/armadura|peitoral|ombreira/.test(t))return'armor';if(/bota|tênis|tenis/.test(t))return'boots';if(/coroa|chapéu|chapeu|capacete/.test(t))return'head';if(/aura|asas|efeito/.test(t))return'aura';return null}
function hookEquip(){document.addEventListener('click',e=>{const b=e.target.closest('button');if(!b||!/equip/i.test(b.textContent||''))return;const card=b.closest('article,section,[class*=card],[class*=item]')||b.parentElement;const k=classify((card&&card.innerText)||'');if(!k)return;eq[k]=true;localStorage.setItem(KEY,JSON.stringify(eq));setTimeout(apply,80)},true)}
function mount(){if(document.getElementById('msPixelAvatar25')){apply();return}const nodes=[...document.querySelectorAll('div,section,main')];const panel=nodes.find(n=>/Meu jogador/i.test(n.textContent||'')&&n.querySelector('svg')&&n.getBoundingClientRect().height>300);if(!panel)return;const candidates=[...panel.querySelectorAll('svg')].filter(s=>s.getBoundingClientRect().height>180);const old=candidates[0];if(old){const wrap=old.parentElement;wrap.innerHTML=avatar();apply();return}const target=panel.querySelector('[class*=character],[id*=character],[class*=avatar],[id*=avatar]');if(target){target.innerHTML=avatar();apply()}}
function boot(){hookEquip();mount();new MutationObserver(()=>mount()).observe(document.body,{childList:true,subtree:true})}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();'''

(root/'beta-v25.css').write_text(css,encoding='utf-8')
(root/'beta-v25.js').write_text(js,encoding='utf-8')
h=index.read_text(encoding='utf-8')
if 'beta-v25.css' not in h:h=h.replace('</head>','<link rel="stylesheet" href="beta-v25.css?v=25"></head>')
if 'beta-v25.js' not in h:h=h.replace('</body>','<script src="beta-v25.js?v=25"></script></body>')
index.write_text(h,encoding='utf-8')
print('Beta 25 pixel avatar aplicado')
