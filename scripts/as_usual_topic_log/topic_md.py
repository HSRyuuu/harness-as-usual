"""topic.md rendering and low-churn update helpers."""

from __future__ import annotations

from pathlib import Path

from .paths import topic_md_path


def render_topic_md(topic_name: str, initial_request: str, summary: str, timestamp: str, actor: str) -> str:
    boundary = summary or "Not narrowed beyond the initial request yet."
    return (
        "# Topic\n\n"
        "## Initial Request\n\n"
        f"{initial_request or 'Not recorded.'}\n\n"
        "## Topic Boundary\n\n"
        f"{boundary}\n\n"
        "## Agent Resume Notes\n\n"
        "- Read `topic.md` first for durable context.\n"
        "- Use `audit.jsonl` and `scripts/topic-log.py status --json` for current phase, next action, and evidence.\n\n"
        "## Durable Decisions\n\n"
        "- None recorded yet.\n\n"
        "## Constraints\n\n"
        "- Do not treat this file as a progress ledger.\n"
        "- Record high-churn progress and verification in `audit.jsonl` through `scripts/topic-log.py`.\n\n"
        "## Artifact Index\n\n"
        "- `topic.md`: low-churn agent resume context.\n"
        "- `audit.jsonl`: canonical append-only event history.\n"
        "- `question-cN.md`: durable requirements question cycles when needed.\n"
        "- `requirements.md`: approved requirements definition.\n"
        "- `plan.md`: approved execution plan.\n"
        "- `code-review-report.md`: execution review findings when present.\n"
        "- `report.md`: final user-facing handoff summary.\n\n"
        "## Created\n\n"
        f"- Topic: `{topic_name}`\n"
        f"- Actor: `{actor}`\n"
        f"- Timestamp: `{timestamp}`\n"
    )


def append_durable_topic_note(topic: Path, heading: str, summary: str, timestamp: str, actor: str, source: str = "") -> None:
    path = topic_md_path(topic)
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    detail = f"- {summary}"
    if source:
        detail += f" (source: {source})"
    detail += f" [{actor}, {timestamp}]"
    text = path.read_text(encoding="utf-8")
    marker = f"## {heading}"
    if marker not in text:
        text = text.rstrip() + f"\n\n{marker}\n\n{detail}\n"
    else:
        head, tail = text.split(marker, 1)
        next_heading = tail.find("\n## ")
        if next_heading == -1:
            section = tail.rstrip()
            tail_rest = ""
        else:
            section = tail[:next_heading].rstrip()
            tail_rest = tail[next_heading:]
        if "- None recorded yet." in section:
            section = section.replace("- None recorded yet.", detail)
        else:
            section = section + "\n" + detail
        text = head + marker + section + tail_rest
        if not text.endswith("\n"):
            text += "\n"
    path.write_text(text, encoding="utf-8")
