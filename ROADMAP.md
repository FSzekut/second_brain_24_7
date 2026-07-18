# Roadmap

Ideias capturadas via app/vault, ainda não implementadas.

## ~~Painel de alertas~~ ✅ Implementado (2026-07-18)

Dashboard de tarefas/prazos pendentes, via dado estruturado (frontmatter `tipo: tarefa`/`prazo`/`projeto`/`status`), sem nenhuma chamada de LLM — documentado em detalhe no [README](README.md#painel-de-alertas-tarefas-e-prazos) ("Funcionalidades" e "Decisões de design"). Usa o mesmo bucket do índice RAG.

## Acesso remoto ao Claude Code via app

Ideia original (usar o link deste app pra acionar/controlar o Claude Code do notebook remotamente) **não é viável como pensado** — pesquisado e confirmado: não existe `/remote`; o que existe é o *Remote Control* nativo do Claude Code (`claude remote-control` / `/remote-control`), que conecta a sessão já rodando no notebook ao claude.ai/code ou app mobile, mas fala só com o backend da própria Anthropic — um app de terceiros (este Streamlit) não consegue interceptar essa conexão, e a sessão local precisa já estar de pé.

Também avaliado e descartado pelo mesmo motivo: **Channels** (plugin oficial `telegram@claude-plugins-official`/Discord) — faz ponte de mensagens entre Telegram/Discord e uma sessão local, mas exige o **notebook ligado com sessão já rodando** (`claude --channels ...`), a mesma limitação do Remote Control. Não resolve "trabalhar fora de casa sem o notebook aberto".

**Conclusão**: nenhuma ferramenta que depende de uma sessão local resolve o objetivo real (continuar trabalhando sem o notebook fisicamente ligado). O caminho seria abandonar a dependência do notebook:
- **Claude Code on the web** — sessão roda inteiramente na nuvem da Anthropic
- **Routines agendadas** (`/schedule` + RemoteTrigger) — dispara sessões na nuvem por conta própria

Sem próximo passo definido ainda — decisão de arquitetura em aberto, não implementação imediata.
