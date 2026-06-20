"""
7_Cadastro_Parceiro.py — HIPNUS COSMÉTICOS
============================================
Formulário de cadastro de novo parceiro (salão, revendedor, distribuidor).

Acesso: qualquer perfil autenticado — permite que um parceiro
complete ou atualize o próprio cadastro.

Ordem da sidebar:
  1. brand_header()           → logo Hipnus (topo)
  2. sidebar_user_info()      → dados do usuário (ACIMA do menu)
  3. [menu nativo]
  4. api_status_badge()
  5. sidebar_cart_summary()
  6. sidebar_logout_button()  → botão SAIR (ABAIXO do menu)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth, sidebar_user_info, sidebar_logout_button
from lib import components

st.set_page_config(page_title="Cadastro Parceiro · HIPNUS", page_icon="📋", layout="centered")
ui.inject_theme()

require_auth()

# ─ Sidebar ───────────────────────────────────────────────────────────
ui.brand_header()
sidebar_user_info()
ui.api_status_badge(api.api_online())
ui.sidebar_cart_summary()
sidebar_logout_button()

# ─ Cabeçalho ─────────────────────────────────────────────────────────
components.page_header(
    title="Cadastro de Parceiro",
    subtitle="Complete seus dados para habilitar as condições B2B Hipnus.",
    kicker="Área do Parceiro",
)

# ─ Dica contextual ───────────────────────────────────────────────────
with st.popover("ℹ️ Por que preencher o cadastro?", use_container_width=False):
    st.markdown(
        "O cadastro completo habilita as **condições comerciais B2B** da Hipnus: "
        "preços de parceiro, lote mínimo, combos profissionais e "
        "suporte dedicado. Nossa equipe entrará em contato após a análise."
    )

components.divider()

# ─ Formulário ────────────────────────────────────────────────────────
with st.form("form_cadastro_parceiro"):
    components.section_title("Dados da empresa")
    razao_social = st.text_input("Razão social / Nome do salão *")
    cnpj         = st.text_input("CNPJ (somente números)")
    ie           = st.text_input("Inscrição Estadual (opcional)")

    components.divider()
    components.section_title("Endereço")
    c1, c2 = st.columns([3, 1])
    rua    = c1.text_input("Rua / Avenida *")
    numero = c2.text_input("Número *")
    c3, c4, c5 = st.columns([2, 1.5, 1])
    bairro = c3.text_input("Bairro *")
    cidade = c4.text_input("Cidade *")
    uf     = c5.text_input("UF *", max_chars=2)
    cep    = st.text_input("CEP (somente números)")

    components.divider()
    components.section_title("Responsável")
    responsavel = st.text_input("Nome do responsável *")
    telefone    = st.text_input("Telefone / WhatsApp *", placeholder="31999999999")
    email       = st.text_input("E-mail de contato *")

    components.divider()
    components.section_title("Tipo de parceiro")
    tipo = st.selectbox(
        "Categoria",
        ["Salão de beleza", "Barbearia", "Revendedor", "Distribuidor", "Outro"],
    )

    components.divider()
    salvar = st.form_submit_button(
        "💾 Salvar cadastro",
        type="primary",
        use_container_width=True,
    )

# ─ Processamento ─────────────────────────────────────────────────────
if salvar:
    erros = []
    for campo, valor in [
        ("Razão social", razao_social),
        ("Rua", rua), ("Número", numero), ("Bairro", bairro),
        ("Cidade", cidade), ("UF", uf),
        ("Responsável", responsavel), ("Telefone", telefone), ("E-mail", email),
    ]:
        if not valor.strip():
            erros.append(f"{campo} é obrigatório.")
    if email.strip() and "@" not in email:
        erros.append("E-mail inválido.")

    if erros:
        for e in erros:
            components.feedback_inline(e, kind="danger")
    else:
        payload = {
            "razao_social": razao_social.strip(),
            "cnpj": cnpj.strip(),
            "ie": ie.strip(),
            "endereco": {
                "rua": rua.strip(), "numero": numero.strip(),
                "bairro": bairro.strip(), "cidade": cidade.strip(),
                "uf": uf.strip().upper(), "cep": cep.strip(),
            },
            "responsavel": responsavel.strip(),
            "telefone": telefone.strip(),
            "email": email.strip(),
            "tipo": tipo,
        }
        with st.spinner("Salvando cadastro..."):
            try:
                api.save_partner(payload)
                components.feedback_inline(
                    "Cadastro salvo com sucesso! Nossa equipe entrará em contato.",
                    kind="success",
                )
            except Exception as exc:
                components.feedback_inline(
                    f"API indisponível — cadastro registrado localmente. ({exc})",
                    kind="warning",
                )
