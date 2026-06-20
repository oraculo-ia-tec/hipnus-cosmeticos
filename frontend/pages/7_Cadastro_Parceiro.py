"""
Cadastro de Parceiro via Convite
================================
Página acessada pelo convidado através do link personalizado.
Valida o token do convite, exibe formulário de cadastro e
registra o novo parceiro no sistema.

Fluxo:
  1. Lê ?token= da query string (ou campo manual)
  2. Valida token via API (GET /invites/{token})
  3. Exibe formulário pré-preenchido com e-mail do convite
  4. Ao submeter, chama POST /invites/{token}/use
  5. Redireciona para Home após cadastro
"""

import streamlit as st
import requests
import re
from datetime import datetime

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Cadastro Parceiro | Hipnus Cosméticos",
    page_icon="💼",
    layout="centered",
)

API_URL = st.secrets.get("HIPNUS_API_URL", "http://localhost:8000")

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def get_query_param(key: str) -> str | None:
    """Lê parâmetro da URL de forma compatível com todas as versões do Streamlit."""
    try:
        params = st.query_params
        return params.get(key)
    except Exception:
        return None


def validar_token(token: str) -> dict | None:
    """Consulta a API para validar o token do convite."""
    try:
        r = requests.get(f"{API_URL}/api/v1/invites/{token}", timeout=5)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def usar_token(token: str, dados: dict) -> tuple[bool, str]:
    """Marca o token como usado e registra o parceiro."""
    try:
        r = requests.post(
            f"{API_URL}/api/v1/invites/{token}/use",
            json=dados,
            timeout=10,
        )
        if r.status_code in (200, 201):
            return True, "Cadastro realizado com sucesso!"
        msg = r.json().get("detail", "Erro ao processar cadastro.")
        return False, msg
    except Exception as e:
        return False, f"Serviço indisponível: {e}"


def validar_email(email: str) -> bool:
    return bool(re.match(r"^[\w.+-]+@[\w-]+\.[\w.]+$", email))


# ──────────────────────────────────────────────
# Estilos
# ──────────────────────────────────────────────
st.markdown("""
<style>
    .invite-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem 2rem;
        text-align: center;
        margin-bottom: 2rem;
        color: white;
    }
    .invite-header h1 { font-size: 2rem; margin-bottom: 0.25rem; }
    .invite-header p  { opacity: 0.8; font-size: 1rem; margin: 0; }
    .badge-role {
        display: inline-block;
        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.3);
        border-radius: 999px;
        padding: 0.25rem 1rem;
        font-size: 0.85rem;
        margin-top: 0.75rem;
        color: white;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        color: #155724;
    }
    .token-manual {
        background: #fff8e1;
        border: 1px solid #ffe082;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        color: #5d4037;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Lógica principal
# ──────────────────────────────────────────────

token_url = get_query_param("token")

# Header
st.markdown("""
<div class="invite-header">
    <h1>💼 Hipnus Cosméticos</h1>
    <p>Você foi convidado para se tornar um parceiro</p>
</div>
""", unsafe_allow_html=True)

# ── Estado da sessão ──
if "cadastro_ok" not in st.session_state:
    st.session_state.cadastro_ok = False
if "invite_data" not in st.session_state:
    st.session_state.invite_data = None
if "token_validado" not in st.session_state:
    st.session_state.token_validado = None

# ── Sucesso ──
if st.session_state.cadastro_ok:
    st.markdown("""
    <div class="success-box">
        <h2>✅ Cadastro realizado!</h2>
        <p>Bem-vindo à família Hipnus Cosméticos.<br>
        Em breve você receberá um e-mail de confirmação.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏠 Ir para a Home", use_container_width=True):
        st.switch_page("pages/1_Home.py")
    st.stop()

# ── Entrada do token ──
token = token_url

if not token:
    st.markdown('<div class="token-manual">ℹ️ Acesse esta página pelo link do seu convite, ou cole o código abaixo.</div>', unsafe_allow_html=True)
    token_input = st.text_input("Código do convite", placeholder="cole aqui o token do seu convite")
    if token_input:
        token = token_input.strip()

if not token:
    st.info("Aguardando código de convite...")
    st.stop()

# ── Validação do token ──
if st.session_state.token_validado != token:
    with st.spinner("Validando seu convite..."):
        invite = validar_token(token)
    if invite is None:
        st.error("❌ Convite inválido, expirado ou já utilizado. Solicite um novo convite ao administrador.")
        st.stop()
    st.session_state.invite_data = invite
    st.session_state.token_validado = token

invite = st.session_state.invite_data

# ── Info do convite ──
role_labels = {
    "distribuidor": "🏭 Distribuidor",
    "revendedor":   "🛍️ Revendedor",
    "salao":        "✂️ Salão de Beleza",
    "profissional": "💇 Profissional",
    "parceiro":     "🤝 Parceiro",
}
role = invite.get("role", "parceiro")
role_label = role_labels.get(role, role.capitalize())

expires_raw = invite.get("expires_at", "")
try:
    exp_dt = datetime.fromisoformat(expires_raw)
    exp_str = exp_dt.strftime("%d/%m/%Y às %H:%M")
except Exception:
    exp_str = expires_raw

st.success(f"✅ Convite válido! Perfil: **{role_label}** — expira em {exp_str}")

# ── Formulário de cadastro ──
st.subheader("Preencha seus dados")

with st.form("form_cadastro_parceiro", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome completo *", placeholder="João da Silva")
        email = st.text_input("E-mail *", value=invite.get("email", ""), disabled=bool(invite.get("email")))
        telefone = st.text_input("Telefone / WhatsApp *", placeholder="(31) 99999-9999")
    with col2:
        empresa = st.text_input("Nome do negócio", placeholder="Salão Beleza Total")
        cidade = st.text_input("Cidade *", placeholder="Belo Horizonte")
        estado = st.selectbox("Estado *", [
            "MG","SP","RJ","ES","BA","GO","DF","PR","SC","RS",
            "MT","MS","AM","PA","CE","PE","MA","PB","RN","AL",
            "SE","PI","TO","RO","AC","RR","AP",
        ])

    senha = st.text_input("Crie uma senha *", type="password", placeholder="mínimo 8 caracteres")
    senha2 = st.text_input("Confirme a senha *", type="password")

    aceite = st.checkbox("Li e aceito os termos de uso e política de privacidade da Hipnus Cosméticos")

    submitted = st.form_submit_button("✅ Concluir cadastro", use_container_width=True, type="primary")

if submitted:
    erros = []
    if not nome.strip():            erros.append("Nome é obrigatório.")
    if not email.strip():           erros.append("E-mail é obrigatório.")
    elif not validar_email(email):  erros.append("E-mail inválido.")
    if not telefone.strip():        erros.append("Telefone é obrigatório.")
    if not cidade.strip():          erros.append("Cidade é obrigatória.")
    if len(senha) < 8:              erros.append("Senha deve ter ao menos 8 caracteres.")
    if senha != senha2:             erros.append("As senhas não coincidem.")
    if not aceite:                  erros.append("Você precisa aceitar os termos de uso.")

    if erros:
        for e in erros:
            st.error(e)
    else:
        payload = {
            "nome": nome.strip(),
            "email": email.strip(),
            "telefone": telefone.strip(),
            "empresa": empresa.strip(),
            "cidade": cidade.strip(),
            "estado": estado,
            "senha": senha,
            "role": role,
            "token": token,
        }
        ok, msg = usar_token(token, payload)
        if ok:
            st.session_state.cadastro_ok = True
            st.rerun()
        else:
            st.error(f"❌ {msg}")
