"""Constants shared by the AsUsual topic-log helper."""

from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "as-usual.audit.v1"

STATUSES = {"active", "blocked", "complete", "follow-up-needed", "cancelled"}

PHASES = {
    "start-work",
    "define-requirements",
    "requirements-complete",
    "writing-plan",
    "plan-review",
    "executing",
    "execution-complete",
    "review-execution",
    "review-complete",
    "review-fixes-needed",
    "cleanup-code",
    "cleanup-complete",
    "finalized",
    "git-action",
    "git-action-complete",
    "direct-execute-complete",
    "blocked",
}

LEGACY_PHASE_ALIASES = {
    "simplify-execution": "cleanup-code",
    "simplify-complete": "cleanup-complete",
}

NEXT_ACTIONS = {
    "",
    "route",
    "answer-questions",
    "write-requirements",
    "approve-plan",
    "write-plan",
    "approve-execute",
    "execute",
    "review-execution",
    "address-review-findings",
    "decide-code-cleanup",
    "cleanup-code",
    "finalize",
    "git-action-decision",
    "git-action",
    "none",
}

LEGACY_NEXT_ACTION_ALIASES = {
    "decide-simplify": "decide-code-cleanup",
    "simplify-execution": "cleanup-code",
}

CODE_CLEANUP_DECISION_EVENTS = {
    "code_cleanup.skipped",
    "code_cleanup.completed",
    "simplify.skipped",
    "simplify.completed",
}

ACTORS = {"codex", "claude", "user", "system"}
HOSTS = {"codex", "claude"}
REVIEW_MODES = {"independent", "self", "local-prompt"}
REVIEW_STATUSES = {"passed", "findings", "blocked"}
VERIFICATION_VERDICTS = {"PASS", "FAIL", "INCONCLUSIVE"}
AUDIT_STATUSES = {"success", "warning", "error"}
GIT_ACTIONS = {"none", "commit", "commit + push", "commit + push + PR"}
ROUTES = {"requirements", "plan", "execute", "direct-execute"}
EXECUTION_MODES = {"inline", "subagent-driven", "mixed"}
TASK_REVIEW_TYPES = {"task"}
TASK_ROLES = {"implementer", "reviewer", "controller"}
TASK_FIX_STATUSES = {"requested", "completed"}
SWEEP_KINDS = {"final", "stale-reference", "mirror", "verification", "custom"}
TASK_COMPLETION_MODES = {"tdd", "approved-tdd-exception"}
TDD_EXCEPTION_CATEGORIES = {"throwaway-prototype", "generated-code", "configuration"}
ROUTE_NEXT_ACTIONS = {
    "requirements": "answer-questions",
    "plan": "write-plan",
    "execute": "execute",
    "direct-execute": "execute",
}
ARTIFACT_KEYS = {"question", "requirements", "plan", "codeReviewReport", "report", "audit", "topic"}
ARTIFACT_FIELD_BY_FILE = {
    "requirements.md": "requirements",
    "plan.md": "plan",
    "code-review-report.md": "codeReviewReport",
    "report.md": "report",
    "topic.md": "topic",
    "audit.jsonl": "audit",
}

JsonObject = dict[str, Any]
