"""
Script — cria/atualiza o usuário de teste "Parceiro Demonstração" (role: b2b).
Usado para demonstrações do sistema a futuros parceiros (revendedores/salões).
Reaplica hash bcrypt caso o registro já exista com hash legado.
Execute a partir da raiz do projeto:
    python scripts/create_demo_partner_user.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "frontend"))

from app.skills.auth_skill import hash_password, verify_password  # noqa: E402
from app.skills.db_skill import get_db_session   # noqa: E402
from app.domains.partners.models.parceiros import Parceiro  # noqa: E402

EMAIL    = "demo.parceiro@talyacosmeticos.com.br"
USERNAME = "demo.parceiro"
NOME     = "Parceiro Demonstração"
EMPRESA  = "Tálya Demo Store"
SENHA    = "TalyaDemo@2026"
ROLE     = "b2b"

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
        existing.empresa    = EMPRESA
        db.commit()
        db.refresh(existing)
        senha_hash = existing.senha_hash
        print(f"[OK] Usuário de teste atualizado — id={existing.id}")
    else:
        p = Parceiro(
            username=USERNAME,
            nome=NOME,
            email=EMAIL,
            empresa=EMPRESA,
            role=ROLE,
            senha_hash=hash_password(SENHA),
        )
        db.add(p)
        db.commit()
        db.refresh(p)
        senha_hash = p.senha_hash
        print(f"[OK] Usuário de teste criado — id={p.id}")

    # Verificação: confirma que a senha em texto plano bate com o hash gravado
    assert verify_password(SENHA, senha_hash), "Falha na verificação de senha pós-gravação"
    print("[OK] Autenticação verificada com sucesso (senha confere com o hash gravado).")
    print(f"     username: {USERNAME}")
    print(f"     email:    {EMAIL}")
    print(f"     senha:    {SENHA}")
    print(f"     role:     {ROLE}")
finally:
    db.close()
