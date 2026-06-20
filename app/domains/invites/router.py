"""
router.py — Domínio Invites
=============================
Endpoints FastAPI para gerenciamento de convites de cadastro.

Rotas:
  POST /api/v1/invites/         — Cria convite e envia e-mail (admin+)
  GET  /api/v1/invites/         — Lista todos os convites (admin+)
  GET  /api/v1/invites/{token}  — Valida token público (sem auth, usado no cadastro)
  POST /api/v1/invites/{token}/use — Marca convite como usado (interno)

Permissões:
  POST /invites/     — requer role super_admin ou admin
  GET  /invites/     — requer role super_admin ou admin
  GET  /invites/{token} — público (sem autenticação)
  POST /invites/{token}/use — público (chamado internamente no cadastro)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.domains.invites import schemas, service
from app.domains.users.router import get_current_user
from app.domains.users.models import User

router = APIRouter(prefix="/invites", tags=["Invites"])

ROLES_ADMIN = {"super_admin", "admin"}


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependência: exige que o usuário seja admin ou super_admin."""
    if current_user.role.value not in ROLES_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return current_user


@router.post(
    "/",
    response_model=schemas.InviteCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Criar convite",
)
def create_invite(
    payload:      schemas.InviteCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(_require_admin),
):
    """
    Cria um novo convite de cadastro e envia e-mail ao destinatário.

    Parâmetros:
      payload.email — e-mail do convidado
      payload.role  — perfil: b2b | b2c | admin

    Retorno:
      InviteCreated com token, signup_url e email_sent.

    Regras de negócio:
      - Apenas admin e super_admin podem criar convites
      - Token UUID único gerado automaticamente
      - E-mail enviado via SMTP Hostinger (falha silenciosa no campo email_sent)
      - Expiração: 7 dias

    Efeitos colaterais:
      - Persiste Invite no banco
      - Envia e-mail ao destinatário
    """
    return service.create_invite(db, payload, created_by=current_user.username)


@router.get(
    "/",
    response_model=list[schemas.InviteOut],
    summary="Listar convites",
)
def list_invites(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(_require_admin),
):
    """
    Lista todos os convites gerados, ordenados do mais recente ao mais antigo.

    Retorno:
      Lista de InviteOut.

    Permissões:
      Somente admin e super_admin.
    """
    return service.list_invites(db)


@router.get(
    "/{token}",
    response_model=schemas.InviteOut,
    summary="Validar token de convite",
)
def get_invite(
    token: str,
    db:    Session = Depends(get_db),
):
    """
    Valida um token de convite público (sem autenticação).

    Usado pela página de cadastro para verificar se o token é válido,
    não expirado e não utilizado antes de exibir o formulário.

    Parâmetros:
      token — token UUID hex do convite

    Retorno:
      InviteOut se válido.

    Erros:
      404 — token não encontrado
      410 — token já utilizado
      410 — token expirado
    """
    from datetime import datetime, timezone
    invite = service.get_invite_by_token(db, token)
    if not invite:
        raise HTTPException(status_code=404, detail="Convite não encontrado.")
    if invite.used:
        raise HTTPException(status_code=410, detail="Este convite já foi utilizado.")
    if invite.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(status_code=410, detail="Este convite expirou.")
    return invite


@router.post(
    "/{token}/use",
    response_model=schemas.InviteOut,
    summary="Marcar convite como usado",
)
def use_invite(
    token: str,
    db:    Session = Depends(get_db),
):
    """
    Marca um convite como usado após o cadastro ser concluído.

    Chamado internamente pelo fluxo de cadastro de parceiro.

    Parâmetros:
      token — token UUID hex do convite

    Retorno:
      InviteOut atualizado.

    Erros:
      404 — token não encontrado
    """
    invite = service.mark_invite_used(db, token)
    if not invite:
        raise HTTPException(status_code=404, detail="Convite não encontrado.")
    return invite
