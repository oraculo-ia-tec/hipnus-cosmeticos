"""
pages/00_IA_Consultora.py — HIPNUS COSMÉTICOS
================================================
Proxy para a IA Consultora (primeiro item do menu).
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[1]
_frontend  = _repo_root / "frontend"
for _p in [str(_repo_root), str(_frontend)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Injeta GROQ_API_KEY no ambiente ANTES do exec()
try:
    import streamlit as st
    _key = ""
    try:
        _key = str(st.secrets["GROQ_API_KEY"]).strip()
    except Exception:
        pass
    if not _key:
        try:
            _key = str(getattr(st.secrets, "GROQ_API_KEY", "")).strip()
        except Exception:
            pass
    if _key:
        os.environ["GROQ_API_KEY"] = _key
except Exception:
    pass

exec((Path(_frontend) / "pages" / "10_🤖_IA_Consultora.py").read_text(encoding="utf-8"))
