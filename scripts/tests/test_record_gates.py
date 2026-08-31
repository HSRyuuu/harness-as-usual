"""Script-enforced core rules.

Each test here pins a rule the harness guarantees rather than documents.
"""

from __future__ import annotations

import json

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


# --- Rule 7: the plan review that clears execution approval (R1) ---------------


def test_execution_approval_requires_a_prior_plan_review(make_unit, run):
    work_dir = make_unit("topic")
    _plan(work_dir)

    assert _approve(work_dir, run) == 2


def test_execution_approval_passes_after_a_plan_review(make_unit, run):
    work_dir = make_unit("topic")
    _plan(work_dir)
    _review(work_dir, run, summary="2 findings, both fixed")

    assert _approve(work_dir, run) == 0


def test_execution_approval_is_refused_without_a_plan_file(make_unit, run, capsys):
    """Rule 7 has two halves the script can see, and this is the first one.

    A review with nothing on disk to review is a claim, not a contract.
    """
    work_dir = make_unit("topic")
    _review(work_dir, run)
    capsys.readouterr()

    assert _approve(work_dir, run) == 2
    assert "plan.md" in capsys.readouterr().err


def test_the_missing_plan_and_missing_review_refusals_are_distinct(make_unit, run, capsys):
    work_dir = make_unit("topic")
    capsys.readouterr()
    _approve(work_dir, run)
    without_plan = capsys.readouterr().err

    _plan(work_dir)
    _approve(work_dir, run)
    without_review = capsys.readouterr().err

    assert "plan.md" in without_plan
    assert "no review is recorded" in without_review
    assert without_plan != without_review


def test_a_review_execution_review_does_not_clear_the_plan_review_gate(make_unit, run, capsys):
    """The review that satisfies rule 7 is the pre-approval one, not any review.

    Reviewing what already shipped, or cleaning up after it, says nothing about
    whether the plan was worth executing.
    """
    work_dir = make_unit("topic")
    _plan(work_dir)
    _review(work_dir, run, summary="post-execution findings", phase="review-execution")
    capsys.readouterr()

    assert _approve(work_dir, run) == 2
    assert "--phase write-plan" in capsys.readouterr().err


def test_a_cleanup_code_review_does_not_clear_the_plan_review_gate(make_unit, run):
    work_dir = make_unit("topic")
    _plan(work_dir)
    _review(work_dir, run, summary="cleanup pass", phase="cleanup-code")

    assert _approve(work_dir, run) == 2


def test_a_failed_plan_review_does_not_clear_the_gate(make_unit, run):
    """A review recorded as an error is a review that did not finish."""
    work_dir = make_unit("topic")
    _plan(work_dir)
    _review(work_dir, run, summary="review aborted", status="error")

    assert _approve(work_dir, run) == 2


def test_the_wrong_review_refusal_names_the_reviews_it_saw(make_unit, run, capsys):
    work_dir = make_unit("topic")
    _plan(work_dir)
    _review(work_dir, run, summary="post-execution findings", phase="review-execution")
    capsys.readouterr()

    _approve(work_dir, run)

    assert "phase=review-execution" in capsys.readouterr().err


def test_a_phaseless_review_does_not_clear_the_gate(make_unit, run):
    """Recorded before the phase was required — it may be any kind of review."""
    work_dir = make_unit("topic")
    _plan(work_dir)
    run("add", "--dir", str(work_dir), "--kind", "review", "--summary", "looked at it")

    assert _approve(work_dir, run) == 2


def test_reapproval_is_refused_without_a_newer_review(make_unit, run):
    """A review spent on the first approval cannot pay for the second.

    The script cannot tell whether the plan changed, so it asks for the cheap
    thing — look at the plan again — rather than guessing.
    """
    work_dir = make_unit("topic")
    _plan(work_dir)
    _review(work_dir, run)
    assert _approve(work_dir, run) == 0

    assert _approve(work_dir, run) == 2


def test_reapproval_refusal_names_the_approval_it_is_measured_against(make_unit, run, capsys):
    """Pointing at the seq is the message's job.

    A user whose record already holds a review reads "no review" as wrong unless
    the refusal says which approval reset the requirement.
    """
    work_dir = make_unit("topic")
    _plan(work_dir)
    _review(work_dir, run)
    _approve(work_dir, run)
    approval_seq = 3
    capsys.readouterr()

    _approve(work_dir, run)

    assert f"seq {approval_seq}" in capsys.readouterr().err


