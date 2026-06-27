"""
7_Cadastro_Parceiro.py — HIPNUS COSMÉTICOS
============================================
Página PÚBLICA de cadastro via convite.
Campos adicionados: usuário (login) e foto de perfil (upload).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import streamlit as st

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for p in [str(_ROOT), str(_FRONTEND)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from lib.db_utils  import resolve_db_url          # noqa: E402
from lib.invite_db import validar_token_db, usar_token_db  # noqa: E402
from lib.user_db   import criar_parceiro, image_to_b64  # noqa: E402

st.set_page_config(
    page_title="Cadastro Parceiro | Hipnus Cosméticos",
    page_icon="💼", layout="centered",
)

API_URL = st.secrets.get("HIPNUS_API_URL", "http://localhost:8000")


def validar_email(email: str) -> bool:
    return bool(re.match(r"^[\w.+-]+@[\w-]+\.[\w.]+$", email))


def validar_username(u: str) -> bool:
    """Só letras, números, . _ - ; mín 3 chars."""
    return bool(re.match(r"^[a-z0-9._-]{3,30}$", u.lower()))


def _validar_token_api(token: str) -> dict | None:
    try:
        import requests
        r = requests.get(f"{API_URL}/api/v1/invites/{token}", timeout=4)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def validar_token(token: str) -> dict | None:
    resultado = _validar_token_api(token)
    return resultado if resultado else validar_token_db(token)


def usar_token(token: str, dados: dict) -> tuple[bool, str]:
    try:
        import requests
        r = requests.post(f"{API_URL}/api/v1/invites/{token}/use", json=dados, timeout=10)
        if r.status_code in (200, 201):
            return True, "Cadastro realizado!"
    except Exception:
        pass
    return usar_token_db(token, dados)


# ─── Estilos ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.invite-header {
    background: linear-gradient(135deg,#1a0733 0%,#3b1278 40%,#6c2bd9 75%,#8b44f6 100%);
    border-radius:16px; padding:2.5rem 2rem 2rem;
    text-align:center; margin-bottom:2rem; color:white;
}
.invite-header h1 { font-size:2rem; margin-bottom:.25rem; }
.invite-header p  { opacity:.8; font-size:1rem; margin:0; }
.success-box {
    background:#d4edda; border:1px solid #c3e6cb; border-radius:12px;
    padding:1.5rem; text-align:center; color:#155724;
}
.avatar-preview img {
    border-radius: 50%; object-fit: cover;
    border: 3px solid #7c3aed; margin: 0 auto; display: block;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="invite-header">
    <h1>💼 Hipnus Cosméticos</h1>
    <p>Você foi convidado para se tornar um parceiro</p>
</div>
""", unsafe_allow_html=True)

