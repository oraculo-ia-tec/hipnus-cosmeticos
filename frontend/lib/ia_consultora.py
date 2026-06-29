"""
ia_consultora.py — HIPNUS COSMÉTICOS
========================================
Skill: 🤖 IA Consultora
Atualização: integração da catalog_llm_skill para domínio de produtos e
preços por perfil de usuário (super_admin / admin / b2b / b2c / demo).
"""
from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from typing import Generator

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL    = "llama-3.3-70b-versatile"
MAX_TOKENS    = 1024


def _get_api_key() -> str:
    """
    Leitura da GROQ_API_KEY em ordem de prioridade:
    1. Variável de ambiente
    2. st.secrets raiz:  GROQ_API_KEY = "..."
    3. st.secrets bloco: [groq]\nGROQ_API_KEY = "..."
    4. Qualquer sub-bloco que contenha GROQ_API_KEY
    """
    val = os.environ.get("GROQ_API_KEY", "").strip()
    if val:
        return val

    try:
        import streamlit as st

        for acesso in (
            lambda: st.secrets["GROQ_API_KEY"],
            lambda: getattr(st.secrets, "GROQ_API_KEY", ""),
            lambda: dict(st.secrets).get("GROQ_API_KEY", ""),
        ):
            try:
                val = str(acesso()).strip()
                if val and val not in ("", "None"):
                    return val
            except Exception:
                pass

        try:
            val = str(st.secrets["groq"]["GROQ_API_KEY"]).strip()
            if val and val not in ("", "None"):
                return val
        except Exception:
            pass

        try:
            val = str(st.secrets.groq.GROQ_API_KEY).strip()
            if val and val not in ("", "None"):
                return val
        except Exception:
            pass

        try:
            for section_key in dict(st.secrets):
                section = st.secrets[section_key]
                try:
                    val = str(section["GROQ_API_KEY"]).strip()
                    if val and val not in ("", "None"):
                        return val
                except Exception:
                    pass
        except Exception:
            pass

    except Exception:
        pass

    return ""


def groq_status() -> dict:
    key = _get_api_key()
    return {
        "configured": bool(key),
        "model": GROQ_MODEL,
        "base_url": GROQ_BASE_URL,
    }


def _brl(v) -> str:
    try:
        s = f"{Decimal(str(v)):,.2f}"
        return f"R$ {s}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(v)


# ── Catalog Skill ─────────────────────────────────────────────────────────────

def load_catalog_skill() -> str:
    """Carrega a skill de catálogo de produtos (docs/skills/catalog_llm_skill.md)."""
    skill_path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "skills"
        / "catalog_llm_skill.md"
    )
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return ""


def build_products_context(products: list[dict], user_role: str) -> str:
    """Formata lista de produtos para injeção no contexto do LLM por perfil."""
    if not products:
        return ""
    linhas = ["\n--- PRODUTOS DO CATÁLOGO (tempo real) ---"]
    for p in products:
        if user_role in ("super_admin", "admin"):
            srp = p.get("suggested_retail_price")
            linha = (
                f"SKU {p['sku']} | {p['name']} | Linha: {p.get('line', '—')} | "
                f"Cat: {p['category']} | Piso: {_brl(p['floor_price'])} | "
                f"SRP: {_brl(srp) if srp else '—'}"
            )
        elif user_role == "b2b":
            linha = (
                f"SKU {p['sku']} | {p['name']} | Linha: {p.get('line', '—')} | "
                f"Seu custo: {_brl(p['floor_price'])}"
            )
        elif user_role == "b2c":
            srp = p.get("suggested_retail_price")
            preco = _brl(srp) if srp else "Consulte o parceiro"
            linha = f"{p['name']} | Linha: {p.get('line', '—')} | Preço: {preco}"
        else:  # demo
            linha = f"{p['name']} | Linha: {p.get('line', '—')} | Categoria: {p['category']}"
        linhas.append(linha)
    linhas.append("--- FIM DOS PRODUTOS ---")
    return "\n".join(linhas)


# ── Context Builder ────────────────────────────────────────────────────────────

