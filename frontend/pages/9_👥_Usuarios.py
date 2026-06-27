"""
9_👥_Usuarios.py — HIPNUS COSMÉTICOS
==========================================
Gestão de usuários: lista usuários demo/seed e parceiros cadastrados no banco.
Acesso restrito a super_admin.
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from lib import ui, components
from lib.auth import (
    require_auth, sidebar_logo, sidebar_user_info,
    sidebar_logout_button, USUARIOS_DEMO,
)

st.set_page_config(
    page_title="Usuários · HIPNUS",
    page_icon="👥",
    layout="wide",
)
ui.inject_theme()

usuario = require_auth(perfis_permitidos=["super_admin"])
sidebar_logo()
sidebar_user_info()
sidebar_logout_button()

components.page_header(
    title="Gestão de Usuários",
    subtitle="Visualize todos os usuários do sistema e seus status.",
    kicker="Área Super Admin",
)

# ─── helpers ──────────────────────────────────────────────────────────────
ROLE_LABEL = {
    "super_admin": "⭐ Super Admin",
    "admin":       "🛡️ Admin",
    "b2b":         "🎤 Profissional",
    "b2c":         "👤 Cliente",
    "demo":        "👀 Demo",
}
ROLE_COLOR = {
    "super_admin": "#7c3aed",
    "admin":       "#1d4ed8",
    "b2b":         "#065f46",
    "b2c":         "#92400e",
    "demo":        "#374151",
}


def _badge(role: str) -> str:
    label = ROLE_LABEL.get(role, role.upper())
    color = ROLE_COLOR.get(role, "#374151")
    return (
        f'<span style="background:{color};color:#fff;font-size:.68rem;font-weight:700;'
        f'letter-spacing:.8px;padding:3px 10px;border-radius:999px;" >'
        f"{label}</span>"
    )


def _fmt_date(val) -> str:
    if not val:
        return "—"
    try:
        dt = datetime.fromisoformat(str(val))
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(val)


# ─── busca parceiros do banco ────────────────────────────────────────────────────
def _listar_parceiros() -> tuple[list[dict], str | None]:
    try:
        from lib.db_utils import get_db_session
        from sqlalchemy import text
        db, err = get_db_session()
        if not db:
            return [], err or "Banco indisponível."
        try:
            rows = db.execute(text(
                "SELECT id, username, nome, email, role, empresa, cidade, estado, "
                "telefone, created_at, updated_at "
                "FROM parceiros ORDER BY created_at DESC"
            )).fetchall()
            return [dict(r._mapping) for r in rows], None
        finally:
            db.close()
    except Exception as exc:
        return [], str(exc)


# ─── tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🏠 Usuários do Sistema", "🤝 Parceiros Cadastrados"])


# ══ TAB 1 — DEMO / SEED ─────────────────────────────────────────────────────────
with tab1:
    components.section_title("Usuários do Sistema")
    st.caption("Usuários fixos configurados no sistema. Acesso ativo enquanto o sistema estiver rodando.")
    components.divider()

    m1, m2, m3 = st.columns(3)
    roles = [u["role"] for u in USUARIOS_DEMO.values()]
    m1.metric("Total", len(USUARIOS_DEMO))
    m2.metric("Admins", sum(1 for r in roles if r in ("super_admin", "admin")))
    m3.metric("Profissionais / Clientes", sum(1 for r in roles if r not in ("super_admin", "admin")))

    components.divider()

    for uname, dados in USUARIOS_DEMO.items():
        role  = dados.get("role", "demo")
        nome  = dados.get("nome", uname)
        email = dados.get("email", "—")
        disp  = dados.get("display_name", "")

        st.html(f"""
        <div style="background:rgba(124,58,237,.07);border:1px solid rgba(185,131,255,.2);
                    border-radius:14px;padding:16px 20px;margin-bottom:10px;
                    display:flex;align-items:center;gap:18px;">
          <div style="width:46px;height:46px;border-radius:50%;
                      background:linear-gradient(135deg,rgba(124,58,237,.5),rgba(185,131,255,.3));
                      border:2px solid rgba(185,131,255,.4);
                      display:flex;align-items:center;justify-content:center;
                      font-size:1.4rem;flex-shrink:0;">
            {{
              'super_admin':'⭐','admin':'🛡️','b2b':'🎤','b2c':'👤'
            }}.get('{role}','👤')
          </div>
          <div style="flex:1;min-width:0;">
            <div style="font-weight:700;font-size:.95rem;color:#fff;margin-bottom:3px;">
              {nome}
              <span style="color:rgba(185,131,255,.6);font-weight:400;font-size:.8rem;margin-left:8px;">@{uname}</span>
            </div>
            <div style="font-size:.8rem;color:rgba(255,255,255,.55);margin-bottom:6px;">{email}</div>
            {_badge(role)}
            {'&nbsp;<span style="background:rgba(255,255,255,.07);color:rgba(255,255,255,.5);font-size:.68rem;padding:3px 9px;border-radius:999px;">'+disp+'</span>' if disp else ''}
          </div>
          <div style="text-align:right;flex-shrink:0;">
            <span style="background:#16a34a22;color:#4ade80;font-size:.72rem;font-weight:700;
                         padding:4px 12px;border-radius:999px;border:1px solid #16a34a44;">
              ● Ativo
            </span>
          </div>
        </div>
        """)


# ══ TAB 2 — PARCEIROS DO BANCO ───────────────────────────────────────────────────
with tab2:
    components.section_title("Parceiros Cadastrados")
    st.caption("Usuários que se cadastraram via convite ou pelo formulário de parceiro.")

    if st.button("🔄 Atualizar lista", key="_refresh_parceiros"):
        st.rerun()

    parceiros, erro = _listar_parceiros()

    if erro:
        st.warning(f"⚠️ Não foi possível acessar o banco de dados. Verifique as configurações.")
    elif not parceiros:
        components.empty_state(
            icon="🤝",
            title="Nenhum parceiro cadastrado",
            message="Os parceiros aparecem aqui após se cadastrarem via convite.",
        )
    else:
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Total", len(parceiros))
        p2.metric("Profissionais B2B", sum(1 for p in parceiros if p.get("role") == "b2b"))
        p3.metric("Clientes B2C",      sum(1 for p in parceiros if p.get("role") == "b2c"))
        p4.metric("Admins",            sum(1 for p in parceiros if p.get("role") in ("admin", "super_admin")))

        components.divider()

        for p in parceiros:
            role      = p.get("role", "b2b")
            nome      = p.get("nome") or p.get("username") or "—"
            email     = p.get("email", "—")
            empresa   = p.get("empresa") or ""
            cidade    = p.get("cidade") or ""
            estado    = p.get("estado") or ""
            telefone  = p.get("telefone") or ""
            criado_em = _fmt_date(p.get("created_at"))
            localiz   = f"{cidade}/{estado}" if cidade and estado else (cidade or estado or "—")

            icone = {"super_admin":"⭐","admin":"🛡️","b2b":"🎤","b2c":"👤"}.get(role, "👤")

            with st.expander(f"{icone} {nome}  ·  {email}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"**Perfil:** {ROLE_LABEL.get(role, role)}")
                    st.markdown(f"**E-mail:** {email}")
                    st.markdown(f"**Telefone:** {telefone or '—'}")
                with c2:
                    st.markdown(f"**Empresa:** {empresa or '—'}")
                    st.markdown(f"**Localização:** {localiz}")
                with c3:
                    st.markdown(f"**Cadastrado em:** {criado_em}")
                    st.html(
                        f'<span style="background:#16a34a22;color:#4ade80;font-size:.72rem;'
                        f'font-weight:700;padding:4px 12px;border-radius:999px;'
                        f'border:1px solid #16a34a44;">● Ativo</span>'
                    )
