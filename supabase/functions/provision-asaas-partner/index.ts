
// supabase/functions/provision-asaas-partner/index.ts
// ============================================================
// HIPNUS COSMETICOS - Edge Function: Provisionamento Asaas
// ============================================================
// Disparada apos aprovacao do parceiro (status -> active).
// Cria subconta (wallet) no Asaas via API oficial e grava os
// IDs de volta na tabela partners, usando service_role.
//
// Deploy:
//   supabase functions deploy provision-asaas-partner
// Env vars (supabase secrets set):
//   ASAAS_API_KEY, ASAAS_BASE_URL, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
// ============================================================

import { serve } from "https://deno.land/std@0.192.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const ASAAS_API_KEY = Deno.env.get("ASAAS_API_KEY")!;
const ASAAS_BASE_URL = Deno.env.get("ASAAS_BASE_URL")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

interface PartnerPayload {
  partner_id: string;
}

serve(async (req) => {
  try {
    const { partner_id }: PartnerPayload = await req.json();

    if (!partner_id) {
      return new Response(JSON.stringify({ error: "partner_id é obrigatório" }), { status: 400 });
    }

    const { data: partner, error: partnerError } = await supabase
      .from("partners")
      .select("*")
      .eq("id", partner_id)
      .single();

    if (partnerError || !partner) {
      return new Response(JSON.stringify({ error: "Parceiro não encontrado" }), { status: 404 });
    }

    if (partner.asaas_account_id) {
      return new Response(JSON.stringify({ message: "Parceiro já possui subconta Asaas", partner }), { status: 200 });
    }

    const onboardingRes = await supabase
      .from("partner_onboarding")
      .select("*")
      .eq("partner_id", partner_id)
      .single();

    const onboarding = onboardingRes.data;

    const asaasPayload = {
      name: partner.legal_name || partner.name,
      email: partner.email,
      cpfCnpj: partner.cpf_cnpj,
      mobilePhone: partner.phone,
      incomeValue: 5000,
      companyType: partner.partner_type === "distribuidor" ? "LIMITED" : "MEI",
    };

    const asaasRes = await fetch(`${ASAAS_BASE_URL}/accounts`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        access_token: ASAAS_API_KEY,
      },
      body: JSON.stringify(asaasPayload),
    });

    if (!asaasRes.ok) {
      const errorBody = await asaasRes.text();
      await supabase.from("partner_status_history").insert({
        partner_id,
        from_status: partner.status,
        to_status: partner.status,
        reason: `Falha ao provisionar Asaas: ${errorBody}`,
      });
      return new Response(JSON.stringify({ error: "Falha ao criar subconta Asaas", detail: errorBody }), { status: 502 });
    }

    const asaasAccount = await asaasRes.json();

    const { error: updateError } = await supabase
      .from("partners")
      .update({
        asaas_account_id: asaasAccount.id,
        asaas_wallet_id: asaasAccount.walletId,
      })
      .eq("id", partner_id);

    if (updateError) {
      return new Response(JSON.stringify({ error: "Falha ao salvar dados Asaas", detail: updateError.message }), { status: 500 });
    }

    await supabase.from("partner_status_history").insert({
      partner_id,
      from_status: partner.status,
      to_status: partner.status,
      reason: "Subconta Asaas provisionada com sucesso",
    });

    return new Response(
      JSON.stringify({
        message: "Subconta Asaas criada com sucesso",
        asaas_account_id: asaasAccount.id,
        asaas_wallet_id: asaasAccount.walletId,
      }),
      { status: 200 },
    );
  } catch (err) {
    return new Response(JSON.stringify({ error: "Erro interno", detail: String(err) }), { status: 500 });
  }
});