def test_reapproval_survives_a_hand_edited_approval_seq(make_unit, run, capsys):
    """A corrupted seq is a refusal that says so, not a TypeError."""
    work_dir = make_unit("topic")
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


def test_reapproval_passes_with_a_review_after_the_last_approval(make_unit, run):
    work_dir = make_unit("topic")
    _plan(work_dir)
    _review(work_dir, run)
    _approve(work_dir, run)

    _review(work_dir, run, summary="re-checked after the plan changed")
    assert _approve(work_dir, run) == 0


def test_direct_work_also_needs_the_plan_review(make_unit, run):
    work_dir = make_unit("direct-work")
    _plan(work_dir)

    assert _approve(work_dir, run) == 2


def test_direct_work_execution_approval_passes_the_same_way(make_unit, run):
    work_dir = make_unit("direct-work")
    _plan(work_dir)
    _review(work_dir, run, summary="checklist re-read")

    assert _approve(work_dir, run) == 0


def test_issue_execution_approval_is_not_gated_on_a_plan_review(make_unit, run):
    work_dir = make_unit("issue")

    assert _approve(work_dir, run) == 0


def test_high_risk_approval_is_not_gated_on_a_review(make_unit, run):
    work_dir = make_unit("topic")

    assert _approve(work_dir, run, action="high-risk") == 0


def test_git_action_approval_is_not_gated_on_a_review(make_unit, run):
    work_dir = make_unit("topic")

    assert _approve(work_dir, run, action="git-action") == 0


# --- Rule 2/4: an approval is the user's decision (R2) -------------------------


def test_every_approval_action_is_refused_without_actor_user(make_unit, run):
    for action in ("execution", "high-risk", "git-action"):
        for actor in ("claude", "codex", "system"):
            work_dir = make_unit("topic", slug=f"2026-07-25-{action}-{actor}")
            _plan(work_dir)
            _review(work_dir, run)

            assert _approve(work_dir, run, action=action, actor=actor) == 2, (action, actor)


def test_every_approval_action_is_refused_on_a_non_success_status(make_unit, run):
    for action in ("execution", "high-risk", "git-action"):
        for status in ("error", "warning"):
            work_dir = make_unit("topic", slug=f"2026-07-25-{action}-{status}")
            _plan(work_dir)
            _review(work_dir, run)

            assert _approve(work_dir, run, action=action, status=status) == 2, (action, status)


def test_every_approval_action_passes_as_a_successful_user_decision(make_unit, run):
    for action in ("execution", "high-risk", "git-action"):
        work_dir = make_unit("topic", slug=f"2026-07-25-{action}-ok")
        _plan(work_dir)
        _review(work_dir, run)

        assert _approve(work_dir, run, action=action) == 0, action


def test_the_actor_refusal_says_what_to_record_instead(make_unit, run, capsys):
    work_dir = make_unit("topic")
    _plan(work_dir)
    _review(work_dir, run)
    capsys.readouterr()

    _approve(work_dir, run, actor="claude")

    message = capsys.readouterr().err
    assert "--actor user" in message
    assert "--actor claude" in message


def test_the_default_actor_no_longer_clears_an_approval(make_unit, run):
    """The hole this closes: a whole record with no user event in it at all."""
    work_dir = make_unit("topic")
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


# --- Rule 3: closing a unit (R3, R5) -------------------------------------------


def test_issue_cannot_finalize_without_a_conclusion(make_unit, run):
    work_dir = make_unit("issue")

    assert _finalize(work_dir, run) == 2


def test_issue_cannot_finalize_without_a_confirmed_entry(make_unit, run):
    work_dir = make_unit("issue")
    (work_dir / "conclusion.md").write_text("# Conclusion\n", encoding="utf-8")
    run("add", "--dir", str(work_dir), "--kind", "hypothesis", "--summary", "cache staleness")

    assert _finalize(work_dir, run) == 2


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

    assert _finalize(work_dir, run) == 0


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


def test_inbox_cannot_be_finalized(make_unit, run, capsys):
    """An unclassified folder has no completion to declare."""
    work_dir = make_unit("inbox")
    capsys.readouterr()

    assert _finalize(work_dir, run) == 2
    assert "inbox cannot be finalized" in capsys.readouterr().err


def test_inbox_finalize_is_refused_even_with_a_reason(make_unit, run):
    work_dir = make_unit("inbox")

    assert _finalize(work_dir, run, "--reason", "not going anywhere", actor="user") == 2


