import json

from google.api_core.exceptions import NotFound
from google.cloud import storage

BUCKET_NAME = "meu-claude-ui-2026-rag-index"
ALERTS_BLOB = "alerts.json"


def load_alerts():
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(ALERTS_BLOB)
    try:
        return json.loads(blob.download_as_text())
    except NotFound:
        return []
