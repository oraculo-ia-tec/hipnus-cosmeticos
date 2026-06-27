"""
pages/0_Dashboard.py — HIPNUS COSMÉTICOS
==========================================
Proxy para o Dashboard Admin no frontend/ (Skill #4).
"""
from __future__ import annotations
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[1]
_frontend  = _repo_root / "frontend"
for _p in [str(_repo_root), str(_frontend)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

exec((Path(_frontend) / "pages" / "0_📊_Dashboard.py").read_text(encoding="utf-8"))
