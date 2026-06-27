import sys
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[1]
_FRONTEND = _ROOT / "frontend"
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Passa __file__ do arquivo REAL para que Path(__file__).parents[]
# funcione corretamente dentro do codigo executado.
_target = _FRONTEND / "pages" / "7_Cadastro_Parceiro.py"
_src    = open(_target, encoding="utf-8").read()
_globs  = {**globals(), "__file__": str(_target)}
exec(compile(_src, str(_target), "exec"), _globs)
