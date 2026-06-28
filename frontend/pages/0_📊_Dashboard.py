"""
0_📊_Dashboard.py — HIPNUS COSMÉTICOS
=======================================
Skill #4 — Dashboard Admin em tempo real.

Visão unificada de:
  - Métricas financeiras via Asaas (cobranças por status e método)
  - Convites de parceiros ativos e utilizados (banco local)
  - Parceiros cadastrados (banco local)
  - Histórico de pedidos da sessão atual

Acesso restrito a super_admin e admin.
Atualização manual via botão ↻.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from lib import ui, components
from lib.auth import require_auth, build_sidebar
from lib.asaas_client import AsaasClient, AsaasError
from lib.invite_db import listar_invites_db
from lib.user_db import listar_parceiros

st.set_page_config(page_title="Dashboard · HIPNUS", page_icon="📊", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin"])
build_sidebar()

components.page_header(
    title="Dashboard Admin",
    subtitle="Visão consolidada de cobranças, convites e parceiros da plataforma.",
    kicker="📊 Painel Operacional",
)

# ─── Helpers ──────────────────────────────────────────────────────────────────────────────────
def _brl(v) -> str:
    try:
        val = Decimal(str(v))
    except Exception:
        val = Decimal("0")
    s = f"{val:,.2f}"
    return f"R$ {s}".replace(",", "X").replace(".", ",").replace("X", ".")

def _status_badge(status: str) -> str:
    return {
        "RECEIVED":  "🟢 Recebido",
        "CONFIRMED": "🟢 Confirmado",
        "PENDING":   "🟡 Pendente",
        "OVERDUE":   "🔴 Vencido",
        "REFUNDED":  "🔵 Estornado",
        "CANCELLED": "⚪ Cancelado",
    }.get(status, status)

def _method_badge(bt: str) -> str:
    return {"PIX": "PIX 🟣", "BOLETO": "Boleto 📜", "CREDIT_CARD": "Cartão 💳"}.get(bt, bt)


# ─── Carrega dados ─────────────────────────────────────────────────────────────────────────────────
def _load_asaas_payments(days: int = 30) -> tuple[list[dict], str | None]:
    try:
        client = AsaasClient()
        if not client.api_key:
            return [], "ASAAS_API_KEY não configurada."
        date_from = (date.today() - timedelta(days=days)).isoformat()
        resp = client.list_payments(date_created_ge=date_from, limit=100)
        return resp.get("data", []), None
    except AsaasError as exc:
        return [], f"Asaas API {exc.status_code}: {exc.payload}"
    except Exception as exc:
        return [], str(exc)

def _load_invites() -> list[dict]:
    try:
        return listar_invites_db()
    except Exception:
        return []

def _load_partners() -> list[dict]:
    try:
        return listar_parceiros()
    except Exception:
        return []


# ─── Filtro de período ────────────────────────────────────────────────────────────────────────
st.html("""
<div style="
  background: linear-gradient(135deg, rgba(15,10,30,.85), rgba(30,15,55,.75));
  border: 1px solid rgba(185,131,255,.25); border-radius: 16px;
  padding: 18px 24px 14px; margin-bottom: 4px; backdrop-filter: blur(8px);
">
  <div style="font-family:'Inter',sans-serif;font-size:.65rem;font-weight:700;
    letter-spacing:1.8px;text-transform:uppercase;
    color:rgba(185,131,255,.55);margin-bottom:10px;">⏱ Filtro de período</div>
