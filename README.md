# ai-commit

Generate clean git commit messages from your staged diff using Codex or OpenCode.

`ai-commit` is a small Python CLI that works in any git repository. It stages changes by default, asks an AI provider for a Conventional Commit message, shows a preview, and then asks before creating the commit.

## Preview

```text
Files changed:
  M src/foo.ts
  A tests/foo.test.ts

Suggested:
  feat(cli): add provider selection
```

## Install

For local development, use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

If you want to install the CLI from this local checkout as an app, use pipx:

```bash
pipx install -e .
```

After publishing to PyPI, the intended public install path is:

```bash
pipx install ai-commit
```

## Usage

Create a commit from all current changes:

```bash
ai-commit
```

Use only files that are already staged:

```bash
ai-commit --staged-only
```

Show the preview without creating a commit:

```bash
ai-commit --dry-run
```

Force a provider for one run:

```bash
ai-commit --provider codex
ai-commit --provider opencode
```

Skip the confirmation prompt:

```bash
ai-commit --yes
```

## Configuration

Optional global config file:

```text
~/.config/ai-commit/config.json
```

Example:

```json
{
  "provider": "codex",
  "codex_model": "gpt-5.4",
  "opencode_model": "openai/gpt-5",
  "confirm": true,
  "staged_only": false,
  "max_diff_chars": 120000
}
```

By default, `ai-commit` runs `git add -A` before reading the staged diff. Set `"staged_only": true` or pass `--staged-only` to commit only changes you staged manually.

## Providers

For Codex, the `codex` command must be available in `PATH`.

For OpenCode, the `opencode` command must be available in `PATH`.

## VS Code or Windsurf

You can call the CLI from a global user task:

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
    }
  ]
}
```

## Development

Run tests:

```bash
python3 -m unittest discover -s tests
```

Check the CLI:

```bash
ai-commit --version
```
