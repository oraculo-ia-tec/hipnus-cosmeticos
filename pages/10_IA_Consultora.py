"""
pages/10_IA_Consultora.py — HIPNUS COSMÉTICOS
================================================
Proxy para a IA Consultora no frontend/ (Skill IA Consultora).
"""
from __future__ import annotations
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[1]
_frontend  = _repo_root / "frontend"
for _p in [str(_repo_root), str(_frontend)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

exec((Path(_frontend) / "pages" / "10_🤖_IA_Consultora.py").read_text(encoding="utf-8"))
