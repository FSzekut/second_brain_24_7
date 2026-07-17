# Roadmap

Ideias capturadas via app/vault, ainda não implementadas.

## Painel de alertas

Tela dedicada para exibir alertas de datas importantes e próximos passos pendentes em várias frentes — algo como um dashboard rápido ao abrir o app, em vez de precisar perguntar pro chat.

## Acesso remoto ao Claude Code via app

Ideia original (usar o link deste app pra acionar/controlar o Claude Code do notebook remotamente) **não é viável como pensado** — pesquisado e confirmado: não existe `/remote`; o que existe é o *Remote Control* nativo do Claude Code (`claude remote-control` / `/remote-control`), que conecta a sessão já rodando no notebook ao claude.ai/code ou app mobile, mas fala só com o backend da própria Anthropic — um app de terceiros (este Streamlit) não consegue interceptar essa conexão, e a sessão local precisa já estar de pé.

Alternativas reais a avaliar, se ainda fizer sentido:
- **Channels** (plugin Telegram/Discord do Claude Code) em vez de app web próprio, pra disparar o Claude Code de qualquer lugar
- **RemoteTrigger + webhook**: este app dispara uma Routine na nuvem via webhook — mas isso cria uma sessão nova, não continua a sessão local existente
