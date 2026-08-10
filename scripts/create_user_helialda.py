"""
Script temporário — cria a usuária Helialda Lopes (role: salao / DONO DE SALÃO).
Execute a partir da raiz do projeto:
    python scripts/create_user_helialda.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "frontend"))

from frontend.lib.user_db import criar_parceiro  # noqa: E402

ok, msg = criar_parceiro(
    nome="Helialda Lopes",
    email="helialdalili@yahoo.com.br",
    senha="helialda@2026",
    role="salao",
    username="helialda",
)

if ok:
    print(f"[OK] {msg}")
else:
    print(f"[ERRO] {msg}")
    sys.exit(1)