def test_inbox_may_be_cancelled(make_unit, run):
    work_dir = make_unit("inbox")
    assert (
        run(
            "add",
            "--dir",
            str(work_dir),
            "--kind",
            "lifecycle",
            "--summary",
            "user dropped it before classifying",
            "--event",
            "cancelled",
        )
        == 0
    )


def test_topic_cannot_finalize_without_a_verification(make_unit, run):
    work_dir = make_unit("topic")
    _verification_file(work_dir)

    assert _finalize(work_dir, run) == 2


def test_direct_work_cannot_finalize_without_a_verification(make_unit, run):
    work_dir = make_unit("direct-work")

    assert _finalize(work_dir, run) == 2


def test_topic_cannot_finalize_without_a_verification_file(make_unit, run, capsys):
    """The record names the evidence; the document is where a later session reads it."""
    work_dir = make_unit("topic")
    _record_verification(work_dir, run)
    capsys.readouterr()

    assert _finalize(work_dir, run) == 2
    assert "verification.md" in capsys.readouterr().err


def test_topic_finalizes_once_the_verification_file_exists(make_unit, run):
    work_dir = make_unit("topic")
    _record_verification(work_dir, run)
    _verification_file(work_dir)

    assert _finalize(work_dir, run) == 0


def test_direct_work_does_not_need_a_verification_file(make_unit, run):
    work_dir = make_unit("direct-work")
    _record_verification(work_dir, run)

    assert _finalize(work_dir, run) == 0


def test_a_cancelled_topic_needs_no_verification_file(make_unit, run):
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


def test_a_verification_directory_does_not_satisfy_the_file_gate(make_unit, run):
    work_dir = make_unit("topic")
    _record_verification(work_dir, run)
    (work_dir / "verification.md").mkdir()

    assert _finalize(work_dir, run) == 2


def test_inconclusive_verification_finalizes_only_with_a_reason(make_unit, run):
    """An honestly unverifiable result may still close — but it has to say why.

    The earlier contract let INCONCLUSIVE through silently. Closing is still
    reachable; what changed is that the record now carries the judgment instead
    of leaving a reader to infer it from a verdict nobody acted on.
    """
    work_dir = make_unit("direct-work")
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")

    assert _finalize(work_dir, run) == 2
    assert (
        _finalize(work_dir, run, "--reason", "no UI available to screenshot", actor="user") == 0
    )


def test_finalizing_with_a_reason_is_the_users_call(make_unit, run, capsys):
    """Accepting a known gap is a decision, so the agent may not sign it alone."""
    work_dir = make_unit("direct-work")
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    capsys.readouterr()

    assert _finalize(work_dir, run, "--reason", "shipping anyway") == 2
    assert "--actor user" in capsys.readouterr().err


def test_finalizing_with_a_reason_is_refused_on_a_non_success_status(make_unit, run):
    work_dir = make_unit("direct-work")
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


def test_a_clean_finalize_needs_no_user_actor(make_unit, run):
    """Only the door over an open gap is the user's; closing clean is not."""
    work_dir = make_unit("direct-work")
    _record_verification(work_dir, run, verdict="PASS")

    assert _finalize(work_dir, run) == 0


def test_finalize_is_refused_on_a_failing_verdict(make_unit, run):
    work_dir = make_unit("topic")
    _verification_file(work_dir)
    _record_verification(work_dir, run, verdict="FAIL")

    assert _finalize(work_dir, run) == 2


def test_finalize_on_a_failing_verdict_passes_with_a_reason(make_unit, run, events):
    work_dir = make_unit("topic")
    _verification_file(work_dir)
    _record_verification(work_dir, run, verdict="FAIL")

    assert (
        _finalize(work_dir, run, "--reason", "shipping the partial fix on purpose", actor="user")
        == 0
    )
    assert events(work_dir)[-1]["data"]["reason"] == "shipping the partial fix on purpose"


def test_an_unresolved_failure_is_not_cancelled_out_by_an_earlier_pass(make_unit, run):
    work_dir = make_unit("topic")
    _verification_file(work_dir)
    _record_verification(work_dir, run, verdict="PASS")
    _record_verification(work_dir, run, verdict="FAIL")

    assert _finalize(work_dir, run) == 2


def test_an_earlier_gap_is_not_buried_by_a_later_pass(make_unit, run, events):
    """The hole this rule closes: a unit finalizing clean on unverified criteria.

    Two real units did exactly this — an INCONCLUSIVE on one acceptance
    criterion, then passing runs on other surfaces, and the close went through
    with nothing recorded about the gap.
    """
    work_dir = make_unit("topic")
    _verification_file(work_dir)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    _record_verification(work_dir, run, verdict="PASS")

    assert _finalize(work_dir, run) == 2


