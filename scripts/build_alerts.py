import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

VAULT_PATH = Path(os.getenv("VAULT_PATH", "/mnt/c/Users/ferna/OneDrive/Obsidian"))
SKIP_DIRS = {".obsidian", "09 - Sistema", ".git"}


def should_skip(relative_path):
    return any(part in SKIP_DIRS for part in relative_path.parts)


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    frontmatter = {}
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip().strip('"')
    return frontmatter


def build_alerts():
    alerts = []
    for path in VAULT_PATH.rglob("*.md"):
        if should_skip(path.relative_to(VAULT_PATH)):
            continue
        frontmatter = parse_frontmatter(path.read_text(encoding="utf-8"))
        if frontmatter.get("classificacao") == "corporativo":
            continue
        if frontmatter.get("tipo") != "tarefa" or frontmatter.get("status") != "pendente":
            continue
        prazo = frontmatter.get("prazo")
        if not prazo:
            continue
        alerts.append({
            "titulo": path.stem,
            "prazo": prazo,
            "projeto": frontmatter.get("projeto", ""),
            "source": str(path.relative_to(VAULT_PATH)),
        })

    alerts.sort(key=lambda a: a["prazo"])

    with open("alerts.json", "w", encoding="utf-8") as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)
    print(f"Alertas salvos: {len(alerts)} tarefa(s) pendente(s) em alerts.json")


if __name__ == "__main__":
    build_alerts()
