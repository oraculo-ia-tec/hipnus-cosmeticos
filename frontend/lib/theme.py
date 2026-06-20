"""
theme.py — HIPNUS COSMÉTICOS
=================================
Injeta o CSS global do design system.
Chamar inject_theme() no topo de cada página, logo após st.set_page_config().

Responsabilidades:
- Tipografia global
- Shell do Streamlit (ocultar elementos padrão)
- Sidebar (logo Hipnus, user info, menu)
- Botões
- Formulários
- Componentes brand (hip-*)
- Utilitários

NÃO incluir estilos inline por página aqui.
CSS específico de página deve vir em inject_page_style() da própria tela.
"""

import streamlit as st
from . import tokens as T


def inject_theme() -> None:
    """Injeta o CSS global do design system HIPNUS.

    Deve ser a primeira chamada após st.set_page_config() em toda página.
    Garante consistência visual, tipografia, sidebar e componentes da marca.
    """
    st.html(f"""
    <style>
    /* ── Fonte ─────────────────────────────────────────────────── */
    @import url('{T.FONT_URL}');
    html, body, [class*="css"] {{ font-family: {T.FONT_STACK}; }}

    /* ── Layout principal ───────────────────────────────────────────── */
    .block-container {{ padding-top: 3rem; max-width: {T.MAX_W_DEFAULT}; }}

    /* ── Shell Streamlit ────────────────────────────────────────────── */
    #MainMenu, footer, header[data-testid="stHeader"] {{
        visibility: hidden; height: 0;
    }}

    /* ── SUPRIME item "streamlit app" do topo da sidebar ───────────────── */
    /* Seletor 1: primeiro li da nav nativa (todas as versões) */
    [data-testid="stSidebarNavItems"] li:first-child,
    [data-testid="stSidebarNav"] > ul > li:first-child,
    nav[data-testid="stSidebarNav"] ul li:first-child {{
        display: none !important;
    }}
    /* Seletor 2: links por href exatos */
    [data-testid="stSidebarNavItems"] a[href="/"],
    [data-testid="stSidebarNavItems"] a[href="/streamlit_app"],
    [data-testid="stSidebarNavItems"] a[href="streamlit_app"] {{
        display: none !important;
    }}
    /* Seletor 3: stSidebarNavLink que contenha o texto “streamlit app” (cobre v1.35+) */
    [data-testid="stSidebarNavLink"]:has(p:first-child) {{}}
    li:has([data-testid="stSidebarNavLink"][href="/"]),
    li:has([data-testid="stSidebarNavLink"][href="/streamlit_app"]),
    li:has([data-testid="stSidebarNavLink"][href="streamlit_app"]) {{
        display: none !important;
    }}
    /* Seletor 4: qualquer nav link cujo texto visível seja exatamente "streamlit app" */
    [data-testid="stSidebarNavLink"] p {{
        text-transform: none;
    }}
    [data-testid="stSidebarNavItems"] li:first-of-type {{
        display: none !important;
    }}

    /* ── Sidebar shell ─────────────────────────────────────────────────── */
    [data-testid="stSidebarHeader"] {{ display: none !important; }}
    section[data-testid="stSidebar"] > div {{ padding-top: 0 !important; }}
    section[data-testid="stSidebar"] .block-container {{ padding-top: 0.5rem; }}

    /* ── Logo Hipnus no topo da sidebar ───────────────────────────────── */
    .hip-sidebar-logo-wrap {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 16px 14px 10px;
        border-bottom: 1px solid {T.BORDER};
        margin-bottom: 2px;
    }}
    .hip-sidebar-logo-icon {{
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: linear-gradient(135deg, {T.PRIMARY} 0%, {T.PRIMARY_DARK} 100%);
        color: {T.TEXT_INVERSE};
        font-weight: 900;
        font-size: 1.15rem;
        letter-spacing: -1px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(124,58,237,.35);
        flex-shrink: 0;
    }}
    .hip-sidebar-logo-text .l1 {{
        font-weight: 800;
        font-size: .95rem;
        color: {T.TEXT_PRIMARY};
        letter-spacing: -.3px;
        line-height: 1.15;
    }}
    .hip-sidebar-logo-text .l2 {{
        font-size: .65rem;
        color: {T.TEXT_MUTED};
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }}

    /* ── Card do usuário logado na sidebar ───────────────────────────────── */
    .hip-sidebar-user {{
        background: linear-gradient(135deg, #f3f0ff 0%, #ede8fb 100%);
        border: 1px solid #d9d3f5;
        border-radius: {T.RADIUS_MD};
        padding: 10px 14px 9px;
        margin: 8px 0 4px;
    }}
    .hip-sidebar-user .uname {{
        font-weight: 700;
        font-size: .93rem;
        color: {T.TEXT_PRIMARY};
        line-height: 1.3;
    }}
    .hip-sidebar-user .umeta {{
        font-size: .71rem;
        color: {T.TEXT_MUTED};
        margin-top: 3px;
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
    }}
    .hip-sidebar-user .badge-role {{
        display: inline-block;
        background: {T.PRIMARY};
        color: {T.TEXT_INVERSE};
        padding: 2px 8px;
        border-radius: {T.RADIUS_PILL};
        font-size: .62rem;
        font-weight: 700;
        letter-spacing: .4px;
        text-transform: uppercase;
    }}
    .hip-sidebar-user .badge-src {{
        display: inline-block;
        background: transparent;
        color: {T.TEXT_MUTED};
        font-size: .62rem;
    }}

    /* ── brand_header() legado (compatibilidade) ───────────────────────────── */
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
        font-weight: 800; font-size: 1rem;
        color: {T.TEXT_PRIMARY}; letter-spacing: -.2px;
    }}
    .hip-brand .sub {{
        font-size: .7rem; color: {T.TEXT_MUTED};
        letter-spacing: .6px; text-transform: uppercase;
    }}

    /* ── Hero ─────────────────────────────────────────────────────────────── */
    .hip-hero {{
        background: linear-gradient(135deg, {T.PRIMARY} 0%, {T.PRIMARY_DARK} 100%);
        color: {T.TEXT_INVERSE}; border-radius: {T.RADIUS_XL};
        padding: 40px 40px 36px; box-shadow: {T.SHADOW_LG};
        margin-bottom: 8px;
    }}
    .hip-hero h1 {{
        font-size: 1.9rem; font-weight: 800;
        margin: 0 0 8px; letter-spacing: -.5px; line-height: 1.2;
    }}
    .hip-hero p {{ font-size: 1rem; opacity: .9; margin: 0; max-width: 600px; }}
    .hip-hero .kicker {{
        display: inline-block;
        background: rgba(255,255,255,.15);
        padding: 4px 12px; border-radius: {T.RADIUS_PILL};
        font-size: .68rem; font-weight: 700;
        letter-spacing: 1.4px; text-transform: uppercase;
        margin-bottom: 12px;
    }}

    /* ── Seções ───────────────────────────────────────────────────────────────── */
    .hip-section-title {{
        font-weight: 800; font-size: 1.22rem;
        color: {T.TEXT_PRIMARY}; letter-spacing: -.3px; margin: 8px 0 2px;
    }}
    .hip-section-sub {{
        color: {T.TEXT_MUTED}; font-size: .88rem; margin-bottom: 12px;
    }}

    /* ── Cards de produto ───────────────────────────────────────────────────────────── */
    .hip-card {{
        background: {T.BG}; border: 1px solid {T.BORDER};
        border-radius: {T.RADIUS_LG}; padding: 16px 16px 14px;
        min-height: 320px; display: flex; flex-direction: column;
        transition: box-shadow .18s ease, transform .18s ease, border-color .18s;
    }}
    .hip-card:hover {{
        box-shadow: {T.SHADOW_MD};
        transform: translateY(-2px);
        border-color: {T.BORDER_STRONG};
    }}
    .hip-thumb {{
        border-radius: {T.RADIUS_MD}; height: 120px; margin-bottom: 12px;
        background: linear-gradient(135deg, {T.SURFACE}, {T.PRIMARY_LIGHT});
        display: flex; align-items: center; justify-content: center;
        font-size: 1.9rem; color: {T.PRIMARY};
    }}
    .hip-card .line-tag {{
        font-size: .62rem; font-weight: 700; letter-spacing: .8px;
        text-transform: uppercase; color: {T.PRIMARY};
        margin-bottom: 4px; display: block; min-height: 14px;
    }}
    .hip-card .pname {{
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

    /* ── Badges ──────────────────────────────────────────────────────────────────────── */
    .hip-badge {{
        display: inline-block;
        background: {T.SURFACE}; color: {T.PRIMARY_DARK};
        border: 1px solid {T.BORDER};
        padding: 3px 10px; border-radius: {T.RADIUS_PILL};
        font-size: .65rem; font-weight: 600; margin: 2px 3px 2px 0;
    }}
    .hip-badge.gold  {{ background: {T.ACCENT_LIGHT}; color: #7A5A1A; border-color: #E6D5A0; }}
    .hip-badge.kit   {{ background: {T.SUCCESS_BG}; color: {T.SUCCESS}; border-color: #BBF7D0; }}
    .hip-badge.info  {{ background: {T.INFO_BG}; color: {T.INFO}; border-color: #BFDBFE; }}

    /* ── Stat card ────────────────────────────────────────────────────────────────────── */
    .hip-stat {{
        background: {T.SURFACE}; border: 1px solid {T.BORDER};
        border-radius: {T.RADIUS_LG}; padding: 16px 18px; text-align: center;
    }}
    .hip-stat .v {{
        font-weight: 800; font-size: 1.45rem; color: {T.PRIMARY};
    }}
    .hip-stat .l {{
        font-size: .72rem; color: {T.TEXT_MUTED};
        text-transform: uppercase; letter-spacing: .6px; margin-top: 2px;
    }}

    /* ── Surface card (genérico) ────────────────────────────────────────────────────────────── */
    .hip-surface {{
        background: {T.SURFACE}; border: 1px solid {T.BORDER};
        border-radius: {T.RADIUS_LG}; padding: 20px 22px;
    }}
    .hip-surface.highlight {{
        background: {T.PRIMARY_LIGHT}; border-color: {T.BORDER_STRONG};
    }}
    .hip-surface.success {{
        background: {T.SUCCESS_BG}; border-color: #BBF7D0;
    }}
    .hip-surface.warning {{
        background: {T.WARNING_BG}; border-color: #FDE68A;
    }}
    .hip-surface.danger  {{
        background: {T.DANGER_BG}; border-color: #FECACA;
    }}

    /* ── Empty state ────────────────────────────────────────────────────────────────────────────── */
    .hip-empty {{
        display: flex; flex-direction: column;
        align-items: center; text-align: center;
        padding: 48px 24px; color: {T.TEXT_MUTED};
    }}
    .hip-empty .icon {{ font-size: 2.4rem; margin-bottom: 12px; }}
    .hip-empty h3 {{
        color: {T.TEXT_PRIMARY}; font-size: 1rem;
        font-weight: 700; margin-bottom: 6px;
    }}
    .hip-empty p {{
        font-size: .88rem; max-width: 32ch;
        line-height: 1.5; margin-bottom: 16px;
    }}

    /* ── Botões ────────────────────────────────────────────────────────────────────────── */
    div.stButton > button {{
        border-radius: {T.RADIUS_MD}; font-weight: 600;
        border: 1px solid {T.BORDER}; transition: all .16s ease;
    }}
    div.stButton > button[kind="primary"] {{
        background: {T.PRIMARY}; border-color: {T.PRIMARY}; color: {T.TEXT_INVERSE};
    }}
    div.stButton > button[kind="primary"]:hover {{
        background: {T.PRIMARY_DARK}; border-color: {T.PRIMARY_DARK};
    }}
    div.stButton > button:focus-visible {{
        outline: 2px solid {T.FOCUS_RING}; outline-offset: 2px;
    }}

    /* ── Auth / Login layout ──────────────────────────────────────────────────────── */
    .hip-auth-wrap {{
        max-width: {T.MAX_W_FORM}; margin: 0 auto; padding: 0 8px;
    }}

    /* Login: logo / identidade */
    .hip-auth-logo {{
        text-align: center;
        padding: 48px 0 32px;
    }}
    .hip-auth-logo .logo-icon {{
        width: 72px; height: 72px;
        border-radius: 20px;
        background: linear-gradient(135deg, {T.PRIMARY} 0%, {T.PRIMARY_DARK} 100%);
        color: {T.TEXT_INVERSE};
        font-weight: 900; font-size: 2rem;
        display: inline-flex;
        align-items: center; justify-content: center;
        box-shadow: 0 8px 24px rgba(124,58,237,.40);
        margin-bottom: 18px;
    }}
    .hip-auth-logo .wordmark {{
        font-size: 2.2rem; font-weight: 800;
        color: {T.PRIMARY}; letter-spacing: -1.5px; line-height: 1;
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
        width: 5px; height: 5px;
        border-radius: 50%;
        background: {T.ACCENT};
        margin: 16px auto 0;
    }}

    /* Login: card principal */
    .hip-auth-card {{
        background: {T.BG};
        border: 1px solid {T.BORDER};
        border-radius: {T.RADIUS_XL};
        padding: 32px 32px 28px;
        box-shadow: 0 8px 32px -8px rgba(124,58,237,.18), 0 2px 8px -2px rgba(26,20,48,.08);
        max-width: {T.MAX_W_FORM};
        margin: 0 auto;
    }}
    .hip-auth-card-title {{
        font-size: 1.08rem;
        font-weight: 700;
        color: {T.TEXT_PRIMARY};
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .hip-auth-card-title::before {{
        content: "";
        display: inline-block;
        width: 4px; height: 18px;
        background: {T.PRIMARY};
        border-radius: 2px;
    }}

    /* Login: footer */
    .hip-auth-footer {{
        text-align: center; margin-top: 24px;
        font-size: .71rem; color: {T.TEXT_FAINT};
        max-width: {T.MAX_W_FORM}; margin-left: auto; margin-right: auto;
        line-height: 1.6;
    }}

    /* ── Formulários ──────────────────────────────────────────────────────────────────────────── */
    .hip-form-section {{ margin-bottom: 12px; }}
    .hip-form-label {{
        font-size: .78rem; font-weight: 600;
        color: {T.TEXT_MUTED}; letter-spacing: .3px;
        text-transform: uppercase; margin-bottom: 6px; display: block;
    }}
    .hip-form-hint {{
        font-size: .75rem; color: {T.TEXT_FAINT};
        margin-top: 4px; line-height: 1.4;
    }}

    /* ── Divider ─────────────────────────────────────────────────────────────────────────────── */
    .hip-divider {{
        height: 1px; background: {T.BORDER};
        margin: 16px 0;
    }}
    </style>
    """)


def inject_login_style() -> None:
    """Injeta estilos específicos da tela de login (sidebar e container centralizados).

    Chamar após inject_theme() somente em streamlit_app.py.
    """
    st.html("""
    <style>
    [data-testid="stSidebar"]        { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    div[data-testid="stHorizontalBlock"] {
        max-width: 440px !important;
        margin: 0 auto !important;
    }
    div[data-testid="stHorizontalBlock"] button { width: 100%; }
    div[data-testid="stTextInputRootElement"] {
        max-width: 440px !important;
        margin: 0 auto !important;
    }
    /* inputs com mais destaque no login */
    div[data-testid="stTextInputRootElement"] input {
        border-radius: 10px !important;
        font-size: .97rem !important;
    }
    div[data-testid="stTextInputRootElement"] input:focus {
        box-shadow: 0 0 0 3px rgba(124,58,237,.18) !important;
    }
    /* bloco de colunas dos botões login/demo */
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
        border-radius: 10px !important;
        font-size: .97rem !important;
        min-height: 44px !important;
    }
    </style>
    """)
