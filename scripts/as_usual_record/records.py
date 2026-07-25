"""Append-only record read/write for AsUsual work units.

Concurrency: appends do a read-then-append under an advisory file lock held by
the CLI layer, matching AsUsual's single-controller model. Two simultaneous
writers without the lock can produce duplicate seqs, which `validate` detects
after the fact.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

from .constants import JsonObject
from .paths import RecordError, audit_path


def current_timestamp() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def read_events(work_dir: Path) -> list[JsonObject]:
    path = audit_path(work_dir)
    if not path.exists():
        raise RecordError(f"record not found: {path}")
    events: list[JsonObject] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RecordError(f"invalid json at {path}:{line_no}: {exc}") from exc
        if not isinstance(entry, dict):
            raise RecordError(f"record line must be a JSON object: {path}:{line_no}")
        events.append(entry)
    return events


def next_seq(events: list[JsonObject]) -> int:
    highest = 0
    for entry in events:
        seq = entry.get("seq")
        if isinstance(seq, int) and not isinstance(seq, bool):
            highest = max(highest, seq)
    return highest + 1


def build_entry(
    events: list[JsonObject],
    *,
    unit: str,
    kind: str,
    actor: str,
    summary: str,
    status: str = "success",
    phase: str = "",
    next_action: str = "",
    data: JsonObject | None = None,
) -> JsonObject:
    entry: JsonObject = {
        "seq": next_seq(events),
        "ts": current_timestamp(),
        "actor": actor,
        "unit": unit,
        "kind": kind,
        "status": status,
        "summary": summary,
    }
    if phase:
        entry["phase"] = phase
    if next_action:
        entry["nextAction"] = next_action
    if data:
        entry["data"] = data
    return entry


def append_entry(work_dir: Path, entry: JsonObject) -> None:
    path = audit_path(work_dir)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")


def find_entry(events: list[JsonObject], seq: int) -> JsonObject:
    for entry in events:
        if entry.get("seq") == seq:
            return entry
    raise RecordError(f"invalid target: seq {seq} not found")


def current_unit(events: list[JsonObject]) -> str:
    """Return the unit the folder currently belongs to, from the newest event."""
    for entry in reversed(events):
        unit = entry.get("unit")
        if isinstance(unit, str) and unit:
            return unit
    raise RecordError("record has no unit; the folder was not initialized by this helper")
