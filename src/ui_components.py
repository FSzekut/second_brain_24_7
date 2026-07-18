from datetime import date
from pathlib import Path
import os
import streamlit as st


def check_password():
    def password_entered():
        if st.session_state["password"] == os.getenv("APP_PASSWORD"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input("Senha de acesso", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Senha incorreta")
    return False

def load_css(file_name):
    css_path = Path(__file__).parent / "assets" / file_name
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def render_page_config():
    st.set_page_config(
        page_title="Meu Claude Pessoal",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="auto",
    )
    st.markdown(
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
        unsafe_allow_html=True,
    )


def render_sidebar(providers, default_messages):
    with st.sidebar:
        st.markdown('<h1><i class="fa-solid fa-gears"></i> Configurações</h1>', unsafe_allow_html=True)
        st.markdown("Ajuste os parâmetros do seu assistente.")

        selected_provider_name = st.selectbox(
            "Escolha o provedor:",
            options=list(providers.keys()),
        )
        st.session_state.selected_provider = selected_provider_name

        model_mapping = providers[selected_provider_name]["models"]
        selected_model_name = st.selectbox(
            "Escolha o modelo:",
            options=list(model_mapping.keys()),
        )
        st.session_state.selected_model = model_mapping[selected_model_name]

        if st.button("Limpar Histórico da Conversa"):
            st.session_state.messages = default_messages.copy()
            st.success("Histórico limpo!")

        st.session_state.show_alerts_panel = st.checkbox(
            "🔔 Mostrar painel de alertas", value=st.session_state.get("show_alerts_panel", True)
        )

    return selected_provider_name, selected_model_name


def render_message_history(messages):
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def render_alerts_panel(alerts):
    st.markdown("### 🔔 Alertas")

    if not alerts:
        st.caption("Nenhuma tarefa pendente.")
        return

    today = date.today()
    rows = []
    for alert in alerts:
        try:
            prazo = date.fromisoformat(alert["prazo"])
        except (KeyError, ValueError):
            continue
        dias = (prazo - today).days
        if dias < 0:
            icone = "🔴"
        elif dias <= 3:
            icone = "🟡"
        else:
            icone = "⚪"
        projeto = f" ({alert['projeto']})" if alert.get("projeto") else ""
        rows.append(f"{icone} **{alert['titulo']}**{projeto}  \nprazo: {alert['prazo']}")

    if not rows:
        st.caption("Nenhuma tarefa pendente.")
        return

    for row in rows:
        st.markdown(row)
        st.divider()


def render_note_capture(save_fn):
    with st.sidebar:
        with st.expander("📝 Capturar nota rápida"):
            with st.form(key="note_form", clear_on_submit=True):
                title = st.text_input("Título (opcional)")
                content = st.text_area("O que você quer anotar?")
                submitted = st.form_submit_button("Salvar nota")

            if submitted:
                if content.strip():
                    filename = save_fn(title, content)
                    st.success(f"Salvo: {filename}")
                else:
                    st.warning("Escreve alguma coisa antes de salvar 🙂")