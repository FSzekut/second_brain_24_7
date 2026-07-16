from datetime import datetime
from google.cloud import storage

INBOX_BUCKET = "meu-claude-ui-2026-notes-inbox"


def save_note_to_inbox(title, content):
    client = storage.Client()
    bucket = client.bucket(INBOX_BUCKET)

    now = datetime.now()
    safe_title = title.strip().replace(" ", "-") if title else "nota"
    filename = f"{now.strftime('%Y-%m-%d-%H%M%S')}-{safe_title}.md"

    frontmatter = (
        "---\n"
        "tipo: captura-app\n"
        f"data: {now.strftime('%Y-%m-%d %H:%M')}\n"
        "origem: meu-claude-ui\n"
        "---\n\n"
    )
    body = frontmatter + (f"# {title}\n\n" if title else "") + content

    bucket.blob(filename).upload_from_string(body, content_type="text/markdown")
    return filename