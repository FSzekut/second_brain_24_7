import anthropic
from openai import OpenAI
from google.genai import types

DEFAULT_MESSAGES = [
    {"role": "assistant", "content": "Olá! Como posso te ajudar hoje?"}
]

SYSTEM_PROMPT = (
    "Você é um assistente pessoal com acesso às notas do usuário via busca semântica. "
    "O bloco \"Contexto do seu second brain\" abaixo de cada pergunta contém trechos "
    "recuperados automaticamente por similaridade — podem ser irrelevantes ou "
    "desatualizados. Use-os somente se realmente responderem à pergunta feita. "
    "Nunca descreva a si mesmo, sua identidade ou seu histórico com base nesse "
    "contexto — ele é material de referência sobre o usuário e seus projetos, "
    "não uma descrição de quem você é. Se o contexto não for relevante ou "
    "suficiente, diga isso em vez de inventar uma resposta a partir dele."
)

MODEL_MAPPING = {
    "Claude Opus 4.8": "claude-opus-4-8",
    "Claude Sonnet 5": "claude-sonnet-5",
    "Claude Haiku 4.5": "claude-haiku-4-5",
}


def get_api_messages(messages):
    return [
        {"role": message["role"], "content": message["content"]}
        for message in messages
        if message["role"] in {"user", "assistant"}
        and message != DEFAULT_MESSAGES[0]
    ]


def stream_response(client, model, messages, max_tokens=2048):
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        yield from stream.text_stream

def stream_nvidia(client, model, messages, max_tokens=4096):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        max_tokens=max_tokens,
        temperature=0.6,
        top_p=0.95,
        stream=True,
        extra_body={"reasoning_budget": 8192},
    )
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            yield content

NVIDIA_MODEL_MAPPING = {
    "Nemotron 3 Nano Omni": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
}

GEMINI_MODEL_MAPPING = {
    "Gemini 3.5 Flash": "gemini-3.5-flash",
    "Gemini 2.5 Pro": "gemini-2.5-pro",
}

def to_gemini_contents(messages):
    role_map = {"user": "user", "assistant": "model"}
    return [
        types.Content(role=role_map[m["role"]], parts=[types.Part.from_text(text=m["content"])])
        for m in messages
    ]

def stream_gemini(client, model, messages, max_tokens=4096):
    contents = to_gemini_contents(messages)
    response = client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text

PROVIDERS = {
    "Claude": {
        "models": MODEL_MAPPING,
        "stream_fn": stream_response,
    },
    "NVIDIA NIM": {
        "models": NVIDIA_MODEL_MAPPING,
        "stream_fn": stream_nvidia,
    },
    "Gemini": {
        "models": GEMINI_MODEL_MAPPING,
        "stream_fn": stream_gemini,
    },
}