import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

INBOX_BUCKET = "meu-claude-ui-2026-notes-inbox"
VAULT_PATH = Path(os.getenv("VAULT_PATH", "/mnt/c/Users/ferna/OneDrive/Obsidian"))
DEST_FOLDER = VAULT_PATH / "00 - Entrada"


def pull_inbox():
    client = storage.Client()
    bucket = client.bucket(INBOX_BUCKET)
    blobs = list(bucket.list_blobs())

    if not blobs:
        print("Nenhuma nota nova no inbox.")
        return

    for blob in blobs:
        safe_name = blob.name.replace("/", "-")
        dest_path = DEST_FOLDER / safe_name
        dest_path.write_text(blob.download_as_text(), encoding="utf-8")
        blob.delete()
        print(f"Trazida: {blob.name}" + (f" (salva como {safe_name})" if safe_name != blob.name else ""))

    print(f"{len(blobs)} nota(s) trazida(s) para 00 - Entrada/")


if __name__ == "__main__":
    pull_inbox()