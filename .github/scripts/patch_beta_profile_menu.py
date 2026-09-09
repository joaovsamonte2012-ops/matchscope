import os
from pathlib import Path

android_dir = Path(os.environ["ANDROID_DIR"])
www = android_dir / "app/src/main/assets/www"
index = www / "index.html"
if not index.exists():
    raise SystemExit("ERRO: index.html nao encontrado")

css = r'''
:root{--ms-safe-top:env(safe-area-inset-top,0px);--ms-safe-right:env(safe-area-inset-right,0px);--ms-safe-bottom:env(safe-area-inset-bottom,0px);--ms-safe-left:env(safe-area-inset-left,0px)}
/* Os botoes antigos continuam no DOM para manter compatibilidade, mas deixam de ocupar a tela. */
#msAccountBtn,#msProfileBtn,#msChatButton{display:none!important}
.ms-profile-menu-trigger{position:fixed;z-index:100020;right:max(14px,calc(var(--ms-safe-right) + 10px));top:max(14px,calc(var(--ms-safe-top) + 10px));width:48px;height:48px;padding:0;border:1px solid #ffffff26;border-radius:50%;background:#172434;color:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 26px #0008;font-size:22px;font-weight:900}
.ms-profile-menu-trigger img{width:100%;height:100%;object-fit:cover;border-radius:50%}
.ms-profile-menu{position:fixed;z-index:100019;right:max(12px,calc(var(--ms-safe-right) + 8px));top:max(70px,calc(var(--ms-safe-top) + 66px));width:min(286px,calc(100vw - 24px - var(--ms-safe-left) - var(--ms-safe-right)));max-height:calc(100dvh - 92px - var(--ms-safe-top) - var(--ms-safe-bottom));overflow:auto;display:none;background:#101a27;border:1px solid #ffffff1c;border-radius:18px;padding:8px;box-shadow:0 18px 55px #000c;color:#fff;font-family:system-ui,sans-serif;overscroll-behavior:contain}
.ms-profile-menu.open{display:block}.ms-profile-menu-title{padding:8px 10px 7px;font-size:11px;color:#aeb8c5;font-weight:800}.ms-profile-menu-item{width:100%;display:flex;align-items:center;gap:11px;border:0;border-radius:13px;background:transparent;color:#fff;padding:12px;text-align:left;font-size:14px;font-weight:850}.ms-profile-menu-item:active{background:#ffffff12}.ms-profile-menu-icon{width:30px;height:30px;border-radius:10px;background:#ffffff0d;display:flex;align-items:center;justify-content:center;font-size:17px;flex:none}.ms-profile-menu-copy{min-width:0;flex:1}.ms-profile-menu-copy small{display:block;color:#96a5b7;font-size:10px;font-weight:600;margin-top:2px}.ms-profile-menu-backdrop{position:fixed;z-index:100018;inset:0;display:none;background:transparent}.ms-profile-menu-backdrop.open{display:block}
/* Modais respeitam recortes, barras do sistema e teclado em aparelhos diferentes. */
.ms-account,.ms-prog{top:max(8px,var(--ms-safe-top))!important;right:max(8px,var(--ms-safe-right))!important;bottom:max(8px,var(--ms-safe-bottom))!important;left:max(8px,var(--ms-safe-left))!important;max-height:calc(100dvh - var(--ms-safe-top) - var(--ms-safe-bottom) - 16px)!important}
.ms-chat-panel{left:max(10px,var(--ms-safe-left))!important;right:max(10px,var(--ms-safe-right))!important;bottom:max(10px,var(--ms-safe-bottom))!important;max-height:min(72dvh,calc(100dvh - var(--ms-safe-top) - var(--ms-safe-bottom) - 20px))!important}
.ms-account-scroll,.ms-prog-scroll,.ms-chat-list{overscroll-behavior:contain;-webkit-overflow-scrolling:touch}
@media(max-width:420px){.ms-profile-menu-trigger{width:44px;height:44px}.ms-profile-menu{top:max(64px,calc(var(--ms-safe-top) + 60px))}}
@media(orientation:landscape) and (max-height:500px){.ms-profile-menu{top:max(58px,calc(var(--ms-safe-top) + 54px));max-height:calc(100dvh - 68px - var(--ms-safe-top) - var(--ms-safe-bottom))}.ms-account,.ms-prog{border-radius:14px!important}}
'''
(www / "beta-profile-menu.css").write_text(css, encoding="utf-8")

