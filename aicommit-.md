Certo. Vamos fazer do jeito utilizável no dia a dia:

* **instala 1 vez no Linux**
* funciona em **qualquer repo git**
* troca entre **Codex** e **OpenCode**
* pode ser disparado por **comando** ou por **atalho global da IDE**

Os pontos que estou usando como base são: o **Codex CLI** suporta execução não interativa com `codex exec` e gravação da última resposta com `--output-last-message`; o **OpenCode** suporta execução não interativa com `opencode run` e seleção de modelo com `--model`; e o VS Code tem **User Tasks** globais acessíveis por `Tasks: Open User Tasks`, o que evita `tasks.json` em cada projeto. ([OpenAI Developers][1])

## Estrutura global

Vamos usar isto:

```text
~/.local/bin/ai-commit
~/.config/ai-commit/config.json
```

Assim você não coloca nada dentro dos projetos.

---

## 1) Criar a pasta de config

No terminal:

```bash
mkdir -p ~/.config/ai-commit
mkdir -p ~/.local/bin
```

---

## 2) Criar o arquivo de config global

Crie `~/.config/ai-commit/config.json`:

```json
{
  "provider": "codex",
  "codex_model": "gpt-5.4-mini",
  "opencode_model": "opencode/kimi-k2.6",
  "confirm": true,
  "staged_only": false,
  "max_diff_chars": 120000
}
```

### O que cada campo faz

* `provider`: `"codex"` ou `"opencode"`
* `codex_model`: modelo usado no Codex
* `opencode_model`: modelo usado no OpenCode; o formato `provider/model` é o esperado pela documentação do OpenCode. ([OpenCode][2])
* `confirm`: pergunta antes de commitar
* `staged_only`: se `false`, faz `git add -A`; se `true`, usa só o que já está staged
* `max_diff_chars`: corta diffs gigantes para evitar prompt desnecessariamente enorme

---

## 3) Criar o comando global `ai-commit`

Crie `~/.local/bin/ai-commit` com este conteúdo:

````python
#!/usr/bin/env python3
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "ai-commit" / "config.json"


def eprint(*args):
    print(*args, file=sys.stderr)


def fail(msg, code=1):
    eprint(f"Erro: {msg}")
    sys.exit(code)


def run(cmd, check=True, capture_output=True, text=True, input_text=None):
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture_output,
        text=text,
        input=input_text,
    )


def load_config():
    defaults = {
        "provider": "codex",
        "codex_model": "gpt-5.4",
        "opencode_model": "openai/gpt-5",
        "confirm": True,
        "staged_only": False,
        "max_diff_chars": 120000,
    }

    if not CONFIG_PATH.exists():
        return defaults

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        defaults.update(data)
        return defaults
    except Exception as e:
        fail(f"não consegui ler {CONFIG_PATH}: {e}")


def ensure_binary(name):
    if shutil.which(name) is None:
        fail(f"comando '{name}' não encontrado no PATH.")


def ensure_git_repo():
    try:
        result = run(["git", "rev-parse", "--is-inside-work-tree"])
        if result.stdout.strip() != "true":
            fail("este diretório não está dentro de um repositório git.")
    except subprocess.CalledProcessError:
        fail("este diretório não está dentro de um repositório git.")


def git_add_all():
    run(["git", "add", "-A"])


def get_diff():
    result = run(["git", "diff", "--cached"], check=False)
    return result.stdout


def build_prompt(diff_text):
    return f"""
You generate git commit messages.

Task:
Analyze the git diff below and return exactly one commit message.

Rules:
- Output exactly one line.
- No quotes.
- No markdown.
- No code fence.
- No explanations.
- Use Conventional Commits.
- Be concise and specific.
- Write in English.
- Prefer: type(scope): summary
- If scope is unclear, use: type: summary
- Choose the most accurate type among:
  feat, fix, refactor, chore, docs, test, ci, build, perf

Git diff:
{diff_text}
""".strip()


def sanitize_message(raw):
    text = raw.strip()

    text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    text = text.strip()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        fail("a IA não retornou nenhuma mensagem.")

    msg = lines[0]
    msg = msg.strip().strip('"').strip("'").strip()
    msg = re.sub(r"^(commit message|message)\s*:\s*", "", msg, flags=re.I).strip()

    if not msg:
        fail("a mensagem de commit ficou vazia.")

    if len(msg) > 120:
        msg = msg[:120].rstrip()

    return msg


