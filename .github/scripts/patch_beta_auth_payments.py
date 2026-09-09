import os
import json
from pathlib import Path

android_dir = Path(os.environ["ANDROID_DIR"])
www = android_dir / "app/src/main/assets/www"
index = www / "index.html"
if not index.exists():
    raise SystemExit("ERRO: index.html nao encontrado")

firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY", ""),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
    "appId": os.getenv("FIREBASE_APP_ID", ""),
}

css = r'''
:root{--ap-green:#17c873;--ap-dark:#0d151f;--ap-panel:#162230;--ap-text:#f5f7fa;--ap-muted:#aeb8c5}
.ms-account-btn{position:fixed;left:14px;bottom:72px;z-index:99990;border:1px solid #ffffff18;border-radius:999px;background:#1a2735;color:#fff;padding:11px 14px;font-weight:900;box-shadow:0 8px 24px #0007}
.ms-account{position:fixed;z-index:99996;inset:8px;display:none;flex-direction:column;background:var(--ap-dark);color:var(--ap-text);border:1px solid #ffffff18;border-radius:20px;overflow:hidden;box-shadow:0 24px 70px #000d;font-family:system-ui,sans-serif}.ms-account.open{display:flex}.ms-account-head{display:flex;justify-content:space-between;align-items:center;padding:14px 15px;border-bottom:1px solid #ffffff12}.ms-account-head h2{font-size:17px;margin:0}.ms-account-close{border:0;background:transparent;color:#fff;font-size:25px}.ms-account-scroll{overflow:auto;padding:14px}.ms-auth-card,.ms-paid-card{background:#ffffff08;border:1px solid #ffffff12;border-radius:16px;padding:13px;margin-bottom:13px}.ms-auth-title{font-size:14px;font-weight:1000;margin-bottom:5px}.ms-auth-sub{font-size:10px;color:var(--ap-muted);line-height:1.35;margin-bottom:11px}.ms-auth-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.ms-auth-provider{border:1px solid #ffffff18;border-radius:12px;background:#ffffff0b;color:#fff;padding:11px 8px;font-weight:900;font-size:11px}.ms-auth-provider.google{background:#fff;color:#17202a}.ms-auth-provider.apple{background:#080808}.ms-auth-provider.facebook{background:#1769e0}.ms-auth-status{margin-top:10px;font-size:10px;color:var(--ap-muted)}
.ms-userbox{display:flex;gap:10px;align-items:center;background:#ffffff08;border-radius:13px;padding:10px}.ms-user-avatar{width:42px;height:42px;border-radius:50%;background:#ffffff12;display:flex;align-items:center;justify-content:center;font-size:19px}.ms-user-name{font-weight:1000;font-size:13px}.ms-user-mail{font-size:10px;color:var(--ap-muted)}.ms-logout{margin-left:auto;border:0;border-radius:10px;background:#ffffff10;color:#fff;padding:8px 10px;font-weight:900;font-size:10px}
.ms-paid-list{display:grid;gap:9px}.ms-paid-item{display:grid;grid-template-columns:42px 1fr auto;gap:10px;align-items:center;background:#ffffff07;border:1px solid #ffffff10;border-radius:13px;padding:10px}.ms-paid-icon{width:42px;height:42px;border-radius:12px;background:#ffffff0b;display:flex;align-items:center;justify-content:center;font-size:23px}.ms-paid-name{font-size:11px;font-weight:1000}.ms-paid-desc{font-size:9px;color:var(--ap-muted);margin-top:2px}.ms-paid-buy{border:0;border-radius:10px;background:var(--ap-green);color:#07140c;padding:9px 11px;font-size:10px;font-weight:1000}.ms-paid-note{font-size:9px;color:var(--ap-muted);line-height:1.35;margin-top:10px}.ms-disabled{opacity:.5}
'''
(www / "beta-auth-payments.css").write_text(css, encoding="utf-8")

