# Roadmap

Ideias capturadas via app/vault, ainda não implementadas.

## Painel de alertas

Tela dedicada para exibir alertas de datas importantes e próximos passos pendentes em várias frentes — algo como um dashboard rápido ao abrir o app, em vez de precisar perguntar pro chat.

**Desenho definido (2026-07-18)**: dado estruturado, não extração via LLM — consistente com a decisão já tomada de sincronização em lote (ver "Decisões de design" no README). Custo de API para essa feature: zero; só custo de nuvem (leitura de um JSON pequeno no Cloud Storage).

Schema novo de frontmatter, aplicado só em notas marcadas deliberadamente como tarefa/compromisso:
```yaml
tipo: tarefa
prazo: 2026-08-01
projeto: nome-do-projeto  # opcional, pra agrupar no painel
status: pendente          # pendente | concluído
```

Arquitetura (mesmo padrão de `build_index.py`/`pull_inbox.py`):
1. `scripts/build_alerts.py` (novo, roda localmente) — varre o vault, filtra notas com `tipo: tarefa` e `status: pendente`, ordena por `prazo`, gera `alerts.json`.
2. `alerts.json` sobe manualmente para um bucket no Cloud Storage (mesmo bucket do índice RAG, ou um novo — a decidir).
3. Painel no app Streamlit lê o `alerts.json` direto, sem chamada a LLM — ordenado por proximidade do prazo, destacando o que está vencendo.

Ainda não implementado — próximo passo é montar o plano de implementação (arquivos a criar/editar, decisão sobre bucket).

## Acesso remoto ao Claude Code via app

Ideia original (usar o link deste app pra acionar/controlar o Claude Code do notebook remotamente) **não é viável como pensado** — pesquisado e confirmado: não existe `/remote`; o que existe é o *Remote Control* nativo do Claude Code (`claude remote-control` / `/remote-control`), que conecta a sessão já rodando no notebook ao claude.ai/code ou app mobile, mas fala só com o backend da própria Anthropic — um app de terceiros (este Streamlit) não consegue interceptar essa conexão, e a sessão local precisa já estar de pé.

Também avaliado e descartado pelo mesmo motivo: **Channels** (plugin oficial `telegram@claude-plugins-official`/Discord) — faz ponte de mensagens entre Telegram/Discord e uma sessão local, mas exige o **notebook ligado com sessão já rodando** (`claude --channels ...`), a mesma limitação do Remote Control. Não resolve "trabalhar fora de casa sem o notebook aberto".

**Conclusão**: nenhuma ferramenta que depende de uma sessão local resolve o objetivo real (continuar trabalhando sem o notebook fisicamente ligado). O caminho seria abandonar a dependência do notebook:
- **Claude Code on the web** — sessão roda inteiramente na nuvem da Anthropic
- **Routines agendadas** (`/schedule` + RemoteTrigger) — dispara sessões na nuvem por conta própria

Sem próximo passo definido ainda — decisão de arquitetura em aberto, não implementação imediata.
