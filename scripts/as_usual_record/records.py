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

from .constants import OPEN_VERDICTS, JsonObject
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


def latest_of_kind(events: list[JsonObject], kind: str) -> JsonObject | None:
    """Return the newest event of `kind`, or None when there is none.

    Both the finalize gate and the derived status need "the verification that
    counts". Two answers to that question is one more than the record can have.
    """
    for entry in reversed(events):
        if entry.get("kind") == kind:
            return entry
    return None


def resolved_targets(events: list[JsonObject], kind: str) -> set[int]:
    """Seqs of `kind` entries that a later entry of the same kind already closed."""
    resolved: set[int] = set()
    for entry in events:
        if entry.get("kind") != kind:
            continue
        target = entry.get("data", {}).get("resolves")
        if isinstance(target, int) and not isinstance(target, bool):
            resolved.add(target)
    return resolved


def open_verifications(events: list[JsonObject]) -> list[JsonObject]:
    """Verifications that failed and were never verified again.

    A completion claim rests on every criterion, not on whichever run happened
    to be last. An INCONCLUSIVE or FAIL stays open until a later verification
    names its seq with --resolves, so a passing run on a different surface can
    no longer bury it.
    """
    resolved = resolved_targets(events, "verification")
    return [
        entry
        for entry in events
        if entry.get("kind") == "verification"
        and entry.get("data", {}).get("verdict") in OPEN_VERDICTS
        and entry.get("seq") not in resolved
    ]


def open_blockers(events: list[JsonObject]) -> list[JsonObject]:
    """Blockers that are still blocking.

    An entry drops off this list two ways: a later blocker resolved it, or it is
    itself nothing but a resolution.

    The second case is what `--status` decides. "A is cleared but B now blocks
    us" is one event and B still has to be visible, so a resolving blocker is not
    filtered on sight — it stays open unless it was recorded as `success`, which
    is the writer saying it closed something and introduced nothing. Without that
    distinction every clean resolution left a phantom behind: the resolution
    could only be closed by another blocker, which would then be open in its
    turn.
    """
    resolved = resolved_targets(events, "blocker")
    return [
        entry
        for entry in events
        if entry.get("kind") == "blocker"
        and entry.get("seq") not in resolved
        and not _is_pure_resolution(entry)
    ]


def _is_pure_resolution(entry: JsonObject) -> bool:
    """A blocker that closes an earlier one and reports nothing still blocking."""
    target = entry.get("data", {}).get("resolves")
    if not isinstance(target, int) or isinstance(target, bool):
        return False
    return entry.get("status") == "success"


def current_unit(events: list[JsonObject]) -> str:
    """Return the unit the folder currently belongs to, from the newest event."""
    for entry in reversed(events):
        unit = entry.get("unit")
        if isinstance(unit, str) and unit:
            return unit
    raise RecordError("record has no unit; the folder was not initialized by this helper")
