from pathlib import Path
from google.cloud import storage

INBOX_BUCKET = "meu-claude-ui-2026-notes-inbox"
DEST_FOLDER = Path("/mnt/c/Users/ferna/OneDrive/Obsidian/00 - Entrada")


def pull_inbox():
    client = storage.Client()
    bucket = client.bucket(INBOX_BUCKET)
    blobs = list(bucket.list_blobs())

    if not blobs:
        print("Nenhuma nota nova no inbox.")
        return

    for blob in blobs:
        dest_path = DEST_FOLDER / blob.name
        dest_path.write_text(blob.download_as_text(), encoding="utf-8")
        blob.delete()
        print(f"Trazida: {blob.name}")

    print(f"{len(blobs)} nota(s) trazida(s) para 00 - Entrada/")


if __name__ == "__main__":
    pull_inbox()