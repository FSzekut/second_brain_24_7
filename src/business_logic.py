import anthropic

DEFAULT_MESSAGES = [
    {"role": "assistant", "content": "Olá! Como posso te ajudar hoje?"}
]

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
        messages=messages,
    ) as stream:
        yield from stream.text_stream