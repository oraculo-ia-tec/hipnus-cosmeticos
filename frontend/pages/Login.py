"""
Login.py — página de login no contexto frontend/Home.py como entry point.
Executa login.py da raiz, corrigindo os caminhos de switch_page para
serem relativos a frontend/ (onde Home.py vive).
"""
import sys
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]  # raiz do projeto
_FRONTEND = Path(__file__).resolve().parents[1]  # frontend/
for _p in [str(_FRONTEND), str(_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

_src = (_ROOT / "login.py").read_text(encoding="utf-8")
# login.py usa caminhos relativos à raiz; ajusta para relativo a frontend/
_src = _src.replace('"frontend/pages/', '"pages/')
exec(compile(_src, str(_ROOT / "login.py"), "exec"), {"__file__": str(_ROOT / "login.py")})
