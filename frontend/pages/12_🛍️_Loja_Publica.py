"""
12_🛍️_Loja_Publica.py — HIPNUS COSMÉTICOS
Skill: Loja Personalizada — Módulo B
Página pública da loja do parceiro. Não exige login.
Acesso via: /?parceiro=slug
"""
from __future__ import annotations
import sys, re
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from lib import ui

st.set_page_config(
    page_title="Loja HIPNUS",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
ui.inject_theme()

CATALOG = [
    dict(id="oro-01", name="Sérum Facial Ouro 24K",         linha="Linha Ouro",    categoria="Facial",
         preco=189.90, preco_parceiro=142.00, estoque=48,   badge="Mais Vendido",
         descricao="Sérum concentrado com partículas de ouro coloidal. Reduz linhas finas e uniformiza o tom da pele.",
         volume="30 ml",  beneficios=["Anti-aging","Luminosidade","Firmeza"]),
    dict(id="oro-02", name="Creme Noturno Regenerador Ouro", linha="Linha Ouro",    categoria="Facial",
         preco=229.90, preco_parceiro=172.00, estoque=32,   badge="Novo",
         descricao="Creme rico em peptídeos e ouro 24K que age durante o sono para regeneração celular intensa.",
         volume="50 ml",  beneficios=["Regeneração","Anti-aging","Hidratação profunda"]),
    dict(id="oro-03", name="Máscara Detox Ouro & Argila",   linha="Linha Ouro",    categoria="Facial",
         preco=149.90, preco_parceiro=112.00, estoque=60,   badge="",
         descricao="Máscara de argila branca com extrato de ouro. Purifica e deixa a pele radiante.",
         volume="100 g", beneficios=["Detox","Poros","Brilho"]),
    dict(id="plt-01", name="Óleo Corporal Platinum Rosas",  linha="Linha Platinum", categoria="Corporal",
         preco=159.90, preco_parceiro=119.00, estoque=55,   badge="Destaque",
         descricao="Óleo seco com extratos de rosa búlgara e vitamina E. Absorção rápida, pele sedosa.",
         volume="120 ml", beneficios=["Hidratação","Elasticidade","Perfume suave"]),
    dict(id="plt-02", name="Esfoliante Corporal Sal Rosa",   linha="Linha Platinum", categoria="Corporal",
         preco=109.90, preco_parceiro=82.00,  estoque=70,   badge="",
         descricao="Esfoliante granulado com sal do Himalaia e óleo de amêndoas. Renova e suaviza.",
         volume="300 g", beneficios=["Renovação celular","Maciez","Tonificação"]),
    dict(id="plt-03", name="Loção Firmadora Platinum Q10",   linha="Linha Platinum", categoria="Corporal",
         preco=139.90, preco_parceiro=104.00, estoque=40,   badge="Mais Pedido",
         descricao="Loção com coenzima Q10 e colágeno vegetal. Tonifica e reduz a aparência da celulite.",
         volume="200 ml", beneficios=["Firmeza","Anti-celulite","Hidratação"]),
    dict(id="ess-01", name="Água Micelar Essence Pure",      linha="Linha Essence",  categoria="Limpeza",
         preco=89.90,  preco_parceiro=67.00,  estoque=85,   badge="",
         descricao="Água micelar bifásica com extrato de camomila e aloe vera. Remove maquiagem sem agredir.",
         volume="200 ml", beneficios=["Limpeza suave","Hidratação","Sem enxágue"]),
    dict(id="ess-02", name="Tônico Facial Essence Rose",     linha="Linha Essence",  categoria="Facial",
         preco=99.90,  preco_parceiro=74.00,  estoque=65,   badge="Novo",
         descricao="Tônico equilibrante com água de rosas e ácido hialurônico. Prepara a pele para a rotina.",
         volume="150 ml", beneficios=["Equilíbrio","Hidratação","Preparo"]),
    dict(id="ess-03", name="Protetor Solar Essence FPS 60",  linha="Linha Essence",  categoria="Proteção",
         preco=129.90, preco_parceiro=97.00,  estoque=50,   badge="Essencial",
         descricao="Protetor solar com textura fluida e acabamento matte. Proteção UVA/UVB + azul.",
         volume="50 ml",  beneficios=["FPS 60","Matte","UVA/UVB"]),
    dict(id="vlv-01", name="Gloss Labial Velvet Rosé",       linha="Linha Velvet",   categoria="Maquiagem",
         preco=69.90,  preco_parceiro=52.00,  estoque=90,   badge="Top 10",
         descricao="Gloss labial com pigmento rosé e efeito volumizador. Fórmula hidratante com vitamina E.",
         volume="8 ml",  beneficios=["Volume","Hidratação","Pigmento"]),
    dict(id="vlv-02", name="Base Velvet Cover HD",           linha="Linha Velvet",   categoria="Maquiagem",
         preco=149.90, preco_parceiro=112.00, estoque=35,   badge="Novo",
         descricao="Base de alta cobertura com tecnologia HD. 40 tons. Longa duração até 16h.",
         volume="30 ml",  beneficios=["Alta cobertura","16h duração","HD"]),
    dict(id="vlv-03", name="Paleta Iluminador Velvet Glow",  linha="Linha Velvet",   categoria="Maquiagem",
         preco=119.90, preco_parceiro=89.00,  estoque=42,   badge="Destaque",
         descricao="Paleta com 4 tons de iluminador prensado. Do dourado suave ao champagne intenso.",
         volume="12 g",  beneficios=["4 tons","Longa duração","Buildable"]),
]

def _brl(v):
    return "R$ " + f"{v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

params = st.query_params
slug   = params.get("parceiro", "").strip().lower()

def _load_parceiro_config(slug: str) -> dict:
    if st.session_state.get("loja_slug") == slug:
        return {
            "nome":      st.session_state.get("loja_nome",  slug),
            "bio":       st.session_state.get("loja_bio",   ""),
            "cor":       st.session_state.get("loja_cor",   "#7c3aed"),
            "ativa":     st.session_state.get("loja_ativa", True),
            "destaques": st.session_state.get("loja_destaques", []),
            "whatsapp":  st.session_state.get("loja_whatsapp", ""),
            "instagram": st.session_state.get("loja_instagram",""),
        }
    return {
        "nome":      slug.replace("_"," ").title() + " · HIPNUS" if slug else "HIPNUS Cosméticos",
        "bio":       "Bem-vinda(o)! Aqui você encontra os melhores produtos de beleza com condições exclusivas.",
        "cor":       "#7c3aed",
        "ativa":     True,
        "destaques": [],
        "whatsapp":  "",
        "instagram": "",
    }

cfg = _load_parceiro_config(slug)

if "loja_pub_acessos" not in st.session_state:
    st.session_state.loja_pub_acessos = {}
if slug:
    st.session_state.loja_pub_acessos[slug] = (
        st.session_state.loja_pub_acessos.get(slug, 0) + 1
    )

cor = cfg["cor"]
st.html(f"""
<style>
[data-testid="stAppViewContainer"] {{ background: #0f0d14; }}
[data-testid="stSidebar"] {{ display: none !important; }}
section.main > div {{ padding-top: 0 !important; }}
.pub-hero {{
    background: linear-gradient(135deg,#1a0f2e 0%,#2d1558 50%,#1a0f2e 100%);
    border: 1px solid {cor}44;
    border-radius: 20px;
    padding: 40px 36px 32px;
    position: relative; overflow: hidden;
    margin-bottom: 28px;
}}
.pub-hero::before {{
    content:""; position:absolute; inset:0;
    background: radial-gradient(ellipse 60% 80% at 80% 50%,{cor}22,transparent);
    pointer-events:none;
}}
.pub-hero-badge {{
    display:inline-block; background:{cor}30;
    border:1px solid {cor}66; color:{cor};
    border-radius:99px; padding:3px 14px;
    font-size:.75rem; font-weight:700; letter-spacing:.4px; margin-bottom:14px;
}}
.pub-hero-nome  {{ font-size:2rem; font-weight:800; color:#f5d0fe; margin-bottom:8px; line-height:1.2; }}
.pub-hero-bio   {{ color:#c4b5fd; font-size:.95rem; line-height:1.55; max-width:600px; }}
.pub-hero-links {{ margin-top:18px; display:flex; gap:16px; flex-wrap:wrap; }}
.pub-hero-link  {{
    background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.12);
    color:#e2e8f0; border-radius:99px; padding:5px 16px;
    font-size:.8rem; font-weight:600; text-decoration:none;
}}
.pub-prod-card {{
    background:#1c1626; border:1px solid rgba(168,85,247,.2);
    border-radius:16px; padding:18px;
    position:relative; overflow:hidden;
}}
.pub-prod-card:hover {{ border-color:{cor}88; box-shadow:0 8px 28px {cor}22; }}
.pub-prod-badge {{
    position:absolute; top:10px; right:10px;
    background:linear-gradient(90deg,#7c3aed,#a855f7);
    color:#fff; border-radius:99px; padding:2px 9px; font-size:.68rem; font-weight:700;
}}
.pub-prod-linha {{ color:#9ca3af; font-size:.7rem; letter-spacing:.5px; margin-bottom:3px; }}
.pub-prod-nome  {{ color:#f5d0fe; font-size:.95rem; font-weight:700; line-height:1.3; margin-bottom:6px; }}
.pub-prod-desc  {{ color:#9ca3af; font-size:.78rem; line-height:1.4; margin-bottom:10px; }}
.pub-prod-vol   {{ color:{cor}; font-size:.72rem; font-weight:600; margin-bottom:8px; }}
.pub-prod-preco {{ color:#e879f9; font-size:1.1rem; font-weight:800; }}
.pub-prod-cheio {{ color:#6b7280; font-size:.82rem; text-decoration:line-through; margin-right:6px; }}
.pub-prod-eco   {{ color:#10b981; font-size:.72rem; font-weight:600; }}
.pub-sem-login {{
    background:rgba(16,185,129,.07); border:1px solid rgba(16,185,129,.25);
    border-radius:10px; padding:10px 16px;
    color:#10b981; font-size:.8rem; font-weight:600;
    margin-bottom:18px;
}}
.pub-footer {{
    margin-top:48px; padding:24px 0 12px;
    border-top:1px solid rgba(185,131,255,.12);
    text-align:center; color:#6b7280; font-size:.78rem;
}}
</style>
""")

if not cfg["ativa"] and slug:
    st.warning("⚠️ Esta loja está temporariamente inativa. Tente novamente mais tarde.")
    st.stop()

links_html = ""
if cfg["whatsapp"]:
    links_html += f'<a class="pub-hero-link" href="https://wa.me/{cfg["whatsapp"]}" target="_blank">💬 WhatsApp</a>'
if cfg["instagram"]:
    links_html += f'<a class="pub-hero-link" href="https://instagram.com/{cfg["instagram"]}" target="_blank">📸 @{cfg["instagram"]}</a>'

st.html(f"""
<div class="pub-hero">
  <div style="position:relative;z-index:1;">
    <div class="pub-hero-badge">🏪 Loja Exclusiva HIPNUS</div>
    <div class="pub-hero-nome">{cfg['nome']}</div>
    <p class="pub-hero-bio">{cfg['bio']}</p>
    {"<div class='pub-hero-links'>" + links_html + "</div>" if links_html else ""}
  </div>
</div>
""")

st.html('<div class="pub-sem-login">🔓 Sem cadastro necessário — navegue e adicione ao carrinho diretamente.</div>')

for _k, _v in {
    "pub_cart": {}, "pub_filtro_linha": [], "pub_busca": "",
    "pub_slug": slug,
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

def pub_add(pid):
    c = st.session_state.pub_cart
    c[pid] = c.get(pid, 0) + 1
    st.session_state.pub_cart = c

def pub_cart_total():
    return sum(
        next((p["preco"] for p in CATALOG if p["id"] == pid), 0) * q
        for pid, q in st.session_state.pub_cart.items()
    )

col_busca, col_qty = st.columns([4, 1])
with col_busca:
    busca = st.text_input("🔍 Buscar produto...", placeholder="Ex: sérum, ouro, protetor…",
                          label_visibility="collapsed", key="pub_busca_input")
    if busca != st.session_state.pub_busca:
        st.session_state.pub_busca = busca
        st.rerun()
with col_qty:
    qty_cart = sum(st.session_state.pub_cart.values())
    st.html(f"""<div style="text-align:right;padding:8px 0;">
        <span style="background:{cor}25;border:1px solid {cor}55;
            color:{cor};border-radius:99px;padding:5px 14px;
            font-size:.82rem;font-weight:700;">
            🛒 {qty_cart} item(s) · {_brl(pub_cart_total())}
        </span>
    </div>""")

LINHAS = sorted(set(p["linha"] for p in CATALOG))
fcols = st.columns(len(LINHAS) + 1)
with fcols[0]:
    if st.button("Todas", key="pub_fl_all",
                 type="secondary" if st.session_state.pub_filtro_linha else "primary",
                 use_container_width=True):
        st.session_state.pub_filtro_linha = []
        st.rerun()
for i, linha in enumerate(LINHAS):
    with fcols[i+1]:
        ativo = linha in st.session_state.pub_filtro_linha
        if st.button(("✓ " if ativo else "") + linha.replace("Linha ",""),
                     key=f"pub_fl_{linha}",
                     type="primary" if ativo else "secondary",
                     use_container_width=True):
            fl = list(st.session_state.pub_filtro_linha)
            if ativo: fl.remove(linha)
            else: fl.append(linha)
            st.session_state.pub_filtro_linha = fl
            st.rerun()

produtos = list(CATALOG)
if cfg["destaques"]:
    def _sort_key(p):
        try:
            return cfg["destaques"].index(p["id"])
        except ValueError:
            return len(cfg["destaques"]) + 1
    produtos.sort(key=_sort_key)

if st.session_state.pub_filtro_linha:
    produtos = [p for p in produtos if p["linha"] in st.session_state.pub_filtro_linha]
if st.session_state.pub_busca:
    q = st.session_state.pub_busca.lower()
    produtos = [p for p in produtos if q in p["name"].lower() or q in p["descricao"].lower()]

st.markdown(f"<div style='color:#9ca3af;font-size:.78rem;margin:8px 0 16px;'>{len(produtos)} produto(s)</div>",
            unsafe_allow_html=True)

if not produtos:
    st.markdown("<div style='text-align:center;padding:48px;color:#6b7280;'>🔍 Nenhum produto encontrado.</div>",
                unsafe_allow_html=True)
else:
    for row_start in range(0, len(produtos), 3):
        row = produtos[row_start:row_start+3]
        cols = st.columns(3)
        for col, prod in zip(cols, row):
            with col:
                economy = prod["preco"] - prod["preco_parceiro"]
                pct     = int(economy / prod["preco"] * 100)
                badge   = f'<div class="pub-prod-badge">{prod["badge"]}</div>' if prod["badge"] else ""
                bens    = "".join(f'<span style="background:rgba(124,58,237,.12);border:1px solid rgba(124,58,237,.28);color:#c4b5fd;border-radius:6px;padding:2px 7px;font-size:.68rem;margin:2px 2px 0 0;">{b}</span>' for b in prod["beneficios"])
                dest    = "⭐ " if prod["id"] in cfg["destaques"] else ""
                st.html(f"""
                <div class="pub-prod-card">
                  {badge}
                  <div class="pub-prod-linha">{prod['linha'].upper()}</div>
                  <div class="pub-prod-nome">{dest}{prod['name']}</div>
                  <div class="pub-prod-desc">{prod['descricao'][:80]}...</div>
                  <div class="pub-prod-vol">📦 {prod['volume']}</div>
                  <div style="margin-bottom:10px;">{bens}</div>
                  <div style="display:flex;align-items:baseline;gap:8px;">
                    <span class="pub-prod-cheio">{_brl(prod['preco'])}</span>
                    <span class="pub-prod-preco">{_brl(prod['preco_parceiro'])}</span>
                  </div>
                  <div class="pub-prod-eco">-{pct}% · economia de {_brl(economy)}</div>
                </div>
                """)
                if st.button(f"🛒 Adicionar", key=f"pub_add_{prod['id']}",
                             use_container_width=True, type="primary"):
                    pub_add(prod["id"])
                    st.rerun()

st.html(f"""
<div class="pub-footer">
  <div style="margin-bottom:6px;">
    <span style="color:{cor};font-weight:700;">HIPNUS Cosméticos</span>
    · Produtos de beleza premium
  </div>
  {"<div style='margin-bottom:4px;'>Consultora: <strong style='color:#f5d0fe;'>" + cfg['nome'] + "</strong></div>" if slug else ""}
  <div>Dúvidas? Entre em contato com sua consultora.</div>
</div>
""")