for key, default in [("cadastro_ok", False), ("invite_data", None), ("token_validado", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─ Tela de sucesso ────────────────────────────────────────────────────────────
if st.session_state.cadastro_ok:
    st.markdown("""
    <div class="success-box">
        <h2>✅ Cadastro realizado!</h2>
        <p>Bem-vindo à família Hipnus Cosméticos.<br>
        Acesse a plataforma com seu e-mail e a senha que você criou.</p>
    </div>
    """, unsafe_allow_html=True)
    st.balloons()
    if st.button("🔐 Fazer login agora", use_container_width=True, type="primary"):
        st.switch_page("streamlit_app.py")
    st.stop()

# ─ Token ─────────────────────────────────────────────────────────────────────
token = st.query_params.get("token", "").strip()
if not token:
    st.info("ℹ️ Acesse esta página pelo link do seu convite, ou cole o código abaixo.")
    token_input = st.text_input("Código do convite", placeholder="cole aqui o token")
    if token_input:
        token = token_input.strip()
if not token:
    st.stop()

# ─ Validação do token ──────────────────────────────────────────────────────────
if st.session_state.token_validado != token:
    with st.spinner("Validando seu convite..."):
        invite = validar_token(token)
    if invite is None:
        st.error("❌ Convite inválido, expirado ou já utilizado. Solicite um novo convite ao administrador.")
        with st.expander("🔧 Detalhes técnicos (admin)"):
            st.code(f"API_URL:      {API_URL}\nDATABASE_URL: {resolve_db_url()}\nToken:        {token[:16]}...", language="text")
        st.stop()
    st.session_state.invite_data    = invite
    st.session_state.token_validado = token

invite = st.session_state.invite_data

role_labels = {
    "b2b": "🎤 Profissional / Salão", "b2c": "👤 Cliente Final",
    "admin": "🛡️ Administrador", "parceiro": "🤝 Parceiro",
}
role       = invite.get("role", "b2b")
role_label = role_labels.get(role, role.capitalize())
try:
    from datetime import datetime
    exp_str = datetime.fromisoformat(invite.get("expires_at", "")).strftime("%d/%m/%Y às %H:%M")
except Exception:
    exp_str = invite.get("expires_at", "—")

st.success(f"✅ Convite válido! Perfil: **{role_label}** — expira em {exp_str}")
st.subheader("📝 Preencha seus dados")

# ─── Formulário ─────────────────────────────────────────────────────────────────
with st.form("form_cadastro_parceiro", clear_on_submit=False):

    # —— Foto de perfil ——
    st.markdown("**📸 Foto de perfil** *(opcional — será exibida no sidebar e no chat da IA)*")
    avatar_file = st.file_uploader(
        "Escolha uma imagem (JPG, PNG, WEBP — máx 2 MB)",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

    col1, col2 = st.columns(2)
    with col1:
        nome     = st.text_input("Nome completo *",       placeholder="João da Silva")
        username = st.text_input(
            "Usuário (login) *",
            placeholder="joaosilva  (só letras, números, . _ -)",
            help="Será seu nome de usuário único na plataforma. Mín 3 caracteres.",
        )
        email    = st.text_input(
            "E-mail *",
            value=invite.get("email", ""),
            disabled=bool(invite.get("email")),
        )
        telefone = st.text_input("Telefone / WhatsApp *", placeholder="(31) 99999-9999")
    with col2:
        empresa = st.text_input("Nome do negócio",       placeholder="Salão Beleza Total")
        cidade  = st.text_input("Cidade *",               placeholder="Belo Horizonte")
        estado  = st.selectbox("Estado *", [
            "MG","SP","RJ","ES","BA","GO","DF","PR","SC","RS",
            "MT","MS","AM","PA","CE","PE","MA","PB","RN","AL",
            "SE","PI","TO","RO","AC","RR","AP",
        ])
        bio = st.text_area(
            "Mini bio", placeholder="Conte um pouco sobre você ou seu negócio...",
            height=100,
        )

    senha  = st.text_input("Crie uma senha *",    type="password", placeholder="mínimo 8 caracteres")
    senha2 = st.text_input("Confirme a senha *",  type="password")
    aceite = st.checkbox("Li e aceito os termos de uso e política de privacidade da Hipnus Cosméticos")

    submitted = st.form_submit_button("✅ Concluir cadastro", use_container_width=True, type="primary")


# ─── Processamento ─────────────────────────────────────────────────────────────
if submitted:
    erros = []
    if not nome.strip():                    erros.append("Nome é obrigatório.")
    if not username.strip():                erros.append("Usuário é obrigatório.")
    elif not validar_username(username):    erros.append("Usuário inválido: use letras minúsculas, números, ponto, hífen ou sublinhado (mín 3 chars).")
    if not email.strip():                   erros.append("E-mail é obrigatório.")
    elif not validar_email(email):          erros.append("E-mail inválido.")
    if not telefone.strip():                erros.append("Telefone é obrigatório.")
    if not cidade.strip():                  erros.append("Cidade é obrigatória.")
    if len(senha) < 8:                      erros.append("Senha deve ter ao menos 8 caracteres.")
    if senha != senha2:                     erros.append("As senhas não coincidem.")
    if not aceite:                          erros.append("Você precisa aceitar os termos de uso.")
    if avatar_file and avatar_file.size > 2 * 1024 * 1024:
        erros.append("Imagem muito grande. Máximo 2 MB.")

    if erros:
        for e in erros:
            st.error(e)
    else:
        # Processa avatar
        avatar_b64 = None
        if avatar_file:
            mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
            mime     = mime_map.get(avatar_file.name.split(".")[-1].lower(), "image/jpeg")
            avatar_b64 = image_to_b64(avatar_file.read(), mime)

        # 1. Marca o convite como usado
        ok_token, msg_token = usar_token(token, {"email": email, "role": role})

        # 2. Cria o parceiro no banco
        ok_db, msg_db = criar_parceiro(
            nome=nome.strip(),
            email=email.strip(),
            senha=senha,
            role=role,
            username=username.strip(),
            telefone=telefone.strip(),
            empresa=empresa.strip(),
            cidade=cidade.strip(),
            estado=estado,
            avatar_b64=avatar_b64,
        )

        if ok_db or ok_token:
            st.session_state.cadastro_ok = True
            st.rerun()
        else:
            st.error(f"❌ {msg_db or msg_token}")
