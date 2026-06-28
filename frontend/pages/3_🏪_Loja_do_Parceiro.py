"""
🏪 Loja do Parceiro — HIPNUS Cosméticos
Estrutura moderna: hero banner · filtros · busca · grid de produtos · carrinho · checkout
"""

import sys
import os
from pathlib import Path

# ── path setup à prova de exec() ─────────────────────────────────────────────────────
def _resolve_lib_root() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent,
        Path(os.getcwd()),
        Path(os.getcwd()) / "frontend",
        Path("/mount/src/hipnus-cosmeticos/frontend"),
        Path("/mount/src/hipnus-cosmeticos") / "frontend",
    ]
    for c in candidates:
        if (c / "lib" / "session_guard.py").exists():
            return c
    p = Path(__file__).resolve()
    for _ in range(6):
        if (p / "lib" / "session_guard.py").exists():
            return p
        if (p / "frontend" / "lib" / "session_guard.py").exists():
            return p / "frontend"
        p = p.parent
    return Path(__file__).resolve().parent.parent

_lib_root = _resolve_lib_root()
if str(_lib_root) not in sys.path:
    sys.path.insert(0, str(_lib_root))

import streamlit as st
from lib.session_guard import check_session_expiry
from lib.theme import inject_theme as apply_theme

