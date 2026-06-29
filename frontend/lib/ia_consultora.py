"""
ia_consultora.py — HIPNUS COSMÉTICOS
========================================
Fix 2026-06-29 v3:
  - load_catalog_skill() reescrito sem regex com emoji (falhava silenciosamente
    no Linux do Streamlit Cloud por encoding).
  - Fallback de portfólio estático injetado quando o banco estiver vazio,
    garantindo que a IA sempre saiba quais produtos existem.
  - MAX_TOKENS aumentado para 800 para respostas mais completas sobre produtos.
"""
from __future__ import annotations

import os
import re
from decimal import Decimal
from pathlib import Path
from typing import Generator

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL    = "llama-3.3-70b-versatile"
MAX_TOKENS    = 800


def _get_api_key() -> str:
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
        for key_path in (
            lambda: st.secrets["groq"]["GROQ_API_KEY"],
            lambda: st.secrets.groq.GROQ_API_KEY,
        ):
            try:
                val = str(key_path()).strip()
                if val and val not in ("", "None"):
                    return val
            except Exception:
                pass
        try:
            for section_key in dict(st.secrets):
                try:
                    val = str(st.secrets[section_key]["GROQ_API_KEY"]).strip()
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
    return {"configured": bool(key), "model": GROQ_MODEL, "base_url": GROQ_BASE_URL}


def _brl(v) -> str:
    try:
        s = f"{Decimal(str(v)):,.2f}"
        return f"R$ {s}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(v)


# ── Portfólio estático de fallback (usado quando o banco está vazio) ────────
# Garante que a IA SEMPRE saiba quais produtos e linhas existem,
# mesmo no Streamlit Cloud onde o SQLite é efêmero entre deploys.

_PORTFOLIO_FALLBACK = """
--- PORTFÓLIO HIPNUS 2026 (referência estática — use quando o banco estiver vazio) ---

LINHAS E PRODUTOS DISPONÍVEIS:

Linha Turmalina:
- Shampoo Turmalina (Home Care) — hidratação, anti-frizz, brilho
- Condicionador Turmalina (Home Care) — suavidade e desembaraço
- Máscara Turmalina (Home Care / Máscara Avulsa) — reconstrução intensa
- Tratamento Turmalina (Tratamento Obrigatorio) — protocolo de salão

Linha Ouro:
- Shampoo Ouro (Home Care) — nutrição com ouro coloidal
- Condicionador Ouro (Home Care) — brilho extremo
- Máscara Ouro (Máscara Avulsa) — nutrição profunda premium
- Óleo Ouro (Home Care) — finalizador com partículas de ouro

Linha Teia de Aranha:
- Shampoo Teia de Aranha (Home Care) — reconstrução com proteína de seda
- Máscara Teia de Aranha (Máscara Avulsa) — restauração de fios muito danificados
- Tratamento Teia de Aranha (Tratamento Obrigatorio) — protocolo profissional

Linha Manga Rosa (vegana):
- Shampoo Manga Rosa (Home Care) — hidratação vegana profunda
- Condicionador Manga Rosa (Home Care) — maciez e leveza
- Máscara Manga Rosa (Máscara Avulsa) — hidratação com manteiga de manga

Linha Carbono Smooth Pro:
- Progressiva Carbono Smooth Pro (Quimicas) — alisamento com carvão ativado
- Shampoo Carbono (Home Care) — manutenção pós-progressiva

Linha Coffee Milk:
- Shampoo Coffee Milk (Home Care) — estimula crescimento com extrato de café
- Máscara Coffee Milk (Máscara Avulsa) — proteínas do leite + cafeína

Linha Masculina (Barber):
- Shampoo Masculino (Linha Masculina) — controle de oleosidade
- Pomada Modeladora (Linha Masculina) — fixação e brilho
- Condicionador Masculino (Linha Masculina) — hidratação para fio masculino

Linha Matizadora:
- Shampoo Matizador Violeta (Matizadores) — neutraliza tons amarelados
- Máscara Matizadora (Mascaras Matizadoras) — pigmentação neutralizadora
- Condicionador Matizador (Matizadores) — manutenção da cor

Linha Silver (loiros e grisalhos):
- Shampoo Silver (Matizadores) — brilho platinado para cabelos brancos/loiros
- Máscara Silver (Mascaras Matizadoras) — tonalização e hidratação

Encapsulados:
- Sérum Encapsulado Reparador (Encapsulados) — ativos de liberação prolongada
- Ampola Encapsulada (Encapsulados) — tratamento intensivo pré-lavagem

Kits disponíveis (is_kit=True):
- Kit Turmalina Completo (Shampoo + Condicionador + Máscara)
- Kit Ouro Premium (Shampoo + Condicionador + Óleo)
- Kit Manga Rosa Vegano (Shampoo + Condicionador + Máscara)
- Kit Barber Completo (Shampoo + Condicionador + Pomada)
- Kit Matizador (Shampoo + Máscara Matizadora)

OBSERVAÇÃO: Preços reais são definidos por cada parceiro acima do piso.
Se o usuário pedir preço específico e não houver dados do banco, diga:
"Os preços variam por parceiro. Consulte seu parceiro Hipnus local ou
cadastre-se para ver as condições."
--- FIM DO PORTFÓLIO ---
"""