def build_context(
    usuario: dict | None = None,
    cart: dict | None = None,
    historico_pedidos: list | None = None,
    smtp_ok: bool | None = None,
    products: list | None = None,
) -> str:
    linhas: list[str] = []

    user_role = "demo"
    if usuario:
        nome   = usuario.get("nome") or usuario.get("name") or "desconhecido"
        perfil = usuario.get("perfil") or usuario.get("role") or "sem perfil"
        email  = usuario.get("email", "")
        user_role = perfil
        linhas.append(f"Usuário logado: {nome} ({perfil}) — {email}")
    else:
        linhas.append("Usuário não identificado na sessão.")

    if cart:
        itens_txt = "; ".join(
            f"{v['name']} x{v['qty']} ({_brl(v['price'])})"
            for v in cart.values()
        )
        total = sum(
            Decimal(str(v["price"])) * Decimal(str(v["qty"]))
            for v in cart.values()
        )
        linhas.append(f"Carrinho atual ({len(cart)} itens, total {_brl(total)}): {itens_txt}")
    else:
        linhas.append("Carrinho atual: vazio.")

    if historico_pedidos:
        pedidos_txt = []
        for o in historico_pedidos[:5]:
            totais = o.get("totais", {})
            pedidos_txt.append(
                f"  Ref {o.get('external_ref','?')} | "
                f"ID {o.get('payment_id','?')} | "
                f"Status {o.get('status','?')} | "
                f"Total {_brl(totais.get('total', 0))}"
            )
        linhas.append(f"Pedidos desta sessão ({len(historico_pedidos)} total):")
        linhas.extend(pedidos_txt)
    else:
        linhas.append("Pedidos nesta sessão: nenhum.")

    if smtp_ok is not None:
        linhas.append(
            f"SMTP (e-mail): {'configurado e ativo' if smtp_ok else 'não configurado ou com erro'}."
        )

    # Injeta contexto de produtos filtrado por role
    if products:
        linhas.append(build_products_context(products, user_role))

    return "\n".join(linhas)


# ── System Prompt ──────────────────────────────────────────────────────────────

def _build_system_prompt(context_block: str, catalog_skill: str = "") -> str:
    skill_section = ""
    if catalog_skill:
        skill_section = f"""

--- SKILL: CATÁLOGO DE PRODUTOS HIPNUS ---
{catalog_skill}
--- FIM DA SKILL ---
"""

    return f"""\
Você é a **IA Consultora da HIPNUS COSMÉTICOS**, assistente especializada na plataforma.

Sua personalidade:
- Comunicativa, objetiva e profissional
- Domina o modelo de negócio: venda de cosméticos profissionais B2B e B2C
- Conhece o sistema de split Hipnus × parceiro (piso + margem + taxa 10 %)
- Adapta linguagem e informações de preço conforme o **perfil do usuário logado**
- Fala em português do Brasil, com linguagem clara e sem termos técnicos desnecessários
- Usa emojis com moderação para dar leveza
- Não inventa dados: se não sabe, diz que não tem essa informação no momento

Regras de preço por perfil:
- super_admin / admin: vê floor_price + suggested_retail_price + análises de margem
- b2b (salão/distribuidor): vê apenas floor_price como "seu custo de compra"
- b2c (consumidor final): vê apenas suggested_retail_price, foco em benefícios
- demo (visitante): apenas nome/linha/categoria, sem preços — incentive o cadastro

Capacidades:
- Explicar como funciona o checkout, os métodos de pagamento (PIX e boleto) e o split
- Calcular repasse ao parceiro dado um valor e floor_price (taxa 10 % da plataforma)
- Informar o que está no carrinho e o total atual
- Detalhar pedidos da sessão (status, valor, referência)
- Orientar sobre convites de parceiros e cadastro
- Explicar prazos e status do Asaas (PENDING, CONFIRMED, RECEIVED, OVERDUE)
- Recomendar produtos por linha, categoria e tipo de cliente
- Calcular margem bruta do parceiro b2b: (preço - floor_price - 10%) / preço

Limitações honestas:
- Não acessa o banco de dados diretamente (apenas contexto da sessão)
- Não consulta a API Asaas em tempo real nesta versão (usa dados da sessão)
- Não processa pagamentos nem envia e-mails
{skill_section}
--- CONTEXTO ATUAL DA SESSÃO ---
{context_block}
--- FIM DO CONTEXTO ---
"""


def chat_stream(
    messages: list[dict],
    context_block: str,
) -> Generator[str, None, None]:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY não configurada. Adicione-a nos Secrets do Streamlit."
        )

    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("Pacote 'openai' não instalado. Adicione `openai` ao requirements.txt.")

    # Carrega a skill de catálogo automaticamente
    catalog_skill = load_catalog_skill()

    client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)

    full_messages = [
        {"role": "system", "content": _build_system_prompt(context_block, catalog_skill)},
        *messages,
    ]

    try:
        stream = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=full_messages,
            max_tokens=MAX_TOKENS,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as exc:
        raise RuntimeError(f"Erro na Groq API: {exc}")
