"""
pages/7_Convites.py — HIPNUS COSMÉTICOS
Redireciona para o módulo real em frontend/pages/6_Convites.py

OBS: O Streamlit Cloud serve /pages/*.py da raiz.
     Este arquivo é o pórtico — importa e executa o código completo.
"""
from __future__ import annotations
import sys
from pathlib import Path
import importlib.util

_ROOT     = Path(__file__).resolve().parents[1]
_FRONTEND = _ROOT / "frontend"
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# URL base real do Streamlit Cloud — aponta para /Cadastro_Parceiro
# (Streamlit usa o nome do arquivo sem número como slug de rota)
import os
import streamlit as st

_BASE_URL = (
    st.secrets.get("APP_BASE_URL", "")
    if hasattr(st, 'secrets') else ""
) or os.getenv("APP_BASE_URL", "https://hipnus-cosmeticos.streamlit.app")
_BASE_URL = _BASE_URL.rstrip("/")

# Injeta a URL correta como variável de ambiente para o módulo filho
os.environ["_HIPNUS_SIGNUP_BASE"] = f"{_BASE_URL}/Cadastro_Parceiro"

# Carrega e executa o módulo real
_target = _FRONTEND / "pages" / "6_Convites.py"
if _target.exists():
    spec = importlib.util.spec_from_file_location("convites_module", str(_target))
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
else:
    st.error(f"❌ Módulo de convites não encontrado em: {_target}")
    st.stop()