cfg = json.dumps(firebase_config, ensure_ascii=False)
js = r'''(()=>{
 const BACKEND=localStorage.getItem('ms_beta_backend')||'https://matchscope-kjf9.onrender.com';
 const FIREBASE_CONFIG=__FIREBASE_CONFIG__;
 const paidProducts=[
   {id:'matchscope.cosmetic.founder_frame',icon:'👑',name:'Moldura Fundador',desc:'Moldura cosmética exclusiva e permanente.'},
   {id:'matchscope.cosmetic.stadium_night',icon:'🌙',name:'Estádio Noite Premium',desc:'Fundo cosmético noturno para o perfil.'},
   {id:'matchscope.cosmetic.legend_kit',icon:'⭐',name:'Kit Lenda Premium',desc:'Uniforme cosmético exclusivo para o jogador.'}
 ];
 let fb=null,auth=null;
 function firebaseReady(){return FIREBASE_CONFIG.apiKey&&FIREBASE_CONFIG.authDomain&&FIREBASE_CONFIG.projectId&&FIREBASE_CONFIG.appId}
 async function loadFirebase(){
   if(auth||!firebaseReady())return auth;
   try{
     const appMod=await import('https://www.gstatic.com/firebasejs/12.2.1/firebase-app.js');
     const authMod=await import('https://www.gstatic.com/firebasejs/12.2.1/firebase-auth.js');
     fb={...authMod}; const app=appMod.initializeApp(FIREBASE_CONFIG); auth=authMod.getAuth(app);
     authMod.onAuthStateChanged(auth,async user=>{if(user){localStorage.setItem('ms_auth_uid',user.uid);await syncSession(user)} render()});
     return auth;
   }catch(e){status('Não foi possível carregar o login social.');return null}
 }
 async function syncSession(user){
   try{const token=await user.getIdToken();localStorage.setItem('ms_auth_token',token);await fetch(`${BACKEND}/auth/session`,{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+token},body:JSON.stringify({legacyUserId:localStorage.getItem('ms_uid')||''})})}catch{}
 }
 function ensure(){
   if(document.getElementById('msAccountBtn'))return;
   document.body.insertAdjacentHTML('beforeend',`<button id="msAccountBtn" class="ms-account-btn">👤 Conta</button><section id="msAccount" class="ms-account"><div class="ms-account-head"><h2>Conta e pagamentos</h2><button id="msAccountClose" class="ms-account-close">×</button></div><div id="msAccountScroll" class="ms-account-scroll"></div></section>`);
   document.getElementById('msAccountBtn').onclick=()=>{document.getElementById('msAccount').classList.add('open');loadFirebase().then(render)};
   document.getElementById('msAccountClose').onclick=()=>document.getElementById('msAccount').classList.remove('open');
 }
 function status(t){const e=document.getElementById('msAuthStatus');if(e)e.textContent=t}
 function providerButton(cls,label,provider){return `<button class="ms-auth-provider ${cls}" data-provider="${provider}">${label}</button>`}
 function currentUser(){return auth?.currentUser||null}
 function render(){
   const root=document.getElementById('msAccountScroll');if(!root)return;const u=currentUser();
   const authHtml=u?`<div class="ms-userbox"><div class="ms-user-avatar">${u.photoURL?`<img src="${u.photoURL}" style="width:42px;height:42px;border-radius:50%">`:'⚽'}</div><div><div class="ms-user-name">${u.displayName||'Usuário MatchScope'}</div><div class="ms-user-mail">${u.email||'Conta conectada'}</div></div><button id="msLogout" class="ms-logout">Sair</button></div>`:`<div class="ms-auth-title">Entrar na MatchScope</div><div class="ms-auth-sub">Use sua conta para manter nível, itens e compras sincronizados entre aparelhos.</div><div class="ms-auth-grid">${providerButton('google','Google / Play','google')}${providerButton('apple',' Apple','apple')}${providerButton('facebook','Facebook','facebook')}${providerButton('','Gmail','google')}</div><div id="msAuthStatus" class="ms-auth-status">${firebaseReady()?'Escolha uma conta para entrar.':'Login pronto no app; faltam as credenciais Firebase do projeto.'}</div>`;
   root.innerHTML=`<div class="ms-auth-card">${authHtml}</div><div class="ms-paid-card"><div class="ms-auth-title">Itens premium</div><div class="ms-auth-sub">Compras reais apenas para cosméticos fixos. MatchCoins e recompensas de palpites continuam gratuitas.</div><div class="ms-paid-list">${paidProducts.map(p=>`<div class="ms-paid-item"><div class="ms-paid-icon">${p.icon}</div><div><div class="ms-paid-name">${p.name}</div><div class="ms-paid-desc">${p.desc}</div></div><button class="ms-paid-buy" data-product="${p.id}">Comprar</button></div>`).join('')}</div><div class="ms-paid-note">No Android, a compra é processada pelo Google Play Billing. No iPhone, será processada pelo StoreKit quando existir a versão iOS.</div></div>`;
   root.querySelectorAll('[data-provider]').forEach(b=>b.onclick=()=>login(b.dataset.provider));
   root.querySelectorAll('[data-product]').forEach(b=>b.onclick=()=>purchase(b.dataset.product,b));
   const lo=document.getElementById('msLogout');if(lo)lo.onclick=logout;
 }
 async function login(provider){
   const a=await loadFirebase();if(!a||!fb)return status('Configure o Firebase Authentication para ativar este login.');
   try{
     let p;if(provider==='google')p=new fb.GoogleAuthProvider();else if(provider==='facebook')p=new fb.FacebookAuthProvider();else{p=new fb.OAuthProvider('apple.com');p.addScope('email');p.addScope('name')}
     await fb.signInWithPopup(a,p);
   }catch(e){status('Falha ao entrar. Verifique a configuração do provedor.')}
 }
 async function logout(){try{await fb.signOut(auth);localStorage.removeItem('ms_auth_token');localStorage.removeItem('ms_auth_uid');render()}catch{}}
 async function purchase(productId,button){
   if(!currentUser()){button.textContent='Entre primeiro';return}
   const bridge=window.MatchScopeBilling;
   if(bridge&&typeof bridge.purchase==='function'){button.disabled=true;button.textContent='Abrindo loja...';try{bridge.purchase(productId)}finally{setTimeout(()=>{button.disabled=false;button.textContent='Comprar'},2500)};return}
   button.textContent='Disponível na Play';setTimeout(()=>button.textContent='Comprar',1800)
 }
 ensure();loadFirebase().then(render);
 window.MatchScopeAuth={render};
})();'''.replace('__FIREBASE_CONFIG__', cfg)
(www / "beta-auth-payments.js").write_text(js, encoding="utf-8")

html=index.read_text(encoding="utf-8")
if 'beta-auth-payments.css' not in html:
    html=html.replace('</head>','<link rel="stylesheet" href="beta-auth-payments.css">\n</head>')
if 'beta-auth-payments.js' not in html:
    html=html.replace('</body>','<script src="beta-auth-payments.js"></script>\n</body>')
index.write_text(html,encoding="utf-8")
print("Conta, login social e camada de pagamentos adicionados à Beta.")
