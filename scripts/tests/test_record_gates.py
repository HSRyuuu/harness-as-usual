"""Script-enforced core rules.

Each test here pins a rule the harness guarantees rather than documents.
"""

from __future__ import annotations

import json


def test_verification_without_verdict_is_refused(make_unit, run):
    work_dir = make_unit("topic")
    assert (
        run("add", "--dir", str(work_dir), "--kind", "verification", "--summary", "ran the tests")
        == 2
    )


def test_verification_with_verdict_is_recorded(make_unit, run, events):
    work_dir = make_unit("topic")
    assert (
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
        == 0
    )
    assert events(work_dir)[-1]["data"]["verdict"] == "PASS"


def test_inconclusive_is_a_valid_verdict(make_unit, run, events):
    work_dir = make_unit("direct-work")
    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "verification",
            "--summary",
            "no UI available to screenshot",
            "--verdict",
            "INCONCLUSIVE",
        )
        == 0
    )
    assert events(work_dir)[-1]["data"]["verdict"] == "INCONCLUSIVE"


def test_confirming_requires_evidence(make_unit, run):
    work_dir = make_unit("issue")
    run("add", "--dir", str(work_dir), "--kind", "hypothesis", "--summary", "cache staleness")

    assert (
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
        )
        == 2
    )


def test_confirming_with_evidence_succeeds(make_unit, run, events):
    work_dir = make_unit("issue")
    run("add", "--dir", str(work_dir), "--kind", "hypothesis", "--summary", "cache staleness")

    assert (
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
            "reproduced twice with TTL=0",
        )
        == 0
    )
    assert events(work_dir)[-1]["data"]["target"] == 2


def test_cancelling_requires_reason(make_unit, run):
    work_dir = make_unit("issue")
    run("add", "--dir", str(work_dir), "--kind", "hypothesis", "--summary", "cache staleness")

    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "status-change",
            "--summary",
            "retracted",
            "--target",
            "2",
            "--to",
            "cancelled",
        )
        == 2
    )


def test_status_change_target_must_exist(make_unit, run):
    work_dir = make_unit("issue")
    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "status-change",
            "--summary",
            "confirmed",
            "--target",
            "99",
            "--to",
            "confirmed",
            "--evidence",
            "e",
        )
        == 2
    )


def test_status_change_target_must_be_a_reasoning_entry(make_unit, run):
    work_dir = make_unit("issue")

    # seq 1 is the lifecycle created event, which carries no reasoning.
    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "status-change",
            "--summary",
            "confirmed",
            "--target",
            "1",
            "--to",
            "confirmed",
            "--evidence",
            "e",
        )
        == 2
    )


def test_execution_approval_requires_a_prior_plan_review(make_unit, run):
    work_dir = make_unit("topic")
    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "approval",
            "--summary",
            "user said go",
            "--action",
            "execution",
        )
        == 2
    )


def test_execution_approval_passes_after_a_review(make_unit, run):
    work_dir = make_unit("topic")
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "review",
        "--summary",
        "2 findings, both fixed",
        "--data",
        "findings=2",
    )

    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "approval",
            "--summary",
            "user said go",
            "--action",
            "execution",
        )
        == 0
    )


def _review(work_dir, run, summary="1 finding, fixed") -> int:
    return run("add", "--dir", str(work_dir), "--kind", "review", "--summary", summary)


def _approve(work_dir, run, action="execution") -> int:
    return run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "approval",
        "--summary",
        "user said go",
        "--action",
        action,
    )


def test_reapproval_is_refused_without_a_newer_review(make_unit, run):
    """A review spent on the first approval cannot pay for the second.

    The script cannot tell whether the plan changed, so it asks for the cheap
    thing — look at the plan again — rather than guessing.
    """
    work_dir = make_unit("topic")
    _review(work_dir, run)
    assert _approve(work_dir, run) == 0

    assert _approve(work_dir, run) == 2


def test_reapproval_refusal_names_the_approval_it_is_measured_against(make_unit, run, capsys):
    """Pointing at the seq is the message's job.

    A user whose record already holds a review reads "no review" as wrong unless
    the refusal says which approval reset the requirement.
    """
    work_dir = make_unit("topic")
    _review(work_dir, run)
    _approve(work_dir, run)
    approval_seq = 3
    capsys.readouterr()

    _approve(work_dir, run)

    assert f"seq {approval_seq}" in capsys.readouterr().err


def test_reapproval_survives_a_hand_edited_approval_seq(make_unit, run):
    """A corrupted seq is a refusal, not a TypeError."""
    work_dir = make_unit("topic")
    _review(work_dir, run)
    _approve(work_dir, run)

    path = work_dir / "audit.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    broken = json.loads(lines[-1])
    broken["seq"] = "three"
    lines[-1] = json.dumps(broken)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert _approve(work_dir, run) == 2


def test_reapproval_passes_with_a_review_after_the_last_approval(make_unit, run):
    work_dir = make_unit("topic")
    _review(work_dir, run)
    _approve(work_dir, run)

    _review(work_dir, run, summary="re-checked after the plan changed")
    assert _approve(work_dir, run) == 0


def test_high_risk_approval_is_not_gated_on_a_review(make_unit, run):
    work_dir = make_unit("topic")

    assert _approve(work_dir, run, action="high-risk") == 0


