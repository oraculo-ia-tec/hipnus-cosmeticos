"""
5_Convites.py — HIPNUS COSMÉTICOS
====================================
Gerenciamento de links de convite para cadastro de novos parceiros.

Acesso exclusivo: SUPER_ADMIN.
Permite gerar, listar e revogar tokens de convite únicos.

Depênde dos endpoints:
  POST   /api/v1/invites
  GET    /api/v1/invites
  DELETE /api/v1/invites/{id}
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth, sidebar_user_info
from lib.config import BRAND

st.set_page_config(page_title="Convites · HIPNUS", page_icon="🔗", layout="wide")
ui.inject_theme()

usuario = require_auth(perfis_permitidos=["super_admin"])

ui.brand_header()
ui.api_status_badge(api.api_online())
sidebar_user_info()
ui.sidebar_cart_summary()

st.markdown('<div class="hip-section-title">🔗 Links de Convite</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hip-section-sub">Gere links de cadastro para novos parceiros. '
    'Cada token é de uso único e expira em 7 dias.</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- Gerar convite
st.subheader("➕ Gerar novo convite")

with st.form("form_invite"):
    prospect_name = st.text_input(
        "Nome do prospect",
        placeholder="Ex.: Salão da Ana — Belo Horizonte/MG",
    )
    expires_days = st.number_input(
        "Validade (dias)", min_value=1, max_value=30, value=7
    )
    gerar = st.form_submit_button("🔗 Gerar link", type="primary")

if gerar:
    if not prospect_name.strip():
        st.warning("⚠️ Informe o nome do prospect.")
    else:
        resultado = api.create_invite(
            token=usuario["token"],
            prospect_name=prospect_name.strip(),
            expires_days=int(expires_days),
        )
        if resultado:
            token = resultado.get("token", "")
            base_url = st.secrets.get("APP_URL", "https://hipnus-cosmeticos.streamlit.app")
            url = f"{base_url}?token={token}"
            st.success(f"✅ Convite gerado para **{prospect_name}**")
            st.code(url, language=None)
            st.caption(f"Token: `{token}` · Válido por {expires_days} dia(s)")
        else:
            st.error("❌ Erro ao gerar convite. Verifique se a API está online.")

st.divider()

# ---------------------------------------------------------------- Listar convites
st.subheader("📋 Convites ativos")

online = api.api_online()
if not online:
    st.info("🟣 API offline — inicie o backend para gerenciar convites.")
else:
    invites = api.list_invites(token=usuario["token"]) or []
    if not invites:
        st.info("Nenhum convite ativo no momento.")
    else:
        for inv in invites:
            cols = st.columns([3, 2, 1.5, 1])
            cols[0].write(inv.get("prospect_name") or "—")
            cols[1].code(inv.get("token", "")[:16] + "...", language=None)
            exp = inv.get("expires_at", "")[:10] if inv.get("expires_at") else "—"
            cols[2].write(f"Expira: {exp}")
            if cols[3].button("🗑️ Revogar", key=f"rev_{inv['id']}"):
                ok = api.revoke_invite(inv["id"], token=usuario["token"])
                if ok:
                    st.toast("Convite revogado.", icon="✅")
                    st.rerun()
                else:
                    st.error("Erro ao revogar.")
