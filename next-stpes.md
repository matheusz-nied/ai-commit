 # Próximos Passos Do ai-commit

  ## Summary

  O projeto já tem o V1 do CLI implementado: pacote Python, preview bonito, providers Codex/OpenCode, README, testes e CI. Agora o foco deve ser validar em uso real, preparar publicação e só depois criar a extensão VS Code.

  Estado atual: os arquivos novos ainda estão untracked no git.

  ## Próximas Ações

  1. Testar localmente em modo editável
      - Rodar python3 -m pip install -e .
      - Confirmar ai-commit --version
      - Em um repo de teste, rodar ai-commit --dry-run --staged-only
      - Depois testar ai-commit --dry-run
  2. Fazer o primeiro commit do projeto
      - Revisar README.md, pyproject.toml, src/ e tests/
  3. Preparar publicação no GitHub
      - Adicionar descrição curta, tópicos e README revisado
      - Confirmar que o CI roda verde no GitHub Actions
  4. Preparar PyPI
      - Criar workflow de release com build de pacote
      - Usar Trusted Publishing/OIDC, sem token fixo
      - Publicar primeiro como 0.1.0
      - Validar instalação com pipx install ai-commit
  5. Só depois criar extensão VS Code
      - Criar extensão mínima que chama o CLI instalado
      - Comandos: AI Commit, AI Commit Dry Run, AI Commit Staged Only
      - Empacotar primeiro como .vsix
      - Publicar no Marketplace depois de validar com usuários reais

  ## Test Plan

  - Antes do commit inicial:
      - PYTHONPATH=src python3 -m unittest discover -s tests
      - PYTHONPATH=src python3 -m py_compile src/ai_commit/*.py src/ai_commit/providers/*.py
      - PYTHONPATH=src python3 -m ai_commit --help
  - Antes de publicar:
      - instalar com pip install -e .
      - testar ai-commit --dry-run --staged-only
      - testar provider real com Codex ou OpenCode autenticado
      - testar em repo com arquivos A, M, D e rename

  ## Assumptions

  - Manter o padrão atual escolhido: ai-commit faz git add -A.
  - --dry-run continua gerando mensagem real com IA, mas não cria commit.
  - A extensão VS Code não deve duplicar lógica; ela deve chamar o CLI.
  - Publicação PyPI deve usar Trusted Publishing, conforme docs oficiais do PyPI.
  - Extensão VS Code deve seguir package.json manifest e empacotamento via vsce.

  Referências: PyPI Trusted Publishing (https://docs.pypi.org/trusted-publishers/), PyPI publish action (https://docs.pypi.org/trusted-publishers/using-a-publisher/), VS Code Publishing Extensions
  (https://code.visualstudio.com/api/working-with-extensions/publishing-extension), VS Code Extension Manifest (https://code.visualstudio.com/api/references/extension-manifest).