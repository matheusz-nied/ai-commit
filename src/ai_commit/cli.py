import argparse
import sys
from typing import Any, Dict, Optional, Sequence

from . import __version__
from .config import load_config
from .errors import AICommitError
from .git_utils import add_all, commit, ensure_git_repo, get_cached_diff, get_cached_name_status
from .messages import sanitize_message
from .preview import render_preview
from .prompts import build_prompt
from .providers import generate_with_codex, generate_with_opencode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-commit",
        description="Generate a Conventional Commit message from your git diff.",
    )
    parser.add_argument("--provider", choices=["codex", "opencode"], help="AI provider to use.")

    staging = parser.add_mutually_exclusive_group()
    staging.add_argument(
        "--staged-only",
        dest="staged_only",
        action="store_true",
        help="Use only changes that are already staged.",
    )
    staging.add_argument(
        "--all",
        dest="staged_only",
        action="store_false",
        help="Stage all changes with git add -A before generating the commit.",
    )
    parser.set_defaults(staged_only=None)

    parser.add_argument("--yes", action="store_true", help="Accept the generated message without prompting.")
    parser.add_argument("--no-confirm", action="store_true", help="Do not ask before creating the commit.")
    parser.add_argument("--dry-run", action="store_true", help="Show the preview without creating a commit.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def resolve_bool(value: Any, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
    raise AICommitError(f"Config value '{name}' must be a boolean.")


def resolve_int(value: Any, name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise AICommitError(f"Config value '{name}' must be an integer.") from exc
    if parsed <= 0:
        raise AICommitError(f"Config value '{name}' must be greater than zero.")
    return parsed


def generate_message(provider: str, prompt: str, config: Dict[str, Any]) -> str:
    if provider == "codex":
        return generate_with_codex(prompt, str(config["codex_model"]))
    if provider == "opencode":
        return generate_with_opencode(prompt, str(config["opencode_model"]))
    raise AICommitError("Invalid provider. Use 'codex' or 'opencode'.")


def run(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config()

    provider = args.provider or str(config["provider"])
    if provider not in {"codex", "opencode"}:
        raise AICommitError("Invalid provider. Use 'codex' or 'opencode'.")

    staged_only = (
        resolve_bool(config["staged_only"], "staged_only")
        if args.staged_only is None
        else args.staged_only
    )
    confirm = resolve_bool(config["confirm"], "confirm") and not args.no_confirm
    max_diff_chars = resolve_int(config["max_diff_chars"], "max_diff_chars")

    ensure_git_repo()

    if not staged_only:
        add_all()

    diff_text = get_cached_diff()
    if not diff_text.strip():
        print("No staged changes to commit.")
        return 0

    if len(diff_text) > max_diff_chars:
        diff_text = diff_text[:max_diff_chars].rstrip() + "\n\n[diff truncated]\n"

    files = get_cached_name_status()
    prompt = build_prompt(diff_text)
    raw_message = generate_message(provider, prompt, config)
    message = sanitize_message(raw_message)

    print()
    print(render_preview(files, message))
    print()

    if args.dry_run:
        print("Dry run: commit not created.")
        return 0

    if confirm and not args.yes:
        answer = input("Create commit? [Y/n]: ").strip().lower()
        if answer in {"n", "no"}:
            print("Cancelled.")
            return 0

    commit(message)
    print("Commit created.")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        return run(argv)
    except AICommitError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
