def build_prompt(diff_text: str) -> str:
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
