"""Sanitized history scenarios; replay instructions live in docs/DEVELOPMENT.md.

The histories were recorded under the legacy units, so they replay on legacy
folders: those must stay resumable and valid after the move to one unit.
"""

from __future__ import annotations

import pytest

from as_usual_record.status import derive_status


def test_history_review_is_not_execution_approval(make_legacy, run, events):
    work_dir = make_legacy("topic")
    args = ("add", "--dir", str(work_dir))
    (work_dir / "plan.md").write_text("# Plan\n\nBound the scan and verify access control.\n")
    assert run(*args, "--kind", "review", "--phase", "write-plan",
               "--next-action", "awaiting-user", "--summary", "four findings corrected") == 0

    status = derive_status(work_dir)
    assert (status["state"], status["phase"], status["nextAction"]) == (
        "open", "write-plan", "awaiting-user")
    assert status["approvals"] == []
    assert status["verification"] is None
    before = events(work_dir)
    assert run(*args, "--kind", "approval", "--action", "execution",
               "--summary", "recorder assumes approval") == 2
    assert events(work_dir) == before
    assert run("validate", "--dir", str(work_dir)) == 0


@pytest.mark.parametrize("gap", ["FAIL", "INCONCLUSIVE"])
def test_history_focused_pass_does_not_clear_another_surface(
    make_legacy, run, events, approve_execution, gap
):
    work_dir = make_legacy("topic")
    approve_execution(work_dir)
    args = ("add", "--dir", str(work_dir))
    (work_dir / "verification.md").write_text("# Verification\n\nIntegration gap remains.\n")
    assert run(*args, "--kind", "verification", "--verdict", gap,
               "--summary", "integration check failed or was skipped") == 0
    gap_seq = events(work_dir)[-1]["seq"]
    assert run(*args, "--kind", "verification", "--verdict", "PASS",
               "--summary", "focused unit tests passed") == 0

    status = derive_status(work_dir)
    assert status["latestVerification"]["verdict"] == "PASS"
    assert status["verification"]["verdict"] == "INCONCLUSIVE"
    before = events(work_dir)
    assert run(*args, "--kind", "lifecycle", "--event", "finalized",
               "--summary", "attempted close over integration gap") == 2
    assert events(work_dir) == before

    assert run(*args, "--kind", "verification", "--verdict", "PASS",
               "--resolves", str(gap_seq), "--summary", "integration check actually ran and passed") == 0
    assert run(*args, "--kind", "lifecycle", "--event", "finalized",
               "--summary", "verified and closed") == 0
    assert derive_status(work_dir)["state"] == "finalized"
    assert run("validate", "--dir", str(work_dir)) == 0


def test_history_cancelled_work_stays_sealed_when_successor_links(
    make_legacy, make_work, run, events
):
    source = make_legacy("topic", slug="2026-01-01-source")
    args = ("add", "--dir", str(source))
    assert run(*args, "--kind", "lifecycle", "--event", "cancelled",
               "--actor", "user", "--reason", "scope replaced",
               "--summary", "user cancelled the original work") == 0
    successor = make_work(slug="2026-01-01-successor")
    assert run("link", "--dir", str(source), "--to-dir", str(successor),
               "--summary", "replacement scope lives in successor") == 0
    before = events(source)
    assert run(*args, "--kind", "work", "--summary", "late result from abandoned work") == 2
    assert events(source) == before
    assert "CANCELLED" in (source / "contexts.md").read_text()
    assert derive_status(source)["state"] == "cancelled"
    assert derive_status(successor)["state"] == "open"
    assert derive_status(source)["links"] and derive_status(successor)["links"]
    assert run("validate", "--dir", str(source)) == 0
    assert run("validate", "--dir", str(successor)) == 0


@pytest.mark.parametrize("unit", ["topic", "direct-work"])
def test_history_changed_surface_requires_resolving_the_new_gap(
    make_legacy, run, events, approve_execution, unit
):
    """The controller detects stale evidence; the helper enforces the recorded gap."""
    work_dir = make_legacy(unit)
    approve_execution(work_dir)
    args = ("add", "--dir", str(work_dir))
    (work_dir / "verification.md").write_text("# Verification\n\nCurrent-state recheck.\n")
    assert run(*args, "--kind", "verification", "--verdict", "PASS",
               "--summary", "check passed against revision A") == 0
    old_pass = events(work_dir)[-1]
    assert run(*args, "--kind", "work", "--summary", "related code changed to revision B") == 0
    assert run(*args, "--kind", "verification", "--verdict", "INCONCLUSIVE",
               "--summary", f"criterion unverified on B; #{old_pass['seq']} tested A") == 0
    gap_seq = events(work_dir)[-1]["seq"]

    before = events(work_dir)
    assert run(*args, "--kind", "lifecycle", "--event", "finalized",
               "--summary", "attempted close with stale evidence") == 2
    assert events(work_dir) == before
    assert derive_status(work_dir)["verification"]["verdict"] == "INCONCLUSIVE"
    assert run(*args, "--kind", "verification", "--verdict", "PASS",
               "--resolves", str(gap_seq), "--summary", "affected check reran on B and passed") == 0
    assert run(*args, "--kind", "lifecycle", "--event", "finalized",
               "--summary", "current state verified") == 0
    assert events(work_dir)[old_pass["seq"] - 1] == old_pass
    assert derive_status(work_dir)["openVerifications"] == []
    assert run("validate", "--dir", str(work_dir)) == 0
