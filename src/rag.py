import json
import numpy as np
from google.cloud import storage

BUCKET_NAME = "meu-claude-ui-2026-rag-index"
INDEX_BLOB = "vault_index.json"
EMBED_MODEL = "nvidia/nemotron-3-embed-1b"
TOP_K = 5

_index_cache = None


def load_index():
    global _index_cache
    if _index_cache is None:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(INDEX_BLOB)
        _index_cache = json.loads(blob.download_as_text())
    return _index_cache


def embed_query(nvidia_client, text):
    response = nvidia_client.embeddings.create(
        model=EMBED_MODEL,
        input=text,
        extra_body={"input_type": "query"},
    )
    return response.data[0].embedding

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def retrieve(nvidia_client, query, top_k=TOP_K):
    index = load_index()
    query_vector = embed_query(nvidia_client, query)
    scored = [(cosine_similarity(query_vector, c["embedding"]), c) for c in index]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


def build_context_block(chunks):
    parts = [f"[{c['source']}]\n{c['text']}" for c in chunks]
    return "Contexto do seu second brain (trechos relevantes das suas notas):\n\n" + "\n\n---\n\n".join(parts)
