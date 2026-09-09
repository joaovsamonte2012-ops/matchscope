import os
import re
from pathlib import Path

android_dir = Path(os.environ["ANDROID_DIR"])
app_dir = android_dir / "app"
gradle = app_dir / "build.gradle.kts"
if not gradle.exists():
    raise SystemExit("ERRO: app/build.gradle.kts nao encontrado")

api_key = os.getenv("FIREBASE_API_KEY", "").strip()
project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()
app_id = os.getenv("FIREBASE_APP_ID", "").strip()
web_client_id = "849104902055-jhqpsu4tb3gi31tqc6gj9hrvhvqthk6v.apps.googleusercontent.com"

for name, value in {
    "FIREBASE_API_KEY": api_key,
    "FIREBASE_PROJECT_ID": project_id,
    "FIREBASE_APP_ID": app_id,
}.items():
    if not value:
        raise SystemExit(f"ERRO: {name} vazio")

# Dependencias oficiais recomendadas para Firebase Auth + Credential Manager.
g = gradle.read_text(encoding="utf-8")
deps = [
    'implementation(platform("com.google.firebase:firebase-bom:34.18.0"))',
    'implementation("com.google.firebase:firebase-auth")',
    'implementation("androidx.credentials:credentials:1.3.0")',
    'implementation("androidx.credentials:credentials-play-services-auth:1.3.0")',
    'implementation("com.google.android.libraries.identity.googleid:googleid:1.1.1")',
]
for dep in deps:
    if dep not in g:
        m = re.search(r"dependencies\s*\{", g)
        if not m:
            raise SystemExit("ERRO: bloco dependencies nao encontrado")
        g = g[:m.end()] + "\n    " + dep + g[m.end():]
gradle.write_text(g, encoding="utf-8")

# Localiza a Activity real do WebView no projeto base.
java_files = list((app_dir / "src/main").rglob("*.java"))
activity = None
for f in java_files:
    text = f.read_text(encoding="utf-8", errors="ignore")
    if "WebView" in text and "addJavascriptInterface" in text and "class MainActivity" in text:
        activity = f
        break
if not activity:
    raise SystemExit("ERRO: MainActivity Java do WebView nao encontrada")

activity_text = activity.read_text(encoding="utf-8")
pkg_match = re.search(r"^\s*package\s+([\w.]+)\s*;", activity_text, flags=re.M)
if not pkg_match:
    raise SystemExit("ERRO: package da MainActivity nao encontrado")
package_name = pkg_match.group(1)

# Descobre o nome da variavel WebView a partir da interface JS existente.
bridge_match = re.search(r"(\w+)\.addJavascriptInterface\s*\(", activity_text)
if not bridge_match:
    raise SystemExit("ERRO: WebView.addJavascriptInterface nao encontrado")
webview_var = bridge_match.group(1)
insert_line = f'{webview_var}.addJavascriptInterface(new MatchScoreGoogleAuth(this, {webview_var}), "MatchScoreNativeAuth");'
if "new MatchScoreGoogleAuth(" not in activity_text:
    line_end = activity_text.find("\n", bridge_match.end())
    if line_end == -1:
        raise SystemExit("ERRO: nao foi possivel inserir bridge nativa")
    activity_text = activity_text[:line_end + 1] + "        " + insert_line + "\n" + activity_text[line_end + 1:]
    activity.write_text(activity_text, encoding="utf-8")

