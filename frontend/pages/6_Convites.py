"""
6_Convites.py — HIPNUS COSMÉTICOS
"""
from __future__ import annotations
import os
import smtplib
import socket
import ssl
import sys
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from lib import ui, components
from lib.auth import require_auth, build_sidebar
from lib.invite_db import (
    criar_invite_db, listar_invites_db,
    deletar_invite_db, reativar_invite_db,
)
from lib.email_service import send_invite_email, send_test_email, smtp_status

st.set_page_config(page_title="Convites · HIPNUS", page_icon="✉️", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin"])
build_sidebar()

components.page_header(
    title="Convites de Parceiros",
    subtitle="Gerencie os acessos B2B da plataforma.",
    kicker="✉️ Gestão de Acessos",
)

# ── Mapa de perfis ─────────────────────────────────────────────────────
ROLES = [
    ("b2b",   "💇 Parceiro / Salão B2B",    "Acesso à loja parceiro, tabela de preços piso e pedidos B2B."),
    ("b2c",   "👤 Cliente Final B2C",       "Acesso à loja consumidor com preços sugeridos."),
    ("admin", "🛡️ Administrador",           "Acesso completo ao painel, relatórios e gestão de usuários."),
]
ROLE_OPTIONS  = [r[0] for r in ROLES]
ROLE_LABELS   = {r[0]: r[1] for r in ROLES}
ROLE_DESC     = {r[0]: r[2] for r in ROLES}

# ── URL base ─────────────────────────────────────────────────────────────────
def _get_base_url() -> str:
    try:
        val = st.secrets.get("APP_BASE_URL", "")
        if val:
            return str(val).rstrip("/")
    except Exception:
        pass
    val = os.getenv("_HIPNUS_SIGNUP_BASE", "")
    if val:
        return val.rstrip("/")
    val = os.getenv("APP_BASE_URL", "")
    if val:
        return val.rstrip("/")
    return "https://hipnus-cosmeticos.streamlit.app"

_base = _get_base_url()
_DEFAULT_SIGNUP_URL = (
    _base if _base.endswith("/Cadastro_Parceiro")
    else f"{_base}/Cadastro_Parceiro"
)


# ── Diagnóstico SMTP ───────────────────────────────────────────────────────
def _smtp_secret(key: str) -> str:
    """Lê chave do Streamlit secrets com fallback env."""
    try:
        v = st.secrets.get("email", {}).get(key) or st.secrets.get(key)
        if v:
            return str(v).strip()
    except Exception:
        pass
    return os.getenv(key, "")


def _testar_conexao_smtp() -> tuple[bool, str]:
    """Testa a conexão SMTP passo a passo e retorna (ok, mensagem_detalhada)."""
    host     = _smtp_secret("EMAIL_HOST") or "smtp.hostinger.com"
    port     = int(_smtp_secret("EMAIL_PORT") or 587)
    user     = _smtp_secret("EMAIL_USERNAME")
    password = _smtp_secret("EMAIL_PASSWORD")
    use_ssl  = (_smtp_secret("EMAIL_USE_SSL") or "false").lower() == "true"
    use_tls  = (_smtp_secret("EMAIL_USE_TLS") or "true").lower() == "true"

    if not user:
        return False, "❌ EMAIL_USERNAME não configurado nos Secrets."
    if not password:
        return False, "❌ EMAIL_PASSWORD não configurado nos Secrets."

    # Passo 1: TCP
    try:
        sock = socket.create_connection((host, port), timeout=8)
        sock.close()
    except socket.timeout:
        return False, f"❌ Timeout TCP ao conectar em {host}:{port}.\nO servidor não respondeu em 8 segundos. Verifique se a porta {port} está aberta."
    except ConnectionRefusedError:
        return False, f"❌ Conexão TCP recusada em {host}:{port}.\nVerifique o EMAIL_HOST e EMAIL_PORT."
    except Exception as e:
        return False, f"❌ Falha TCP em {host}:{port}: {e}"

    # Passo 2: SMTP handshake + login
    ctx = ssl.create_default_context()
    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, context=ctx, timeout=15) as s:
                s.login(user, password)
        else:
            with smtplib.SMTP(host, port, timeout=15) as s:
                s.ehlo()
                if use_tls:
                    s.starttls(context=ctx)
                    s.ehlo()
                s.login(user, password)
        return True, f"✅ Conexão e autenticação bem-sucedidas em {host}:{port}."
    except smtplib.SMTPAuthenticationError as e:
        return False, (
            f"❌ Falha de autenticação em {host}:{port}.\n"
            f"Verifique EMAIL_USERNAME e EMAIL_PASSWORD.\nDetalhe: {e}"
        )
    except smtplib.SMTPConnectError as e:
        return False, f"❌ SMTP não conectou em {host}:{port}: {e}"
    except ssl.SSLError as e:
        return False, (
            f"❌ Erro SSL em {host}:{port}.\n"
            f"Tente EMAIL_USE_SSL=false e EMAIL_USE_TLS=true (porta 587).\nDetalhe: {e}"
        )
    except Exception as e:
        return False, f"❌ Erro inesperado: {type(e).__name__}: {e}"


