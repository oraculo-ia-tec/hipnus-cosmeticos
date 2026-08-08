"""
email_service.py — TÁLYA COSMÉTICOS
=====================================
Re-exporta de app.skills.email_skill para retrocompatibilidade.
A implementação completa está em app/skills/email_skill.py.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.skills.email_skill import (  # noqa: F401
    send_email,
    send_invite_email,
    send_order_confirmation_email,
    send_test_email,
    smtp_status,
)

__all__ = [
    "send_email",
    "send_invite_email",
    "send_order_confirmation_email",
    "send_test_email",
    "smtp_status",
]
