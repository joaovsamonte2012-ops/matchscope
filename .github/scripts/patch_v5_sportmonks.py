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


backend_url = os.environ.get("MATCHSCOPE_API_BASE_URL", "").strip().rstrip("/")
if not backend_url.startswith("https://"):
    raise SystemExit("ERRO: MATCHSCOPE_API_BASE_URL deve começar com https://")

# BuildConfig com a URL pública do backend. O token Sportmonks NÃO vai para o APK.
gradle = app_gradle.read_text(encoding="utf-8")
if "MATCHSCOPE_API_BASE_URL" not in gradle:
    gradle += r'''

android {
    buildFeatures {
        buildConfig = true
    }
    defaultConfig {
        val matchscopeApiBaseUrl = System.getenv("MATCHSCOPE_API_BASE_URL") ?: ""
        buildConfigField("String", "MATCHSCOPE_API_BASE_URL", "\"${matchscopeApiBaseUrl}\"")
    }
}
'''
    app_gradle.write_text(gradle, encoding="utf-8")

# Permissão INTERNET
m = manifest.read_text(encoding="utf-8")
if "android.permission.INTERNET" not in m:
    pos = m.find(">")
    if pos < 0:
        raise SystemExit("ERRO: AndroidManifest invalido")
    m = m[: pos + 1] + '\n    <uses-permission android:name="android.permission.INTERNET" />' + m[pos + 1 :]
    manifest.write_text(m, encoding="utf-8")

java = main_activity.read_text(encoding="utf-8")

# Troca o host direto da API-Football pelo backend seguro do MatchScope.
if "BuildConfig.MATCHSCOPE_API_BASE_URL" not in java:
    old_urls = [
        '"https://v3.football.api-sports.io"',
        '"https://v3.football.api-sports.io/"',
    ]
    replaced = False
    for old in old_urls:
        if old in java:
            java = java.replace(old, "BuildConfig.MATCHSCOPE_API_BASE_URL", 1)
            replaced = True
            break
    if not replaced:
        java2, count = re.subn(
            r'"https://v3\.football\.api-sports\.io/?"',
            "BuildConfig.MATCHSCOPE_API_BASE_URL",
            java,
            count=1,
        )
        java = java2
        replaced = count == 1
    if not replaced:
        idx = java.find("api-sports")
        print(java[max(0, idx-500):idx+800] if idx >= 0 else java[:1800])
        raise SystemExit("ERRO: URL base antiga nao encontrada em MainActivity.java")

# O app deixa de exigir uma chave local. A credencial real fica somente no backend.
mm = re.search(r"private\s+String\s+getPreferences\s*\(\s*\)\s*\{", java)
if not mm:
    raise SystemExit("ERRO: metodo getPreferences() nao encontrado")
open_pos = java.find("{", mm.start())
end = brace_end(java, open_pos)
if end < 0:
    raise SystemExit("ERRO: getPreferences() incompleto")
replacement = '''private String getPreferences() {
        return "backend-proxy";
    }'''
java = java[: mm.start()] + replacement + java[end:]
main_activity.write_text(java, encoding="utf-8")

js = app_js.read_text(encoding="utf-8")

# Renderiza dinamicamente TODAS as estatísticas que o backend Sportmonks retornar.
markers = ["if(state.tab==='stats')", 'if(state.tab==="stats")']
s = -1
for marker in markers:
    s = js.find(marker)
    if s >= 0:
        break
if s < 0:
    idx = js.find("state.tab")
    print("CONTEXTO TABS:\n" + (js[max(0, idx - 500): idx + 1800] if idx >= 0 else js[:1800]))
    raise SystemExit("ERRO: aba de estatisticas nao encontrada")

open_pos = js.find("{", s)
end = brace_end(js, open_pos)
if end < 0:
    raise SystemExit("ERRO: bloco de estatisticas incompleto")

new_stats = '''if(state.tab==='stats'){
      const teams=d.raw?.statistics||[];
      if(d.loaded && !teams.length)return `<section class="card" style="padding:14px"><div class="section-title">Estatísticas da partida</div><div class="divider"></div><div class="empty-copy">A Sportmonks não disponibilizou estatísticas detalhadas para esta partida.</div></section>`;
      const homeStats=teams[0]?.statistics||[];
      const awayStats=teams[1]?.statistics||[];
      const order=[];const seen=new Set();
      [...homeStats,...awayStats].forEach(st=>{if(st?.type&&!seen.has(st.type)){seen.add(st.type);order.push(st.type)}});
      const valueFor=(arr,type)=>{const x=arr.find(st=>st?.type===type);return x?.value===null||x?.value===undefined?'—':x.value};
      const safeNum=(v)=>{if(v===null||v===undefined||v==='—')return null;const n=parseFloat(String(v).replace('%','').replace(',','.'));return Number.isFinite(n)?n:null};
      const renderRow=(type)=>{
        const lv=valueFor(homeStats,type),rv=valueFor(awayStats,type),ln=safeNum(lv),rn=safeNum(rv);
        if(ln!==null&&rn!==null){const pct=String(lv).includes('%')||String(rv).includes('%');return statRow(type,ln,rn,pct?'%':'');}
        return `<div class="stat"><b>${esc(lv)}</b><span>${esc(type)}</span><b>${esc(rv)}</b></div>`;
      };
      const rows=order.map(renderRow).join('');
      return `<section class="card" style="padding:14px"><div class="section-title">Estatísticas da partida</div>${rows||'<div class="empty-copy">Sem estatísticas disponíveis.</div>'}</section>`;
    }'''
js = js[:s] + new_stats + js[end:]

# Atualiza referências visíveis do provedor antigo.
js = js.replace("API-Football", "Sportmonks")
app_js.write_text(js, encoding="utf-8")

checks = {
    "Backend no BuildConfig": "BuildConfig.MATCHSCOPE_API_BASE_URL" in main_activity.read_text(encoding="utf-8"),
    "Sem chave Sportmonks no APK": "SPORTMONKS_TOKEN" not in main_activity.read_text(encoding="utf-8"),
    "Stats dinamicas": "const homeStats=teams[0]?.statistics||[];" in js,
}
for name, ok in checks.items():
    print(f"{name}: {'OK' if ok else 'FALHOU'}")
    if not ok:
        raise SystemExit(f"ERRO: validacao falhou: {name}")

print("Patch V5 Sportmonks aplicado com sucesso.")
