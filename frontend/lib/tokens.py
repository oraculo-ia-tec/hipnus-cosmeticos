"""
tokens.py — TÁLYA COSMÉTICOS
=================================
Tokens semânticos do design system.
Centraliza todas as referências visuais em um único lugar.
Importe este módulo onde precisar de valores de cor, espaçamento ou raio.

Paleta alinhada com talya-cosmeticos.html (warm rose/gold premium).
"""

# ─ Paleta base ────────────────────────────────────────────────────────
PRIMARY        = "#b76e79"   # rosa Tálya (accent-1)
PRIMARY_DARK   = "#8f4f58"   # rosa escuro
PRIMARY_LIGHT  = "#f5e6e8"   # rosa claro
ACCENT         = "#c9a04e"   # dourado (accent-2)
ACCENT_LIGHT   = "#f9f2e3"   # dourado claro
ACCENT_WARM    = "#7c5c4a"   # marrom quente (accent-3)

# ─ Superfícies ───────────────────────────────────────────────────────
BG             = "#fbf6f2"   # off-white quente
BG_DEEP        = "#f5ece4"   # off-white mais profundo
SURFACE        = "#f1e4da"   # superfície quente
SURFACE_STRONG = "#e8d5c8"   # superfície forte
SURFACE_DARK   = "#3a2620"   # marrom escuro (fundo escuro)

# ─ Texto ─────────────────────────────────────────────────────────────
TEXT_PRIMARY   = "#3a2620"   # marrom escuro
TEXT_SECONDARY = "#6b4f43"   # marrom médio
TEXT_MUTED     = "#a08876"   # marrom claro/muted
TEXT_FAINT     = "#c4b0a6"   # muito claro
TEXT_INVERSE   = "#fbf6f2"   # texto sobre fundo escuro

# ─ Feedback ──────────────────────────────────────────────────────────
SUCCESS        = "#16A34A"
SUCCESS_BG     = "#F0FDF4"
WARNING        = "#D97706"
WARNING_BG     = "#FFFBEB"
DANGER         = "#DC2626"
DANGER_BG      = "#FEF2F2"
INFO           = "#2563EB"
INFO_BG        = "#EFF6FF"

# ─ Bordas ────────────────────────────────────────────────────────────
BORDER         = "rgba(183,110,121,0.18)"  # glass-border do HTML
BORDER_STRONG  = "#d4a8b0"
FOCUS_RING     = "#b76e79"

# ─ Raio de borda ─────────────────────────────────────────────────────
RADIUS_SM      = "8px"
RADIUS_MD      = "12px"
RADIUS_LG      = "16px"
RADIUS_XL      = "20px"
RADIUS_PILL    = "999px"

# ─ Sombras ───────────────────────────────────────────────────────────
SHADOW_SM      = "0 2px 8px -2px rgba(58,38,32,.10)"
SHADOW_MD      = "0 8px 24px -8px rgba(58,38,32,.18)"
SHADOW_LG      = "0 16px 40px -16px rgba(183,110,121,.28)"

# ─ Tipografia ────────────────────────────────────────────────────────
FONT_BODY      = "'Manrope', 'Inter', sans-serif"
FONT_DISPLAY   = "'Cormorant', 'Playfair Display', serif"
FONT_STACK     = FONT_BODY   # alias legado
FONT_URL       = (
    "https://fonts.googleapis.com/css2?"
    "family=Cormorant:ital,wght@0,400;0,600;0,700;1,500"
    "&family=Manrope:wght@300;400;500;600;700;800"
    "&display=swap"
)

# ─ Larguras máximas ──────────────────────────────────────────────────
MAX_W_FORM     = "440px"
MAX_W_DEFAULT  = "1180px"

# ─ Assets ────────────────────────────────────────────────────────────
LOGO_PATH      = "frontend/static/logomarca.jpg"
AVATAR_PATH    = "frontend/static/talya_avatar.png"

# ─ Moeda ─────────────────────────────────────────────────────────────
CURRENCY       = "R$"
