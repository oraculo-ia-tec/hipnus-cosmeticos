"""
db_utils.py — TÁLYA COSMÉTICOS
=================================
Re-exporta de app.skills.db_skill para retrocompatibilidade.
A implementação completa está em app/skills/db_skill.py.
"""
import sys
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.skills.db_skill import (  # noqa: F401, E402
    PROJECT_ROOT,
    get_db_session,
    init_db,
    resolve_db_url,
)

# Aliases para compatibilidade com código que usa FRONTEND_DIR
FRONTEND_DIR = _FRONTEND

__all__ = [
    "PROJECT_ROOT",
    "FRONTEND_DIR",
    "resolve_db_url",
    "get_db_session",
    "init_db",
]
