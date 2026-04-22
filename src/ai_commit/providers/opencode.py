import shutil
import subprocess

from ..errors import AICommitError


def generate_with_opencode(prompt: str, model: str) -> str:
    if shutil.which("opencode") is None:
        raise AICommitError("Command 'opencode' was not found in PATH.")

    proc = subprocess.run(
        ["opencode", "run", "--model", model, prompt],
        text=True,
        capture_output=True,
    )

    if proc.returncode != 0:
        details = (proc.stderr or proc.stdout or "").strip()
        raise AICommitError(f"OpenCode failed: {details}")

    content = proc.stdout.strip()
    if not content:
        raise AICommitError("OpenCode returned no content.")
    return content
