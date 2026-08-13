"""Script-enforced gates for the AsUsual record layer.

These implement the core rules that must not depend on agent goodwill. Every
refusal here is a rule the harness guarantees rather than merely documents.
"""

from __future__ import annotations

from pathlib import Path

from .constants import (
    ACTORS,
    APPROVAL_ACTIONS,
    CLOSING_LIFECYCLE_EVENTS,
    KINDS,
    LIFECYCLE_EVENTS,
    MOVE_BLOCKING_FILES,
    NEXT_ACTION_SPECIALS,
    OPEN_VERDICTS,
    PHASES,
    PLAN_REVIEW_UNITS,
    REASONING_KINDS,
    STATUS_CHANGE_STATES,
    STATUSES,
    UNIT_PHASES,
    UNITS,
    VERDICTS,
    VERIFICATION_UNITS,
    JsonObject,
)
from .paths import RecordError
from .records import find_entry, latest_of_kind, open_verifications


def validate_enum(name: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        raise RecordError(f"invalid {name}: {value}. allowed: {', '.join(sorted(allowed))}")


def validate_vocabulary(
    *,
    unit: str,
    kind: str,
    actor: str,
    status: str,
    phase: str,
    next_action: str,
) -> None:
    validate_enum("unit", unit, UNITS)
    validate_enum("kind", kind, KINDS)
    validate_enum("actor", actor, ACTORS)
    validate_enum("status", status, STATUSES)
    if phase:
        validate_enum("phase", phase, PHASES)
        allowed = UNIT_PHASES[unit]
        if phase not in allowed:
            raise RecordError(
                f"phase {phase} is not used by unit {unit}. "
                f"allowed: {', '.join(sorted(allowed))}"
            )
    if next_action:
        validate_enum("nextAction", next_action, PHASES | NEXT_ACTION_SPECIALS)


def check_not_closed(events: list[JsonObject], kind: str, data: JsonObject) -> None:
    """Core gate: a finalized or cancelled record is sealed.

    The single exception is linking another work unit, which must stay possible
    after closure so a concluded issue can point at the follow-up work it spawned.
    """
    closing = _closing_event(events)
    if closing is None:
        return
    is_link = kind == "lifecycle" and data.get("event") == "linked"
    if is_link:
        return
    state = closing.get("data", {}).get("event", "closed")
    raise RecordError(
        f"record is {state} (seq {closing.get('seq')}); only lifecycle link entries may be appended"
    )


def _closing_event(events: list[JsonObject]) -> JsonObject | None:
    for entry in events:
        if entry.get("kind") != "lifecycle":
            continue
        if entry.get("data", {}).get("event") in CLOSING_LIFECYCLE_EVENTS:
            return entry
    return None


def check_kind_payload(
    work_dir: Path,
    events: list[JsonObject],
    *,
    unit: str,
    kind: str,
    data: JsonObject,
) -> None:
    """Per-kind required fields and cross-event preconditions."""
    if kind == "verification":
        verdict = data.get("verdict")
        if not verdict:
            raise RecordError(
                "verification requires --verdict (PASS|FAIL|INCONCLUSIVE); "
                "an unverifiable result is INCONCLUSIVE, never PASS"
            )
        validate_enum("verdict", str(verdict), VERDICTS)
        _check_verification_resolves(events, data)

    elif kind == "status-change":
        _check_status_change(events, data)

    elif kind == "approval":
        _check_approval(events, unit, data)

    elif kind == "lifecycle":
        event = data.get("event")
        if not event:
            raise RecordError("lifecycle requires an event name")
        validate_enum("lifecycle event", str(event), LIFECYCLE_EVENTS)
        if event == "finalized":
            _check_finalize(events, work_dir, unit, data)


def _check_verification_resolves(events: list[JsonObject], data: JsonObject) -> None:
    """--resolves may only close an earlier verification that actually failed.

    Pointing it anywhere else would let the finalize gate be cleared by a
    reference that closes nothing.
    """
    target = data.get("resolves")
    if target is None:
        return
    if not isinstance(target, int) or isinstance(target, bool):
        raise RecordError("--resolves takes the seq of the verification it closes")
    entry = find_entry(events, target)
    if entry.get("kind") != "verification":
        raise RecordError(
            f"invalid --resolves target: seq {target} is kind {entry.get('kind')}, "
            "not a verification"
        )
    verdict = entry.get("data", {}).get("verdict")
    if verdict not in OPEN_VERDICTS:
        raise RecordError(
            f"invalid --resolves target: seq {target} is {verdict}, so there is "
            "nothing to resolve"
        )


def _check_status_change(events: list[JsonObject], data: JsonObject) -> None:
    target = data.get("target")
    if not isinstance(target, int) or isinstance(target, bool):
        raise RecordError("status-change requires --target <seq>")
    state = data.get("to")
    if not state:
        raise RecordError("status-change requires --to (confirmed|cancelled)")
    validate_enum("status-change target state", str(state), STATUS_CHANGE_STATES)

    entry = find_entry(events, target)
    if entry.get("kind") not in REASONING_KINDS:
        raise RecordError(
            f"invalid target: seq {target} is kind {entry.get('kind')}, not a reasoning entry"
        )

    if state == "confirmed" and not data.get("evidence"):
        raise RecordError(
            "confirming requires --evidence. record the reproduction evidence, or an "
            "explicit 'could not reproduce because ...' judgment as the evidence text"
        )
    if state == "cancelled" and not data.get("reason"):
        raise RecordError("cancelling requires --reason")


def _check_approval(events: list[JsonObject], unit: str, data: JsonObject) -> None:
    action = data.get("action")
    if not action:
        raise RecordError("approval requires --action (high-risk|execution|git-action)")
    validate_enum("approval action", str(action), APPROVAL_ACTIONS)

    if action == "execution" and unit in PLAN_REVIEW_UNITS:
        # The review has to be newer than the approval it is meant to support.
        # A first approval has nothing before it, so any review satisfies it —
        # `since` stays 0 and every real seq clears it.
        previous = latest_of_kind(
            [entry for entry in events if entry.get("data", {}).get("action") == "execution"],
            "approval",
        )
        # A damaged record must not relax the gate. Refusing here is louder than
        # silently treating the approval as if it had never happened.
        if previous is not None and _seq(previous) == 0:
            raise RecordError(
                f"the previous execution approval has an unusable seq "
                f"({previous.get('seq')!r}); the record looks hand-edited. run validate "
                "and repair it before approving again"
            )
        since = _seq(previous) if previous else 0
        if not any(
            entry.get("kind") == "review" and _seq(entry) > since for entry in events
        ):
            raise RecordError(
                "core rule: the plan must be critically reviewed before execution approval. "
                + (
                    f"the last one was approved at seq {since}; review the plan again and "
                    "record what changed before approving it a second time"
                    if since
                    else "record a review entry (findings + what was improved) first"
                )
            )


def _seq(entry: JsonObject) -> int:
    seq = entry.get("seq")
    return seq if isinstance(seq, int) and not isinstance(seq, bool) else 0


def _check_finalize(
    events: list[JsonObject], work_dir: Path, unit: str, data: JsonObject
) -> None:
    if unit in VERIFICATION_UNITS:
        latest = latest_of_kind(events, "verification")
        # Two distinct failures, deliberately not merged: no evidence at all is
        # not something the user can accept with a reason, because there is no
        # result for them to have seen.
        if latest is None:
            raise RecordError(
                "cannot finalize without a recorded verification: a completion claim needs "
                "evidence that matches the surface. record --kind verification with a verdict, "
                "using INCONCLUSIVE when the evidence could not be obtained, or close with the "
                "cancelled event"
            )
        # Not "is the newest verdict PASS" — a later pass on another surface used
        # to bury an earlier gap and close the unit clean. Every failed run stays
        # open until something re-verifies it by seq.
        unresolved = open_verifications(events)
        if unresolved and not data.get("reason"):
            listed = ", ".join(
                f"seq {entry.get('seq')} {entry.get('data', {}).get('verdict')}"
                for entry in unresolved
            )
            raise RecordError(
                f"cannot finalize with unresolved verifications ({listed}): re-verify and "
                "record the passing run with --resolves <seq>, accept them explicitly with "
                '--reason "<why this is being closed anyway>", or close with the cancelled '
                "event"
            )
    if unit != "issue":
        return
    if not (work_dir / "conclusion.md").exists():
        raise RecordError(
            f"issue cannot be finalized without conclusion.md in {work_dir}. "
            "write the conclusion before recording closure, or close with the cancelled event"
        )
    if not any(
        entry.get("kind") == "status-change" and entry.get("data", {}).get("to") == "confirmed"
        for entry in events
    ):
        raise RecordError(
            "issue cannot be finalized without a confirmed entry: a conclusion needs something "
            "it rests on. confirm the hypothesis or direction with --kind status-change "
            "--to confirmed --evidence, using an explicit 'could not reproduce because ...' as "
            "the evidence when that is the finding, or close with the cancelled event"
        )


def check_move_allowed(work_dir: Path) -> None:
    """A folder that produced its own work output keeps its unit label.

    Blocklist, not allowlist: stray files must never change the outcome.
    """
    present = [name for name in MOVE_BLOCKING_FILES if (work_dir / name).exists()]
    if present:
        raise RecordError(
            f"cannot move {work_dir}: it already produced {', '.join(present)}. "
            "create a new work folder for the other unit and link the two instead"
        )
