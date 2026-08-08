"""
streamlit_app.py — TÁLYA COSMÉTICOS
=====================================
Entrypoint do Streamlit Cloud.
Configura st.navigation() para registrar login.py + frontend/pages/*.py,
permitindo que st.switch_page() funcione corretamente no Cloud.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_FRONTEND = _ROOT / "frontend"
for _p in [str(_FRONTEND), str(_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from app.db.init_db import init_db
    init_db()
except Exception:
    pass

import streamlit as st

_pages_dir = _FRONTEND / "pages"
_pg = st.navigation(
    [st.Page("login.py", title="Login", default=True)] +
    [st.Page(str(p)) for p in sorted(_pages_dir.glob("[0-9]*.py"))],
    position="hidden",
)
_pg.run()
