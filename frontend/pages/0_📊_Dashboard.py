"""
0_📊_Dashboard.py — HIPNUS COSMÉTICOS
=======================================
Skill #4 — Dashboard Admin com gráficos Seaborn + bordas separadoras.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from collections import Counter

_ROOT     = Path(__file__).resolve().parents[2]
_FRONTEND = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_FRONTEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import streamlit as st
from lib import ui, components
from lib.auth import require_auth, build_sidebar
from lib.asaas_client import AsaasClient, AsaasError
from lib.invite_db import listar_invites_db
from lib.user_db import listar_parceiros

sns.set_theme(style="whitegrid", font="DejaVu Sans")
PALETTE_HIPNUS = ["#7c3aed", "#a78bfa", "#10b981", "#f59e0b", "#ef4444", "#3b82f6"]
BORDER_COLOR   = "#e5e0f5"

st.set_page_config(page_title="Dashboard · HIPNUS", page_icon="📊", layout="wide")
ui.inject_theme()
usuario = require_auth(perfis_permitidos=["super_admin", "admin"])
build_sidebar()

components.page_header(
    title="Dashboard Admin",
    subtitle="Visão consolidada de cobranças, gráficos Seaborn, convites e parceiros da plataforma.",
    kicker="📊 Painel Operacional",
)

st.html("""
<style>
  .seaborn-card-title {
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem; font-weight: 700;
    letter-spacing: 1.6px; text-transform: uppercase;
    color: rgba(124,58,237,0.55); margin-bottom: 12px;
  }
  .section-separator {
    border: none; border-top: 2px solid #e5e0f5;
    margin: 28px 0 20px; border-radius: 2px;
  }
  .grafico-wrapper {
    border: 2px solid #e5e0f5; border-radius: 14px;
    padding: 16px; background: #ffffff; margin-bottom: 8px;
  }
</style>
""")


def _brl(v) -> str:
    try:
        val = Decimal(str(v))
    except Exception:
        val = Decimal("0")
    s = f"{val:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

def _status_badge(status: str) -> str:
    _map = {
        "RECEIVED":  "Recebido",  "CONFIRMED": "Confirmado",
        "PENDING":   "Pendente",  "OVERDUE":   "Vencido",
        "REFUNDED":  "Estornado", "CANCELLED": "Cancelado",
    }
    return _map.get(status, status)

def _method_badge(bt: str) -> str:
    return {"PIX": "PIX", "BOLETO": "Boleto", "CREDIT_CARD": "Cartao"}.get(bt, bt)

def _status_color(status: str) -> str:
    return {
        "RECEIVED": "#10b981", "CONFIRMED": "#10b981",
        "PENDING":  "#f59e0b", "OVERDUE":   "#ef4444",
        "REFUNDED": "#3b82f6", "CANCELLED": "#9ca3af",
    }.get(status, "#7c3aed")


def _resolve_api_key() -> tuple[str, str]:
    import os
    try:
        v = st.secrets.get("ASAAS_API_KEY", "")
        if v and str(v).strip():
            return str(v).strip(), "st.secrets (raiz)"
    except Exception:
        pass
    try:
        v = st.secrets.get("asaas", {}).get("ASAAS_API_KEY", "")
        if v and str(v).strip():
            return str(v).strip(), "st.secrets [asaas]"
    except Exception:
        pass
    try:
        v = st.secrets.get("hipnus", {}).get("ASAAS_API_KEY", "")
        if v and str(v).strip():
            return str(v).strip(), "st.secrets [hipnus]"
    except Exception:
        pass
    v = os.environ.get("ASAAS_API_KEY", "")
    if v and v.strip():
        return v.strip(), "os.environ"
    try:
        keys_found = list(st.secrets.keys())
    except Exception:
        keys_found = []
    motivo = (
        "ASAAS_API_KEY nao encontrada. "
        "Chaves visiveis em st.secrets: " + str(keys_found) + ". "
        "Dica: Settings -> Secrets -> ASAAS_API_KEY = seu_token"
    )
    return "", motivo


def _load_asaas_payments(days: int = 30) -> tuple[list[dict], str | None]:
    api_key, fonte_ou_erro = _resolve_api_key()
    if not api_key:
        return [], fonte_ou_erro
    try:
        import os
        base_url = (
            st.secrets.get("ASAAS_BASE_URL", "")
            or os.environ.get("ASAAS_BASE_URL", "https://api-sandbox.asaas.com/v3")
        )
        client = AsaasClient(api_key=api_key, base_url=base_url)
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


st.html("""
<div style="background:linear-gradient(135deg,rgba(15,10,30,.85),rgba(30,15,55,.75));
  border:2px solid rgba(185,131,255,.30);border-radius:16px;
  padding:18px 24px 14px;margin-bottom:4px;backdrop-filter:blur(8px);">
  <div style="font-family:'Inter',sans-serif;font-size:.65rem;font-weight:700;
    letter-spacing:1.8px;text-transform:uppercase;color:rgba(185,131,255,.55);
    margin-bottom:10px;">Filtro de periodo</div>
