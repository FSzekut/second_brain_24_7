import logging
import os
import rag

import inbox
from google import genai
from openai import OpenAI
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

selected_provider_name, selected_model_name = ui_components.render_sidebar(
    business_logic.PROVIDERS, business_logic.DEFAULT_MESSAGES
)
ui_components.render_note_capture(inbox.save_note_to_inbox)

if not ANTHROPIC_API_KEY:
    st.error("API Key da Anthropic não encontrada. Defina ANTHROPIC_API_KEY no arquivo .env ou nas variáveis de ambiente.")
    st.stop()

try:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
except Exception as e:
    st.error("Erro ao inicializar o cliente da Anthropic. Verifique sua API Key. 🤖")
    st.stop()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

try:
    nvidia_client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_API_KEY)
except Exception as e:
    st.error("Erro ao inicializar o cliente da NVIDIA. Verifique sua API Key. 🤖")
    st.stop()

clients = {
    "Claude": client,
    "NVIDIA NIM": nvidia_client,
}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error("Erro ao inicializar o cliente do Gemini. Verifique sua API Key. 🤖")
    st.stop()

clients = {
    "Claude": client,
    "NVIDIA NIM": nvidia_client,
    "Gemini": gemini_client,
}

st.markdown('<h1>Meu Brain Pessoal <i class="fa-solid fa-robot"></i></h1>', unsafe_allow_html=True)
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
                provider_info = business_logic.PROVIDERS[st.session_state.selected_provider]
                active_client = clients[st.session_state.selected_provider]
                api_messages = business_logic.get_api_messages(st.session_state.messages)
                retrieved_chunks = rag.retrieve(nvidia_client, prompt)
                context_block = rag.build_context_block(retrieved_chunks)
                api_messages[-1]["content"] = f"{context_block}\n\nPergunta do usuário: {api_messages[-1]['content']}"
                response = cast(str, st.write_stream(
                    provider_info["stream_fn"](active_client, st.session_state.selected_model, api_messages)
                ))
            except Exception as e:
                logger.error("Erro ao chamar API Anthropic: %r", e, exc_info=True)
                st.error(f"Ocorreu um erro ao chamar a API: {e}")
                response = "Desculpe, ocorreu um erro."

    st.session_state.messages.append({"role": "assistant", "content": response})