"""
streamlit_app.py — HIPNUS COSMÉTICOS
======================================
Entrypoint para o Streamlit Cloud.
Redireciona para a página de Login como porta de entrada obrigatória.
"""
import sys
from pathlib import Path

frontend_path = Path(__file__).resolve().parent / "frontend"
if str(frontend_path) not in sys.path:
    sys.path.insert(0, str(frontend_path))

# Importa e executa a página de Login diretamente
exec(open(frontend_path / "Login.py", encoding="utf-8").read())
