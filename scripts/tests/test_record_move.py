"""Unit relabelling.

`move` exists for exactly one situation: a folder that has not yet produced its
own work output turns out to belong to a different unit.
"""

from __future__ import annotations

import pytest


def test_inbox_moves_into_a_unit(make_unit, run, as_usual, events):
    work_dir = make_unit("inbox", slug="2026-07-25-unclear")

    assert run("move", "--dir", str(work_dir), "--to", "topic") == 0

    moved = as_usual / "topic" / "2026-07-25-unclear"
    assert moved.exists()
    assert not work_dir.exists()

    last = events(moved)[-1]
    assert last["kind"] == "lifecycle"
    assert last["data"]["event"] == "unit-selected"
    assert last["data"]["from"] == ".as-usual/inbox/2026-07-25-unclear"
    assert last["data"]["to"] == ".as-usual/topic/2026-07-25-unclear"
    assert last["unit"] == "topic"


def test_move_can_rename_the_slug(make_unit, run, as_usual):
    work_dir = make_unit("inbox", slug="2026-07-25-unclear")

    assert run("move", "--dir", str(work_dir), "--to", "issue", "--slug", "2026-07-25-crash") == 0
    assert (as_usual / "issue" / "2026-07-25-crash").exists()


def test_move_updates_the_frontmatter_in_contexts(make_unit, run, as_usual):
    work_dir = make_unit("inbox", slug="2026-07-25-unclear")
    run("move", "--dir", str(work_dir), "--to", "direct-work")

    front = _frontmatter(as_usual / "direct-work" / "2026-07-25-unclear" / "contexts.md")
    assert front["unit"] == "direct-work"
    assert front["slug"] == "2026-07-25-unclear"


def test_move_with_a_new_slug_updates_both_fields(make_unit, run, as_usual):
    """`--slug` renames the folder, so the document's own slug has to follow."""
    work_dir = make_unit("inbox", slug="2026-07-25-unclear")
    run("move", "--dir", str(work_dir), "--to", "issue", "--slug", "2026-07-25-crash")

    front = _frontmatter(as_usual / "issue" / "2026-07-25-crash" / "contexts.md")
    assert front["unit"] == "issue"
    assert front["slug"] == "2026-07-25-crash"


def test_move_updates_a_pre_frontmatter_contexts_document(make_unit, run, as_usual):
    """0.2.x shipped the `## Work Unit` form; those folders still exist elsewhere.

    Without the fallback, `move` would silently leave the document claiming a
    unit the record no longer agrees with.
    """
    work_dir = make_unit("inbox", slug="2026-07-25-unclear")
    (work_dir / "contexts.md").write_text(
        "# Context\n\n## Work Unit\n\ninbox\n\n## Decisions\n",
        encoding="utf-8",
    )

    assert run("move", "--dir", str(work_dir), "--to", "topic") == 0

    body = (as_usual / "topic" / "2026-07-25-unclear" / "contexts.md").read_text(
        encoding="utf-8"
    )
    assert body.split("## Work Unit", 1)[1].split("##", 1)[0].strip() == "topic"


def _frontmatter(path) -> dict[str, str]:
    body = path.read_text(encoding="utf-8")
    assert body.startswith("---\n"), body[:40]
    block = body.split("---\n", 2)[1]
    return dict(
        (key.strip(), value.strip())
        for key, _, value in (line.partition(":") for line in block.splitlines())
        if key.strip()
    )


def test_subsequent_events_carry_the_new_unit(make_unit, run, as_usual, events):
    work_dir = make_unit("inbox", slug="2026-07-25-unclear")
    run("move", "--dir", str(work_dir), "--to", "issue")

    moved = as_usual / "issue" / "2026-07-25-unclear"
    run("add", "--dir", str(moved), "--kind", "hypothesis", "--summary", "maybe the retry loop")

    assert events(moved)[-1]["unit"] == "issue"


def test_mid_gathering_issue_can_still_move(make_unit, run, as_usual):
    """Intended side effect: an investigation that turns out to be a simple fix."""
    work_dir = make_unit("issue", slug="2026-07-25-slow")
    run("add", "--dir", str(work_dir), "--kind", "decision", "--summary", "just a stale constant")

    assert run("move", "--dir", str(work_dir), "--to", "direct-work") == 0
    assert (as_usual / "direct-work" / "2026-07-25-slow").exists()


def test_requirements_blocks_the_move(make_unit, run):
    work_dir = make_unit("topic")
    (work_dir / "requirements.md").write_text("# Requirements\n", encoding="utf-8")

    assert run("move", "--dir", str(work_dir), "--to", "direct-work") == 2
    assert work_dir.exists()


def test_plan_blocks_the_move(make_unit, run):
    work_dir = make_unit("direct-work")
    (work_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")

    assert run("move", "--dir", str(work_dir), "--to", "topic") == 2


def test_conclusion_blocks_the_move(make_unit, run):
    work_dir = make_unit("issue")
    (work_dir / "conclusion.md").write_text("# Conclusion\n", encoding="utf-8")

    assert run("move", "--dir", str(work_dir), "--to", "topic") == 2


def test_stray_files_do_not_block_the_move(make_unit, run, as_usual):
    """Blocklist, not allowlist: unrelated files must not affect the decision."""
    work_dir = make_unit("inbox", slug="2026-07-25-unclear")
    (work_dir / "scratch.md").write_text("notes\n", encoding="utf-8")
    (work_dir / "evidence").mkdir()

    assert run("move", "--dir", str(work_dir), "--to", "issue") == 0
    assert (as_usual / "issue" / "2026-07-25-unclear" / "scratch.md").exists()


def test_move_refuses_an_occupied_target(make_unit, run):
    make_unit("topic", slug="2026-07-25-taken")
    work_dir = make_unit("inbox", slug="2026-07-25-taken")

    assert run("move", "--dir", str(work_dir), "--to", "topic") == 2
    assert work_dir.exists()


def test_move_to_inbox_is_not_a_target(make_unit, run):
    """inbox is a staging unit, never a destination — argparse rejects it outright."""
    work_dir = make_unit("topic")
    with pytest.raises(SystemExit):
        run("move", "--dir", str(work_dir), "--to", "inbox")


def test_closed_record_cannot_move(make_unit, run):
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
        "closed",
        "--event",
        "finalized",
    )

    assert run("move", "--dir", str(work_dir), "--to", "topic") == 2
