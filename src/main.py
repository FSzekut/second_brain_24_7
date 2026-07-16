import logging
import os

import anthropic
import streamlit as st
from dotenv import load_dotenv

import business_logic
import ui_components

from typing import cast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

ui_components.render_page_config()
ui_components.load_css("style.css")

if not ui_components.check_password():
    st.stop()

selected_model_name = ui_components.render_sidebar(
    business_logic.MODEL_MAPPING, business_logic.DEFAULT_MESSAGES
)

if not ANTHROPIC_API_KEY:
    st.error("API Key da Anthropic não encontrada. Defina ANTHROPIC_API_KEY no arquivo .env ou nas variáveis de ambiente.")
    st.stop()

try:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
except Exception as e:
    st.error("Erro ao inicializar o cliente da Anthropic. Verifique sua API Key. 🤖")
    st.stop()

st.markdown('<h1>Meu Claude Pessoal <i class="fa-solid fa-robot"></i></h1>', unsafe_allow_html=True)
st.caption(f"Utilizando o modelo: **{selected_model_name}**")

if "messages" not in st.session_state:
    st.session_state.messages = business_logic.DEFAULT_MESSAGES.copy()

ui_components.render_message_history(st.session_state.messages)

if prompt := st.chat_input("Qual sua dúvida?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                api_messages = business_logic.get_api_messages(st.session_state.messages)
                response = cast(str, st.write_stream(
                    business_logic.stream_response(client, st.session_state.selected_model, api_messages)
                ))
            except Exception as e:
                logger.error("Erro ao chamar API Anthropic: %r", e, exc_info=True)
                st.error(f"Ocorreu um erro ao chamar a API: {e}")
                response = "Desculpe, ocorreu um erro."

    st.session_state.messages.append({"role": "assistant", "content": response})