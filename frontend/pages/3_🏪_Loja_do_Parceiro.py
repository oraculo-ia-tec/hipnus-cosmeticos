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
from lib.theme import apply_theme

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
.prod-preco-parceiro {
    font-size:1.3rem; font-weight:800;
    background:linear-gradient(90deg,#e879f9,#a855f7);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.prod-preco-cheio { color:#6b7280; font-size:.82rem; text-decoration:line-through; }
.prod-economia {
    background:rgba(34,197,94,.15); border:1px solid rgba(34,197,94,.3);
    color:#86efac; border-radius:6px; padding:2px 8px; font-size:.72rem;
}
.prod-estoque      { color:#6b7280; font-size:.72rem; margin-bottom:14px; }
.prod-estoque.baixo { color:#fbbf24; }
.section-title {
    color:#f5d0fe; font-size:1.1rem; font-weight:700;
    border-left:3px solid #7c3aed; padding-left:10px; margin-bottom:16px;
}
.resumo-box {
    background:linear-gradient(135deg,#1a0f2e,#2d1558);
    border:1px solid rgba(168,85,247,.3); border-radius:16px; padding:24px;
}
.resumo-linha {
    display:flex; justify-content:space-between; color:#c4b5fd;
    font-size:.9rem; padding:6px 0; border-bottom:1px solid rgba(168,85,247,.1);
}
.resumo-total       { display:flex; justify-content:space-between; margin-top:12px; }
.resumo-total-label { color:#f5d0fe; font-size:1rem; font-weight:700; }
.resumo-total-val {
    font-size:1.4rem; font-weight:800;
    background:linear-gradient(90deg,#e879f9,#a855f7);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.checkout-section {
    background:#1c1626; border:1px solid rgba(168,85,247,.2);
    border-radius:16px; padding:24px; margin-bottom:20px;
}
.checkout-section-title {
    color:#e879f9; font-size:.9rem; font-weight:700;
    letter-spacing:.5px; text-transform:uppercase; margin-bottom:16px;
}
</style>
""", unsafe_allow_html=True)


def render_loja():
    user = st.session_state.get("user", {})
    nome = user.get("nome", "Parceiro") if isinstance(user, dict) else "Parceiro"

    col_logo, col_cart = st.columns([8, 2])
    with col_logo:
        st.markdown('<div style="font-size:1.1rem;font-weight:800;background:linear-gradient(90deg,#e879f9,#a855f7);-webkit-background-clip:text;-webkit-text-fill-color:transparent">🏪 HIPNUS · Loja do Parceiro</div>', unsafe_allow_html=True)
    with col_cart:
        qty = cart_total_qty()
        label = "ns" if qty != 1 else ""
        if st.button(f"🛒 {qty} item{label}", key="go_cart_top", use_container_width=True):
            st.session_state.loja_view = "carrinho"
            st.rerun()

    st.markdown(
        '<div class="loja-hero">'
        '<div class="loja-hero-badge">✨ EXCLUSIVO PARCEIROS</div>'
        f'<h1 class="loja-hero-title">Bem-vindo(a), {nome}!</h1>'
        '<p class="loja-hero-sub">Preços especiais de parceiro em toda a linha HIPNUS.<br>'
        'Descontos de até 35% e frete grátis acima de R$ 500.</p>'
        '<div class="loja-hero-stats">'
        f'<div class="loja-hero-stat"><div class="loja-hero-stat-val">{len(CATALOG)}</div><div class="loja-hero-stat-lbl">Produtos</div></div>'
        f'<div class="loja-hero-stat"><div class="loja-hero-stat-val">{len(LINHAS)}</div><div class="loja-hero-stat-lbl">Linhas</div></div>'
        '<div class="loja-hero-stat"><div class="loja-hero-stat-val">25%</div><div class="loja-hero-stat-lbl">Desconto médio</div></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    with st.expander("🔍 Busca · Filtros", expanded=True):
        col_busca, col_cat = st.columns([3, 2])
        with col_busca:
            busca = st.text_input("Buscar", value=st.session_state.loja_busca,
                                  placeholder="nome, benefício...", label_visibility="collapsed")
            st.session_state.loja_busca = busca
        with col_cat:
            idx_cat = CATEGORIAS.index(st.session_state.loja_filtro_cat) if st.session_state.loja_filtro_cat in CATEGORIAS else 0
            cat = st.selectbox("Categoria", CATEGORIAS, index=idx_cat, label_visibility="collapsed")
            st.session_state.loja_filtro_cat = cat
        linhas_sel = st.multiselect("Linhas", LINHAS, default=st.session_state.loja_filtro_linha)
        st.session_state.loja_filtro_linha = linhas_sel

    prods = get_filtered_products()
    col_res, col_ord = st.columns([6, 2])
    with col_res:
        st.caption(f"{len(prods)} produto(s) encontrado(s)")
    with col_ord:
        ordem = st.selectbox("Ordenar", ["Destaque", "Menor preço", "Maior preço", "Nome A-Z"],
                             label_visibility="collapsed")
    if ordem == "Menor preço":
        prods = sorted(prods, key=lambda p: p["preco_parceiro"])
    elif ordem == "Maior preço":
        prods = sorted(prods, key=lambda p: p["preco_parceiro"], reverse=True)
    elif ordem == "Nome A-Z":
        prods = sorted(prods, key=lambda p: p["name"])

    if not prods:
        st.info("🔍 Nenhum produto encontrado. Tente outro filtro.")
        if st.button("Limpar filtros"):
            st.session_state.loja_busca = ""
            st.session_state.loja_filtro_cat = "Todas"
            st.session_state.loja_filtro_linha = []
            st.rerun()
        return

    for row_start in range(0, len(prods), 3):
        row = prods[row_start:row_start + 3]
        cols = st.columns(3)
        for col, prod in zip(cols, row):
            with col:
                economia = prod["preco"] - prod["preco_parceiro"]
                estoque_cls = "baixo" if prod["estoque"] < 20 else ""
                badge_html = f'<div class="prod-badge">{prod["badge"]}</div>' if prod["badge"] else ""
                bens = "".join(f'<span class="prod-benefit-tag">{b}</span>' for b in prod["beneficios"])
                est_icon = "⚠️" if prod["estoque"] < 20 else "✅"
                economia_fmt = f"R$ {economia:.0f}"
                st.markdown(
                    f'<div class="prod-card">{badge_html}'
                    f'<div class="prod-linha">🌿 {prod["linha"]}</div>'
                    f'<div class="prod-name">{prod["name"]}</div>'
                    f'<div class="prod-desc">{prod["descricao"]}</div>'
                    f'<div class="prod-volume">📦 {prod["volume"]}</div>'
                    f'<div class="prod-beneficios">{bens}</div>'
                    f'<div class="prod-precos">'
                    f'<span class="prod-preco-parceiro">R$ {prod["preco_parceiro"]:.2f}</span>'
                    f'<span class="prod-preco-cheio">R$ {prod["preco"]:.2f}</span>'
                    f'<span class="prod-economia">-{economia_fmt}</span></div>'
                    f'<div class="prod-estoque {estoque_cls}">{est_icon} {prod["estoque"]} em estoque</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                b1, b2 = st.columns([3, 1])
                with b1:
                    if st.button("🛒 Adicionar", key=f"add_{prod['id']}", use_container_width=True):
                        add_to_cart(prod["id"])
                        st.toast(f"✅ {prod['name']} adicionado!", icon="🛒")
                        st.rerun()
                with b2:
                    q_cart = st.session_state.loja_cart.get(prod["id"], 0)
                    if q_cart:
                        st.markdown(
                            f'<div style="text-align:center;color:#a855f7;font-weight:800;padding-top:6px">{q_cart}</div>',
                            unsafe_allow_html=True,
                        )


def render_carrinho():
    c1, c2, c3 = st.columns([2, 5, 2])
    with c1:
        if st.button("← Loja", key="cart_back"):
            st.session_state.loja_view = "loja"; st.rerun()
    with c2:
        st.markdown('<div class="section-title" style="font-size:1.3rem">🛒 Carrinho</div>', unsafe_allow_html=True)
    with c3:
        if st.session_state.loja_cart:
            if st.button("🗑️ Limpar", key="clear_cart"):
                st.session_state.loja_cart = {}; st.rerun()

    cart = st.session_state.loja_cart
    if not cart:
        st.info("🛒 Carrinho vazio. Adicione produtos na loja.")
        if st.button("← Ir para a loja", key="back_to_loja_empty"):
            st.session_state.loja_view = "loja"; st.rerun()
        return

    col_itens, col_resumo = st.columns([3, 2])
    with col_itens:
        st.markdown('<div class="section-title">Itens</div>', unsafe_allow_html=True)
        for pid, qty in list(cart.items()):
            prod = next((p for p in CATALOG if p["id"] == pid), None)
            if not prod:
                continue
            subtotal = prod["preco_parceiro"] * qty
            st.markdown(
                f'<div style="background:#1c1626;border:1px solid rgba(168,85,247,.2);'
                f'border-radius:12px;padding:14px;margin-bottom:10px">'
                f'<div style="color:#9ca3af;font-size:.75rem">{prod["linha"]} · {prod["volume"]}</div>'
                f'<div style="color:#f5d0fe;font-weight:700">{prod["name"]}</div>'
                f'<div style="color:#a855f7;font-weight:800">R$ {subtotal:.2f}</div></div>',
                unsafe_allow_html=True,
            )
            ca, cb, cc, cd = st.columns([1, 2, 1, 1])
            with ca:
                if st.button("−", key=f"dec_{pid}"):
                    update_cart_qty(pid, qty - 1); st.rerun()
            with cb:
                preco_fmt = f"R$ {prod['preco_parceiro']:.2f}"
                st.markdown(
                    f'<div style="text-align:center;color:#e879f9;font-weight:700;padding-top:4px">{qty}x · {preco_fmt}</div>',
                    unsafe_allow_html=True,
                )
            with cc:
                if st.button("+", key=f"inc_{pid}"):
                    update_cart_qty(pid, qty + 1); st.rerun()
            with cd:
                if st.button("🗑", key=f"del_{pid}"):
                    remove_from_cart(pid); st.rerun()

    with col_resumo:
        st.markdown('<div class="section-title">Resumo</div>', unsafe_allow_html=True)
        total = cart_total_valor()
        total_cheio = sum(
            next((p for p in CATALOG if p["id"] == pid), {}).get("preco", 0) * qty
            for pid, qty in cart.items()
        )
        economia = total_cheio - total
        frete = 0.0 if total >= 500 else 29.90
        frete_cor = "#86efac" if frete == 0 else "#f5d0fe"
        frete_str = "GRATIS" if frete == 0 else f"R$ {frete:.2f}"
        frete_msg = "Frete gratis!" if frete == 0 else f"Falta R$ {500-total:.0f} para frete gratis"
        itens_html = "".join(
            '<div class="resumo-linha">'
            '<span>' + next((p["name"] for p in CATALOG if p["id"]==pid), pid)[:28] + '</span>'
            '<span>R$ ' + f"{next((p for p in CATALOG if p['id']==pid), {}).get('preco_parceiro', 0)*q:.2f}" + '</span></div>'
            for pid, q in cart.items()
        )
        st.markdown(
            f'<div class="resumo-box">{itens_html}'
            f'<div class="resumo-linha"><span>🏷️ Economia</span><span style="color:#86efac">-R$ {economia:.2f}</span></div>'
            f'<div class="resumo-linha"><span>🚚 Frete</span><span style="color:{frete_cor}">{frete_str}</span></div>'
            f'<p style="color:#a855f7;font-size:.75rem;margin:8px 0 0">{frete_msg}</p>'
            f'<div class="resumo-total"><span class="resumo-total-label">Total</span>'
            f'<span class="resumo-total-val">R$ {total+frete:.2f}</span></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💳 Finalizar Pedido", key="go_checkout", use_container_width=True):
            st.session_state.loja_view = "checkout"; st.rerun()


def render_checkout():
    c1, c2 = st.columns([2, 7])
    with c1:
        if st.button("← Carrinho", key="checkout_back"):
            st.session_state.loja_view = "carrinho"; st.rerun()
    with c2:
        st.markdown('<div class="section-title" style="font-size:1.3rem">💳 Finalizar Pedido</div>', unsafe_allow_html=True)

    user = st.session_state.get("user", {})
    nome_user  = user.get("nome",  "") if isinstance(user, dict) else ""
    email_user = user.get("email", "") if isinstance(user, dict) else ""

    col_form, col_resumo = st.columns([3, 2])
    with col_form:
        st.markdown('<div class="checkout-section"><div class="checkout-section-title">📦 Dados de Entrega</div>', unsafe_allow_html=True)
        nome  = st.text_input("Nome completo",   value=nome_user,  key="co_nome")
        email = st.text_input("E-mail",           value=email_user, key="co_email")
        ct, cc = st.columns(2)
        with ct: tel = st.text_input("Telefone", key="co_tel", placeholder="(11) 9xxxx-xxxx")
        with cc: cpf = st.text_input("CPF",      key="co_cpf", placeholder="000.000.000-00")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="checkout-section"><div class="checkout-section-title">🏠 Endereço</div>', unsafe_allow_html=True)
        cep_col, _ = st.columns([2, 3])
        with cep_col: cep = st.text_input("CEP", key="co_cep", placeholder="00000-000")
        rua = st.text_input("Rua / Av.", key="co_rua")
        cn, cc2 = st.columns([1, 3])
        with cn:  num  = st.text_input("Num",          key="co_num")
        with cc2: comp = st.text_input("Complemento", key="co_comp")
        cb, cci, cuf = st.columns([2, 3, 1])
        with cb:  bairro = st.text_input("Bairro",  key="co_bairro")
        with cci: cidade = st.text_input("Cidade",  key="co_cidade")
        with cuf: uf     = st.text_input("UF",      key="co_uf", max_chars=2)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<div class="checkout-section"><div class="checkout-section-title">💳 Pagamento</div>', unsafe_allow_html=True)
        metodo = st.radio("Pagamento", ["💠 PIX", "📄 Boleto", "💳 Cartao de Credito"],
                          key="co_metodo", horizontal=True)
        if "Cartao" in metodo:
            cnn, cvv = st.columns([3, 1])
            with cnn: st.text_input("Numero do cartao", key="co_card_num", placeholder="0000 0000 0000 0000")
            with cvv: st.text_input("CVV", key="co_cvv", placeholder="123", max_chars=3)
            cnm, cvc = st.columns(2)
            with cnm: st.text_input("Nome no cartao", key="co_card_nome")
            with cvc: st.text_input("Validade", key="co_venc", placeholder="MM/AA")
            st.selectbox("Parcelamento", [f"{i}x sem juros" for i in range(1, 7)], key="co_parcelas")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_resumo:
        st.markdown('<div class="section-title">Resumo</div>', unsafe_allow_html=True)
        cart  = st.session_state.loja_cart
        total = cart_total_valor()
        frete = 0.0 if total >= 500 else 29.90
        grand = total + frete
        frete_cor = "#86efac" if frete == 0 else "#f5d0fe"
        frete_str = "GRATIS" if frete == 0 else f"R$ {frete:.2f}"
        itens_resumo = "".join(
            '<div class="resumo-linha">'
            '<span>' + next((p["name"] for p in CATALOG if p["id"]==pid), pid)[:22] + f'... x{q}</span>'
            '<span>R$ ' + f"{next((p for p in CATALOG if p['id']==pid), {}).get('preco_parceiro', 0)*q:.2f}" + '</span></div>'
            for pid, q in cart.items()
        )
        st.markdown(
            f'<div class="resumo-box">{itens_resumo}'
            f'<div class="resumo-linha"><span>🚚 Frete</span><span style="color:{frete_cor}">{frete_str}</span></div>'
            f'<div class="resumo-total"><span class="resumo-total-label">Total</span>'
            f'<span class="resumo-total-val">R$ {grand:.2f}</span></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        campos_ok = all([nome, email, tel, cpf, cep, rua, num, bairro, cidade, uf])
        if not campos_ok:
            st.warning("Preencha todos os campos obrigatorios.", icon="⚠️")
        if st.button("✅ Confirmar Pedido", key="confirmar_pedido",
                     use_container_width=True, disabled=not campos_ok):
            pedido = {
                "items": [{"id": pid, "name": next((p["name"] for p in CATALOG if p["id"]==pid), pid),
                           "price": next((p["preco_parceiro"] for p in CATALOG if p["id"]==pid), 0),
                           "qty": q} for pid, q in cart.items()],
                "cliente": {"nome": nome, "email": email, "tel": tel, "cpf": cpf},
                "endereco": {"cep": cep, "rua": rua, "num": num, "comp": comp,
                             "bairro": bairro, "cidade": cidade, "uf": uf},
                "pagamento": metodo, "total": grand, "frete": frete,
            }
            st.session_state["loja_pedido_confirmado"] = pedido
            st.session_state.loja_cart = {}
            st.session_state.loja_view = "confirmado"
            st.rerun()


def render_confirmado():
    pedido  = st.session_state.get("loja_pedido_confirmado", {})
    total   = pedido.get("total", 0)
    metodo  = pedido.get("pagamento", "")
    cliente = pedido.get("cliente", {})
    nome_cli = cliente.get("nome", "")
    email_cli = cliente.get("email", "")
    st.balloons()
    st.markdown(
        '<div style="text-align:center;padding:60px 20px">'
        '<div style="font-size:4rem">🎉</div>'
        '<h1 style="background:linear-gradient(90deg,#e879f9,#a855f7);-webkit-background-clip:text;'
        '-webkit-text-fill-color:transparent;font-size:2rem;margin:16px 0 8px">Pedido Confirmado!</h1>'
        f'<p style="color:#c4b5fd;font-size:1.05rem">Obrigado, <strong>{nome_cli}</strong>!<br>'
        f'Pedido de <strong>R$ {total:.2f}</strong> via <strong>{metodo}</strong> recebido.</p>'
        f'<p style="color:#9ca3af;font-size:.85rem;margin-top:12px">Confirmacao enviada para {email_cli}</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏪 Continuar comprando", key="cont_comprando", use_container_width=True):
            st.session_state.loja_view = "loja"
            st.session_state.loja_pedido_confirmado = {}
            st.rerun()
    with col2:
        if st.button("📊 Ver Dashboard", key="go_dash", use_container_width=True):
            st.switch_page("pages/0_Dashboard.py")


_VIEW_MAP = {"loja": render_loja, "carrinho": render_carrinho,
             "checkout": render_checkout, "confirmado": render_confirmado}
_VIEW_MAP.get(st.session_state.loja_view, render_loja)()
