"""
components.py — HIPNUS COSMÉTICOS
=====================================
Wrappers de componentes de UI genéricos e reutilizáveis.

Todos os componentes recebem dados simples e retornam None.
Nenhum componente acessa session_state diretamente —
callbacks e estado ficam na página que chama o componente.
"""

from __future__ import annotations
import streamlit as st
from . import tokens as T


# ─────────────────────────────────────────────── cabeçalho de página
def page_header(
    title: str,
    subtitle: str | None = None,
    kicker: str | None = None,
) -> None:
    """Renderiza o hero institucional de uma página.

    Args:
        title:    Título principal da página (H1).
        subtitle: Texto de suporte (opcional).
        kicker:   Etiqueta de categoria em pill acima do título (opcional).

    Exemplo::

        components.page_header(
            title="Tratamento capilar profissional, direto da fonte.",
            subtitle="Vitrine para consumidor final e profissional.",
            kicker="Marketplace oficial da marca",
        )
    """
    kicker_html = f'<span class="kicker">{kicker}</span>' if kicker else ""
    subtitle_html = f'<p>{subtitle}</p>' if subtitle else ""
    st.html(f"""
    <div class="hip-hero">
        {kicker_html}
        <h1>{title}</h1>
        {subtitle_html}
    </div>
    """)


# ─────────────────────────────────────────────── título de seção
def section_title(title: str, subtitle: str | None = None) -> None:
    """Renderiza título e subtítulo de seção com a tipografia da marca."""
    sub_html = f'<div class="hip-section-sub">{subtitle}</div>' if subtitle else ""
    st.html(f"""
    <div class="hip-section-title">{title}</div>
    {sub_html}
    """)


# ─────────────────────────────────────────────── surface card
def surface_card(content_html: str, variant: str = "default") -> None:
    """Envolve conteúdo HTML em um card de superfície institucional.

    Args:
        content_html: HTML interno do card.
        variant:      'default' | 'highlight' | 'success' | 'warning' | 'danger'

    Exemplo::

        components.surface_card("<p>Texto</p>", variant="highlight")
    """
    cls = "hip-surface" + (f" {variant}" if variant != "default" else "")
    st.html(f'<div class="{cls}">{content_html}</div>')


# ─────────────────────────────────────────────── empty state
def empty_state(
    icon: str,
    title: str,
    message: str,
    action_label: str | None = None,
    action_key: str | None = None,
) -> bool:
    """Renderiza o estado vazio de uma seção.

    Args:
        icon:         Emoji ou caractere unicode de ícone.
        title:        Título do estado vazio.
        message:      Mensagem explicativa para o usuário.
        action_label: Texto do botão de ação (opcional).
        action_key:   Key única do botão (obrigatória se action_label for informado).

    Returns:
        True se o botão de ação for clicado, False caso contrário.

    Exemplo::

        clicked = components.empty_state(
            icon="🛒",
            title="Seu carrinho está vazio",
            message="Adicione produtos no catálogo para começar.",
            action_label="Ir para o catálogo",
            action_key="empty_cart_action",
        )
        if clicked:
            st.switch_page("pages/2_Catalogo.py")
    """
    st.html(f"""
    <div class="hip-empty">
        <div class="icon">{icon}</div>
        <h3>{title}</h3>
        <p>{message}</p>
    </div>
    """)
    if action_label and action_key:
        col = st.columns([1, 2, 1])[1]
        return col.button(action_label, key=action_key, use_container_width=True, type="primary")
    return False


# ─────────────────────────────────────────────── divider
def divider() -> None:
    """Linha divisória visual no padrão da marca."""
    st.html('<div class="hip-divider"></div>')


# ─────────────────────────────────────────────── feedback inline
def feedback_inline(
    message: str,
    kind: str = "info",
) -> None:
    """Exibe uma mensagem de feedback inline no estilo da marca.

    Args:
        message: Texto da mensagem.
        kind:    'info' | 'success' | 'warning' | 'danger'

    Uso preferencial para mensagens dentro de formulários ou cards.
    Para alertas de contexto rápido, use st.popover().
    Para confirmações, use st.dialog().
    """
    icons = {
        "info":    ("ℹ️", "info"),
        "success": ("✅", "success"),
        "warning": ("⚠️", "warning"),
        "danger":  ("❌", "danger"),
    }
    icon, variant = icons.get(kind, ("ℹ️", "info"))
    surface_card(
        f'<span style="font-size:.88rem;">{icon} {message}</span>',
        variant=variant,
    )


# ─────────────────────────────────────────────── stat card
def stat_card(value: str | int, label: str) -> None:
    """Renderiza um card de indicador numérico (KPI).

    Args:
        value: Valor numérico ou string a exibir em destaque.
        label: Rótulo descritivo abaixo do valor.

    Uso: sempre dentro de st.columns() para criar grade de KPIs.
    """
    st.html(f"""
    <div class="hip-stat">
        <div class="v">{value}</div>
        <div class="l">{label}</div>
    </div>
    """)
