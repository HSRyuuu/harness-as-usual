"""Script-enforced core rules.

Each test here pins a rule the harness guarantees rather than documents.
"""

from __future__ import annotations


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


def test_issue_finalizes_once_the_conclusion_exists(make_unit, run):
    work_dir = make_unit("issue")
    (work_dir / "conclusion.md").write_text("# Conclusion\n", encoding="utf-8")

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


def test_topic_finalize_needs_no_conclusion_file(make_unit, run):
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
        == 0
    )


def test_lifecycle_requires_a_known_event(make_unit, run):
    work_dir = make_unit("topic")
    assert (
        run("add", "--dir", str(work_dir), "--kind", "lifecycle", "--summary", "s") == 2
    )
