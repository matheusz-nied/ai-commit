import json
from pathlib import Path
from typing import Any, Dict, Optional

from .errors import AICommitError


CONFIG_PATH = Path.home() / ".config" / "ai-commit" / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "provider": "codex",
    "codex_model": "gpt-5.4",
    "opencode_model": "opencode-go/kimi-k2.5",
    "confirm": True,
    "staged_only": False,
    "max_diff_chars": 120000,
}


def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    config_path = path or CONFIG_PATH
    config = dict(DEFAULT_CONFIG)

    if not config_path.exists():
        return config

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise AICommitError(f"Could not read {config_path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise AICommitError(f"Invalid JSON in {config_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise AICommitError(f"Config file must contain a JSON object: {config_path}")

    config.update(data)
    return config
