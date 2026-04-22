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
        details = proc.stderr.strip()
        hint = f" Details: {details}" if details else ""
        raise AICommitError(
            "OpenCode returned no content. Check the model id and authentication."
            f" Try --model opencode-go/kimi-k2.5, opencode-go/glm-5, "
            f"opencode-go/minimax-m2.5, or opencode-go/qwen3.6-plus.{hint}"
        )
    return content
