import os
from pathlib import Path

android_dir = Path(os.environ["ANDROID_DIR"])
js_file = android_dir / "app/src/main/assets/www/beta-auth-payments.js"
if not js_file.exists():
    raise SystemExit("ERRO: beta-auth-payments.js nao encontrado; execute o patch de conta antes")

js = js_file.read_text(encoding="utf-8")
js = js.replace("MatchScope", "MatchScore").replace("palpites", "análises")

js = js.replace(
    "let fb=null,auth=null;",
    "let fb=null,auth=null,nativeUser=null;"
)

js = js.replace(
    "function currentUser(){return auth?.currentUser||null}",
    "function currentUser(){return nativeUser||auth?.currentUser||null}"
)

old_login = """async function login(provider){
   const a=await loadFirebase();if(!a||!fb)return status('Configure o Firebase Authentication para ativar este login.');
   try{
     let p;if(provider==='google')p=new fb.GoogleAuthProvider();else if(provider==='facebook')p=new fb.FacebookAuthProvider();else{p=new fb.OAuthProvider('apple.com');p.addScope('email');p.addScope('name')}
     await fb.signInWithPopup(a,p);
   }catch(e){status('Falha ao entrar. Verifique a configuração do provedor.')}
 }"""
new_login = """async function login(provider){
   if(provider==='google'&&window.MatchScoreNativeAuth&&typeof window.MatchScoreNativeAuth.signInGoogle==='function'){
     status('Abrindo sua conta Google...');
     window.MatchScoreNativeAuth.signInGoogle();
     return;
   }
   const a=await loadFirebase();if(!a||!fb)return status('Este provedor ainda não está disponível nesta versão.');
   try{
     let p;if(provider==='facebook')p=new fb.FacebookAuthProvider();else{p=new fb.OAuthProvider('apple.com');p.addScope('email');p.addScope('name')}
     await fb.signInWithPopup(a,p);
   }catch(e){status('Falha ao entrar. Verifique a configuração do provedor.')}
 }"""
if old_login not in js:
    raise SystemExit("ERRO: bloco login esperado nao encontrado")
js = js.replace(old_login, new_login)

old_logout = """async function logout(){try{await fb.signOut(auth);localStorage.removeItem('ms_auth_token');localStorage.removeItem('ms_auth_uid');render()}catch{}}"""
new_logout = """async function logout(){
   try{
     if(nativeUser&&window.MatchScoreNativeAuth&&typeof window.MatchScoreNativeAuth.signOut==='function')window.MatchScoreNativeAuth.signOut();
     if(auth&&fb)await fb.signOut(auth);
   }catch{}
   nativeUser=null;localStorage.removeItem('ms_auth_token');localStorage.removeItem('ms_auth_uid');localStorage.removeItem('ms_native_user');render();
 }"""
if old_logout not in js:
    raise SystemExit("ERRO: bloco logout esperado nao encontrado")
js = js.replace(old_logout, new_logout)

anchor = """ensure();loadFirebase().then(render);
 window.MatchScoreAuth={render};"""
replacement = """try{const saved=JSON.parse(localStorage.getItem('ms_native_user')||'null');if(saved&&saved.uid)nativeUser=saved}catch{}
 window.MatchScoreNativeLogin={
   success(payload){
     try{
       const u=typeof payload==='string'?JSON.parse(payload):payload;
       nativeUser={uid:u.uid,displayName:u.name||'Usuário MatchScore',email:u.email||'',photoURL:u.photoURL||''};
       localStorage.setItem('ms_auth_uid',u.uid||'');
       localStorage.setItem('ms_auth_token',u.token||'');
       localStorage.setItem('ms_native_user',JSON.stringify(nativeUser));
       status('Conta Google conectada com sucesso.');render();
     }catch(e){status('Login concluído, mas houve erro ao atualizar a conta.')}
   },
   error(message){status(message||'Não foi possível entrar com Google.')},
   signedOut(){nativeUser=null;localStorage.removeItem('ms_auth_token');localStorage.removeItem('ms_auth_uid');localStorage.removeItem('ms_native_user');render()}
 };
 ensure();loadFirebase().then(render);
 window.MatchScoreAuth={render};"""
if anchor not in js:
    raise SystemExit("ERRO: ponto final do script de auth nao encontrado")
js = js.replace(anchor, replacement)

js_file.write_text(js, encoding="utf-8")
print("WebView conectado ao login Google nativo.")