def test_a_later_pass_resolves_the_gap_when_it_names_the_seq(make_unit, run, events):
    work_dir = make_unit("topic")
    _verification_file(work_dir)
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


def test_unresolved_verifications_finalize_with_a_reason(make_unit, run):
    work_dir = make_unit("topic")
    _verification_file(work_dir)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    _record_verification(work_dir, run, verdict="PASS")

    assert _finalize(work_dir, run, "--reason", "test data never arrived", actor="user") == 0


def test_the_refusal_names_every_unresolved_seq(make_unit, run, capsys):
    work_dir = make_unit("topic")
    _verification_file(work_dir)
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    _record_verification(work_dir, run, verdict="FAIL")

    assert _finalize(work_dir, run) == 2
    message = capsys.readouterr().err
    assert "seq 2 INCONCLUSIVE" in message
    assert "seq 3 FAIL" in message


def test_a_resolving_verification_that_itself_failed_stays_open(make_unit, run, events):
    """Resolving one gap by opening another does not clear the gate."""
    work_dir = make_unit("topic")
    _verification_file(work_dir)
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


def test_finalize_without_any_verification_ignores_reason(make_unit, run):
    """No evidence and bad evidence are different failures.

    `--reason` accepts a verdict the user has seen. It must not stand in for a
    verification that was never run.
    """
    work_dir = make_unit("topic")
    _verification_file(work_dir)

    assert _finalize(work_dir, run, "--reason", "trust me", actor="user") == 2


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
    _verification_file(work_dir)

    assert _finalize(work_dir, run) == 0


def test_lifecycle_requires_a_known_event(make_unit, run):
    work_dir = make_unit("topic")
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


def test_resolves_refuses_a_seq_that_does_not_exist(make_unit, run):
    work_dir = make_unit("topic")
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")

    assert _resolving_verification(work_dir, run, 99) == 2


def test_resolves_refuses_a_non_verification_target(make_unit, run, events):
    work_dir = make_unit("topic")
    run("add", "--dir", str(work_dir), "--kind", "note", "--summary", "just a note")
    note = events(work_dir)[-1]["seq"]

    assert _resolving_verification(work_dir, run, note) == 2


def test_resolves_refuses_a_passing_target(make_unit, run, events):
    work_dir = make_unit("topic")
    _record_verification(work_dir, run, verdict="PASS")
    passing = events(work_dir)[-1]["seq"]

    assert _resolving_verification(work_dir, run, passing) == 2


def test_resolves_refuses_its_own_or_a_later_seq(make_unit, run, events):
    """The entry being added is not in the record yet, so forward seqs cannot resolve."""
    work_dir = make_unit("topic")
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    own = events(work_dir)[-1]["seq"] + 1

    assert _resolving_verification(work_dir, run, own) == 2
    assert _resolving_verification(work_dir, run, own + 5) == 2


def test_resolves_is_refused_on_kinds_that_have_nothing_to_close(make_unit, run, events):
    work_dir = make_unit("topic")
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


def test_the_wrong_kind_refusal_names_the_two_kinds_that_do(make_unit, run, events, capsys):
    work_dir = make_unit("topic")
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


def test_a_verification_may_not_resolve_a_blocker(make_unit, run, events):
    work_dir = make_unit("topic")
    _blocker(work_dir, run)
    blocker = events(work_dir)[-1]["seq"]

    assert _resolving_verification(work_dir, run, blocker) == 2


def test_a_blocker_may_not_resolve_a_verification(make_unit, run, events):
    work_dir = make_unit("topic")
    _record_verification(work_dir, run, verdict="FAIL")
    failure = events(work_dir)[-1]["seq"]

    assert _blocker(work_dir, run, "cleared", "--resolves", str(failure)) == 2


def test_a_blocker_may_not_resolve_a_seq_that_does_not_exist(make_unit, run):
    work_dir = make_unit("topic")

    assert _blocker(work_dir, run, "cleared", "--resolves", "99") == 2


def test_a_blocker_resolves_an_earlier_blocker(make_unit, run, events):
    work_dir = make_unit("topic")
    _blocker(work_dir, run, "waiting on the vendor")
    first = events(work_dir)[-1]["seq"]

    assert _blocker(work_dir, run, "vendor replied", "--resolves", str(first)) == 0
    assert events(work_dir)[-1]["data"]["resolves"] == first


