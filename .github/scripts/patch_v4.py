import os
import re
from pathlib import Path

android_dir = Path(os.environ["ANDROID_DIR"])
main_activity = android_dir / "app/src/main/java/com/matchscope/app/MainActivity.java"
app_gradle = android_dir / "app/build.gradle.kts"
manifest = android_dir / "app/src/main/AndroidManifest.xml"
app_js = android_dir / "app/src/main/assets/www/app.js"

for p in (main_activity, app_gradle, manifest, app_js):
    if not p.exists():
        raise SystemExit(f"ERRO: arquivo nao encontrado: {p}")


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


# API key do Secret no BuildConfig
gradle = app_gradle.read_text(encoding="utf-8")
if "API_FOOTBALL_KEY" not in gradle:
    gradle += r'''

android {
    buildFeatures {
        buildConfig = true
    }
    defaultConfig {
        val apiFootballKey = System.getenv("API_FOOTBALL_KEY") ?: ""
        buildConfigField("String", "API_FOOTBALL_KEY", "\"${apiFootballKey}\"")
    }
}
'''
    app_gradle.write_text(gradle, encoding="utf-8")

# Permissao INTERNET
m = manifest.read_text(encoding="utf-8")
if "android.permission.INTERNET" not in m:
    pos = m.find(">")
    if pos < 0:
        raise SystemExit("ERRO: AndroidManifest invalido")
    m = m[: pos + 1] + '\n    <uses-permission android:name="android.permission.INTERNET" />' + m[pos + 1 :]
    manifest.write_text(m, encoding="utf-8")

# MainActivity: chave salva no aparelho ou chave embutida no build
java = main_activity.read_text(encoding="utf-8")
if "BuildConfig.API_FOOTBALL_KEY" not in java:
    mm = re.search(r"private\s+String\s+getPreferences\s*\(\s*\)\s*\{", java)
    if not mm:
        raise SystemExit("ERRO: metodo getPreferences() nao encontrado")
    open_pos = java.find("{", mm.start())
    end = brace_end(java, open_pos)
    if end < 0:
        raise SystemExit("ERRO: getPreferences() incompleto")
    replacement = '''private String getPreferences() {
        String saved = getSharedPreferences(PREFS, MODE_PRIVATE).getString(API_KEY, "");
        if (saved != null && !saved.trim().isEmpty()) return saved.trim();
        String builtIn = BuildConfig.API_FOOTBALL_KEY;
        return builtIn == null ? "" : builtIn.trim();
    }'''
    java = java[: mm.start()] + replacement + java[end:]
    main_activity.write_text(java, encoding="utf-8")

js = app_js.read_text(encoding="utf-8")

# Adiciona chamadas dedicadas de estatisticas, eventos e escalacoes.
if "/fixtures/statistics?fixture=" not in js:
    pm = re.search(
        r"const\s*\[\s*d\s*,\s*h\s*,\s*a\s*\]\s*=\s*await\s+Promise\.all\s*\(\s*\[",
        js,
    )
    if not pm:
        # Gera um trecho util no log para diagnostico, sem abortar silenciosamente.
        idx = js.find("Promise.all")
        context = js[max(0, idx - 500) : idx + 1200] if idx >= 0 else js[:1500]
        print("CONTEXTO APP.JS:\n" + context)
        raise SystemExit("ERRO: Promise.all de detalhes nao encontrado")

    header = js[pm.start() : pm.end()]
    header = re.sub(
        r"const\s*\[\s*d\s*,\s*h\s*,\s*a\s*\]",
        "const [d,h,a,stats,events,lineups]",
        header,
        count=1,
    )
    js = js[: pm.start()] + header + js[pm.end() :]

    pm2 = re.search(
        r"const\s*\[\s*d\s*,\s*h\s*,\s*a\s*,\s*stats\s*,\s*events\s*,\s*lineups\s*\]\s*=\s*await\s+Promise\.all\s*\(\s*\[",
        js,
    )
    if not pm2:
        raise SystemExit("ERRO: Promise.all alterado nao localizado")

    close = js.find("]);", pm2.end())
    if close < 0:
        raise SystemExit("ERRO: fechamento Promise.all nao encontrado")

    left = js[:close].rstrip()
    if not left.endswith(","):
        left += ","
    injected = '''
        api(`/fixtures/statistics?fixture=${encodeURIComponent(id)}`).catch(()=>({response:[]})),
        api(`/fixtures/events?fixture=${encodeURIComponent(id)}`).catch(()=>({response:[]})),
        api(`/fixtures/lineups?fixture=${encodeURIComponent(id)}`).catch(()=>({response:[]}))
      '''
    js = left + injected + js[close:]

    # Encontra parseFixture(raw) que vem depois deste Promise.all.
    parsed = re.search(r"const\s+parsed\s*=\s*parseFixture\s*\(\s*raw\s*\)\s*;", js[close:])
    if not parsed:
        idx = js.find("parseFixture", close)
        context = js[max(0, idx - 500) : idx + 1000] if idx >= 0 else js[close : close + 1500]
        print("CONTEXTO PARSE:\n" + context)
        raise SystemExit("ERRO: parseFixture(raw) nao encontrado")
    parsed_start = close + parsed.start()
    attach = '''raw.statistics=stats.response||raw.statistics||[];
      raw.events=events.response||raw.events||[];
      raw.lineups=lineups.response||raw.lineups||[];
      '''
    js = js[:parsed_start] + attach + js[parsed_start:]

