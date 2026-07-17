import os
import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

VAULT_PATH = Path(os.getenv("VAULT_PATH", "/mnt/c/Users/ferna/OneDrive/Obsidian"))
SKIP_DIRS = {".obsidian", "09 - Sistema", ".git"}
EMBED_MODEL = "nvidia/nemotron-3-embed-1b"
CHUNK_SIZE = 1500

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=os.getenv("NVIDIA_API_KEY"))


def should_skip(relative_path):
    return any(part in SKIP_DIRS for part in relative_path.parts)


def is_corporate(text):
    frontmatter = text.split("---")[1] if text.startswith("---") else ""
    return "classificacao: corporativo" in frontmatter


def chunk_text(text, size=CHUNK_SIZE):
    paragraphs = text.split("\n\n")
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) > size and current:
            chunks.append(current.strip())
            current = ""
        current += p + "\n\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks


def embed(text, input_type):
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=text,
        extra_body={"input_type": input_type},
    )
    return response.data[0].embedding


def build_index():
    index = []
    for path in VAULT_PATH.rglob("*.md"):
        if should_skip(path.relative_to(VAULT_PATH)):
            continue
        text = path.read_text(encoding="utf-8")
        if is_corporate(text):
            continue
        for chunk in chunk_text(text):
            vector = embed(chunk, input_type="passage")
            index.append({
                "text": chunk,
                "source": str(path.relative_to(VAULT_PATH)),
                "embedding": vector,
            })
        print(f"Indexado: {path.name} ({len(index)} chunks até agora)")

    with open("vault_index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    print(f"Índice salvo: {len(index)} chunks em vault_index.json")


if __name__ == "__main__":
    build_index()