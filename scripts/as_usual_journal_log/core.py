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


def find_reasoning_entry(entries: list[JsonObject], seq: int) -> JsonObject:
    for entry in entries:
        if entry.get("seq") == seq:
            if entry.get("kind") not in REASONING_KINDS:
                raise JournalError(
                    f"invalid target: seq {seq} is kind {entry.get('kind')}, "
                    f"not a reasoning entry"
                )
            return entry
    raise JournalError(f"invalid target: seq {seq} not found")


def derive_status(entries: list[JsonObject]) -> JsonObject:
    entry_status: dict[int, str] = {}
    issue_status = "open"
    follow_ups: list[str] = []
    last_seq = 0
    for entry in entries:
        last_seq = max(last_seq, entry.get("seq", 0))
        kind = entry.get("kind")
        if kind in REASONING_KINDS:
            entry_status[entry["seq"]] = "added"
        elif kind == "status-change":
            target = entry.get("target")
            if isinstance(target, int) and target in entry_status:
                entry_status[target] = entry.get("status", "added")
        elif kind == "lifecycle":
            event = entry.get("event")
            if event == "concluded":
                issue_status = "concluded"
            elif event == "cancelled":
                issue_status = "cancelled"
            if entry.get("followUp"):
                follow_ups.append(entry["followUp"])

    def bucket(status: str) -> list[int]:
        return sorted(seq for seq, value in entry_status.items() if value == status)

    return {
        "issueStatus": issue_status,
        "active": bucket("added"),
        "confirmed": bucket("confirmed"),
        "cancelled": bucket("cancelled"),
        "followUps": follow_ups,
        "lastSeq": last_seq,
    }


def validate_entries(entries: list[JsonObject]) -> list[str]:
    problems: list[str] = []
    seen_seq: set[int] = set()
    reasoning_seqs: set[int] = set()
    previous_seq = 0
    for index, entry in enumerate(entries, 1):
        seq = entry.get("seq")
        if not isinstance(seq, int) or seq <= 0:
            problems.append(f"entry {index}: invalid seq {seq!r}")
            continue
        if seq in seen_seq:
            problems.append(f"entry {index}: duplicate seq {seq}")
        if seq <= previous_seq:
            problems.append(f"entry {index}: seq {seq} not increasing")
        seen_seq.add(seq)
        previous_seq = max(previous_seq, seq)

        kind = entry.get("kind")
        status = entry.get("status")
        actor = entry.get("actor")
        if kind not in KINDS:
            problems.append(f"seq {seq}: invalid kind {kind!r}")
        if status not in ENTRY_STATUSES:
            problems.append(f"seq {seq}: invalid status {status!r}")
        if actor not in ACTORS:
            problems.append(f"seq {seq}: invalid actor {actor!r}")

        if kind in REASONING_KINDS:
            reasoning_seqs.add(seq)
            if status != "added":
                problems.append(f"seq {seq}: reasoning entry must start as added")
        elif kind == "status-change":
            target = entry.get("target")
            if not isinstance(target, int) or target not in reasoning_seqs:
                problems.append(f"seq {seq}: target {target!r} is not an earlier reasoning entry")
            if status not in {"confirmed", "cancelled"}:
                problems.append(f"seq {seq}: status-change must be confirmed or cancelled")
            if status == "cancelled" and not entry.get("reason"):
                problems.append(f"seq {seq}: cancelled status-change requires reason")
        elif kind == "lifecycle":
            if entry.get("event") not in LIFECYCLE_EVENTS:
                problems.append(f"seq {seq}: invalid lifecycle event {entry.get('event')!r}")

    if entries:
        first = entries[0]
        if first.get("kind") != "lifecycle" or first.get("event") != "created":
            problems.append("entry 1: journal must start with a lifecycle created event")
    else:
        problems.append("journal is empty")
    return problems


def render_markdown(entries: list[JsonObject]) -> str:
    derived = derive_status(entries)
    by_seq = {entry["seq"]: entry for entry in entries if "seq" in entry}

    def section(title: str, seqs: list[int]) -> list[str]:
        lines = [f"## {title}", ""]
        if not seqs:
            lines.append("(none)")
        for seq in seqs:
            entry = by_seq[seq]
            lines.append(f"- #{seq} [{entry.get('kind')}] {entry.get('content', '')}")
        lines.append("")
        return lines

    lines = [f"# Journal View (issue: {derived['issueStatus']})", ""]
    lines += section("Confirmed", derived["confirmed"])
    lines += section("Active", derived["active"])
    lines += section("Cancelled", derived["cancelled"])
    lines += ["## Log", ""]
    for entry in entries:
        seq = entry.get("seq")
        detail = entry.get("content") or entry.get("reason") or entry.get("evidence") or ""
        suffix = f" -> #{entry['target']}" if entry.get("target") else ""
        lines.append(
            f"- #{seq} {entry.get('ts', '')} [{entry.get('kind')}/{entry.get('status')}]"
            f"{suffix} {detail}"
        )
    lines.append("")
    return "\n".join(lines)


def init_issue(issue_dir: Path, *, initial_request: str, actor: str) -> JsonObject:
    if journal_path(issue_dir).exists():
        raise JournalError(f"journal already exists: {journal_path(issue_dir)}")
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
    issue_dir.mkdir(parents=True, exist_ok=True)
    append_entry(issue_dir, entry)
    problem = problem_template().replace("{initial_request}", initial_request)
    (issue_dir / PROBLEM_FILE).write_text(problem, encoding="utf-8")
    return entry
