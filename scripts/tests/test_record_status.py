"""Derived state and after-the-fact validation."""

from __future__ import annotations

import json

import pytest

from as_usual_record.constants import (
    KINDS,
    LIFECYCLE_EVENTS,
    RETIRED_KINDS,
    RETIRED_LIFECYCLE_EVENTS,
)
from as_usual_record.status import derive_status
from as_usual_record.validation import validate_record


def test_status_reports_unit_phase_and_next_action(make_unit, run):
    work_dir = make_unit("topic")
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "decision",
        "--summary",
        "scope agreed",
        "--phase",
        "gathering-context",
        "--next-action",
        "write-requirements",
    )

    status = derive_status(work_dir)
    assert status["unit"] == "topic"
    assert status["state"] == "open"
    assert status["phase"] == "gathering-context"
    assert status["nextAction"] == "write-requirements"
    assert status["eventCount"] == 2


def test_status_tracks_the_latest_verification(make_unit, run):
    work_dir = make_unit("direct-work")
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "verification",
        "--summary",
        "first run",
        "--verdict",
        "INCONCLUSIVE",
    )
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "verification",
        "--summary",
        "re-run after fix",
        "--verdict",
        "PASS",
    )

    status = derive_status(work_dir)
    assert status["verification"]["verdict"] == "PASS"
    # The latest verdict and the open gaps answer different questions: the pass is
    # real, and the earlier INCONCLUSIVE it did not re-verify is still outstanding.
    assert [entry["seq"] for entry in status["openVerifications"]] == [2]
    assert status["openVerifications"][0]["verdict"] == "INCONCLUSIVE"


def test_open_blockers_are_listed_until_resolved(make_unit, run):
    work_dir = make_unit("topic")
    run("add", "--dir", str(work_dir), "--kind", "blocker", "--summary", "missing API key")
    assert len(derive_status(work_dir)["blockers"]) == 1

    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "blocker",
        "--summary",
        "key provided",
        "--resolves",
        "2",
    )
    assert derive_status(work_dir)["blockers"] == []


def test_status_lists_approvals_and_confirmations(make_unit, run):
    work_dir = make_unit("issue")
    run("add", "--dir", str(work_dir), "--kind", "hypothesis", "--summary", "retry storm")
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "status-change",
        "--summary",
        "confirmed",
        "--target",
        "2",
        "--to",
        "confirmed",
        "--evidence",
        "reproduced",
    )
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "approval",
        "--summary",
        "repro script approved",
        "--action",
        "execution",
        "--actor",
        "user",
    )

    status = derive_status(work_dir)
    assert status["confirmed"] == [2]
    assert status["approvals"][0]["action"] == "execution"
    # A resuming session reads status, not the raw log: who approved has to survive here.
    assert status["approvals"][0]["actor"] == "user"


def test_move_allowed_flips_once_output_exists(make_unit):
    work_dir = make_unit("topic")
    assert derive_status(work_dir)["moveAllowed"] is True

    (work_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
    assert derive_status(work_dir)["moveAllowed"] is False


def test_state_reflects_closure(make_unit, run):
    work_dir = make_unit("topic")
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "verification",
        "--summary",
        "pytest -q: 12 passed",
        "--verdict",
        "PASS",
    )
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "lifecycle",
        "--summary",
        "closed",
        "--event",
        "finalized",
    )

    assert derive_status(work_dir)["state"] == "finalized"


def test_status_json_output(make_unit, run, capsys):
    work_dir = make_unit("issue")
    capsys.readouterr()

    assert run("status", "--dir", str(work_dir), "--json") == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["unit"] == "issue"


def test_validate_accepts_a_healthy_record(make_unit, run):
    work_dir = make_unit("topic")
    run("add", "--dir", str(work_dir), "--kind", "note", "--summary", "n")

    assert validate_record(work_dir) == []
    assert run("validate", "--dir", str(work_dir)) == 0


def test_validate_catches_hand_edited_duplicate_seq(make_unit):
    work_dir = make_unit("topic")
    path = work_dir / "audit.jsonl"
    forged = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(forged) + "\n")

    problems = validate_record(work_dir)
    assert any("duplicate seq" in problem for problem in problems)


def test_validate_catches_an_append_after_closure(make_unit, run):
    work_dir = make_unit("topic")
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "verification",
        "--summary",
        "pytest -q: 12 passed",
        "--verdict",
        "PASS",
    )
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "lifecycle",
        "--summary",
        "closed",
        "--event",
        "finalized",
    )
    path = work_dir / "audit.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "seq": 99,
                    "ts": "2026-07-25T00:00:00+09:00",
                    "actor": "claude",
                    "unit": "topic",
                    "kind": "note",
                    "status": "success",
                    "summary": "snuck in",
                }
            )
            + "\n"
        )

    problems = validate_record(work_dir)
    assert any("after the record was closed" in problem for problem in problems)


