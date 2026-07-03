
"""
Guia de botões e estilos para Streamlit - HIPNUS COSMETICOS
===========================================================

Principios aplicados:
- Usar st.button com type='primary' para acoes principais.
- Usar key unica por botao para possibilitar CSS especifico no DOM.
- Aplicar CSS com seletor baseado em .st-key-<key>, padrao discutido na comunidade Streamlit.
- Botao Sair deve ficar sempre visivel na sidebar e com estilo de acao destrutiva/sessao.
"""

import streamlit as st

HIPNUS_BUTTON_CSS = """
<style>
button[kind="primary"] {
    background: linear-gradient(135deg, #111827, #7c3aed);
    color: #ffffff;
    border: 0;
    border-radius: 12px;
    font-weight: 600;
    min-height: 44px;
}
button[kind="primary"]:hover {
    filter: brightness(1.05);
}
button[kind="secondary"] {
    border-radius: 12px;
    border: 1px solid #d1d5db;
}

/* Botao Sair especifico */
div[class*="st-key-btn_logout"] .stButton button {
    background: #ffffff;
    color: #b91c1c;
    border: 1px solid #fecaca;
    border-radius: 12px;
    font-weight: 700;
    width: 100%;
}
div[class*="st-key-btn_logout"] .stButton button:hover {
    background: #fef2f2;
    border-color: #fca5a5;
}

/* CTA de compra */
div[class*="st-key-btn_checkout"] .stButton button,
div[class*="st-key-btn_add_cart"] .stButton button {
    background: linear-gradient(135deg, #7c3aed, #ec4899);
    color: white;
    border: 0;
    border-radius: 12px;
    font-weight: 700;
}

/* Botoes operacionais de parceiro/admin */
div[class*="st-key-btn_save"] .stButton button,
div[class*="st-key-btn_update"] .stButton button,
div[class*="st-key-btn_filter"] .stButton button {
    background: #111827;
    color: white;
    border: 0;
    border-radius: 10px;
}
</style>
"""


def inject_button_theme():
    st.markdown(HIPNUS_BUTTON_CSS, unsafe_allow_html=True)


def sidebar_logout_button(on_logout):
    with st.sidebar:
        st.markdown("---")
        if st.button("Sair", key="btn_logout", use_container_width=True):
            on_logout()


def example_buttons():
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("Adicionar ao carrinho", key="btn_add_cart_1", type="primary", use_container_width=True)
    with c2:
        st.button("Salvar", key="btn_save_product", use_container_width=True)
    with c3:
        st.button("Atualizar estoque", key="btn_update_stock", use_container_width=True)
