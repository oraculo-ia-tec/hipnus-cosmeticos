"""
6_Cadastro_Parceiro.py — HIPNUS COSMÉTICOS
============================================
Formulário público de cadastro de parceiro via link de convite.

Acesso: público, mas requer ?token= válido na URL (query param).
O token é validado na API antes de exibir o formulário.
Após cadastro, o token é marcado como usado (uso único).

Depênde dos endpoints:
  GET  /api/v1/invites/validate?token=...
  POST /api/v1/partners?invite_token=...
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.config import BRAND, COLORS

st.set_page_config(
    page_title="Cadastro de Parceiro · HIPNUS",
    page_icon="🏪",
    layout="centered",
)
ui.inject_theme()

# Oculta sidebar e menu para página pública
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    #MainMenu { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

c = COLORS
st.markdown(
    f"""
    <div style="text-align:center; padding:2rem 0 1rem;">
        <div style="font-size:2.2rem; font-weight:800; color:{c['primary']};
                    letter-spacing:-1px;">HIPNUS</div>
        <div style="font-size:.9rem; color:{c['muted']}; letter-spacing:2px;">COSMÉTICOS</div>
        <div style="margin-top:.6rem; font-size:.85rem; color:{c['muted']};">Cadastro de Parceiro Oficial</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------- token via query param
params = st.query_params
token = params.get("token", "")

if not token:
    st.error("❌ Este link de cadastro é inválido ou já foi utilizado.")
    st.info("Entre em contato com a equipe Hipnus para solicitar um novo convite.")
    st.stop()

# ---------------------------------------------------------------- valida token
validacao = api.validate_invite(token)

if not validacao or not validacao.get("valid"):
    st.error("❌ Convite inválido, expirado ou já utilizado.")
    st.info("Solicite um novo link de convite à equipe Hipnus.")
    st.stop()

st.success(
    f"✅ Convite válido! Bem-vindo(a), **{validacao.get('prospect_name', 'parceiro')}**."
)
st.markdown("---")

# ---------------------------------------------------------------- formulário
st.subheader("🏪 Dados do seu negócio")

with st.form("form_parceiro"):
    col1, col2 = st.columns(2)
    with col1:
        nome        = st.text_input("Razão Social / Nome *", placeholder="Ex.: Salão Bela Hair LTDA")
        slug        = st.text_input("Slug da loja *", placeholder="Ex.: salao-bela-hair",
                                    help="Identificador único público da sua loja. Só letras, números e hífen.")
        email       = st.text_input("E-mail comercial *", placeholder="contato@salaobela.com")
        phone       = st.text_input("Telefone", placeholder="31999999999")
    with col2:
        display_name = st.text_input("Nome de exibição da loja *", placeholder="Ex.: Salão Bela Hair")
        cpf_cnpj     = st.text_input("CPF / CNPJ * (somente números)", placeholder="00000000000")
        city         = st.text_input("Cidade", placeholder="Belo Horizonte")
        state        = st.text_input("Estado", placeholder="MG", max_chars=2)

    descricao = st.text_area(
        "Descrição da loja (opcional)",
        placeholder="Conte um pouco sobre seu salão, especialidades, diferenciais...",
        height=90,
    )

    st.divider()
    st.caption(
        "⚠️ Após o cadastro, a equipe Hipnus analisará e ativará sua conta de parceiro. "
        "Uma subconta Asaas será criada automaticamente para receber repasses."
    )
    cadastrar = st.form_submit_button("✅ Finalizar cadastro", type="primary", use_container_width=True)

if cadastrar:
    erros = []
    if not nome.strip():         erros.append("Razão Social obrigatória.")
    if not slug.strip():         erros.append("Slug da loja obrigatório.")
    if not display_name.strip(): erros.append("Nome de exibição obrigatório.")
    if not email.strip() or "@" not in email: erros.append("E-mail inválido.")
    if not cpf_cnpj.strip() or not cpf_cnpj.strip().isdigit(): erros.append("CPF/CNPJ inválido.")

    if erros:
        for e in erros:
            st.error(e)
    else:
        with st.spinner("Cadastrando parceiro..."):
            resultado = api.create_partner(
                invite_token=token,
                data={
                    "name":         nome.strip(),
                    "slug":         slug.strip().lower(),
                    "display_name": display_name.strip(),
                    "email":        email.strip(),
                    "phone":        phone.strip(),
                    "cpf_cnpj":     cpf_cnpj.strip(),
                    "city":         city.strip(),
                    "state":        state.strip().upper(),
                    "description":  descricao.strip(),
                },
            )
            if resultado:
                st.success("🎉 Cadastro realizado com sucesso!")
                st.info(
                    "A equipe Hipnus analisará seu cadastro em até 2 dias úteis. "
                    "Você receberá um e-mail de confirmação com as próximas etapas."
                )
                # Invalida token na URL para evitar reuso
                st.query_params.clear()
            else:
                st.error(
                    "❌ Erro ao finalizar cadastro. Verifique se o slug já está em uso "
                    "ou entre em contato com a Hipnus."
                )