bridge_java = activity.parent / "MatchScoreGoogleAuth.java"
bridge_java.write_text(f'''package {package_name};

import android.app.Activity;
import android.os.CancellationSignal;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import androidx.annotation.NonNull;
import androidx.credentials.Credential;
import androidx.credentials.CredentialManager;
import androidx.credentials.CredentialManagerCallback;
import androidx.credentials.CustomCredential;
import androidx.credentials.GetCredentialRequest;
import androidx.credentials.GetCredentialResponse;
import androidx.credentials.exceptions.GetCredentialException;

import com.google.android.libraries.identity.googleid.GetGoogleIdOption;
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.auth.GoogleAuthProvider;

import org.json.JSONObject;

public final class MatchScoreGoogleAuth {{
    private static final String WEB_CLIENT_ID = "{web_client_id}";
    private final Activity activity;
    private final WebView webView;
    private final FirebaseAuth auth;
    private final CredentialManager credentialManager;

    public MatchScoreGoogleAuth(Activity activity, WebView webView) {{
        this.activity = activity;
        this.webView = webView;
        if (FirebaseApp.getApps(activity).isEmpty()) {{
            FirebaseOptions options = new FirebaseOptions.Builder()
                    .setApiKey("{api_key}")
                    .setApplicationId("{app_id}")
                    .setProjectId("{project_id}")
                    .build();
            FirebaseApp.initializeApp(activity, options);
        }}
        this.auth = FirebaseAuth.getInstance();
        this.credentialManager = CredentialManager.create(activity);
    }}

    @JavascriptInterface
    public void signInGoogle() {{
        activity.runOnUiThread(() -> startGoogle(false));
    }}

    private void startGoogle(boolean authorizedOnly) {{
        GetGoogleIdOption google = new GetGoogleIdOption.Builder()
                .setFilterByAuthorizedAccounts(authorizedOnly)
                .setServerClientId(WEB_CLIENT_ID)
                .build();
        GetCredentialRequest request = new GetCredentialRequest.Builder()
                .addCredentialOption(google)
                .build();
        credentialManager.getCredentialAsync(
                activity,
                request,
                new CancellationSignal(),
                activity.getMainExecutor(),
                new CredentialManagerCallback<GetCredentialResponse, GetCredentialException>() {{
                    @Override public void onResult(GetCredentialResponse result) {{
                        handleCredential(result.getCredential());
                    }}
                    @Override public void onError(@NonNull GetCredentialException e) {{
                        fail("Nao foi possivel abrir o login Google: " + e.getClass().getSimpleName());
                    }}
                }}
        );
    }}

    private void handleCredential(Credential credential) {{
        try {{
            if (!(credential instanceof CustomCredential)) {{
                fail("Credencial Google invalida.");
                return;
            }}
            CustomCredential custom = (CustomCredential) credential;
            if (!GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL.equals(custom.getType())) {{
                fail("Credencial recebida nao e do Google.");
                return;
            }}
            GoogleIdTokenCredential google = GoogleIdTokenCredential.createFrom(custom.getData());
            auth.signInWithCredential(GoogleAuthProvider.getCredential(google.getIdToken(), null))
                    .addOnCompleteListener(activity, task -> {{
                        if (!task.isSuccessful() || auth.getCurrentUser() == null) {{
                            fail("Firebase recusou o login Google.");
                            return;
                        }}
                        sendUser(auth.getCurrentUser());
                    }});
        }} catch (Exception e) {{
            fail("Falha ao processar a conta Google.");
        }}
    }}

    private void sendUser(FirebaseUser user) {{
        user.getIdToken(true).addOnCompleteListener(task -> {{
            try {{
                JSONObject o = new JSONObject();
                o.put("uid", user.getUid());
                o.put("name", user.getDisplayName() == null ? "Usuario MatchScore" : user.getDisplayName());
                o.put("email", user.getEmail() == null ? "" : user.getEmail());
                o.put("photoURL", user.getPhotoUrl() == null ? "" : user.getPhotoUrl().toString());
                o.put("token", task.isSuccessful() && task.getResult() != null ? task.getResult().getToken() : "");
                String payload = JSONObject.quote(o.toString());
                webView.post(() -> webView.evaluateJavascript(
                        "window.MatchScoreNativeLogin&&window.MatchScoreNativeLogin.success(" + payload + ")", null));
            }} catch (Exception e) {{
                fail("Login concluido, mas nao foi possivel atualizar a tela.");
            }}
        }});
    }}

    @JavascriptInterface
    public void signOut() {{
        activity.runOnUiThread(() -> {{
            auth.signOut();
            webView.evaluateJavascript("window.MatchScoreNativeLogin&&window.MatchScoreNativeLogin.signedOut()", null);
        }});
    }}

    private void fail(String message) {{
        String quoted = JSONObject.quote(message);
        webView.post(() -> webView.evaluateJavascript(
                "window.MatchScoreNativeLogin&&window.MatchScoreNativeLogin.error(" + quoted + ")", null));
    }}
}}
''', encoding="utf-8")

print("Login Google nativo Android aplicado.")
print(f"Activity: {activity}")
print(f"Bridge: {bridge_java}")
