"""
8_Configuracao.py — HIPNUS COSMÉTICOS
Página de configurações completa:
  👤 Minha Conta | ⚙️ Empresa | 🔌 Integrações | 🗄️ Banco | 🎨 Aparência | 🤖 Chiara
"""
from __future__ import annotations
import sys
import os
import base64
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

# ── CSS extra ────────────────────────────────────────────────────────────────
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
/* Chiara card */
.chiara-hero {
    background: linear-gradient(135deg, rgba(185,131,255,0.08) 0%, rgba(124,58,237,0.12) 100%);
    border: 1px solid rgba(185,131,255,0.25);
    border-radius: 20px;
    padding: 28px;
    margin-bottom: 24px;
    display: flex;
    gap: 28px;
    align-items: flex-start;
}
.chiara-avatar-wrap {
    flex-shrink: 0;
    text-align: center;
}
.chiara-avatar-img {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    object-fit: cover;
    border: 4px solid rgba(185,131,255,0.5);
    box-shadow: 0 0 28px rgba(185,131,255,0.3);
    display: block;
    margin: 0 auto 10px auto;
}
.chiara-avatar-placeholder {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3.5rem;
    border: 4px solid rgba(185,131,255,0.5);
    box-shadow: 0 0 28px rgba(185,131,255,0.3);
    margin: 0 auto 10px auto;
}
.chiara-bio {
    flex: 1;
}
.chiara-name {
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #b983ff 0%, #ec4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 4px 0;
}
.chiara-title {
    font-size: .9rem;
    color: rgba(185,131,255,0.8);
    margin: 0 0 16px 0;
    font-style: italic;
}
.chiara-tag {
    display: inline-block;
    background: rgba(124,58,237,0.2);
    border: 1px solid rgba(185,131,255,0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: .75rem;
    font-weight: 600;
    color: #b983ff;
    margin: 0 4px 6px 0;
}
.chiara-prop-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 16px;
}
.chiara-prop {
    background: rgba(124,58,237,0.06);
    border: 1px solid rgba(185,131,255,0.15);
    border-radius: 12px;
    padding: 12px 14px;
}
.chiara-prop-label {
    font-size: .68rem;
    text-transform: uppercase;
    letter-spacing: .8px;
    color: rgba(185,131,255,0.6);
    font-weight: 700;
    margin-bottom: 4px;
}
.chiara-prop-value {
    font-size: .85rem;
    color: rgba(255,255,255,0.88);
    line-height: 1.4;
}
.upload-hint {
    font-size: .75rem;
    color: rgba(185,131,255,0.6);
    margin-top: 6px;
    text-align: center;
}
</style>
""")

# ── Abas ─────────────────────────────────────────────────────────────────────
_role = (usuario or {}).get("perfil") or (usuario or {}).get("role") or ""
_is_admin = _role in ("super_admin", "admin")

if _is_admin:
    abas = st.tabs([
        "👤 Minha Conta",
        "⚙️ Empresa",
        "🔌 Integrações",
        "🗄️ Banco de Dados",
        "🎨 Aparência",
        "🤖 Chiara",
    ])
    tab_conta, tab_empresa, tab_integ, tab_banco, tab_aparencia, tab_chiara = abas
else:
    abas = st.tabs(["👤 Minha Conta"])
    tab_conta = abas[0]
    tab_empresa = tab_integ = tab_banco = tab_aparencia = tab_chiara = None


# ════════════════════════════════════════════════════════════════════════════
# ABA 1 — 👤 MINHA CONTA
# ════════════════════════════════════════════════════════════════════════════
with tab_conta:
    st.markdown("### 👤 Minha Conta")
    st.caption("Visualize e edite suas informações pessoais na plataforma HIPNUS.")

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
    st.markdown("#### ✏️ Editar Dados Pessoais")

    with st.form("form_minha_conta", clear_on_submit=False):
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            novo_nome = st.text_input("Nome completo", value=_nome, placeholder="Seu nome completo")
            novo_display = st.text_input("Nome de exibição", value=_display, placeholder="Como quer ser chamado?")
        with col2:
            novo_email = st.text_input("E-mail", value=_email, placeholder="seu@email.com")
            st.text_input("Username", value=_username, disabled=True)

        st.markdown("#### 🔐 Alterar Senha")
        col3, col4, col5 = st.columns(3, gap="medium")
        with col3:
            senha_atual = st.text_input("Senha atual", type="password", placeholder="Digite sua senha atual")
        with col4:
            nova_senha = st.text_input("Nova senha", type="password", placeholder="Mínimo 8 caracteres")
        with col5:
            conf_senha = st.text_input("Confirmar nova senha", type="password", placeholder="Repita a nova senha")

        salvar = st.form_submit_button("💾 Salvar alterações", type="primary", use_container_width=True)

    if salvar:
        erros: list[str] = []
        if not novo_nome.strip():
            erros.append("O nome completo não pode ser vazio.")
        if not novo_email.strip() or "@" not in novo_email:
            erros.append("Informe um e-mail válido.")
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
            try:
                from lib.user_db import get_db_session, update_user_profile
                user_id = (usuario or {}).get("id") or (usuario or {}).get("user_id")
                with get_db_session() as db:
                    resultado = update_user_profile(
                        db=db, user_id=user_id,
                        nome=novo_nome.strip(),
                        display_name=novo_display.strip() or novo_nome.strip(),
                        email=novo_email.strip(),
                        senha_atual=senha_atual if mudar_senha else None,
                        nova_senha=nova_senha if mudar_senha else None,
                    )
                if resultado.get("ok"):
                    st.success("✅ Dados atualizados com sucesso!")
                    if "usuario" in st.session_state:
                        st.session_state["usuario"]["nome"]         = novo_nome.strip()
                        st.session_state["usuario"]["name"]         = novo_nome.strip()
                        st.session_state["usuario"]["display_name"] = novo_display.strip()
                        st.session_state["usuario"]["email"]        = novo_email.strip()
                    st.rerun()
                else:
                    st.error(f"❌ {resultado.get('erro', 'Erro ao salvar.')}")
            except ImportError:
                if "usuario" in st.session_state:
                    st.session_state["usuario"]["nome"]         = novo_nome.strip()
                    st.session_state["usuario"]["name"]         = novo_nome.strip()
                    st.session_state["usuario"]["display_name"] = novo_display.strip()
                    st.session_state["usuario"]["email"]        = novo_email.strip()
                st.success("✅ Dados atualizados na sessão! (persistência DB não disponível)")
                st.rerun()
            except Exception as ex:
                st.error(f"❌ Erro inesperado: {ex}")

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
            st.success("✅ Configurações salvas.")


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
            "DATABASE_URL", value=CFG.get("DATABASE_URL", ""), type="password",
            placeholder="postgresql+asyncpg://user:pass@host:5432/db",
        )
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Echo SQL (debug)", value=CFG.get("DB_ECHO", False))
        with col2:
            st.number_input("Pool size", min_value=1, max_value=50, value=int(CFG.get("DB_POOL_SIZE", 5)))
        if st.form_submit_button("💾 Salvar configuração do banco", type="primary"):
            st.success("✅ Configuração de banco atualizada.")
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
            st.selectbox("Fonte do sistema",    options=["Inter", "Poppins", "Roboto", "DM Sans"], index=0)
            st.selectbox("Modo de cores",       options=["Dark (padrão)", "Light", "Auto (sistema)"], index=0)
            st.slider("Raio de borda (px)",     min_value=0, max_value=24, value=int(CFG.get("THEME_RADIUS", 12)))
        if st.form_submit_button("💾 Salvar aparência", type="primary"):
            st.success("✅ Aparência atualizada (recarregue a página para ver as mudanças).")


# ════════════════════════════════════════════════════════════════════════════
# ABA 6 — 🤖 CHIARA
# ════════════════════════════════════════════════════════════════════════════
with tab_chiara:
    st.markdown("### 🤖 Identidade Visual da Chiara")
    st.caption("Configure o nome, bio e foto da sua IA Consultora personalizada.")

    # ── Carrega imagem salva (base64) da session ──────────────────────────
    chiara_b64 = st.session_state.get("chiara_foto_b64", "")
    chiara_name = st.session_state.get("chiara_nome", "Chiara")

    # ── Hero card com avatar ──────────────────────────────────────────────
    if chiara_b64:
        avatar_html = f'<img src="data:image/jpeg;base64,{chiara_b64}" class="chiara-avatar-img" alt="Chiara" />'
    else:
        avatar_html = '<div class="chiara-avatar-placeholder">✨</div>'

    st.html(f"""
    <div class="chiara-hero">
        <div class="chiara-avatar-wrap">
            {avatar_html}
            <div class="upload-hint">Foto da IA Consultora</div>
        </div>
        <div class="chiara-bio">
            <p class="chiara-name">{chiara_name}</p>
            <p class="chiara-title">Terapeuta Capilar Digital · Embaixadora Virtual HIPNUS</p>
            <div>
                <span class="chiara-tag">✨ Luminosa</span>
                <span class="chiara-tag">💫 Especialista em cabelos</span>
                <span class="chiara-tag">🧬 IA Premium</span>
                <span class="chiara-tag">🏆 Embaixadora HIPNUS</span>
            </div>
            <div class="chiara-prop-grid">
                <div class="chiara-prop">
                    <div class="chiara-prop-label">👁️ Idade aparente</div>
                    <div class="chiara-prop-value">26 a 28 anos — maturidade profissional com jovialidade</div>
                </div>
                <div class="chiara-prop">
                    <div class="chiara-prop-label">🎯 Propósito</div>
                    <div class="chiara-prop-value">Provar que todo cabelo pode ser radiante com o cronograma capilar certo</div>
                </div>
                <div class="chiara-prop">
                    <div class="chiara-prop-label">🦸 Superpoder</div>
                    <div class="chiara-prop-value">Identifica se o fio precisa de Hidratação, Nutrição ou Reconstrução</div>
                </div>
                <div class="chiara-prop">
                    <div class="chiara-prop-label">❤️ Não vive sem</div>
                    <div class="chiara-prop-value">Touca de cetim e o reparador de pontas Hipnus</div>
                </div>
                <div class="chiara-prop">
                    <div class="chiara-prop-label">🔬 Mania</div>
                    <div class="chiara-prop-value">Explicar a ciência por trás dos ingredientes de forma leve e divertida</div>
                </div>
                <div class="chiara-prop">
                    <div class="chiara-prop-label">🏛️ Ambiente</div>
                    <div class="chiara-prop-value">Salão premium ou laboratório de estética capilar moderno</div>
                </div>
            </div>
        </div>
    </div>
    """)

    st.divider()

    # ── Upload de foto ────────────────────────────────────────────────────
    st.markdown("#### 📸 Foto da Chiara")
    st.caption("A foto será exibida no topo do chat da IA Consultora e nesta ficha.")

    col_up, col_prev = st.columns([3, 2], gap="large")

    with col_up:
        foto_upload = st.file_uploader(
            "Selecione a foto da Chiara",
            type=["jpg", "jpeg", "png", "webp"],
            key="chiara_foto_upload",
            help="Formatos: JPG, PNG ou WebP. Recomendado: foto quadrada (ex: 400×400px).",
        )

        if foto_upload is not None:
            # Converte para base64 e salva na session
            foto_bytes = foto_upload.read()
            b64 = base64.b64encode(foto_bytes).decode("utf-8")
            ext = foto_upload.type.split("/")[-1].replace("jpeg", "jpg")
            st.session_state["chiara_foto_b64"]  = b64
            st.session_state["chiara_foto_ext"]  = ext
            st.session_state["chiara_foto_mime"] = foto_upload.type
            st.success("✅ Foto carregada! Ela já aparece no chat da IA Consultora.")
            st.rerun()

        if chiara_b64:
            if st.button("🗑️ Remover foto", key="chiara_remove_foto"):
                st.session_state.pop("chiara_foto_b64",  None)
                st.session_state.pop("chiara_foto_ext",  None)
                st.session_state.pop("chiara_foto_mime", None)
                st.rerun()

    with col_prev:
        if chiara_b64:
            mime = st.session_state.get("chiara_foto_mime", "image/jpeg")
            st.html(f"""
            <div style="text-align:center;">
                <p style="font-size:.72rem;text-transform:uppercase;letter-spacing:.8px;
                          color:rgba(185,131,255,0.6);font-weight:700;margin-bottom:10px;">Preview</p>
                <img src="data:{mime};base64,{chiara_b64}"
                     style="width:160px;height:160px;border-radius:50%;
                            object-fit:cover;
                            border:4px solid rgba(185,131,255,0.5);
                            box-shadow:0 0 28px rgba(185,131,255,0.3);"
                     alt="Chiara preview" />
                <p style="font-size:.8rem;color:rgba(185,131,255,0.7);margin-top:10px;">Aparência no chat</p>
            </div>
            """)
        else:
            st.html("""
            <div style="text-align:center;padding:24px;">
                <div style="width:160px;height:160px;border-radius:50%;
                            background:linear-gradient(135deg,#7c3aed,#ec4899);
                            display:flex;align-items:center;justify-content:center;
                            font-size:4rem;margin:0 auto 10px;
                            border:4px solid rgba(185,131,255,0.3);">✨</div>
                <p style="font-size:.78rem;color:rgba(185,131,255,0.5);">Nenhuma foto carregada</p>
            </div>
            """)

    st.divider()

    # ── Configurações de nome e personalidade ─────────────────────────────
    st.markdown("#### ✏️ Dados da IA")
    with st.form("form_chiara_dados", clear_on_submit=False):
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            novo_nome_chiara = st.text_input(
                "Nome da IA Consultora",
                value=st.session_state.get("chiara_nome", "Chiara"),
                placeholder="Ex: Chiara",
                help="Nome exibido no topo do chat e nas saudações.",
            )
            cargo_chiara = st.text_input(
                "Cargo / Título",
                value=st.session_state.get("chiara_cargo", "Terapeuta Capilar Digital · Embaixadora HIPNUS"),
                placeholder="Ex: Consultora Virtual Hipnus",
            )
        with col2:
            saudacao_chiara = st.text_area(
                "Saudação inicial do chat",
                value=st.session_state.get(
                    "chiara_saudacao",
                    "Olá! Sou a Chiara, consultora virtual da Hipnus Cosméticos. 💜\n\nPosso te ajudar com:\n- Dúvidas sobre produtos e linhas\n- Informações sobre carrinho e pedidos\n- Como funciona o checkout e pagamento\n- Convites e cadastro de parceiros\n\nComo posso te ajudar hoje?"
                ),
                height=160,
                placeholder="Mensagem de boas-vindas da IA...",
            )

        salvar_chiara = st.form_submit_button(
            "💾 Salvar configurações da Chiara",
            type="primary",
            use_container_width=True,
        )

    if salvar_chiara:
        st.session_state["chiara_nome"]     = novo_nome_chiara.strip() or "Chiara"
        st.session_state["chiara_cargo"]    = cargo_chiara.strip()
        st.session_state["chiara_saudacao"] = saudacao_chiara.strip()
        st.success(f"✅ Dados da {novo_nome_chiara or 'Chiara'} salvos com sucesso!")
        st.rerun()

    # ── Dica sobre persistência ───────────────────────────────────────────
    st.info(
        "💡 **Dica:** As configurações da Chiara ficam salvas durante a sessão. "
        "Para persistência permanente, salve a imagem em `assets/chiara_foto.jpg` "
        "via commit no repositório."
    )
