"""
6_Convites.py — HIPNUS COSMÉTICOS
====================================
Gerenciamento de convites de cadastro para parceiros e distribuidores.

Estrutura em 3 abas:
  tab1 — Enviar Convite  : envia convite por e-mail via API (com SMTP real).
  tab2 — Gerar Convite   : gera token/link offline para envio manual.
  tab3 — Monitorar       : lista e monitora todos os convites da sessão / API.

Correções aplicadas (v2):
  - Bug 1: `email_sent` agora é lido corretamente do retorno da API;
            se a API não retornar o campo, assume True quando status==201
            (significa que o backend processou — o e-mail é responsabilidade do backend).
  - Bug 2: Fallback offline só ocorre em exceção de rede/timeout real;
            erros HTTP da API (4xx/5xx) agora exibem a mensagem de erro real
            em vez de cair silenciosamente no modo offline.
  - Bug 3: Adicionado diagnóstico de configuração SMTP visível ao admin
            para facilitar depuração quando EMAIL_USERNAME não está configurado.
"""
from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
import streamlit as st
from lib import ui
from lib.auth import require_auth, sidebar_logo, sidebar_user_info, sidebar_logout_button
from lib import components
from lib.config import API_V1, APP_URL, SMTP_USER, SMTP_HOST, SMTP_PORT

# ─── Setup ───────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Convites · HIPNUS", page_icon="📨", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin"])
sidebar_logo()
sidebar_user_info()
sidebar_logout_button()

if "_convites_gerados" not in st.session_state:
    st.session_state["_convites_gerados"] = []


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _gerar_convite_offline(email: str, role: str, criado_por: str) -> dict:
    """
    Gera convite localmente sem depender da API.
    Token UUID4 hex, link de cadastro montado com APP_URL.
    Usado apenas em tab2 (Gerar Convite) ou como fallback de rede.
    """
    token      = uuid.uuid4().hex
    signup_url = f"{APP_URL}/Cadastro_Parceiro?invite={token}"
    expires_at = datetime.utcnow() + timedelta(days=7)
    return {
        "token":      token,
        "email":      email,
        "role":       role,
        "created_by": criado_por,
        "signup_url": signup_url,
        "expires_at": expires_at.strftime("%d/%m/%Y %H:%M") + " UTC",
        "email_sent": False,
        "origem":     "offline",
    }


def _enviar_convite_api(email: str, role: str, token_jwt: str | None) -> tuple[dict | None, str | None]:
    """
    Cria convite via API e dispara envio de e-mail pelo backend (SMTP Hostinger).

    Retorna (resultado_dict, erro_str).
    - Se sucesso (201): retorna (dict, None). email_sent=True quando status==201.
    - Se erro HTTP (4xx/5xx): retorna (None, mensagem_de_erro).
    - Se falha de rede: retorna (None, "API indisponível").

    Correção aplicada:
      Antes, qualquer status != 201 caia silenciosamente em offline.
      Agora, erros HTTP retornam a mensagem real da API para o admin.
      `email_sent` é True sempre que status==201 (backend assume responsabilidade).
    """
    headers = {"Authorization": f"Bearer {token_jwt}"} if token_jwt else {}
    try:
        r = httpx.post(
            f"{API_V1}/invites/",
            json={"email": email, "role": role},
            headers=headers,
            timeout=8.0,
        )
        if r.status_code == 201:
            data = r.json()
            data["origem"]     = "api"
            # FIX: se o backend não retornar email_sent explicitamente,
            # assume True — 201 significa que o backend processou o envio.
            data["email_sent"] = data.get("email_sent", True)
            data["expires_at"] = data.get("expires_at", "")
            return data, None
        else:
            # FIX: expõe o erro real da API em vez de cair em offline silencioso
            try:
                detalhe = r.json().get("detail", r.text)
            except Exception:
                detalhe = r.text
            return None, f"API retornou HTTP {r.status_code}: {detalhe}"
    except httpx.TimeoutException:
        return None, "Timeout ao conectar com a API (> 8s)."
    except httpx.ConnectError:
        return None, "API indisponível — não foi possível conectar."
    except Exception as exc:
        return None, f"Erro inesperado: {exc}"


def _buscar_convites_api(token_jwt: str | None) -> list[dict]:
    """Busca lista de convites da API. Retorna lista vazia se falhar."""
    headers = {"Authorization": f"Bearer {token_jwt}"} if token_jwt else {}
    try:
        r = httpx.get(f"{API_V1}/invites/", headers=headers, timeout=6.0)
        if r.status_code == 200:
            return [{**inv, "origem": "api"} for inv in r.json()]
    except Exception:
        pass
    return []


def _badge_role(role: str) -> str:
    return {"b2b": "🎤 Profissional", "b2c": "👤 Cliente", "admin": "🛡️ Admin"}.get(role, role)


