"""CLI parser and entrypoint for topic-log."""

from __future__ import annotations

import argparse

from .commands import (
    cmd_answer_question,
    cmd_approve_execution,
    cmd_approve_high_risk,
    cmd_artifact,
    cmd_audit,
    cmd_blocker,
    cmd_complete_execution,
    cmd_complete_plan,
    cmd_complete_requirements,
    cmd_complete_task,
    cmd_decision,
    cmd_dispatch_task,
    cmd_finalize_topic,
    cmd_init,
    cmd_note,
    cmd_record_memory,
    cmd_record_memory_candidate,
    cmd_record_question,
    cmd_record_review,
    cmd_record_skill,
    cmd_record_sweep,
    cmd_record_task_commit,
    cmd_record_task_fix,
    cmd_record_task_review,
    cmd_route_start_work,
    cmd_select_git_action,
    cmd_skip_code_cleanup,
    cmd_status,
    cmd_validate,
    cmd_verification,
)
from .constants import (
    AUDIT_STATUSES,
    EXECUTION_MODES,
    GIT_ACTIONS,
    REVIEW_MODES,
    REVIEW_STATUSES,
    ROUTES,
    STATUSES,
    SWEEP_KINDS,
    TASK_FIX_STATUSES,
    TASK_REVIEW_TYPES,
    TASK_ROLES,
)
from .paths import resolve_topic_dir, topic_lock


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage AsUsual topic.md and audit.jsonl.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize topic.md and audit.jsonl.")
    init.add_argument("--topic-dir", required=True)
    init.add_argument("--topic", required=True)
    init.add_argument("--initial-request", default="")
    init.add_argument("--summary", default="")
    init.add_argument("--actor", default="codex")
    init.add_argument("--host", default="")
    init.add_argument("--session-id", default="")
    init.add_argument("--notes", default="")
    init.add_argument("--timestamp", default="")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    audit = sub.add_parser("audit", help="Append one audit.jsonl event.")
    audit.add_argument("--topic-dir", required=True)
    audit.add_argument("--event", required=True)
    audit.add_argument("--actor", default="codex")
    audit.add_argument("--phase", default="")
    audit.add_argument("--artifacts", default="")
    audit.add_argument("--route", default="")
    audit.add_argument("--initial-request-ref", default="")
    audit.add_argument("--notes", default="")
    audit.add_argument("--status", choices=sorted(AUDIT_STATUSES), default="success")
    audit.add_argument("--summary", default="")
    audit.add_argument("--next-action", default="")
    audit.add_argument("--error-kind", default="")
    audit.add_argument("--retry-hint", default="")
    audit.add_argument("--stop-condition", default="")
    audit.add_argument("--timestamp", default="")
    audit.set_defaults(func=cmd_audit)

    artifact = sub.add_parser("artifact", help="Record one artifact event.")
    artifact.add_argument("--topic-dir", required=True)
    artifact.add_argument("--name", required=True)
    artifact.add_argument("--value", required=True)
    artifact.add_argument("--append", action="store_true")
    artifact.add_argument("--actor", default="codex")
    artifact.add_argument("--phase", default="")
    artifact.add_argument("--summary", default="")
    artifact.add_argument("--notes", default="")
    artifact.add_argument("--next-action", default="")
    artifact.add_argument("--timestamp", default="")
    artifact.set_defaults(func=cmd_artifact)

    route = sub.add_parser("route-start-work", help="Append start-work routing event.")
    route.add_argument("--topic-dir", required=True)
    route.add_argument("--route", required=True, choices=sorted(ROUTES))
    route.add_argument("--reason", default="")
    route.add_argument("--next-action", default="")
    route.add_argument("--skipped-gates", default="")
    route.add_argument("--verification-plan", default="")
    route.add_argument("--actor", default="codex")
    route.add_argument("--timestamp", default="")
    route.set_defaults(func=cmd_route_start_work)

    record_question = sub.add_parser("record-question", help="Append requirements question creation event.")
    record_question.add_argument("--topic-dir", required=True)
    record_question.add_argument("--question", required=True)
    record_question.add_argument("--summary", default="")
    record_question.add_argument("--actor", default="codex")
    record_question.add_argument("--timestamp", default="")
    record_question.set_defaults(func=cmd_record_question)

    answer_question = sub.add_parser("answer-question", help="Append requirements question answered event.")
    answer_question.add_argument("--topic-dir", required=True)
    answer_question.add_argument("--question", required=True)
    answer_question.add_argument("--source", choices=["file", "chat"], default="file")
    answer_question.add_argument("--next-action", default="")
    answer_question.add_argument("--summary", default="")
    answer_question.add_argument("--notes", default="")
    answer_question.add_argument("--actor", default="codex")
    answer_question.add_argument("--timestamp", default="")
    answer_question.set_defaults(func=cmd_answer_question)

    complete_requirements = sub.add_parser("complete-requirements", help="Append requirements completion event.")
    complete_requirements.add_argument("--topic-dir", required=True)
    complete_requirements.add_argument("--requirements", default="requirements.md")
    complete_requirements.add_argument("--summary", default="")
    complete_requirements.add_argument("--actor", default="codex")
    complete_requirements.add_argument("--timestamp", default="")
    complete_requirements.set_defaults(func=cmd_complete_requirements)

    complete_plan = sub.add_parser("complete-plan", help="Append plan completion event.")
    complete_plan.add_argument("--topic-dir", required=True)
    complete_plan.add_argument("--plan", default="plan.md")
    complete_plan.add_argument("--summary", default="")
    complete_plan.add_argument("--actor", default="codex")
    complete_plan.add_argument("--timestamp", default="")
    complete_plan.set_defaults(func=cmd_complete_plan)

    approve_execution = sub.add_parser("approve-execution", help="Append execution approval event.")
    approve_execution.add_argument("--topic-dir", required=True)
    approve_execution.add_argument("--summary", default="")
    approve_execution.add_argument("--approved-by", default="user")
    approve_execution.add_argument("--source", default="chat")
    approve_execution.add_argument("--actor", default="user")
    approve_execution.add_argument("--timestamp", default="")
    approve_execution.set_defaults(func=cmd_approve_execution)

    approve_high_risk = sub.add_parser("approve-high-risk", help="Append high-risk approval event.")
    approve_high_risk.add_argument("--topic-dir", required=True)
    approve_high_risk.add_argument("--operation-id", required=True)
    approve_high_risk.add_argument("--description", default="")
    approve_high_risk.add_argument("--approved-by", default="user")
    approve_high_risk.add_argument("--rollback", default="")
    approve_high_risk.add_argument("--summary", default="")
    approve_high_risk.add_argument("--artifacts", default="")
    approve_high_risk.add_argument("--actor", default="user")
    approve_high_risk.add_argument("--timestamp", default="")
    approve_high_risk.set_defaults(func=cmd_approve_high_risk)

    complete_task = sub.add_parser("complete-task", help="Append task completion event.")
    complete_task.add_argument("--topic-dir", required=True)
    complete_task.add_argument("--task", required=True)
    complete_task.add_argument("--summary", default="")
    complete_task.add_argument("--verification", default="")
    complete_task.add_argument("--mode", default="")
    complete_task.add_argument("--test-target", default="")
    complete_task.add_argument("--red-evidence", default="")
    complete_task.add_argument("--green-evidence", default="")
    complete_task.add_argument("--expected-result", default="")
    complete_task.add_argument("--result", default="")
    complete_task.add_argument("--exception-category", default="")
    complete_task.add_argument("--exception-approval", default="")
    complete_task.add_argument("--artifacts", default="")
    complete_task.add_argument("--actor", default="codex")
    complete_task.add_argument("--timestamp", default="")
    complete_task.set_defaults(func=cmd_complete_task)

    complete_execution = sub.add_parser("complete-execution", help="Append execution completion event.")
    complete_execution.add_argument("--topic-dir", required=True)
    complete_execution.add_argument("--summary", default="")
    complete_execution.add_argument("--verification", default="")
    complete_execution.add_argument("--result", default="")
    complete_execution.add_argument("--artifacts", default="")
    complete_execution.add_argument("--actor", default="codex")
    complete_execution.add_argument("--timestamp", default="")
    complete_execution.set_defaults(func=cmd_complete_execution)

    dispatch_task = sub.add_parser("dispatch-task", help="Append task dispatch event.")
    dispatch_task.add_argument("--topic-dir", required=True)
    dispatch_task.add_argument("--task", required=True)
    dispatch_task.add_argument("--mode", required=True, choices=sorted(EXECUTION_MODES))
    dispatch_task.add_argument("--role", default="implementer", choices=sorted(TASK_ROLES))
    dispatch_task.add_argument("--context", default="")
    dispatch_task.add_argument("--summary", default="")
    dispatch_task.add_argument("--artifacts", default="")
    dispatch_task.add_argument("--actor", default="codex")
    dispatch_task.add_argument("--timestamp", default="")
    dispatch_task.set_defaults(func=cmd_dispatch_task)

    task_review = sub.add_parser("record-task-review", help="Append task-level review event.")
    task_review.add_argument("--topic-dir", required=True)
    task_review.add_argument("--task", required=True)
    task_review.add_argument("--review-type", default="task", choices=sorted(TASK_REVIEW_TYPES))
    task_review.add_argument("--status", required=True, choices=sorted(REVIEW_STATUSES))
    task_review.add_argument("--critical", type=int, default=0)
    task_review.add_argument("--important", type=int, default=0)
    task_review.add_argument("--minor", type=int, default=0)
    task_review.add_argument("--finding-ids", default="")
    task_review.add_argument("--summary", default="")
    task_review.add_argument("--artifacts", default="")
    task_review.add_argument("--actor", default="codex")
    task_review.add_argument("--timestamp", default="")
    task_review.set_defaults(func=cmd_record_task_review)

    task_fix = sub.add_parser("record-task-fix", help="Append task fix request or completion event.")
    task_fix.add_argument("--topic-dir", required=True)
    task_fix.add_argument("--task", required=True)
    task_fix.add_argument("--finding-id", required=True)
    task_fix.add_argument("--status", required=True, choices=sorted(TASK_FIX_STATUSES))
    task_fix.add_argument("--summary", default="")
    task_fix.add_argument("--artifacts", default="")
    task_fix.add_argument("--actor", default="codex")
    task_fix.add_argument("--timestamp", default="")
    task_fix.set_defaults(func=cmd_record_task_fix)

    task_commit = sub.add_parser("record-task-commit", help="Append task commit boundary event.")
    task_commit.add_argument("--topic-dir", required=True)
    task_commit.add_argument("--task", required=True)
    task_commit.add_argument("--sha", required=True)
    task_commit.add_argument("--summary", default="")
    task_commit.add_argument("--actor", default="codex")
    task_commit.add_argument("--timestamp", default="")
    task_commit.set_defaults(func=cmd_record_task_commit)

    sweep = sub.add_parser("record-sweep", help="Append final or task sweep evidence event.")
    sweep.add_argument("--topic-dir", required=True)
    sweep.add_argument("--kind", required=True, choices=sorted(SWEEP_KINDS))
    sweep.add_argument("--command", required=True)
    sweep.add_argument("--result", required=True)
    sweep.add_argument("--summary", default="")
    sweep.add_argument("--status", choices=sorted(AUDIT_STATUSES), default="success")
    sweep.add_argument("--phase", default="")
    sweep.add_argument("--next-action", default="")
    sweep.add_argument("--artifacts", default="")
    sweep.add_argument("--actor", default="codex")
    sweep.add_argument("--timestamp", default="")
    sweep.set_defaults(func=cmd_record_sweep)

    record_review = sub.add_parser("record-review", help="Append execution review event.")
    record_review.add_argument("--topic-dir", required=True)
    record_review.add_argument("--mode", required=True, choices=sorted(REVIEW_MODES))
    record_review.add_argument("--status", required=True, choices=sorted(REVIEW_STATUSES))
    record_review.add_argument("--critical", type=int, default=0)
    record_review.add_argument("--important", type=int, default=0)
    record_review.add_argument("--minor", type=int, default=0)
    record_review.add_argument("--reason", default="")
    record_review.add_argument("--report", default="")
    record_review.add_argument("--actor", default="codex")
    record_review.add_argument("--timestamp", default="")
    record_review.set_defaults(func=cmd_record_review)

    skip_code_cleanup = sub.add_parser("skip-code-cleanup", help="Append code cleanup skipped event.")
    skip_code_cleanup.add_argument("--topic-dir", required=True)
    skip_code_cleanup.add_argument("--reason", default="")
    skip_code_cleanup.add_argument("--actor", default="codex")
    skip_code_cleanup.add_argument("--timestamp", default="")
    skip_code_cleanup.set_defaults(func=cmd_skip_code_cleanup)

    skip_simplify = sub.add_parser("skip-simplify", help="Deprecated alias for skip-code-cleanup.")
    skip_simplify.add_argument("--topic-dir", required=True)
    skip_simplify.add_argument("--reason", default="")
    skip_simplify.add_argument("--actor", default="codex")
    skip_simplify.add_argument("--timestamp", default="")
    skip_simplify.set_defaults(func=cmd_skip_code_cleanup)

    finalize_topic = sub.add_parser("finalize-topic", help="Append topic finalization event.")
    finalize_topic.add_argument("--topic-dir", required=True)
    finalize_topic.add_argument("--status", required=True, choices=sorted(STATUSES - {"active"}))
    finalize_topic.add_argument("--summary", default="")
    finalize_topic.add_argument("--report", default="report.md")
    finalize_topic.add_argument("--actor", default="codex")
    finalize_topic.add_argument("--timestamp", default="")
    finalize_topic.set_defaults(func=cmd_finalize_topic)

    select_git_action = sub.add_parser("select-git-action", help="Append selected git action event.")
    select_git_action.add_argument("--topic-dir", required=True)
    select_git_action.add_argument("--action", required=True, choices=sorted(GIT_ACTIONS))
    select_git_action.add_argument("--summary", default="")
    select_git_action.add_argument("--actor", default="user")
    select_git_action.add_argument("--timestamp", default="")
    select_git_action.set_defaults(func=cmd_select_git_action)

    rec_mem_cand = sub.add_parser("record-memory-candidate")
    rec_mem_cand.add_argument("--topic-dir", required=True)
    rec_mem_cand.add_argument("--summary", required=True)
    rec_mem_cand.add_argument("--source-phase", default="")
    rec_mem_cand.add_argument("--proposed-target", choices=["memory", "skill", "undecided"], default="undecided")
    rec_mem_cand.add_argument("--actor", default="codex")
    rec_mem_cand.set_defaults(func=cmd_record_memory_candidate)

    rec_mem = sub.add_parser("record-memory")
    rec_mem.add_argument("--topic-dir", required=True)
    rec_mem.add_argument("--summary", required=True)
    rec_mem.add_argument("--files", default="")
    rec_mem.add_argument("--actor", default="codex")
    rec_mem.set_defaults(func=cmd_record_memory)

    rec_skill = sub.add_parser("record-skill")
    rec_skill.add_argument("--topic-dir", required=True)
    rec_skill.add_argument("--state", choices=["created", "candidate"], required=True)
    rec_skill.add_argument("--summary", required=True)
    rec_skill.add_argument("--kind", choices=["new", "patch"], required=True)
    rec_skill.add_argument("--patch-target", default="")
    rec_skill.add_argument("--dest", default="")
    rec_skill.add_argument("--rationale", default="")
    rec_skill.add_argument("--brief", default="")
    rec_skill.add_argument("--actor", default="codex")
    rec_skill.set_defaults(func=cmd_record_skill)

    note = sub.add_parser("note", help="Append note event.")
    note.add_argument("--topic-dir", required=True)
    note.add_argument("--summary", required=True)
    note.add_argument("--durable-topic-note", action="store_true")
    note.add_argument("--phase", default="")
    note.add_argument("--next-action", default="")
    note.add_argument("--actor", default="codex")
    note.add_argument("--timestamp", default="")
    note.set_defaults(func=cmd_note)

    decision = sub.add_parser("decision", help="Append decision event.")
    decision.add_argument("--topic-dir", required=True)
    decision.add_argument("--summary", required=True)
    decision.add_argument("--source", required=True)
    decision.add_argument("--durable-topic-note", action="store_true")
    decision.add_argument("--phase", default="")
    decision.add_argument("--next-action", default="")
    decision.add_argument("--actor", default="codex")
    decision.add_argument("--timestamp", default="")
    decision.set_defaults(func=cmd_decision)

    blocker = sub.add_parser("blocker", help="Append blocker event.")
    blocker.add_argument("--topic-dir", required=True)
    blocker.add_argument("--summary", required=True)
    blocker.add_argument("--id", required=True)
    blocker.add_argument("--next-action", default="none")
    blocker.add_argument("--actor", default="codex")
    blocker.add_argument("--timestamp", default="")
    blocker.set_defaults(func=cmd_blocker)

    verification = sub.add_parser("verification", help="Append verification event.")
    verification.add_argument("--topic-dir", required=True)
    verification.add_argument("--summary", required=True)
    verification.add_argument("--command", required=True)
    verification.add_argument("--result", required=True)
    verification.add_argument("--verdict", required=True)
    verification.add_argument("--phase", default="")
    verification.add_argument("--next-action", default="")
    verification.add_argument("--artifacts", default="")
    verification.add_argument("--actor", default="codex")
    verification.add_argument("--timestamp", default="")
    verification.set_defaults(func=cmd_verification)

    status = sub.add_parser("status", help="Print derived topic status.")
    status.add_argument("--topic-dir", required=True)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    validate = sub.add_parser("validate", help="Validate topic.md and audit.jsonl.")
    validate.add_argument("--topic-dir", required=True)
    validate.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "topic_dir"):
        topic = resolve_topic_dir(args.topic_dir)
        with topic_lock(topic):
            args.func(args)
    else:
        args.func(args)
    return 0
