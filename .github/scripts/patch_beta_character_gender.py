import os
from pathlib import Path

android_dir=Path(os.environ['ANDROID_DIR'])
www=android_dir/'app/src/main/assets/www'
index=www/'index.html'
if not index.exists(): raise SystemExit('ERRO: index.html nao encontrado')

css=r'''
.ms-character-choice{display:flex;gap:8px;margin:0 0 12px}.ms-character-choice button{flex:1;border:1px solid #ffffff18;border-radius:11px;background:#ffffff09;color:#dfe8ef;padding:9px 8px;font-size:11px;font-weight:900}.ms-character-choice button.active{background:var(--pg-green,#17c873);color:#07130c;border-color:transparent}
'''
(www/'beta-character-gender.css').write_text(css,encoding='utf-8')

js=r'''(()=>{
 const KEY='ms_character_style';
 const style=()=>localStorage.getItem(KEY)||'male';
 function femaleSvg(p){const tier=p?.stage?.tier||1,c=['#88929d','#8aa6b8','#49a56d','#2fbe72','#20ce78','#12d783','#d6a843','#efb843','#ffd867'][Math.max(0,Math.min(8,tier-1))],gold=tier>=7?'#f2c45f':'#e9eef3',star=tier>=5?'★':'',crown=tier>=9?'♛':'';return `<svg class="ms-avatar" viewBox="0 0 150 200" xmlns="http://www.w3.org/2000/svg"><ellipse cx="75" cy="190" rx="52" ry="8" fill="#0005"/><path d="M48 48q0-38 27-39q29 2 29 39l-8 28H55z" fill="#2b211e"/><circle cx="75" cy="39" r="21" fill="#d2a47d"/><path d="M52 34q7-27 24-25q20 2 24 26q-13-9-25-8q-13 0-23 7" fill="#29231f"/><path d="M43 75q32-18 64 0l8 72H35z" fill="${c}" stroke="${gold}" stroke-width="3"/><path d="M45 79L23 130l17 8l23-47M105 79l22 51l-17 8l-23-47" fill="${c}" stroke="${gold}" stroke-width="3"/><path d="M53 144l-8 47h21l9-45M97 144l8 47H84l-9-45" fill="#171d26" stroke="${gold}" stroke-width="3"/><text x="75" y="116" fill="${gold}" text-anchor="middle" font-size="34" font-weight="900">${tier>=9?'10':tier}</text><text x="75" y="70" fill="#ffe072" text-anchor="middle" font-size="20">${star}</text><text x="75" y="24" fill="#ffe072" text-anchor="middle" font-size="25">${crown}</text></svg>`}
 function injectChoice(){const root=document.getElementById('msProgScroll');if(!root||root.querySelector('.ms-character-choice'))return;const hero=root.querySelector('.ms-hero-card');if(!hero)return;hero.insertAdjacentHTML('beforebegin',`<div class="ms-character-choice"><button data-character="male">⚽ Jogador</button><button data-character="female">⚽ Jogadora</button></div>`);root.querySelectorAll('[data-character]').forEach(b=>{b.classList.toggle('active',b.dataset.character===style());b.onclick=()=>{localStorage.setItem(KEY,b.dataset.character);apply();root.querySelectorAll('[data-character]').forEach(x=>x.classList.toggle('active',x.dataset.character===style()))}})}
 function apply(){const root=document.getElementById('msProgScroll');if(!root)return;const avatar=root.querySelector('.ms-avatar');if(style()==='female'&&avatar){const wrap=avatar.parentElement;const levelText=wrap.querySelector('.ms-level-big')?.textContent||'';const stageText=wrap.querySelector('.ms-stage-name')?.textContent||'';let tier=1;const m=levelText.match(/LVL\s+(\d+)/i);if(m)tier=Math.max(1,Math.min(9,Math.ceil(Number(m[1])/20)));avatar.outerHTML=femaleSvg({stage:{tier}})}injectChoice()}
 const observer=new MutationObserver(()=>apply());
 function start(){const p=document.getElementById('msProgScroll');if(p)observer.observe(p,{childList:true,subtree:true});apply()}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();
})();'''
(www/'beta-character-gender.js').write_text(js,encoding='utf-8')
html=index.read_text(encoding='utf-8')
if 'beta-character-gender.css' not in html: html=html.replace('</head>','<link rel="stylesheet" href="beta-character-gender.css">\n</head>')
if 'beta-character-gender.js' not in html: html=html.replace('</body>','<script src="beta-character-gender.js"></script>\n</body>')
index.write_text(html,encoding='utf-8')
print('Opcao Jogador/Jogadora adicionada ao Meu jogador.')
