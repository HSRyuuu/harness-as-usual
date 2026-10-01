"""Script-enforced core rules.

Each test here pins a rule the harness guarantees rather than documents.
"""

from __future__ import annotations

import json

import pytest

from as_usual_record.validation import audit_sealed, validate_record


def _plan(work_dir) -> None:
    """The execution contract rule 7 reviews. Its content is not the script's business."""
    (work_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")


def _verification_file(work_dir) -> None:
    (work_dir / "verification.md").write_text("# Verification\n", encoding="utf-8")


def _review(
    work_dir,
    run,
    summary: str = "1 finding, fixed",
    phase: str = "write-plan",
    status: str = "success",
) -> int:
    return run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "review",
        "--summary",
        summary,
        "--phase",
        phase,
        "--status",
        status,
    )


def _approve(
    work_dir,
    run,
    action: str = "execution",
    actor: str = "user",
    status: str = "success",
) -> int:
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
        "--actor",
        actor,
        "--status",
        status,
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


def _finalize(work_dir, run, *extra: str, actor: str = "claude") -> int:
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
        "--actor",
        actor,
        *extra,
    )


def test_verification_without_verdict_is_refused(make_work, run):
    work_dir = make_work()
    assert (
        run("add", "--dir", str(work_dir), "--kind", "verification", "--summary", "ran the tests")
        == 2
    )


def test_verification_with_verdict_is_recorded(make_work, run, events):
    work_dir = make_work()
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


def test_inconclusive_is_a_valid_verdict(make_work, run, events):
    work_dir = make_work()
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


def test_confirming_requires_evidence(make_work, run):
    work_dir = make_work()
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


def test_confirming_with_evidence_succeeds(make_work, run, events):
    work_dir = make_work()
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


def test_cancelling_requires_reason(make_work, run):
    work_dir = make_work()
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


def test_status_change_target_must_exist(make_work, run):
    work_dir = make_work()
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


def test_status_change_target_must_be_a_reasoning_entry(make_work, run):
    work_dir = make_work()

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


# --- Rule 7: the plan review that clears execution approval (R1) ---------------


def test_execution_approval_requires_a_prior_plan_review(make_work, run):
    work_dir = make_work()
    _plan(work_dir)

    assert _approve(work_dir, run) == 2


def test_execution_approval_passes_after_a_plan_review(make_work, run):
    work_dir = make_work()
    _plan(work_dir)
    _review(work_dir, run, summary="2 findings, both fixed")

    assert _approve(work_dir, run) == 0


def test_execution_approval_is_refused_without_a_plan_file(make_work, run, capsys):
    """Rule 7 has two halves the script can see, and this is the first one.

    A review with nothing on disk to review is a claim, not a contract.
    """
    work_dir = make_work()
    _review(work_dir, run)
    capsys.readouterr()

    assert _approve(work_dir, run) == 2
    assert "plan.md" in capsys.readouterr().err


def test_the_missing_plan_and_missing_review_refusals_are_distinct(make_work, run, capsys):
    work_dir = make_work()
    capsys.readouterr()
    _approve(work_dir, run)
    without_plan = capsys.readouterr().err

    _plan(work_dir)
    _approve(work_dir, run)
    without_review = capsys.readouterr().err

    assert "plan.md" in without_plan
    assert "no review is recorded" in without_review
    assert without_plan != without_review


def test_a_review_execution_review_does_not_clear_the_plan_review_gate(make_work, run, capsys):
    """The review that satisfies rule 7 is the pre-approval one, not any review.

    Reviewing what already shipped, or cleaning up after it, says nothing about
    whether the plan was worth executing.
    """
    work_dir = make_work()
    _plan(work_dir)
    _review(work_dir, run, summary="post-execution findings", phase="review-execution")
    capsys.readouterr()

    assert _approve(work_dir, run) == 2
    assert "--phase write-plan" in capsys.readouterr().err