st.set_page_config(
    page_title="Loja do Parceiro · HIPNUS",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()
check_session_expiry()

# ── catálogo de produtos ──────────────────────────────────────────────────────────
CATALOG = [
    dict(id="oro-01", name="Sérum Facial Ouro 24K", linha="Linha Ouro", categoria="Facial",
         preco=189.90, preco_parceiro=142.00, estoque=48,
         badge="Mais Vendido", descricao="Sérum concentrado com partículas de ouro coloidal. Reduz linhas finas e uniformiza o tom da pele.",
         volume="30 ml", beneficios=["Anti-aging", "Luminosidade", "Firmeza"]),
    dict(id="oro-02", name="Creme Noturno Regenerador Ouro", linha="Linha Ouro", categoria="Facial",
         preco=229.90, preco_parceiro=172.00, estoque=32,
         badge="Novo", descricao="Creme rico em peptídeos e ouro 24K que age durante o sono para regeneração celular intensa.",
         volume="50 ml", beneficios=["Regeneração", "Anti-aging", "Hidratação profunda"]),
    dict(id="oro-03", name="Máscara Detox Ouro & Argila", linha="Linha Ouro", categoria="Facial",
         preco=149.90, preco_parceiro=112.00, estoque=60,
         badge="", descricao="Máscara de argila branca com extrato de ouro. Purifica e deixa a pele radiante.",
         volume="100 g", beneficios=["Detox", "Poros", "Brilho"]),
    dict(id="plt-01", name="Óleo Corporal Platinum Rosas", linha="Linha Platinum", categoria="Corporal",
         preco=159.90, preco_parceiro=119.00, estoque=55,
         badge="Destaque", descricao="Óleo seco com extratos de rosa búlgara e vitamina E. Absorção rápida, pele sedosa.",
         volume="120 ml", beneficios=["Hidratação", "Elasticidade", "Perfume suave"]),
    dict(id="plt-02", name="Esfoliante Corporal Sal Rosa", linha="Linha Platinum", categoria="Corporal",
         preco=109.90, preco_parceiro=82.00, estoque=70,
         badge="", descricao="Esfoliante granulado com sal do Himalaia e óleo de amêndoas. Renova e suaviza.",
         volume="300 g", beneficios=["Renovação celular", "Maciez", "Tonificação"]),
    dict(id="plt-03", name="Loção Firmadora Platinum Q10", linha="Linha Platinum", categoria="Corporal",
         preco=139.90, preco_parceiro=104.00, estoque=40,
         badge="Mais Pedido", descricao="Loção com coenzima Q10 e colágeno vegetal. Tonifica e reduz a aparência da celulite.",
         volume="200 ml", beneficios=["Firmeza", "Anti-celulite", "Hidratação"]),
    dict(id="ess-01", name="Água Micelar Essence Pure", linha="Linha Essence", categoria="Limpeza",
         preco=89.90, preco_parceiro=67.00, estoque=85,
         badge="", descricao="Água micelar bifásica com extrato de camomila e aloe vera. Remove maquiagem sem agredir.",
         volume="200 ml", beneficios=["Limpeza suave", "Hidratação", "Sem enxágue"]),
    dict(id="ess-02", name="Tônico Facial Essence Rose", linha="Linha Essence", categoria="Facial",
         preco=99.90, preco_parceiro=74.00, estoque=65,
         badge="Novo", descricao="Tônico equilibrante com água de rosas e ácido hialurônico. Prepara a pele para a rotina.",
         volume="150 ml", beneficios=["Equilíbrio", "Hidratação", "Preparo"]),
    dict(id="ess-03", name="Protetor Solar Essence FPS 60", linha="Linha Essence", categoria="Proteção",
         preco=129.90, preco_parceiro=97.00, estoque=50,
         badge="Essencial", descricao="Protetor solar com textura fluida e acabamento matte. Proteção UVA/UVB + azul.",
         volume="50 ml", beneficios=["FPS 60", "Matte", "UVA/UVB"]),
    dict(id="vlv-01", name="Gloss Labial Velvet Rosé", linha="Linha Velvet", categoria="Maquiagem",
         preco=69.90, preco_parceiro=52.00, estoque=90,
         badge="Top 10", descricao="Gloss labial com pigmento rosé e efeito volumizador. Fórmula hidratante com vitamina E.",
         volume="8 ml", beneficios=["Volume", "Hidratação", "Pigmento"]),
    dict(id="vlv-02", name="Base Velvet Cover HD", linha="Linha Velvet", categoria="Maquiagem",
         preco=149.90, preco_parceiro=112.00, estoque=35,
         badge="Novo", descricao="Base de alta cobertura com tecnologia HD. 40 tons. Longa duração até 16h.",
         volume="30 ml", beneficios=["Alta cobertura", "16h duração", "HD"]),
    dict(id="vlv-03", name="Paleta Iluminador Velvet Glow", linha="Linha Velvet", categoria="Maquiagem",
         preco=119.90, preco_parceiro=89.00, estoque=42,
         badge="Destaque", descricao="Paleta com 4 tons de iluminador prensado. Do dourado suave ao champagne intenso.",
         volume="12 g", beneficios=["4 tons", "Longa duração", "Buildable"]),
]

LINHAS = sorted(set(p["linha"] for p in CATALOG))
CATEGORIAS = ["Todas"] + sorted(set(p["categoria"] for p in CATALOG))

for _k, _v in {
    "loja_cart": {}, "loja_filtro_linha": [], "loja_filtro_cat": "Todas",
    "loja_busca": "", "loja_view": "loja", "loja_produto_detalhe": None,
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


def cart_total_qty():
    return sum(st.session_state.loja_cart.values())

def cart_total_valor():
    total = 0.0
    for pid, qty in st.session_state.loja_cart.items():
        prod = next((p for p in CATALOG if p["id"] == pid), None)
        if prod:
            total += prod["preco_parceiro"] * qty
    return total

def add_to_cart(pid, qty=1):
    cart = st.session_state.loja_cart
    cart[pid] = cart.get(pid, 0) + qty
    st.session_state.loja_cart = cart

def remove_from_cart(pid):
    st.session_state.loja_cart.pop(pid, None)

def update_cart_qty(pid, qty):
    if qty <= 0:
        remove_from_cart(pid)
    else:
        st.session_state.loja_cart[pid] = qty

def get_filtered_products():
    prods = list(CATALOG)
    if st.session_state.loja_filtro_linha:
        prods = [p for p in prods if p["linha"] in st.session_state.loja_filtro_linha]
    if st.session_state.loja_filtro_cat != "Todas":
        prods = [p for p in prods if p["categoria"] == st.session_state.loja_filtro_cat]
    if st.session_state.loja_busca:
        q = st.session_state.loja_busca.lower()
        prods = [p for p in prods if q in p["name"].lower() or q in p["descricao"].lower()]
    return prods


st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0f0d14; }
[data-testid="stSidebar"] { display: none !important; }
section.main > div { padding-top: 0 !important; }
.loja-hero {
    background: linear-gradient(135deg,#1a0f2e 0%,#2d1558 50%,#1a0f2e 100%);
    border: 1px solid rgba(168,85,247,.25); border-radius: 20px;
    padding: 48px 40px 40px; margin-bottom: 32px;
    position: relative; overflow: hidden;
}
.loja-hero::before {
    content:""; position:absolute; inset:0;
    background:radial-gradient(ellipse 60% 80% at 80% 50%,rgba(168,85,247,.15),transparent);
    pointer-events:none;
}
.loja-hero-title {
    font-size:2.2rem; font-weight:800;
    background:linear-gradient(90deg,#e879f9,#a855f7,#7c3aed);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0 0 8px;
}
.loja-hero-sub   { color:#c4b5fd; font-size:1rem; margin:0; }
.loja-hero-badge {
    display:inline-block; background:rgba(168,85,247,.2);
    border:1px solid rgba(168,85,247,.4); color:#e879f9;
    border-radius:99px; padding:4px 14px; font-size:.78rem;
    font-weight:600; letter-spacing:.5px; margin-bottom:16px;
}
.loja-hero-stats { display:flex; gap:32px; margin-top:24px; }
.loja-hero-stat  { text-align:center; }
.loja-hero-stat-val { font-size:1.5rem; font-weight:800; color:#e879f9; line-height:1; }
.loja-hero-stat-lbl { color:#9ca3af; font-size:.75rem; margin-top:4px; }
.prod-card {
    background:#1c1626; border:1px solid rgba(168,85,247,.2);
    border-radius:16px; padding:20px;
    position:relative; overflow:hidden;
    transition:border-color .2s,box-shadow .2s;
}
.prod-card:hover { border-color:rgba(168,85,247,.55); box-shadow:0 8px 32px rgba(124,58,237,.18); }
.prod-badge {
    position:absolute; top:12px; right:12px;
    background:linear-gradient(90deg,#7c3aed,#a855f7);
    color:#fff; border-radius:99px; padding:2px 10px; font-size:.7rem; font-weight:700;
}
.prod-linha   { color:#9ca3af; font-size:.72rem; letter-spacing:.5px; margin-bottom:4px; }
.prod-name    { color:#f5d0fe; font-size:1rem; font-weight:700; line-height:1.3; margin-bottom:6px; }
.prod-desc    { color:#9ca3af; font-size:.82rem; line-height:1.45; margin-bottom:12px; }
.prod-volume  { color:#7c3aed; font-size:.75rem; font-weight:600; margin-bottom:10px; }
.prod-beneficios { display:flex; flex-wrap:wrap; gap:4px; margin-bottom:14px; }
.prod-benefit-tag {
    background:rgba(124,58,237,.15); border:1px solid rgba(124,58,237,.3);
    color:#c4b5fd; border-radius:6px; padding:2px 8px; font-size:.7rem;
}
.prod-precos { display:flex; align-items:baseline; gap:10px; margin-bottom:14px; }
.prod-preco-cheio { color:#6b7280; font-size:.85rem; text-decoration:line-through; }
.prod-preco-parc  { color:#e879f9; font-size:1.15rem; font-weight:800; }
.prod-economy     { color:#10b981; font-size:.75rem; font-weight:600; }
.prod-estoque     { color:#9ca3af; font-size:.72rem; }
.cart-badge {
    background:linear-gradient(90deg,#7c3aed,#a855f7);
    color:#fff; border-radius:99px;
    padding:4px 16px; font-size:.82rem; font-weight:700;
    display:inline-flex; align-items:center; gap:6px;
}
.cart-mini {
    background:#1c1626; border:1px solid rgba(168,85,247,.25);
    border-radius:14px; padding:16px 18px; margin-bottom:12px;
}
.cart-item-name { color:#f5d0fe; font-size:.88rem; font-weight:600; }
.cart-item-sub  { color:#9ca3af; font-size:.75rem; }
.cart-total {
    background:linear-gradient(135deg,rgba(124,58,237,.12),rgba(168,85,247,.06));
    border:1px solid rgba(168,85,247,.3); border-radius:12px;
    padding:14px 18px; display:flex; justify-content:space-between;
    align-items:center; margin-top:8px;
}
.cart-total-lbl { color:#9ca3af; font-size:.85rem; }
.cart-total-val { color:#e879f9; font-size:1.2rem; font-weight:800; }
.detalhe-hero {
    background:linear-gradient(135deg,#1a0f2e,#2d1558);
    border:1px solid rgba(168,85,247,.25); border-radius:20px;
    padding:32px 32px 28px; margin-bottom:20px;
}
.detalhe-nome  { color:#f5d0fe; font-size:1.5rem; font-weight:800; margin:8px 0; }
.detalhe-linha { color:#a855f7; font-size:.8rem; letter-spacing:.6px; font-weight:600; }
.detalhe-desc  { color:#c4b5fd; font-size:.95rem; line-height:1.6; margin:12px 0; }
.filtro-chip {
    display:inline-block; background:rgba(124,58,237,.12);
    border:1px solid rgba(124,58,237,.3); color:#c4b5fd;
    border-radius:99px; padding:4px 14px; font-size:.78rem;
    font-weight:500; margin:2px; cursor:pointer;
    transition:all .15s ease;
}
.filtro-chip.ativo {
    background:rgba(124,58,237,.35); border-color:rgba(168,85,247,.7);
    color:#e879f9; font-weight:700;
}
</style>
""", unsafe_allow_html=True)


def _brl(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ── header fixo com carrinho ───────────────────────────────────────────────────────
qty  = cart_total_qty()
val  = cart_total_valor()
n_prods = len(CATALOG)
n_linhas = len(LINHAS)

st.markdown(
    f"""
    <div class="loja-hero">
      <div class="loja-hero-badge">🏪 Área Exclusiva Parceiro</div>
      <div class="loja-hero-title">Loja HIPNUS</div>
      <p class="loja-hero-sub">Preços especiais para revendedores · Compre com condições exclusivas</p>
      <div class="loja-hero-stats">
        <div class="loja-hero-stat">
          <div class="loja-hero-stat-val">{n_prods}</div>
          <div class="loja-hero-stat-lbl">Produtos</div>
        </div>
        <div class="loja-hero-stat">
          <div class="loja-hero-stat-val">{n_linhas}</div>
          <div class="loja-hero-stat-lbl">Linhas</div>
        </div>
        <div class="loja-hero-stat">
          <div class="loja-hero-stat-val">{qty}</div>
          <div class="loja-hero-stat-lbl">No carrinho</div>
        </div>
        <div class="loja-hero-stat">
          <div class="loja-hero-stat-val">{_brl(val)}</div>
          <div class="loja-hero-stat-lbl">Total atual</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── navegação de view ──────────────────────────────────────────────────────────────
if st.session_state.loja_view == "detalhe" and st.session_state.loja_produto_detalhe:
    # ── VIEW DETALHE ────────────────────────────────────────────────────────────────
    if st.button("← Voltar à loja", key="btn_back"):
        st.session_state.loja_view = "loja"
        st.session_state.loja_produto_detalhe = None
        st.rerun()

    prod = next((p for p in CATALOG if p["id"] == st.session_state.loja_produto_detalhe), None)
    if not prod:
        st.warning("Produto não encontrado.")
        st.stop()

    economy = prod["preco"] - prod["preco_parceiro"]
    pct     = int(economy / prod["preco"] * 100)

    st.markdown(
        f"""
        <div class="detalhe-hero">
          <div class="detalhe-linha">{prod['linha'].upper()} · {prod['categoria'].upper()}</div>
          <div class="detalhe-nome">{prod['name']}</div>
          <p class="detalhe-desc">{prod['descricao']}</p>
          <div style="color:#9ca3af;font-size:.82rem;margin-bottom:8px;">
            📦 Volume: <strong style="color:#c4b5fd;">{prod['volume']}</strong>
            &nbsp;&nbsp;·&nbsp;&nbsp;
            🏷 Estoque: <strong style="color:#c4b5fd;">{prod['estoque']} un</strong>
          </div>
          <div class="prod-beneficios">
            {''.join(f"<span class='prod-benefit-tag'>{b}</span>" for b in prod['beneficios'])}
          </div>
          <div class="prod-precos">
            <span class="prod-preco-cheio">{_brl(prod['preco'])}</span>
            <span class="prod-preco-parc">{_brl(prod['preco_parceiro'])}</span>
            <span class="prod-economy">-{pct}% ({_brl(economy)} de economia)</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    d1, d2, d3 = st.columns([1, 1, 2])
    qty_input = d1.number_input("Quantidade", min_value=1, max_value=prod["estoque"],
                                value=1, step=1, key=f"det_qty_{prod['id']}")
    with d2:
        st.write("")
        st.write("")
        if st.button("🛒 Adicionar", key=f"det_add_{prod['id']}", type="primary"):
            add_to_cart(prod["id"], qty_input)
            st.success(f"{qty_input}x {prod['name']} adicionado!")
            st.rerun()
    with d3:
        in_cart = st.session_state.loja_cart.get(prod["id"], 0)
        if in_cart:
            st.markdown(
                f'<div style="padding:8px 0;color:#10b981;font-weight:600;font-size:.9rem;">'
                f'✅ {in_cart} unidade(s) no carrinho — {_brl(prod["preco_parceiro"] * in_cart)}</div>',
                unsafe_allow_html=True,
            )

    st.stop()


# ── VIEW LOJA (principal) ──────────────────────────────────────────────────────────
left, right = st.columns([3, 1])

with left:
    # busca
    busca = st.text_input(
        "🔍 Buscar produto...", value=st.session_state.loja_busca,
        placeholder="Ex: sérum, ouro, protetor…", key="_busca_input",
        label_visibility="collapsed",
    )
    if busca != st.session_state.loja_busca:
        st.session_state.loja_busca = busca
        st.rerun()

    # filtros de linha
    st.markdown("<div style='margin:8px 0 4px;color:#9ca3af;font-size:.78rem;font-weight:600;'"
                ">FILTRAR POR LINHA:</div>", unsafe_allow_html=True)
    fcols = st.columns(len(LINHAS))
    for i, linha in enumerate(LINHAS):
        with fcols[i]:
            ativo = linha in st.session_state.loja_filtro_linha
            label = ("✓ " if ativo else "") + linha.replace("Linha ", "")
            if st.button(label, key=f"fl_{linha}",
                         type="primary" if ativo else "secondary",
                         use_container_width=True):
                fl = list(st.session_state.loja_filtro_linha)
                if ativo:
                    fl.remove(linha)
                else:
                    fl.append(linha)
                st.session_state.loja_filtro_linha = fl
                st.rerun()

    # filtro categoria
    cat = st.selectbox(
        "Categoria:", options=CATEGORIAS,
        index=CATEGORIAS.index(st.session_state.loja_filtro_cat),
        key="_sel_cat", label_visibility="collapsed",
    )
    if cat != st.session_state.loja_filtro_cat:
        st.session_state.loja_filtro_cat = cat
        st.rerun()

    produtos = get_filtered_products()
    st.markdown(
        f"<div style='color:#9ca3af;font-size:.8rem;margin:8px 0 16px;'>"
        f"{len(produtos)} produto(s) encontrado(s)</div>",
        unsafe_allow_html=True,
    )

    if not produtos:
        st.markdown(
            """<div style='text-align:center;padding:48px 24px;color:#6b7280;'>
            <div style='font-size:2.5rem;margin-bottom:12px;'>🔍</div>
            <div style='font-size:1rem;font-weight:600;color:#9ca3af;'>Nenhum produto encontrado</div>
            <div style='font-size:.85rem;margin-top:6px;'>Tente ajustar os filtros ou a busca.</div></div>""",
            unsafe_allow_html=True,
        )
    else:
        for row_start in range(0, len(produtos), 3):
            row = produtos[row_start:row_start + 3]
            cols = st.columns(3)
            for col, prod in zip(cols, row):
                with col:
                    economy = prod["preco"] - prod["preco_parceiro"]
                    pct     = int(economy / prod["preco"] * 100)
                    badge_html = (
                        f'<div class="prod-badge">{prod["badge"]}</div>'
                        if prod["badge"] else ""
                    )
                    beneficios_html = "".join(
                        f'<span class="prod-benefit-tag">{b}</span>'
                        for b in prod["beneficios"]
                    )
                    st.markdown(
                        f"""
                        <div class="prod-card">
                          {badge_html}
                          <div class="prod-linha">{prod['linha'].upper()}</div>
                          <div class="prod-name">{prod['name']}</div>
                          <div class="prod-desc">{prod['descricao'][:90]}{'...' if len(prod['descricao']) > 90 else ''}</div>
                          <div class="prod-volume">📦 {prod['volume']}</div>
                          <div class="prod-beneficios">{beneficios_html}</div>
                          <div class="prod-precos">
                            <span class="prod-preco-cheio">{_brl(prod['preco'])}</span>
                            <span class="prod-preco-parc">{_brl(prod['preco_parceiro'])}</span>
                          </div>
                          <div class="prod-economy">✨ -{}% · economia de {_brl(economy)}</div>
                          <div class="prod-estoque" style="margin-top:6px;">🏷 {prod['estoque']} em estoque</div>
                        </div>
                        """.format(pct),
                        unsafe_allow_html=True,
                    )
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if st.button("🛒 Adicionar", key=f"add_{prod['id']}",
                                     use_container_width=True):
                            add_to_cart(prod["id"])
                            st.rerun()
                    with bc2:
                        if st.button("🔍 Detalhes", key=f"det_{prod['id']}",
                                     use_container_width=True):
                            st.session_state.loja_view = "detalhe"
                            st.session_state.loja_produto_detalhe = prod["id"]
                            st.rerun()

with right:
    st.markdown("<div style='color:#a855f7;font-size:.9rem;font-weight:700;margin-bottom:12px;'>🛒 Carrinho</div>",
                unsafe_allow_html=True)

    cart = st.session_state.loja_cart
    if not cart:
        st.markdown(
            """<div style='text-align:center;padding:24px 12px;color:#6b7280;'>
            <div style='font-size:1.8rem;'>🛒</div>
            <div style='font-size:.82rem;margin-top:6px;'>Carrinho vazio</div></div>""",
            unsafe_allow_html=True,
        )
    else:
        for pid, qty in list(cart.items()):
            prod = next((p for p in CATALOG if p["id"] == pid), None)
            if not prod:
                continue
            subtotal = prod["preco_parceiro"] * qty
            st.markdown(
                f"""
                <div class="cart-mini">
                  <div class="cart-item-name">{prod['name']}</div>
                  <div class="cart-item-sub">
                    {qty}x {_brl(prod['preco_parceiro'])} = <strong style="color:#e879f9;">{_brl(subtotal)}</strong>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1:
                if st.button("-", key=f"dec_{pid}", use_container_width=True):
                    update_cart_qty(pid, qty - 1)
                    st.rerun()
            with c2:
                if st.button("+", key=f"inc_{pid}", use_container_width=True):
                    update_cart_qty(pid, qty + 1)
                    st.rerun()
            with c3:
                if st.button("🗑", key=f"rm_{pid}", use_container_width=True):
                    remove_from_cart(pid)
                    st.rerun()

        total_val = cart_total_valor()
        total_qty = cart_total_qty()
        st.markdown(
            f"""
            <div class="cart-total">
              <div>
                <div class="cart-total-lbl">{total_qty} item(s)</div>
                <div class="cart-total-val">{_brl(total_val)}</div>
              </div>
              <div style="color:#10b981;font-size:.78rem;font-weight:600;">Preço parceiro</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

        if st.button("💳 Ir para Checkout", type="primary", use_container_width=True, key="btn_checkout"):
            # Serializa carrinho para session_state de checkout
            items = []
            for pid, qty in cart.items():
                prod = next((p for p in CATALOG if p["id"] == pid), None)
                if prod:
                    items.append({
                        "id":             pid,
                        "name":           prod["name"],
                        "preco_unitario": prod["preco_parceiro"],
                        "quantidade":     qty,
                        "subtotal":       prod["preco_parceiro"] * qty,
                    })
            st.session_state["checkout_items"]  = items
            st.session_state["checkout_total"]   = cart_total_valor()
            st.switch_page("pages/5_💳_Checkout.py")

        if st.button("🗑 Limpar carrinho", use_container_width=True, key="btn_clear"):
            st.session_state.loja_cart = {}
            st.rerun()
