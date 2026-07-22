# Operations Runbook

This runbook documents the local maintenance commands for keeping the deployed
app in sync with the Obsidian vault.

The full vault never runs inside Cloud Run. The local scripts read markdown files
from disk, generate derived JSON artifacts, and then those artifacts are uploaded
to Cloud Storage.

## Safety Model

- `vault_index.json` contains chunks and embeddings derived from personal notes.
- `alerts.json` contains structured task metadata derived from personal notes.
- Both files are generated locally and intentionally ignored by git.
- Do not commit `.env`, `vault_index.json`, `alerts.json`, raw vault exports, or
  downloaded notes.
- Notes marked with `classificacao: corporativo` are skipped by both the RAG
  indexer and the alerts generator.

## Prerequisites

Run commands from the project root:

```bash
cd /path/to/second_brain_24_7
```

Install dependencies and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure local environment variables in `.env`:

```bash
NVIDIA_API_KEY=nvapi-...
VAULT_PATH=/absolute/path/to/your/Obsidian/vault
```

`VAULT_PATH` is optional if your vault lives at the script default path, but it
should be set explicitly on any other machine.

Authenticate the Google Cloud CLI with an account that can write to the index
bucket and read/delete from the inbox bucket:

```bash
gcloud auth login
gcloud config set project <your-gcp-project-id>
```

## Update the RAG Index

Use this after adding or editing notes that the app should be able to retrieve.

```bash
python scripts/build_index.py
gcloud storage cp vault_index.json gs://meu-claude-ui-2026-rag-index/vault_index.json
```

What happens:

1. `scripts/build_index.py` scans markdown files under `VAULT_PATH`.
2. It skips `.obsidian`, `09 - Sistema`, `.git`, and notes marked
   `classificacao: corporativo`.
3. It chunks note text, generates NVIDIA NV-Embed embeddings, and writes
   `vault_index.json`.
4. The upload command publishes the generated index to the Cloud Storage bucket
   read by the deployed app.

The deployed app loads `vault_index.json` from the bucket on startup and uses it
for cosine-similarity retrieval in `src/rag.py`.

## Update the Alerts Panel

Use this after creating, changing, or completing dated task notes.

```bash
python scripts/build_alerts.py
gcloud storage cp alerts.json gs://meu-claude-ui-2026-rag-index/alerts.json
```

Task notes must use this frontmatter:

```yaml
tipo: tarefa
titulo: Human-readable title
prazo: 2026-08-01
projeto: project-name
status: pendente
```

When a task is done, remove the task frontmatter instead of changing the status
to `concluído`. The alerts generator only looks for `tipo: tarefa` with
`status: pendente`.

## Pull Captured Notes Back Into the Vault

Use this after capturing notes through the app while away from the local vault.

```bash
python scripts/pull_inbox.py
```

What happens:

1. The script lists blobs from the app inbox bucket.
2. Each blob is downloaded into `00 - Entrada/` under `VAULT_PATH`.
3. The blob is deleted from the bucket after a successful local write.

There is no symmetric `push_inbox.py`: app-captured notes are written to the
inbox bucket by the deployed app, then pulled back into the vault locally.

## Common Maintenance Flow

After a productive vault session:

```bash
python scripts/build_index.py
gcloud storage cp vault_index.json gs://meu-claude-ui-2026-rag-index/vault_index.json

python scripts/build_alerts.py
gcloud storage cp alerts.json gs://meu-claude-ui-2026-rag-index/alerts.json
```

After using the remote note capture feature:

```bash
python scripts/pull_inbox.py
```

## Troubleshooting

If `build_index.py` fails with an authentication error, check:

- `.env` contains `NVIDIA_API_KEY`.
- The virtual environment is active.
- `python-dotenv` is installed through `requirements.txt`.

If upload fails, check:

- `gcloud auth login` has been run.
- `gcloud config get-value project` points at the expected project.
- The current Google account has write access to the index bucket.

If `pull_inbox.py` fails, check:

- The current Google account can read and delete objects in the inbox bucket.
- `VAULT_PATH` points at a writable local vault path.
- `00 - Entrada/` exists under the vault.
