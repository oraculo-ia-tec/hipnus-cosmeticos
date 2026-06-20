"""
6_Convites.py — HIPNUS COSMÉTICOS
Gerenciamento de convites para novos parceiros.
Acesso: super_admin, admin.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
import streamlit as st
from lib import api, ui
from lib.auth import require_auth, sidebar_logo, sidebar_user_info, sidebar_logout_button
from lib import components
from lib.config import API_V1

st.set_page_config(page_title="Convites · HIPNUS", page_icon="📨", layout="wide")
ui.inject_theme()
require_auth(perfis_permitidos=["super_admin", "admin"])

# ─ Sidebar: topo ────────────────────────────────────────────────────────
sidebar_logo()
sidebar_user_info()
ui.api_status_badge(api.api_online())

# ─ Header ────────────────────────────────────────────────────────────
components.page_header(
    title="Convites de Parceiros",
    subtitle="Gerencie convites para cadastro de novos distribuidores e salões.",
    kicker="Área Admin",
)

# ─ Gerar convite ───────────────────────────────────────────────────────
components.section_title("Gerar novo convite")
with st.form("form_invite"):
    email_dest = st.text_input("E-mail do destinatário", placeholder="parceiro@email.com")
    role_dest  = st.selectbox("Perfil do convidado", ["b2b", "admin"])
    submitted  = st.form_submit_button("📨 Gerar convite", use_container_width=True)

if submitted:
    if not email_dest:
        st.error("Informe o e-mail do destinatário.")
    else:
        token = st.session_state.get("token")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            r = httpx.post(
                f"{API_V1}/invites/",
                json={"email": email_dest, "role": role_dest},
                headers=headers,
                timeout=8.0,
            )
            if r.status_code == 201:
                data = r.json()
                st.success(
                    f"✅ Convite gerado para **{email_dest}**!\n\n"
                    f"**Token:** `{data.get('token', 'N/A')}`\n\n"
                    f"**Link de cadastro:** `{data.get('signup_url', 'N/A')}`"
                )
            else:
                st.error(f"Erro ao gerar convite: {r.status_code} — {r.text}")
        except Exception as e:
            st.warning(f"⚠️ API indisponível: {e}")

components.divider()

# ─ Lista de convites ─────────────────────────────────────────────────────
components.section_title("Convites existentes")
token = st.session_state.get("token")
headers = {"Authorization": f"Bearer {token}"} if token else {}
try:
    r = httpx.get(f"{API_V1}/invites/", headers=headers, timeout=8.0)
    if r.status_code == 200:
        invites = r.json()
        if not invites:
            components.empty_state(
                icon="📨",
                title="Nenhum convite gerado",
                message="Gere o primeiro convite acima.",
            )
        else:
            for inv in invites:
                used = inv.get("used", False)
                status = "✅ Usado" if used else "⏳ Pendente"
                with st.expander(f"{inv.get('email', 'N/A')} — {status}"):
                    st.markdown(f"**Perfil:** {inv.get('role', 'N/A')}")
                    st.markdown(f"**Token:** `{inv.get('token', 'N/A')}`")
                    st.markdown(f"**Criado em:** {inv.get('created_at', 'N/A')}")
                    st.markdown(f"**Expira em:** {inv.get('expires_at', 'N/A')}")
    else:
        st.warning(f"Não foi possível carregar convites: {r.status_code}")
except Exception as e:
    st.info(f"⚠️ API offline — sem dados de convites ({e})")

# ─ Sidebar: rodapé ───────────────────────────────────────────────────────
st.sidebar.divider()
sidebar_logout_button()
