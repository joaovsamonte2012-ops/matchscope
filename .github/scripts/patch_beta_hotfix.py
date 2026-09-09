import os
import re
import shutil
from pathlib import Path

android_dir = Path(os.environ["ANDROID_DIR"])
www = android_dir / "app/src/main/assets/www"
index = www / "index.html"
if not index.exists():
    raise SystemExit("ERRO HOTFIX: index.html nao encontrado")

# -----------------------------------------------------------------------------
# 1) Assets visuais reais do RPG (os mockups aprovados anteriormente)
# -----------------------------------------------------------------------------
repo_root = Path(os.environ.get("GITHUB_WORKSPACE", ".")).resolve()
assets_src = repo_root / ".github/assets"
assets_dst = www / "assets"
assets_dst.mkdir(parents=True, exist_ok=True)
visual_assets = {
    "matchscore-rpg-hero.jpg": "matchscore-rpg-hero.jpg",
    "matchscore-rpg-progression.jpg": "matchscore-rpg-progression.jpg",
    "matchscore-rpg-catalog.jpg": "matchscore-rpg-catalog.jpg",
}
for src_name, dst_name in visual_assets.items():
    src = assets_src / src_name
    if not src.exists():
        raise SystemExit(f"ERRO HOTFIX: asset ausente: {src}")
    shutil.copy2(src, assets_dst / dst_name)

# -----------------------------------------------------------------------------
# Helpers para editar metodos Java sem depender de formatacao especifica
# -----------------------------------------------------------------------------
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
            if ch in ('"', "'"):
                quote = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i + 1
        i += 1
    return -1


def replace_java_method(text: str, signature_regex: str, replacement: str):
    m = re.search(signature_regex, text, flags=re.M)
    if not m:
        return text, False
    open_pos = text.find("{", m.start(), m.end() + 1)
    if open_pos < 0:
        return text, False
    end = brace_end(text, open_pos)
    if end < 0:
        return text, False
    return text[:m.start()] + replacement + text[end:], True

# -----------------------------------------------------------------------------
# 2) Corrige a ponte da API: hasApiKey precisa enxergar a chave do BuildConfig
#    (patch_v4 ja faz getPreferences() usar BuildConfig.API_FOOTBALL_KEY)
# -----------------------------------------------------------------------------
java_files = list((android_dir / "app/src/main").rglob("*.java"))
activity = None
for f in java_files:
    text = f.read_text(encoding="utf-8", errors="ignore")
    if "class MainActivity" in text and "WebView" in text and "addJavascriptInterface" in text:
        activity = f
        break
if activity is None:
    raise SystemExit("ERRO HOTFIX: MainActivity do WebView nao encontrada")

java = activity.read_text(encoding="utf-8")

java, api_fixed = replace_java_method(
    java,
    r"public\s+boolean\s+hasApiKey\s*\(\s*\)\s*\{",
    '''public boolean hasApiKey() {
        String key = getPreferences();
        return key != null && !key.trim().isEmpty();
    }''',
)
if not api_fixed:
    raise SystemExit("ERRO HOTFIX: metodo hasApiKey() nao encontrado")

# Se existir, a mascara tambem deve refletir a chave embutida e nao apenas SharedPreferences.
java, _ = replace_java_method(
    java,
    r"public\s+String\s+getMaskedApiKey\s*\(\s*\)\s*\{",
    '''public String getMaskedApiKey() {
        String key = getPreferences();
        if (key == null || key.trim().isEmpty()) return "";
        key = key.trim();
        if (key.length() <= 8) return "••••••••";
        return key.substring(0, 4) + "••••••••" + key.substring(key.length() - 4);
    }''',
)

# -----------------------------------------------------------------------------
# 3) Botao Voltar Android: fecha painel/menu primeiro, volta de rota depois,
#    e so sai do app com dois toques consecutivos na tela inicial.
# -----------------------------------------------------------------------------
bridge_match = re.search(r"(\w+)\.addJavascriptInterface\s*\(", java)
if not bridge_match:
    raise SystemExit("ERRO HOTFIX: variavel WebView nao localizada")
webview_var = bridge_match.group(1)

if "MATCHSCORE_BACK_BIND" not in java:
    line_end = java.find("\n", bridge_match.end())
    if line_end < 0:
        raise SystemExit("ERRO HOTFIX: nao foi possivel ligar WebView ao Back")
    bind = f"        this.msBackWebView = {webview_var}; // MATCHSCORE_BACK_BIND\n"
    java = java[:line_end + 1] + bind + java[line_end + 1:]

back_method = '''@Override
    public void onBackPressed() {
        if (msBackWebView == null) {
            super.onBackPressed();
            return;
        }
        msBackWebView.evaluateJavascript(
                "(function(){try{return !!(window.MatchScoreBack&&window.MatchScoreBack());}catch(e){return false;}})()",
                value -> {
                    if (!"true".equals(value)) msBackFallback();
                }
        );
    }'''

