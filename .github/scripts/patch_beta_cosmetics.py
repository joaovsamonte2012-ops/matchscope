import os
from pathlib import Path

android_dir = Path(os.environ['ANDROID_DIR'])
www = android_dir / 'app/src/main/assets/www'
index = www / 'index.html'
if not index.exists():
    raise SystemExit('ERRO: index.html nao encontrado')

css = r'''
.ms-cosmetics{margin-top:14px}.ms-cosmetics-note{font-size:10px;color:#aab5c2;margin:0 0 9px}.ms-cosmetic-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.ms-cosmetic{background:#ffffff08;border:1px solid #ffffff12;border-radius:14px;padding:10px;min-width:0}.ms-cosmetic-art{height:78px;border-radius:11px;display:grid;place-items:center;font-size:42px;background:linear-gradient(145deg,#152637,#0c1723);border:1px solid #ffffff12}.ms-cosmetic-name{font-size:11px;font-weight:900;margin-top:7px}.ms-cosmetic-kind{font-size:9px;color:#aab5c2}.ms-cosmetic-price{font-size:11px;font-weight:1000;color:#f3c969;margin-top:5px}.ms-cosmetic-rarity{font-size:8px;font-weight:900;padding:2px 6px;border-radius:99px;background:#ffffff12;float:right}.ms-cosmetic-buy{width:100%;border:0;border-radius:9px;padding:8px;margin-top:7px;background:#f3c969;color:#1a1404;font-size:10px;font-weight:1000}.ms-cosmetic-buy:disabled{opacity:.45}.ms-cosmetic-owned{background:#ffffff12;color:#fff}@media(max-width:360px){.ms-cosmetic-grid{grid-template-columns:1fr}}
'''
(www/'beta-cosmetics.css').write_text(css,encoding='utf-8')

js = r'''
(()=>{
 const EXTRA=[
  {id:'uniforme_elite',name:'Uniforme Elite',type:'gear',kind:'Uniforme',price:650,rarity:'Épico',icon:'👕'},
  {id:'uniforme_lendario',name:'Uniforme Lendário',type:'gear',kind:'Uniforme',price:500,rarity:'Raro',icon:'👕'},
  {id:'uniforme_fogo',name:'Uniforme Fogo',type:'gear',kind:'Uniforme',price:450,rarity:'Raro',icon:'🔥'},
  {id:'uniforme_estrela',name:'Uniforme Estrela',type:'gear',kind:'Uniforme',price:300,rarity:'Comum',icon:'⭐'},
  {id:'estadio_champions',name:'Estádio Champions',type:'stadium',kind:'Estádio',price:950,rarity:'Lendário',icon:'🏟️'},
  {id:'estadio_classico',name:'Estádio Clássico',type:'stadium',kind:'Estádio',price:700,rarity:'Épico',icon:'🏟️'},
  {id:'bola_champions',name:'Bola Champions',type:'gear',kind:'Bola',price:400,rarity:'Raro',icon:'⚽'},
  {id:'bola_dourada',name:'Bola Dourada',type:'gear',kind:'Bola',price:750,rarity:'Épico',icon:'🏆'},
  {id:'comemoracao_classica',name:'Comemoração Clássica',type:'gear',kind:'Comemoração',price:350,rarity:'Raro',icon:'🙌'},
  {id:'comemoracao_coracao',name:'Comemoração Coração',type:'gear',kind:'Comemoração',price:250,rarity:'Comum',icon:'🫶'},
  {id:'efeito_chamas',name:'Efeito Chamas',type:'gear',kind:'Efeito',price:800,rarity:'Épico',icon:'🔥'},
  {id:'efeito_gelo',name:'Efeito Gelo',type:'gear',kind:'Efeito',price:600,rarity:'Raro',icon:'❄️'},
  {id:'fundo_vestiario',name:'Plano de Fundo Vestiário',type:'frame',kind:'Plano de fundo',price:500,rarity:'Épico',icon:'🖼️'}
 ];
 function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
 function uid(){let v=localStorage.getItem('ms_uid');if(!v){v='u_'+Date.now().toString(36)+Math.random().toString(36).slice(2,9);localStorage.setItem('ms_uid',v)}return v}
 const backend=()=>localStorage.getItem('ms_beta_backend')||'https://matchscope-kjf9.onrender.com';
 function inject(){const root=document.getElementById('msProgScroll');if(!root||root.querySelector('.ms-cosmetics'))return;const sec=document.createElement('div');sec.className='ms-section ms-cosmetics';sec.innerHTML='<div class="ms-section-title">Mais cosméticos ✨</div><p class="ms-cosmetics-note">Personalize seu jogador com itens exclusivos do MatchScore.</p><div class="ms-cosmetic-grid">'+EXTRA.map(i=>'<div class="ms-cosmetic"><span class="ms-cosmetic-rarity">'+esc(i.rarity)+'</span><div class="ms-cosmetic-art">'+i.icon+'</div><div class="ms-cosmetic-name">'+esc(i.name)+'</div><div class="ms-cosmetic-kind">'+esc(i.kind)+'</div><div class="ms-cosmetic-price">🪙 '+i.price+'</div><button type="button" class="ms-cosmetic-buy" data-ms-cosmetic="'+esc(i.id)+'">Comprar</button></div>').join('')+'</div>';root.appendChild(sec);sec.querySelectorAll('[data-ms-cosmetic]').forEach(b=>b.addEventListener('click',async()=>{b.disabled=true;const old=b.textContent;b.textContent='Comprando...';try{const r=await fetch(backend()+'/store/buy/'+encodeURIComponent(uid()),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({itemId:b.dataset.msCosmetic})});if(r.ok||r.status===409){b.textContent='Adquirido';b.classList.add('ms-cosmetic-owned')}else{b.textContent=r.status===402?'MatchCoins insuficientes':'Indisponível';setTimeout(()=>{b.disabled=false;b.textContent=old},1600)}}catch(e){b.disabled=false;b.textContent=old}}))}
 const obs=new MutationObserver(()=>inject());function start(){const root=document.getElementById('msProgScroll');if(root){obs.observe(root,{childList:true,subtree:false});inject()}else setTimeout(start,400)}start();
})();
'''
(www/'beta-cosmetics.js').write_text(js,encoding='utf-8')

html=index.read_text(encoding='utf-8')
if 'beta-cosmetics.css' not in html:
    html=html.replace('</head>','<link rel="stylesheet" href="beta-cosmetics.css?v=1"></head>')
if 'beta-cosmetics.js' not in html:
    html=html.replace('</body>','<script src="beta-cosmetics.js?v=1"></script></body>')
index.write_text(html,encoding='utf-8')
print('Loja visual de cosmeticos MatchScore aplicada.')
