"""
Página de Loja do Parceiro — vitrine pública individual de cada parceiro.

O cliente acessa pelo *slug* da loja. Mostra o branding do parceiro e as
ofertas (produtos Hipnus + preço de venda definido pelo parceiro, sempre
acima do piso). Depende da API do backend (endpoints /stores).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from lib import api, ui  # noqa: E402

st.set_page_config(page_title="Loja do Parceiro · HIPNUS", page_icon="🏪", layout="wide")
ui.inject_theme()

ui.brand_header()
online = api.api_online()
ui.api_status_badge(online)
ui.sidebar_cart_summary()

st.markdown('<div class="hip-section-title">Loja do parceiro</div>', unsafe_allow_html=True)
st.markdown('<div class="hip-section-sub">Cada parceiro Hipnus tem sua própria vitrine. '
            'Informe o identificador (slug) da loja.</div>', unsafe_allow_html=True)

slug = st.text_input("Slug da loja", placeholder="ex.: salao-bela-hair")

if not online:
    st.info("As lojas de parceiros são carregadas da API. Inicie o backend "
            "(`uvicorn app.main:app`) e cadastre um parceiro para visualizar uma loja.")

if slug:
    store = api.get_store(slug)
    if not store:
        st.warning(f"Loja '{slug}' não encontrada.")
    else:
        # Cabeçalho da loja
        st.markdown(
            f"""
            <div class="hip-hero" style="padding:30px 34px;">
              <span class="kicker">Loja parceira oficial Hipnus</span>
              <h1>{store['display_name']}</h1>
              <p>{store.get('description') or 'Produtos oficiais Hipnus Cosméticos.'}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        listings = api.get_store_listings(store["id"])
        products = {p["id"]: p for p in api.get_products()}
        if not listings:
            st.info("Esta loja ainda não possui produtos publicados.")
        else:
            st.caption(f"{len(listings)} produto(s) à venda nesta loja.")
            per_row = 4
            for i in range(0, len(listings), per_row):
                cols = st.columns(per_row)
                for col, lst in zip(cols, listings[i : i + per_row]):
                    base = products.get(lst["product_id"], {})
                    # Card com o preço de venda do parceiro (não o sugerido).
                    p = {**base,
                         "id": lst.get("id", lst["product_id"]),
                         "suggested_retail_price": lst["sale_price"]}
                    with col:
                        ui.product_card(p, key_prefix=f"store{store['id']}")
