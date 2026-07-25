"""Closed vocabularies for the AsUsual record layer.

Extension rule: add a value here only when a script gate enforces something with
it. Anything a gate does not check belongs in `summary` or `data`, not in a new
vocabulary entry.
"""

from __future__ import annotations

from typing import Any


SCHEMA_VERSION = "as-usual.record.v1"

CONTEXTS_FILE = "contexts.md"
AUDIT_FILE = "audit.jsonl"

# Work units. `inbox` is the pre-classification staging unit; the other three are
# the durable work units.
UNITS = {"inbox", "topic", "direct-work", "issue"}
MOVE_TARGETS = {"topic", "direct-work", "issue"}

# Files whose presence means the folder has produced its own work output, which
# freezes its unit label. Blocklist, not allowlist: unrelated stray files must
# never affect the decision.
MOVE_BLOCKING_FILES = ("requirements.md", "plan.md", "conclusion.md")

KINDS = {
    "lifecycle",
    "approval",
    "verification",
    "review",
    "decision",
    "work",
    "hypothesis",
    "status-change",
    "blocker",
    "artifact",
    "memory",
    "note",
}

LIFECYCLE_EVENTS = {
    "created",
    "unit-selected",
    "phase-entered",
    "finalized",
    "cancelled",
    "linked",
}

CLOSING_LIFECYCLE_EVENTS = {"finalized", "cancelled"}

# phase == the name of the skill that currently owns the work.
PHASES = {
    "gathering-context",
    "write-requirements",
    "write-plan",
    "execute-plan",
    "review-execution",
    "cleanup-code",
    "investigating",
    "concluding",
    "finalize",
    "git-action",
    "blocked",
}

# Each unit uses only its subset. This mirrors the owner skills' matrices.
UNIT_PHASES = {
    "inbox": {"gathering-context", "blocked"},
    "topic": {
        "gathering-context",
        "write-requirements",
        "write-plan",
        "execute-plan",
        "review-execution",
        "cleanup-code",
        "finalize",
        "git-action",
        "blocked",
    },
    "direct-work": {
        "gathering-context",
        "write-plan",
        "execute-plan",
        "review-execution",
        "cleanup-code",
        "finalize",
        "git-action",
        "blocked",
    },
    "issue": {
        "gathering-context",
        "investigating",
        "concluding",
        "finalize",
        "git-action",
        "blocked",
    },
}

# nextAction is either the next phase name or one of these.
NEXT_ACTION_SPECIALS = {"awaiting-user", "none"}

STATUSES = {"success", "warning", "error"}
ACTORS = {"claude", "codex", "user", "system"}
VERDICTS = {"PASS", "FAIL", "INCONCLUSIVE"}
STATUS_CHANGE_STATES = {"confirmed", "cancelled"}
APPROVAL_ACTIONS = {"high-risk", "execution", "git-action"}

# Units whose execution approval must be preceded by a plan review (core rule 7).
PLAN_REVIEW_UNITS = {"topic", "direct-work"}

# Units that produce a code change, so finalizing one is a completion claim and
# needs recorded verification behind it (core rule 3).
VERIFICATION_UNITS = {"topic", "direct-work"}

# status-change may only target an entry that carries reasoning.
REASONING_KINDS = {"decision", "hypothesis", "review", "work", "note"}

JsonObject = dict[str, Any]
