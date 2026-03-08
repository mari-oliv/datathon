# CHANGELOG — alterações recentes

Resumo das mudanças feitas para facilitar execução e robustez do projeto:

- Dockerfile
  - Instalado `bash` e `ca-certificates` na imagem runtime para evitar erros de `/bin/bash` ausente.
  - Ajustado `CMD` para usar `bash -c` com o caminho absoluto do entrypoint.

- scripts/docker_entrypoint.sh
  - Adicionado `#!/usr/bin/env bash` (shebang) para garantir o interpretador correto.

- monitoring/dashboard.py
  - Garantido `sys.path` para permitir `import src.*` dentro do container.
  - Adicionadas transformações para criar `Fase_ideal_num` e `gap_fase` quando ausentes.
  - Garantido preenchimento das `risk_cols` com as médias do modelo antes de aplicar centroids.
  - Restaurada exibição da tabela de estatísticas por feature (`st.dataframe(stats_df)`).
  - Removido o gráfico de delta (conforme solicitado).

- Makefile
  - Adicionado `Makefile` com alvos: `install`, `start`, `start-dev`, `stop`, `build`, `run`, `test`, `logs`, `clean`.
  - `make start` tenta instalar/iniciar local e faz fallback automático para container; se container falhar, executa `start-dev`.
  - `make install` atualiza `pip/setuptools/wheel` antes de instalar dependências.

- README.md
  - Substituído por versão sucinta em português com: motivação, problema que resolve, rotas, portas, quick-start e uso do `Makefile`.

- requirements.txt
  - Fixadas versões das dependências principais para reduzir variação entre máquinas.

- Correções menores
  - Ajustes e comentários em `scripts/run_monitor.sh` e `Dockerfile` para melhorar mensagens e estabilidade.

Como validar
- `make start` — comando recomendado para iniciar tudo (tenta local e faz fallback quando necessário).
- `make logs` — ver logs de API e Streamlit.
- `make test` — executar testes (pytest).

Se quiser que eu documente os passos para publicar uma release (ou crie um `RELEASE.md`), me avise.