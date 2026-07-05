"""Command handler facade for topic-log subcommands."""

from __future__ import annotations

from .command_execution import (
    cmd_approve_execution,
    cmd_approve_high_risk,
    cmd_complete_execution,
    cmd_complete_task,
    cmd_dispatch_task,
    cmd_record_sweep,
    cmd_record_task_commit,
    cmd_record_task_fix,
    cmd_record_task_review,
)
from .command_lifecycle import (
    cmd_answer_question,
    cmd_artifact,
    cmd_audit,
    cmd_complete_plan,
    cmd_complete_requirements,
    cmd_init,
    cmd_record_question,
    cmd_route_start_work,
)
from .command_memory import cmd_record_memory, cmd_record_memory_candidate, cmd_record_skill
from .command_misc import cmd_blocker, cmd_decision, cmd_note, cmd_status, cmd_validate, cmd_verification
from .command_review_finalize import (
    cmd_finalize_topic,
    cmd_record_review,
    cmd_select_git_action,
    cmd_skip_code_cleanup,
)

__all__ = [
    "cmd_answer_question",
    "cmd_approve_execution",
    "cmd_approve_high_risk",
    "cmd_artifact",
    "cmd_audit",
    "cmd_blocker",
    "cmd_complete_execution",
    "cmd_complete_plan",
    "cmd_complete_requirements",
    "cmd_complete_task",
    "cmd_decision",
    "cmd_dispatch_task",
    "cmd_finalize_topic",
    "cmd_init",
    "cmd_note",
    "cmd_record_memory",
    "cmd_record_memory_candidate",
    "cmd_record_question",
    "cmd_record_review",
    "cmd_record_skill",
    "cmd_record_sweep",
    "cmd_record_task_commit",
    "cmd_record_task_fix",
    "cmd_record_task_review",
    "cmd_route_start_work",
    "cmd_select_git_action",
    "cmd_skip_code_cleanup",
    "cmd_status",
    "cmd_validate",
    "cmd_verification",
]
