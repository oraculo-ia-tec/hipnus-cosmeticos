"""Exceções de domínio do HIPNUS COSMÉTICOS.

Mapeadas para respostas HTTP coerentes em app/main.py.
"""


class DomainError(Exception):
    """Erro de regra de negócio (mapeado para HTTP 422/409)."""

    status_code = 422

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class PriceBelowFloorError(DomainError):
    """Tentativa de cadastrar preço de venda abaixo do piso do produto."""

    status_code = 422
