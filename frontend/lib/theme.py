"""
theme.py — HIPNUS COSMÉTICOS  ·  Premium Neon Edition 2026
============================================================
Injeta o CSS global do design system.
Chamar inject_theme() no topo de cada página, logo após st.set_page_config().
"""

import streamlit as st
from . import tokens as T


def inject_theme() -> None:
    """Injeta o CSS global do design system HIPNUS Premium Neon."""
    st.html(f"""
    <style>
    /* ── Google Fonts Premium ────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800;900&family=Inter:wght@300;400;500;600;700;800;900&family=Syne:wght@700;800&display=swap');

    /* ── Variáveis de Design ────────────────────────────────────────── */
    :root {{
      --neon-purple:  #b983ff;
      --neon-violet:  #7c3aed;
      --neon-cyan:    #00f5ff;
      --neon-pink:    #ff6ef7;
      --neon-gold:    #ffd700;
      --glass-bg:     rgba(26, 7, 51, 0.6);
      --glass-border: rgba(185, 131, 255, 0.25);
      --glow-purple:  0 0 20px rgba(185,131,255,0.4), 0 0 60px rgba(124,58,237,0.2);
      --glow-cyan:    0 0 20px rgba(0,245,255,0.4),   0 0 60px rgba(0,245,255,0.15);
      --glow-pink:    0 0 20px rgba(255,110,247,0.4), 0 0 60px rgba(255,110,247,0.15);
      --transition-smooth: cubic-bezier(0.16, 1, 0.3, 1);
      --font-display: 'Syne', 'Playfair Display', serif;
      --font-body:    'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* ── Animações Globais ────────────────────────────────────────── */
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

    /* ── Tipografia Global ────────────────────────────────────────── */
    html, body, [class*="css"] {{
      font-family: var(--font-body);
      -webkit-font-smoothing: antialiased;
    }}
    h1, h2, h3, .hip-hero h1, .hip-section-title {{
      font-family: var(--font-display);
      letter-spacing: -0.02em;
    }}

    /* ── Layout principal ─────────────────────────────────────────── */
    .block-container {{ padding-top: 3rem; max-width: {T.MAX_W_DEFAULT}; }}

    /* ── Shell Streamlit ─────────────────────────────────────────── */
    #MainMenu, footer, header[data-testid="stHeader"] {{
        visibility: hidden; height: 0;
    }}

    /* ── SUPRIME item streamlit app da sidebar ──────────────────────── */
    [data-testid="stSidebarNavItems"] li:first-child,
    [data-testid="stSidebarNav"] > ul > li:first-child {{ display: none !important; }}
    [data-testid="stSidebarNavItems"] a[href="/"],
    [data-testid="stSidebarNavItems"] a[href="/streamlit_app"],
    [data-testid="stSidebarNavItems"] a[href="streamlit_app"] {{ display: none !important; }}
    li:has([data-testid="stSidebarNavLink"][href="/"]),
    li:has([data-testid="stSidebarNavLink"][href="/streamlit_app"]) {{ display: none !important; }}

    /* ── SIDEBAR: estrutura dark premium mesh ──────────────────────── */
    section[data-testid="stSidebar"] > div {{
        display: flex !important;
        flex-direction: column !important;
        background:
          radial-gradient(ellipse at 10% 10%, rgba(124,58,237,.18) 0%, transparent 55%),
          radial-gradient(ellipse at 90% 85%, rgba(0,245,255,.06) 0%, transparent 50%),
          linear-gradient(180deg, #0a0015 0%, #110028 50%, #0a0015 100%) !important;
    }}

    /* ── SIDEBAR: reordenação ───────────────────────────────────── */
    [data-testid="stSidebarHeader"]       {{ display: none !important; }}
    [data-testid="stSidebarUserContent"]  {{ order: 1 !important; padding-top: 0 !important; margin-top: 0 !important; }}
    [data-testid="stSidebarNav"]          {{ order: 2 !important; display: none !important; }}
    [data-testid="stSidebarNavSeparator"] {{ display: none !important; }}
    section[data-testid="stSidebar"] > div > div.block-container {{
        order: 3 !important; padding-top: 0 !important; padding-bottom: 0.5rem !important;
    }}

    /* ── Collapse gap iframes html ────────────────────────────────── */
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

    /* ── Scrollbar premium ─────────────────────────────────────────── */
    ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(180deg, #7c3aed, #5b21b6);
        border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{ background: #b983ff; }}

    /* ── Hip brand_header() legado ────────────────────────────────── */
    .hip-brand {{
        display: flex; align-items: center; gap: 12px;
        padding: 12px 0 8px; margin-bottom: 4px;
    }}
    .hip-logo {{
        width: 38px; height: 38px; border-radius: {T.RADIUS_MD};
        background: linear-gradient(135deg, {T.PRIMARY}, {T.ACCENT});
        color: {T.TEXT_INVERSE}; font-weight: 800;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem; box-shadow: {T.SHADOW_SM}; flex-shrink: 0;
    }}
    .hip-brand .name {{
        font-family: 'Syne', sans-serif;
        font-weight: 800; font-size: 1rem; color: {T.TEXT_PRIMARY}; letter-spacing: -.2px;
    }}
    .hip-brand .sub {{
        font-size: .7rem; color: {T.TEXT_MUTED}; letter-spacing: .6px; text-transform: uppercase;
    }}

    /* ── Hero Premium Neon ────────────────────────────────────────── */
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
        content: ''; position: absolute; top: -50px; right: -50px;
        width: 200px; height: 200px; border-radius: 50%;
        background: radial-gradient(circle, rgba(185,131,255,0.15) 0%, transparent 70%);
        pointer-events: none;
    }}
    .hip-hero h1 {{
        font-family: 'Syne', sans-serif;
        font-size: 1.9rem; font-weight: 800;
        margin: 0 0 8px; letter-spacing: -.5px; line-height: 1.2;
    }}
    .hip-hero p {{ font-size: 1rem; opacity: .85; margin: 0; max-width: 600px; line-height: 1.6; }}
    .hip-hero .kicker {{
        display: inline-block;
        background: rgba(185,131,255,.2); border: 1px solid rgba(185,131,255,.3);
        padding: 5px 14px; border-radius: 999px;
        font-size: .65rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
        margin-bottom: 14px; color: var(--neon-purple);
    }}

    /* ── Seções ────────────────────────────────────────────────────────────── */
    .hip-section-title {{
        font-family: 'Syne', sans-serif;
        font-weight: 800; font-size: 1.22rem;
        color: {T.TEXT_PRIMARY}; letter-spacing: -.3px; margin: 8px 0 2px;
    }}
    .hip-section-sub {{ color: {T.TEXT_MUTED}; font-size: .88rem; margin-bottom: 12px; }}

    /* ── Cards de produto ─────────────────────────────────────────────── */
    .hip-card {{
        background: {T.BG}; border: 1px solid {T.BORDER};
        border-radius: {T.RADIUS_LG}; padding: 16px 16px 14px;
        min-height: 320px; display: flex; flex-direction: column;
        transition: box-shadow .25s var(--transition-smooth), transform .25s var(--transition-smooth), border-color .25s;
        position: relative; overflow: hidden;
    }}
    .hip-card::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--neon-purple), transparent);
        opacity: 0; transition: opacity .25s ease;
    }}
    .hip-card:hover {{
        box-shadow: 0 8px 30px rgba(124,58,237,.15), 0 0 0 1px rgba(185,131,255,0.3);
        transform: translateY(-4px); border-color: rgba(185,131,255,0.35);
    }}
    .hip-card:hover::before {{ opacity: 1; }}
    .hip-thumb {{
        border-radius: {T.RADIUS_MD}; height: 120px; margin-bottom: 12px;
        background: linear-gradient(135deg, {T.SURFACE}, {T.PRIMARY_LIGHT});
        display: flex; align-items: center; justify-content: center;
        font-size: 1.9rem; color: {T.PRIMARY}; position: relative; overflow: hidden;
    }}
    .hip-card .line-tag {{
        font-size: .62rem; font-weight: 700; letter-spacing: .8px;
        text-transform: uppercase; color: var(--neon-violet);
        margin-bottom: 4px; display: block; min-height: 14px;
    }}
    .hip-card .pname {{
        font-family: 'Inter', sans-serif; font-weight: 600; font-size: .9rem;
        color: {T.TEXT_PRIMARY}; line-height: 1.35; min-height: 42px; margin-bottom: 6px;
    }}
    .hip-card .badges {{ min-height: 26px; margin-bottom: 4px; }}
    .hip-card .price {{
        margin-top: auto; font-weight: 800; font-size: 1.12rem; color: {T.TEXT_PRIMARY};
    }}
    .hip-card .price small {{ font-weight: 500; color: {T.TEXT_MUTED}; font-size: .68rem; }}
    .hip-card .floor {{ font-size: .68rem; color: {T.TEXT_MUTED}; }}

    /* ── Badges ────────────────────────────────────────────────────── */
    .hip-badge {{
        display: inline-block; background: {T.SURFACE}; color: {T.PRIMARY_DARK};
        border: 1px solid {T.BORDER}; padding: 3px 10px; border-radius: {T.RADIUS_PILL};
        font-size: .65rem; font-weight: 600; margin: 2px 3px 2px 0;
        transition: all .15s ease;
    }}
    .hip-badge:hover {{ border-color: rgba(185,131,255,0.4); box-shadow: 0 0 8px rgba(185,131,255,0.2); }}
    .hip-badge.gold  {{ background: {T.ACCENT_LIGHT}; color: #7A5A1A; border-color: #E6D5A0; }}
    .hip-badge.kit   {{ background: {T.SUCCESS_BG}; color: {T.SUCCESS}; border-color: #BBF7D0; }}
    .hip-badge.info  {{ background: {T.INFO_BG}; color: {T.INFO}; border-color: #BFDBFE; }}
    .hip-badge.neon  {{ background: rgba(185,131,255,0.12); color: var(--neon-purple); border-color: rgba(185,131,255,0.3); box-shadow: 0 0 8px rgba(185,131,255,0.2); }}

    /* ── Stat card Neon ─────────────────────────────────────────────── */
    .hip-stat {{
        background: linear-gradient(135deg, rgba(124,58,237,0.08) 0%, rgba(185,131,255,0.04) 100%);
        border: 1px solid rgba(185,131,255,0.2);
        border-radius: {T.RADIUS_LG}; padding: 16px 18px; text-align: center;
        transition: all .2s ease; position: relative; overflow: hidden;
    }}
    .hip-stat::after {{
        content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, var(--neon-violet), var(--neon-purple), var(--neon-cyan));
    }}
    .hip-stat:hover {{
        border-color: rgba(185,131,255,0.4);
        box-shadow: var(--glow-purple); transform: translateY(-2px);
    }}
    .hip-stat .v {{
        font-family: 'Syne', sans-serif; font-weight: 800; font-size: 1.6rem;
        background: linear-gradient(135deg, var(--neon-purple), var(--neon-cyan));
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }}
    .hip-stat .l {{
        font-size: .72rem; color: {T.TEXT_MUTED};
        text-transform: uppercase; letter-spacing: .6px; margin-top: 4px;
    }}

    /* ── Surface card ─────────────────────────────────────────────── */
    .hip-surface {{
        background: {T.SURFACE}; border: 1px solid {T.BORDER};
        border-radius: {T.RADIUS_LG}; padding: 20px 22px;
        transition: border-color .2s ease;
    }}
    .hip-surface:hover {{ border-color: rgba(185,131,255,0.25); }}
    .hip-surface.highlight {{ background: {T.PRIMARY_LIGHT}; border-color: {T.BORDER_STRONG}; }}
    .hip-surface.success   {{ background: {T.SUCCESS_BG}; border-color: #BBF7D0; }}
    .hip-surface.warning   {{ background: {T.WARNING_BG}; border-color: #FDE68A; }}
    .hip-surface.danger    {{ background: {T.DANGER_BG};  border-color: #FECACA; }}
    .hip-surface.glass {{
        background: rgba(26,7,51,0.4); border-color: rgba(185,131,255,0.2);
        backdrop-filter: blur(12px);
    }}

    /* ── Empty state ─────────────────────────────────────────────────── */
    .hip-empty {{
        display: flex; flex-direction: column;
        align-items: center; text-align: center;
        padding: 48px 24px; color: {T.TEXT_MUTED};
    }}
    .hip-empty .icon {{ font-size: 2.4rem; margin-bottom: 12px; animation: float 3s ease-in-out infinite; }}
    .hip-empty h3 {{
        font-family: 'Syne', sans-serif;
        color: {T.TEXT_PRIMARY}; font-size: 1rem; font-weight: 700; margin-bottom: 6px;
    }}
    .hip-empty p {{ font-size: .88rem; max-width: 32ch; line-height: 1.5; margin-bottom: 16px; }}

    /* ── Botões Premium Neon ──────────────────────────────────────────── */
    div.stButton > button {{
        font-family: 'Inter', sans-serif !important;
        border-radius: {T.RADIUS_MD}; font-weight: 600;
        border: 1px solid {T.BORDER};
        transition: all .2s var(--transition-smooth);
        letter-spacing: 0.2px;
    }}
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {T.PRIMARY} 0%, #5b21b6 100%) !important;
        border-color: transparent !important; color: #fff !important;
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

    /* ── Divider Neon ─────────────────────────────────────────────────── */
    .hip-divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(185,131,255,0.4), transparent);
        margin: 16px 0; border: none;
    }}

    /* ── Selection color ─────────────────────────────────────────────── */
    ::selection {{ background: rgba(185,131,255,0.25); color: #1a0a2e; }}
    </style>
    """)


def inject_login_style() -> None:
    """Injeta estilos específicos da tela de login premium neon."""
    st.html("""
    <style>
    [data-testid="stSidebar"]        { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stMainBlockContainer"],
    [data-testid="stMain"] > div,
    .block-container {
        padding: 0 !important; max-width: 100% !important; margin: 0 !important;
    }
    [data-testid="stTextInputRootElement"] { max-width: 100% !important; }
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
        width: 100%; border-radius: 12px !important;
        min-height: 50px !important; font-size: .96rem !important;
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stHtml"] { display: block; width: 100%; }
    </style>
    """)