# Remove uma implementacao antiga de onBackPressed se houver, preservando o @Override
# quando ele estiver imediatamente antes do metodo.
m_back = re.search(r"(?:@Override\s*)?public\s+void\s+onBackPressed\s*\(\s*\)\s*\{", java, flags=re.M)
if m_back:
    open_pos = java.find("{", m_back.start(), m_back.end() + 1)
    end = brace_end(java, open_pos)
    if end < 0:
        raise SystemExit("ERRO HOTFIX: onBackPressed antigo incompleto")
    java = java[:m_back.start()] + back_method + java[end:]
    has_back_override = True
else:
    has_back_override = False

if "MATCHSCORE_BACK_HELPERS" not in java:
    last = java.rfind("}")
    if last < 0:
        raise SystemExit("ERRO HOTFIX: classe MainActivity invalida")
    helpers = '''

    // MATCHSCORE_BACK_HELPERS
    private android.webkit.WebView msBackWebView;
    private long msLastBackMs = 0L;

    private void msBackFallback() {
        if (msBackWebView != null && msBackWebView.canGoBack()) {
            msBackWebView.goBack();
            return;
        }
        long now = System.currentTimeMillis();
        if (now - msLastBackMs < 1800L) {
            super.onBackPressed();
            return;
        }
        msLastBackMs = now;
        android.widget.Toast.makeText(this, "Pressione voltar novamente para sair", android.widget.Toast.LENGTH_SHORT).show();
    }
'''
    if not has_back_override:
        helpers += "\n    " + back_method.replace("\n", "\n    ") + "\n"
    java = java[:last] + helpers + java[last:]

activity.write_text(java, encoding="utf-8")

# -----------------------------------------------------------------------------
# 4) JS/CSS: back-aware overlays + galeria visual dentro de Meu jogador
# -----------------------------------------------------------------------------
css = r'''
.ms-visuals{margin:0 0 14px;padding:12px;border-radius:18px;background:linear-gradient(145deg,#101b30,#0b1426);border:1px solid #ffffff18;box-shadow:0 12px 28px #0005}.ms-visuals-title{font-size:15px;font-weight:1000;color:#fff;margin-bottom:3px}.ms-visuals-sub{font-size:10px;color:#9facbf;margin-bottom:10px}.ms-visual-hero{position:relative;overflow:hidden;border-radius:15px;border:1px solid #f3c96955;background:#070d18;cursor:pointer}.ms-visual-hero img{display:block;width:100%;height:auto;max-height:430px;object-fit:cover}.ms-visual-badge{position:absolute;left:9px;bottom:9px;padding:6px 8px;border-radius:9px;background:#080d18dd;border:1px solid #f3c96966;color:#f7dc8d;font-size:9px;font-weight:1000}.ms-visual-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px}.ms-visual-card{overflow:hidden;border-radius:13px;border:1px solid #ffffff18;background:#ffffff08;cursor:pointer}.ms-visual-card img{display:block;width:100%;aspect-ratio:1.45/1;object-fit:cover}.ms-visual-card span{display:block;padding:7px 8px;font-size:9px;font-weight:900;color:#e7edf6}.ms-visual-modal{position:fixed;inset:0;z-index:99999;display:none;align-items:center;justify-content:center;padding:18px;background:#020711ee;backdrop-filter:blur(8px)}.ms-visual-modal.open{display:flex}.ms-visual-modal-inner{width:min(680px,100%);max-height:92vh;overflow:auto;border-radius:18px;background:#0c1424;border:1px solid #ffffff22;box-shadow:0 20px 60px #000a}.ms-visual-modal img{display:block;width:100%;height:auto}.ms-visual-modal-top{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 12px;color:#fff;font-size:11px;font-weight:900}.ms-visual-modal-close{border:0;border-radius:9px;background:#ffffff14;color:#fff;padding:7px 10px;font-weight:900}.ms-api-fixed-note{display:none}@media(max-width:380px){.ms-visual-grid{grid-template-columns:1fr}.ms-visual-hero img{max-height:none}}
'''.strip()
(www / "beta-hotfix.css").write_text(css, encoding="utf-8")