def _painel_diagnostico():
    """Expander com diagnóstico completo dos Secrets e teste de conexão."""
    with st.expander("🔧 Diagnóstico SMTP — clique para ver detalhes", expanded=False):
        smtp = smtp_status()

        # Tabela de Secrets
        col_a, col_b = st.columns(2)
        chaves = [
            ("EMAIL_HOST",     smtp["host"]),
            ("EMAIL_PORT",     str(smtp["port"])),
            ("EMAIL_USERNAME", "✅ configurado" if smtp["user_configured"]     else "❌ ausente"),
            ("EMAIL_PASSWORD", "✅ configurado" if smtp["password_configured"] else "❌ ausente"),
            ("EMAIL_USE_TLS",  str(smtp["use_tls"])),
            ("EMAIL_USE_SSL",  str(smtp["use_ssl"])),
            ("EMAIL_REMETENTE", smtp["from_email"]),
        ]
        with col_a:
            st.markdown("**Chave**")
            for k, _ in chaves:
                st.markdown(f"`{k}`")
        with col_b:
            st.markdown("**Valor / Status**")
            for _, v in chaves:
                st.markdown(v)

        st.markdown("---")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔌 Testar conexão SMTP", use_container_width=True):
                with st.spinner("Testando conexão..."):
                    ok, msg = _testar_conexao_smtp()
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
                    st.markdown("""
**Soluções comuns:**
- **Autenticação falha** → confirme usuário e senha no painel Hostinger
- **Porta 587 bloqueada** → tente `EMAIL_PORT=465` + `EMAIL_USE_SSL=true` + `EMAIL_USE_TLS=false`
- **Porta 465 bloqueada** → tente `EMAIL_PORT=587` + `EMAIL_USE_SSL=false` + `EMAIL_USE_TLS=true`
- **Streamlit Cloud bloqueia SMTP** → use um relay SMTP (SendGrid, Mailgun, Brevo)
                    """)

        with c2:
            email_teste = st.text_input("📥 Seu e-mail", placeholder="seuemail@email.com", key="smtp_test_dest")
            if st.button("📧 Enviar e-mail de teste", use_container_width=True, disabled=not smtp["ready"]):
                if not email_teste or "@" not in email_teste:
                    st.error("Informe um e-mail válido.")
                else:
                    with st.spinner("Enviando..."):
                        ok, msg = send_test_email(email_teste)
                    if ok:
                        st.success(f"✅ E-mail de teste enviado para **{email_teste}**. Verifique sua caixa de entrada.")
                    else:
                        st.error(f"❌ {msg}")


tab_novo, tab_email, tab_lista, tab_smtp = st.tabs([
    "➕ Novo Convite",
    "📧 Enviar por E-mail",
    "📋 Lista de Convites",
    "🔧 Diagnóstico SMTP",
])

# ── Aba 1: Gerar token ───────────────────────────────────────────────────
with tab_novo:
    with st.form("form_convite"):
        email = st.text_input("📧 E-mail do parceiro")
        role  = st.selectbox(
            "👥 Tipo de usuário convidado",
            options=ROLE_OPTIONS,
            format_func=lambda v: ROLE_LABELS[v],
        )
        st.caption(ROLE_DESC.get(role, ""))
        dias   = st.number_input("Validade (dias)", min_value=1, max_value=365, value=30)
        submit = st.form_submit_button("🔗 Gerar Convite", use_container_width=True)
    if submit:
        if not email or "@" not in email:
            st.error("Informe um e-mail válido.")
        else:
            try:
                token = criar_invite_db(email=email, role=role, dias=int(dias))
                link  = f"{_DEFAULT_SIGNUP_URL}?token={token}"
                st.success(f"✅ Convite gerado para **{email}** · perfil **{ROLE_LABELS[role]}**")
                st.markdown("**Link de cadastro (copie e envie manualmente):**")
                st.code(link, language="text")
                st.caption("⚠️ Teste o link abrindo em uma aba anônima antes de enviar.")
            except Exception as exc:
                st.error(f"Erro ao criar convite: {exc}")