def test_a_cleanup_code_review_does_not_clear_the_plan_review_gate(make_work, run):
    work_dir = make_work()
    _plan(work_dir)
    _review(work_dir, run, summary="cleanup pass", phase="cleanup-code")

    assert _approve(work_dir, run) == 2


def test_a_failed_plan_review_does_not_clear_the_gate(make_work, run):
    """A review recorded as an error is a review that did not finish."""
    work_dir = make_work()
    _plan(work_dir)
    _review(work_dir, run, summary="review aborted", status="error")

    assert _approve(work_dir, run) == 2


def test_the_wrong_review_refusal_names_the_reviews_it_saw(make_work, run, capsys):
    work_dir = make_work()
    _plan(work_dir)
    _review(work_dir, run, summary="post-execution findings", phase="review-execution")
    capsys.readouterr()

    _approve(work_dir, run)

    assert "phase=review-execution" in capsys.readouterr().err


def test_a_phaseless_review_does_not_clear_the_gate(make_work, run):
    """Recorded before the phase was required — it may be any kind of review."""
    work_dir = make_work()
    _plan(work_dir)
    run("add", "--dir", str(work_dir), "--kind", "review", "--summary", "looked at it")

    assert _approve(work_dir, run) == 2


def test_reapproval_is_refused_without_a_newer_review(make_work, run):
    """A review spent on the first approval cannot pay for the second.

    The script cannot tell whether the plan changed, so it asks for the cheap
    thing — look at the plan again — rather than guessing.
    """
    work_dir = make_work()
    _plan(work_dir)
    _review(work_dir, run)
    assert _approve(work_dir, run) == 0

    assert _approve(work_dir, run) == 2


def test_reapproval_refusal_names_the_approval_it_is_measured_against(make_work, run, capsys):
    """Pointing at the seq is the message's job.

    A user whose record already holds a review reads "no review" as wrong unless
    the refusal says which approval reset the requirement.
    """
    work_dir = make_work()
    _plan(work_dir)
    _review(work_dir, run)
    _approve(work_dir, run)
    approval_seq = 3
    capsys.readouterr()

    _approve(work_dir, run)

    assert f"seq {approval_seq}" in capsys.readouterr().err


def test_reapproval_survives_a_hand_edited_approval_seq(make_work, run, capsys):
    """A corrupted seq is a refusal that says so, not a TypeError."""
    work_dir = make_work()
    _plan(work_dir)
    _review(work_dir, run)
    assert _approve(work_dir, run) == 0

    path = work_dir / "audit.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    broken = json.loads(lines[-1])
    broken["seq"] = "three"
    lines[-1] = json.dumps(broken)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    capsys.readouterr()

    assert _approve(work_dir, run) == 2
    assert "hand-edited" in capsys.readouterr().err


def test_reapproval_passes_with_a_review_after_the_last_approval(make_work, run):
    work_dir = make_work()
    _plan(work_dir)
    _review(work_dir, run)
    _approve(work_dir, run)

    _review(work_dir, run, summary="re-checked after the plan changed")
    assert _approve(work_dir, run) == 0


def test_a_later_execution_approval_is_gated_even_after_investigating(make_work, run):
    """Investigation carries on into implementation in the same folder.

    A reproduction approved while investigating does not stand in for the plan
    review the later execution approval needs.
    """
    work_dir = make_work()
    assert _approve(work_dir, run, action="reproduction") == 0
    _plan(work_dir)

    assert _approve(work_dir, run) == 2
    _review(work_dir, run)
    assert _approve(work_dir, run) == 0


def test_reproduction_approval_is_not_gated_on_a_plan_review(make_work, run, events):
    """A reproduction script is written to learn, not to change the product."""
    work_dir = make_work()

    assert _approve(work_dir, run, action="reproduction") == 0
    assert events(work_dir)[-1]["data"]["action"] == "reproduction"


