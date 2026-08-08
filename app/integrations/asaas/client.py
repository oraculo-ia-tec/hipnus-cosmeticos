"""
client.py — Integração Asaas
==============================
Re-exporta de app.skills.asaas_skill para retrocompatibilidade.
A implementação completa está em app/skills/asaas_skill.py.
"""
from app.skills.asaas_skill import AsaasClient, AsaasError  # noqa: F401

__all__ = ["AsaasClient", "AsaasError"]

