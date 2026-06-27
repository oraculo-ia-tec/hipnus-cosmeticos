from pathlib import Path; import sys
_r = Path(__file__).resolve().parents[1]; _f = _r / "frontend"
for _p in [str(_r), str(_f)]:
    if _p not in sys.path: sys.path.insert(0, _p)
exec((_f / "pages" / "8_Configuracao.py").read_text(encoding="utf-8"))
