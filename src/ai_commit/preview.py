import os
import sys
from typing import Iterable, Optional, TextIO

from .git_utils import ChangedFile


STATUS_COLORS = {
    "A": "\033[32m",
    "M": "\033[33m",
    "D": "\033[31m",
    "R": "\033[36m",
    "C": "\033[36m",
}
RESET = "\033[0m"
BOLD = "\033[1m"


def supports_color(stream: TextIO = sys.stdout) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return hasattr(stream, "isatty") and stream.isatty()


def render_preview(
    files: Iterable[ChangedFile],
    message: str,
    color: Optional[bool] = None,
    stream: TextIO = sys.stdout,
) -> str:
    use_color = supports_color(stream) if color is None else color
    lines = ["Files changed:"]

    file_list = list(files)
    if file_list:
        for item in file_list:
            status = item.status
            if use_color:
                color_code = STATUS_COLORS.get(status, "")
                status = f"{color_code}{status}{RESET}" if color_code else status
            lines.append(f"  {status} {item.path}")
    else:
        lines.append("  (none)")

    suggested = f"{BOLD}{message}{RESET}" if use_color else message
    lines.extend(["", "Suggested:", f"  {suggested}"])

    return "\n".join(lines)