def test_legacy_issue_execution_approval_is_not_gated_on_a_plan_review(make_legacy, run):
    """A legacy issue recorded its reproduction scripts as `execution`."""
    work_dir = make_legacy("issue")

    assert _approve(work_dir, run) == 0


@pytest.mark.parametrize("unit", ["topic", "direct-work", "inbox"])
def test_legacy_non_issue_execution_approval_is_still_gated(make_legacy, run, unit):
    work_dir = make_legacy(unit)
    _plan(work_dir)

    assert _approve(work_dir, run) == 2
    _review(work_dir, run)
    assert _approve(work_dir, run) == 0


def test_high_risk_approval_is_not_gated_on_a_review(make_work, run):
    work_dir = make_work()

    assert _approve(work_dir, run, action="high-risk") == 0


def test_git_action_approval_is_not_gated_on_a_review(make_work, run):
    work_dir = make_work()

    assert _approve(work_dir, run, action="git-action") == 0


# --- Rule 2/4: an approval is the user's decision (R2) -------------------------


def test_every_approval_action_is_refused_without_actor_user(make_work, run):
    for action in ("execution", "reproduction", "high-risk", "git-action"):
        for actor in ("claude", "codex", "system"):
            work_dir = make_work(slug=f"2026-07-25-{action}-{actor}")
            _plan(work_dir)
            _review(work_dir, run)

            assert _approve(work_dir, run, action=action, actor=actor) == 2, (action, actor)


def test_every_approval_action_is_refused_on_a_non_success_status(make_work, run):
    for action in ("execution", "reproduction", "high-risk", "git-action"):
        for status in ("error", "warning"):
            work_dir = make_work(slug=f"2026-07-25-{action}-{status}")
            _plan(work_dir)
            _review(work_dir, run)

            assert _approve(work_dir, run, action=action, status=status) == 2, (action, status)


def test_every_approval_action_passes_as_a_successful_user_decision(make_work, run):
    for action in ("execution", "reproduction", "high-risk", "git-action"):
        work_dir = make_work(slug=f"2026-07-25-{action}-ok")
        _plan(work_dir)
        _review(work_dir, run)

        assert _approve(work_dir, run, action=action) == 0, action


def test_the_actor_refusal_says_what_to_record_instead(make_work, run, capsys):
    work_dir = make_work()
    _plan(work_dir)
    _review(work_dir, run)
    capsys.readouterr()

    _approve(work_dir, run, actor="claude")

    message = capsys.readouterr().err
    assert "--actor user" in message
    assert "--actor claude" in message


def test_the_default_actor_no_longer_clears_an_approval(make_work, run):
    """The hole this closes: a whole record with no user event in it at all."""
    work_dir = make_work()
    _plan(work_dir)
    _review(work_dir, run)

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


# --- Rule 3: closing a record (R3, R5) -----------------------------------------


def _executed(work_dir, run) -> None:
    """An approved execution: what makes finalizing a completion claim."""
    _plan(work_dir)
    _review(work_dir, run)
    assert _approve(work_dir, run) == 0


def _confirmed_conclusion(work_dir, run, events) -> None:
    """A conclusion.md resting on a confirmed entry."""
    (work_dir / "conclusion.md").write_text("# Conclusion\n", encoding="utf-8")
    run("add", "--dir", str(work_dir), "--kind", "hypothesis", "--summary", "cache staleness")
    hypothesis = events(work_dir)[-1]["seq"]
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
            str(hypothesis),
            "--to",
            "confirmed",
            "--evidence",
            "reproduced with a cold cache",
        )
        == 0
    )


