"""
theme.py — HIPNUS COSMÉTICOS  ·  Premium Neon Edition
=======================================================
Injeta o CSS global do design system.
Chamar inject_theme() no topo de cada página, logo após st.set_page_config().

Responsabilidades:
- Tipografia premium (Playfair Display + Inter via Google Fonts)
- Shell do Streamlit (ocultar elementos padrão)
- Sidebar (logo Hipnus, user info, menu)
- Botões com neon glow
- Formulários glass
- Componentes brand (hip-*)
- Botão flutuante (FAB)
- Animações globais
- Utilitários

NÃO incluir estilos inline por página aqui.
CSS específico de página deve vir em inject_page_style() da própria tela.
"""

import streamlit as st
from . import tokens as T


def inject_theme() -> None:
    """Injeta o CSS global do design system HIPNUS Premium Neon.

    Deve ser a primeira chamada após st.set_page_config() em toda página.
    Garante consistência visual, tipografia, sidebar e componentes da marca.
    """
    st.html(f"""
    <style>
    /* ── Google Fonts Premium ─────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ── Variáveis de Design ──────────────────────────────────────────────────── */
    :root {{
      --neon-purple: #b983ff;
      --neon-violet: #7c3aed;
      --neon-cyan:   #00f5ff;
      --neon-pink:   #ff6ef7;
      --neon-gold:   #ffd700;
      --glass-bg:    rgba(26, 7, 51, 0.6);
      --glass-border: rgba(185, 131, 255, 0.25);
      --glow-purple: 0 0 20px rgba(185,131,255,0.4), 0 0 60px rgba(124,58,237,0.2);
      --glow-cyan:   0 0 20px rgba(0,245,255,0.4), 0 0 60px rgba(0,245,255,0.15);
      --glow-pink:   0 0 20px rgba(255,110,247,0.4), 0 0 60px rgba(255,110,247,0.15);
      --transition-smooth: cubic-bezier(0.16, 1, 0.3, 1);
    }}

    /* ── Animações Globais ────────────────────────────────────────────────────── */
    @keyframes shimmer {{
      0%   {{ background-position: -200% center; }}
      100% {{ background-position:  200% center; }}
    }}
    @keyframes float {{
      0%, 100% {{ transform: translateY(0px); }}
      50%       {{ transform: translateY(-8px); }}
    }}
    @keyframes pulse-neon {{
      0%, 100% {{ box-shadow: 0 0 10px rgba(185,131,255,0.3), 0 0 30px rgba(124,58,237,0.15); }}
      50%       {{ box-shadow: 0 0 25px rgba(185,131,255,0.6), 0 0 60px rgba(124,58,237,0.35), 0 0 100px rgba(124,58,237,0.1); }}
    }}
    @keyframes gradient-flow {{
      0%   {{ background-position: 0% 50%; }}
      50%  {{ background-position: 100% 50%; }}
      100% {{ background-position: 0% 50%; }}
    }}
    @keyframes fadeInUp {{
      from {{ opacity: 0; transform: translateY(20px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes borderGlow {{
      0%, 100% {{ border-color: rgba(185,131,255,0.3); }}
      50%       {{ border-color: rgba(185,131,255,0.8); }}
    }}
    @keyframes rotateSlow {{
      from {{ transform: rotate(0deg); }}
      to   {{ transform: rotate(360deg); }}
    }}
    @keyframes neon-text-pulse {{
      0%, 100% {{ text-shadow: 0 0 10px rgba(185,131,255,0.5), 0 0 20px rgba(185,131,255,0.3); }}
      50%       {{ text-shadow: 0 0 20px rgba(185,131,255,0.9), 0 0 40px rgba(185,131,255,0.6), 0 0 60px rgba(124,58,237,0.4); }}
    }}

    /* ── Tipografia Global ────────────────────────────────────────────────────── */
    html, body, [class*="css"] {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      -webkit-font-smoothing: antialiased;
    }}
    h1, h2, h3, .hip-hero h1, .hip-section-title {{
      font-family: 'Playfair Display', 'Georgia', serif;
      letter-spacing: -0.02em;
    }}

    /* ── Layout principal ─────────────────────────────────────────────────────── */
    .block-container {{ padding-top: 3rem; max-width: {T.MAX_W_DEFAULT}; }}

    /* ── Shell Streamlit ──────────────────────────────────────────────────────── */
    #MainMenu, footer, header[data-testid="stHeader"] {{
        visibility: hidden; height: 0;
    }}

    /* ── SUPRIME item "streamlit app" do topo da sidebar ─────────────────────── */
    [data-testid="stSidebarNavItems"] li:first-child,
    [data-testid="stSidebarNav"] > ul > li:first-child {{
        display: none !important;
    }}
    [data-testid="stSidebarNavItems"] a[href="/"],
    [data-testid="stSidebarNavItems"] a[href="/streamlit_app"],
    [data-testid="stSidebarNavItems"] a[href="streamlit_app"] {{
        display: none !important;
    }}
    li:has([data-testid="stSidebarNavLink"][href="/"]),
    li:has([data-testid="stSidebarNavLink"][href="/streamlit_app"]) {{
        display: none !important;
    }}

    /* ── SIDEBAR: reordenação logo+card ACIMA do menu nativo ─────────────────── */
    section[data-testid="stSidebar"] > div {{
        display: flex !important;
        flex-direction: column !important;
        background: linear-gradient(180deg, #0d0019 0%, #1a0733 50%, #0d0019 100%) !important;
    }}
    [data-testid="stSidebarHeader"]       {{ display: none !important; }}
    [data-testid="stSidebarUserContent"]  {{ order: 1 !important; padding-top: 0 !important; margin-top: 0 !important; }}
    [data-testid="stSidebarNav"]          {{ order: 2 !important; margin-top: 0 !important; padding-top: 0 !important; }}
    [data-testid="stSidebarNavSeparator"] {{ order: 2 !important; }}
    section[data-testid="stSidebar"] > div > div.block-container {{
        order: 3 !important; padding-top: 0 !important; padding-bottom: 0.5rem !important;
    }}

    /* ── Sidebar nav links premium ───────────────────────────────────────────── */
    [data-testid="stSidebarNavLink"] {{
      color: rgba(185,131,255,0.8) !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 500 !important;
      font-size: 0.88rem !important;
      padding: 10px 16px !important;
      border-radius: 10px !important;
      transition: all 0.2s var(--transition-smooth) !important;
      border: 1px solid transparent !important;
    }}
    [data-testid="stSidebarNavLink"]:hover {{
      color: #fff !important;
      background: rgba(185,131,255,0.12) !important;
      border-color: rgba(185,131,255,0.25) !important;
      text-shadow: 0 0 10px rgba(185,131,255,0.5) !important;
    }}
    [data-testid="stSidebarNavLink"][aria-current="page"] {{
      color: var(--neon-purple) !important;
      background: rgba(185,131,255,0.15) !important;
      border-color: rgba(185,131,255,0.35) !important;
      box-shadow: 0 0 15px rgba(185,131,255,0.2) !important;
    }}

    /* ── COLAPSA o gap do iframe stHtml que envolve o card do usuário ─────────── */
    [data-testid="stSidebarUserContent"] [data-testid="stHtml"] {{
        margin-bottom: 0 !important; padding-bottom: 0 !important; line-height: 0 !important;
    }}
    [data-testid="stSidebarUserContent"] [data-testid="stHtml"] iframe {{
        margin-bottom: 0 !important; display: block !important;
    }}
    [data-testid="stSidebarUserContent"] > div > div:has([data-testid="stHtml"]) {{
        gap: 0 !important; margin-bottom: 0 !important; padding-bottom: 0 !important;
    }}
    [data-testid="stSidebarUserContent"] .stVerticalBlock {{ gap: 0 !important; }}

    /* ── Logo Hipnus na sidebar — Premium ────────────────────────────────────── */
    .hip-sidebar-logo-wrap {{
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 20px 16px 14px;
        border-bottom: 1px solid rgba(185,131,255,0.2);
        margin-bottom: 4px;
        position: relative;
    }}
    .hip-sidebar-logo-wrap::after {{
        content: '';
        position: absolute;
        bottom: -1px; left: 16px; right: 16px;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--neon-purple), transparent);
        opacity: 0.6;
    }}
    .hip-sidebar-logo-icon {{
        width: 42px; height: 42px;
        border-radius: 12px;
        background: linear-gradient(135deg, {T.PRIMARY} 0%, {T.PRIMARY_DARK} 100%);
        color: #fff;
        font-family: 'Playfair Display', serif;
        font-weight: 900;
        font-size: 1.2rem;
        letter-spacing: -1px;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 4px 20px rgba(124,58,237,.5), 0 0 30px rgba(185,131,255,.2);
        flex-shrink: 0;
        animation: pulse-neon 3s ease-in-out infinite;
    }}
    .hip-sidebar-logo-text .l1 {{
        font-family: 'Playfair Display', serif;
        font-weight: 800;
        font-size: 1.05rem;
        background: linear-gradient(135deg, #fff 0%, var(--neon-purple) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -.3px;
        line-height: 1.15;
    }}
    .hip-sidebar-logo-text .l2 {{
        font-size: .65rem;
        color: rgba(185,131,255,0.6);
        letter-spacing: 2px;
        text-transform: uppercase;
    }}

    /* ── Card do usuário logado na sidebar — Neon Glass ─────────────────────── */
    .hip-sidebar-user {{
        background: linear-gradient(135deg, rgba(124,58,237,0.15) 0%, rgba(185,131,255,0.08) 100%);
        border: 1px solid rgba(185,131,255,0.2);
        border-radius: 14px;
        padding: 12px 14px 10px;
        margin: 8px 0 4px;
        backdrop-filter: blur(10px);
        transition: all 0.2s ease;
    }}
    .hip-sidebar-user:hover {{
        border-color: rgba(185,131,255,0.4);
        box-shadow: 0 0 20px rgba(185,131,255,0.15);
    }}
    .hip-sidebar-user .uname {{
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 0.95rem;
        color: #fff;
        line-height: 1.3;
    }}
    .hip-sidebar-user .umeta {{
        font-size: .78rem;
        color: rgba(185,131,255,0.7);
        margin-top: 5px;
        display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
    }}
    .hip-sidebar-user .badge-role {{
        display: inline-block;
        background: linear-gradient(135deg, {T.PRIMARY} 0%, #5b21b6 100%);
        color: #fff;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: .68rem; font-weight: 700; letter-spacing: .6px;
        text-transform: uppercase;
        box-shadow: 0 0 12px rgba(124,58,237,0.4);
    }}
    .hip-sidebar-user .badge-src {{
        display: inline-block;
        background: transparent;
        color: rgba(185,131,255,0.6);
        font-size: .72rem;
    }}

    /* ── Botão Sair na sidebar ────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] div.block-container div.stButton > button {{
        width: 100% !important;
        background: rgba(185,131,255,0.08) !important;
        color: rgba(185,131,255,0.9) !important;
        border: 1px solid rgba(185,131,255,0.25) !important;
        border-radius: 12px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.87rem !important;
        padding: 10px 0 !important;
        min-height: 42px !important;
        transition: all .2s var(--transition-smooth) !important;
    }}
    section[data-testid="stSidebar"] div.block-container div.stButton > button:hover {{
        background: rgba(185,131,255,0.18) !important;
        color: #fff !important;
        border-color: rgba(185,131,255,0.5) !important;
        box-shadow: 0 0 20px rgba(185,131,255,0.25) !important;
    }}

    /* ── brand_header() legado (compatibilidade) ─────────────────────────────── */
    .hip-brand {{
        display: flex; align-items: center; gap: 12px;
        padding: 12px 0 8px; margin-bottom: 4px;
    }}
    .hip-logo {{
        width: 38px; height: 38px; border-radius: {T.RADIUS_MD};
        background: linear-gradient(135deg, {T.PRIMARY}, {T.ACCENT});
        color: {T.TEXT_INVERSE}; font-weight: 800;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem; box-shadow: {T.SHADOW_SM};
        flex-shrink: 0;
    }}
    .hip-brand .name {{
        font-family: 'Playfair Display', serif;
        font-weight: 800; font-size: 1rem;
        color: {T.TEXT_PRIMARY}; letter-spacing: -.2px;
    }}
    .hip-brand .sub {{
        font-size: .7rem; color: {T.TEXT_MUTED};
        letter-spacing: .6px; text-transform: uppercase;
    }}

    /* ── Hero Premium Neon ────────────────────────────────────────────────────── */
    .hip-hero {{
        background: linear-gradient(135deg, {T.PRIMARY} 0%, {T.PRIMARY_DARK} 100%);
        background-size: 200% 200%;
        animation: gradient-flow 8s ease infinite;
        color: {T.TEXT_INVERSE}; border-radius: {T.RADIUS_XL};
        padding: 40px 40px 36px;
        box-shadow: {T.SHADOW_LG}, var(--glow-purple);
        margin-bottom: 8px;
        border: 1px solid rgba(185,131,255,0.2);
        position: relative; overflow: hidden;
    }}
    .hip-hero::before {{
        content: '';
        position: absolute; top: -50px; right: -50px;
        width: 200px; height: 200px; border-radius: 50%;
        background: radial-gradient(circle, rgba(185,131,255,0.15) 0%, transparent 70%);
        pointer-events: none;
    }}
    .hip-hero h1 {{
        font-family: 'Playfair Display', serif;
        font-size: 1.9rem; font-weight: 800;
        margin: 0 0 8px; letter-spacing: -.5px; line-height: 1.2;
    }}
    .hip-hero p {{ font-size: 1rem; opacity: .85; margin: 0; max-width: 600px; line-height: 1.6; }}
    .hip-hero .kicker {{
        display: inline-block;
        background: rgba(185,131,255,.2);
        border: 1px solid rgba(185,131,255,.3);
        padding: 5px 14px; border-radius: 999px;
        font-size: .65rem; font-weight: 700;
        letter-spacing: 2px; text-transform: uppercase;
        margin-bottom: 14px;
        color: var(--neon-purple);
    }}

    /* ── Seções ───────────────────────────────────────────────────────────────── */
    .hip-section-title {{
        font-family: 'Playfair Display', serif;
        font-weight: 800; font-size: 1.22rem;
        color: {T.TEXT_PRIMARY}; letter-spacing: -.3px; margin: 8px 0 2px;
    }}
    .hip-section-sub {{
        color: {T.TEXT_MUTED}; font-size: .88rem; margin-bottom: 12px;
    }}

    /* ── Cards de produto — Neon Glass ───────────────────────────────────────── */
    .hip-card {{
        background: {T.BG};
        border: 1px solid {T.BORDER};
        border-radius: {T.RADIUS_LG};
        padding: 16px 16px 14px;
        min-height: 320px; display: flex; flex-direction: column;
        transition: box-shadow .25s var(--transition-smooth), transform .25s var(--transition-smooth), border-color .25s;
        position: relative; overflow: hidden;
    }}
    .hip-card::before {{
        content: '';
        position: absolute; top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--neon-purple), transparent);
        opacity: 0;
        transition: opacity .25s ease;
    }}
    .hip-card:hover {{
        box-shadow: 0 8px 30px rgba(124,58,237,.15), 0 0 0 1px rgba(185,131,255,0.3);
        transform: translateY(-4px);
        border-color: rgba(185,131,255,0.35);
    }}
    .hip-card:hover::before {{ opacity: 1; }}
    .hip-thumb {{
        border-radius: {T.RADIUS_MD}; height: 120px; margin-bottom: 12px;
        background: linear-gradient(135deg, {T.SURFACE}, {T.PRIMARY_LIGHT});
        display: flex; align-items: center; justify-content: center;
        font-size: 1.9rem; color: {T.PRIMARY};
        position: relative; overflow: hidden;
    }}
    .hip-card .line-tag {{
        font-size: .62rem; font-weight: 700; letter-spacing: .8px;
        text-transform: uppercase; color: var(--neon-violet);
        margin-bottom: 4px; display: block; min-height: 14px;
    }}
    .hip-card .pname {{
        font-family: 'Inter', sans-serif;
        font-weight: 600; font-size: .9rem; color: {T.TEXT_PRIMARY};
        line-height: 1.35; min-height: 42px; margin-bottom: 6px;
    }}
    .hip-card .badges {{ min-height: 26px; margin-bottom: 4px; }}
    .hip-card .price {{
        margin-top: auto; font-weight: 800;
        font-size: 1.12rem; color: {T.TEXT_PRIMARY};
    }}
    .hip-card .price small {{
        font-weight: 500; color: {T.TEXT_MUTED}; font-size: .68rem;
    }}
    .hip-card .floor {{ font-size: .68rem; color: {T.TEXT_MUTED}; }}

    /* ── Badges ───────────────────────────────────────────────────────────────── */
    .hip-badge {{
        display: inline-block;
        background: {T.SURFACE}; color: {T.PRIMARY_DARK};
        border: 1px solid {T.BORDER};
        padding: 3px 10px; border-radius: {T.RADIUS_PILL};
        font-size: .65rem; font-weight: 600; margin: 2px 3px 2px 0;
        transition: all .15s ease;
    }}
    .hip-badge:hover {{
        border-color: rgba(185,131,255,0.4);
        box-shadow: 0 0 8px rgba(185,131,255,0.2);
    }}
    .hip-badge.gold  {{ background: {T.ACCENT_LIGHT}; color: #7A5A1A; border-color: #E6D5A0; }}
    .hip-badge.kit   {{ background: {T.SUCCESS_BG}; color: {T.SUCCESS}; border-color: #BBF7D0; }}
    .hip-badge.info  {{ background: {T.INFO_BG}; color: {T.INFO}; border-color: #BFDBFE; }}
    .hip-badge.neon  {{ background: rgba(185,131,255,0.12); color: var(--neon-purple); border-color: rgba(185,131,255,0.3); box-shadow: 0 0 8px rgba(185,131,255,0.2); }}

    /* ── Stat card Neon ───────────────────────────────────────────────────────── */
    .hip-stat {{
        background: linear-gradient(135deg, rgba(124,58,237,0.08) 0%, rgba(185,131,255,0.04) 100%);
        border: 1px solid rgba(185,131,255,0.2);
        border-radius: {T.RADIUS_LG}; padding: 16px 18px; text-align: center;
        transition: all .2s ease;
        position: relative; overflow: hidden;
    }}
    .hip-stat::after {{
        content: '';
        position: absolute; bottom: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--neon-violet), var(--neon-purple), var(--neon-cyan));
    }}
    .hip-stat:hover {{
        border-color: rgba(185,131,255,0.4);
        box-shadow: var(--glow-purple);
        transform: translateY(-2px);
    }}
    .hip-stat .v {{
        font-family: 'Playfair Display', serif;
        font-weight: 800; font-size: 1.6rem;
        background: linear-gradient(135deg, var(--neon-purple), var(--neon-cyan));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    .hip-stat .l {{
        font-size: .72rem; color: {T.TEXT_MUTED};
        text-transform: uppercase; letter-spacing: .6px; margin-top: 4px;
    }}

    /* ── Surface card (genérico) ─────────────────────────────────────────────── */
    .hip-surface {{
        background: {T.SURFACE}; border: 1px solid {T.BORDER};
        border-radius: {T.RADIUS_LG}; padding: 20px 22px;
        transition: border-color .2s ease;
    }}
    .hip-surface:hover {{ border-color: rgba(185,131,255,0.25); }}
    .hip-surface.highlight {{
        background: {T.PRIMARY_LIGHT}; border-color: {T.BORDER_STRONG};
    }}
    .hip-surface.success {{ background: {T.SUCCESS_BG}; border-color: #BBF7D0; }}
    .hip-surface.warning {{ background: {T.WARNING_BG}; border-color: #FDE68A; }}
    .hip-surface.danger  {{ background: {T.DANGER_BG};  border-color: #FECACA; }}
    .hip-surface.glass {{
        background: rgba(26,7,51,0.4);
        border-color: rgba(185,131,255,0.2);
        backdrop-filter: blur(12px);
    }}

    /* ── Empty state ──────────────────────────────────────────────────────────── */
    .hip-empty {{
        display: flex; flex-direction: column;
        align-items: center; text-align: center;
        padding: 48px 24px; color: {T.TEXT_MUTED};
    }}
    .hip-empty .icon {{
        font-size: 2.4rem; margin-bottom: 12px;
        animation: float 3s ease-in-out infinite;
    }}
    .hip-empty h3 {{
        font-family: 'Playfair Display', serif;
        color: {T.TEXT_PRIMARY}; font-size: 1rem;
        font-weight: 700; margin-bottom: 6px;
    }}
    .hip-empty p {{
        font-size: .88rem; max-width: 32ch;
        line-height: 1.5; margin-bottom: 16px;
    }}

    /* ── Botões Premium Neon ──────────────────────────────────────────────────── */
    div.stButton > button {{
        font-family: 'Inter', sans-serif !important;
        border-radius: {T.RADIUS_MD}; font-weight: 600;
        border: 1px solid {T.BORDER};
        transition: all .2s var(--transition-smooth);
        letter-spacing: 0.2px;
    }}
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {T.PRIMARY} 0%, #5b21b6 100%) !important;
        border-color: transparent !important;
        color: #fff !important;
        box-shadow: 0 4px 20px rgba(124,58,237,.35), 0 0 0 0 rgba(185,131,255,0);
    }}
    div.stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #8b44f6 0%, {T.PRIMARY} 100%) !important;
        box-shadow: 0 8px 30px rgba(124,58,237,.5), 0 0 30px rgba(185,131,255,.2) !important;
        transform: translateY(-2px);
    }}
    div.stButton > button:focus-visible {{
        outline: 2px solid {T.FOCUS_RING}; outline-offset: 2px;
        box-shadow: 0 0 0 4px rgba(185,131,255,.25) !important;
    }}

    /* ── Botão Flutuante FAB ──────────────────────────────────────────────────── */
    .hip-fab {{
        position: fixed;
        bottom: 28px; right: 28px;
        width: 58px; height: 58px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--neon-violet), #5b21b6);
        color: #fff;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.4rem;
        box-shadow: 0 4px 20px rgba(124,58,237,.5), var(--glow-purple);
        cursor: pointer;
        z-index: 9999;
        border: 1px solid rgba(185,131,255,0.3);
        transition: all .25s var(--transition-smooth);
        animation: pulse-neon 3s ease-in-out infinite;
        text-decoration: none;
    }}
    .hip-fab:hover {{
        transform: scale(1.12) translateY(-3px);
        box-shadow: 0 8px 40px rgba(124,58,237,.7), 0 0 50px rgba(185,131,255,.35) !important;
        animation: none;
    }}
    .hip-fab-label {{
        position: fixed;
        bottom: 38px; right: 96px;
        background: rgba(13,0,25,0.9);
        border: 1px solid rgba(185,131,255,0.3);
        color: rgba(185,131,255,0.9);
        padding: 6px 12px;
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
        font-size: .75rem; font-weight: 600;
        pointer-events: none;
        opacity: 0;
        transition: opacity .2s ease;
        backdrop-filter: blur(8px);
        white-space: nowrap;
    }}
    .hip-fab:hover + .hip-fab-label {{ opacity: 1; }}

    /* ── Auth / Login layout ──────────────────────────────────────────────────── */
    .hip-auth-wrap {{
        max-width: {T.MAX_W_FORM}; margin: 0 auto; padding: 0 8px;
    }}
    .hip-auth-logo {{
        text-align: center;
        padding: 48px 0 32px;
    }}
    .hip-auth-logo .logo-icon {{
        width: 72px; height: 72px;
        border-radius: 20px;
        background: linear-gradient(135deg, {T.PRIMARY} 0%, {T.PRIMARY_DARK} 100%);
        color: {T.TEXT_INVERSE};
        font-family: 'Playfair Display', serif;
        font-weight: 900; font-size: 2rem;
        display: inline-flex;
        align-items: center; justify-content: center;
        box-shadow: 0 8px 24px rgba(124,58,237,.40), var(--glow-purple);
        margin-bottom: 18px;
        animation: pulse-neon 3s ease-in-out infinite;
    }}
    .hip-auth-logo .wordmark {{
        font-family: 'Playfair Display', serif;
        font-size: 2.2rem; font-weight: 800;
        background: linear-gradient(135deg, {T.PRIMARY}, var(--neon-purple));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -1.5px; line-height: 1;
    }}
    .hip-auth-logo .sub {{
        font-size: .82rem; color: {T.TEXT_MUTED};
        letter-spacing: 3px; margin-top: 5px;
        text-transform: uppercase;
    }}
    .hip-auth-logo .tagline {{
        font-size: .82rem; color: {T.TEXT_FAINT};
        margin-top: 10px; line-height: 1.5;
    }}
    .hip-auth-logo .divider-dot {{
        display: inline-block;
        width: 5px; height: 5px; border-radius: 50%;
        background: var(--neon-purple);
        margin: 16px auto 0;
        box-shadow: 0 0 8px var(--neon-purple);
    }}
    .hip-auth-card {{
        background: {T.BG};
        border: 1px solid {T.BORDER};
        border-radius: {T.RADIUS_XL};
        padding: 32px 32px 28px;
        box-shadow: 0 8px 32px -8px rgba(124,58,237,.18), 0 2px 8px -2px rgba(26,20,48,.08);
        max-width: {T.MAX_W_FORM};
        margin: 0 auto;
        transition: box-shadow .25s ease, border-color .25s ease;
    }}
    .hip-auth-card:hover {{
        box-shadow: 0 8px 40px rgba(124,58,237,.25), 0 0 0 1px rgba(185,131,255,.2);
        border-color: rgba(185,131,255,0.3);
    }}
    .hip-auth-card-title {{
        font-family: 'Inter', sans-serif;
        font-size: 1.08rem; font-weight: 700;
        color: {T.TEXT_PRIMARY}; margin-bottom: 20px;
        display: flex; align-items: center; gap: 8px;
    }}
    .hip-auth-card-title::before {{
        content: '';
        display: inline-block; width: 4px; height: 18px;
        background: linear-gradient(180deg, var(--neon-purple), var(--neon-violet));
        border-radius: 2px;
        box-shadow: 0 0 8px rgba(185,131,255,0.5);
    }}
    .hip-auth-footer {{
        text-align: center; margin-top: 24px;
        font-size: .71rem; color: {T.TEXT_FAINT};
        max-width: {T.MAX_W_FORM}; margin-left: auto; margin-right: auto;
        line-height: 1.6;
    }}

    /* ── Formulários Premium ──────────────────────────────────────────────────── */
    .hip-form-section {{ margin-bottom: 12px; }}
    .hip-form-label {{
        font-family: 'Inter', sans-serif;
        font-size: .78rem; font-weight: 600;
        color: {T.TEXT_MUTED}; letter-spacing: .3px;
        text-transform: uppercase; margin-bottom: 6px; display: block;
    }}
    .hip-form-hint {{
        font-size: .75rem; color: {T.TEXT_FAINT};
        margin-top: 4px; line-height: 1.4;
    }}
    [data-testid="stTextInput"] > div > div > input {{
        font-family: 'Inter', sans-serif !important;
        border-radius: 12px !important;
        border: 1.5px solid {T.BORDER} !important;
        transition: border-color .2s ease, box-shadow .2s ease !important;
    }}
    [data-testid="stTextInput"] > div > div > input:focus {{
        border-color: var(--neon-violet) !important;
        box-shadow: 0 0 0 3px rgba(124,58,237,.12), 0 0 15px rgba(185,131,255,.1) !important;
    }}

    /* ── Divider Neon ─────────────────────────────────────────────────────────── */
    .hip-divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(185,131,255,0.4), transparent);
        margin: 16px 0;
        border: none;
    }}

    /* ── Scrollbar premium ────────────────────────────────────────────────────── */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(180deg, var(--neon-violet), #5b21b6);
        border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--neon-purple); }}

    /* ── Selection color ─────────────────────────────────────────────────────── */
    ::selection {{
        background: rgba(185,131,255,0.25);
        color: #1a0a2e;
    }}
    </style>
    """)


def inject_login_style() -> None:
    """Injeta estilos específicos da tela de login premium neon (layout=wide, split-screen).

    Chamar após inject_theme() somente em streamlit_app.py.
    Gerencia: supressão de sidebar, padding zero no container, layout full-viewport.
    """
    st.html("""
    <style>
    /* Esconde sidebar e controle de colapso na página de login */
    [data-testid="stSidebar"]        { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* Remove padding padrão do container para permitir full-viewport */
    [data-testid="stMainBlockContainer"],
    [data-testid="stMain"] > div,
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
        margin: 0 !important;
    }

    /* Largura total nos inputs e botões do form de login */
    [data-testid="stTextInputRootElement"] {
        max-width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
        width: 100%;
        border-radius: 12px !important;
        min-height: 50px !important;
        font-size: .96rem !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Garante que o bloco HTML do painel esquerdo ocupe todo o lado */
    [data-testid="stHtml"] {
        display: block;
        width: 100%;
    }
    </style>
    """)
