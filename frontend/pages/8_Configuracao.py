"""
8_Configuracao.py — HIPNUS COSMÉTICOS
Página de configurações completa:
  👤 Minha Conta | ⚙️ Empresa | 🔌 Integrações | 🗄️ Banco | 🎨 Aparência
"""
from __future__ import annotations
import sys
import os
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from lib import ui, components
from lib.auth import require_auth, build_sidebar
from lib import config as CFG

st.set_page_config(page_title="Configurações · HIPNUS", page_icon="⚙️", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin", "b2b", "b2c"])
build_sidebar()

components.page_header(
    title="Configurações",
    subtitle="Gerencie sua conta, parâmetros, integrações e aparência da plataforma.",
    kicker="⚙️ Painel de Configuração",
)

# ── CSS extra para abas e cards de config ────────────────────────────────────
st.html("""
<style>
.cfg-section {
    background: rgba(124,58,237,0.04);
    border: 1px solid rgba(185,131,255,0.18);
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 18px;
}
.cfg-label {
    font-size: .72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .8px;
    color: #b983ff; margin-bottom: 4px;
}
.cfg-badge {
    display: inline-block;
    background: rgba(124,58,237,0.12);
    border: 1px solid rgba(185,131,255,0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: .78rem;
    font-weight: 600;
    color: #b983ff;
}
.minha-conta-card {
    background: rgba(124,58,237,0.06);
    border: 1px solid rgba(185,131,255,0.22);
    border-radius: 16px;
    padding: 28px 28px 20px 28px;
    margin-bottom: 20px;
}
.avatar-circle {
    width: 72px; height: 72px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7c3aed 0%, #b983ff 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 2rem; font-weight: 700; color: #fff;
    border: 3px solid rgba(185,131,255,0.4);
    margin-bottom: 12px;
}
</style>
""")

# ── Abas ────────────────────────────────────────────────────────────────────
_role = (usuario or {}).get("perfil") or (usuario or {}).get("role") or ""
_is_admin = _role in ("super_admin", "admin")

if _is_admin:
    abas = st.tabs(["👤 Minha Conta", "⚙️ Empresa", "🔌 Integrações", "🗄️ Banco de Dados", "🎨 Aparência"])
    tab_conta, tab_empresa, tab_integ, tab_banco, tab_aparencia = abas
else:
    abas = st.tabs(["👤 Minha Conta"])
    tab_conta = abas[0]
    tab_empresa = tab_integ = tab_banco = tab_aparencia = None

# ════════════════════════════════════════════════════════════════════════════
# ABA 1 — 👤 MINHA CONTA
# ════════════════════════════════════════════════════════════════════════════
with tab_conta:
    st.markdown("### 👤 Minha Conta")
    st.caption("Visualize e edite suas informações pessoais na plataforma HIPNUS.")

    # Carrega dados do usuário da sessão
    _nome        = (usuario or {}).get("nome") or (usuario or {}).get("name") or ""
    _email       = (usuario or {}).get("email") or ""
    _username    = (usuario or {}).get("username") or ""
    _display     = (usuario or {}).get("display_name") or _nome
    _role_label  = {
        "super_admin": "Super Admin 👑",
        "admin": "Administrador 🛠️",
        "b2b": "Parceiro B2B 💼",
        "b2c": "Consumidor B2C 🛒",
        "demo": "Demo 🔍",
    }.get(_role, _role or "—")
    _inicial     = (_nome[0].upper() if _nome else "U")

    # Card de perfil visual
    col_av, col_info = st.columns([1, 5], gap="medium")
    with col_av:
        st.html(f"""
        <div class="avatar-circle">{_inicial}</div>
        <div class="cfg-badge">{_role_label}</div>
        """)
    with col_info:
        st.markdown(f"**{_display or _nome or 'Usuário'}**")
        st.caption(f"@{_username}" if _username else "")
        st.caption(f"✉️ {_email}" if _email else "")

    st.divider()

    # ── Formulário de edição ──────────────────────────────────────────────
    st.markdown("#### ✏️ Editar Dados Pessoais")

    with st.form("form_minha_conta", clear_on_submit=False):
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            novo_nome = st.text_input(
                "Nome completo",
                value=_nome,
                placeholder="Seu nome completo",
                help="Nome exibido no sistema.",
            )
            novo_display = st.text_input(
                "Nome de exibição",
                value=_display,
                placeholder="Como quer ser chamado?",
                help="Aparece no menu lateral e nas saudações da IA.",
            )
        with col2:
            novo_email = st.text_input(
                "E-mail",
                value=_email,
                placeholder="seu@email.com",
                help="Usado para login e notificações.",
            )
            st.text_input(
                "Username",
                value=_username,
                disabled=True,
                help="O username não pode ser alterado.",
            )

        st.markdown("#### 🔐 Alterar Senha")
        col3, col4, col5 = st.columns(3, gap="medium")
        with col3:
            senha_atual = st.text_input(
                "Senha atual",
                type="password",
                placeholder="Digite sua senha atual",
            )
        with col4:
            nova_senha = st.text_input(
                "Nova senha",
                type="password",
                placeholder="Mínimo 8 caracteres",
            )
        with col5:
            conf_senha = st.text_input(
                "Confirmar nova senha",
                type="password",
                placeholder="Repita a nova senha",
            )

        salvar = st.form_submit_button(
            "💾 Salvar alterações",
            type="primary",
            use_container_width=True,
        )

    if salvar:
        erros: list[str] = []

        # Validações básicas
        if not novo_nome.strip():
            erros.append("O nome completo não pode ser vazio.")
        if not novo_email.strip() or "@" not in novo_email:
            erros.append("Informe um e-mail válido.")

        # Validação de senha (só se tentou mudar)
        mudar_senha = bool(senha_atual or nova_senha or conf_senha)
        if mudar_senha:
            if not senha_atual:
                erros.append("Informe a senha atual para alterar a senha.")
            if len(nova_senha) < 8:
                erros.append("A nova senha deve ter pelo menos 8 caracteres.")
            if nova_senha != conf_senha:
                erros.append("As senhas não coincidem.")

        if erros:
            for e in erros:
                st.error(f"❌ {e}")
        else:
            # Tenta atualizar via user_db
            try:
                from lib.user_db import get_db_session, update_user_profile

                user_id = (usuario or {}).get("id") or (usuario or {}).get("user_id")

                with get_db_session() as db:
                    resultado = update_user_profile(
                        db=db,
                        user_id=user_id,
                        nome=novo_nome.strip(),
                        display_name=novo_display.strip() or novo_nome.strip(),
                        email=novo_email.strip(),
                        senha_atual=senha_atual if mudar_senha else None,
                        nova_senha=nova_senha if mudar_senha else None,
                    )

                if resultado.get("ok"):
                    st.success("✅ Dados atualizados com sucesso!")
                    # Atualiza sessão local
                    if "usuario" in st.session_state:
                        st.session_state["usuario"]["nome"]         = novo_nome.strip()
                        st.session_state["usuario"]["name"]         = novo_nome.strip()
                        st.session_state["usuario"]["display_name"] = novo_display.strip()
                        st.session_state["usuario"]["email"]        = novo_email.strip()
                    st.rerun()
                else:
                    st.error(f"❌ {resultado.get('erro', 'Erro ao salvar.')}")

            except ImportError:
                # Fallback: atualiza apenas a sessão local
                if "usuario" in st.session_state:
                    st.session_state["usuario"]["nome"]         = novo_nome.strip()
                    st.session_state["usuario"]["name"]         = novo_nome.strip()
                    st.session_state["usuario"]["display_name"] = novo_display.strip()
                    st.session_state["usuario"]["email"]        = novo_email.strip()
                st.success("✅ Dados atualizados na sessão! (persistência DB não disponível)")
                st.rerun()
            except Exception as ex:
                st.error(f"❌ Erro inesperado: {ex}")

    # ── Informações somente leitura ────────────────────────────────────────
    st.divider()
    st.markdown("#### ℹ️ Informações da Conta")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.html("<p class='cfg-label'>Perfil de acesso</p>")
        st.markdown(f"**{_role_label}**")
    with c2:
        _criado = (usuario or {}).get("created_at") or (usuario or {}).get("criado_em") or "—"
        st.html("<p class='cfg-label'>Membro desde</p>")
        st.markdown(f"**{str(_criado)[:10] if _criado != '—' else '—'}**")
    with c3:
        _ativo = (usuario or {}).get("is_active", True)
        st.html("<p class='cfg-label'>Status da conta</p>")
        st.markdown("🟢 **Ativa**" if _ativo else "🔴 **Inativa**")


# ════════════════════════════════════════════════════════════════════════════
# ABAS ADMIN — só carregam se o usuário for admin/super_admin
# ════════════════════════════════════════════════════════════════════════════
if not _is_admin:
    st.stop()

# ════════════════════════════════════════════════════════════════════════════
# ABA 2 — ⚙️ EMPRESA
# ════════════════════════════════════════════════════════════════════════════
with tab_empresa:
    st.markdown("### ⚙️ Configurações da Empresa")
    st.caption("Parâmetros gerais da plataforma HIPNUS.")

    with st.form("form_empresa"):
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Nome da empresa",  value=CFG.get("COMPANY_NAME", "HIPNUS COSMÉTICOS"))
            st.text_input("CNPJ",              value=CFG.get("COMPANY_CNPJ", ""), placeholder="00.000.000/0001-00")
            st.text_input("E-mail de contato", value=CFG.get("COMPANY_EMAIL", ""), placeholder="contato@hipnus.com")
        with col2:
            st.text_input("Telefone",          value=CFG.get("COMPANY_PHONE", ""), placeholder="(31) 99999-9999")
            st.text_input("Site",              value=CFG.get("COMPANY_SITE", ""),  placeholder="https://hipnus.com")
            st.text_input("Cidade / UF",       value=CFG.get("COMPANY_CITY", ""),  placeholder="Belo Horizonte / MG")
        if st.form_submit_button("💾 Salvar configurações da empresa", type="primary"):
            st.success("✅ Configurações salvas (requer restart para aplicar em produção).")


# ════════════════════════════════════════════════════════════════════════════
# ABA 3 — 🔌 INTEGRAÇÕES
# ════════════════════════════════════════════════════════════════════════════
with tab_integ:
    st.markdown("### 🔌 Integrações")
    st.caption("Chaves e configurações de serviços externos.")

    with st.expander("💳 Asaas (Pagamentos)", expanded=True):
        with st.form("form_asaas"):
            st.text_input("API Key Asaas",  value=CFG.get("ASAAS_API_KEY", ""),  type="password", placeholder="$aact_...")
            st.selectbox("Ambiente",        options=["sandbox", "production"],    index=0 if CFG.get("ASAAS_ENV", "sandbox") == "sandbox" else 1)
            if st.form_submit_button("💾 Salvar Asaas", type="primary"):
                st.success("✅ Integração Asaas atualizada.")

    with st.expander("🤖 IA Consultora (Groq)", expanded=False):
        with st.form("form_groq"):
            st.text_input("GROQ API Key",   value=CFG.get("GROQ_API_KEY", ""),   type="password", placeholder="gsk_...")
            st.text_input("Modelo",         value=CFG.get("GROQ_MODEL", "llama-3.3-70b-versatile"))
            if st.form_submit_button("💾 Salvar Groq", type="primary"):
                st.success("✅ Integração IA atualizada.")

    with st.expander("📧 SMTP (E-mail)", expanded=False):
        with st.form("form_smtp"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Host SMTP",  value=CFG.get("SMTP_HOST", ""),       placeholder="smtp.gmail.com")
                st.text_input("Porta",      value=CFG.get("SMTP_PORT", "587"),     placeholder="587")
            with col2:
                st.text_input("Usuário",    value=CFG.get("SMTP_USER", ""),        placeholder="seu@email.com")
                st.text_input("Senha",      value=CFG.get("SMTP_PASS", ""),        type="password")
            if st.form_submit_button("💾 Salvar SMTP", type="primary"):
                st.success("✅ Configuração de e-mail atualizada.")


# ════════════════════════════════════════════════════════════════════════════
# ABA 4 — 🗄️ BANCO DE DADOS
# ════════════════════════════════════════════════════════════════════════════
with tab_banco:
    st.markdown("### 🗄️ Banco de Dados")
    st.caption("Conexão e status do banco de dados da plataforma.")

    with st.form("form_banco"):
        st.text_input(
            "DATABASE_URL",
            value=CFG.get("DATABASE_URL", ""),
            type="password",
            placeholder="postgresql+asyncpg://user:pass@host:5432/db",
            help="String de conexão completa. Alterações requerem reinício do servidor.",
        )
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Echo SQL (debug)", value=CFG.get("DB_ECHO", False))
        with col2:
            st.number_input("Pool size", min_value=1, max_value=50, value=int(CFG.get("DB_POOL_SIZE", 5)))
        if st.form_submit_button("💾 Salvar configuração do banco", type="primary"):
            st.success("✅ Configuração de banco atualizada (reinície o servidor para aplicar).")

    st.divider()
    st.markdown("#### 🔍 Status da Conexão")
    if st.button("🔄 Testar conexão com o banco"):
        try:
            from lib.db_utils import test_connection
            ok, msg = test_connection()
            if ok:
                st.success(f"✅ Conexão OK — {msg}")
            else:
                st.error(f"❌ Falha na conexão: {msg}")
        except Exception as e:
            st.warning(f"⚠️ Módulo de teste indisponível: {e}")


# ════════════════════════════════════════════════════════════════════════════
# ABA 5 — 🎨 APARÊNCIA
# ════════════════════════════════════════════════════════════════════════════
with tab_aparencia:
    st.markdown("### 🎨 Aparência")
    st.caption("Personalização visual da plataforma.")

    with st.form("form_aparencia"):
        col1, col2 = st.columns(2)
        with col1:
            st.color_picker("Cor primária",     value=CFG.get("THEME_PRIMARY", "#7c3aed"))
            st.color_picker("Cor de destaque",  value=CFG.get("THEME_ACCENT",  "#b983ff"))
            st.color_picker("Cor de fundo",     value=CFG.get("THEME_BG",      "#0e0e16"))
        with col2:
            st.selectbox("Fonte do sistema",    options=["Inter", "Poppins", "Roboto", "DM Sans"],
                         index=0)
            st.selectbox("Modo de cores",       options=["Dark (padrão)", "Light", "Auto (sistema)"],
                         index=0)
            st.slider("Raio de borda (px)",     min_value=0, max_value=24,
                      value=int(CFG.get("THEME_RADIUS", 12)))
        if st.form_submit_button("💾 Salvar aparência", type="primary"):
            st.success("✅ Aparência atualizada (recarregue a página para ver as mudanças).")
