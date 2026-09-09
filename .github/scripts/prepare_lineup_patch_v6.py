import os
from pathlib import Path

android_dir = Path(os.environ["ANDROID_DIR"])
app_js = android_dir / "app/src/main/assets/www/app.js"
if not app_js.exists():
    raise SystemExit(f"ERRO: arquivo nao encontrado: {app_js}")

js = app_js.read_text(encoding="utf-8")
marker = js.find("function renderMatchTab")
if marker < 0:
    raise SystemExit("ERRO: funcao renderMatchTab nao encontrada")

# O patch antigo localiza a primeira ocorrencia de raw.lineups. A integracao V4
# tambem usa raw.lineups em loadDetail, antes da aba visual. Nesta etapa trocamos
# somente essas referencias anteriores por notacao de colchetes, mantendo o
# mesmo comportamento JavaScript e fazendo o patch mirar a aba de Escalacoes.
prefix = js[:marker]
suffix = js[marker:]
replacements = {
    "d.raw?.lineups": "d.raw?.[\"lineups\"]",
    "d.raw.lineups": "d.raw[\"lineups\"]",
    "raw?.lineups": "raw?.[\"lineups\"]",
    "raw.lineups": "raw[\"lineups\"]",
}
count = 0
for old, new in replacements.items():
    n = prefix.count(old)
    if n:
        prefix = prefix.replace(old, new)
        count += n

app_js.write_text(prefix + suffix, encoding="utf-8")
print(f"Preparo da aba de escalacoes concluido: {count} referencia(s) anteriores ajustada(s).")