def _cancel(work_dir, run) -> int:
    return run(
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


def test_a_fresh_record_has_nothing_to_finalize(make_work, run, capsys):
    """Neither an approved execution nor a conclusion: no completion to declare."""
    work_dir = make_work()
    capsys.readouterr()

    assert _finalize(work_dir, run) == 2
    assert "nothing to finalize" in capsys.readouterr().err


def test_nothing_to_finalize_is_refused_even_with_a_reason(make_work, run):
    work_dir = make_work()

    assert _finalize(work_dir, run, "--reason", "not going anywhere", actor="user") == 2


def test_a_verification_alone_is_nothing_to_finalize(make_work, run):
    """Evidence without an approved execution proves nothing was completed."""
    work_dir = make_work()
    _record_verification(work_dir, run)

    assert _finalize(work_dir, run) == 2


def test_a_reproduction_approval_is_nothing_to_finalize(make_work, run):
    """A reproduction is not a code change, so it makes no completion claim."""
    work_dir = make_work()
    _approve(work_dir, run, action="reproduction")
    _record_verification(work_dir, run)

    assert _finalize(work_dir, run) == 2


def test_a_record_with_nothing_to_finalize_may_be_cancelled(make_work, run):
    work_dir = make_work()

    assert _cancel(work_dir, run) == 0


def test_a_conclusion_needs_a_confirmed_entry(make_work, run, capsys):
    work_dir = make_work()
    (work_dir / "conclusion.md").write_text("# Conclusion\n", encoding="utf-8")
    run("add", "--dir", str(work_dir), "--kind", "hypothesis", "--summary", "cache staleness")
    capsys.readouterr()

    assert _finalize(work_dir, run) == 2
    assert "confirmed entry" in capsys.readouterr().err


def test_a_conclusion_finalizes_once_it_rests_on_a_confirmed_entry(make_work, run, events):
    work_dir = make_work()
    _confirmed_conclusion(work_dir, run, events)

    assert _finalize(work_dir, run) == 0


def test_a_conclusion_only_record_needs_no_verification(make_work, run, events):
    """Investigation ends in an understanding, not a completion claim."""
    work_dir = make_work()
    _confirmed_conclusion(work_dir, run, events)
    (work_dir / "requirements.md").write_text("# Requirements\n", encoding="utf-8")

    assert _finalize(work_dir, run) == 0


def test_an_executed_record_cannot_finalize_without_a_verification(make_work, run):
    work_dir = make_work()
    _executed(work_dir, run)

    assert _finalize(work_dir, run) == 2


def test_executed_without_requirements_needs_no_verification_file(make_work, run):
    """Settled work: the recorded verification is the evidence."""
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run)

    assert _finalize(work_dir, run) == 0


def test_requirements_make_verification_file_required(make_work, run, capsys):
    """The record names the evidence; the document is where a later session reads it."""
    work_dir = make_work()
    (work_dir / "requirements.md").write_text("# Requirements\n", encoding="utf-8")
    _executed(work_dir, run)
    _record_verification(work_dir, run)
    capsys.readouterr()

    assert _finalize(work_dir, run) == 2
    assert "verification.md" in capsys.readouterr().err


def test_requirements_finalize_once_the_verification_file_exists(make_work, run):
    work_dir = make_work()
    (work_dir / "requirements.md").write_text("# Requirements\n", encoding="utf-8")
    _executed(work_dir, run)
    _record_verification(work_dir, run)
    _verification_file(work_dir)

    assert _finalize(work_dir, run) == 0


def test_a_verification_directory_does_not_satisfy_the_file_gate(make_work, run):
    work_dir = make_work()
    (work_dir / "requirements.md").write_text("# Requirements\n", encoding="utf-8")
    _executed(work_dir, run)
    _record_verification(work_dir, run)
    (work_dir / "verification.md").mkdir()

    assert _finalize(work_dir, run) == 2


def test_a_cancelled_record_needs_no_verification(make_work, run):
    work_dir = make_work()
    (work_dir / "requirements.md").write_text("# Requirements\n", encoding="utf-8")
    _executed(work_dir, run)

    assert _cancel(work_dir, run) == 0


