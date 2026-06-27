# pages/9_Configuracao.py — HIPNUS COSMÉTICOS
# Redireciona para a página real em frontend/pages/8_Configuracao.py
# Padrão idêntico aos demais arquivos em pages/ (raiz do repositório).
import sys
from pathlib import Path

frontend = Path(__file__).resolve().parents[1] / "frontend"
if str(frontend) not in sys.path:
    sys.path.insert(0, str(frontend))

exec(open(frontend / "pages" / "8_Configuracao.py", encoding="utf-8").read())