def generate_with_codex(prompt, model):
    ensure_binary("codex")

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as tmp:
        out_path = tmp.name

    try:
        cmd = [
            "codex", "exec",
            "--model", model,
            "--skip-git-repo-check",
            "--sandbox", "read-only",
            "--output-last-message", out_path,
            "-"
        ]

        proc = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True
        )

        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            fail(f"falha ao executar Codex: {err}")

        content = Path(out_path).read_text(encoding="utf-8").strip()
        if not content:
            fail("o Codex não retornou conteúdo.")
        return content
    finally:
        try:
            os.remove(out_path)
        except OSError:
            pass


def generate_with_opencode(prompt, model):
    ensure_binary("opencode")

    cmd = [
        "opencode", "run",
        "--model", model,
        prompt
    ]

    proc = subprocess.run(
        cmd,
        text=True,
        capture_output=True
    )

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        fail(f"falha ao executar OpenCode: {err}")

    content = proc.stdout.strip()
    if not content:
        fail("o OpenCode não retornou conteúdo.")
    return content


def git_commit(message):
    proc = subprocess.run(["git", "commit", "-m", message], text=True)
    if proc.returncode != 0:
        fail("o git commit falhou.", proc.returncode)


def parse_args():
    args = sys.argv[1:]
    parsed = {
        "provider": None,
        "no_confirm": False,
        "yes": False,
        "staged_only": None,
    }

    i = 0
    while i < len(args):
        arg = args[i]

        if arg == "--provider":
            if i + 1 >= len(args):
                fail("faltou valor para --provider")
            parsed["provider"] = args[i + 1].strip().lower()
            i += 2
            continue

        if arg == "--no-confirm":
            parsed["no_confirm"] = True
            i += 1
            continue

        if arg == "--yes":
            parsed["yes"] = True
            i += 1
            continue

        if arg == "--staged-only":
            parsed["staged_only"] = True
            i += 1
            continue

        if arg == "--all":
            parsed["staged_only"] = False
            i += 1
            continue

        fail(f"argumento desconhecido: {arg}")

    return parsed


def main():
    cfg = load_config()
    cli = parse_args()

    provider = cli["provider"] or cfg["provider"]
    confirm = cfg["confirm"] and not cli["no_confirm"]
    staged_only = cfg["staged_only"] if cli["staged_only"] is None else cli["staged_only"]
    max_diff_chars = int(cfg["max_diff_chars"])

    ensure_git_repo()

    if not staged_only:
        git_add_all()

    diff_text = get_diff()
    if not diff_text.strip():
        print("Nenhuma mudança staged para commit.")
        sys.exit(0)

    if len(diff_text) > max_diff_chars:
        diff_text = diff_text[:max_diff_chars] + "\n\n[diff truncated]\n"

    prompt = build_prompt(diff_text)

    if provider == "codex":
        raw = generate_with_codex(prompt, cfg["codex_model"])
    elif provider == "opencode":
        raw = generate_with_opencode(prompt, cfg["opencode_model"])
    else:
        fail("provider inválido. Use 'codex' ou 'opencode'.")

    message = sanitize_message(raw)

    print("\nMensagem gerada:")
    print(f"  {message}\n")

    if confirm and not cli["yes"]:
        answer = input("Confirmar commit? [Y/n]: ").strip().lower()
        if answer in {"n", "no"}:
            print("Cancelado.")
            sys.exit(0)

    git_commit(message)
    print("Commit realizado com sucesso.")


if __name__ == "__main__":
    main()
````

---

## 4) Dar permissão e colocar no PATH

```bash
chmod +x ~/.local/bin/ai-commit
```

Adicione isto ao seu `~/.bashrc` ou `~/.zshrc` se ainda não existir:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Depois recarregue:

```bash
source ~/.bashrc
```

ou:

```bash
source ~/.zshrc
```

Teste:

```bash
ai-commit --help
```

Observação: o script acima não implementa `--help`, então ele vai reclamar de argumento inválido se você passar isso. O teste real melhor é:

```bash
which ai-commit
```

e depois, dentro de um repo git:

```bash
ai-commit
```

---

## 5) Uso no dia a dia

### provider padrão do config

```bash
ai-commit
```

### forçar Codex

```bash
ai-commit --provider codex
```

### forçar OpenCode

```bash
ai-commit --provider opencode
```

### usar só arquivos já staged

```bash
ai-commit --staged-only
```

### pular confirmação

```bash
ai-commit --no-confirm --yes
```

---

## 6) Como trocar entre Codex e OpenCode

Você pode trocar de dois jeitos.

### Permanente

Edite:

`~/.config/ai-commit/config.json`

Exemplo:

```json
{
  "provider": "opencode",
  "codex_model": "gpt-5.4",
  "opencode_model": "openai/gpt-5",
  "confirm": true,
  "staged_only": false,
  "max_diff_chars": 120000
}
```