def test_investigated_and_implemented_needs_both_gates(make_work, run, events):
    """A folder that concluded and then carried on into a change owes both."""
    work_dir = make_work()
    (work_dir / "conclusion.md").write_text("# Conclusion\n", encoding="utf-8")
    run("add", "--dir", str(work_dir), "--kind", "hypothesis", "--summary", "cache staleness")
    _executed(work_dir, run)
    _record_verification(work_dir, run)

    # Verified, but the conclusion rests on nothing yet.
    assert _finalize(work_dir, run) == 2


def test_investigated_and_implemented_needs_a_verification_too(make_work, run, events):
    work_dir = make_work()
    _confirmed_conclusion(work_dir, run, events)
    _executed(work_dir, run)

    # The conclusion is confirmed, but the change was never verified.
    assert _finalize(work_dir, run) == 2
    _record_verification(work_dir, run)
    assert _finalize(work_dir, run) == 0


def test_inconclusive_verification_finalizes_only_with_a_reason(make_work, run):
    """An honestly unverifiable result may still close — but it has to say why.

    The earlier contract let INCONCLUSIVE through silently. Closing is still
    reachable; what changed is that the record now carries the judgment instead
    of leaving a reader to infer it from a verdict nobody acted on.
    """
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")

    assert _finalize(work_dir, run) == 2
    assert (
        _finalize(work_dir, run, "--reason", "no UI available to screenshot", actor="user") == 0
    )


def test_finalizing_with_a_reason_is_the_users_call(make_work, run, capsys):
    """Accepting a known gap is a decision, so the agent may not sign it alone."""
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    capsys.readouterr()

    assert _finalize(work_dir, run, "--reason", "shipping anyway") == 2
    assert "--actor user" in capsys.readouterr().err


def test_finalizing_with_a_reason_is_refused_on_a_non_success_status(make_work, run):
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")

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
            "--actor",
            "user",
            "--status",
            "warning",
            "--reason",
            "shipping anyway",
        )
        == 2
    )


def test_a_clean_finalize_needs_no_user_actor(make_work, run):
    """Only the door over an open gap is the user's; closing clean is not."""
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="PASS")

    assert _finalize(work_dir, run) == 0


def test_finalize_is_refused_on_a_failing_verdict(make_work, run):
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="FAIL")

    assert _finalize(work_dir, run) == 2


def test_finalize_on_a_failing_verdict_passes_with_a_reason(make_work, run, events):
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="FAIL")

    assert (
        _finalize(work_dir, run, "--reason", "shipping the partial fix on purpose", actor="user")
        == 0
    )
    assert events(work_dir)[-1]["data"]["reason"] == "shipping the partial fix on purpose"


def test_an_unresolved_failure_is_not_cancelled_out_by_an_earlier_pass(make_work, run):
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="PASS")
    _record_verification(work_dir, run, verdict="FAIL")

    assert _finalize(work_dir, run) == 2


def test_an_earlier_gap_is_not_buried_by_a_later_pass(make_work, run, events):
    """The hole this rule closes: a unit finalizing clean on unverified criteria.

    Two real units did exactly this — an INCONCLUSIVE on one acceptance
    criterion, then passing runs on other surfaces, and the close went through
    with nothing recorded about the gap.
    """
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    _record_verification(work_dir, run, verdict="PASS")

    assert _finalize(work_dir, run) == 2


def test_a_later_pass_resolves_the_gap_when_it_names_the_seq(make_work, run, events):
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    gap = events(work_dir)[-1]["seq"]
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "verification",
        "--summary",
        "re-ran with the data in place",
        "--verdict",
        "PASS",
        "--resolves",
        str(gap),
    )

    assert _finalize(work_dir, run) == 0


def test_unresolved_verifications_finalize_with_a_reason(make_work, run):
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    _record_verification(work_dir, run, verdict="PASS")

    assert _finalize(work_dir, run, "--reason", "test data never arrived", actor="user") == 0