# ── Catalog Skill (docs/skills/catalog_llm_skill.md) ────────────────────────

def load_catalog_skill() -> str:
    """
    Carrega a skill de catálogo removendo apenas blocos de código Python
    e seções técnicas de instrução (não-LLM).
    Usa split por texto puro — sem regex com emoji que falham no Linux.
    """
    skill_path = (
        Path(__file__).resolve().parents[2]
        / "docs" / "skills" / "catalog_llm_skill.md"
    )
    if not skill_path.exists():
        return ""

    content = skill_path.read_text(encoding="utf-8")

    # Remove blocos de código Python (não úteis para o LLM)
    content = re.sub(r"```python.*?```", "", content, flags=re.DOTALL)
    content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)

    # Remove seções técnicas de instrução ao desenvolvedor
    # (corta no primeiro marcador encontrado, sem depender de emoji)
    cortes = [
        "## Como usar esta skill",
        "## Contexto Din",          # "## Contexto Dinâmico"
        "## Checklist",
        "## Como usar",
    ]
    for marcador in cortes:
        idx = content.find(marcador)
        if idx != -1:
            content = content[:idx]
            break

    # Limpa linhas em branco excessivas
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


# ── Produtos do banco ────────────────────────────────────────────────────────

def build_products_context(products: list[dict], user_role: str) -> str:
    """Formata lista de produtos para injeção no contexto.
    Se o banco estiver vazio, usa o portfólio estático como fallback.
    """
    if not products:
        # Banco vazio ou inacessível — injeta portfólio estático
        return _PORTFOLIO_FALLBACK

    linhas = ["\n--- PRODUTOS DO CATÁLOGO (dados reais do banco) ---"]
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


# ── Context Builder ──────────────────────────────────────────────────────────

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

    linhas.append(build_products_context(products or [], user_role))
    return "\n".join(linhas)


# ── Knowledge Base da Empresa ────────────────────────────────────────────────

_HIPNUS_KB = """
--- KNOWLEDGE BASE: HIPNUS COSMÉTICOS ---

SOBRE A EMPRESA:
- Hipnus Cosméticos é uma marca profissional brasileira de cosméticos capilares.
- Distribui via rede de parceiros: profissionais, salões, distribuidores e revendedores.
- A Hipnus recebe 10% de cada venda online como taxa da plataforma (split Asaas).
- O parceiro fica com: preço_venda - floor_price - (preço_venda * 0.10).
- Não existem lojas físicas próprias da Hipnus — tudo via parceiros.

FORMAS DE PAGAMENTO:
- PIX (confirmação instantânea), Boleto bancário, Cartão de crédito — todos via Asaas.

MODELO DE PARCERIA:
- Parceiros são convidados por link exclusivo ou pelo admin.
- Após cadastro, o parceiro define preços acima do piso (floor_price).
- Venda física pode ser registrada manualmente no sistema.
--- FIM DO KNOWLEDGE BASE ---
"""


# ── System Prompt ────────────────────────────────────────────────────────────

def _build_system_prompt(context_block: str, catalog_skill: str = "") -> str:
    skill_section = ""
    if catalog_skill:
        skill_section = f"""

--- SKILL: CATÁLOGO DE PRODUTOS HIPNUS ---
{catalog_skill}
--- FIM DA SKILL ---
"""

    return f"""\
Você é a **Chiara**, IA Consultora da **HIPNUS COSMÉTICOS**.
Conhece profundamente as linhas, produtos, modelo de negócio e como ajudar
parceiros e consumidores. Seja direta, objetiva, calorosa e concisa.

REGRAS DE RESPOSTA (obrigatórias):
1. Máximo 3 parágrafos curtos. Use listas bullet ao listar itens.
2. NUNCA invente preços. Só cite valores presentes no contexto da sessão.
   Se não tiver preço real: "Os preços variam por parceiro. Cadastre-se para
   ver condições exclusivas ou consulte seu parceiro Hipnus."
3. NUNCA mostre floor_price para b2c ou demo.
4. Sobre MÁSCARAS e PRODUTOS: use sempre o portfólio abaixo — NUNCA diga
   "não encontrei" quando há produtos listados no portfólio ou no catálogo.
5. Responda SEMPRE em português do Brasil. Máximo 2 emojis por resposta.

PERFIS E VISÃO DE PREÇOS:
- super_admin/admin: vê Piso + SRP + margem
- b2b: vê apenas "seu custo" (floor_price) + cálculo de margem
- b2c: vê apenas SRP. Foco em benefícios.
- demo: sem preços. Incentive o cadastro.

CAPACIDADES:
- Informar sobre linhas, produtos, benefícios, diferenciais
- Calcular repasse: repasse = preço_venda - floor_price - (preço_venda * 0.10)
- Carrinho e pedidos da sessão atual
- Recomendar produtos por tipo de cabelo ou necessidade
- Convites, cadastro de parceiros, modelo de negócio
{_HIPNUS_KB}
{skill_section}
--- CONTEXTO ATUAL DA SESSÃO ---
{context_block}
--- FIM DO CONTEXTO ---
"""


# ── Chat Stream ──────────────────────────────────────────────────────────────

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
