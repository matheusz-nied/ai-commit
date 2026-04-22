import subprocess
from dataclasses import dataclass
from typing import List, Sequence

from .errors import AICommitError


@dataclass(frozen=True)
class ChangedFile:
    status: str
    path: str


def run_git(args: Sequence[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        check=check,
        capture_output=True,
        text=True,
    )


def ensure_git_repo() -> None:
    try:
        result = run_git(["rev-parse", "--is-inside-work-tree"])
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AICommitError("This directory is not inside a git repository.") from exc

    if result.stdout.strip() != "true":
        raise AICommitError("This directory is not inside a git repository.")


def add_all() -> None:
    try:
        run_git(["add", "-A"])
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AICommitError("Failed to stage changes with git add -A.") from exc


def get_cached_diff() -> str:
    try:
        result = run_git(["diff", "--cached"], check=False)
    except OSError as exc:
        raise AICommitError("Failed to read staged diff.") from exc
    return result.stdout


def get_cached_name_status() -> List[ChangedFile]:
    try:
        result = run_git(["diff", "--cached", "--name-status"], check=False)
    except OSError as exc:
        raise AICommitError("Failed to read staged files.") from exc
    return parse_name_status(result.stdout)


def parse_name_status(output: str) -> List[ChangedFile]:
    files: List[ChangedFile] = []

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split("\t")
        status = parts[0][:1]

        if status in {"R", "C"} and len(parts) >= 3:
            path = f"{parts[1]} -> {parts[2]}"
        elif len(parts) >= 2:
            path = parts[1]
        else:
            path = line

        files.append(ChangedFile(status=status, path=path))

    return files


def commit(message: str) -> None:
    try:
        result = subprocess.run(["git", "commit", "-m", message], text=True)
    except OSError as exc:
        raise AICommitError("Failed to run git commit.") from exc

    if result.returncode != 0:
        raise AICommitError("git commit failed.")
