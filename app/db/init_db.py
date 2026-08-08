"""
init_db.py — Inicialização do banco de dados
==============================================
Delega para app.skills.db_skill que centraliza a lógica de resolução
de DATABASE_URL e criação de tabelas.

Mantido por retrocompatibilidade — código legado que importa
`from app.db.init_db import init_db` continuará funcionando.
"""
from app.skills.db_skill import init_db, resolve_db_url  # noqa: F401

__all__ = ["init_db", "resolve_db_url"]
