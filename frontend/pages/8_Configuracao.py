"""
8_Configuracao.py — HIPNUS COSMÉTICOS
Painel de configurações para admin/super_admin.
Corrigido 2026-06-29: fotos da Chiara e do usuário agora são persistidas
no banco SQLite via user_db.salvar_foto_chiara() e user_db.atualizar_perfil().
Assim as imagens sobrevivem a logout/login e reinicializações do Streamlit.
"""
from __future__ import annotations
import sys, base64, hashlib
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from lib import ui
from lib.auth import require_auth, build_sidebar

st.set_page_config(page_title="Configurações · HIPNUS", page_icon="⚙️", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin"])
build_sidebar()

# ── Imports do banco ─────────────────────────────────────────────────────────
try:
    from lib.user_db import (
        atualizar_perfil, alterar_senha, buscar_por_email,
        salvar_foto_chiara, salvar_nome_chiara, carregar_config_chiara,
        set_app_config, get_app_config,
    )
    DB_OK = True
except Exception:
    DB_OK = False


# ─────────────────────────────────────────────────────────────────────────────
# ABA: MINHA CONTA
# ─────────────────────────────────────────────────────────────────────────────
def _tab_minha_conta():
    perfil      = st.session_state.get("perfil", "demo")
    nome        = st.session_state.get("nome", "")
    display_nm  = st.session_state.get("display_name", "") or nome
    email       = st.session_state.get("email", "")
    avatar_b64  = st.session_state.get("avatar_b64", "")

    badge_map = {
        "super_admin": ("Super Admin 🌟", "#7c3aed"),
        "admin":       ("Admin 🛡️",       "#2563eb"),
        "b2b":         ("Parceiro B2B 💼", "#059669"),
        "b2c":         ("Consumidor B2C 🛒","#d97706"),
        "demo":        ("Demo 👀",          "#6b7280"),
    }
    badge_label, badge_color = badge_map.get(perfil, (perfil.upper(), "#6b7280"))
    initial = (display_nm or "U")[0].upper()

    # Avatar card
    if avatar_b64:
        # Normaliza: aceita tanto base64 puro quanto data-uri completa
        src = avatar_b64 if avatar_b64.startswith("data:") else f"data:image/jpeg;base64,{avatar_b64}"
        st.html(f"""
        <div style="display:flex;flex-direction:column;align-items:center;padding:24px 0 16px;">
          <img src="{src}" style="width:100px;height:100px;border-radius:50%;
            object-fit:cover;border:3px solid {badge_color};box-shadow:0 0 20px {badge_color}44;" />
          <div style="margin-top:12px;font-size:1.1rem;font-weight:700;color:#fff;">{display_nm}</div>
          <div style="margin-top:6px;padding:3px 14px;border-radius:999px;
            background:{badge_color}33;color:{badge_color};font-size:.75rem;font-weight:700;
            letter-spacing:.8px;text-transform:uppercase;">{badge_label}</div>
        </div>""")
    else:
        st.html(f"""
        <div style="display:flex;flex-direction:column;align-items:center;padding:24px 0 16px;">
          <div style="width:100px;height:100px;border-radius:50%;
            background:linear-gradient(135deg,{badge_color},{badge_color}88);
            border:3px solid {badge_color};box-shadow:0 0 20px {badge_color}44;
            display:flex;align-items:center;justify-content:center;
            font-size:2.5rem;font-weight:800;color:#fff;">{initial}</div>
          <div style="margin-top:12px;font-size:1.1rem;font-weight:700;color:#fff;">{display_nm}</div>
          <div style="margin-top:6px;padding:3px 14px;border-radius:999px;
            background:{badge_color}33;color:{badge_color};font-size:.75rem;font-weight:700;
            letter-spacing:.8px;text-transform:uppercase;">{badge_label}</div>
        </div>""")

    st.divider()

    # Upload avatar do usuário
    st.markdown("##### 📷 Foto de perfil")
    foto_up = st.file_uploader(
        "Enviar nova foto (JPG/PNG, máx 2 MB)",
        type=["jpg", "jpeg", "png", "webp"],
        key="conta_avatar_upload",
    )
    if foto_up:
        foto_bytes = foto_up.read()
        novo_hash  = hashlib.md5(foto_bytes).hexdigest()
        if novo_hash != st.session_state.get("_avatar_upload_hash"):
            mime  = foto_up.type or "image/jpeg"
            b64   = base64.b64encode(foto_bytes).decode()
            # Persiste no banco SE for parceiro com e-mail
            if DB_OK and email:
                atualizar_perfil(email=email, avatar_b64=b64)
            # Atualiza session_state
            st.session_state["avatar_b64"]         = b64
            st.session_state["_avatar_upload_hash"] = novo_hash
            st.session_state["_avatar_loaded"]      = True
            st.success("✅ Foto de perfil atualizada!")
            st.rerun()

    st.divider()

    # Editar dados
    st.markdown("##### ✏️ Editar dados")
    with st.form("form_conta"):
        novo_nome    = st.text_input("Nome completo",   value=nome)
        novo_display = st.text_input("Nome de exibição", value=display_nm)
        novo_email   = st.text_input("E-mail",           value=email, disabled=True,
                                      help="O e-mail não pode ser alterado")
        if st.form_submit_button("💾 Salvar", use_container_width=True):
            if DB_OK and email:
                atualizar_perfil(
                    email=email,
                    nome=novo_nome or nome,
                    username=novo_display or display_nm,
                )
            st.session_state["nome"]         = novo_nome or nome
            st.session_state["display_name"] = novo_display or display_nm
            st.success("✅ Dados atualizados!")
            st.rerun()

    st.divider()

    # Trocar senha
    st.markdown("##### 🔒 Trocar senha")
    with st.form("form_senha"):
        senha_atual  = st.text_input("Senha atual",         type="password")
        nova_senha   = st.text_input("Nova senha",           type="password")
        conf_senha   = st.text_input("Confirmar nova senha", type="password")
        if st.form_submit_button("🔑 Alterar senha", use_container_width=True):
            if not senha_atual or not nova_senha:
                st.error("Preencha todos os campos.")
            elif nova_senha != conf_senha:
                st.error("As senhas não coincidem.")
            elif len(nova_senha) < 8:
                st.error("A nova senha deve ter pelo menos 8 caracteres.")
            elif DB_OK and email:
                from lib.user_db import alterar_senha
                ok, msg = alterar_senha(email, senha_atual, nova_senha)
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")
            else:
                st.info("Troca de senha disponível apenas para contas cadastradas no banco.")

    st.divider()

    # Info somente leitura
    with st.container():
        c1, c2, c3 = st.columns(3)
        c1.metric("Perfil de acesso", perfil.replace("_", " ").upper())
        c2.metric("Status", "✅ Ativo")
        c3.metric("E-mail", email[:22] + "…" if len(email) > 22 else email)


# ─────────────────────────────────────────────────────────────────────────────
# ABA: IA CONSULTORA (Chiara)
# ─────────────────────────────────────────────────────────────────────────────
def _tab_ia_consultora():
    st.markdown("### 🤖 Configurar IA Consultora (Chiara)")

    # Carrega do banco se ainda não carregado
    if not st.session_state.get("_chiara_loaded"):
        try:
            cfg = carregar_config_chiara()
            if cfg.get("nome"):      st.session_state["chiara_nome"]      = cfg["nome"]
            if cfg.get("cargo"):     st.session_state["chiara_cargo"]     = cfg["cargo"]
            if cfg.get("foto_b64"): st.session_state["chiara_foto_b64"]  = cfg["foto_b64"]
            if cfg.get("foto_mime"): st.session_state["chiara_foto_mime"] = cfg["foto_mime"]
            if cfg.get("saudacao"): st.session_state["chiara_saudacao"]  = cfg["saudacao"]
        except Exception:
            pass
        st.session_state["_chiara_loaded"] = True

    _chiara_b64  = st.session_state.get("chiara_foto_b64", "")
    _chiara_mime = st.session_state.get("chiara_foto_mime", "image/jpeg")
    _chiara_nome = st.session_state.get("chiara_nome", "Chiara")
    _chiara_cargo = st.session_state.get("chiara_cargo", "Terapeuta Capilar Digital · Embaixadora HIPNUS")

    # Preview da foto atual
    col_prev, col_up = st.columns([1, 2])
    with col_prev:
        if _chiara_b64:
            st.html(f"""
            <div style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:8px 0;">
              <img src="data:{_chiara_mime};base64,{_chiara_b64}"
                   style="width:120px;height:120px;border-radius:50%;object-fit:cover;
                          border:3px solid rgba(185,131,255,.6);
                          box-shadow:0 0 30px rgba(185,131,255,.4);" />
              <span style="font-size:.75rem;color:rgba(185,131,255,.7);font-style:italic;">Foto atual</span>
            </div>""")
        else:
            initial = _chiara_nome[0].upper() if _chiara_nome else "C"
            st.html(f"""
            <div style="display:flex;flex-direction:column;align-items:center;gap:8px;padding:8px 0;">
              <div style="width:120px;height:120px;border-radius:50%;
                background:linear-gradient(135deg,#7c3aed,#ec4899);
                display:flex;align-items:center;justify-content:center;
                font-size:3rem;font-weight:800;color:#fff;
                border:3px solid rgba(185,131,255,.6);
                box-shadow:0 0 30px rgba(185,131,255,.4);">{initial}</div>
              <span style="font-size:.75rem;color:rgba(185,131,255,.7);font-style:italic;">Sem foto</span>
            </div>""")

    with col_up:
        st.markdown("**📷 Upload da foto da Chiara**")
        foto_upload = st.file_uploader(
            "Escolha uma imagem (JPG/PNG, máx 2 MB)",
            type=["jpg", "jpeg", "png", "webp"],
            key="chiara_foto_upload_cfg",
        )
        if foto_upload:
            foto_bytes = foto_upload.read()
            novo_hash  = hashlib.md5(foto_bytes).hexdigest()
            if novo_hash != st.session_state.get("chiara_foto_hash"):
                mime = foto_upload.type or "image/jpeg"
                b64  = base64.b64encode(foto_bytes).decode()
                # ── PERSISTE NO BANCO ──────────────────────────────────────
                if DB_OK:
                    salvar_foto_chiara(b64, mime)
                # ── Atualiza session_state ─────────────────────────────────
                st.session_state["chiara_foto_b64"]  = b64
                st.session_state["chiara_foto_mime"] = mime
                st.session_state["chiara_foto_hash"] = novo_hash
                st.success("✅ Foto salva! Ela será mantida mesmo após logout.")
                st.rerun()
            else:
                st.success("✅ Foto já carregada.")

    st.divider()

    # Nome e cargo
    with st.form("form_chiara_nome"):
        novo_nome  = st.text_input("Nome da IA",      value=_chiara_nome,  placeholder="Chiara")
        novo_cargo = st.text_input("Cargo / descrição", value=_chiara_cargo,
                                   placeholder="Terapeuta Capilar Digital · Embaixadora HIPNUS")
        if st.form_submit_button("💾 Salvar nome e cargo", use_container_width=True):
            if DB_OK:
                salvar_nome_chiara(novo_nome, novo_cargo)
            st.session_state["chiara_nome"]  = novo_nome
            st.session_state["chiara_cargo"] = novo_cargo
            st.success("✅ Nome e cargo atualizados!")
            st.rerun()

    st.divider()

    # Saudação
    st.markdown("**💬 Saudação inicial personalizada**")
    saudacao_atual = st.session_state.get("chiara_saudacao", "")
    nova_saudacao  = st.text_area(
        "Mensagem de boas-vindas da Chiara",
        value=saudacao_atual,
        height=120,
        placeholder="Olá! Sou a Chiara, consultora da Hipnus...",
        key="chiara_saudacao_input",
    )
    if st.button("💾 Salvar saudação", key="btn_save_saudacao"):
        if DB_OK:
            set_app_config("chiara_saudacao", nova_saudacao)
        st.session_state["chiara_saudacao"] = nova_saudacao
        st.success("✅ Saudação salva!")
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# ABA: CONFIGURAÇÕES GROQ
# ─────────────────────────────────────────────────────────────────────────────
def _tab_groq():
    st.markdown("### 🔑 Chave de API — Groq")
    st.info(
        "A GROQ_API_KEY deve ser configurada nos **Secrets** do Streamlit Cloud.\n\n"
        "Acesse: **Settings → Secrets** e adicione:\n```toml\nGROQ_API_KEY = \"gsk_...\"\n```"
    )
    try:
        from lib.ia_consultora import groq_status
        status = groq_status()
        if status["configured"]:
            st.success(f"✅ API configurada · modelo: `{status['model']}`")
        else:
            st.error("❌ GROQ_API_KEY não encontrada.")
    except Exception as e:
        st.warning(f"Não foi possível verificar o status da API: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# ABA: SISTEMA
# ─────────────────────────────────────────────────────────────────────────────
def _tab_sistema():
    st.markdown("### 🗄️ Sistema e Banco de Dados")
    if st.button("🔍 Verificar conexão com o banco"):
        try:
            from lib.db_utils import get_db_session
            db, err = get_db_session()
            if db:
                st.success("✅ Banco de dados conectado com sucesso!")
                db.close()
            else:
                st.error(f"❌ Falha na conexão: {err}")
        except Exception as e:
            st.error(f"❌ Erro: {e}")

    st.divider()
    st.markdown("**📋 Variáveis de ambiente ativas**")
    import os
    env_vars = ["GROQ_API_KEY", "DATABASE_URL", "ASAAS_API_KEY", "SMTP_HOST"]
    for var in env_vars:
        val = os.environ.get(var)
        if val:
            st.success(f"✅ `{var}` — configurada")
        else:
            st.warning(f"⚠️ `{var}` — não encontrada")


# ─────────────────────────────────────────────────────────────────────────────
# ROTEAMENTO DE ABAS
# ─────────────────────────────────────────────────────────────────────────────
st.title("⚙️ Configurações")

perfil_atual = st.session_state.get("perfil", "demo")

if perfil_atual in {"super_admin", "admin"}:
    aba_conta, aba_ia, aba_groq, aba_sistema = st.tabs([
        "👤 Minha Conta",
        "🤖 IA Consultora",
        "🔑 Groq API",
        "🗄️ Sistema",
    ])
    with aba_conta:   _tab_minha_conta()
    with aba_ia:      _tab_ia_consultora()
    with aba_groq:    _tab_groq()
    with aba_sistema: _tab_sistema()
else:
    # b2b / b2c veem apenas a aba de conta
    st.markdown("### 👤 Minha Conta")
    _tab_minha_conta()
