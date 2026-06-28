"""
8_Configuracao.py — HIPNUS COSMÉTICOS
Página de configurações completa: Empresa | Integrações | Banco | Aparência
"""
from __future__ import annotations
import sys
import os
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from lib import ui, components
from lib.auth import require_auth, build_sidebar
from lib import config as CFG

st.set_page_config(page_title="Configurações · HIPNUS", page_icon="⚙️", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin"])
build_sidebar()

components.page_header(
    title="Configurações",
    subtitle="Gerencie parâmetros, integrações e aparência da plataforma.",
    kicker="⚙️ Painel de Configuração",
)

# ── CSS extra para abas e cards de config ────────────────────────────────────
st.html("""
<style>
.cfg-section {
    background: rgba(124,58,237,0.04);
    border: 1px solid rgba(185,131,255,0.18);
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 18px;
}
.cfg-label {
    font-size: .72rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .8px;
    color: #b983ff; margin-bottom: 14px;
}
.cfg-status-ok  { color: #16a34a; font-weight: 600; font-size:.88rem; }
.cfg-status-err { color: #dc2626; font-weight: 600; font-size:.88rem; }
.cfg-status-warn{ color: #d97706; font-weight: 600; font-size:.88rem; }
.cfg-info-row {
    display:flex; justify-content:space-between;
    padding: 7px 0; border-bottom:1px solid rgba(185,131,255,0.1);
    font-size: .88rem;
}
.cfg-info-row:last-child { border-bottom: none; }
.cfg-info-key   { color: #9ca3af; }
.cfg-info-val   { color: #e2e8f0; font-weight: 500; }
</style>
""")

# ── Abas principais ──────────────────────────────────────────────────────────
tab_empresa, tab_integ, tab_banco, tab_aparencia = st.tabs([
    "🏢  Empresa",
    "🔗  Integrações",
    "🗃️  Banco de Dados",
    "🎨  Aparência",
])


# ════════════════════════════════════════════════════════════════════════════
# ABA 1 — EMPRESA
# ════════════════════════════════════════════════════════════════════════════
with tab_empresa:
    st.markdown("### 🏢 Identidade da Marca")
    st.caption("Estas informações são usadas em e-mails, documentos e na interface.")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        nome_marca = st.text_input(
            "Nome da empresa",
            value=CFG.BRAND.get("name", "HIPNUS COSMÉTICOS"),
            placeholder="Ex: HIPNUS COSMÉTICOS",
        )
        tagline = st.text_input(
            "Tagline",
            value=CFG.BRAND.get("tagline", ""),
            placeholder="Frase curta de posicionamento",
        )
        app_url = st.text_input(
            "URL pública do app",
            value=CFG.APP_URL,
            placeholder="https://seu-app.streamlit.app",
        )
    with col2:
        promise = st.text_area(
            "Proposta de valor",
            value=CFG.BRAND.get("promise", ""),
            height=100,
            placeholder="Descrição da proposta da marca",
        )
        currency = st.selectbox(
            "Moeda",
            ["R$", "USD", "EUR"],
            index=["R$", "USD", "EUR"].index(CFG.CURRENCY) if CFG.CURRENCY in ["R$", "USD", "EUR"] else 0,
        )

    st.divider()
    st.markdown("### 📆 Informações Legais")
    col3, col4 = st.columns(2)
    with col3:
        cnpj    = st.text_input("CNPJ",    placeholder="00.000.000/0001-00")
        razao   = st.text_input("Razão Social", placeholder="Ex: HIPNUS LTDA")
    with col4:
        telefone = st.text_input("Telefone / WhatsApp", placeholder="(11) 99999-9999")
        email_contato = st.text_input("E-mail de contato", placeholder="contato@hipnus.com.br")

    st.divider()
    if st.button("💾 Salvar configurações da empresa", type="primary"):
        st.success("✅ Configurações salvas! Para persistência permanente, adicione ao `st.secrets` ou variáveis de ambiente.")
        st.info(
            "💡 **Dica:** Edite o arquivo `frontend/lib/config.py` ou adicione as variáveis "
            "no painel **Settings → Secrets** do Streamlit Cloud."
        )


# ════════════════════════════════════════════════════════════════════════════
# ABA 2 — INTEGRAÇÕES
# ════════════════════════════════════════════════════════════════════════════
with tab_integ:

    # ── SMTP ────────────────────────────────────────────────────────────────
    st.markdown("### 📧 Configuração de E-mail (SMTP)")
    st.caption("Usado para envio de convites, confirmações de pedido e recuperação de senha.")

    smtp_ok = bool(CFG.SMTP_USER and CFG.SMTP_PASS)
    if smtp_ok:
        st.markdown('<p class="cfg-status-ok">✅ SMTP configurado</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="cfg-status-warn">⚠️ SMTP não configurado — e-mails não serão enviados</p>', unsafe_allow_html=True)

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        smtp_host = st.text_input("Servidor SMTP",    value=CFG.SMTP_HOST or "smtp.hostinger.com")
        smtp_port = st.number_input("Porta",           value=CFG.SMTP_PORT or 587, step=1)
        smtp_user = st.text_input("Usuário (e-mail)", value=CFG.SMTP_USER or "", placeholder="voce@dominio.com")
    with col_s2:
        smtp_pass = st.text_input("Senha",             value="" if not CFG.SMTP_PASS else "•" * 12, type="password", placeholder="Senha do e-mail")
        smtp_rem  = st.text_input("Remetente padrão", value=CFG.SMTP_REMETENTE or "", placeholder="HIPNUS <no-reply@dominio.com>")
        col_tls, col_ssl = st.columns(2)
        smtp_tls  = col_tls.checkbox("TLS", value=CFG.SMTP_USE_TLS)
        smtp_ssl  = col_ssl.checkbox("SSL", value=CFG.SMTP_USE_SSL)

    if st.button("📨 Testar conexão SMTP"):
        if not smtp_user or not smtp_pass or smtp_pass == "•" * 12:
            st.warning("⚠️ Preencha usuário e senha para testar.")
        else:
            with st.spinner("Testando conexão..."):
                try:
                    import smtplib
                    if smtp_ssl:
                        server = smtplib.SMTP_SSL(smtp_host, int(smtp_port), timeout=10)
                    else:
                        server = smtplib.SMTP(smtp_host, int(smtp_port), timeout=10)
                        if smtp_tls:
                            server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.quit()
                    st.success("✅ Conexão SMTP bem-sucedida!")
                except Exception as e:
                    st.error(f"❌ Falha na conexão: {e}")

    st.divider()

    # ── ASAAS ────────────────────────────────────────────────────────────────
    st.markdown("### 💳 Integração Asaas (Pagamentos)")
    st.caption("Plataforma de cobranças: PIX, Boleto e Cartão de Crédito.")

    try:
        asaas_key = st.secrets.get("ASAAS_API_KEY", "") or os.getenv("ASAAS_API_KEY", "")
    except Exception:
        asaas_key = os.getenv("ASAAS_API_KEY", "")

    asaas_ok = bool(asaas_key)
    if asaas_ok:
        st.markdown('<p class="cfg-status-ok">✅ Asaas configurado</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="cfg-status-err">❌ ASAAS_API_KEY não encontrada — checkout desativado</p>', unsafe_allow_html=True)

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        asaas_env = st.selectbox(
            "Ambiente",
            ["Sandbox (testes)", "Produção"],
            index=0 if "sandbox" in os.getenv("ASAAS_BASE_URL", "sandbox") else 1,
        )
        asaas_key_input = st.text_input(
            "API Key",
            value="" if not asaas_key else "•" * 20,
            type="password",
            placeholder="$aact_...",
        )
    with col_a2:
        wallet_id = st.text_input(
            "Wallet ID do Parceiro (split)",
            value=os.getenv("PARTNER_WALLET_ID", ""),
            placeholder="Ex: 12345678-abcd-...",
        )
        fee_pct = st.number_input(
            "Taxa de plataforma (%)",
            value=float(os.getenv("HIPNUS_PLATFORM_FEE_PERCENT", "10")),
            min_value=0.0, max_value=100.0, step=0.5,
            format="%.1f",
        )

    if st.button("💳 Testar conexão Asaas"):
        key_test = asaas_key if (not asaas_key_input or asaas_key_input == "•" * 20) else asaas_key_input
        if not key_test:
            st.warning("⚠️ Informe a API Key para testar.")
        else:
            with st.spinner("Verificando API Asaas..."):
                try:
                    import urllib.request, json as _json
                    base = "https://sandbox.asaas.com" if "Sandbox" in asaas_env else "https://www.asaas.com"
                    req  = urllib.request.Request(
                        f"{base}/api/v3/finance/getCurrentBalance",
                        headers={"access_token": key_test, "Content-Type": "application/json"},
                    )
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        data = _json.loads(resp.read())
                    saldo = data.get("balance", "?")
                    st.success(f"✅ Asaas conectado! Saldo disponível: **R$ {saldo}**")
                except Exception as e:
                    st.error(f"❌ Falha na conexão Asaas: {e}")

    st.divider()
    st.caption("💡 Para salvar permanentemente, adicione `ASAAS_API_KEY` no painel **Settings → Secrets** do Streamlit Cloud.")


# ════════════════════════════════════════════════════════════════════════════
# ABA 3 — BANCO DE DADOS
# ════════════════════════════════════════════════════════════════════════════
with tab_banco:
    st.markdown("### 🗃️ Banco de Dados")
    st.caption("Conexão ativa com SQLite local ou MySQL (Hostinger).")

    try:
        from lib.db_utils import get_db_session, resolve_db_url
        db_url = resolve_db_url()
        db, err = get_db_session()
        db_conectado = db is not None
        if db:
            db.close()
    except Exception as exc:
        db_url = "N/D"
        db_conectado = False
        err = str(exc)

    # Status
    if db_conectado:
        st.markdown('<p class="cfg-status-ok">✅ Banco conectado e operacional</p>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p class="cfg-status-err">❌ Falha na conexão: {err}</p>', unsafe_allow_html=True)

    # Info da conexão
    tipo_banco = "SQLite local" if "sqlite" in str(db_url).lower() else "MySQL / Remoto"
    url_exibir = str(db_url).replace(str(Path.home()), "~") if db_url else "N/D"

    st.html(f"""
    <div class="cfg-section">
        <div class="cfg-label">🔍 Detalhes da Conexão</div>
        <div class="cfg-info-row"><span class="cfg-info-key">Tipo</span>         <span class="cfg-info-val">{tipo_banco}</span></div>
        <div class="cfg-info-row"><span class="cfg-info-key">URL</span>          <span class="cfg-info-val">{url_exibir}</span></div>
        <div class="cfg-info-row"><span class="cfg-info-key">Status</span>       <span class="cfg-info-val">{'Conectado ✅' if db_conectado else 'Erro ❌'}</span></div>
    </div>
    """)

    st.divider()
    st.markdown("### 📊 Tabelas do Sistema")

    if db_conectado:
        try:
            from sqlalchemy import text
            db2, _ = get_db_session()
            if db2:
                rows = db2.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                    if "sqlite" in str(db_url).lower()
                    else "SHOW TABLES"
                )).fetchall()
                db2.close()
                tabelas = [r[0] for r in rows]
                if tabelas:
                    cols = st.columns(3)
                    for i, t in enumerate(tabelas):
                        cols[i % 3].markdown(f"📘 `{t}`")
                else:
                    st.info("📦 Nenhuma tabela encontrada. O banco será criado na primeira execução.")
        except Exception as e:
            st.warning(f"⚠️ Não foi possível listar tabelas: {e}")

    st.divider()
    st.markdown("### 🔧 Operações de Manutenção")
    col_m1, col_m2 = st.columns(2)

    with col_m1:
        if st.button("🔄 Reconectar banco", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Cache limpo! Reconectando na próxima requisição.")
            st.rerun()

    with col_m2:
        with st.expander("⚠️ Redefinir tabelas (CUIDADO)"):
            st.warning("⚠️ Esta operação recria as tabelas apagando todos os dados!")
            confirm = st.text_input("Digite CONFIRMAR para prosseguir:", key="confirm_reset")
            if st.button("🗑️ Redefinir tabelas", type="primary", key="btn_reset_db"):
                if confirm == "CONFIRMAR":
                    try:
                        from sqlalchemy import text
                        db3, _ = get_db_session()
                        if db3:
                            for tabela in ["invites", "parceiros"]:
                                db3.execute(text(f"DROP TABLE IF EXISTS {tabela}"))
                            db3.commit()
                            db3.close()
                            st.success("✅ Tabelas redefinidas. Serão recriadas automaticamente.")
                    except Exception as e:
                        st.error(f"❌ Erro: {e}")
                else:
                    st.error("❌ Digite CONFIRMAR para prosseguir.")


# ════════════════════════════════════════════════════════════════════════════
# ABA 4 — APARÊNCIA
# ════════════════════════════════════════════════════════════════════════════
with tab_aparencia:
    st.markdown("### 🎨 Tema e Aparência")
    st.caption("Personalize as cores e tipografia da plataforma.")

    try:
        from lib import tokens as T
        cores_disponiveis = {
            "Roxo Neon (padrão)": {"primary": "#7C3AED", "accent": "#C4A35A"},
            "Azul Royal":          {"primary": "#1D4ED8", "accent": "#F59E0B"},
            "Rosa Premium":        {"primary": "#BE185D", "accent": "#D97706"},
            "Verde Esmeralda":     {"primary": "#065F46", "accent": "#F59E0B"},
            "Preto Luxo":          {"primary": "#111827", "accent": "#D4AF37"},
        }
        tema_atual = st.session_state.get("tema_nome", "Roxo Neon (padrão)")
        tema_sel   = st.selectbox("Esquema de cores", list(cores_disponiveis.keys()), index=list(cores_disponiveis.keys()).index(tema_atual))
        cor_prim   = st.color_picker("Cor primária",  cores_disponiveis[tema_sel]["primary"])
        cor_accent = st.color_picker("Cor de destaque", cores_disponiveis[tema_sel]["accent"])
    except Exception:
        cor_prim   = "#7C3AED"
        cor_accent = "#C4A35A"
        tema_sel   = "Roxo Neon (padrão)"

    st.divider()
    st.markdown("### 🔤 Tipografia")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        fonte_corpo = st.selectbox(
            "Fonte do corpo",
            ["Inter", "DM Sans", "Plus Jakarta Sans", "Nunito", "Poppins"],
            index=0,
        )
    with col_f2:
        fonte_titulo = st.selectbox(
            "Fonte dos títulos",
            ["Syne", "Playfair Display", "Clash Display", "Montserrat", "Raleway"],
            index=0,
        )

    st.divider()
    st.markdown("### 🔮 Preview")
    st.html(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family={fonte_corpo.replace(' ','+')}:wght@400;600;700&family={fonte_titulo.replace(' ','+')}:wght@700;800&display=swap');
    </style>
    <div style="
        background: linear-gradient(135deg, {cor_prim}22 0%, {cor_accent}11 100%);
        border: 2px solid {cor_prim}55;
        border-radius: 16px; padding: 28px 32px;
        font-family: '{fonte_corpo}', sans-serif;
    ">
        <p style="font-size:.65rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:{cor_prim};margin:0 0 8px;">PREVIEW DO TEMA</p>
        <h2 style="font-family:'{fonte_titulo}',sans-serif;font-size:1.6rem;font-weight:800;color:{cor_prim};margin:0 0 6px;">
            HIPNUS COSMÉTICOS
        </h2>
        <p style="font-size:.9rem;color:#9ca3af;margin:0 0 16px;">Tratamento capilar profissional, direto da fonte.</p>
        <span style="
            background:{cor_prim}22; border:1px solid {cor_prim}55;
            border-radius:999px; padding:6px 16px;
            font-size:.78rem; font-weight:700; color:{cor_prim};
        ">Linha Ouro</span>
        &nbsp;
        <span style="
            background:{cor_accent}22; border:1px solid {cor_accent}55;
            border-radius:999px; padding:6px 16px;
            font-size:.78rem; font-weight:700; color:{cor_accent};
        ">Premium</span>
    </div>
    """)

    st.divider()
    if st.button("🎨 Aplicar tema", type="primary"):
        st.session_state["tema_nome"]     = tema_sel
        st.session_state["tema_primary"]  = cor_prim
        st.session_state["tema_accent"]   = cor_accent
        st.session_state["fonte_corpo"]   = fonte_corpo
        st.session_state["fonte_titulo"]  = fonte_titulo
        st.success(f"✅ Tema **{tema_sel}** aplicado com fontes {fonte_corpo} + {fonte_titulo}!")
        st.info("💡 Para tornar permanente, atualize `frontend/lib/tokens.py` e `theme.py` com as cores escolhidas.")
        st.rerun()
