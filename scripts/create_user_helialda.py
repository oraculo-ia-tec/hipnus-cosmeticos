"""
Script — cria/atualiza a usuária Helialda Lopes (role: salao / DONO DE SALÃO).
Reaplica hash bcrypt caso o registro já exista com hash SHA-256 legado.
Execute a partir da raiz do projeto:
    python scripts/create_user_helialda.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "frontend"))

from app.skills.auth_skill import hash_password  # noqa: E402
from app.skills.db_skill import get_db_session   # noqa: E402
from app.domains.partners.models.parceiros import Parceiro  # noqa: E402

EMAIL    = "helialdalili@yahoo.com.br"
USERNAME = "helialda"
NOME     = "Helialda Lopes"
SENHA    = "helialda@2026"
ROLE     = "salao"

db, err = get_db_session()
if not db:
    print(f"[ERRO] Banco indisponível: {err}")
    sys.exit(1)

try:
    existing = db.query(Parceiro).filter(Parceiro.email == EMAIL).first()
    if existing:
        existing.senha_hash = hash_password(SENHA)
        existing.role       = ROLE
        existing.username   = USERNAME
        existing.nome       = NOME
        db.commit()
        print(f"[OK] Usuária atualizada com hash bcrypt — id={existing.id}")
    else:
        p = Parceiro(
            username=USERNAME,
            nome=NOME,
            email=EMAIL,
            role=ROLE,
            senha_hash=hash_password(SENHA),
        )
        db.add(p)
        db.commit()
        print(f"[OK] Usuária criada com hash bcrypt — id={p.id}")
finally:
    db.close()
