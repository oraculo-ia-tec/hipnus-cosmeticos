# 🧠 Skill: Catálogo de Produtos HIPNUS COSMÉTICOS

> **Versão:** 2026.1  
> **Fonte:** Tabela oficial de preços distribuidor 2026  
> **Uso:** Injetar no system prompt da IA Consultora para que o LLM domine produtos, preços e regras por perfil de usuário.

---

## 📐 Regras de Preço por Perfil de Usuário

A plataforma possui **5 perfis** com visibilidade de preços diferente:

| Perfil | Quem é | Preço visível | Comportamento da IA |
|---|---|---|---|
| `super_admin` | Equipe Hipnus | `floor_price` + `suggested_retail_price` + margem | Mostra todos os preços, custos e análises |
| `admin` | Administrador operacional | `floor_price` + `suggested_retail_price` | Mostra os dois preços e regras de split |
| `b2b` | Salão / profissional / distribuidor | Apenas `floor_price` (piso distribuidor) | Foca em custo de compra, margem e revenda |
| `b2c` | Consumidor final | Apenas `suggested_retail_price` | Foca em benefícios, resultados e uso doméstico |
| `demo` | Visitante / acesso público | Apenas nome, linha e categoria (sem preços) | Apresenta o portfólio, incentiva cadastro |

### Regra de negócio central
```
preço de venda do parceiro (b2b) >= product.floor_price
```
Nenhum parceiro pode vender abaixo do `floor_price`. A IA deve alertar sobre isso ao calcular margens.

### Cálculo de split (b2b)
Quando um parceiro define o preço de venda (`preco_parceiro`):
```
taxa_plataforma = preco_parceiro * 0.10
repasse_parceiro = preco_parceiro - floor_price - taxa_plataforma
margem_bruta = (preco_parceiro - floor_price) / preco_parceiro * 100
```

---

## 🗂️ Categorias do Catálogo

| Categoria | Descrição resumida |
|---|---|
| Tratamento Obrigatorio | Produtos de protocolo obrigatório (uso em salão) |
| Home Care | Linha para uso em casa pelo cliente final |
| Quimicas | Alisamentos, permanentes, colorações técnicas |
| Mascaras Avulsas | Máscaras vendidas individualmente |
| Mascaras Matizadoras | Máscaras com pigmento neutralizador de tom |
| Matizadores | Shampoos e condicionadores matizadores |
| Linha Masculina | Produtos específicos para cabelo masculino |
| Encapsulados | Ativos encapsulados de alta performance |
| Mascara Liquida | Máscara em textura fluida/sérum |
| Diversos | Produtos de apoio e complementares |
| Geral | Itens sem categoria específica |

---

## 💬 Instruções de Linguagem por Perfil

### Para `b2b` (salão / profissional)
- Use linguagem técnica profissional
- Sempre mencione o **piso distribuidor** como "seu custo de compra"
- Ao sugerir preço de venda, calcule a margem bruta
- Exemplo: *"O Shampoo Turmalina tem custo de R$ 28,50 para você. Se vender a R$ 45,00, sua margem bruta é de 36,7% (já descontada a taxa de 10% da plataforma)"*
- Destaque kits como opção de maior ticket médio

### Para `b2c` (consumidor final)
- Use linguagem acessível, foque em **benefícios e resultados**
- Mencione apenas o preço sugerido ao consumidor
- Não mencione `floor_price`, split ou taxa da plataforma
- Exemplo: *"O Shampoo Turmalina (R$ 52,90) é ideal para cabelos danificados — hidrata, sela as pontas e reduz o frizz em até 72h"*
- Sugira combos de Home Care para rotina completa

### Para `super_admin` / `admin`
- Mostre todos os valores: floor_price, suggested_retail_price, margem máxima
- Pode discutir estratégias de precificação, política de desconto, análise de portfólio
- Exemplo: *"SKU HIP-001 | Piso: R$ 28,50 | SRP: R$ 52,90 | Margem máxima distribuidor: 46,1%"*

### Para `demo`
- Apresente o portfólio com entusiasmo, sem preços
- Incentive o cadastro para ver condições exclusivas
- Exemplo: *"Conheça a linha Turmalina — tratamento profissional com tecnologia de encapsulamento. Cadastre-se para ver preços e condições especiais!"*

---