js = r'''(()=>{
 const $=id=>document.getElementById(id);
 function userPhoto(){try{return window.MatchScoreAuth?.photoURL||window.MatchScopeAuth?.photoURL||''}catch{return ''}}
 function ensure(){
   if($('msProfileMenuTrigger'))return;
   document.body.insertAdjacentHTML('beforeend',`<div id="msProfileMenuBackdrop" class="ms-profile-menu-backdrop"></div><button id="msProfileMenuTrigger" class="ms-profile-menu-trigger" aria-label="Abrir menu do perfil" aria-expanded="false">👤</button><div id="msProfileMenu" class="ms-profile-menu" role="menu"><div class="ms-profile-menu-title">MatchScore</div><button class="ms-profile-menu-item" data-open="account"><span class="ms-profile-menu-icon">👤</span><span class="ms-profile-menu-copy">Conta<small>Login e configurações da conta</small></span></button><button class="ms-profile-menu-item" data-open="player"><span class="ms-profile-menu-icon">⚽</span><span class="ms-profile-menu-copy">Meu jogador<small>Nível, itens e evolução</small></span></button><button class="ms-profile-menu-item" data-open="chat"><span class="ms-profile-menu-icon">💬</span><span class="ms-profile-menu-copy">Chat ao vivo<small>Converse durante a partida</small></span></button></div>`);
   const trigger=$('msProfileMenuTrigger'),menu=$('msProfileMenu'),backdrop=$('msProfileMenuBackdrop');
   const close=()=>{menu.classList.remove('open');backdrop.classList.remove('open');trigger.setAttribute('aria-expanded','false')};
   trigger.onclick=()=>{const open=!menu.classList.contains('open');menu.classList.toggle('open',open);backdrop.classList.toggle('open',open);trigger.setAttribute('aria-expanded',String(open))};
   backdrop.onclick=close;
   menu.querySelectorAll('[data-open]').forEach(b=>b.onclick=()=>{const kind=b.dataset.open;close();if(kind==='account')$('msAccountBtn')?.click();if(kind==='player')$('msProfileBtn')?.click();if(kind==='chat')$('msChatButton')?.click()});
   document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
   refreshAvatar();
 }
 function refreshAvatar(){const b=$('msProfileMenuTrigger');if(!b)return;const src=userPhoto();if(src)b.innerHTML=`<img src="${src.replace(/"/g,'&quot;')}" alt="Perfil">`;else b.textContent='👤'}
 function fitKeyboard(){
   if(!window.visualViewport)return;
   const vv=window.visualViewport;
   const keyboard=Math.max(0,window.innerHeight-vv.height-vv.offsetTop);
   document.documentElement.style.setProperty('--ms-keyboard',keyboard+'px');
   const chat=$('msChatPanel');if(chat&&chat.classList.contains('open'))chat.style.bottom=`max(10px, calc(env(safe-area-inset-bottom, 0px) + ${keyboard}px))`;
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ensure);else ensure();
 if(window.visualViewport){visualViewport.addEventListener('resize',fitKeyboard);visualViewport.addEventListener('scroll',fitKeyboard)}
 setInterval(refreshAvatar,1500);fitKeyboard();
})();'''
(www / "beta-profile-menu.js").write_text(js, encoding="utf-8")

html=index.read_text(encoding="utf-8")
if 'beta-profile-menu.css' not in html:
    html=html.replace('</head>','<link rel="stylesheet" href="beta-profile-menu.css">\n</head>')
if 'beta-profile-menu.js' not in html:
    html=html.replace('</body>','<script src="beta-profile-menu.js"></script>\n</body>')
index.write_text(html,encoding="utf-8")
print("Menu de perfil responsivo aplicado: Conta, Meu jogador e Chat sem sobrepor a navegacao inferior.")
