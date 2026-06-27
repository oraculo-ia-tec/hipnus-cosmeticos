"""
ia_consultora.py — HIPNUS COSMÉTICOS
========================================
Skill: 🤖 IA Consultora
"""
from __future__ import annotations

import os
from decimal import Decimal
from typing import Generator

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL    = "llama-3.3-70b-versatile"
MAX_TOKENS    = 1024


def _get_api_key() -> str:
    """
    Leitura da GROQ_API_KEY em ordem de prioridade:
    1. Variável de ambiente (injetada pelo proxy antes do exec)
    2. st.secrets via subscript
    3. st.secrets via atributo
    4. st.secrets via dict()
    """
    # 1. Ambiente (mais confiável no contexto exec)
    val = os.environ.get("GROQ_API_KEY", "").strip()
    if val:
        return val

    # 2–4. Streamlit Secrets como fallback
    try:
        import streamlit as st
        try:
            val = str(st.secrets["GROQ_API_KEY"]).strip()
            if val:
                return val
        except Exception:
            pass
        try:
            val = str(getattr(st.secrets, "GROQ_API_KEY", "")).strip()
            if val:
                return val
        except Exception:
            pass
        try:
            val = str(dict(st.secrets).get("GROQ_API_KEY", "")).strip()
            if val:
                return val
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


def build_context(
    usuario: dict | None = None,
    cart: dict | None = None,
    historico_pedidos: list | None = None,
    smtp_ok: bool | None = None,
) -> str:
    linhas: list[str] = []

    if usuario:
        nome   = usuario.get("nome") or usuario.get("name") or "desconhecido"
        perfil = usuario.get("perfil") or usuario.get("role") or "sem perfil"
        email  = usuario.get("email", "")
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
        linhas.append(f"SMTP (e-mail): {'configurado e ativo' if smtp_ok else 'não configurado ou com erro'}.")

    return "\n".join(linhas)


def _build_system_prompt(context_block: str) -> str:
    return f"""\
Você é a **IA Consultora da HIPNUS COSMÉTICOS**, assistente especializada na plataforma.

Sua personalidade:
- Comunicativa, objetiva e profissional
- Domina o modelo de negócio: venda de cosméticos profissionais B2B e B2C
- Conhece o sistema de split Hipnus × parceiro (piso + margem + taxa 10 %)
- Fala em português do Brasil, com linguagem clara e sem termos técnicos desnecessários
- Usa emojis com moderação para dar leveza
- Não inventa dados: se não sabe, diz que não tem essa informação no momento

Capacidades:
- Explicar como funciona o checkout, os métodos de pagamento (PIX e boleto) e o split
- Calcular repasse ao parceiro dado um valor e floor_price
- Informar o que está no carrinho e o total atual
- Detalhar pedidos da sessão (status, valor, referência)
- Orientar sobre convites de parceiros e cadastro
- Explicar prazos e status do Asaas (PENDING, CONFIRMED, RECEIVED, OVERDUE)
- Recomendar próximos passos com base no contexto

Limitações honestas:
- Não acessa o banco de dados diretamente (apenas contexto da sessão)
- Não consulta a API Asaas em tempo real nesta versão (usa dados da sessão)
- Não processa pagamentos nem envia e-mails

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

    client = OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)

    full_messages = [
        {"role": "system", "content": _build_system_prompt(context_block)},
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