def test_the_refusal_names_every_unresolved_seq(make_work, run, events, capsys):
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    gap = events(work_dir)[-1]["seq"]
    _record_verification(work_dir, run, verdict="FAIL")

    assert _finalize(work_dir, run) == 2
    message = capsys.readouterr().err
    assert f"seq {gap} INCONCLUSIVE" in message
    assert f"seq {gap + 1} FAIL" in message


def test_a_resolving_verification_that_itself_failed_stays_open(make_work, run, events):
    """Resolving one gap by opening another does not clear the gate."""
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    gap = events(work_dir)[-1]["seq"]
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "verification",
        "--summary",
        "re-ran, still cannot tell",
        "--verdict",
        "INCONCLUSIVE",
        "--resolves",
        str(gap),
    )

    assert _finalize(work_dir, run) == 2


def test_finalize_without_any_verification_ignores_reason(make_work, run):
    """No evidence and bad evidence are different failures.

    `--reason` accepts a verdict the user has seen. It must not stand in for a
    verification that was never run.
    """
    work_dir = make_work()
    _executed(work_dir, run)

    assert _finalize(work_dir, run, "--reason", "trust me", actor="user") == 2


# --- Legacy records keep their two shims ---------------------------------------


def test_legacy_issue_execution_does_not_require_a_verification(make_legacy, run, events):
    """A legacy issue's `execution` was a reproduction, not a completion claim."""
    work_dir = make_legacy("issue")
    assert _approve(work_dir, run) == 0
    _confirmed_conclusion(work_dir, run, events)

    assert _finalize(work_dir, run) == 0


def test_legacy_issue_execution_alone_is_nothing_to_finalize(make_legacy, run):
    work_dir = make_legacy("issue")
    _approve(work_dir, run)

    assert _finalize(work_dir, run) == 2


def test_legacy_issue_still_needs_a_confirmed_entry(make_legacy, run):
    work_dir = make_legacy("issue")
    (work_dir / "conclusion.md").write_text("# Conclusion\n", encoding="utf-8")

    assert _finalize(work_dir, run) == 2


def test_legacy_topic_needs_verification_md_without_requirements(make_legacy, run, capsys):
    """A legacy topic always agreed requirements, even if the file is missing."""
    work_dir = make_legacy("topic")
    _executed(work_dir, run)
    _record_verification(work_dir, run)
    capsys.readouterr()

    assert _finalize(work_dir, run) == 2
    assert "verification.md" in capsys.readouterr().err
    _verification_file(work_dir)
    assert _finalize(work_dir, run) == 0


def test_legacy_direct_work_finalizes_on_content(make_legacy, run):
    work_dir = make_legacy("direct-work")
    assert _finalize(work_dir, run) == 2
    _executed(work_dir, run)
    _record_verification(work_dir, run)

    assert _finalize(work_dir, run) == 0


def test_legacy_inbox_has_nothing_to_finalize(make_legacy, run):
    work_dir = make_legacy("inbox")

    assert _finalize(work_dir, run, "--reason", "not going anywhere", actor="user") == 2
    assert _cancel(work_dir, run) == 0


def test_lifecycle_requires_a_known_event(make_work, run):
    work_dir = make_work()
    assert (
        run("add", "--dir", str(work_dir), "--kind", "lifecycle", "--summary", "s") == 2
    )


# --- --resolves closes one open entry of the same kind (R4) --------------------


def _resolving_verification(work_dir, run, target: int, verdict: str = "PASS") -> int:
    return run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "verification",
        "--summary",
        "re-run",
        "--verdict",
        verdict,
        "--resolves",
        str(target),
    )


def _blocker(work_dir, run, summary: str = "blocked on the vendor", *extra: str) -> int:
    return run(
        "add", "--dir", str(work_dir), "--kind", "blocker", "--summary", summary, *extra
    )