js = r'''(()=>{
'use strict';
const byId=id=>document.getElementById(id);
function closeClass(id){const e=byId(id);if(e&&e.classList.contains('open')){e.classList.remove('open');return true}return false}
function closeProfileMenu(){const menu=byId('msProfileMenu'),back=byId('msProfileMenuBackdrop'),trigger=byId('msProfileMenuTrigger');if(menu&&menu.classList.contains('open')){menu.classList.remove('open');back&&back.classList.remove('open');trigger&&trigger.setAttribute('aria-expanded','false');return true}return false}
window.MatchScoreBack=function(){
  if(closeClass('msVisualModal'))return true;
  if(closeProfileMenu())return true;
  if(closeClass('msAccount'))return true;
  if(closeClass('msProg'))return true;
  if(closeClass('msChatPanel'))return true;
  return false;
};
function ensureModal(){let m=byId('msVisualModal');if(m)return m;m=document.createElement('div');m.id='msVisualModal';m.className='ms-visual-modal';m.innerHTML='<div class="ms-visual-modal-inner"><div class="ms-visual-modal-top"><span id="msVisualModalTitle">MatchScore RPG</span><button class="ms-visual-modal-close" type="button">Fechar</button></div><img id="msVisualModalImg" alt="Visual MatchScore RPG"></div>';document.body.appendChild(m);m.querySelector('.ms-visual-modal-close').onclick=()=>m.classList.remove('open');m.addEventListener('click',e=>{if(e.target===m)m.classList.remove('open')});return m}
function openVisual(src,title){const m=ensureModal(),img=byId('msVisualModalImg'),t=byId('msVisualModalTitle');if(img)img.src=src;if(t)t.textContent=title||'MatchScore RPG';m.classList.add('open')}
function injectVisuals(){const root=byId('msProgScroll');if(!root||byId('msVisualPanels'))return;const sec=document.createElement('section');sec.id='msVisualPanels';sec.className='ms-visuals';sec.innerHTML=`<div class="ms-visuals-title">🛡️ Arsenal & evolução</div><div class="ms-visuals-sub">Os visuais das armaduras e painéis agora fazem parte do aplicativo.</div><div class="ms-visual-hero" data-ms-visual="assets/matchscore-rpg-hero.jpg" data-title="Armadura lendária equipada"><img src="assets/matchscore-rpg-hero.jpg" alt="Armadura lendária MatchScore"><div class="ms-visual-badge">ARMADURA LENDÁRIA · VER</div></div><div class="ms-visual-grid"><div class="ms-visual-card" data-ms-visual="assets/matchscore-rpg-progression.jpg" data-title="Progressão do jogador"><img src="assets/matchscore-rpg-progression.jpg" alt="Painel de progressão MatchScore"><span>Progressão · Amador → Lenda</span></div><div class="ms-visual-card" data-ms-visual="assets/matchscore-rpg-catalog.jpg" data-title="Catálogo de cosméticos"><img src="assets/matchscore-rpg-catalog.jpg" alt="Catálogo de cosméticos MatchScore"><span>Catálogo · Itens RPG</span></div></div>`;const rpg=root.querySelector('.ms-rpgx');if(rpg)root.insertBefore(sec,rpg);else root.prepend(sec);sec.querySelectorAll('[data-ms-visual]').forEach(e=>e.addEventListener('click',()=>openVisual(e.dataset.msVisual,e.dataset.title)))}
function startVisuals(){const root=byId('msProgScroll');if(!root){setTimeout(startVisuals,350);return}let queued=false;const schedule=()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;injectVisuals()})};new MutationObserver(schedule).observe(root,{childList:true});injectVisuals()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',startVisuals);else startVisuals();
})();'''
(www / "beta-hotfix.js").write_text(js, encoding="utf-8")

html = index.read_text(encoding="utf-8")
if "beta-hotfix.css" not in html:
    html = html.replace("</head>", '<link rel="stylesheet" href="beta-hotfix.css?v=1"></head>')
if "beta-hotfix.js" not in html:
    html = html.replace("</body>", '<script src="beta-hotfix.js?v=1"></script></body>')
index.write_text(html, encoding="utf-8")

# Validacoes do build: se algo essencial nao entrou, falha aqui e nao gera APK quebrado.
java_check = activity.read_text(encoding="utf-8")
html_check = index.read_text(encoding="utf-8")
checks = {
    "API hasApiKey via getPreferences": "public boolean hasApiKey()" in java_check and "String key = getPreferences();" in java_check,
    "Back Android": "MATCHSCORE_BACK_HELPERS" in java_check and "window.MatchScoreBack" in java_check,
    "Galeria JS": "beta-hotfix.js" in html_check,
    "Galeria CSS": "beta-hotfix.css" in html_check,
    "Imagem armadura": (assets_dst / "matchscore-rpg-hero.jpg").exists(),
    "Imagem progressao": (assets_dst / "matchscore-rpg-progression.jpg").exists(),
    "Imagem catalogo": (assets_dst / "matchscore-rpg-catalog.jpg").exists(),
}
for name, ok in checks.items():
    print(f"HOTFIX {name}: {'OK' if ok else 'FALHOU'}")
    if not ok:
        raise SystemExit(f"ERRO HOTFIX: validacao falhou: {name}")
print("Hotfix API + voltar + visuais RPG aplicado com sucesso.")
