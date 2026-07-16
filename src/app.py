import streamlit as st
import anthropic
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_MESSAGES = [
    {"role": "assistant", "content": "Olá! Como posso te ajudar hoje?"}
]


# --- 1. CONFIGURAÇÃO DA PÁGINA E ESTILO ---
st.set_page_config(
    page_title="Meu Claude Pessoal",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto",
)

st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">', unsafe_allow_html=True)

# Carrega a API Key do arquivo .env (para desenvolvimento local)
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def load_css(file_name):
    css_path = Path(__file__).parent / "assets" / file_name
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

def get_api_messages(messages):
    return [
        {"role": message["role"], "content": message["content"]}
        for message in messages
        if message["role"] in {"user", "assistant"}
        and message != DEFAULT_MESSAGES[0]
    ]

load_css("style.css")

# --- 2. BARRA LATERAL (SIDEBAR) COM CONFIGURAÇÕES ---
with st.sidebar:
    st.markdown('<h1><i class="fa-solid fa-gears"></i> Configurações</h1>', unsafe_allow_html=True)
    st.markdown("Ajuste os parâmetros do seu assistente Claude.")

    model_mapping = {
        "Claude Opus 4.8": "claude-opus-4-8",
        "Claude Sonnet 5": "claude-sonnet-5",
        "Claude Haiku 4.5": "claude-haiku-4-5",
    }
    selected_model_name = st.selectbox(
        "Escolha o modelo:",
        options=list(model_mapping.keys()),
        index=1  # 'Sonnet' como padrão
    )
    st.session_state.selected_model = model_mapping[selected_model_name]

    if st.button("Limpar Histórico da Conversa"):
        st.session_state.messages = DEFAULT_MESSAGES.copy()
        st.success("Histórico limpo!")

# --- 3. INICIALIZAÇÃO DO CLIENTE E DO CHAT ---
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
    st.session_state.messages = DEFAULT_MESSAGES.copy()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. LÓGICA DO CHAT ---
if prompt := st.chat_input("Qual sua dúvida?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                api_messages = get_api_messages(st.session_state.messages)

                with client.messages.stream(
                    model=st.session_state.selected_model,
                    max_tokens=2048,
                    messages=api_messages,
                ) as stream:
                    response = st.write_stream(stream.text_stream)
            except Exception as e:
                logger.error("Erro ao chamar API Anthropic: %r", e, exc_info=True)
                st.error(f"Ocorreu um erro ao chamar a API: {e}")
                response = "Desculpe, ocorreu um erro."

    st.session_state.messages.append({"role": "assistant", "content": response})
