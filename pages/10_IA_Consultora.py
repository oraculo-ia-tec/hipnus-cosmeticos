"""
pages/10_IA_Consultora.py — HIPNUS COSMÉTICOS
================================================
Proxy para a IA Consultora no frontend/ (Skill IA Consultora).
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

# Injeta a chave GROQ no ambiente ANTES de executar a página
# Isso garante que _get_api_key() a encontre via os.environ
# independentemente de como st.secrets se comporta no exec()
try:
    import streamlit as st
    _key = st.secrets.get("GROQ_API_KEY", "") or ""
    if not _key:
        # tenta acesso direto por subscript
        try:
            _key = st.secrets["GROQ_API_KEY"]
        except Exception:
            _key = ""
    if _key:
        os.environ["GROQ_API_KEY"] = str(_key).strip()
except Exception:
    pass

exec((Path(_frontend) / "pages" / "10_🤖_IA_Consultora.py").read_text(encoding="utf-8"))