def test_validate_catches_a_verification_without_verdict(make_unit):
    work_dir = make_unit("topic")
    path = work_dir / "audit.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "seq": 2,
                    "ts": "2026-07-25T00:00:00+09:00",
                    "actor": "claude",
                    "unit": "topic",
                    "kind": "verification",
                    "status": "success",
                    "summary": "trust me",
                }
            )
            + "\n"
        )

    problems = validate_record(work_dir)
    assert any("valid verdict" in problem for problem in problems)


def test_validate_catches_a_phase_outside_the_unit(make_unit):
    work_dir = make_unit("topic")
    path = work_dir / "audit.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "seq": 2,
                    "ts": "2026-07-25T00:00:00+09:00",
                    "actor": "claude",
                    "unit": "topic",
                    "kind": "note",
                    "status": "success",
                    "summary": "n",
                    "phase": "investigating",
                }
            )
            + "\n"
        )

    problems = validate_record(work_dir)
    assert any("not used by unit" in problem for problem in problems)


def _append(work_dir, entry: dict) -> None:
    """Write an event straight to the record, the way a stale tool would."""
    with (work_dir / "audit.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


@pytest.mark.parametrize("kind", ["artifact", "memory"])
def test_validate_accepts_a_retired_kind(make_unit, kind):
    """A value that was legal when it was written stays readable after removal.

    `validate` audits for hand-editing, not for vocabulary drift over time.
    """
    work_dir = make_unit("topic")
    _append(
        work_dir,
        {
            "seq": 2,
            "ts": "2026-07-25T00:00:00+09:00",
            "actor": "claude",
            "unit": "topic",
            "kind": kind,
            "status": "success",
            "summary": "requirements.md written",
        },
    )

    assert validate_record(work_dir) == []


def test_validate_accepts_a_retired_lifecycle_event(make_unit):
    work_dir = make_unit("topic")
    _append(
        work_dir,
        {
            "seq": 2,
            "ts": "2026-07-25T00:00:00+09:00",
            "actor": "claude",
            "unit": "topic",
            "kind": "lifecycle",
            "status": "success",
            "summary": "entered write-plan",
            "data": {"event": "phase-entered"},
        },
    )

    assert validate_record(work_dir) == []


def _write_contexts(work_dir, body: str) -> None:
    (work_dir / "contexts.md").write_text(body, encoding="utf-8")


def test_validate_catches_a_unit_mismatch_in_the_legacy_section(make_unit):
    """The pre-frontmatter form still has to be cross-checked.

    Work folders created before the frontmatter format are still resumed, so
    this path is live rather than historical.
    """
    work_dir = make_unit("topic")
    _write_contexts(work_dir, "# Context\n\n## Work Unit\n\nissue\n")

    problems = validate_record(work_dir)
    assert any("issue" in problem and "topic" in problem for problem in problems)


def test_validate_reads_the_unit_from_frontmatter(make_unit):
    """Frontmatter wins over a leftover section — the priority is the point."""
    work_dir = make_unit("topic")
    _write_contexts(
        work_dir,
        "---\nunit: issue\nslug: 2026-07-25-sample\n---\n\n# Context\n\n"
        "## Work Unit\n\ntopic\n",
    )

    problems = validate_record(work_dir)
    assert any("issue" in problem for problem in problems)


def test_validate_passes_when_the_declared_unit_agrees(make_unit):
    work_dir = make_unit("issue")
    _write_contexts(work_dir, "---\nunit: issue\nslug: 2026-07-25-sample\n---\n\n# Context\n")

    assert validate_record(work_dir) == []


def test_validate_catches_a_missing_unit_declaration(make_unit):
    """Deleting the declaration must not be a way around the cross-check."""
    work_dir = make_unit("topic")
    _write_contexts(work_dir, "# Context\n\nno declaration anywhere\n")

    problems = validate_record(work_dir)
    assert any("declare" in problem for problem in problems)


def test_validate_refuses_a_missing_contexts_file(make_unit, run):
    """Already enforced by `require_existing_dir`; pinned here so it stays that way."""
    work_dir = make_unit("topic")
    (work_dir / "contexts.md").unlink()

    assert run("validate", "--dir", str(work_dir)) == 2


def test_retired_vocabulary_is_disjoint_from_current():
    """A value cannot be both current and retired — the distinction is the point."""
    assert KINDS & RETIRED_KINDS == set()
    assert LIFECYCLE_EVENTS & RETIRED_LIFECYCLE_EVENTS == set()


@pytest.mark.parametrize("kind", ["artifact", "memory"])
def test_add_refuses_a_retired_kind(make_unit, run, kind):
    """Retiring a value keeps the past readable; it must not keep the future open."""
    work_dir = make_unit("topic")

    with pytest.raises(SystemExit):
        run("add", "--dir", str(work_dir), "--kind", kind, "--summary", "nope")
