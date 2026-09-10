import os
import re
from pathlib import Path

android_dir = Path(os.environ['ANDROID_DIR'])
app_dir = android_dir / 'app'
www = app_dir / 'src/main/assets/www'
js_file = www / 'v28.js'
if not js_file.exists():
    raise SystemExit('ERRO: v28.js nao encontrado')

# Localiza MainActivity e a WebView real.
activity = None
for f in (app_dir / 'src/main').rglob('*.java'):
    text = f.read_text(encoding='utf-8', errors='ignore')
    if 'class MainActivity' in text and 'addJavascriptInterface' in text and 'WebView' in text:
        activity = f
        break
if not activity:
    raise SystemExit('ERRO: MainActivity nao encontrada')

text = activity.read_text(encoding='utf-8')
pkg = re.search(r'^\s*package\s+([\w.]+)\s*;', text, re.M)
if not pkg:
    raise SystemExit('ERRO: package da MainActivity nao encontrado')
package_name = pkg.group(1)
web = re.search(r'(\w+)\.addJavascriptInterface\s*\(', text)
if not web:
    raise SystemExit('ERRO: variavel WebView nao encontrada')
webview_var = web.group(1)
insert = f'{webview_var}.addJavascriptInterface(new MatchScoreV28Api(this, {webview_var}), "MatchScoreV28Api");'
if 'new MatchScoreV28Api(' not in text:
    line_end = text.find('\n', web.end())
    if line_end < 0:
        raise SystemExit('ERRO: ponto de injecao da bridge nao encontrado')
    text = text[:line_end+1] + '        ' + insert + '\n' + text[line_end+1:]
    activity.write_text(text, encoding='utf-8')

bridge = activity.parent / 'MatchScoreV28Api.java'
bridge.write_text(f'''package {package_name};

import android.app.Activity;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MatchScoreV28Api {{
    private final Activity activity;
    private final WebView webView;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    public MatchScoreV28Api(Activity activity, WebView webView) {{
        this.activity = activity;
        this.webView = webView;
    }}

    @JavascriptInterface
    public void fixturesByDate(String date) {{
        request("https://v3.football.api-sports.io/fixtures?date=" + safe(date));
    }}

    private String safe(String value) {{
        return value == null ? "" : value.replaceAll("[^0-9-]", "");
    }}

    private void request(String url) {{
        executor.execute(() -> {{
            HttpURLConnection c = null;
            try {{
                String key = BuildConfig.API_FOOTBALL_KEY == null ? "" : BuildConfig.API_FOOTBALL_KEY.trim();
                if (key.isEmpty()) throw new IllegalStateException("API_FOOTBALL_KEY vazia");
                c = (HttpURLConnection) new URL(url).openConnection();
                c.setRequestMethod("GET");
                c.setConnectTimeout(12000);
                c.setReadTimeout(18000);
                c.setRequestProperty("x-apisports-key", key);
                c.setRequestProperty("Accept", "application/json");
                int code = c.getResponseCode();
                InputStream in = code >= 200 && code < 300 ? c.getInputStream() : c.getErrorStream();
                BufferedReader br = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) sb.append(line);
                if (code < 200 || code >= 300) throw new IllegalStateException("HTTP " + code + ": " + sb);
                success(sb.toString());
            }} catch (Exception e) {{
                fail(e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage());
            }} finally {{
                if (c != null) c.disconnect();
            }}
        }});
    }}

    private void success(String rawJson) {{
        String quoted = JSONObject.quote(rawJson);
        webView.post(() -> webView.evaluateJavascript(
                "window.MatchScoreV28Native&&window.MatchScoreV28Native.success(" + quoted + ")", null));
    }}

    private void fail(String message) {{
        String quoted = JSONObject.quote(message);
        webView.post(() -> webView.evaluateJavascript(
                "window.MatchScoreV28Native&&window.MatchScoreV28Native.error(" + quoted + ")", null));
    }}
}}
''', encoding='utf-8')

js = js_file.read_text(encoding='utf-8')
js = re.sub(r"const API='https://matchscope-kjf9\.onrender\.com';\n", '', js, count=1)
start = js.find('async function loadMatches()')
if start < 0:
    raise SystemExit('ERRO: loadMatches nao encontrada')
end_marker = "if(document.readyState==='loading')"
end = js.find(end_marker, start)
if end < 0:
    raise SystemExit('ERRO: final de loadMatches nao encontrado')
new_loader = r'''function renderApiFootball(raw){
 const stat=$('#v28Api'),root=$('#v28Matches');
 let j;try{j=typeof raw==='string'?JSON.parse(raw):raw}catch(e){throw new Error('JSON invalido')}
 const arr=Array.isArray(j?.response)?j.response:[];
 const errs=j?.errors;
 if(errs && ((Array.isArray(errs)&&errs.length)||(typeof errs==='object'&&Object.keys(errs).length))) throw new Error('API-Football retornou erro');
 stat.textContent=`API-Football OK · ${arr.length}`;stat.classList.add('ok');
 if(!arr.length){root.innerHTML='<div class="v28-card v28-empty">Nenhuma partida encontrada para hoje.</div>';return;}
 root.innerHTML=arr.slice(0,40).map(m=>{const h=m.teams?.home||{},a=m.teams?.away||{},gh=m.goals?.home,ga=m.goals?.away,when=m.fixture?.date?new Date(m.fixture.date).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'}):'';return `<div class="v28-card v28-match"><div class="v28-team">${h.logo?`<img src="${esc(h.logo)}">`:''}<b>${esc(h.name||'Casa')}</b></div><div><div class="v28-score">${gh??'-'} × ${ga??'-'}</div><div class="v28-meta">${esc(when)} · ${esc(m.league?.name||'')}</div></div><div class="v28-team">${a.logo?`<img src="${esc(a.logo)}">`:''}<b>${esc(a.name||'Fora')}</b></div></div>`}).join('');
}
function loadMatches(){
 const stat=$('#v28Api'),root=$('#v28Matches');
 window.MatchScoreV28Native={success:(raw)=>{try{renderApiFootball(raw)}catch(e){window.MatchScoreV28Native.error(e.message)}},error:(msg)=>{stat.textContent='API indisponível';stat.classList.remove('ok');root.innerHTML=`<div class="v28-card v28-empty">Falha ao carregar partidas da API-Football.<br><small>${esc(msg||'Erro desconhecido')}</small></div>`;}};
 try{if(!window.MatchScoreV28Api||typeof window.MatchScoreV28Api.fixturesByDate!=='function')throw new Error('Bridge nativa indisponível');window.MatchScoreV28Api.fixturesByDate(dateLocal());}catch(e){window.MatchScoreV28Native.error(e.message)}
}
'''
js = js[:start] + new_loader + js[end:]
js_file.write_text(js, encoding='utf-8')

check = js_file.read_text(encoding='utf-8')
for needle in ['MatchScoreV28Api.fixturesByDate', 'API-Football OK', 'MatchScoreV28Native']:
    if needle not in check:
        raise SystemExit('ERRO: validacao V28 API-Football falhou: ' + needle)
print('V28 integrada a API-Football via bridge nativa.')
print('Bridge:', bridge)
