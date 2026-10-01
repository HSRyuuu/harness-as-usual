"""What replaced `move`: adopting artifacts at init, and carrying on in place.

A folder no longer changes unit. Investigation continues into implementation in
the same folder, and genuinely separate follow-up work gets its own folder plus
a link.
"""

from __future__ import annotations

import pytest

from as_usual_record.status import derive_status


def _init(run, work_dir, request: str = "adopt me") -> int:
    return run("init", "--dir", str(work_dir), "--request", request, "--actor", "claude")


@pytest.mark.parametrize("artifact", ["requirements.md", "plan.md", "conclusion.md"])
def test_init_adopts_each_artifact_without_a_record(as_usual, run, capsys, artifact):
    work_dir = as_usual / "work" / "2026-07-25-orphan"
    work_dir.mkdir(parents=True)
    (work_dir / artifact).write_text("# Written past the helper\n", encoding="utf-8")
    capsys.readouterr()

    assert _init(run, work_dir) == 0
    assert f"adopted {artifact}" in capsys.readouterr().out
    assert (work_dir / artifact).read_text() == "# Written past the helper\n"
    assert artifact in derive_status(work_dir)["artifacts"]


def test_stray_files_are_neither_adopted_nor_blocking(as_usual, run, capsys):
    """Blocklist, not allowlist: unrelated files must not affect the decision."""
    work_dir = as_usual / "work" / "2026-07-25-stray"
    (work_dir / "evidence").mkdir(parents=True)
    (work_dir / "scratch.md").write_text("notes\n", encoding="utf-8")
    capsys.readouterr()

    assert _init(run, work_dir) == 0
    assert "adopted" not in capsys.readouterr().out
    assert (work_dir / "scratch.md").exists()


@pytest.mark.parametrize("unit", ["inbox", "topic", "direct-work", "issue"])
def test_init_refuses_a_pre_v2_folder_that_holds_a_record(make_legacy, run, events, unit):
    """Re-initializing an old unit's folder as work would rewrite its history."""
    work_dir = make_legacy(unit)
    before = events(work_dir)

    assert _init(run, work_dir, request="start over") == 2
    assert events(work_dir) == before


def test_move_is_gone(make_work, run):
    work_dir = make_work()
    with pytest.raises(SystemExit):
        run("move", "--dir", str(work_dir), "--to", "topic")


def test_investigation_carries_on_into_implementation_in_place(
    make_work, run, events, approve_execution
):
    """The folder `move` used to relabel now simply continues."""
    work_dir = make_work()
    args = ("add", "--dir", str(work_dir))
    assert run(*args, "--kind", "hypothesis", "--phase", "investigate",
               "--summary", "a stale constant") == 0
    assert run(*args, "--kind", "approval", "--action", "reproduction", "--actor", "user",
               "--summary", "repro script approved") == 0
    assert run(*args, "--kind", "status-change", "--target", "2", "--to", "confirmed",
               "--evidence", "repro fails on the constant", "--summary", "cause confirmed") == 0

    approve_execution(work_dir)
    assert run(*args, "--kind", "verification", "--verdict", "PASS",
               "--summary", "repro passes after the fix") == 0
    assert run(*args, "--kind", "lifecycle", "--event", "finalized",
               "--summary", "fixed") == 0

    assert work_dir.exists()
    assert {entry["unit"] for entry in events(work_dir)} == {"work"}
    assert derive_status(work_dir)["state"] == "finalized"
    assert run("validate", "--dir", str(work_dir)) == 0
