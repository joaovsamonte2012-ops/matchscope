import os
import re
from pathlib import Path

android_dir = Path(os.environ["ANDROID_DIR"])
app_js = android_dir / "app/src/main/assets/www/app.js"
if not app_js.exists():
    raise SystemExit(f"ERRO: arquivo nao encontrado: {app_js}")


def brace_end(text: str, open_pos: int) -> int:
    depth = 0
    quote = None
    escape = False
    i = open_pos
    while i < len(text):
        ch = text[i]
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
        else:
            if ch in ('"', "'", "`"):
                quote = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i + 1
        i += 1
    return -1


js = app_js.read_text(encoding="utf-8")

# Localiza automaticamente a aba de escalacoes pelo uso de raw.lineups.
needle_positions = [
    js.find("d.raw?.lineups"),
    js.find("d.raw.lineups"),
    js.find("raw?.lineups"),
    js.find("raw.lineups"),
]
needle_positions = [p for p in needle_positions if p >= 0]
if not needle_positions:
    idx = js.find("lineup")
    print("CONTEXTO LINEUP:\n" + (js[max(0, idx - 800):idx + 1800] if idx >= 0 else js[:2200]))
    raise SystemExit("ERRO: dados de escalacao nao encontrados em app.js")

needle = min(needle_positions)

# Nao depende mais de espacos ou do nome exato da aba. Procura o bloco if que
# realmente envolve o uso de raw.lineups e preserva a condicao original.
candidates = []
for match in re.finditer(r"\bif\s*\(", js[:needle]):
    pos = match.start()
    open_candidate = js.find("{", pos, needle + 1)
    if open_candidate < 0:
        continue
    end_candidate = brace_end(js, open_candidate)
    if end_candidate <= needle:
        continue
    header = js[pos:open_candidate]
    if len(header) > 500:
        continue
    score = 0
    low = header.lower()
    if "tab" in low:
        score += 10
    if "lineup" in low or "escala" in low:
        score += 20
    candidates.append((score, pos, open_candidate, end_candidate, header))

if not candidates:
    print("CONTEXTO LINEUP:\n" + js[max(0, needle - 1200):needle + 1800])
    raise SystemExit("ERRO: bloco da aba de escalacoes nao encontrado")

# Prioriza condicoes que falam de lineup/tab; em empate, usa a mais proxima.
candidates.sort(key=lambda x: (x[0], x[1]))
score, start, open_pos, end, original_header = candidates[-1]
if score == 0:
    print("AVISO: aba localizada por bloco envolvente, sem marcador de tab no cabecalho.")

