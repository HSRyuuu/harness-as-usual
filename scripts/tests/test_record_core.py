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


def test_init_writes_request_and_unit_into_contexts(make_unit, events):
    work_dir = make_unit("issue", request="왜 죽는지 모르겠음", slug="2026-07-25-crash")
    body = (work_dir / "contexts.md").read_text(encoding="utf-8")

    assert "왜 죽는지 모르겠음" in body
    assert "## Decisions" in body
    assert "## Q&A Log" in body

    front = _frontmatter(body)
    assert front["unit"] == "issue"
    assert front["slug"] == "2026-07-25-crash"
    # Taken from the `created` event, so the document cannot disagree with the
    # record about the day.
    assert front["created"] == events(work_dir)[0]["ts"][:10]


def test_init_leaves_no_template_scaffolding_behind(make_unit):
    """The rendered document is the user's first read; it must not look like a form."""
    work_dir = make_unit("topic")
    body = (work_dir / "contexts.md").read_text(encoding="utf-8")

    assert "<!--" not in body
    assert "## Work Unit" not in body
    assert "## Artifacts" not in body
    assert "**Q:**" not in body
    assert "{unit}" not in body and "{slug}" not in body and "{created}" not in body


def test_request_containing_a_placeholder_is_not_substituted_again(make_unit):
    """The request is verbatim user text and may name a placeholder token."""
    work_dir = make_unit("topic", request="rename {slug} to {created} everywhere")
    body = (work_dir / "contexts.md").read_text(encoding="utf-8")

    assert "rename {slug} to {created} everywhere" in body


def _frontmatter(body: str) -> dict[str, str]:
    assert body.startswith("---\n"), body[:40]
    block = body.split("---\n", 2)[1]
    return dict(
        (key.strip(), value.strip())
        for key, _, value in (line.partition(":") for line in block.splitlines())
        if key.strip()
    )


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


def test_init_refuses_after_the_audit_is_deleted(make_unit, run):
    """Deleting the record must not hand the folder back as a fresh unit.

    Sealing and the move restriction both read `audit.jsonl`, so re-initializing
    over a folder that still holds its other artifacts wipes both gates at once.
    """
    work_dir = make_unit("topic")
    (work_dir / "plan.md").write_text("a plan", encoding="utf-8")
    (work_dir / "audit.jsonl").unlink()

    assert (
        run(
            "init",
            "--dir",
            str(work_dir),
            "--unit",
            "direct-work",
            "--request",
            "starting over",
            "--actor",
            "claude",
        )
        == 2
    )
    assert not (work_dir / "audit.jsonl").exists()


def test_init_refusal_names_what_is_in_the_way(make_unit, run, capsys):
    """"Cannot init" without naming the file leaves the user guessing."""
    work_dir = make_unit("topic")
    (work_dir / "plan.md").write_text("a plan", encoding="utf-8")
    capsys.readouterr()

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

    message = capsys.readouterr().err
    assert "contexts.md" in message and "plan.md" in message


def test_init_still_succeeds_in_an_empty_dir(as_usual: Path, run):
    """The normal path — a folder with nothing in it — is untouched."""
    work_dir = as_usual / "topic" / "2026-07-26-empty"
    work_dir.mkdir(parents=True)

    assert (
        run(
            "init",
            "--dir",
            str(work_dir),
            "--unit",
            "topic",
            "--request",
            "fresh start",
            "--actor",
            "claude",
        )
        == 0
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
    assert events(follow_up)[-1]["data"]["to"] == ".as-usual/issue/2026-07-25-crash"


def test_link_records_project_relative_paths(make_unit, run, events, as_usual):
    """An absolute path bakes this machine into an append-only record forever."""
    first = make_unit("topic", slug="2026-07-25-one")
    second = make_unit("issue", slug="2026-07-25-two")

    assert run("link", "--dir", str(first), "--to-dir", str(second)) == 0

    assert events(first)[-1]["data"]["to"] == ".as-usual/issue/2026-07-25-two"
    assert events(second)[-1]["data"]["to"] == ".as-usual/topic/2026-07-25-one"
    assert not str(as_usual).startswith(".")  # the fixture root really is absolute


def test_missing_record_is_reported(run, tmp_path: Path):
    assert run("add", "--dir", str(tmp_path / "nope"), "--kind", "note", "--summary", "s") == 2