def _badge_origem(origem: str) -> str:
    return "🟢 API" if origem == "api" else "🟡 Offline"


def _card_link(signup_url: str, role: str, criado_por: str, origem: str) -> None:
    """Renderiza card visual com link de cadastro copiável."""
    st.html(f"""
    <div style="background:#f3f0ff;border:1.5px solid #c4b5fd;border-radius:12px;
                padding:18px 20px;margin:12px 0;">
        <div style="font-size:.72rem;font-weight:700;letter-spacing:.8px;
                    text-transform:uppercase;color:#7C3AED;margin-bottom:6px;">
            🔗 Link de cadastro — expira em 7 dias
        </div>
        <div style="font-size:.88rem;color:#1A1430;word-break:break-all;
                    background:#fff;padding:10px 14px;border-radius:8px;
                    border:1px solid #ddd5f8;font-family:monospace;">
            {signup_url}
        </div>
        <div style="font-size:.75rem;color:#6B6580;margin-top:8px;">
            Perfil: <strong>{_badge_role(role)}</strong> &nbsp;·&nbsp;
            Criado por: <strong>{criado_por}</strong> &nbsp;·&nbsp;
            Origem: {_badge_origem(origem)}
        </div>
    </div>
    """)
    st.text_area(
        "Copie o link:",
        value=signup_url,
        height=75,
        help="Selecione e copie (Ctrl+C / Cmd+C)",
        key=f"_copy_{signup_url[-8:]}",
    )


def _aviso_smtp() -> None:
    """Mostra diagnóstico de SMTP quando EMAIL_USERNAME não está configurado."""
    if not SMTP_USER:
        st.html(f"""
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:10px;
                    padding:12px 16px;font-size:.82rem;color:#92400e;margin-top:8px;">
            <strong>⚙️ SMTP não configurado — e-mail automático desabilitado.</strong><br>
            Configure nos Streamlit Secrets:<br>
            <code>[email]</code><br>
            <code>EMAIL_HOST = "{SMTP_HOST}"</code><br>
            <code>EMAIL_PORT = "{SMTP_PORT}"</code><br>
            <code>EMAIL_USERNAME = "seu@email.com"</code><br>
            <code>EMAIL_PASSWORD = "sua_senha"</code><br>
            <code>EMAIL_REMETENTE = "noreply@hipnuscosmeticos.com.br"</code>
        </div>
        """)


