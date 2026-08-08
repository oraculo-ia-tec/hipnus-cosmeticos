
"""
pages/onboarding_and_store_config.py — TÁLYA COSMÉTICOS
==========================================================
Telas Streamlit:
1. Cadastro de Parceiro (distribuidor/salao)
2. Aprovacao de Parceiros (admin)
3. Configuracao da Loja (tema, banner, secoes)
"""
import streamlit as st
from lib.supabase_client import get_supabase
from lib.onboarding_queries import (
    create_partner_application, submit_onboarding_documents,
    get_my_partner_status, get_pending_partners,
    approve_partner, reject_partner,
)

supabase = get_supabase()


# ============================================================
# PAGINA 1 — Cadastro de Parceiro
# ============================================================
def page_partner_signup():
    st.title("Torne-se Parceiro Tálya")
    st.caption("Cadastre-se como Distribuidor ou Salão e ganhe sua loja virtual personalizada.")

    status = get_my_partner_status(supabase, st.session_state.user_id)

    if status:
        render_status_banner(status["status"])
        if status["status"] == "pending" and not status.get("partner_onboarding"):
            render_documents_form(status["id"])
        return

    with st.form("form_partner_signup"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nome / Razão social")
            cpf_cnpj = st.text_input("CPF ou CNPJ")
            partner_type = st.selectbox("Tipo de parceiro", ["distribuidor", "salao"],
                                         format_func=lambda x: "Distribuidor" if x == "distribuidor" else "Salão")
        with col2:
            email = st.text_input("E-mail")
            phone = st.text_input("Telefone / WhatsApp")
            legal_name = st.text_input("Nome fantasia (opcional)")

        submitted = st.form_submit_button("Enviar cadastro", type="primary", use_container_width=True, key="btn_partner_signup")

        if submitted:
            if not (name and cpf_cnpj and email):
                st.error("Preencha nome, CPF/CNPJ e e-mail.")
            else:
                create_partner_application(supabase, st.session_state.user_id, {
                    "name": name, "legal_name": legal_name, "email": email,
                    "phone": phone, "cpf_cnpj": cpf_cnpj, "partner_type": partner_type,
                })
                st.success("Cadastro enviado! Agora envie seus documentos para análise.")
                st.rerun()


def render_status_banner(status: str):
    labels = {
        "pending": ("⏳ Cadastro em análise", "warning"),
        "active": ("✅ Parceiro ativo — sua loja já está no ar", "success"),
        "suspended": ("⚠️ Conta suspensa — contate o suporte", "error"),
        "rejected": ("❌ Cadastro rejeitado", "error"),
    }
    text, kind = labels.get(status, ("Status desconhecido", "info"))
    getattr(st, kind)(text)


def render_documents_form(partner_id: str):
    st.subheader("Envio de documentos")
    with st.form("form_docs"):
        doc_front = st.text_input("URL documento (frente)")
        doc_back = st.text_input("URL documento (verso)")
        proof_address = st.text_input("URL comprovante de endereço")
        st.markdown("**Dados bancários / PIX**")
        bank_name = st.text_input("Banco")
        pix_key = st.text_input("Chave PIX")

        submitted = st.form_submit_button("Enviar documentos", type="primary", key="btn_docs_submit")
        if submitted:
            submit_onboarding_documents(supabase, partner_id, {
                "document_front_url": doc_front,
                "document_back_url": doc_back,
                "proof_of_address_url": proof_address,
                "bank_name": bank_name,
                "pix_key": pix_key,
            })
            st.success("Documentos enviados! Aguarde a aprovação do time Tálya.")
            st.rerun()


# ============================================================
# PAGINA 2 — Aprovacao de Parceiros (admin)
# ============================================================
def page_admin_partner_approval():
    st.title("Aprovação de Parceiros")
    pending = get_pending_partners(supabase)

    if not pending:
        st.info("Nenhum parceiro pendente de aprovação.")
        return

    for partner in pending:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"### {partner['name']} · {partner['partner_type'].title()}")
                st.write(f"CPF/CNPJ: {partner['cpf_cnpj']} · E-mail: {partner['email']}")
                onboarding = partner.get("partner_onboarding")
                if onboarding:
                    st.write(f"Banco: {onboarding.get('bank_name','—')} · PIX: {onboarding.get('pix_key','—')}")
                else:
                    st.warning("Documentos ainda não enviados.")
            with c2:
                if st.button("✅ Aprovar", key=f"btn_approve_{partner['id']}", type="primary", use_container_width=True):
                    approve_partner(supabase, partner["id"], st.session_state.user_id)
                    st.success("Parceiro aprovado! Loja criada automaticamente.")
                    st.rerun()
                if st.button("❌ Rejeitar", key=f"btn_reject_{partner['id']}", use_container_width=True):
                    reject_partner(supabase, partner["id"], st.session_state.user_id, "Documentação incompleta")
                    st.warning("Parceiro rejeitado.")
                    st.rerun()


