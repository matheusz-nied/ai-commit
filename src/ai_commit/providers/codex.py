import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..errors import AICommitError


def generate_with_codex(prompt: str, model: str) -> str:
    if shutil.which("codex") is None:
        raise AICommitError("Command 'codex' was not found in PATH.")

    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as tmp:
        output_path = tmp.name

    try:
        proc = subprocess.run(
            [
                "codex",
                "exec",
                "--model",
                model,
                "--skip-git-repo-check",
                "--sandbox",
                "read-only",
                "--output-last-message",
                output_path,
                "-",
            ],
            input=prompt,
            text=True,
            capture_output=True,
        )

        if proc.returncode != 0:
            details = (proc.stderr or proc.stdout or "").strip()
            raise AICommitError(f"Codex failed: {details}")

        content = Path(output_path).read_text(encoding="utf-8").strip()
        if not content:
            raise AICommitError("Codex returned no content.")
        return content
    finally:
        try:
            os.remove(output_path)
        except OSError:
            pass
