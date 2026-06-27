"""
pages/9_Configuracao.py — HIPNUS COSMÉTICOS
=============================================
Página de Configuração de conta — disponível para TODOS os perfis.
Esta é a página que o Streamlit Cloud lê para montar o menu sidebar.
Implementação completa aqui (não usa exec para evitar duplo set_page_config).
"""
from __future__ import annotations
import sys
from pathlib import Path

# Garante paths corretos para imports
_repo_root = Path(__file__).resolve().parents[1]
_frontend  = _repo_root / "frontend"
for _p in [str(_repo_root), str(_frontend)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
from lib import ui, components
from lib.auth import require_auth, sidebar_logo, sidebar_user_info, sidebar_logout_button
from lib.user_db import atualizar_perfil, alterar_senha, buscar_por_email, image_to_b64
from lib.email_service import smtp_status, send_test_email

st.set_page_config(page_title="Configurações · HIPNUS", page_icon="⚙️", layout="wide")
ui.inject_theme()
usuario = require_auth()
sidebar_logo()
sidebar_user_info()
sidebar_logout_button()

components.page_header(
    title="Configurações da Conta",
    subtitle="Gerencie seu perfil, foto e preferências da sua conta Hipnus.",
    kicker="Minha Conta",
)

email_logado  = usuario.get("email", "")
nome_logado   = usuario.get("nome", "")
perfil_logado = usuario.get("perfil", "demo")

parceiro_db = buscar_por_email(email_logado) if (email_logado and "@" in email_logado) else None
smtp = smtp_status()

def _val(campo: str, fallback: str = "") -> str:
    if parceiro_db and parceiro_db.get(campo):
        return str(parceiro_db[campo])
    return st.session_state.get(campo, fallback)

avatar_atual = (parceiro_db.get("avatar_b64") if parceiro_db else None) or st.session_state.get("avatar_b64")

# ── Tabs
tab_perfil, tab_foto, tab_senha, tab_email = st.tabs(["👤 Perfil", "📸 Foto de Perfil", "🔑 Senha", "📧 E-mail"])

# ══ TAB 1 — PERFIL
with tab_perfil:
    components.section_title("Informações pessoais")
    icone_map    = {"super_admin": "⭐", "admin": "🛡️", "b2b": "🎤", "b2c": "👤", "demo": "👀"}
    role_display = {"super_admin": "⭐ Super Admin", "admin": "🛡️ Admin",
                    "b2b": "🎤 Profissional", "b2c": "👤 Cliente", "demo": "👀 Demo"}.get(perfil_logado, perfil_logado)
    img_tag = (
        f'<img src="{avatar_atual}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;border:3px solid #7c3aed;"/>'
        if avatar_atual else
        f'<div style="width:80px;height:80px;border-radius:50%;background:#f3f0ff;border:3px solid #7c3aed;'
        f'display:flex;align-items:center;justify-content:center;font-size:2.2rem;">{icone_map.get(perfil_logado, "👤")}</div>'
    )
    st.html(f"""
    <div style="display:flex;align-items:center;gap:20px;background:#f8f7fc;
                border:1px solid #e5e0f5;border-radius:16px;padding:20px 24px;margin-bottom:20px;">
        {img_tag}
        <div>
            <div style="font-size:1.1rem;font-weight:700;color:#1a0a2e;">{nome_logado}</div>
            <div style="font-size:.82rem;color:#7c3aed;font-weight:600;margin:2px 0;">{role_display}</div>
            <div style="font-size:.78rem;color:#6b7280;">{email_logado}</div>
        </div>
    </div>""")

    if perfil_logado == "demo":
        st.info("👀 Modo demonstração — alterações não estão disponíveis.")
    else:
        with st.form("form_perfil", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                novo_nome     = st.text_input("Nome completo",   value=_val("nome", nome_logado))
                novo_username = st.text_input("Usuário (login)", value=_val("username", usuario.get("login", "")),
                                              help="Mín 3 chars. Letras minúsculas, números, . _ -")
                novo_tel      = st.text_input("Telefone",         value=_val("telefone"))
            with c2:
                nova_empresa = st.text_input("Empresa / negócio", value=_val("empresa"))
                nova_cidade  = st.text_input("Cidade",             value=_val("cidade"))
                novo_estado  = st.selectbox("Estado", ["MG","SP","RJ","ES","BA","GO","DF","PR","SC","RS",
                                                       "MT","MS","AM","PA","CE","PE","MA","PB","RN","AL",
                                                       "SE","PI","TO","RO","AC","RR","AP"], index=0)
            nova_bio = st.text_area("Mini bio", value=_val("bio"), height=90,
                                   placeholder="Conte um pouco sobre você ou seu negócio...")
            salvar = st.form_submit_button("💾 Salvar alterações", use_container_width=True, type="primary")
        if salvar:
            if not parceiro_db:
                st.session_state["nome"]         = novo_nome
                st.session_state["display_name"] = novo_username or novo_nome
                st.success("✅ Sessão atualizada (temporário — usuário seed).")
            else:
                ok, msg = atualizar_perfil(email=email_logado, nome=novo_nome, username=novo_username,
                                           telefone=novo_tel, empresa=nova_empresa,
                                           cidade=nova_cidade, estado=novo_estado, bio=nova_bio)
                if ok:
                    st.session_state["nome"]         = novo_nome
                    st.session_state["display_name"] = nova_empresa or novo_nome
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

# ══ TAB 2 — FOTO
with tab_foto:
    components.section_title("Foto de perfil")
    col_prev, col_up = st.columns([1, 2])
    with col_prev:
        st.markdown("**Foto atual**")
        if avatar_atual:
            st.html(f'<img src="{avatar_atual}" style="width:120px;height:120px;border-radius:50%;object-fit:cover;border:3px solid #7c3aed;display:block;"/>')
        else:
            st.html('<div style="width:120px;height:120px;border-radius:50%;background:#f3f0ff;border:3px solid #7c3aed;display:flex;align-items:center;justify-content:center;font-size:3rem;">👤</div>')
    with col_up:
        st.markdown("**Enviar nova foto**")
        st.caption("📸 JPG, PNG ou WEBP · Máx 2 MB")
        novo_avatar = st.file_uploader("imagem", type=["jpg","jpeg","png","webp"],
                                       label_visibility="collapsed", key="up_avatar")
        if novo_avatar:
            if novo_avatar.size > 2 * 1024 * 1024:
                st.error("❌ Imagem muito grande. Máximo 2 MB.")
            else:
                mime_map = {"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png","webp":"image/webp"}
                mime     = mime_map.get(novo_avatar.name.split(".")[-1].lower(), "image/jpeg")
                novo_b64 = image_to_b64(novo_avatar.read(), mime)
                st.html(f'<p style="font-size:.8rem;color:#6b7280;">Pré-visualização:</p><img src="{novo_b64}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;border:2px solid #7c3aed;"/>')
                if st.button("💾 Salvar foto", type="primary", use_container_width=True):
                    if parceiro_db:
                        atualizar_perfil(email_logado, avatar_b64=novo_b64)
                    st.session_state["avatar_b64"] = novo_b64
                    st.success("✅ Foto atualizada!")
                    st.rerun()
    if avatar_atual:
        components.divider()
        if st.button("🗑️ Remover foto de perfil"):
            if parceiro_db:
                atualizar_perfil(email_logado, avatar_b64="")
            st.session_state["avatar_b64"] = None
            st.success("✅ Foto removida.")
            st.rerun()

# ══ TAB 3 — SENHA
with tab_senha:
    components.section_title("Alterar senha")
    if not parceiro_db:
        st.info("🔑 Usuários seed/demo não podem alterar senha aqui.")
    else:
        with st.form("form_senha", clear_on_submit=True):
            senha_atual = st.text_input("Senha atual",           type="password")
            nova_senha  = st.text_input("Nova senha",            type="password", placeholder="mín 8 caracteres")
            nova_senha2 = st.text_input("Confirme a nova senha", type="password")
            btn_senha   = st.form_submit_button("🔑 Alterar senha", use_container_width=True, type="primary")
        if btn_senha:
            if len(nova_senha) < 8:
                st.error("❌ Senha deve ter ao menos 8 caracteres.")
            elif nova_senha != nova_senha2:
                st.error("❌ As senhas não coincidem.")
            else:
                ok_p, msg_p = alterar_senha(email_logado, senha_atual, nova_senha)
                st.success(f"✅ {msg_p}") if ok_p else st.error(f"❌ {msg_p}")

# ══ TAB 4 — E-MAIL
with tab_email:
    components.section_title("Notificações por e-mail")

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown("**Status do SMTP**")
        st.caption("Diagnóstico seguro do ambiente Hostinger sem expor senha.")
        st.html(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:10px 0 18px;">
            <div style="background:#f8f7fc;border:1px solid #e5e0f5;border-radius:14px;padding:14px;">
                <div style="font-size:.72rem;color:#6b7280;text-transform:uppercase;font-weight:700;">Host</div>
                <div style="font-size:.95rem;color:#1a0a2e;font-weight:700;">{smtp['host']}</div>
            </div>
            <div style="background:#f8f7fc;border:1px solid #e5e0f5;border-radius:14px;padding:14px;">
                <div style="font-size:.72rem;color:#6b7280;text-transform:uppercase;font-weight:700;">Porta</div>
                <div style="font-size:.95rem;color:#1a0a2e;font-weight:700;">{smtp['port']}</div>
            </div>
            <div style="background:#f8f7fc;border:1px solid #e5e0f5;border-radius:14px;padding:14px;">
                <div style="font-size:.72rem;color:#6b7280;text-transform:uppercase;font-weight:700;">Usuário SMTP</div>
                <div style="font-size:.95rem;color:{'#16a34a' if smtp['user_configured'] else '#dc2626'};font-weight:700;">{'Configurado' if smtp['user_configured'] else 'Pendente'}</div>
            </div>
            <div style="background:#f8f7fc;border:1px solid #e5e0f5;border-radius:14px;padding:14px;">
                <div style="font-size:.72rem;color:#6b7280;text-transform:uppercase;font-weight:700;">Senha SMTP</div>
                <div style="font-size:.95rem;color:{'#16a34a' if smtp['password_configured'] else '#dc2626'};font-weight:700;">{'Configurada' if smtp['password_configured'] else 'Pendente'}</div>
            </div>
        </div>
        """)

        if smtp["ready"]:
            st.success(f"✅ SMTP pronto para uso. Remetente padrão: {smtp['from_email']}")
        else:
            st.warning("⚠️ SMTP ainda incompleto. Preencha as variáveis no ambiente antes de testar o envio.")

    with c2:
        st.markdown("**Teste de envio**")
        destino_teste = st.text_input(
            "Enviar teste para",
            value=email_logado or "",
            placeholder="email@dominio.com",
            key="smtp_email_teste",
        )
        st.caption("Use um e-mail válido para validar o SMTP da Hostinger em produção.")
        enviar_teste = st.button("📨 Enviar e-mail de teste", type="primary", use_container_width=True)
        if enviar_teste:
            if not destino_teste or "@" not in destino_teste:
                st.error("❌ Informe um e-mail válido para teste.")
            else:
                ok_mail, msg_mail = send_test_email(destino_teste.strip())
                st.success(f"✅ {msg_mail}") if ok_mail else st.error(f"❌ {msg_mail}")

    components.divider()
    st.markdown("**Próximos disparos prontos para plugar nesta skill**")
    st.markdown(
        "- Convite de parceiro enviado automaticamente após aprovação.\n"
        "- Confirmação de pedido com resumo da compra.\n"
        "- Atualização de pagamento/checkout.\n"
        "- Alerta interno para o admin quando um novo parceiro concluir cadastro."
    )
