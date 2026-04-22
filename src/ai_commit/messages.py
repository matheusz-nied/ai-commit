import re

from .errors import AICommitError


def sanitize_message(raw: str, max_length: int = 120) -> str:
    text = raw.strip()
    text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    text = text.strip()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise AICommitError("The AI provider returned an empty commit message.")

    message = lines[0].strip()
    message = re.sub(r"^(commit message|message)\s*:\s*", "", message, flags=re.I)
    message = message.strip().strip('"').strip("'").strip()

    if not message:
        raise AICommitError("The generated commit message is empty.")

    if len(message) > max_length:
        message = message[:max_length].rstrip()

    return message
