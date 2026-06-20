"""
0_Home.py — HIPNUS COSMÉTICOS
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from lib import api, ui
from lib.auth import require_auth, sidebar_logo, sidebar_user_info
from lib.config import BRAND
from lib import components, commerce

st.set_page_config(page_title="HIPNUS COSMÉTICOS", page_icon="💜", layout="wide")
ui.inject_theme()
require_auth()

# ─ Sidebar ──────────────────────────────────────────────────────
sidebar_logo()
sidebar_user_info()

# ─ Dados ─────────────────────────────────────────────────────────────
products = api.get_products()
lines    = api.list_lines()
cats     = api.list_categories()

components.page_header(title=BRAND["tagline"], subtitle=BRAND["promise"], kicker="Marketplace oficial da marca")

kits = sum(1 for p in products if p.get("is_kit"))
c1, c2, c3, c4 = st.columns(4)
for col, value, label in [
    (c1, len(products), "Produtos"), (c2, len(lines), "Linhas da marca"),
    (c3, len(cats), "Categorias"), (c4, kits, "Kits & combos"),
]:
    with col:
        components.stat_card(value, label)

components.divider()

with st.popover("💡 Como navegar pela vitrine", use_container_width=False):
    st.markdown("Use o **menu lateral** para acessar o Catálogo completo, as Linhas da marca e a Loja do Parceiro.")

components.section_title("Linhas da marca", subtitle="Coleções desenvolvidas para cada necessidade capilar.")
line_html = "".join(f'<span class="hip-badge">{ln}</span>' for ln in lines)
st.html(line_html)
components.divider()

components.section_title("Destaques", subtitle="Kits de tratamento e itens premium da linha Ouro.")
featured = [p for p in products if p.get("is_kit")][:4]
if len(featured) < 4:
    featured += [p for p in products if (p.get("line") or "").lower() == "ouro"][:4 - len(featured)]
featured = featured[:4] or products[:4]
cols = st.columns(4)
for col, p in zip(cols, featured):
    with col:
        commerce.product_card(p, key_prefix="home", on_add=ui.add_to_cart)
components.divider()
st.caption("HIPNUS COSMÉTICOS · vitrine para consumidor final e profissional.")