# ============================================================
# PAGINA 3 — Configuracao da Loja (tema moderno)
# ============================================================
def page_store_config(store_id: str):
    st.title("Configurar minha Loja")

    theme = (
        supabase.table("store_themes").select("*").eq("store_id", store_id).maybe_single().execute().data
        or {}
    )

    tab_identidade, tab_cores, tab_secoes, tab_preview = st.tabs(
        ["🏷️ Identidade", "🎨 Cores e tema", "🧩 Seções da vitrine", "👁️ Pré-visualização"]
    )

    # --- Aba Identidade ---
    with tab_identidade:
        with st.form("form_identidade"):
            logo_url = st.text_input("URL do logo", value=theme.get("logo_url", ""))
            banner_url = st.text_input("URL do banner principal", value=theme.get("banner_url", ""))
            tagline = st.text_input("Frase de destaque", value=theme.get("tagline", ""),
                                     placeholder="Ex: Sua beleza, nosso cuidado.")
            about_text = st.text_area("Sobre a loja", value=theme.get("about_text", ""))
            whatsapp = st.text_input("WhatsApp de contato", value=theme.get("whatsapp_number", ""))
            instagram = st.text_input("Instagram (@usuario)", value=theme.get("instagram_handle", ""))

            if st.form_submit_button("Salvar identidade", type="primary", key="btn_save_identity"):
                _upsert_theme(store_id, {
                    "logo_url": logo_url, "banner_url": banner_url, "tagline": tagline,
                    "about_text": about_text, "whatsapp_number": whatsapp, "instagram_handle": instagram,
                })
                st.success("Identidade da loja atualizada.")
                st.rerun()

    # --- Aba Cores ---
    with tab_cores:
        with st.form("form_cores"):
            primary_color = st.color_picker("Cor primária", value=theme.get("primary_color", "#7c3aed"))
            secondary_color = st.color_picker("Cor secundária", value=theme.get("secondary_color", "#ec4899"))
            background_style = st.radio("Estilo de fundo", ["light", "dark"],
                                         index=0 if theme.get("background_style", "light") == "light" else 1,
                                         format_func=lambda x: "Claro" if x == "light" else "Escuro", horizontal=True)
            show_ratings = st.toggle("Exibir avaliações de produtos", value=theme.get("show_ratings", True))

            if st.form_submit_button("Salvar tema", type="primary", key="btn_save_theme"):
                _upsert_theme(store_id, {
                    "primary_color": primary_color, "secondary_color": secondary_color,
                    "background_style": background_style, "show_ratings": show_ratings,
                })
                st.success("Tema visual atualizado.")
                st.rerun()

    # --- Aba Secoes ---
    with tab_secoes:
        sections = (
            supabase.table("store_sections").select("*").eq("store_id", store_id)
            .order("display_order").execute().data
        )
        st.caption("Adicione blocos que aparecem na sua loja, em ordem.")

        for sec in sections:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{sec['section_type'].replace('_',' ').title()}** — {sec.get('title','')}")
                    st.caption(sec.get("content", "")[:120])
                with c2:
                    st.toggle("Ativo", value=sec["is_active"], key=f"toggle_sec_{sec['id']}")

        with st.expander("➕ Adicionar nova seção"):
            with st.form("form_new_section"):
                section_type = st.selectbox("Tipo de seção",
                    ["banner", "linha_destaque", "depoimentos", "sobre", "combo", "promocao"])
                title = st.text_input("Título")
                content = st.text_area("Conteúdo")
                image_url = st.text_input("URL da imagem (opcional)")

                if st.form_submit_button("Adicionar seção", type="primary", key="btn_add_section"):
                    supabase.table("store_sections").insert({
                        "store_id": store_id, "section_type": section_type,
                        "title": title, "content": content, "image_url": image_url,
                        "display_order": len(sections),
                    }).execute()
                    st.success("Seção adicionada.")
                    st.rerun()

    # --- Aba Preview ---
    with tab_preview:
        _render_store_preview(theme, sections if 'sections' in locals() else [])


def _upsert_theme(store_id: str, fields: dict) -> None:
    fields["store_id"] = store_id
    supabase.table("store_themes").upsert(fields, on_conflict="store_id").execute()


def _render_store_preview(theme: dict, sections: list[dict]):
    primary = theme.get("primary_color", "#7c3aed")
    secondary = theme.get("secondary_color", "#ec4899")
    bg = "#0f0f14" if theme.get("background_style") == "dark" else "#ffffff"
    text_color = "#f3f4f6" if theme.get("background_style") == "dark" else "#111827"

    st.markdown(f"""
    <div style="background:{bg};color:{text_color};border-radius:16px;padding:24px;
                border:1px solid #33333333;">
      <div style="height:140px;border-radius:12px;
                  background:linear-gradient(135deg,{primary},{secondary});
                  display:flex;align-items:center;justify-content:center;
                  color:white;font-size:22px;font-weight:700;">
        {theme.get('tagline') or 'Sua loja Tálya'}
      </div>
      <p style="margin-top:16px;">{theme.get('about_text') or 'Descrição da loja aparecerá aqui.'}</p>
    </div>
    """, unsafe_allow_html=True)

    for sec in sections:
        if not sec.get("is_active", True):
            continue
        st.markdown(f"""
        <div style="margin-top:12px;padding:16px;border-radius:12px;
                    border:1px solid #33333333;">
          <b>{sec['title']}</b><br>
          <span style="color:#9ca3af;">{sec.get('content','')}</span>
        </div>
        """, unsafe_allow_html=True)
