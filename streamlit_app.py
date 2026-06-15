"""
streamlit_app.py — HIPNUS COSMÉTICOS
======================================
Entrypoint para o Streamlit Cloud.

O Streamlit Cloud detecta automaticamente este arquivo na raiz do
repositório como ponto de entrada. Ele simplesmente redireciona para
a Home real do frontend, garantindo que o sys.path esteja correto.

Não edite este arquivo para adicionar lógica — use frontend/Home.py.
"""
import sys
from pathlib import Path

# Garante que os módulos de frontend/lib sejam encontrados
frontend_path = Path(__file__).resolve().parent / "frontend"
if str(frontend_path) not in sys.path:
    sys.path.insert(0, str(frontend_path))

# Executa a Home do frontend diretamente
exec(open(frontend_path / "Home.py", encoding="utf-8").read())
