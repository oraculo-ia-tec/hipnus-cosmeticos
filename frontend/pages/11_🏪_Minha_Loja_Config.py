"""
11_🏪_Minha_Loja_Config.py — HIPNUS COSMÉTICOS
Skill: Loja Personalizada — Módulo A
Cada parceiro configura sua loja: slug, banner, bio, produtos em destaque, cor.
"""
from __future__ import annotations
import sys, re, json
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from lib import ui, components
from lib.auth import require_auth, build_sidebar

st.set_page_config(
    page_title="Minha Loja · HIPNUS",
    page_icon="🏪",
    layout="wide",
)
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin", "b2b", "b2c"])
build_sidebar()

components.page_header(
    title="Minha Loja",
    subtitle="Configure seu link exclusivo, personalize sua vitrine e compartilhe com seus clientes.",
    kicker="🏪 Loja Personalizada",
)

# ── CSS padrão do sistema ─────────────────────────────────────────────────────
st.html("""
<style>
.loja-cfg-card {
    background: rgba(124,58,237,0.04);
    border: 1px solid rgba(185,131,255,0.18);
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 18px;
}
.loja-cfg-label {
    font-size: .72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .8px;
    color: #b983ff; margin-bottom: 14px;
}
.link-box {
    background: rgba(124,58,237,0.10);
    border: 1.5px solid rgba(168,85,247,0.40);
    border-radius: 10px;
    padding: 14px 18px;
    font-family: monospace;
    font-size: 1rem;
    color: #e879f9;
    word-break: break-all;
    margin: 8px 0 16px;
}
.preview-loja {
    background: linear-gradient(135deg,#1a0f2e 0%,#2d1558 50%,#1a0f2e 100%);
    border: 1px solid rgba(168,85,247,.25);
    border-radius: 20px;
    padding: 32px 28px;
    position: relative;
    overflow: hidden;
}
.preview-loja::before {
    content:""; position:absolute; inset:0;
    background:radial-gradient(ellipse 60% 80% at 80% 50%,rgba(168,85,247,.15),transparent);
    pointer-events:none;
}
.preview-nome   { font-size:1.6rem; font-weight:800; color:#f5d0fe; margin-bottom:6px; }
.preview-bio    { color:#c4b5fd; font-size:.92rem; line-height:1.5; margin-bottom:16px; }
.preview-badge  {
    display:inline-block;
    background:rgba(168,85,247,.2); border:1px solid rgba(168,85,247,.4);
    color:#e879f9; border-radius:99px; padding:3px 14px;
    font-size:.75rem; font-weight:700; letter-spacing:.4px;
}
.produto-destaque-tag {
    display:inline-block;
    background:rgba(124,58,237,.15); border:1px solid rgba(124,58,237,.3);
    color:#c4b5fd; border-radius:8px; padding:3px 10px;
    font-size:.75rem; margin:3px 3px 3px 0;
}
.stat-mini { text-align:center; }
.stat-mini-val { font-size:1.3rem; font-weight:800; color:#e879f9; }
.stat-mini-lbl { color:#9ca3af; font-size:.72rem; margin-top:2px; }
.status-ativo   { color:#10b981; font-weight:700; font-size:.85rem; }
.status-inativo { color:#9ca3af; font-weight:600; font-size:.85rem; }
</style>
""")

# ── Estado da sessão ─────────────────────────────────────────────────────────
_nome_raw = usuario.get("nome", usuario.get("email", "parceiro"))
_slug_default = re.sub(r"[^a-z0-9_]", "_", _nome_raw.lower().split()[0])