### Só naquela execução

```bash
ai-commit --provider codex
```

ou

```bash
ai-commit --provider opencode
```

O Codex CLI documenta `codex exec` e `--output-last-message`; o OpenCode documenta `opencode run` e a prioridade do `--model` na resolução do modelo. ([OpenAI Developers][1])

---

## 7) Disparar com 1 clique no VS Code / Windsurf sem configurar por projeto

O caminho certo é usar **User Tasks**, que são globais no VS Code. A documentação do VS Code indica abrir isso com `Tasks: Open User Tasks`. ([Visual Studio Code][3])

Abra a palette e rode:

`Tasks: Open User Tasks`

No arquivo global de tasks, coloque:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "AI Commit",
      "type": "shell",
      "command": "ai-commit",
      "options": {
        "cwd": "${workspaceFolder}"
      },
      "presentation": {
        "reveal": "always",
        "panel": "dedicated",
        "focus": true
      },
      "problemMatcher": []
    },
    {
      "label": "AI Commit (OpenCode)",
      "type": "shell",
      "command": "ai-commit --provider opencode",
      "options": {
        "cwd": "${workspaceFolder}"
      },
      "presentation": {
        "reveal": "always",
        "panel": "dedicated",
        "focus": true
      },
      "problemMatcher": []
    },
    {
      "label": "AI Commit (Codex)",
      "type": "shell",
      "command": "ai-commit --provider codex",
      "options": {
        "cwd": "${workspaceFolder}"
      },
      "presentation": {
        "reveal": "always",
        "panel": "dedicated",
        "focus": true
      },
      "problemMatcher": []
    }
  ]
}
```

Como `cwd` usa `${workspaceFolder}`, a task roda no projeto aberto. O VS Code documenta o uso de variáveis como `${workspaceFolder}` em tasks e launch configs. ([Visual Studio Code][4])

---

## 8) Colocar atalho de teclado global

No `keybindings.json` do usuário:

```json
[
  {
    "key": "ctrl+alt+g",
    "command": "workbench.action.tasks.runTask",
    "args": "AI Commit"
  }
]
```

Opcionalmente, um atalho para cada provider:

```json
[
  {
    "key": "ctrl+alt+g",
    "command": "workbench.action.tasks.runTask",
    "args": "AI Commit"
  },
  {
    "key": "ctrl+alt+o",
    "command": "workbench.action.tasks.runTask",
    "args": "AI Commit (OpenCode)"
  },
  {
    "key": "ctrl+alt+c",
    "command": "workbench.action.tasks.runTask",
    "args": "AI Commit (Codex)"
  }
]
```

---

## 9) O fluxo final fica assim

Você abre qualquer projeto git na IDE e aperta:

* `Ctrl + Alt + G`

ou roda no terminal:

* `ai-commit`

O script:

* detecta se está em repo git
* faz `git add -A` por padrão
* lê o diff staged
* chama Codex ou OpenCode
* gera a mensagem
* mostra para você
* faz o `git commit`

---

## 10) Duas melhorias que valem muito a pena

### A. comando para alternar provider rápido

Você pode criar aliases:

```bash
alias aic='ai-commit --provider codex'
alias aio='ai-commit --provider opencode'
```

### B. modo só staged

Para quando você separou mudanças manualmente:

```bash
alias aics='ai-commit --provider codex --staged-only'
```

---

## 11) O que eu manteria assim mesmo

Eu manteria a **confirmação** antes do commit. Esse é o melhor ponto de equilíbrio entre velocidade e controle. Se você tirar isso, um diff ruim ou uma resposta ruim da IA polui teu histórico muito rápido.

## 12) Se der erro em algum provider

Os pontos mais comuns são:

* `codex` não está no `PATH`
* `opencode` não está no `PATH`
* você não está autenticado em um deles
* modelo configurado no arquivo não existe naquele provider
* o repo não tem nada staged

Se quiser, no próximo passo eu monto uma **v2 melhorada** com:

* `--push`
* `--dry-run`
* exclusão de arquivos irrelevantes
* e fallback automático: tenta Codex, se falhar usa OpenCode.

[1]: https://developers.openai.com/codex/cli/reference?utm_source=chatgpt.com "Command line options – Codex CLI"
[2]: https://opencode.ai/docs/models/?utm_source=chatgpt.com "Models"
[3]: https://code.visualstudio.com/docs/debugtest/tasks?utm_source=chatgpt.com "Integrate with External Tools via Tasks"
[4]: https://code.visualstudio.com/docs/reference/variables-reference?utm_source=chatgpt.com "Variables reference"