def test_a_blocker_cannot_be_resolved_twice(make_unit, run, events):
    """Two closes on one blocker would hide whichever gap is still open."""
    work_dir = make_unit("topic")
    _blocker(work_dir, run, "waiting on the vendor")
    first = events(work_dir)[-1]["seq"]
    _blocker(work_dir, run, "vendor replied", "--resolves", str(first))

    assert _blocker(work_dir, run, "and again", "--resolves", str(first)) == 2


def test_a_verification_gap_cannot_be_resolved_twice(make_unit, run, events):
    work_dir = make_unit("topic")
    _record_verification(work_dir, run, verdict="INCONCLUSIVE")
    gap = events(work_dir)[-1]["seq"]
    _resolving_verification(work_dir, run, gap)

    assert _resolving_verification(work_dir, run, gap) == 2


def test_the_double_resolve_refusal_says_it_was_already_resolved(make_unit, run, events, capsys):
    work_dir = make_unit("topic")
    _blocker(work_dir, run, "waiting on the vendor")
    first = events(work_dir)[-1]["seq"]
    _blocker(work_dir, run, "vendor replied", "--resolves", str(first))
    capsys.readouterr()

    _blocker(work_dir, run, "and again", "--resolves", str(first))

    assert "already resolved" in capsys.readouterr().err


def test_a_sealed_unit_with_an_open_gap_and_no_reason_warns(make_unit, run, tmp_path):
    """The gate that would refuse this today did not exist when such records closed.

    Reporting it as a problem would reach backwards and invalidate a record that
    was legal when written, so it is a warning and the exit code stays clean.
    """
    work_dir = make_unit("direct-work")
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "verification",
        "--summary",
        "could not reach the service",
        "--verdict",
        "INCONCLUSIVE",
    )
    # Written straight to the file: the append gate refuses this shape today, and
    # the point is auditing a record that got past an older one.
    audit = work_dir / "audit.jsonl"
    audit.write_text(
        audit.read_text()
        + json.dumps(
            {
                "seq": 3,
                "ts": "2026-08-13T13:03:16+09:00",
                "actor": "claude",
                "unit": "direct-work",
                "kind": "lifecycle",
                "status": "success",
                "summary": "closed",
                "data": {"event": "finalized"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    warnings = audit_sealed(work_dir)
    assert len(warnings) == 1
    assert "seq 2 INCONCLUSIVE" in warnings[0]
    assert "no --reason" in warnings[0]
    assert validate_record(work_dir) == []


def test_a_sealed_unit_whose_reason_is_not_the_users_warns(make_unit, run):
    work_dir = make_unit("direct-work")
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "verification",
        "--summary",
        "could not reach the service",
        "--verdict",
        "INCONCLUSIVE",
    )
    audit = work_dir / "audit.jsonl"
    audit.write_text(
        audit.read_text()
        + json.dumps(
            {
                "seq": 3,
                "ts": "2026-08-13T13:03:16+09:00",
                "actor": "claude",
                "unit": "direct-work",
                "kind": "lifecycle",
                "status": "success",
                "summary": "closed",
                "data": {"event": "finalized", "reason": "shipping anyway"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    warnings = audit_sealed(work_dir)
    assert len(warnings) == 1
    assert "not\nthe user" in warnings[0] or "not the user" in warnings[0]


def test_a_sealed_topic_without_verification_md_warns_but_stays_valid(make_unit, run):
    work_dir = make_unit("topic")
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "verification",
        "--summary",
        "suite green",
        "--verdict",
        "PASS",
    )
    audit = work_dir / "audit.jsonl"
    audit.write_text(
        audit.read_text()
        + json.dumps(
            {
                "seq": 3,
                "ts": "2026-08-12T16:32:00+09:00",
                "actor": "claude",
                "unit": "topic",
                "kind": "lifecycle",
                "status": "success",
                "summary": "closed",
                "data": {"event": "finalized"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    warnings = audit_sealed(work_dir)
    assert any("no verification.md" in warning for warning in warnings)
    assert validate_record(work_dir) == []


def test_an_open_unit_is_not_audited_as_sealed(make_unit, run):
    work_dir = make_unit("topic")
    run(
        "add",
        "--dir",
        str(work_dir),
        "--kind",
        "verification",
        "--summary",
        "could not reach the service",
        "--verdict",
        "INCONCLUSIVE",
    )
    assert audit_sealed(work_dir) == []
