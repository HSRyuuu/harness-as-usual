"""Derived state and after-the-fact validation."""

from __future__ import annotations

import json

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

    assert derive_status(work_dir)["verification"]["verdict"] == "PASS"


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
    )

    status = derive_status(work_dir)
    assert status["confirmed"] == [2]
    assert status["approvals"][0]["action"] == "execution"


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
