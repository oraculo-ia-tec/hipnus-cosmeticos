"""
HIPNUS COSMÉTICOS — Home (entry point Streamlit Cloud)
=========================================================
Este arquivo é o entry point real do Streamlit Cloud.
Se o usuário não estiver autenticado, renderiza a tela de login
inline (importando Login como módulo). Caso contrário, exibe
a vitrine principal.

Executar: streamlit run frontend/Home.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

st.set_page_config(
    page_title="HIPNUS COSMÉTICOS",
    page_icon="💜",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Guarda de autenticação ─────────────────────────────────
if not st.session_state.get("autenticado"):
    # Renderiza o login inline sem st.switch_page
    import importlib, types
    # Executa o Login.py como script dentro do mesmo runtime
    login_path = Path(__file__).parent / "Login.py"
    spec = importlib.util.spec_from_file_location("Login", login_path)
    login_mod = importlib.util.module_from_spec(spec)
    # Não executa set_page_config de novo (já foi chamado acima)
    # Monkey-patch para ignorar set_page_config duplicado
    _orig_set_page_config = st.set_page_config
    st.set_page_config = lambda **kwargs: None
    try:
        spec.loader.exec_module(login_mod)
    finally:
        st.set_page_config = _orig_set_page_config
    st.stop()

# ── Vitrine (usuário autenticado) ────────────────────────────
st.set_page_config = lambda **kwargs: None  # já configurado

from lib import api, ui
from lib.config import BRAND

ui.inject_theme()
ui.brand_header()
ui.api_status_badge(api.api_online())
st.sidebar.markdown("Navegue pela vitrine usando o menu acima.")
ui.sidebar_cart_summary()

products = api.get_products()
lines    = api.list_lines()
cats     = api.list_categories()

st.markdown(
    f"""
    <div class="hip-hero">
      <span class="kicker">Marketplace oficial da marca</span>
      <h1>{BRAND['tagline']}</h1>
      <p>{BRAND['promise']}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
kits = sum(1 for p in products if p.get("is_kit"))
for col, v, l in [
    (c1, len(products),  "Produtos"),
    (c2, len(lines),     "Linhas da marca"),
    (c3, len(cats),      "Categorias"),
    (c4, kits,           "Kits & combos"),
]:
    col.markdown(f'<div class="hip-stat"><div class="v">{v}</div><div class="l">{l}</div></div>',
                 unsafe_allow_html=True)

st.markdown("")
st.page_link("pages/1_🛒_Catálogo.py", label="Explorar catálogo completo", icon="🛒")

st.markdown('<div class="hip-section-title">Linhas da marca</div>', unsafe_allow_html=True)
st.markdown('<div class="hip-section-sub">Coleções desenvolvidas para cada necessidade capilar.</div>',
            unsafe_allow_html=True)
line_html = "".join(f'<span class="hip-badge">{ln}</span>' for ln in lines)
st.markdown(line_html, unsafe_allow_html=True)

st.markdown("")
st.markdown('<div class="hip-section-title">Destaques</div>', unsafe_allow_html=True)
st.markdown('<div class="hip-section-sub">Kits de tratamento e itens premium da linha Ouro.</div>',
            unsafe_allow_html=True)

featured = [p for p in products if p.get("is_kit")][:4]
if len(featured) < 4:
    featured += [p for p in products if (p.get("line") or "").lower() == "ouro"][: 4 - len(featured)]
featured = featured[:4] or products[:4]

cols = st.columns(4)
for col, p in zip(cols, featured):
    with col:
        ui.product_card(p, key_prefix="home")

st.markdown("---")
st.caption("HIPNUS COSMÉTICOS · vitrine para consumidor final e profissional.")
