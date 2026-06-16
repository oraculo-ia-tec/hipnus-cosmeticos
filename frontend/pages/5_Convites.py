"""
5_Convites.py — HIPNUS COSMÉTICOS
====================================
Página de Convites — envio e gestão de convites para novos parceiros.

Acesso restrito: admin e super_admin.

Ordem da sidebar:
  1. brand_header()
  2. sidebar_user_info()      ← ACIMA do menu
  3. [menu nativo]
  4. api_status_badge()
  5. sidebar_cart_summary()
  6. sidebar_logout_button()  ← ABAIXO do menu
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from lib import api, ui
from lib.auth import require_auth, sidebar_user_info, sidebar_logout_button

st.set_page_config(page_title="Convites · HIPNUS", page_icon="📧", layout="wide")
ui.inject_theme()

require_auth(perfis_permitidos=["admin", "super_admin"])

# ─── Sidebar ───────────────────────────────────────────────────────────
ui.brand_header()                       # 1. Logo
sidebar_user_info()                     # 2. Usuário (ACIMA do menu)
# --- [menu nativo Streamlit aqui] ---
ui.api_status_badge(api.api_online())   # 4. Status API
ui.sidebar_cart_summary()               # 5. Carrinho
sidebar_logout_button()                 # 6. SAIR (ABAIXO do menu)

st.markdown('<div class="hip-section-title">📧 Convites de Parceiros</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hip-section-sub">Envie convites por e-mail para novos parceiros e revendedores.</div>',
    unsafe_allow_html=True,
)

# ─── Formulário de envio ────────────────────────────────────────────────
with st.form("form_convite"):
    email_dest = st.text_input("E-mail do parceiro *", placeholder="parceiro@exemplo.com")
    nome_dest  = st.text_input("Nome do parceiro (opcional)", placeholder="Ex.: Salão Beleza Total")
    mensagem   = st.text_area(
        "Mensagem personalizada (opcional)",
        placeholder="Olá! Convidamos você a fazer parte da rede de parceiros Hipnus...",
        height=120,
    )
    enviar = st.form_submit_button("📨 Enviar convite", type="primary", use_container_width=True)

if enviar:
    erros = []
    if not email_dest.strip() or "@" not in email_dest:
        erros.append("E-mail inválido.")
    if erros:
        for e in erros:
            st.error(e)
    else:
        with st.spinner("Enviando convite..."):
            try:
                resultado = api.send_invite(
                    email=email_dest.strip(),
                    nome=nome_dest.strip() or None,
                    mensagem=mensagem.strip() or None,
                )
                st.success(f"✅ Convite enviado para **{email_dest.strip()}**!")
            except Exception as exc:
                st.warning(
                    f"API indisponível — convite registrado localmente. ({exc})"
                )

# ─── Lista de convites enviados ─────────────────────────────────────────
st.markdown("---")
st.markdown("### Convites enviados")

try:
    convites = api.list_invites()
except Exception:
    convites = []

if not convites:
    st.info("Nenhum convite enviado ainda.")
else:
    for c in convites:
        status_icon = "✅" if c.get("accepted") else "⏳"
        st.markdown(
            f"{status_icon} **{c.get('email')}** "
            f"— enviado em {c.get('created_at', '—')[:10]} "
            f"— status: {'aceito' if c.get('accepted') else 'pendente'}"
        )
