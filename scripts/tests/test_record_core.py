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
    # The bands are not pre-written: a section arrives when it has something to
    # hold, so a fresh document carries the request and nothing else.
    assert "## Decisions" not in body
    assert "## Q&A Log" not in body

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
    # The record files are what is in the way. `plan.md` beside them is not —
    # an artifact alone no longer blocks init, so it is not named here either.
    assert "contexts.md" in message and "audit.jsonl" in message


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


def _contexts(work_dir, body: str) -> None:
    (work_dir / "contexts.md").write_text(body, encoding="utf-8")


def test_append_to_band_adds_under_an_existing_band(make_unit):
    from as_usual_record.contexts import append_to_band

    work_dir = make_unit("topic")
    _contexts(
        work_dir,
        "---\nunit: topic\n---\n\n# Context\n\n## Initial Request\n\nbuild it\n\n"
        "## Linked Work\n\n- `.as-usual/issue/2026-08-01-cause` — prior investigation\n",
    )

    assert append_to_band(work_dir, "## Linked Work", "- `.as-usual/topic/2026-08-02-next` — follow-up")
    body = (work_dir / "contexts.md").read_text()
    assert "prior investigation" in body
    assert "follow-up" in body
    assert body.index("prior investigation") < body.index("follow-up")


def test_append_to_band_replaces_an_empty_marker(make_unit):
    from as_usual_record.contexts import append_to_band

    work_dir = make_unit("topic")
    _contexts(
        work_dir,
        "---\nunit: topic\n---\n\n# Context\n\n## Linked Work\n\n_None._\n",
    )

    assert append_to_band(work_dir, "## Linked Work", "- `.as-usual/topic/x` — why")
    body = (work_dir / "contexts.md").read_text()
    assert "_None._" not in body
    assert "— why" in body


def test_append_to_band_creates_a_missing_band_in_order(make_unit):
    """A young unit has no Linked Work band at all; the entry still has a home."""
    from as_usual_record.contexts import append_to_band

    work_dir = make_unit("topic")
    _contexts(
        work_dir,
        "---\nunit: topic\n---\n\n# Context\n\n## Initial Request\n\nbuild it\n\n"
        "## Decisions\n\n### something - 2026-08-31 10:00:00\n\nagreed\n",
    )

    assert append_to_band(work_dir, "## Linked Work", "- `.as-usual/topic/x` — why")
    body = (work_dir / "contexts.md").read_text()
    assert "## Linked Work" in body
    # core-rules.md fixes the order: after the request, before the decisions.
    assert body.index("## Initial Request") < body.index("## Linked Work") < body.index("## Decisions")


def test_append_to_band_refuses_a_damaged_document(make_unit):
    """No frontmatter and no title: there is no safe place to put anything."""
    from as_usual_record.contexts import append_to_band

    work_dir = make_unit("topic")
    _contexts(work_dir, "just a loose note with no structure\n")
    before = (work_dir / "contexts.md").read_text()

    assert append_to_band(work_dir, "## Linked Work", "- `.as-usual/topic/x` — why") is False
    assert (work_dir / "contexts.md").read_text() == before


def test_prepend_notice_lands_above_every_band(make_unit):
    from as_usual_record.contexts import prepend_notice

    work_dir = make_unit("topic")
    _contexts(
        work_dir,
        "---\nunit: topic\n---\n\n# Context\n\n## Initial Request\n\nbuild it\n",
    )

    assert prepend_notice(work_dir, "> **CANCELLED 2026-08-31 (#3)** — premise was false")
    body = (work_dir / "contexts.md").read_text()
    assert body.index("CANCELLED") < body.index("## Initial Request")


def test_prepend_notice_refuses_a_document_without_a_title(make_unit):
    from as_usual_record.contexts import prepend_notice

    work_dir = make_unit("topic")
    _contexts(work_dir, "---\nunit: topic\n---\n\nno title here\n")
    before = (work_dir / "contexts.md").read_text()

    assert prepend_notice(work_dir, "> **CANCELLED**") is False
    assert (work_dir / "contexts.md").read_text() == before


def test_init_writes_no_placeholders(make_unit):
    work_dir = make_unit("topic")
    body = (work_dir / "contexts.md").read_text()
    for marker in ("_Not set._", "_None._", "_None yet._", "_No questions raised yet._"):
        assert marker not in body


def test_init_adopts_a_folder_holding_only_an_artifact(as_usual: Path, run, capsys):
    """An artifact written past the helper is not a record, and saying so was false.

    The old guard refused this folder as "already a work record", which left the
    only recovery as deleting a document nobody wanted to delete — and the
    folder could never acquire the record it was missing.
    """
    work_dir = as_usual / "topic" / "2026-08-31-orphan"
    work_dir.mkdir(parents=True)
    (work_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
    capsys.readouterr()

    assert (
        run(
            "init",
            "--dir",
            str(work_dir),
            "--unit",
            "topic",
            "--request",
            "adopt me",
            "--actor",
            "claude",
        )
        == 0
    )
    assert (work_dir / "audit.jsonl").exists()
    assert (work_dir / "contexts.md").exists()
    assert (work_dir / "plan.md").read_text() == "# Plan\n"
    assert "adopted plan.md" in capsys.readouterr().out


def test_link_writes_into_both_documents(as_usual: Path, run, make_unit):
    from as_usual_record.status import derive_status

    left = make_unit("topic", slug="2026-08-31-left")
    right = make_unit("issue", slug="2026-08-31-right")

    assert run("link", "--dir", str(left), "--to-dir", str(right), "--summary", "cause of this") == 0

    left_body = (left / "contexts.md").read_text()
    right_body = (right / "contexts.md").read_text()
    assert "## Linked Work" in left_body and "## Linked Work" in right_body
    assert "2026-08-31-right" in left_body
    assert "2026-08-31-left" in right_body
    assert "cause of this" in left_body and "cause of this" in right_body
    # The two surfaces agree: the event and the document say the same thing.
    assert derive_status(left)["links"] == ["2026-08-31-right"] or "2026-08-31-right" in str(
        derive_status(left)["links"]
    )


def test_link_leaves_a_damaged_document_alone(as_usual: Path, run, make_unit, capsys):
    left = make_unit("topic", slug="2026-08-31-l2")
    right = make_unit("issue", slug="2026-08-31-r2")
    (left / "contexts.md").write_text("loose note\n", encoding="utf-8")
    capsys.readouterr()

    assert run("link", "--dir", str(left), "--to-dir", str(right), "--summary", "why") == 0
    assert (left / "contexts.md").read_text() == "loose note\n"
    assert "could not write the link" in capsys.readouterr().out
    # The event still landed on both sides.
    assert "2026-08-31-r2" in (left / "audit.jsonl").read_text()


def test_cancelling_marks_the_document(make_unit, run):
    work_dir = make_unit("topic")

    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "lifecycle",
            "--event",
            "cancelled",
            "--actor",
            "user",
            "--reason",
            "already cached upstream",
            "--summary",
            "premise was false",
        )
        == 0
    )

    body = (work_dir / "contexts.md").read_text()
    assert "CANCELLED" in body
    assert "premise was false" in body
    assert "already cached upstream" in body
    assert body.index("CANCELLED") < body.index("## Initial Request")
