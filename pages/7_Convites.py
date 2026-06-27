import sys
from pathlib import Path

# Garante que _ROOT (raiz do projeto) e frontend/ estejam no sys.path
# ANTES do exec(), para que lib.invite_db e lib.db_utils sejam encontrados.
_ROOT     = Path(__file__).resolve().parents[1]
_FRONTEND = _ROOT / "frontend"
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

exec(open(_FRONTEND / "pages" / "6_Convites.py", encoding="utf-8").read())
