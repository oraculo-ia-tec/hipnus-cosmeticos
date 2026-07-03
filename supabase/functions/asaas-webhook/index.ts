
// supabase/functions/asaas-webhook/index.ts
// ============================================================
// HIPNUS COSMETICOS - Edge Function: Webhook Asaas
// ============================================================
// Recebe eventos de pagamento do Asaas e atualiza public.payments.
// A trigger fn_generate_commission cuida do split automaticamente
// apos o UPDATE de status = 'confirmed'.
//
// Deploy:
//   supabase functions deploy asaas-webhook --no-verify-jwt
// Env vars:
//   ASAAS_WEBHOOK_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
// ============================================================

import { serve } from "https://deno.land/std@0.192.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const WEBHOOK_TOKEN = Deno.env.get("ASAAS_WEBHOOK_TOKEN")!;

const supabase = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);

serve(async (req) => {
  const token = req.headers.get("asaas-access-token");
  if (token !== WEBHOOK_TOKEN) {
    return new Response(JSON.stringify({ error: "Token inválido" }), { status: 401 });
  }

  const payload = await req.json();
  const event = payload.event;
  const payment = payload.payment;

  if (!payment?.id) {
    return new Response(JSON.stringify({ error: "Payload inválido" }), { status: 400 });
  }

  let newStatus: string | null = null;
  if (event === "PAYMENT_CONFIRMED" || event === "PAYMENT_RECEIVED") newStatus = "confirmed";
  if (event === "PAYMENT_OVERDUE") newStatus = "failed";
  if (event === "PAYMENT_REFUNDED") newStatus = "refunded";

  if (!newStatus) {
    return new Response(JSON.stringify({ message: "Evento ignorado", event }), { status: 200 });
  }

  const { error } = await supabase
    .from("payments")
    .update({ status: newStatus, paid_at: newStatus === "confirmed" ? new Date().toISOString() : null })
    .eq("asaas_payment_id", payment.id);

  if (error) {
    return new Response(JSON.stringify({ error: "Falha ao atualizar pagamento", detail: error.message }), { status: 500 });
  }

  return new Response(JSON.stringify({ message: "Pagamento atualizado", status: newStatus }), { status: 200 });
});
