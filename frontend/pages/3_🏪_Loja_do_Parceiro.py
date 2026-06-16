"""
3_Loja_do_Parceiro.py — HIPNUS COSMÉTICOS
==========================================
Página exclusiva B2B: catálogo com preços de piso (floor_price),
lote mínimo e políticas comerciais para profissionais e revendedores.

Acesso restrito: apenas perfis b2b, admin e super_admin.

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

st.set_page_config(page_title="Loja do Parceiro · HIPNUS", page_icon="🏪", layout="wide")
ui.inject_theme()

require_auth(perfis_permitidos=["b2b", "admin", "super_admin"])

# ─── Sidebar ───────────────────────────────────────────────────────────
ui.brand_header()                       # 1. Logo
sidebar_user_info()                     # 2. Usuário (ACIMA do menu)
# --- [menu nativo Streamlit aqui] ---
ui.api_status_badge(api.api_online())   # 4. Status API
ui.sidebar_cart_summary()               # 5. Carrinho
sidebar_logout_button()                 # 6. SAIR (ABAIXO do menu)

products = api.get_products()

st.markdown('<div class="hip-section-title">🏪 Loja do Parceiro</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hip-section-sub">Preços de piso exclusivos para profissionais e revendedores Hipnus.</div>',
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------- filtros
f1, f2 = st.columns([2, 1.5])
search   = f1.text_input("Buscar produto", placeholder="Ex.: máscara, ouro...")
line     = f2.selectbox("Linha", ["Todas"] + api.list_lines())
only_kits = st.checkbox("Apenas kits / combos")

def _matches(p: dict) -> bool:
    if search and search.lower() not in p["name"].lower():
        return False
    if line != "Todas" and p.get("line") != line:
        return False
    if only_kits and not p.get("is_kit"):
        return False
    return True

results = [p for p in products if _matches(p)]
st.caption(f"{len(results)} produto(s) encontrado(s).")

if not results:
    st.info("Nenhum produto corresponde aos filtros selecionados.")
else:
    per_row = 4
    for i in range(0, len(results), per_row):
        cols = st.columns(per_row)
        for col, p in zip(cols, results[i : i + per_row]):
            with col:
                ui.product_card(p, key_prefix="b2b")

st.markdown("---")
st.caption(
    "Os preços exibidos são o **piso parceiro** (floor_price). "
    "O preço final ao consumidor é definido por cada parceiro em sua loja."
)