for _k, _v in {
    "loja_slug":       st.session_state.get("loja_slug",        _slug_default),
    "loja_nome":       st.session_state.get("loja_nome",        _nome_raw),
    "loja_bio":        st.session_state.get("loja_bio",         ""),
    "loja_cor":        st.session_state.get("loja_cor",         "#7c3aed"),
    "loja_ativa":      st.session_state.get("loja_ativa",       True),
    "loja_destaques":  st.session_state.get("loja_destaques",   []),
    "loja_whatsapp":   st.session_state.get("loja_whatsapp",    ""),
    "loja_instagram":  st.session_state.get("loja_instagram",   ""),
    "loja_saved":      st.session_state.get("loja_saved",       False),
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

BASE_URL = "https://hipnus-cosmeticos.streamlit.app"

CATALOG_IDS = [
    ("oro-01","Sérum Facial Ouro 24K"),
    ("oro-02","Creme Noturno Regenerador Ouro"),
    ("oro-03","Máscara Detox Ouro & Argila"),
    ("plt-01","Óleo Corporal Platinum Rosas"),
    ("plt-02","Esfoliante Corporal Sal Rosa"),
    ("plt-03","Loção Firmadora Platinum Q10"),
    ("ess-01","Água Micelar Essence Pure"),
    ("ess-02","Tônico Facial Essence Rose"),
    ("ess-03","Protetor Solar Essence FPS 60"),
    ("vlv-01","Gloss Labial Velvet Rosé"),
    ("vlv-02","Base Velvet Cover HD"),
    ("vlv-03","Paleta Iluminador Velvet Glow"),
]

link_publico = f"{BASE_URL}/?parceiro={st.session_state.loja_slug}"

# ── Layout principal ─────────────────────────────────────────────────────────
tab_cfg, tab_preview, tab_stats = st.tabs([
    "⚙️  Configurar Loja",
    "👁️  Preview",
    "📊  Estatísticas",
])

# ════════════════════════════════════════════════════════════════════════════
# ABA 1 — CONFIGURAR
# ════════════════════════════════════════════════════════════════════════════
with tab_cfg:
    col_form, col_link = st.columns([3, 2])

    with col_form:
        st.html('<div class="loja-cfg-card">'
                '<div class="loja-cfg-label">🔗 Identidade & Link</div></div>')

        novo_slug = st.text_input(
            "Slug da loja (aparece no link)",
            value=st.session_state.loja_slug,
            help="Somente letras minúsculas, números e _. Ex: joana_silva",
            placeholder="ex: joana_silva",
        )
        slug_valido = bool(re.fullmatch(r"[a-z0-9_]{3,30}", novo_slug))
        if not slug_valido and novo_slug:
            st.caption("⚠️ Use apenas letras minúsculas, números e _ (3–30 chars)")
        elif slug_valido:
            st.caption(f"✅ Link: `{BASE_URL}/?parceiro={novo_slug}`")

        novo_nome = st.text_input(
            "Nome de exibição na loja",
            value=st.session_state.loja_nome,
            placeholder="Ex: Joana Silva Cosméticos",
        )
        nova_bio = st.text_area(
            "Mensagem de boas-vindas / bio",
            value=st.session_state.loja_bio,
            placeholder="Ex: Olá! Sou consultora HIPNUS há 3 anos. Aqui você encontra os melhores produtos com preço exclusivo.",
            max_chars=220,
            height=90,
        )
        col_cor, col_wa = st.columns(2)
        with col_cor:
            nova_cor = st.color_picker("Cor de destaque", value=st.session_state.loja_cor)
        with col_wa:
            novo_wa = st.text_input("WhatsApp (só números)", value=st.session_state.loja_whatsapp,
                                    placeholder="5511999999999")
        novo_ig = st.text_input("Instagram (sem @)", value=st.session_state.loja_instagram,
                                placeholder="joana.cosmeticos")

        st.markdown("---")
        st.markdown("**🌟 Produtos em destaque** *(até 4)*")
        nomes_disponiveis = [n for _, n in CATALOG_IDS]
        atual_nomes = [n for _, n in CATALOG_IDS if _ in st.session_state.loja_destaques]
        sel_destaques = st.multiselect(
            "Selecione os produtos que aparecem primeiro na sua loja:",
            options=nomes_disponiveis,
            default=atual_nomes,
            max_selections=4,
            label_visibility="collapsed",
        )
        novos_ids = [i for i, n in CATALOG_IDS if n in sel_destaques]

        st.markdown("---")
        nova_ativa = st.toggle("🟢 Loja ativa (visível para clientes)", value=st.session_state.loja_ativa)

        if st.button("💾 Salvar configurações", type="primary", use_container_width=True):
            if not slug_valido:
                st.error("Corrija o slug antes de salvar.")
            else:
                st.session_state.loja_slug      = novo_slug
                st.session_state.loja_nome      = novo_nome
                st.session_state.loja_bio       = nova_bio
                st.session_state.loja_cor       = nova_cor
                st.session_state.loja_ativa     = nova_ativa
                st.session_state.loja_destaques = novos_ids
                st.session_state.loja_whatsapp  = novo_wa
                st.session_state.loja_instagram = novo_ig
                st.session_state.loja_saved     = True
                st.success("✅ Configurações salvas com sucesso!")
                st.rerun()

    with col_link:
        status_txt = (
            '<span class="status-ativo">● Loja Ativa</span>'
            if st.session_state.loja_ativa
            else '<span class="status-inativo">○ Loja Inativa</span>'
        )
        st.html(f'<div class="loja-cfg-card">'
                f'<div class="loja-cfg-label">🔗 Seu Link Exclusivo</div>'
                f'<div style="margin-bottom:6px;">{status_txt}</div>'
                f'<div class="link-box">{link_publico}</div>'
                f'</div>')

        st.markdown("**📤 Compartilhar via:**")
        wa_msg = f"Oi! Acesse minha loja HIPNUS com condições especiais 👇%0A{link_publico}"
        col_a, col_b = st.columns(2)
        with col_a:
            st.link_button("💬 WhatsApp", f"https://wa.me/?text={wa_msg}", use_container_width=True)
        with col_b:
            st.link_button("📸 Instagram", "https://instagram.com", use_container_width=True)

        st.markdown("---")
        st.markdown("**📋 Dicas para divulgar:**")
        st.markdown("""
- Cole o link na bio do Instagram
- Envie no status do WhatsApp
- Adicione na sua assinatura de e-mail
- Compartilhe em grupos de clientes
        """)

        if st.session_state.loja_saved:
            st.success("🎉 Sua loja está configurada!")

# ════════════════════════════════════════════════════════════════════════════
# ABA 2 — PREVIEW
# ════════════════════════════════════════════════════════════════════════════
with tab_preview:
    st.caption("Prévia de como seus clientes verão sua loja ao acessar o link.")
    st.markdown("---")

    cor = st.session_state.loja_cor
    nome_exib = st.session_state.loja_nome or "Minha Loja HIPNUS"
    bio_exib  = st.session_state.loja_bio  or "Bem-vindo! Aqui você encontra os melhores produtos HIPNUS com preço exclusivo."
    destaques = [n for i, n in CATALOG_IDS if i in st.session_state.loja_destaques]

    dest_tags = "".join(f'<span class="produto-destaque-tag">⭐ {n}</span>' for n in destaques)
    wa_val    = st.session_state.loja_whatsapp
    ig_val    = st.session_state.loja_instagram
    contatos  = ""
    if wa_val:
        contatos += f'<a href="https://wa.me/{wa_val}" style="color:#10b981;text-decoration:none;margin-right:16px;">💬 WhatsApp</a>'
    if ig_val:
        contatos += f'<a href="https://instagram.com/{ig_val}" style="color:#e879f9;text-decoration:none;">📸 @{ig_val}</a>'

    st.html(f"""
    <div class="preview-loja" style="border-color:{cor}40;">
      <div style="position:relative;z-index:1;">
        <div class="preview-badge" style="background:{cor}30;border-color:{cor}66;color:{cor};">
          🏪 Loja Exclusiva HIPNUS
        </div>
        <div class="preview-nome" style="color:{cor};margin-top:10px;">{nome_exib}</div>
        <p class="preview-bio">{bio_exib}</p>
        {"<div style='margin-bottom:14px;'>" + dest_tags + "</div>" if destaques else ""}
        {"<div style='margin-top:8px;'>" + contatos + "</div>" if contatos else ""}
        <div style="margin-top:20px;padding:10px 0;border-top:1px solid rgba(168,85,247,.2);
             color:#9ca3af;font-size:.78rem;">
          🔗 {link_publico}
        </div>
      </div>
    </div>
    """)

    st.markdown("---")
    st.caption("🛒 Abaixo apareceria o grid de produtos da loja, filtros e carrinho.")

# ════════════════════════════════════════════════════════════════════════════
# ABA 3 — ESTATÍSTICAS
# ════════════════════════════════════════════════════════════════════════════
with tab_stats:
    st.html('<div class="loja-cfg-card"><div class="loja-cfg-label">📊 Desempenho da Loja</div></div>')

    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, "—", "Acessos ao link"),
        (c2, "—", "Pedidos gerados"),
        (c3, "R$ —", "Volume de vendas"),
        (c4, "—%", "Taxa de conversão"),
    ]:
        with col:
            st.html(f"""<div class="stat-mini">
                <div class="stat-mini-val">{val}</div>
                <div class="stat-mini-lbl">{lbl}</div>
            </div>""")

    st.info("📈 As estatísticas serão populadas automaticamente pelo Módulo C (Rastreio de Vendas por Parceiro).", icon="ℹ️")
    st.markdown("""
**O que será rastreado:**
- Cada acesso ao link `?parceiro=slug`
- Cada pedido concluído via link do parceiro
- Volume total de vendas atribuídas
- Produtos mais vendidos pelo parceiro
    """)
