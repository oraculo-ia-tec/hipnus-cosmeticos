from pathlib import Path; import sys
_r = Path(__file__).resolve().parents[1]; _f = _r / "frontend"
for _p in [str(_r), str(_f)]:
    if _p not in sys.path: sys.path.insert(0, _p)
# Busca o arquivo pelo padrão, ignorando o emoji exato
_matches = sorted((_f / "pages").glob("3_*Loja*Parceiro*.py"))
if not _matches:
    raise FileNotFoundError("Arquivo 3_*Loja*Parceiro*.py não encontrado em frontend/pages/")
exec(_matches[0].read_text(encoding="utf-8"))
