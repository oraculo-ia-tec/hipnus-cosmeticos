"""
asaas_client.py — HIPNUS COSMÉTICOS
=====================================
Re-exporta de app.skills.asaas_skill para retrocompatibilidade.
A implementação completa está em app/skills/asaas_skill.py.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.skills.asaas_skill import AsaasClient, AsaasError, AsaasService  # noqa: F401

__all__ = ["AsaasClient", "AsaasError", "AsaasService"]