</div>
""")

_f1, _f2 = st.columns([2, 1])
with _f1:
    dias = st.selectbox("⏱ Cobranças dos últimos:", options=[7,15,30,60,90], index=2,
                        format_func=lambda d: f"{d} dias", key="dash_dias")
with _f2:
    st.write("")
    atualizar = st.button("↻ Atualizar dados", use_container_width=True, key="_btn_atualizar")

st.html("<div style='margin-bottom:20px;'></div>")


# ─── Cache de dados ───────────────────────────────────────────────────────────────────────────────
cache_key = f"_dash_payments_{dias}"
if atualizar or cache_key not in st.session_state:
    with st.spinner("Buscando cobranças na API Asaas..."):
        payments, asaas_error = _load_asaas_payments(dias)
    st.session_state[cache_key] = payments
    st.session_state["_dash_asaas_error"] = asaas_error
else:
    payments = st.session_state[cache_key]
    asaas_error = st.session_state.get("_dash_asaas_error")

invites  = _load_invites()
partners = _load_partners()
session_orders = st.session_state.get("historico_pedidos", [])


# ─── KPIs ──────────────────────────────────────────────────────────────────────────────────────
if asaas_error:
    st.warning(f"⚠️ API Asaas indisponível: {asaas_error}. Exibindo dados locais da sessão.")

if payments:
    total_recebido = sum(Decimal(str(p.get("value",0))) for p in payments if p.get("status") in ("RECEIVED","CONFIRMED"))
    total_pendente = sum(Decimal(str(p.get("value",0))) for p in payments if p.get("status") == "PENDING")
    total_vencido  = sum(Decimal(str(p.get("value",0))) for p in payments if p.get("status") == "OVERDUE")
    n_recebido = sum(1 for p in payments if p.get("status") in ("RECEIVED","CONFIRMED"))
    n_pendente = sum(1 for p in payments if p.get("status") == "PENDING")
    n_vencido  = sum(1 for p in payments if p.get("status") == "OVERDUE")
elif session_orders:
    total_recebido = sum(Decimal(str(o.get("totais",{}).get("total",0))) for o in session_orders)
    total_pendente = total_vencido = Decimal("0")
    n_recebido = len(session_orders)
    n_pendente = n_vencido = 0
else:
    total_recebido = total_pendente = total_vencido = Decimal("0")
    n_recebido = n_pendente = n_vencido = 0

n_invites_total  = len(invites)
n_invites_ativos = sum(1 for i in invites if not i.get("used"))
n_invites_usado  = sum(1 for i in invites if i.get("used"))
n_parceiros      = len(partners)

components.section_title("Financeiro")
k1, k2, k3, k4 = st.columns(4)
k1.metric("🟢 Recebido",      _brl(total_recebido), f"{n_recebido} cobranças")
k2.metric("🟡 Pendente",      _brl(total_pendente), f"{n_pendente} cobranças")
k3.metric("🔴 Vencido",       _brl(total_vencido),  f"{n_vencido} cobranças")
k4.metric("📊 Total cobranças", len(payments) or len(session_orders))

components.divider()
components.section_title("Plataforma")
p1, p2, p3, p4 = st.columns(4)
p1.metric("🤝 Parceiros",      n_parceiros)
p2.metric("📨 Convites ativos", n_invites_ativos)
p3.metric("✅ Convites usados", n_invites_usado)
p4.metric("📍 Convites totais", n_invites_total)

components.divider()
tab_cob, tab_inv, tab_par, tab_sess = st.tabs(["💳 Cobranças", "📨 Convites", "🤝 Parceiros", "🛘 Sessão"])

with tab_cob:
    components.section_title(f"Cobranças — últimos {dias} dias")
    if not payments:
        if session_orders:
            st.info("📋 API Asaas sem dados. Exibindo pedidos da sessão atual.")
            for o in session_orders:
                totais = o.get("totais", {})
                st.html(f"""
                <div style="background:#f8f7fc;border:1px solid #e5e0f5;border-radius:12px;
                            padding:14px 18px;margin:8px 0;display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-size:.85rem;font-weight:700;color:#1a0a2e;">{o.get('external_ref','--')}</div>
                        <div style="font-size:.75rem;color:#6b7280;margin-top:2px;">{_status_badge(o.get('status',''))} &nbsp;·&nbsp; {_method_badge('')}</div>
                    </div>
                    <div style="font-size:1rem;font-weight:800;color:#7c3aed;">{_brl(totais.get('total',0))}</div>
                </div>""")
        else:
            components.empty_state(icon="💳", title="Sem cobranças",
                                    message="Configure ASAAS_API_KEY para ver dados em tempo real.")
    else:
        for p in payments:
            ref  = p.get("externalReference") or p.get("description", "—")
            val  = _brl(p.get("value", 0))
            stat = _status_badge(p.get("status", ""))
            meth = _method_badge(p.get("billingType", ""))
            dt   = (p.get("dateCreated") or "")[:10]
            link = p.get("invoiceUrl") or p.get("bankSlipUrl") or ""
            st.html(f"""
            <div style="background:#f8f7fc;border:1px solid #e5e0f5;border-radius:12px;
                        padding:14px 18px;margin:8px 0;display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-size:.85rem;font-weight:700;color:#1a0a2e;">{ref}</div>
                    <div style="font-size:.75rem;color:#6b7280;margin-top:2px;">{stat} &nbsp;·&nbsp; {meth} &nbsp;·&nbsp; {dt}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:1rem;font-weight:800;color:#7c3aed;">{val}</div>
                    {f'<a href="{link}" target="_blank" style="font-size:.72rem;color:#7c3aed;">Ver cobrança ↗</a>' if link else ''}
                </div>
            </div>""")

with tab_inv:
    components.section_title("Convites de parceiros")
    if not invites:
        components.empty_state(icon="📨", title="Sem convites", message="Crie convites em Convites de Parceiros.")
    else:
        for inv in invites:
            usado      = inv.get("used", False)
            badge_uso  = "✅ Usado" if usado else "⏳ Pendente"
            role_label = {"b2b":"🎤 Profissional","b2c":"👤 Cliente","admin":"🛡️ Admin"}.get(inv.get("role",""), inv.get("role",""))
            expires    = str(inv.get("expires_at") or "")[:10]
            email      = inv.get("email", "")
            st.html(f"""
            <div style="background:{'#f0fdf4' if usado else '#faf7ff'};border:1px solid {'#86efac' if usado else '#e9d5ff'};
                        border-radius:12px;padding:12px 18px;margin:6px 0;display:flex;justify-content:space-between;">
                <div>
                    <div style="font-size:.85rem;font-weight:700;color:#1a0a2e;">{email}</div>
                    <div style="font-size:.75rem;color:#6b7280;margin-top:2px;">{role_label} &nbsp;·&nbsp; Expira: {expires}</div>
                </div>
                <div style="font-size:.82rem;font-weight:700;color:{'#16a34a' if usado else '#7c3aed'};">{badge_uso}</div>
            </div>""")

with tab_par:
    components.section_title("Parceiros cadastrados")
    if not partners:
        components.empty_state(icon="🤝", title="Sem parceiros", message="Os parceiros aparecem após concluir o cadastro via convite.")
    else:
        for p in partners:
            perfil = p.get("perfil") or p.get("role", "")
            badge  = {"⭐":"super_admin","🛡️":"admin","🎤":"b2b","👤":"b2c","👀":"demo"}
            icon   = {v: k for k, v in badge.items()}.get(perfil, "🤝")
            nome   = p.get("nome") or p.get("name", "")
            email  = p.get("email", "")
            cidade = p.get("cidade") or p.get("city", "")
            estado = p.get("estado") or p.get("state", "")
            loc    = f"{cidade}/{estado}" if cidade else estado or "—"
            st.html(f"""
            <div style="background:#f8f7fc;border:1px solid #e5e0f5;border-radius:12px;
                        padding:12px 18px;margin:6px 0;display:flex;align-items:center;gap:14px;">
                <div style="font-size:1.6rem;">{icon}</div>
                <div>
                    <div style="font-size:.88rem;font-weight:700;color:#1a0a2e;">{nome}</div>
                    <div style="font-size:.75rem;color:#6b7280;">{email} &nbsp;·&nbsp; {loc}</div>
                </div>
            </div>""")

with tab_sess:
    components.section_title("Pedidos desta sessão")
    if not session_orders:
        components.empty_state(icon="🛘", title="Nenhum pedido na sessão",
                                message="Os pedidos finalizados no checkout aparecem aqui.")
    else:
        for o in session_orders:
            totais = o.get("totais", {})
            st.html(f"""
            <div style="background:#f3f0ff;border:1px solid #c4b5fd;border-radius:12px;padding:14px 18px;margin:8px 0;">
                <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                    <span style="font-size:.85rem;font-weight:700;color:#1a0a2e;">{o.get('external_ref','—')}</span>
                    <span style="font-size:1rem;font-weight:800;color:#7c3aed;">{_brl(totais.get('total',0))}</span>
                </div>
                <div style="font-size:.75rem;color:#6b7280;">
                    {_status_badge(o.get('status',''))} &nbsp;·&nbsp;
                    ID: <code>{o.get('payment_id','—')}</code>
                </div>
            </div>""")
        m1, m2 = st.columns(2)
        m1.metric("Total da sessão", _brl(sum(Decimal(str(o.get('totais',{}).get('total',0))) for o in session_orders)))
        m2.metric("Pedidos", len(session_orders))