# ── Aba 2: Gerar + Enviar por E-mail ────────────────────────────
with tab_email:
    smtp = smtp_status()

    # Status banner
    if smtp["ready"]:
        st.success(f"✅ SMTP pronto · Remetente: `{smtp['from_email']}`")
    else:
        st.error(
            "❌ **SMTP não está pronto.** "
            "Verifique as credenciais na aba **🔧 Diagnóstico SMTP** ao lado."
        )

    st.html(
        f'<div style="background:rgba(124,58,237,.07);border:1px solid rgba(168,85,247,.25);'
        f'border-radius:10px;padding:10px 16px;font-size:.78rem;margin-bottom:14px;">'
        f'🔗 URL de cadastro: '
        f'<code style="color:#7c3aed;font-weight:700;">{_DEFAULT_SIGNUP_URL}</code>'
        f'</div>'
    )

    with st.form("form_convite_email"):
        email_dest = st.text_input("📧 E-mail do convidado", placeholder="parceiro@email.com")
        role_dest  = st.selectbox(
            "👥 Tipo de usuário",
            options=ROLE_OPTIONS,
            format_func=lambda v: ROLE_LABELS[v],
            key="role_email",
        )
        st.caption(ROLE_DESC.get(role_dest, ""))
        dias_dest   = st.number_input("Validade (dias)", min_value=1, max_value=365, value=30, key="dias_email")
        signup_base = st.text_input(
            "🔗 URL de cadastro",
            value=_DEFAULT_SIGNUP_URL,
            help="O token é adicionado como ?token=... automaticamente.",
        )
        enviar = st.form_submit_button(
            "📤 Gerar token e enviar e-mail",
            use_container_width=True,
            type="primary",
            disabled=not smtp["ready"],
        )

    if enviar:
        if not email_dest or "@" not in email_dest:
            st.error("Informe um e-mail válido.")
        else:
            try:
                token = criar_invite_db(email=email_dest, role=role_dest, dias=int(dias_dest))
                signup_url = f"{signup_base.rstrip('/')}?token={token}"
                with st.spinner("📤 Enviando e-mail..."):
                    ok, msg = send_invite_email(
                        destinatario=email_dest,
                        signup_url=signup_url,
                        role=role_dest,
                    )
                if ok:
                    st.success(f"✅ Convite enviado para **{email_dest}** · perfil **{ROLE_LABELS[role_dest]}**!")
                    st.info(f"🔗 Link enviado: `{signup_url}`")
                else:
                    st.error(f"❌ Falha ao enviar e-mail: {msg}")
                    st.warning("🔧 Acesse a aba **Diagnóstico SMTP** para testar a conexão e identificar o problema.")
                    st.markdown("**Link gerado (copie e envie manualmente enquanto resolve o SMTP):**")
                    st.code(signup_url, language="text")
            except Exception as exc:
                st.error(f"Erro: {type(exc).__name__}: {exc}")

# ── Aba 3: Lista de convites ──────────────────────────────────────────
with tab_lista:
    try:
        invites = listar_invites_db()
    except Exception as exc:
        st.error(f"Erro ao listar convites: {exc}")
        invites = []

    if not invites:
        components.empty_state(
            icon="✉️",
            title="Nenhum convite",
            message="Crie o primeiro convite nas abas ao lado.",
        )
    else:
        for inv in invites:
            usado     = inv.get("used", False)
            email_inv = inv.get("email", "")
            token_inv = inv.get("token", "")
            expires   = str(inv.get("expires_at") or "")[:10]
            role_inv  = inv.get("role", "")
            role_lbl  = ROLE_LABELS.get(role_inv, role_inv)
            link_inv  = f"{_DEFAULT_SIGNUP_URL}?token={token_inv}" if token_inv else ""
            badge     = "✅ Usado" if usado else "⏳ Ativo"

            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            with c1:
                st.markdown(f"**{email_inv}** · {role_lbl} · Expira: {expires} · {badge}")
                if link_inv and not usado:
                    st.caption(f"🔗 `{link_inv}`")
            with c2:
                if not usado and st.button("📋 Link", key=f"copy_{token_inv}"):
                    st.code(link_inv, language="text")
            with c3:
                if usado and st.button("🔄 Reativar", key=f"reat_{token_inv}"):
                    try:
                        reativar_invite_db(token_inv, dias=30)
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with c4:
                if st.button("🗑️", key=f"del_{token_inv}"):
                    try:
                        deletar_invite_db(token_inv)
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