def test_resolves_refuses_a_seq_that_does_not_exist(make_work, run):
    work_dir = make_work()
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")

    assert _resolving_verification(work_dir, run, 99) == 2


def test_resolves_refuses_a_non_verification_target(make_work, run, events):
    work_dir = make_work()
    run("add", "--dir", str(work_dir), "--kind", "note", "--summary", "just a note")
    note = events(work_dir)[-1]["seq"]

    assert _resolving_verification(work_dir, run, note) == 2


def test_resolves_refuses_a_passing_target(make_work, run, events):
    work_dir = make_work()
    _record_verification(work_dir, run, verdict="PASS")
    passing = events(work_dir)[-1]["seq"]

    assert _resolving_verification(work_dir, run, passing) == 2


def test_resolves_refuses_its_own_or_a_later_seq(make_work, run, events):
    """The entry being added is not in the record yet, so forward seqs cannot resolve."""
    work_dir = make_work()
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    own = events(work_dir)[-1]["seq"] + 1

    assert _resolving_verification(work_dir, run, own) == 2
    assert _resolving_verification(work_dir, run, own + 5) == 2


def test_resolves_is_refused_on_kinds_that_have_nothing_to_close(make_work, run, events):
    work_dir = make_work()
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    gap = events(work_dir)[-1]["seq"]

    for kind in ("note", "work", "review", "decision", "hypothesis"):
        assert (
            run(
                "add",
                "--dir",
                str(work_dir),
                "--kind",
                kind,
                "--summary",
                "unrelated",
                "--resolves",
                str(gap),
            )
            == 2
        ), kind


def test_the_wrong_kind_refusal_names_the_two_kinds_that_do(make_work, run, events, capsys):
    work_dir = make_work()
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    gap = events(work_dir)[-1]["seq"]
    capsys.readouterr()

    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "note",
        "--summary",
        "unrelated",
        "--resolves",
        str(gap),
    )

    message = capsys.readouterr().err
    assert "blocker" in message
    assert "verification" in message


def test_a_verification_may_not_resolve_a_blocker(make_work, run, events):
    work_dir = make_work()
    _blocker(work_dir, run)
    blocker = events(work_dir)[-1]["seq"]

    assert _resolving_verification(work_dir, run, blocker) == 2


def test_a_blocker_may_not_resolve_a_verification(make_work, run, events):
    work_dir = make_work()
    _record_verification(work_dir, run, verdict="FAIL")
    failure = events(work_dir)[-1]["seq"]

    assert _blocker(work_dir, run, "cleared", "--resolves", str(failure)) == 2


def test_a_blocker_may_not_resolve_a_seq_that_does_not_exist(make_work, run):
    work_dir = make_work()

    assert _blocker(work_dir, run, "cleared", "--resolves", "99") == 2


def test_a_blocker_resolves_an_earlier_blocker(make_work, run, events):
    work_dir = make_work()
    _blocker(work_dir, run, "waiting on the vendor")
    first = events(work_dir)[-1]["seq"]

    assert _blocker(work_dir, run, "vendor replied", "--resolves", str(first)) == 0
    assert events(work_dir)[-1]["data"]["resolves"] == first


def test_a_blocker_cannot_be_resolved_twice(make_work, run, events):
    """Two closes on one blocker would hide whichever gap is still open."""
    work_dir = make_work()
    _blocker(work_dir, run, "waiting on the vendor")
    first = events(work_dir)[-1]["seq"]
    _blocker(work_dir, run, "vendor replied", "--resolves", str(first))

    assert _blocker(work_dir, run, "and again", "--resolves", str(first)) == 2


def test_a_verification_gap_cannot_be_resolved_twice(make_work, run, events):
    work_dir = make_work()
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    gap = events(work_dir)[-1]["seq"]
    _resolving_verification(work_dir, run, gap)

    assert _resolving_verification(work_dir, run, gap) == 2


