# cache-bust: 2026-06-29T03:15Z — força recompilação do bytecode no Streamlit Cloud
from pathlib import Path; import sys
_r = Path(__file__).resolve().parents[1]; _f = _r / "frontend"
for _p in [str(_r), str(_f), str(_f / "lib")]:
    if _p not in sys.path: sys.path.insert(0, _p)
_target = _f / "pages" / "8_Configuracao.py"
_g = {**globals(), "__file__": str(_target)}
exec(compile(_target.read_text(encoding="utf-8"), str(_target), "exec"), _g)
