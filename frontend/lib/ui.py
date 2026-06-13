"""
Componentes e tema visual compartilhados da vitrine HIPNUS COSMÉTICOS.

Centraliza:
- injeção de CSS custom (visual clean/premium institucional)
- helpers de formatação (preço BRL)
- cabeçalho da marca e barra de status da API
- card de produto e badges
- estado e operações do carrinho (em st.session_state)
"""
from __future__ import annotations

import streamlit as st

from lib.config import BRAND, COLORS, CURRENCY


# ----------------------------------------------------------------- formatação
def brl(value) -> str:
    """Formata um número como moeda brasileira (R$ 1.234,56)."""
    if value is None:
        return "—"
    s = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{CURRENCY} {s}"


# ----------------------------------------------------------------------- tema
def inject_theme() -> None:
    """Injeta o CSS global da marca. Chamar no topo de cada página."""
    c = COLORS
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
        .block-container {{ padding-top: 3.2rem; max-width: 1180px; }}
        #MainMenu, footer, header[data-testid="stHeader"] {{ visibility: hidden; height: 0; }}
        section[data-testid="stSidebar"] .block-container {{ padding-top: 2rem; }}

        /* ---------- Hero / cabeçalho ---------- */
        .hip-hero {{
            background: linear-gradient(135deg, {c['primary']} 0%, {c['primary_dark']} 100%);
            color: #fff; border-radius: 20px; padding: 44px 40px;
            box-shadow: 0 18px 40px -18px rgba(91,33,182,.55);
            margin-bottom: 8px;
        }}
        .hip-hero h1 {{ font-size: 2.1rem; font-weight: 800; margin: 0 0 8px; letter-spacing: -.5px; }}
        .hip-hero p {{ font-size: 1.02rem; opacity: .92; margin: 0; max-width: 640px; }}
        .hip-hero .kicker {{
            display:inline-block; background: rgba(255,255,255,.16);
            padding: 5px 13px; border-radius: 999px; font-size:.72rem;
            font-weight:600; letter-spacing:1.4px; text-transform:uppercase; margin-bottom:14px;
        }}

        /* ---------- Brand bar ---------- */
        .hip-brand {{ display:flex; align-items:center; gap:12px; margin-bottom:6px; }}
        .hip-logo {{
            width:40px;height:40px;border-radius:11px;
            background:linear-gradient(135deg,{c['primary']},{c['accent']});
            color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center;
            font-size:1.05rem; box-shadow:0 6px 16px -6px rgba(124,58,237,.6);
        }}
        .hip-brand .name {{ font-weight:800; font-size:1.12rem; color:{c['ink']}; letter-spacing:-.3px; }}
        .hip-brand .sub {{ font-size:.74rem; color:{c['muted']}; letter-spacing:.5px; text-transform:uppercase; }}

        /* ---------- Cards de produto ---------- */
        .hip-card {{
            background:{c['bg']}; border:1px solid {c['border']}; border-radius:16px;
            padding:18px 18px 16px; min-height:330px;
            display:flex; flex-direction:column;
            transition: box-shadow .18s ease, transform .18s ease, border-color .18s;
        }}
        .hip-card .price {{ margin-top:auto; }}
        .hip-card:hover {{
            box-shadow:0 16px 34px -20px rgba(26,20,48,.4);
            transform: translateY(-3px); border-color:{c['primary']};
        }}
        .hip-thumb {{
            border-radius:12px; height:130px; margin-bottom:14px;
            background:linear-gradient(135deg,{c['surface']},#ECE6FA);
            display:flex;align-items:center;justify-content:center;
            font-size:2.1rem; color:{c['primary']};
        }}
        .hip-card .line-tag {{
            font-size:.66rem; font-weight:700; letter-spacing:.8px; text-transform:uppercase;
            color:{c['primary']}; margin-bottom:5px; display:block; min-height:14px;
        }}
        .hip-card .pname {{
            font-weight:600; font-size:.92rem; color:{c['ink']}; line-height:1.3;
            min-height:46px; margin-bottom:8px;
        }}
        .hip-card .badges {{ min-height:28px; margin-bottom:4px; }}
        .hip-card .price {{ font-weight:800; font-size:1.18rem; color:{c['ink']}; }}
        .hip-card .price small {{ font-weight:500; color:{c['muted']}; font-size:.72rem; }}
        .hip-card .floor {{ font-size:.72rem; color:{c['muted']}; }}

        .hip-badge {{
            display:inline-block; background:{c['surface']}; color:{c['primary_dark']};
            border:1px solid {c['border']}; padding:3px 10px; border-radius:999px;
            font-size:.68rem; font-weight:600; margin:2px 4px 2px 0;
        }}
        .hip-badge.gold {{ background:#FBF6E9; color:#8A6D24; border-color:#EBDFC0; }}
        .hip-badge.kit  {{ background:#EEF7EE; color:{c['success']}; border-color:#CDEBCD; }}

        .hip-section-title {{
            font-weight:800; font-size:1.32rem; color:{c['ink']};
            letter-spacing:-.4px; margin: 6px 0 2px;
        }}
        .hip-section-sub {{ color:{c['muted']}; font-size:.9rem; margin-bottom:14px; }}

        .hip-stat {{
            background:{c['surface']}; border:1px solid {c['border']}; border-radius:14px;
            padding:16px 18px; text-align:center;
        }}
        .hip-stat .v {{ font-weight:800; font-size:1.5rem; color:{c['primary']}; }}
        .hip-stat .l {{ font-size:.78rem; color:{c['muted']}; text-transform:uppercase; letter-spacing:.6px; }}

        div.stButton > button {{
            border-radius:10px; font-weight:600; border:1px solid {c['border']};
        }}
        div.stButton > button[kind="primary"] {{
            background:{c['primary']}; border-color:{c['primary']};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------- brand bar
def brand_header() -> None:
    """Renderiza a barra de marca no topo da sidebar/página."""
    st.markdown(
        f"""
        <div class="hip-brand">
          <div class="hip-logo">H</div>
          <div>
            <div class="name">HIPNUS</div>
            <div class="sub">Cosméticos</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def api_status_badge(online: bool) -> None:
    """Mostra na sidebar se a vitrine está conectada à API ou em modo demo."""
    if online:
        st.sidebar.success("API conectada", icon="🟢")
    else:
        st.sidebar.info("Modo demonstração (catálogo local)", icon="🟣")


# ------------------------------------------------------------ ícone por categoria
_CATEGORY_ICON = {
    "Mascara Liquida": "💧", "Tratamento Obrigatorio": "✨", "Home Care": "🏠",
    "Quimicas": "🧪", "Mascaras Avulsas": "🎭", "Mascaras Matizadoras": "🎨",
    "Matizadores": "🎨", "Linha Masculina": "🧔", "Encapsulados": "💊",
    "Diversos": "🧴", "Geral": "🧴",
}


def category_icon(category: str | None) -> str:
    return _CATEGORY_ICON.get(category or "", "🧴")


# ----------------------------------------------------------------- card produto
def product_card(p: dict, *, key_prefix: str = "cat") -> None:
    """
    Renderiza um card de produto com preço e botão de adicionar ao carrinho.

    `p` deve conter: id, name, line, category, floor_price,
    suggested_retail_price, is_kit. O preço exibido prioriza o preço de
    varejo sugerido; o piso é mostrado como referência.
    """
    price = p.get("suggested_retail_price") or p.get("floor_price")
    line = p.get("line") or ""
    badges = ""
    if p.get("is_kit"):
        badges += '<span class="hip-badge kit">KIT</span>'
    if (p.get("line") or "").lower() == "ouro":
        badges += '<span class="hip-badge gold">Linha Ouro</span>'

    st.markdown(
        f"""
        <div class="hip-card">
          <div class="hip-thumb">{category_icon(p.get('category'))}</div>
          <span class="line-tag">{line}&nbsp;</span>
          <div class="pname">{p['name'].title()}</div>
          <div class="badges">{badges}</div>
          <div class="price">{brl(price)}
            <small>{'sugerido' if p.get('suggested_retail_price') else 'a partir de'}</small>
          </div>
          <div class="floor">Piso parceiro: {brl(p.get('floor_price'))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Adicionar ao carrinho", key=f"{key_prefix}_add_{p['id']}", use_container_width=True):
        add_to_cart(p)
        st.toast(f"Adicionado: {p['name'].title()}", icon="🛒")


# ---------------------------------------------------------------------- carrinho
def _cart() -> dict:
    if "cart" not in st.session_state:
        st.session_state.cart = {}
    return st.session_state.cart


def add_to_cart(p: dict, qty: int = 1) -> None:
    cart = _cart()
    pid = p["id"]
    price = float(p.get("suggested_retail_price") or p.get("floor_price") or 0)
    if pid in cart:
        cart[pid]["qty"] += qty
    else:
        cart[pid] = {"id": pid, "name": p["name"].title(), "price": price, "qty": qty}


def cart_count() -> int:
    return sum(item["qty"] for item in _cart().values())


def cart_total() -> float:
    return sum(item["price"] * item["qty"] for item in _cart().values())


def remove_from_cart(pid: int) -> None:
    _cart().pop(pid, None)


def clear_cart() -> None:
    st.session_state.cart = {}


def sidebar_cart_summary() -> None:
    """Resumo compacto do carrinho na sidebar."""
    count = cart_count()
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"🛒 **Carrinho:** {count} item(ns)")
    if count:
        st.sidebar.markdown(f"**Total:** {brl(cart_total())}")
        st.sidebar.page_link("pages/4_🛒_Carrinho.py", label="Ver carrinho", icon="➡️")