def test_the_double_resolve_refusal_says_it_was_already_resolved(make_work, run, events, capsys):
    work_dir = make_work()
    _blocker(work_dir, run, "waiting on the vendor")
    first = events(work_dir)[-1]["seq"]
    _blocker(work_dir, run, "vendor replied", "--resolves", str(first))
    capsys.readouterr()

    _blocker(work_dir, run, "and again", "--resolves", str(first))

    assert "already resolved" in capsys.readouterr().err


def _seal_by_hand(work_dir, events, unit: str = "work", **data) -> None:
    """Append a finalized event straight to the file.

    The append gate refuses these shapes today; the point is auditing a record
    that got past an older one.
    """
    with (work_dir / "audit.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "seq": len(events(work_dir)) + 1,
                    "ts": "2026-08-13T13:03:16+09:00",
                    "actor": "claude",
                    "unit": unit,
                    "kind": "lifecycle",
                    "status": "success",
                    "summary": "closed",
                    "data": {"event": "finalized", **data},
                }
            )
            + "\n"
        )


def test_a_sealed_unit_with_an_open_gap_and_no_reason_warns(make_work, run, events):
    """The gate that would refuse this today did not exist when such records closed.

    Reporting it as a problem would reach backwards and invalidate a record that
    was legal when written, so it is a warning and the exit code stays clean.
    """
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    gap = events(work_dir)[-1]["seq"]
    _seal_by_hand(work_dir, events)

    warnings = audit_sealed(work_dir)
    assert len(warnings) == 1
    assert f"seq {gap} INCONCLUSIVE" in warnings[0]
    assert "no --reason" in warnings[0]
    assert validate_record(work_dir) == []


def test_a_sealed_unit_whose_reason_is_not_the_users_warns(make_work, run, events):
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    _seal_by_hand(work_dir, events, reason="shipping anyway")

    warnings = audit_sealed(work_dir)
    assert len(warnings) == 1
    assert "not\nthe user" in warnings[0] or "not the user" in warnings[0]


def test_a_sealed_record_with_requirements_but_no_verification_md_warns(make_work, run, events):
    work_dir = make_work()
    (work_dir / "requirements.md").write_text("# Requirements\n", encoding="utf-8")
    _executed(work_dir, run)
    _record_verification(work_dir, run)
    _seal_by_hand(work_dir, events)

    warnings = audit_sealed(work_dir)
    assert any("no verification.md" in warning for warning in warnings)
    assert validate_record(work_dir) == []


def test_a_sealed_record_with_nothing_to_finalize_warns(make_work, events):
    work_dir = make_work()
    _seal_by_hand(work_dir, events)

    warnings = audit_sealed(work_dir)
    assert any("neither an approved execution nor a conclusion.md" in w for w in warnings)
    assert validate_record(work_dir) == []


def test_a_sealed_legacy_topic_without_verification_md_warns_but_stays_valid(
    make_legacy, run, events
):
    work_dir = make_legacy("topic")
    _executed(work_dir, run)
    _record_verification(work_dir, run)
    _seal_by_hand(work_dir, events, unit="topic")

    warnings = audit_sealed(work_dir)
    assert any("no verification.md" in warning for warning in warnings)
    assert validate_record(work_dir) == []


def test_a_sealed_legacy_issue_audits_on_its_conclusion(make_legacy, run, events):
    """Its `execution` approvals were reproductions: no verification is owed."""
    work_dir = make_legacy("issue")
    _approve(work_dir, run)
    _confirmed_conclusion(work_dir, run, events)
    assert _finalize(work_dir, run) == 0

    assert audit_sealed(work_dir) == []
    assert validate_record(work_dir) == []


def test_an_open_unit_is_not_audited_as_sealed(make_work, run):
    work_dir = make_work()
    _executed(work_dir, run)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")

    assert audit_sealed(work_dir) == []
