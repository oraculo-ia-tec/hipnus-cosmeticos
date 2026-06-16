"""
0_Home.py — HIPNUS COSMÉTICOS
================================
Página inicial da vitrine (pós-login).
Hero da marca, indicadores do portfólio, destaques e atalhos.

Acesso: qualquer perfil autenticado (admin, b2b, b2c, demo).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth, sidebar_user_info, sidebar_logout_button
from lib.config import BRAND

st.set_page_config(page_title="HIPNUS COSMÉTICOS", page_icon="💜", layout="wide")
ui.inject_theme()

# ─ Guarda de autenticação ───────────────────────────────────
require_auth()

# ─ Sidebar ──────────────────────────────────────────
ui.brand_header()
sidebar_user_info()
ui.api_status_badge(api.api_online())
ui.sidebar_cart_summary()
sidebar_logout_button()

# ─ Dados ────────────────────────────────────────────────
products = api.get_products()
lines    = api.list_lines()
cats     = api.list_categories()

# ─ Hero ─────────────────────────────────────────────────
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

# ─ Indicadores ──────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
kits = sum(1 for p in products if p.get("is_kit"))
for col, v, l in [
    (c1, len(products), "Produtos"),
    (c2, len(lines),    "Linhas da marca"),
    (c3, len(cats),     "Categorias"),
    (c4, kits,          "Kits & combos"),
]:
    col.markdown(
        f'<div class="hip-stat"><div class="v">{v}</div><div class="l">{l}</div></div>',
        unsafe_allow_html=True,
    )

# Atalho para catálogo — sem st.page_link para evitar erros de path
st.markdown("")
st.info("🛒 Use o menu lateral para acessar o **Catálogo** completo de produtos.")

# ─ Linhas da marca ────────────────────────────────────────
st.markdown('<div class="hip-section-title">Linhas da marca</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hip-section-sub">Coleções desenvolvidas para cada necessidade capilar.</div>',
    unsafe_allow_html=True,
)
line_html = "".join(f'<span class="hip-badge">{ln}</span>' for ln in lines)
st.markdown(line_html, unsafe_allow_html=True)

# ─ Destaques ───────────────────────────────────────────
st.markdown("")
st.markdown('<div class="hip-section-title">Destaques</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hip-section-sub">Kits de tratamento e itens premium da linha Ouro.</div>',
    unsafe_allow_html=True,
)

featured = [p for p in products if p.get("is_kit")][:4]
if len(featured) < 4:
    featured += [
        p for p in products
        if (p.get("line") or "").lower() == "ouro"
    ][: 4 - len(featured)]
featured = featured[:4] or products[:4]

cols = st.columns(4)
for col, p in zip(cols, featured):
    with col:
        ui.product_card(p, key_prefix="home")

st.markdown("---")
st.caption(
    "HIPNUS COSMÉTICOS · vitrine para consumidor final e profissional. "
    "Preços de varejo são sugestões; cada parceiro define o preço final em sua loja."
)
