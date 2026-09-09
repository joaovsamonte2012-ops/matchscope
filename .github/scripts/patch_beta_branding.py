import os
import re
from pathlib import Path

android_dir = Path(os.environ["ANDROID_DIR"])
app_dir = android_dir / "app"
main_dir = app_dir / "src/main"
res_dir = main_dir / "res"
manifest = main_dir / "AndroidManifest.xml"
gradle = app_dir / "build.gradle.kts"

if not manifest.exists():
    raise SystemExit(f"ERRO: AndroidManifest nao encontrado: {manifest}")
if not gradle.exists():
    raise SystemExit(f"ERRO: build.gradle.kts nao encontrado: {gradle}")

# Nome do aplicativo
values_dir = res_dir / "values"
values_dir.mkdir(parents=True, exist_ok=True)
strings_file = values_dir / "strings.xml"
if strings_file.exists():
    strings = strings_file.read_text(encoding="utf-8")
    if re.search(r'<string\s+name=["\']app_name["\']>.*?</string>', strings, flags=re.S):
        strings = re.sub(
            r'<string\s+name=["\']app_name["\']>.*?</string>',
            '<string name="app_name">MatchScope Beta</string>',
            strings,
            count=1,
            flags=re.S,
        )
    else:
        strings = strings.replace("</resources>", '    <string name="app_name">MatchScope Beta</string>\n</resources>')
else:
    strings = '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <string name="app_name">MatchScope Beta</string>\n</resources>\n'
strings_file.write_text(strings, encoding="utf-8")

# Logo vetorial: campo de futebol estilizado + lente do MatchScope.
drawable_dir = res_dir / "drawable"
drawable_dir.mkdir(parents=True, exist_ok=True)
logo = drawable_dir / "matchscope_beta_logo.xml"
logo.write_text('''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:fillColor="#101722" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#17C873" android:pathData="M12,12h84v84h-84z"/>
    <path android:fillColor="#101722" android:pathData="M17,17h74v74h-74z"/>
    <path android:strokeColor="#17C873" android:strokeWidth="3" android:fillColor="@android:color/transparent" android:pathData="M24,25h60v58h-60zM54,25v58M24,54h60"/>
    <path android:strokeColor="#17C873" android:strokeWidth="3" android:fillColor="@android:color/transparent" android:pathData="M54,45a9,9 0,1 0,0 18a9,9 0,1 0,0 -18"/>
    <path android:fillColor="#F5F7FA" android:pathData="M70,64a13,13 0,1 0,-9.19,-3.81A13,13 0,0 0,70,64zM70,59a8,8 0,1 1,5.66,-2.34A8,8 0,0 1,70,59z"/>
    <path android:fillColor="#F5F7FA" android:pathData="M79,59l14,14l-5,5l-14,-14z"/>
    <path android:fillColor="#17C873" android:pathData="M81,18h17v17h-17z"/>
    <path android:fillColor="#101722" android:pathData="M85,22h9v9h-9z"/>
</vector>
''', encoding="utf-8")

# Manifest: nome e icone da beta.
xml = manifest.read_text(encoding="utf-8")
app_match = re.search(r'<application\b[^>]*>', xml, flags=re.S)
if not app_match:
    raise SystemExit("ERRO: tag <application> nao encontrada")
app_tag = app_match.group(0)

def set_attr(tag: str, attr: str, value: str) -> str:
    pattern = rf'\s{re.escape(attr)}="[^"]*"'
    replacement = f' {attr}="{value}"'
    if re.search(pattern, tag):
        return re.sub(pattern, replacement, tag, count=1)
    return tag[:-1] + replacement + '>'

app_tag = set_attr(app_tag, "android:label", "@string/app_name")
app_tag = set_attr(app_tag, "android:icon", "@drawable/matchscope_beta_logo")
app_tag = set_attr(app_tag, "android:roundIcon", "@drawable/matchscope_beta_logo")
xml = xml[:app_match.start()] + app_tag + xml[app_match.end():]
manifest.write_text(xml, encoding="utf-8")

# Identidade de pacote separada para instalar Beta e V6 juntas.
g = gradle.read_text(encoding="utf-8")
app_id_pattern = r'applicationId\s*=\s*"[^"]+"'
if re.search(app_id_pattern, g):
    g = re.sub(app_id_pattern, 'applicationId = "com.matchscope.app.beta"', g, count=1)
else:
    print("AVISO: applicationId nao localizado; mantendo pacote original.")

# Identificacao de versao beta, quando os campos existirem.
if re.search(r'versionName\s*=\s*"[^"]+"', g):
    g = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "0.7.0-beta"', g, count=1)
if re.search(r'versionCode\s*=\s*\d+', g):
    current = re.search(r'versionCode\s*=\s*(\d+)', g)
    if current:
        new_code = max(int(current.group(1)) + 1, 7)
        g = re.sub(r'versionCode\s*=\s*\d+', f'versionCode = {new_code}', g, count=1)

gradle.write_text(g, encoding="utf-8")

# Titulo visual simples dentro do WebView, sem depender da estrutura do JS.
index_file = main_dir / "assets/www/index.html"
if index_file.exists():
    html = index_file.read_text(encoding="utf-8")
    html = re.sub(r'<title>.*?</title>', '<title>MatchScope Beta</title>', html, count=1, flags=re.S)
    if 'data-matchscope-beta' not in html:
        badge = '''\n<style data-matchscope-beta>
  .matchscope-beta-badge{position:fixed;right:10px;top:10px;z-index:99999;background:#17c873;color:#101722;border-radius:999px;padding:4px 8px;font:700 10px/1.2 system-ui,sans-serif;letter-spacing:.08em;box-shadow:0 2px 10px #0005;pointer-events:none}
</style>
<div class="matchscope-beta-badge" data-matchscope-beta>BETA</div>\n'''
        if '<body' in html:
            body_end = html.find('>', html.find('<body'))
            html = html[:body_end+1] + badge + html[body_end+1:]
    index_file.write_text(html, encoding="utf-8")

print("Branding MatchScope Beta aplicado com sucesso.")
print(f"Logo: {logo}")
print("Nome: MatchScope Beta")
print("Pacote alvo: com.matchscope.app.beta")