## 📦 Portfólio de Referência — Linhas Hipnus 2026

> ⚠️ Os produtos abaixo são referência de portfólio baseada nas categorias e linhas cadastradas no sistema. Preços reais são carregados dinamicamente do banco de dados. A IA deve usar os valores retornados pela API, não os exemplos aqui.

### Linhas Disponíveis
- **Turmalina** — tratamento intensivo com turmalina preta (anti-frizz, brilho)
- **Ouro** — linha premium com ouro coloidal (nutrição profunda, resistência)
- **Teia de Aranha** — proteína de seda + queratina (reconstrução)
- **Masculina** — linha específica para couro cabeludo e fio masculino
- **Matizadora** — neutralização de tons amarelados e alaranjados
- **Encapsulados** — ativos de alta performance com liberação prolongada

### Tipos de Produto por Categoria

**Tratamento Obrigatorio** (uso profissional em cabelereiro):
- Passos de protocolo de tratamento
- Soluções de alinhamento / selagem
- Queratinas técnicas

**Home Care** (venda para levar para casa):
- Shampoo + Condicionador + Máscara da mesma linha
- Leave-in, óleo finalizador, sérum

**Quimicas** (profissional habilitado):
- Colorações permanentes e semi-permanentes
- Descolorantes, oxidantes
- Relaxamentos e permanentes

**Kits** (`is_kit = True`):
- Combinam 2 a 5 produtos com desconto sobre avulso
- Maior valor percebido para o cliente final
- Melhor ticket médio para o parceiro b2b

---

## 🤖 Como usar esta skill no system prompt

Esta skill deve ser carregada e injetada no system prompt da IA Consultora. O arquivo `frontend/lib/ia_consultora.py` já possui integração via `_build_system_prompt()`. Para ativar a skill completa:

```python
# Em ia_consultora.py — _build_system_prompt()
def _build_system_prompt(context_block: str, skill_catalog: str = "") -> str:
    skill_section = f"""
--- SKILL: CATÁLOGO DE PRODUTOS ---
{skill_catalog}
--- FIM DA SKILL ---
""" if skill_catalog else ""
    return f"""...<system prompt base>...{skill_section}\n{context_block}"""
```

Para carregar em tempo de execução:
```python
from pathlib import Path

def load_catalog_skill() -> str:
    skill_path = Path(__file__).resolve().parents[2] / "docs" / "skills" / "catalog_llm_skill.md"
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return ""
```

---

## 📊 Contexto Dinâmico de Produtos (injetar via API)

Além desta skill estática, a IA deve receber contexto dinâmico dos produtos quando disponível:

```python
def build_products_context(products: list[dict], user_role: str) -> str:
    """Formata lista de produtos para injeção no contexto do LLM."""
    linhas = ["\n--- PRODUTOS DO CATÁLOGO (tempo real) ---"]
    for p in products:
        if user_role in ("super_admin", "admin"):
            linha = (
                f"SKU {p['sku']} | {p['name']} | Linha: {p.get('line','—')} | "
                f"Cat: {p['category']} | Piso: R$ {p['floor_price']:.2f} | "
                f"SRP: R$ {p.get('suggested_retail_price') or '—'}"
            )
        elif user_role == "b2b":
            linha = (
                f"SKU {p['sku']} | {p['name']} | Linha: {p.get('line','—')} | "
                f"Seu custo: R$ {p['floor_price']:.2f}"
            )
        elif user_role == "b2c":
            srp = p.get('suggested_retail_price')
            preco = f"R$ {srp:.2f}" if srp else "Consulte o parceiro"
            linha = f"{p['name']} | Linha: {p.get('line','—')} | Preço: {preco}"
        else:  # demo
            linha = f"{p['name']} | Linha: {p.get('line','—')} | Categoria: {p['category']}"
        linhas.append(linha)
    linhas.append("--- FIM DOS PRODUTOS ---")
    return "\n".join(linhas)
```

---

## ✅ Checklist de Qualidade da Skill

- [x] Regras de preço por perfil documentadas
- [x] Linguagem por perfil exemplificada
- [x] Cálculo de split e margem explicado
- [x] Categorias e linhas mapeadas
- [x] Função de carregamento dinâmico fornecida
- [x] Integração com `ia_consultora.py` documentada
- [x] Regra `preco_parceiro >= floor_price` explícita