</div>
""")

_f1, _f2 = st.columns([2, 1])
with _f1:
    dias = st.selectbox("Cobranças dos ultimos:", options=[7, 15, 30, 60, 90], index=2,
                        format_func=lambda d: f"{d} dias", key="dash_dias")
with _f2:
    st.write("")
    atualizar = st.button("Atualizar dados", use_container_width=True, key="_btn_atualizar")

st.html("<div style='margin-bottom:20px;'></div>")

cache_key = f"_dash_payments_{dias}"
if atualizar:
    for k in [cache_key, "_dash_asaas_error"]:
        st.session_state.pop(k, None)

if cache_key not in st.session_state:
    with st.spinner("Buscando cobranças na API Asaas..."):
        payments, asaas_error = _load_asaas_payments(dias)
    st.session_state[cache_key]          = payments
    st.session_state["_dash_asaas_error"] = asaas_error
else:
    payments    = st.session_state[cache_key]
    asaas_error = st.session_state.get("_dash_asaas_error")

invites        = _load_invites()
partners       = _load_partners()
session_orders = st.session_state.get("historico_pedidos", [])

if asaas_error:
    is_key_missing = "nao encontrada" in asaas_error or "nao configurada" in asaas_error
    if is_key_missing:
        with st.expander("API Asaas: ASAAS_API_KEY nao encontrada", expanded=True):
            st.markdown("""
