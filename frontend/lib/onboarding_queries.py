
"""
onboarding_queries.py — TÁLYA COSMÉTICOS
==========================================
Queries para o modulo de Onboarding de Parceiros.
"""
from supabase import Client


# ---------- Cadastro (parceiro) ----------

def create_partner_application(supabase: Client, user_id: str, data: dict) -> dict | None:
    """Cria o registro inicial do parceiro (status=pending)."""
    payload = {
        "user_id": user_id,
        "name": data["name"],
        "legal_name": data.get("legal_name"),
        "email": data["email"],
        "phone": data.get("phone"),
        "cpf_cnpj": data["cpf_cnpj"],
        "partner_type": data["partner_type"],
        "status": "pending",
    }
    try:
        res = supabase.table("partners").insert(payload).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def submit_onboarding_documents(supabase: Client, partner_id: str, docs: dict) -> dict | None:
    """Envia documentos e dados bancarios para analise."""
    docs["partner_id"] = partner_id
    docs["submitted_at"] = "now()"
    try:
        res = supabase.table("partner_onboarding").upsert(docs, on_conflict="partner_id").execute()
        return res.data[0] if res.data else None
    except Exception:
        return None


def get_my_partner_status(supabase: Client, user_id: str) -> dict | None:
    """Consulta status atual do cadastro do parceiro logado."""
    try:
        res = (
            supabase.table("partners")
            .select("*, partner_onboarding(*)")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        return res.data
    except Exception:
        return None


# ---------- Aprovacao (admin) ----------

def get_pending_partners(supabase: Client) -> list[dict]:
    """Lista parceiros pendentes de aprovacao para a tela do admin."""
    try:
        res = (
            supabase.table("partners")
            .select("*, partner_onboarding(*)")
            .eq("status", "pending")
            .order("created_at")
            .execute()
        )
        return res.data or []
    except Exception:
        return []


def approve_partner(supabase: Client, partner_id: str, reviewer_id: str) -> bool:
    """Aprova o parceiro. Trigger cria loja e estoque automaticamente."""
    try:
        supabase.table("partner_onboarding").update({
            "reviewed_by": reviewer_id, "reviewed_at": "now()",
        }).eq("partner_id", partner_id).execute()
        supabase.table("partners").update({"status": "active"}).eq("id", partner_id).execute()
        return True
    except Exception:
        return False


def reject_partner(supabase: Client, partner_id: str, reviewer_id: str, reason: str) -> bool:
    """Rejeita o parceiro com motivo registrado."""
    try:
        supabase.table("partner_onboarding").update({
            "reviewed_by": reviewer_id, "reviewed_at": "now()", "rejection_reason": reason,
        }).eq("partner_id", partner_id).execute()
        supabase.table("partners").update({"status": "rejected"}).eq("id", partner_id).execute()
        return True
    except Exception:
        return False


def suspend_partner(supabase: Client, partner_id: str, reason: str) -> dict:
    """Suspende parceiro ativo (ex: inadimplencia, denuncia)."""
    res = supabase.table("partners").update({"status": "suspended"}).eq("id", partner_id).execute()
    return res.data


def provision_asaas_subaccount(supabase: Client, partner_id: str, asaas_account_id: str, asaas_wallet_id: str) -> dict:
    """Grava os IDs da subconta Asaas apos provisionamento via API oficial."""
    res = (
        supabase.table("partners")
        .update({
            "asaas_account_id": asaas_account_id,
            "asaas_wallet_id": asaas_wallet_id,
        })
        .eq("id", partner_id)
        .execute()
    )
    return res.data