# ─── Header ──────────────────────────────────────────────────────────────────
components.page_header(
    title="Convites de Parceiros",
    subtitle="Gerencie convites personalizados para novos distribuidores, salões e parceiros.",
    kicker="Área Admin",
)

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📨 Enviar Convite", "🔗 Gerar Convite", "📋 Monitorar Convites"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ENVIAR CONVITE (via API + SMTP real)
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    components.section_title("Enviar convite por e-mail")
    st.caption(
        "Cria o convite no banco de dados e envia automaticamente para o e-mail do convidado "
        "via SMTP Hostinger configurado no backend."
    )

    _aviso_smtp()

    with st.form("form_enviar_convite", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            email_t1 = st.text_input(
                "E-mail do destinatário",
                placeholder="parceiro@email.com",
            )
        with col2:
            role_t1 = st.selectbox(
                "Perfil do convidado",
                ["b2b", "b2c", "admin"],
                format_func=lambda r: {
                    "b2b": "Profissional / Salão",
                    "b2c": "Cliente Final",
                    "admin": "Administrador",
                }.get(r, r),
                key="role_t1",
            )
        submitted_t1 = st.form_submit_button(
            "📨 Enviar convite por e-mail",
            use_container_width=True,
            type="primary",
        )

    if submitted_t1:
        if not email_t1 or "@" not in email_t1:
            st.error("⚠️ Informe um e-mail válido para o destinatário.")
        else:
            criado_por = usuario.get("login", "admin")
            token_jwt  = st.session_state.get("token")

            with st.spinner("Conectando à API e enviando e-mail..."):
                resultado, erro = _enviar_convite_api(email_t1, role_t1, token_jwt)

            if resultado is not None:
                # Sucesso via API
                st.session_state["_convites_gerados"].insert(0, resultado)
                signup_url = resultado.get("signup_url", "")
                email_sent = resultado.get("email_sent", True)

                if email_sent:
                    st.success(f"✅ Convite enviado por e-mail para **{email_t1}**!")
                else:
                    # API criou o convite mas informou que o e-mail não foi enviado
                    st.warning(
                        "✅ Convite criado no banco de dados, mas o **e-mail não foi disparado**. "
                        "Verifique as variáveis SMTP no backend (VPS Hostinger)."
                    )
                _card_link(signup_url, role_t1, criado_por, "api")

            else:
                # FIX: exibe erro real da API / rede, não cai em offline silencioso
                st.error(f"❌ Falha ao criar convite via API.\n\n**Detalhe:** {erro}")
                st.info(
                    "💡 Se o backend não estiver disponível, use a aba **🔗 Gerar Convite** "
                    "para criar um link offline e enviar manualmente."
                )
                _aviso_smtp()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — GERAR CONVITE (offline / manual)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    components.section_title("Gerar link de convite manual")
    st.caption(
        "Gera um token UUID localmente sem depender do backend. "
        "Copie o link gerado e envie manualmente ao convidado por WhatsApp, e-mail ou outro canal."
    )

    with st.form("form_gerar_convite", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            email_t2 = st.text_input(
                "E-mail do destinatário (para registro)",
                placeholder="parceiro@email.com",
            )
        with col2:
            role_t2 = st.selectbox(
                "Perfil do convidado",
                ["b2b", "b2c", "admin"],
                format_func=lambda r: {
                    "b2b": "Profissional / Salão",
                    "b2c": "Cliente Final",
                    "admin": "Administrador",
                }.get(r, r),
                key="role_t2",
            )
        submitted_t2 = st.form_submit_button(
            "🔗 Gerar link de convite",
            use_container_width=True,
        )

    if submitted_t2:
        if not email_t2 or "@" not in email_t2:
            st.error("⚠️ Informe um e-mail válido para o destinatário.")
        else:
            criado_por = usuario.get("login", "admin")
            resultado  = _gerar_convite_offline(email_t2, role_t2, criado_por)
            st.session_state["_convites_gerados"].insert(0, resultado)

            st.info("📋 Convite gerado localmente. Copie o link abaixo e envie manualmente.")
            _card_link(resultado["signup_url"], role_t2, criado_por, "offline")

            st.html("""
            <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
                        padding:12px 16px;font-size:.82rem;color:#166534;margin-top:4px;">
                <strong>ℹ️ Convite gerado offline:</strong> o token não está salvo no banco de dados.
                Quando o convidado acessar o link, o backend deve validar o token via
                <code>GET /api/v1/invites/{token}</code>. Certifique-se de que o backend
                esteja online no momento do cadastro.
            </div>
            """)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — MONITORAR CONVITES
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    components.section_title("Monitorar convites")

    token_jwt = st.session_state.get("token")

    col_refresh, col_info = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Atualizar lista da API", use_container_width=True):
            with st.spinner("Buscando convites..."):
                convites_api = _buscar_convites_api(token_jwt)
            if convites_api:
                # Mescla sem duplicar tokens
                tokens_existentes = {c.get("token") for c in st.session_state["_convites_gerados"]}
                for inv in convites_api:
                    if inv.get("token") not in tokens_existentes:
                        st.session_state["_convites_gerados"].append(inv)
                st.success(f"✅ {len(convites_api)} convite(s) carregado(s) da API.")
            else:
                st.info("API sem convites registrados ou indisponível.")

    convites = st.session_state.get("_convites_gerados", [])

    if not convites:
        components.empty_state(
            icon="📨",
            title="Nenhum convite registrado",
            message="Use as abas 'Enviar Convite' ou 'Gerar Convite' para criar o primeiro convite, "
                    "ou clique em 'Atualizar lista da API' para carregar convites existentes.",
        )
    else:
        # Métricas rápidas
        total     = len(convites)
        usados    = sum(1 for c in convites if c.get("used"))
        pendentes = total - usados
        api_count = sum(1 for c in convites if c.get("origem") == "api")
        offline_c = total - api_count

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", total)
        m2.metric("Pendentes", pendentes)
        m3.metric("Usados", usados)
        m4.metric("Via API / Offline", f"{api_count} / {offline_c}")

        components.divider()

        for inv in convites:
            email_inv  = inv.get("email", "N/A")
            role_inv   = inv.get("role", "b2b")
            usado      = inv.get("used", False)
            origem_inv = inv.get("origem", "offline")
            status_str = "✅ Usado" if usado else "⏳ Pendente"
            expira     = inv.get("expires_at", "—")
            url_inv    = inv.get("signup_url", "")
            email_sent = inv.get("email_sent", False)

            label = (
                f"{email_inv}  —  {status_str}  ·  {_badge_role(role_inv)}  ·  {_badge_origem(origem_inv)}"
            )
            with st.expander(label):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Perfil:** {_badge_role(role_inv)}")
                    st.markdown(f"**Status:** {status_str}")
                    st.markdown(f"**Expira em:** {expira}")
                    st.markdown(f"**Origem:** {_badge_origem(origem_inv)}")
                    st.markdown(f"**E-mail enviado:** {'✅ Sim' if email_sent else '❌ Não'}")
                with col_b:
                    st.markdown(f"**Token:** `{inv.get('token', 'N/A')}`")
                    if url_inv:
                        st.markdown("**Link de cadastro:**")
                        st.code(url_inv, language=None)
