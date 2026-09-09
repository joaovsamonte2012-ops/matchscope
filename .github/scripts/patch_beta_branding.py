import os
import re
from pathlib import Path

android_dir = Path(os.environ['ANDROID_DIR'])
app_dir = android_dir / 'app'
main_dir = app_dir / 'src/main'
res_dir = main_dir / 'res'
manifest = main_dir / 'AndroidManifest.xml'
gradle = app_dir / 'build.gradle.kts'

if not manifest.exists():
    raise SystemExit(f'ERRO: AndroidManifest nao encontrado: {manifest}')
if not gradle.exists():
    raise SystemExit(f'ERRO: build.gradle.kts nao encontrado: {gradle}')

# Nome oficial
values_dir = res_dir / 'values'
values_dir.mkdir(parents=True, exist_ok=True)
strings_file = values_dir / 'strings.xml'
strings = strings_file.read_text(encoding='utf-8') if strings_file.exists() else '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n</resources>\n'
if re.search(r'<string\s+name=["\']app_name["\']>.*?</string>', strings, flags=re.S):
    strings = re.sub(r'<string\s+name=["\']app_name["\']>.*?</string>', '<string name="app_name">MatchScore</string>', strings, count=1, flags=re.S)
else:
    strings = strings.replace('</resources>', '    <string name="app_name">MatchScore</string>\n</resources>')
strings_file.write_text(strings, encoding='utf-8')

# Icone vetorial MatchScore: futebol + graficos de analise
drawable_dir = res_dir / 'drawable'
drawable_dir.mkdir(parents=True, exist_ok=True)
logo = drawable_dir / 'matchscore_icon.xml'
logo.write_text('''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">
 <path android:fillColor="#07110B" android:pathData="M0,0h108v108h-108z"/>
 <path android:strokeColor="#21F36B" android:strokeWidth="4" android:fillColor="@android:color/transparent" android:pathData="M8,8h92v92h-92z"/>
 <path android:fillColor="#E9EEF0" android:pathData="M24,70L24,35L35,35L54,55L73,35L84,35L84,70L73,70L73,50L54,70L35,50L35,70z"/>
 <path android:fillColor="#21F36B" android:pathData="M54,55L73,35L84,35L84,70L73,70L73,50L54,70z"/>
 <path android:strokeColor="#21F36B" android:strokeWidth="4" android:fillColor="@android:color/transparent" android:pathData="M68,29L77,20L84,27L94,16"/>
 <path android:fillColor="#21F36B" android:pathData="M89,16h5v5z"/>
 <path android:fillColor="#21F36B" android:pathData="M75,82h5v10h-5zM83,77h5v15h-5zM91,70h5v22h-5z"/>
</vector>''', encoding='utf-8')

xml = manifest.read_text(encoding='utf-8')
app_match = re.search(r'<application\b[^>]*>', xml, flags=re.S)
if not app_match:
    raise SystemExit('ERRO: tag <application> nao encontrada')
app_tag = app_match.group(0)
def set_attr(tag, attr, value):
    pattern = rf'\s{re.escape(attr)}="[^"]*"'
    replacement = f' {attr}="{value}"'
    return re.sub(pattern, replacement, tag, count=1) if re.search(pattern, tag) else tag[:-1] + replacement + '>'
app_tag = set_attr(app_tag, 'android:label', '@string/app_name')
app_tag = set_attr(app_tag, 'android:icon', '@drawable/matchscore_icon')
app_tag = set_attr(app_tag, 'android:roundIcon', '@drawable/matchscore_icon')
xml = xml[:app_match.start()] + app_tag + xml[app_match.end():]
manifest.write_text(xml, encoding='utf-8')

# Pacote alinhado ao app registrado no Firebase
g = gradle.read_text(encoding='utf-8')
if re.search(r'applicationId\s*=\s*"[^"]+"', g):
    g = re.sub(r'applicationId\s*=\s*"[^"]+"', 'applicationId = "com.matchscore.app"', g, count=1)
if re.search(r'versionName\s*=\s*"[^"]+"', g):
    g = re.sub(r'versionName\s*=\s*"[^"]+"', 'versionName = "0.7.1-beta"', g, count=1)
if re.search(r'versionCode\s*=\s*\d+', g):
    m = re.search(r'versionCode\s*=\s*(\d+)', g)
    g = re.sub(r'versionCode\s*=\s*\d+', f'versionCode = {max(int(m.group(1))+1, 8)}', g, count=1)
gradle.write_text(g, encoding='utf-8')

# Corrige textos visiveis antigos no WebView
www = main_dir / 'assets/www'
if www.exists():
    for f in www.rglob('*'):
        if f.is_file() and f.suffix.lower() in {'.html','.js','.css','.json'}:
            try:
                text = f.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue
            text = text.replace('MatchScope Beta', 'MatchScore').replace('MatchScope', 'MatchScore')
            if f.name == 'index.html':
                text = re.sub(r'<title>.*?</title>', '<title>MatchScore</title>', text, count=1, flags=re.S)
            f.write_text(text, encoding='utf-8')

print('Branding MatchScore aplicado com sucesso.')
print('Nome: MatchScore')
print('Pacote: com.matchscore.app')
print(f'Icone: {logo}')
