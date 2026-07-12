"""Core journal operations for AsUsual find-cause issues."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

SCHEMA_VERSION = "as-usual.journal.v1"

REASONING_KINDS = {"finding", "decision", "hypothesis", "interview"}
KINDS = REASONING_KINDS | {"status-change", "approval", "lifecycle"}
ENTRY_STATUSES = {"added", "confirmed", "cancelled"}
LIFECYCLE_EVENTS = {"created", "concluded", "cancelled", "follow-up-linked"}
ACTORS = {"claude", "codex", "user"}
ISSUE_STATUSES = {"open", "concluded", "cancelled"}

JOURNAL_FILE = "journal.jsonl"
PROBLEM_FILE = "problem.md"

PROBLEM_FALLBACK = """# Problem

## Initial Request

{initial_request}

## Current Understanding

(Symptoms, impact, reproduction conditions, and problem boundary. Update freely as the investigation evolves.)

## Background Knowledge

(Domain/background knowledge confirmed through user interviews.)

## Active Hypotheses

(Currently active hypotheses with journal seq references.)
"""


class JournalError(ValueError):
    """Raised for invalid journal operations."""


def now_ts() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def journal_path(issue_dir: Path) -> Path:
    return issue_dir / JOURNAL_FILE


def read_entries(issue_dir: Path) -> list[JsonObject]:
    path = journal_path(issue_dir)
    if not path.exists():
        raise JournalError(f"journal not found: {path}")
    entries: list[JsonObject] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise JournalError(f"invalid json at line {line_no}: {exc}") from exc
    return entries


def next_seq(entries: list[JsonObject]) -> int:
    return max((entry.get("seq", 0) for entry in entries), default=0) + 1


def build_entry(
    entries: list[JsonObject],
    *,
    actor: str,
    kind: str,
    status: str,
    **fields: Any,
) -> JsonObject:
    if actor not in ACTORS:
        raise JournalError(f"invalid actor: {actor} (allowed: {sorted(ACTORS)})")
    if kind not in KINDS:
        raise JournalError(f"invalid kind: {kind} (allowed: {sorted(KINDS)})")
    if status not in ENTRY_STATUSES:
        raise JournalError(f"invalid status: {status} (allowed: {sorted(ENTRY_STATUSES)})")
    entry: JsonObject = {
        "seq": next_seq(entries),
        "ts": now_ts(),
        "actor": actor,
        "kind": kind,
        "status": status,
    }
    entry.update({key: value for key, value in fields.items() if value is not None})
    return entry


def append_entry(issue_dir: Path, entry: JsonObject) -> JsonObject:
    with journal_path(issue_dir).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def problem_template() -> str:
    template_path = Path(__file__).resolve().parents[2] / "templates" / PROBLEM_FILE
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return PROBLEM_FALLBACK


def init_issue(issue_dir: Path, *, initial_request: str, actor: str) -> JsonObject:
    if journal_path(issue_dir).exists():
        raise JournalError(f"journal already exists: {journal_path(issue_dir)}")
    issue_dir.mkdir(parents=True, exist_ok=True)
    entry = build_entry(
        [],
        actor=actor,
        kind="lifecycle",
        status="added",
        event="created",
        content=f"issue created: {issue_dir.name}",
        initialRequest=initial_request,
        schemaVersion=SCHEMA_VERSION,
    )
    append_entry(issue_dir, entry)
    problem = problem_template().replace("{initial_request}", initial_request)
    (issue_dir / PROBLEM_FILE).write_text(problem, encoding="utf-8")
    return entry