def test_direct_work_also_needs_the_plan_review(make_unit, run):
    work_dir = make_unit("direct-work")
    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "approval",
            "--summary",
            "go",
            "--action",
            "execution",
        )
        == 2
    )


def test_issue_execution_approval_is_not_gated_on_a_plan_review(make_unit, run):
    work_dir = make_unit("issue")
    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "approval",
            "--summary",
            "user approved a reproduction script",
            "--action",
            "execution",
        )
        == 0
    )


def test_high_risk_approval_needs_no_review(make_unit, run):
    work_dir = make_unit("topic")
    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "approval",
            "--summary",
            "user approved deleting build/",
            "--action",
            "high-risk",
        )
        == 0
    )


def test_issue_cannot_finalize_without_a_conclusion(make_unit, run):
    work_dir = make_unit("issue")
    assert (
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
        == 2
    )


def test_issue_cannot_finalize_without_a_confirmed_entry(make_unit, run):
    work_dir = make_unit("issue")
    (work_dir / "conclusion.md").write_text("# Conclusion\n", encoding="utf-8")
    run("add", "--dir", str(work_dir), "--kind", "hypothesis", "--summary", "cache staleness")

    assert (
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
        == 2
    )


def test_issue_finalizes_once_the_conclusion_rests_on_a_confirmed_entry(make_unit, run):
    work_dir = make_unit("issue")
    (work_dir / "conclusion.md").write_text("# Conclusion\n", encoding="utf-8")
    run("add", "--dir", str(work_dir), "--kind", "hypothesis", "--summary", "cache staleness")
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
        "reproduced with a cold cache",
    )

    assert (
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
        == 0
    )


def test_issue_may_be_cancelled_without_a_conclusion(make_unit, run):
    work_dir = make_unit("issue")
    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "lifecycle",
            "--summary",
            "user abandoned the investigation",
            "--event",
            "cancelled",
        )
        == 0
    )


def _record_verification(work_dir, run, verdict="PASS"):
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "verification",
        "--summary",
        "pytest -q: 12 passed",
        "--verdict",
        verdict,
    )


def test_topic_cannot_finalize_without_a_verification(make_unit, run):
    work_dir = make_unit("topic")
    assert (
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
        == 2
    )


def test_direct_work_cannot_finalize_without_a_verification(make_unit, run):
    work_dir = make_unit("direct-work")
    assert (
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
        == 2
    )


def _finalize(work_dir, run, *reason: str) -> int:
    return run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "lifecycle",
        "--summary",
        "closed",
        "--event",
        "finalized",
        *reason,
    )


def test_inconclusive_verification_finalizes_only_with_a_reason(make_unit, run):
    """An honestly unverifiable result may still close — but it has to say why.

    The earlier contract let INCONCLUSIVE through silently. Closing is still
    reachable; what changed is that the record now carries the judgment instead
    of leaving a reader to infer it from a verdict nobody acted on.
    """
    work_dir = make_unit("direct-work")
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")

    assert _finalize(work_dir, run) == 2
    assert _finalize(work_dir, run, "--reason", "no UI available to screenshot") == 0


def test_finalize_is_refused_on_a_failing_verdict(make_unit, run):
    work_dir = make_unit("topic")
    _record_verification(work_dir, run, verdict="FAIL")

    assert _finalize(work_dir, run) == 2


def test_finalize_on_a_failing_verdict_passes_with_a_reason(make_unit, run, events):
    work_dir = make_unit("topic")
    _record_verification(work_dir, run, verdict="FAIL")

    assert _finalize(work_dir, run, "--reason", "shipping the partial fix on purpose") == 0
    assert events(work_dir)[-1]["data"]["reason"] == "shipping the partial fix on purpose"


def test_finalize_reads_the_latest_verdict_not_the_first(make_unit, run):
    """A later failure is not cancelled out by an earlier pass."""
    work_dir = make_unit("topic")
    _record_verification(work_dir, run, verdict="PASS")
    _record_verification(work_dir, run, verdict="FAIL")

    assert _finalize(work_dir, run) == 2


def test_finalize_without_any_verification_ignores_reason(make_unit, run):
    """No evidence and bad evidence are different failures.

    `--reason` accepts a verdict the user has seen. It must not stand in for a
    verification that was never run.
    """
    work_dir = make_unit("topic")

    assert _finalize(work_dir, run, "--reason", "trust me") == 2


def test_finalize_still_passes_on_a_passing_verdict(make_unit, run):
    work_dir = make_unit("direct-work")
    _record_verification(work_dir, run, verdict="PASS")

    assert _finalize(work_dir, run) == 0


def test_unverified_topic_may_still_be_cancelled(make_unit, run):
    work_dir = make_unit("topic")
    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "lifecycle",
            "--summary",
            "user dropped it",
            "--event",
            "cancelled",
        )
        == 0
    )


def test_topic_finalize_needs_no_conclusion_file(make_unit, run):
    work_dir = make_unit("topic")
    _record_verification(work_dir, run)

    assert (
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
        == 0
    )


def test_lifecycle_requires_a_known_event(make_unit, run):
    work_dir = make_unit("topic")
    assert (
        run("add", "--dir", str(work_dir), "--kind", "lifecycle", "--summary", "s") == 2
    )