# Substitui somente o bloco da aba Estatisticas por renderizacao dinamica de tudo o que a API retornar.
markers = ["if(state.tab==='stats')", 'if(state.tab==="stats")']
s = -1
for marker in markers:
    s = js.find(marker)
    if s >= 0:
        break
if s < 0:
    idx = js.find("state.tab")
    print("CONTEXTO TABS:\n" + (js[max(0, idx - 500) : idx + 1800] if idx >= 0 else js[:1800]))
    raise SystemExit("ERRO: aba de estatisticas nao encontrada")

open_pos = js.find("{", s)
end = brace_end(js, open_pos)
if end < 0:
    raise SystemExit("ERRO: bloco de estatisticas incompleto")

new_stats = '''if(state.tab==='stats'){
      const teams=d.raw?.statistics||[];
      if(d.loaded && !teams.length)return `<section class="card" style="padding:14px"><div class="section-title">Estatísticas da partida</div><div class="divider"></div><div class="empty-copy">A API-Football não disponibilizou estatísticas detalhadas para esta partida.</div></section>`;
      const homeStats=teams[0]?.statistics||[];
      const awayStats=teams[1]?.statistics||[];
      const order=[];const seen=new Set();
      [...homeStats,...awayStats].forEach(s=>{if(s?.type&&!seen.has(s.type)){seen.add(s.type);order.push(s.type)}});
      const valueFor=(arr,type)=>{const x=arr.find(s=>s?.type===type);return x?.value===null||x?.value===undefined?'—':x.value};
      const labels={'Ball Possession':'Posse de bola','Total Shots':'Finalizações','Shots on Goal':'Chutes no alvo','Shots off Goal':'Chutes para fora','Blocked Shots':'Chutes bloqueados','Shots insidebox':'Chutes dentro da área','Shots outsidebox':'Chutes fora da área','Corner Kicks':'Escanteios','Offsides':'Impedimentos','Fouls':'Faltas','Yellow Cards':'Cartões amarelos','Red Cards':'Cartões vermelhos','Goalkeeper Saves':'Defesas do goleiro','Total passes':'Passes','Passes accurate':'Passes certos','Passes %':'Precisão de passes','expected_goals':'Gols esperados (xG)','Goals Prevented':'Gols evitados'};
      const rows=order.map(type=>statRow(labels[type]||type,valueFor(homeStats,type),valueFor(awayStats,type))).join('');
      return `<section class="card" style="padding:14px"><div class="section-title">Estatísticas da partida</div>${rows||'<div class="empty-copy">Sem estatísticas disponíveis.</div>'}</section>`;
    }'''
js = js[:s] + new_stats + js[end:]
app_js.write_text(js, encoding="utf-8")

checks = {
    "BuildConfig API key": "BuildConfig.API_FOOTBALL_KEY" in main_activity.read_text(encoding="utf-8"),
    "Endpoint statistics": "/fixtures/statistics?fixture=" in js,
    "Endpoint events": "/fixtures/events?fixture=" in js,
    "Endpoint lineups": "/fixtures/lineups?fixture=" in js,
    "Stats dinamicas": "const homeStats=teams[0]?.statistics||[];" in js,
}
for name, ok in checks.items():
    print(f"{name}: {'OK' if ok else 'FALHOU'}")
    if not ok:
        raise SystemExit(f"ERRO: validacao falhou: {name}")

print("Patch V4 aplicado com sucesso.")
