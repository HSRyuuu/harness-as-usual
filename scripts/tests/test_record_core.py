"""Init, append, sequencing, vocabulary, and record sealing."""

from __future__ import annotations

from pathlib import Path

import pytest

from as_usual_record.constants import SCHEMA_VERSION


def test_init_creates_both_common_files(make_unit, events):
    work_dir = make_unit("topic")

    assert (work_dir / "contexts.md").exists()
    assert (work_dir / "audit.jsonl").exists()

    recorded = events(work_dir)
    assert len(recorded) == 1
    created = recorded[0]
    assert created["seq"] == 1
    assert created["unit"] == "topic"
    assert created["kind"] == "lifecycle"
    assert created["data"]["event"] == "created"
    assert created["data"]["schemaVersion"] == SCHEMA_VERSION
    assert created["data"]["initialRequest"] == "sample request"


def test_init_writes_request_and_unit_into_contexts(make_unit):
    work_dir = make_unit("issue", request="왜 죽는지 모르겠음")
    body = (work_dir / "contexts.md").read_text(encoding="utf-8")

    assert "왜 죽는지 모르겠음" in body
    assert "## Decisions" in body
    assert "## Q&A Log" in body


def test_init_refuses_to_overwrite_existing_record(make_unit, run):
    work_dir = make_unit("topic")
    assert (
        run(
            "init",
            "--dir",
            str(work_dir),
            "--unit",
            "topic",
            "--request",
            "again",
            "--actor",
            "claude",
        )
        == 2
    )


def test_seq_increments_across_appends(make_unit, run, events):
    work_dir = make_unit("direct-work")
    for index in range(3):
        assert run("add", "--dir", str(work_dir), "--kind", "note", "--summary", f"n{index}") == 0

    assert [entry["seq"] for entry in events(work_dir)] == [1, 2, 3, 4]


def test_unit_is_inherited_from_the_record(make_unit, run, events):
    work_dir = make_unit("issue")
    run("add", "--dir", str(work_dir), "--kind", "hypothesis", "--summary", "maybe the cache")

    assert events(work_dir)[-1]["unit"] == "issue"


def test_data_pairs_are_recorded(make_unit, run, events):
    work_dir = make_unit("topic")
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "work",
        "--summary",
        "task 1 done",
        "--data",
        "files=a.py,b.py",
    )

    assert events(work_dir)[-1]["data"]["files"] == "a.py,b.py"


@pytest.mark.parametrize(
    "argv_tail",
    [
        ("--kind", "note", "--summary", "s", "--phase", "investigating"),
        ("--kind", "note", "--summary", "s", "--next-action", "not-a-phase"),
    ],
)
def test_phase_vocabulary_is_scoped_to_the_unit(make_unit, run, argv_tail):
    work_dir = make_unit("topic")
    assert run("add", "--dir", str(work_dir), *argv_tail) == 2


def test_issue_may_use_its_own_phases(make_unit, run, events):
    work_dir = make_unit("issue")
    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "note",
            "--summary",
            "s",
            "--phase",
            "investigating",
        )
        == 0
    )
    assert events(work_dir)[-1]["phase"] == "investigating"


def test_record_is_sealed_after_finalize(make_unit, run):
    work_dir = make_unit("direct-work")
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
        "done",
        "--event",
        "finalized",
    )

    assert run("add", "--dir", str(work_dir), "--kind", "note", "--summary", "late") == 2


def test_link_is_still_allowed_after_closure(make_unit, run, events, as_usual):
    issue_dir = make_unit("issue", slug="2026-07-25-crash")
    (issue_dir / "conclusion.md").write_text("# Conclusion\n", encoding="utf-8")
    run(
        "add",
        "--dir",
        str(issue_dir),
        "--kind",
        "decision",
        "--summary",
        "root cause is the retry loop",
    )
    run(
        "add",
        "--dir",
        str(issue_dir),
        "--kind",
        "status-change",
        "--summary",
        "confirmed the retry loop",
        "--target",
        "2",
        "--to",
        "confirmed",
        "--evidence",
        "reproduced with the retry disabled",
    )
    # Asserted: without a real closure the link below would prove nothing.
    assert (
        run(
            "add",
            "--dir",
            str(issue_dir),
            "--kind",
            "lifecycle",
            "--summary",
            "concluded",
            "--event",
            "finalized",
        )
        == 0
    )

    follow_up = as_usual / "topic" / "2026-07-25-fix-retry"
    assert (
        run(
            "init",
            "--dir",
            str(follow_up),
            "--unit",
            "topic",
            "--request",
            "fix the retry loop",
            "--actor",
            "claude",
        )
        == 0
    )
    assert run("link", "--dir", str(issue_dir), "--to-dir", str(follow_up)) == 0

    assert events(issue_dir)[-1]["data"]["event"] == "linked"
    assert events(follow_up)[-1]["data"]["to"] == str(issue_dir)


def test_missing_record_is_reported(run, tmp_path: Path):
    assert run("add", "--dir", str(tmp_path / "nope"), "--kind", "note", "--summary", "s") == 2
