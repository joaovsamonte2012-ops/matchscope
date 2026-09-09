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

# Nome oficial do aplicativo
values_dir = res_dir / "values"
values_dir.mkdir(parents=True, exist_ok=True)
strings_file = values_dir / "strings.xml"
if strings_file.exists():
    strings = strings_file.read_text(encoding="utf-8")
    if re.search(r'<string\s+name=["\']app_name["\']>.*?</string>', strings, flags=re.S):
        strings = re.sub(r'<string\s+name=["\']app_name["\']>.*?</string>', '<string name="app_name">MatchScore</string>', strings, count=1, flags=re.S)
    else:
        strings = strings.replace("</resources>", '    <string name="app_name">MatchScore</string>\n</resources>')
else:
    strings = '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <string name="app_name">MatchScore</string>\n</resources>\n'
strings_file.write_text(strings, encoding="utf-8")

# Logo vetorial temporario do MatchScore.
drawable_dir = res_dir / "drawable"
drawable_dir.mkdir(parents=True, exist_ok=True)
logo = drawable_dir / "matchscore_beta_logo.xml"
logo.write_text('''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#101722" android:pathData="M0,0h108v108h-108z"/>
    <path android:fillColor="#17C873" android:pathData="M12,12h84v84h-84z"/>
    <path android:fillColor="#101722" android:pathData="M17,17h74v74h-74z"/>
    <path android:strokeColor="#17C873" android:strokeWidth="3" android:fillColor="@android:color/transparent" android:pathData="M24,25h60v58h-60zM54,25v58M24,54h60"/>
    <path android:strokeColor="#17C873" android:strokeWidth="3" android:fillColor="@android:color/transparent" android:pathData="M54,45a9,9 0,1 0,0 18a9,9 0,1 0,0 -18"/>
    <path android:fillColor="#F5F7FA" android:pathData="M70,64a13,13 0,1 0,-9.19,-3.81A13,13 0,0 0,70,64zM70,59a8,8 0,1 1,5.66,-2.34A8,8 0,0 1,70,59z"/>
    <path android:fillColor="#F5F7FA" android:pathData="M79,59l14,14l-5,5l-14,-14z"/>
</vector>''', encoding="utf-8")

xml = manifest.read_text(encoding="utf-8")n