# ── Aba 4: Diagnóstico SMTP ──────────────────────────────────────────
with tab_smtp:
    st.markdown("### 🔧 Diagnóstico de Configuração SMTP")
    st.caption("Use esta aba para verificar se as credenciais estão corretas e a conexão funciona.")

    smtp = smtp_status()

    # Grade de status das chaves
    st.markdown("#### Secrets configurados")
    chaves = [
        ("EMAIL_HOST",      smtp["host"],                                     "✅" if smtp["host"] else "❌"),
        ("EMAIL_PORT",      str(smtp["port"]),                                "✅" if smtp["port"] else "❌"),
        ("EMAIL_USERNAME",  "✅ configurado" if smtp["user_configured"]     else "❌ ausente",  "✅" if smtp["user_configured"]     else "❌"),
        ("EMAIL_PASSWORD",  "✅ configurado" if smtp["password_configured"] else "❌ ausente",  "✅" if smtp["password_configured"] else "❌"),
        ("EMAIL_USE_TLS",   str(smtp["use_tls"]),                             "✅"),
        ("EMAIL_USE_SSL",   str(smtp["use_ssl"]),                             "✅"),
        ("EMAIL_REMETENTE", smtp["from_email"],                               "✅" if smtp["from_email"] else "❌"),
    ]

    for k, v, badge in chaves:
        c1, c2, c3 = st.columns([2, 3, 1])
        c1.markdown(f"`{k}`")
        c2.markdown(v)
        c3.markdown(badge)

    st.markdown("---")
    st.markdown("#### Testar conexão")
    st.caption(
        "O botão abaixo tenta conectar ao servidor SMTP e fazer login. "
        "O erro exato é exibido para facilitar o diagnóstico."
    )

    if st.button("🔌 Testar conexão SMTP agora", use_container_width=True, type="primary"):
        with st.spinner("Conectando ao servidor de e-mail..."):
            ok, detalhe = _testar_conexao_smtp()
        if ok:
            st.success(detalhe)
        else:
            st.error(detalhe)
            st.markdown("""
##### Como resolver:
| Erro | Solução |
|---|---|
| Autenticação falha | Confirme usuário/senha no painel Hostinger. Se usa senha de aplicativo, verifique. |
| Timeout TCP | Streamlit Cloud pode bloquear porta 587. Tente porta **465** com `EMAIL_USE_SSL=true`. |
| SSL Error | Tente `EMAIL_USE_SSL=false` + `EMAIL_USE_TLS=true` + porta `587`. |
| SMTP não conectou | Verifique `EMAIL_HOST` — Hostinger usa `smtp.hostinger.com`. |
| Porta bloqueada | Use serviço relay: **SendGrid**, **Mailgun** ou **Brevo** (gratuitos). |
            """)

    st.markdown("---")
    st.markdown("#### Enviar e-mail de teste")
    email_teste = st.text_input("📥 Enviar teste para", placeholder="seu@email.com", key="diag_email")
    if st.button("📧 Enviar e-mail de teste", use_container_width=True, disabled=not smtp["ready"]):
        if not email_teste or "@" not in email_teste:
            st.error("Informe um e-mail válido.")
        else:
            with st.spinner("Enviando e-mail de teste..."):
                ok, msg = send_test_email(email_teste)
            if ok:
                st.success(f"✅ E-mail de teste enviado para **{email_teste}**! Verifique sua caixa de entrada (e spam).")
            else:
                st.error(f"❌ Falha: {msg}")

    st.markdown("---")
    st.markdown("""
#### 💡 Formato correto dos Secrets

No painel **Streamlit Cloud → Manage app → Secrets**, adicione:

```toml
[email]
EMAIL_HOST      = "smtp.hostinger.com"
EMAIL_PORT      = 587
EMAIL_USERNAME  = "noreply@hipnuscosmeticos.com.br"
EMAIL_PASSWORD  = "sua_senha_aqui"
EMAIL_USE_TLS   = true
EMAIL_USE_SSL   = false
EMAIL_REMETENTE = "HIPNUS COSM\u00c9TICOS <noreply@hipnuscosmeticos.com.br>"
```

Se a porta 587 estiver bloqueada (erro de timeout), use:
```toml
EMAIL_PORT    = 465
EMAIL_USE_SSL = true
EMAIL_USE_TLS = false
```
    """)
