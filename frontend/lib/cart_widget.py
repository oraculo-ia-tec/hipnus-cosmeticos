"""
cart_widget.py — HIPNUS COSMÉTICOS
======================================
Carrinho flutuante global: botão fixo no canto superior direito
que mostra a quantidade de itens e redireciona para a página Carrinho.

Uso — chamar em TODAS as páginas autenticadas após inject_theme():

    from lib.cart_widget import floating_cart
    floating_cart()
"""
from __future__ import annotations
import streamlit as st


def floating_cart() -> None:
    """
    Injeta um botão flutuante no canto superior direito com o total
    de itens no carrinho. Clicando, redireciona para pages/5_Carrinho.py.
    Visível apenas para perfis que podem comprar (b2b, b2c, admin, super_admin).
    """
    perfil = st.session_state.get("perfil", "demo")
    if perfil not in ("super_admin", "admin", "b2b", "b2c"):
        return

    cart: dict = st.session_state.get("cart", {})
    total_itens = sum(item.get("qty", 0) for item in cart.values())

    badge_html = ""
    if total_itens > 0:
        badge_html = f"""
        <span id="hip-cart-badge">{total_itens}</span>
        """

    st.html(f"""
    <style>
    #hip-float-cart {{
      position: fixed;
      top: 14px;
      right: 18px;
      z-index: 999999;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      background: linear-gradient(135deg, rgba(124,58,237,.85), rgba(91,33,182,.9));
      border: 1px solid rgba(185,131,255,.45);
      border-radius: 999px;
      padding: 8px 18px 8px 14px;
      box-shadow: 0 4px 20px rgba(124,58,237,.35);
      backdrop-filter: blur(10px);
      transition: all .2s ease;
      text-decoration: none;
      color: #fff;
      font-family: 'Inter', sans-serif;
      font-size: .9rem;
      font-weight: 600;
    }}
    #hip-float-cart:hover {{
      background: linear-gradient(135deg, rgba(139,92,246,.95), rgba(109,40,217,.95));
      box-shadow: 0 6px 28px rgba(124,58,237,.55);
      transform: translateY(-1px);
    }}
    #hip-cart-icon {{
      font-size: 1.15rem;
      line-height: 1;
    }}
    #hip-cart-label {{
      font-size: .88rem;
      font-weight: 600;
      letter-spacing: .01em;
    }}
    #hip-cart-badge {{
      background: #f43f5e;
      color: #fff;
      font-size: .68rem;
      font-weight: 800;
      min-width: 20px;
      height: 20px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0 5px;
      margin-left: 2px;
      box-shadow: 0 0 0 2px rgba(124,58,237,.7);
    }}
    </style>
    <a id="hip-float-cart" href="/5_Carrinho" target="_self">
      <span id="hip-cart-icon">🛒</span>
      <span id="hip-cart-label">Carrinho</span>
      {badge_html}
    </a>
    """)
