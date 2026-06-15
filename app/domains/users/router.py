"""
router.py — Domínio Users
===========================
Endpoints de autenticação e gerenciamento de usuários.

Rotas pública:
  POST /api/v1/auth/login    — autentica e retorna JWT
  POST /api/v1/auth/register — cadastro de novo usuário (b2c por padrão)

Rotas protegidas (requerem JWT válido no header Authorization):
  GET  /api/v1/auth/me       — retorna dados do usuário logado
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.domains.users import service
from app.domains.users.schemas import LoginRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> dict:
    """
    Dependência FastAPI: decodifica o JWT e retorna o payload.
    Lança 401 se o token for inválido ou expirado.
    """
    try:
        payload = service.decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


@router.post("/login", response_model=TokenResponse, summary="Login com username e senha")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db:   Session = Depends(get_db),
):
    """
    Autentica o usuário e retorna um JWT de acesso.

    Parâmetros (form-data):
      username: nome de usuário
      password: senha em texto plano

    Retorno:
      access_token, token_type, user (dados completos do usuário)

    Efeitos colaterais:
      Nenhum — operacao somente leitura no banco.
    """
    user = service.authenticate(db, form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = service.create_access_token(user)
    return TokenResponse(access_token=token, token_type="bearer", user=UserRead.model_validate(user))


@router.post("/register", response_model=UserRead, status_code=201, summary="Cadastro de novo usuário")
def register(data: UserCreate, db: Session = Depends(get_db)):
    """
    Cadastra um novo usuário na plataforma.

    Regras:
      - username e e-mail devem ser únicos.
      - Role padrão: b2c. Somente super_admin pode criar outros roles.
      - is_verified inicia como False (confirmação de e-mail futura).

    Retorno: dados públicos do usuário criado (sem senha).
    """
    try:
        user = service.create_user(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return UserRead.model_validate(user)


@router.get("/me", response_model=UserRead, summary="Dados do usuário autenticado")
def me(payload: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retorna os dados atualizados do usuário logado a partir do banco.

    Requer: Authorization: Bearer <token>

    Retorno: UserRead com todos os campos públicos.
    """
    user = service.get_by_id(db, int(payload["id"]))
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return UserRead.model_validate(user)
