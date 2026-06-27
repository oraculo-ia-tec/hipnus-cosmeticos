"""
pages/00_IA_Consultora.py — HIPNUS COSMÉTICOS
================================================
Proxy para a IA Consultora (primeiro item do menu).
A chave GROQ está em secrets.toml na seção [groq].
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

import streamlit as st

# Chave dentro da seção [groq] no secrets.toml
os.environ["GROQ_API_KEY"] = str(st.secrets["groq"]["GROQ_API_KEY"]).strip()

exec((Path(_frontend) / "pages" / "10_🤖_IA_Consultora.py").read_text(encoding="utf-8"))
