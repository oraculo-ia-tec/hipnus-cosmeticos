"""
7_Cadastro_Parceiro.py — HIPNUS COSMÉTICOS
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

st.set_page_config(page_title="Cadastro Parceiro · HIPNUS", page_icon="🏪", layout="wide")
ui.inject_theme()
require_auth()
sidebar_logo()
sidebar_user_info()
sidebar_logout_button()

components.page_header(title="Cadastro de Parceiro", subtitle="Preencha os dados da empresa para solicitar acesso à área B2B.")

with st.form("form_parceiro"):
    st.markdown("### Dados pessoais")
    c1, c2 = st.columns(2)
    nome     = c1.text_input("Nome completo *")
    email    = c2.text_input("E-mail *")
    telefone = c1.text_input("Telefone / WhatsApp")
    cpf_cnpj = c2.text_input("CPF ou CNPJ")
    st.markdown("### Dados do negócio")
    c3, c4 = st.columns(2)
    empresa  = c3.text_input("Nome do salão / empresa")
    cidade   = c4.text_input("Cidade")
    estado   = c3.selectbox("Estado", ["","AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"])
    segmento = c4.selectbox("Segmento", ["","Salão de beleza","Barbearia","Distribuidora","Loja de cosméticos","Outro"])
    token_inv = st.text_input("Token de convite (opcional)")
    obs       = st.text_area("Observações", height=80)
    submitted = st.form_submit_button("🏪 Solicitar cadastro", use_container_width=True)

if submitted:
    if not nome or not email:
        st.error("❌ Preencha nome e e-mail obrigatórios.")
    else:
        payload = {"name": nome, "email": email, "phone": telefone, "document": cpf_cnpj,
                   "company": empresa, "city": cidade, "state": estado, "segment": segmento,
                   "invite_token": token_inv or None, "notes": obs}
        token_sess = st.session_state.get("token")
        headers = {"Authorization": f"Bearer {token_sess}"} if token_sess else {}
        try:
            r = httpx.post(f"{API_V1}/partners/", json=payload, headers=headers, timeout=8.0)
            if r.status_code in (200, 201):
                st.success("✅ Solicitação enviada! Nossa equipe entrará em contato em breve.")
            else:
                st.error(f"Erro ao enviar: {r.status_code} — {r.text}")
        except Exception as e:
            st.warning(f"⚠️ API indisponível — solicitação não enviada ({e})")
