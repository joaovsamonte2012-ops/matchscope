import os
from pathlib import Path

www=Path(os.environ['ANDROID_DIR'])/'app/src/main/assets/www'
jsf=www/'v28.js'; cssf=www/'v28.css'
js=jsf.read_text(encoding='utf-8'); css=cssf.read_text(encoding='utf-8')

# Botoes reais e marcadores clicaveis.
js=js.replace('<button class="on" data-tab="home">','<button type="button" class="on" data-tab="home">')
js=js.replace('<button data-tab="player">','<button type="button" data-tab="player">')
js=js.replace('<button data-tab="items">','<button type="button" data-tab="items">')
js=js.replace('<button data-tab="rank">','<button type="button" data-tab="rank">')
js=js.replace('<button class="v28-equip ${state.equipped===id?', '<button type="button" class="v28-equip ${state.equipped===id?')

# Adiciona sheet de detalhes dentro do overlay.
needle='<div id="v28Toast" class="v28-toast"></div></div>`);'
replacement='<div id="v28Toast" class="v28-toast"></div><div id="v28Sheet" class="v28-sheet"><div class="v28-sheet-card"><button type="button" class="v28-sheet-close" data-close-sheet>×</button><div id="v28SheetBody"></div></div></div></div>`);'
if needle in js: js=js.replace(needle,replacement,1)

# Estado guarda partidas para abrir detalhes.
js=js.replace("const state={tab:'home',frame:0,equipped:'armor'};", "const state={tab:'home',frame:0,equipped:'armor',matches:[]};")

# Troca binding frágil por delegação única de eventos no overlay.
start=js.find('function bind(){')
end=js.find('function go(',start)
if start<0 or end<0: raise SystemExit('ERRO: bind/go nao encontrados')
new_bind=r'''function bind(){
 const root=$('#msV28');
 if(!root||root.dataset.touchBound==='1')return;
 root.dataset.touchBound='1';
 root.addEventListener('click',e=>{
   const tab=e.target.closest('[data-tab]');
   if(tab&&root.contains(tab)){e.preventDefault();e.stopPropagation();go(tab.dataset.tab,true);return;}
   const equip=e.target.closest('[data-e]');
   if(equip&&root.contains(equip)){e.preventDefault();e.stopPropagation();state.equipped=equip.dataset.e;renderItems();toast('Item equipado');return;}
   const match=e.target.closest('[data-fixture-index]');
   if(match&&root.contains(match)){e.preventDefault();e.stopPropagation();openMatch(Number(match.dataset.fixtureIndex));return;}
   const close=e.target.closest('[data-close-sheet]');
   if(close&&root.contains(close)){e.preventDefault();e.stopPropagation();closeSheet();}
 },true);
 window.addEventListener('popstate',e=>{const t=e.state?.v28||'home';go(t,false)});
}
function openMatch(i){
 const m=state.matches[i];if(!m)return;
 const h=m.teams?.home||{},a=m.teams?.away||{};
 const gh=m.goals?.home,ga=m.goals?.away;
 const when=m.fixture?.date?new Date(m.fixture.date).toLocaleString('pt-BR',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}):'Horário não informado';
 const status=m.fixture?.status?.long||m.fixture?.status?.short||'';
 $('#v28SheetBody').innerHTML=`<div class="v28-detail-league">${esc(m.league?.name||'Partida')}</div><div class="v28-detail-teams"><div>${h.logo?`<img src="${esc(h.logo)}">`:''}<b>${esc(h.name||'Casa')}</b></div><strong>${gh??'-'} × ${ga??'-'}</strong><div>${a.logo?`<img src="${esc(a.logo)}">`:''}<b>${esc(a.name||'Fora')}</b></div></div><div class="v28-detail-meta">${esc(when)}${status?' · '+esc(status):''}</div>`;
 $('#v28Sheet').classList.add('on');
}
function closeSheet(){const s=$('#v28Sheet');if(s)s.classList.remove('on');}
'''
js=js[:start]+new_bind+js[end:]

# Remove handlers individuais dos itens; a delegação acima cuida de tudo.
old="$$('[data-e]',root).forEach(b=>b.onclick=()=>{state.equipped=b.dataset.e;renderItems();toast('Item equipado');});"
js=js.replace(old,'')

# Guarda resposta e torna cada partida clicável.
js=js.replace("const arr=Array.isArray(j?.response)?j.response:[];", "const arr=Array.isArray(j?.response)?j.response:[];state.matches=arr;")
js=js.replace("root.innerHTML=arr.slice(0,40).map(m=>{", "root.innerHTML=arr.slice(0,40).map((m,i)=>{")
js=js.replace('<div class="v28-card v28-match">${h.logo?', '<div class="v28-card v28-match" data-fixture-index="${i}" role="button" tabindex="0">${h.logo?')

css += r'''
/* V28 touch hotfix */
.v28-nav{position:relative;z-index:40}.v28-nav button,.v28-equip,.v28-match,.v28-sheet-close{pointer-events:auto;touch-action:manipulation;-webkit-tap-highlight-color:transparent;cursor:pointer;user-select:none}.v28-nav button,.v28-equip{min-height:44px}.v28-match{position:relative;z-index:1}.v28-sheet{display:none;position:absolute;inset:0;z-index:100;background:#02070dbb;align-items:flex-end;padding:16px 14px calc(16px + var(--safe-b));touch-action:manipulation}.v28-sheet.on{display:flex}.v28-sheet-card{position:relative;width:100%;max-width:730px;margin:0 auto;border:1px solid var(--v28-line);border-radius:24px;background:#0b1928;padding:22px 16px 18px;box-shadow:0 -18px 60px #000a}.v28-sheet-close{position:absolute;right:10px;top:8px;width:44px;height:44px;border:0;border-radius:14px;background:#172c41;color:white;font-size:28px}.v28-detail-league{text-align:center;color:var(--v28-mut);font-weight:800;padding:4px 44px 18px}.v28-detail-teams{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:12px;text-align:center}.v28-detail-teams img{display:block;width:58px;height:58px;object-fit:contain;margin:0 auto 8px}.v28-detail-teams b{display:block;font-size:13px}.v28-detail-teams strong{font-size:24px}.v28-detail-meta{text-align:center;color:var(--v28-mut);margin-top:18px;font-size:12px}
'''

for mark in ["closest('[data-tab]')",'data-fixture-index','openMatch(Number','touchBound']:
    if mark not in js: raise SystemExit('ERRO: hotfix ausente: '+mark)
if 'touch-action:manipulation' not in css: raise SystemExit('ERRO: CSS touch ausente')
jsf.write_text(js,encoding='utf-8');cssf.write_text(css,encoding='utf-8')
print('Hotfix de toque V28 aplicado: navegação, equipamentos e partidas clicáveis.')