**Como corrigir no Streamlit Cloud:**
1. Acesse o app -> **Manage app** (canto inferior direito)
2. Va em **Settings -> Secrets**
3. Confirme que o secret esta exatamente assim:
```toml
ASSAS_API_KEY = "$aact_SUA_CHAVE_AQUI"
```
            """)
            st.caption("Detalhes: " + str(asaas_error))
    else:
        st.warning("Asaas API retornou erro: " + str(asaas_error))


if payments:
    total_recebido = sum(Decimal(str(p.get("value",0))) for p in payments
                         if p.get("status") in ("RECEIVED","CONFIRMED"))
    total_pendente = sum(Decimal(str(p.get("value",0))) for p in payments
                         if p.get("status") == "PENDING")
    total_vencido  = sum(Decimal(str(p.get("value",0))) for p in payments
                         if p.get("status") == "OVERDUE")
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
k1.metric("Recebido",        _brl(total_recebido), str(n_recebido) + " cobranças")
k2.metric("Pendente",        _brl(total_pendente), str(n_pendente) + " cobranças")
k3.metric("Vencido",         _brl(total_vencido),  str(n_vencido) + " cobranças")
k4.metric("Total cobranças", len(payments) or len(session_orders))

st.html("<hr class='section-separator'>")

components.section_title("Plataforma")
p1, p2, p3, p4 = st.columns(4)
p1.metric("Parceiros",       n_parceiros)
p2.metric("Convites ativos", n_invites_ativos)
p3.metric("Convites usados", n_invites_usado)
p4.metric("Convites totais", n_invites_total)

st.html("<hr class='section-separator'>")


components.section_title("Graficos — Analise Visual (Seaborn)")

_source = payments if payments else []
if not _source and session_orders:
    _source = [
        {"status": o.get("status", "PENDING"), "billingType": "PIX",
         "value": float(o.get("totais",{}).get("total", 0)),
         "dateCreated": str(date.today())}
        for o in session_orders
    ]

df_pay = pd.DataFrame(_source) if _source else pd.DataFrame(
    columns=["status","billingType","value","dateCreated"])

if not df_pay.empty:
    df_pay["value"]       = pd.to_numeric(df_pay["value"], errors="coerce").fillna(0)
    df_pay["dateCreated"] = pd.to_datetime(df_pay["dateCreated"], errors="coerce")
    _status_map = {
        "RECEIVED":"Recebido","CONFIRMED":"Confirmado","PENDING":"Pendente",
        "OVERDUE":"Vencido","REFUNDED":"Estornado","CANCELLED":"Cancelado"
    }
    _method_map = {"PIX":"PIX","BOLETO":"Boleto","CREDIT_CARD":"Cartao"}
    df_pay["status_pt"] = df_pay["status"].map(_status_map).fillna(df_pay["status"])
    df_pay["metodo_pt"] = df_pay["billingType"].map(_method_map).fillna(
        df_pay["billingType"].fillna("Outro"))

has_data = not df_pay.empty

g_col1, g_col2 = st.columns(2)

with g_col1:
    st.html("<div class='grafico-wrapper'>")
    st.html("<div class='seaborn-card-title'>Valor por Status</div>")
    if has_data:
        df_s = df_pay.groupby("status_pt")["value"].sum().reset_index()
        df_s.columns = ["Status", "Valor"]
        df_s = df_s.sort_values("Valor", ascending=False)
        cores = {"Recebido":"#10b981","Confirmado":"#10b981","Pendente":"#f59e0b",
                 "Vencido":"#ef4444","Estornado":"#3b82f6","Cancelado":"#9ca3af"}
        fig, ax = plt.subplots(figsize=(6, 3.8))
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#f8f7fc")
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER_COLOR); spine.set_linewidth(1.5)
        bars = ax.barh(df_s["Status"], df_s["Valor"],
                       color=[cores.get(s,"#7c3aed") for s in df_s["Status"]],
                       edgecolor=BORDER_COLOR, linewidth=1.2)
        for bar in bars:
            w = bar.get_width()
            label_val = "R$ " + f"{w:,.0f}".replace(",",".")
            ax.text(w*1.02, bar.get_y()+bar.get_height()/2,
                    label_val, va="center", ha="left",
                    fontsize=8, color="#374151", fontweight="bold")
        ax.set_xlabel("Valor Total (R$)", fontsize=9, color="#6b7280")
        ax.set_title("Ultimos " + str(dias) + " dias", fontsize=10, color="#374151", pad=8)
        ax.xaxis.grid(True, color=BORDER_COLOR, linestyle="--", alpha=0.7)
        ax.yaxis.grid(False)
        ax.tick_params(colors="#6b7280", labelsize=9)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    else:
        st.info("Sem dados de pagamentos.")
    st.html("</div>")

with g_col2:
    st.html("<div class='grafico-wrapper'>")
    st.html("<div class='seaborn-card-title'>Metodo de Pagamento</div>")
    if has_data:
        df_m = df_pay["metodo_pt"].value_counts().reset_index()
        df_m.columns = ["Metodo", "Qtd"]
        cores_m = {"PIX":"#7c3aed","Boleto":"#f59e0b","Cartao":"#3b82f6","Outro":"#9ca3af"}
        fig2, ax2 = plt.subplots(figsize=(5, 3.8))
        fig2.patch.set_facecolor("#ffffff")
        wedges, texts, autotexts = ax2.pie(
            df_m["Qtd"], labels=df_m["Metodo"], autopct="%1.0f%%", startangle=90,
            colors=[cores_m.get(m,"#a78bfa") for m in df_m["Metodo"]],
            pctdistance=0.78, wedgeprops=dict(edgecolor=BORDER_COLOR, linewidth=2))
        for t in autotexts:
            t.set_fontsize(9); t.set_fontweight("bold"); t.set_color("#1a0a2e")
        for t in texts:
            t.set_fontsize(9); t.set_color("#374151")
        total_cob = int(df_m["Qtd"].sum())
        ax2.set_title("Total: " + str(total_cob) + " cobranças", fontsize=10, color="#374151", pad=8)
        plt.tight_layout()
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
    else:
        st.info("Sem dados de pagamentos.")
    st.html("</div>")

st.html("<hr class='section-separator'>")

g_col3, g_col4 = st.columns([3, 2])

with g_col3:
    st.html("<div class='grafico-wrapper'>")
    st.html("<div class='seaborn-card-title'>Tendencia diaria (R$)</div>")
    if has_data and not df_pay["dateCreated"].isna().all():
        df_line = df_pay[df_pay["status"].isin(["RECEIVED","CONFIRMED","PENDING"])].copy()
        df_line["data_dia"] = df_line["dateCreated"].dt.date
        df_daily = df_line.groupby(["data_dia","status_pt"])["value"].sum().reset_index()
        df_daily.columns = ["Data","Status","Valor"]
        fig3, ax3 = plt.subplots(figsize=(7, 3.8))
        fig3.patch.set_facecolor("#ffffff")
        ax3.set_facecolor("#f8f7fc")
        for spine in ax3.spines.values():
            spine.set_edgecolor(BORDER_COLOR); spine.set_linewidth(1.5)
        paleta_l = {"Recebido":"#10b981","Confirmado":"#10b981","Pendente":"#f59e0b"}
        sns.lineplot(data=df_daily, x="Data", y="Valor", hue="Status",
                     palette=paleta_l, ax=ax3, linewidth=2.2, markers=True, dashes=False)
        rec = df_daily[df_daily["Status"]=="Recebido"]
        if not rec.empty:
            ax3.fill_between(rec["Data"], rec["Valor"], alpha=0.15, color="#10b981")
        ax3.set_xlabel("Data", fontsize=9, color="#6b7280")
        ax3.set_ylabel("Valor (R$)", fontsize=9, color="#6b7280")
        ax3.tick_params(colors="#6b7280", labelsize=8, rotation=30)
        ax3.yaxis.grid(True, color=BORDER_COLOR, linestyle="--", alpha=0.7)
        ax3.xaxis.grid(False)
        ax3.legend(fontsize=8, framealpha=0.85, edgecolor=BORDER_COLOR, facecolor="#ffffff")
        plt.tight_layout()
        st.pyplot(fig3, use_container_width=True)
        plt.close(fig3)
    else:
        st.info("Sem dados temporais suficientes.")
    st.html("</div>")

with g_col4:
    st.html("<div class='grafico-wrapper'>")
    st.html("<div class='seaborn-card-title'>Quantidade por Status</div>")
    if has_data:
        df_cnt = df_pay["status_pt"].value_counts().reset_index()
        df_cnt.columns = ["Status","Qtd"]
        cores_c = {"Recebido":"#10b981","Confirmado":"#10b981","Pendente":"#f59e0b",
                   "Vencido":"#ef4444","Estornado":"#3b82f6","Cancelado":"#9ca3af"}
        fig4, ax4 = plt.subplots(figsize=(4.5, 3.8))
        fig4.patch.set_facecolor("#ffffff")
        ax4.set_facecolor("#f8f7fc")
        for spine in ax4.spines.values():
            spine.set_edgecolor(BORDER_COLOR); spine.set_linewidth(1.5)
        sns.barplot(data=df_cnt, y="Status", x="Qtd",
                    palette=[cores_c.get(s,"#7c3aed") for s in df_cnt["Status"]],
                    ax=ax4, edgecolor=BORDER_COLOR, linewidth=1.2)
        for container in ax4.containers:
            ax4.bar_label(container, fmt="%d", padding=3,
                          fontsize=9, color="#374151", fontweight="bold")
        ax4.set_xlabel("Quantidade", fontsize=9, color="#6b7280")
        ax4.set_ylabel("", fontsize=9)
        ax4.xaxis.grid(True, color=BORDER_COLOR, linestyle="--", alpha=0.6)
        ax4.yaxis.grid(False)
        ax4.tick_params(colors="#6b7280", labelsize=9)
        plt.tight_layout()
        st.pyplot(fig4, use_container_width=True)
        plt.close(fig4)
    else:
        st.info("Sem dados.")
    st.html("</div>")

st.html("<hr class='section-separator'>")

g_col5, g_col6 = st.columns(2)

with g_col5:
    st.html("<div class='grafico-wrapper'>")
    st.html("<div class='seaborn-card-title'>Status dos Convites</div>")
    df_inv_chart = pd.DataFrame({
        "Status": ["Ativos", "Usados", "Total"],
        "Qtd":    [n_invites_ativos, n_invites_usado, n_invites_total]
    })
    fig5, ax5 = plt.subplots(figsize=(5, 3.2))
    fig5.patch.set_facecolor("#ffffff")
    ax5.set_facecolor("#f8f7fc")
    for spine in ax5.spines.values():
        spine.set_edgecolor(BORDER_COLOR); spine.set_linewidth(1.5)
    bars5 = ax5.bar(df_inv_chart["Status"], df_inv_chart["Qtd"],
                    color=["#f59e0b","#10b981","#7c3aed"],
                    edgecolor=BORDER_COLOR, linewidth=1.5, width=0.55)
    ax5.bar_label(bars5, fmt="%d", padding=4, fontsize=11, color="#374151", fontweight="bold")
    ax5.set_ylabel("Quantidade", fontsize=9, color="#6b7280")
    ax5.yaxis.grid(True, color=BORDER_COLOR, linestyle="--", alpha=0.6)
    ax5.xaxis.grid(False)
    ax5.tick_params(colors="#6b7280", labelsize=10)
    max_val = df_inv_chart["Qtd"].max()
    ax5.set_ylim(0, max(max_val * 1.3, 5))
    plt.tight_layout()
    st.pyplot(fig5, use_container_width=True)
    plt.close(fig5)
    st.html("</div>")

with g_col6:
    st.html("<div class='grafico-wrapper'>")
    st.html("<div class='seaborn-card-title'>Parceiros por Perfil</div>")
    if partners:
        perfis = [p.get("perfil") or p.get("role","outro") for p in partners]
        df_perf = pd.DataFrame(Counter(perfis).items(), columns=["Perfil","Qtd"])
        labels_pt = {"b2b":"Profissional","b2c":"Cliente","admin":"Admin",
                     "super_admin":"Super Admin","demo":"Demo"}
        df_perf["Perfil"] = df_perf["Perfil"].map(lambda x: labels_pt.get(x, x))
        df_perf = df_perf.sort_values("Qtd", ascending=False)
        fig6, ax6 = plt.subplots(figsize=(5, 3.2))
        fig6.patch.set_facecolor("#ffffff")
        ax6.set_facecolor("#f8f7fc")
        for spine in ax6.spines.values():
            spine.set_edgecolor(BORDER_COLOR); spine.set_linewidth(1.5)
        bars6 = ax6.bar(df_perf["Perfil"], df_perf["Qtd"],
                        color=sns.color_palette(PALETTE_HIPNUS, n_colors=len(df_perf)),
                        edgecolor=BORDER_COLOR, linewidth=1.5, width=0.55)
        ax6.bar_label(bars6, fmt="%d", padding=4, fontsize=11, color="#374151", fontweight="bold")
        ax6.set_ylabel("Quantidade", fontsize=9, color="#6b7280")
        ax6.yaxis.grid(True, color=BORDER_COLOR, linestyle="--", alpha=0.6)
        ax6.xaxis.grid(False)
        ax6.tick_params(colors="#6b7280", labelsize=9, rotation=15)
        max_perf = df_perf["Qtd"].max()
        ax6.set_ylim(0, max(max_perf * 1.3, 5))
        plt.tight_layout()
        st.pyplot(fig6, use_container_width=True)
        plt.close(fig6)
    else:
        st.info("Nenhum parceiro cadastrado ainda.")
    st.html("</div>")

st.html("<hr class='section-separator'>")


components.section_title("Detalhes Operacionais")
tab_cob, tab_inv, tab_par, tab_sess = st.tabs(
    ["Cobranças", "Convites", "Parceiros", "Sessao"])

with tab_cob:
    components.section_title("Cobranças — ultimos " + str(dias) + " dias")
    if not payments:
        if session_orders:
            st.info("API Asaas sem dados. Exibindo pedidos da sessao atual.")
            for o in session_orders:
                totais = o.get("totais", {})
                ref_val = str(o.get("external_ref", "--"))
                status_val = _status_badge(str(o.get("status", "")))
                brl_val = _brl(totais.get("total", 0))
                st.html(
                    '<div style="background:#f8f7fc;border:2px solid #e5e0f5;border-radius:12px;'
                    'padding:14px 18px;margin:8px 0;display:flex;justify-content:space-between;align-items:center;">'
                    '<div>'
                    '<div style="font-size:.85rem;font-weight:700;color:#1a0a2e;">' + ref_val + '</div>'
                    '<div style="font-size:.75rem;color:#6b7280;margin-top:2px;">' + status_val + '</div>'
                    '</div>'
                    '<div style="font-size:1rem;font-weight:800;color:#7c3aed;">' + brl_val + '</div>'
                    '</div>'
                )
        else:
            components.empty_state(icon="Cobranças", title="Sem cobranças",
                                    message="Configure ASAAS_API_KEY para ver dados em tempo real.")
    else:
        for p in payments:
            ref  = str(p.get("externalReference") or p.get("description", "—"))
            sc   = _status_color(str(p.get("status","")))
            link = str(p.get("invoiceUrl") or p.get("bankSlipUrl") or "")
            status_txt  = _status_badge(str(p.get("status","")))
            method_txt  = _method_badge(str(p.get("billingType","")))
            date_txt    = str(p.get("dateCreated") or "")[:10]
            brl_val     = _brl(p.get("value", 0))
            link_html   = ('<a href="' + link + '" target="_blank" style="font-size:.72rem;color:#7c3aed;">Ver cobrança</a>') if link else ""
            st.html(
                '<div style="background:#f8f7fc;border:2px solid #e5e0f5;'
                'border-radius:12px;border-left:5px solid ' + sc + ';'
                'padding:14px 18px;margin:8px 0;'
                'display:flex;justify-content:space-between;align-items:center;">'
                '<div>'
                '<div style="font-size:.85rem;font-weight:700;color:#1a0a2e;">' + ref + '</div>'
                '<div style="font-size:.75rem;color:#6b7280;margin-top:2px;">'
                + status_txt + ' &nbsp;&middot;&nbsp; ' + method_txt + ' &nbsp;&middot;&nbsp; ' + date_txt +
                '</div></div>'
                '<div style="text-align:right;">'
                '<div style="font-size:1rem;font-weight:800;color:#7c3aed;">' + brl_val + '</div>'
                + link_html +
                '</div></div>'
            )

with tab_inv:
    components.section_title("Convites de parceiros")
    if not invites:
        components.empty_state(icon="Convites", title="Sem convites",
                                message="Crie convites em Convites de Parceiros.")
    else:
        _role_lbl = {"b2b": "Profissional", "b2c": "Cliente", "admin": "Admin"}
        for inv in invites:
            usado     = inv.get("used", False)
            role_lbl  = _role_lbl.get(str(inv.get("role","")), str(inv.get("role","")))
            bg_color  = "#f0fdf4" if usado else "#faf7ff"
            bd_color  = "#86efac" if usado else "#e9d5ff"
            st_color  = "#16a34a" if usado else "#7c3aed"
            st_label  = "Usado" if usado else "Pendente"
            expires   = str(inv.get("expires_at") or "")[:10]
            email_inv = str(inv.get("email", ""))
            st.html(
                '<div style="background:' + bg_color + ';border:2px solid ' + bd_color + ';'
                'border-radius:12px;padding:12px 18px;margin:6px 0;display:flex;justify-content:space-between;">'
                '<div>'
                '<div style="font-size:.85rem;font-weight:700;color:#1a0a2e;">' + email_inv + '</div>'
                '<div style="font-size:.75rem;color:#6b7280;margin-top:2px;">' + role_lbl + ' &nbsp;&middot;&nbsp; Expira: ' + expires + '</div>'
                '</div>'
                '<div style="font-size:.82rem;font-weight:700;color:' + st_color + ';">' + st_label + '</div>'
                '</div>'
            )

with tab_par:
    components.section_title("Parceiros cadastrados")
    if not partners:
        components.empty_state(icon="Parceiros", title="Sem parceiros",
                                message="Os parceiros aparecem apos cadastro via convite.")
    else:
        icons_map = {"super_admin":"Estrela","admin":"Admin","b2b":"Pro","b2c":"Cliente","demo":"Demo"}
        for p in partners:
            perfil = str(p.get("perfil") or p.get("role", ""))
            icon   = icons_map.get(perfil, "")
            cidade = str(p.get("cidade") or p.get("city", ""))
            estado = str(p.get("estado") or p.get("state", ""))
            loc    = (cidade + "/" + estado) if cidade else (estado or "—")
            nome_p  = str(p.get("nome") or p.get("name", ""))
            email_p = str(p.get("email", ""))
            st.html(
                '<div style="background:#f8f7fc;border:2px solid #e5e0f5;'
                'border-radius:12px;padding:12px 18px;margin:6px 0;display:flex;align-items:center;gap:14px;">'
                '<div style="font-size:1rem;color:#7c3aed;font-weight:700;">[' + icon + ']</div>'
                '<div>'
                '<div style="font-size:.88rem;font-weight:700;color:#1a0a2e;">' + nome_p + '</div>'
                '<div style="font-size:.75rem;color:#6b7280;">' + email_p + ' &nbsp;&middot;&nbsp; ' + loc + '</div>'
                '</div></div>'
            )

with tab_sess:
    components.section_title("Pedidos desta sessao")
    if not session_orders:
        components.empty_state(icon="Sessao", title="Nenhum pedido na sessao",
                                message="Os pedidos finalizados no checkout aparecem aqui.")
    else:
        for o in session_orders:
            totais    = o.get("totais", {})
            ext_ref   = str(o.get("external_ref", "—"))
            brl_val   = _brl(totais.get("total", 0))
            status_lbl = _status_badge(str(o.get("status", "")))
            pay_id    = str(o.get("payment_id", "—"))
            st.html(
                '<div style="background:#f3f0ff;border:2px solid #c4b5fd;'
                'border-radius:12px;padding:14px 18px;margin:8px 0;">'
                '<div style="display:flex;justify-content:space-between;margin-bottom:6px;">'
                '<span style="font-size:.85rem;font-weight:700;color:#1a0a2e;">' + ext_ref + '</span>'
                '<span style="font-size:1rem;font-weight:800;color:#7c3aed;">' + brl_val + '</span>'
                '</div>'
                '<div style="font-size:.75rem;color:#6b7280;">'
                + status_lbl + ' &nbsp;&middot;&nbsp; ID: <code>' + pay_id + '</code>'
                '</div></div>'
            )
        m1, m2 = st.columns(2)
        total_sess = sum(Decimal(str(o.get("totais",{}).get("total",0))) for o in session_orders)
        m1.metric("Total da sessao", _brl(total_sess))
        m2.metric("Pedidos",         len(session_orders))