new_lineup = r'''if(state.tab==='lineup'||state.tab==='lineups'){
      const lineups=d.raw?.lineups||[];
      if(d.loaded&&!lineups.length)return `<section class="card" style="padding:14px"><div class="section-title">Escalações</div><div class="divider"></div><div class="empty-copy">A escalação oficial ainda não foi disponibilizada para esta partida.</div></section>`;

      const home=lineups[0]||{};
      const away=lineups[1]||{};
      const starters=(team)=>(team?.startXI||team?.startingXI||[]).map(x=>x?.player||x).filter(Boolean).slice(0,11);
      const subs=(team)=>(team?.substitutes||team?.bench||[]).map(x=>x?.player||x).filter(Boolean);
      const hp=starters(home),ap=starters(away);

      const posCode=(p)=>String(p?.pos||p?.position||'').toUpperCase();
      const fallbackGrid=(players)=>{
        const groups={G:[],D:[],M:[],F:[]};
        players.forEach((p,i)=>{
          const c=posCode(p);
          const k=c.startsWith('G')?'G':c.startsWith('D')?'D':c.startsWith('M')?'M':c.startsWith('A')||c.startsWith('F')?'F':(i===0?'G':'M');
          groups[k].push(p);
        });
        const rows=[groups.G,groups.D,groups.M,groups.F].filter(r=>r.length);
        const map=new Map();
        rows.forEach((row,ri)=>row.forEach((p,ci)=>map.set(p,`${ri+1}:${ci+1}`)));
        return map;
      };

      const buildPositions=(players,side)=>{
        const fallback=fallbackGrid(players);
        const parsed=players.map(p=>{
          const raw=String(p?.grid||p?.formation_field||fallback.get(p)||'');
          const m=raw.match(/^(\d+):(\d+)$/);
          return {p,row:m?Number(m[1]):1,col:m?Number(m[2]):1};
        });
        const maxRow=Math.max(2,...parsed.map(x=>x.row));
        const cols={};
        parsed.forEach(x=>cols[x.row]=Math.max(cols[x.row]||0,x.col));
        return parsed.map(x=>{
          let left=(x.col/(Math.max(1,cols[x.row])+1))*100;
          if(side==='away')left=100-left;
          const progress=(x.row-1)/(maxRow-1);
          const top=side==='home'?(94-progress*38):(6+progress*38);
          return {...x,left,top};
        });
      };

      const playerNode=(x,side)=>{
        const p=x.p||{};
        const number=p.number??p.jersey_number??'';
        const name=p.name||p.player_name||'Jogador';
        return `<div class="ms-player ${side}" style="left:${x.left}%;top:${x.top}%"><div class="ms-shirt">${esc(String(number||'•'))}</div><div class="ms-player-name">${esc(name)}</div></div>`;
      };

      const homePos=buildPositions(hp,'home');
      const awayPos=buildPositions(ap,'away');
      const homeName=home?.team?.name||d.home||'Casa';
      const awayName=away?.team?.name||d.away||'Fora';
      const homeFormation=home?.formation||'';
      const awayFormation=away?.formation||'';

      const renderSubs=(team,label)=>{
        const list=subs(team);
        if(!list.length)return '';
        return `<div class="ms-bench"><div class="ms-bench-title">${esc(label)}</div>${list.map(p=>`<div class="ms-bench-player"><span>${esc(String(p.number??p.jersey_number??'—'))}</span><b>${esc(p.name||p.player_name||'Jogador')}</b><small>${esc(p.pos||p.position||'')}</small></div>`).join('')}</div>`;
      };

      return `<section class="card ms-lineup-card">
        <style>
          .ms-lineup-card{padding:14px;overflow:hidden}.ms-lineup-head{display:flex;justify-content:space-between;align-items:center;gap:8px;margin:2px 0 12px;font-size:12px}.ms-lineup-head b{font-size:13px}.ms-formation{opacity:.72;font-weight:700}
          .ms-pitch{position:relative;width:100%;height:620px;max-height:72vh;min-height:520px;border-radius:14px;overflow:hidden;background:repeating-linear-gradient(0deg,#348653 0,#348653 62px,#3b905a 62px,#3b905a 124px);border:2px solid rgba(255,255,255,.72);box-shadow:inset 0 0 0 2px rgba(0,0,0,.08)}
          .ms-pitch:before{content:'';position:absolute;left:0;right:0;top:50%;border-top:2px solid rgba(255,255,255,.72)}.ms-center{position:absolute;left:50%;top:50%;width:96px;height:96px;border:2px solid rgba(255,255,255,.72);border-radius:50%;transform:translate(-50%,-50%)}.ms-center:after{content:'';position:absolute;width:6px;height:6px;background:#fff;border-radius:50%;left:50%;top:50%;transform:translate(-50%,-50%)}
          .ms-box{position:absolute;left:22%;width:56%;height:92px;border:2px solid rgba(255,255,255,.72)}.ms-box.top{top:-2px}.ms-box.bottom{bottom:-2px}.ms-goal{position:absolute;left:38%;width:24%;height:18px;border:2px solid rgba(255,255,255,.72)}.ms-goal.top{top:-2px}.ms-goal.bottom{bottom:-2px}
          .ms-player{position:absolute;transform:translate(-50%,-50%);width:74px;text-align:center;z-index:3}.ms-shirt{margin:auto;width:29px;height:29px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:900;color:#fff;border:2px solid rgba(255,255,255,.92);box-shadow:0 2px 5px rgba(0,0,0,.3)}.ms-player.home .ms-shirt{background:#1769aa}.ms-player.away .ms-shirt{background:#242424}.ms-player-name{margin-top:3px;color:#fff;font-size:10px;line-height:11px;font-weight:800;text-shadow:0 1px 3px #000,0 1px 2px #000;white-space:normal;overflow:hidden;max-height:23px}
          .ms-benches{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}.ms-bench{border:1px solid rgba(128,128,128,.2);border-radius:12px;padding:10px}.ms-bench-title{font-weight:800;margin-bottom:8px}.ms-bench-player{display:grid;grid-template-columns:24px 1fr auto;gap:5px;align-items:center;padding:6px 0;border-top:1px solid rgba(128,128,128,.12);font-size:11px}.ms-bench-player small{opacity:.65}
          @media(max-width:390px){.ms-pitch{height:550px}.ms-player{width:66px}.ms-player-name{font-size:9px}.ms-benches{grid-template-columns:1fr}}
        </style>
        <div class="section-title">Escalações</div>
        <div class="ms-lineup-head"><span><b>${esc(awayName)}</b> <span class="ms-formation">${esc(awayFormation)}</span></span><span><b>${esc(homeName)}</b> <span class="ms-formation">${esc(homeFormation)}</span></span></div>
        <div class="ms-pitch"><div class="ms-center"></div><div class="ms-box top"></div><div class="ms-box bottom"></div><div class="ms-goal top"></div><div class="ms-goal bottom"></div>${awayPos.map(x=>playerNode(x,'away')).join('')}${homePos.map(x=>playerNode(x,'home')).join('')}</div>
        <div class="ms-benches">${renderSubs(away,`${awayName} — reservas`)}${renderSubs(home,`${homeName} — reservas`)}</div>
      </section>`;
    }'''

# Mantem exatamente a condicao original da aba encontrada no app base.
new_lineup = js[start:open_pos + 1] + new_lineup[new_lineup.find("{") + 1:]
js = js[:start] + new_lineup + js[end:]
app_js.write_text(js, encoding="utf-8")

check = app_js.read_text(encoding="utf-8")
required = ["ms-pitch", "buildPositions", "formation_field", "Escalações"]
for item in required:
    if item not in check:
        raise SystemExit(f"ERRO: validacao do campinho falhou: {item}")

print("Campinho tatico de escalacoes aplicado com sucesso.")
