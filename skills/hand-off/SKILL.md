---
name: hand-off
description: Use when the user invokes an AsUsual hand-off command such as /as-usual:hand-off or asks to resume a topic from another Claude, Codex, or session using an existing .as-usual topic path.
---

# Hand Off

## Overview

This skill resumes an existing AsUsual topic created or advanced by another session. It is not a workflow phase and does not add a new gate; it rehydrates topic artifacts, checks the current state, and routes to the existing owner skill.

## Responsibility Boundary

| Skill | Responsibility |
| --- | --- |
| `hand-off` | Select an existing topic, perform hand-off first reads, summarize state, and route to the current owner skill |
| `using-as-usual` | General AsUsual activation and new topic initialization; delegates here on an explicit topic path or a cross-session resume |
| `start-work` | Route a new topic or unclear current phase after first reads |
| `define-requirements` | Validate question answers and write or update `requirements.md` |
| `writing-plan` | Write or update `plan.md` from completed requirements |
| `executing-plan` | Execute or finish verifying an approved plan |
| `review-execution` | Review completed execution and ask about optional code cleanup |
| `cleanup-code`, `finalize`, `git-action` | Continue their normal post-execution responsibilities |

`hand-off` may do the same required first reads as `using-as-usual`, but it must not create a new topic unless the user abandons hand-off and explicitly starts new AsUsual work.

## Inputs

This skill is entered two ways: the user invokes an explicit hand-off command, or `using-as-usual` delegates here after activation detects a cross-session resume.

Handle these forms:

- `/as-usual:hand-off`
- `/as-usual:hand-off path`
- Requests that supply an existing AsUsual topic path or explicitly reference another Claude/Codex/session that started or advanced the topic.
- Delegation from `using-as-usual` when activation detects an explicit topic path or a cross-session resume.

Ordinary same-session resume phrasing such as "I answered", "write the requirements", or "continue" with no cross-session signal stays in `using-as-usual`; do not treat it as a hand-off.

The path may point to:

- a topic directory containing `topic.md` and `audit.jsonl`
- any file inside a topic directory
- a target project root containing `.as-usual/topic/`
- a `.as-usual/topic/` collection directory

## Topic Selection

1. Read the full `as-usual-rules/core-workflow.md` before routing. Prefer a path announced by the SessionStart hook when present; otherwise resolve it from the AsUsual plugin root, which is the parent directory of the `skills/` directory containing this skill.
2. If a path was supplied, resolve it to a canonical topic directory:
   - If the path contains `topic.md` and `audit.jsonl`, use it.
   - If the path is a file or nested folder under a topic, walk upward until the topic directory is found.
   - If the path is a target project root or `.as-usual/topic/`, choose the most recently modified topic directory and state which one was selected.
   - If the path is ambiguous or does not contain an AsUsual topic, stop and ask for the correct topic path.
3. If no path was supplied, inspect both `.as-usual/topic/` and `.as-usual/issue/` in the current project. If only topics exist, read the most recent topic candidate's `topic.md`, `audit.jsonl`, and derived status, then ask the user to confirm before continuing (list up to three plausible topics with their names and next actions). If only issues exist, route to the Issue Hand-Off path below. If both exist, list recent topics and issues together and ask the user which to resume. If neither exists, say there is nothing to resume.
4. Do not use legacy `.as-usual/topics/` paths for new work. If only legacy artifacts exist, explain that hand-off needs a canonical `.as-usual/topic/yyyy-MM-dd-name/` topic or an explicit migration request.

## Issue Hand-Off

If the supplied path resolves inside `.as-usual/issue/` (an issue directory, a file inside one, or the `issue/` collection) — or no path was supplied and issues are the resume target selected in step 3 — this is a find-cause issue, not a coding topic. Do not apply topic first reads or completion verification. Read `problem.md`, run `python3 <plugin-root>/scripts/journal-log.py status --issue-dir <dir> --json`, then route to the `find-cause` skill. If several recent issues look plausible, list up to three with their slugs and derived status before continuing.

## First Reads

After selecting a topic:

1. Read `topic.md`.
2. Read `audit.jsonl`.
3. Run `python3 <plugin-root>/scripts/topic-log.py status --topic-dir <topic-dir> --json` when available.
4. Read `question-cN.md` files in order when they exist.
5. Read `requirements.md` when it exists.
6. Read `plan.md` when it exists.
7. Read `code-review-report.md` or `report.md` only when derived status or the latest request makes them relevant.
8. Inspect `git status --short` and relevant diffs when `plan.md` exists and there are signs that implementation may already have happened.

Do not trust chat memory from the previous session. Treat the topic artifacts and actual working tree as source of truth.

## Resume Routing

Use derived status first, then artifact presence as a fallback.

- Open `question-cN.md` answers are missing or contradictory: stop and tell the user which question file needs an answer.
- Questions are answered but `requirements.md` is missing or stale: invoke `define-requirements`.
- `requirements.md` exists, `plan.md` is missing, and the topic is requirements-complete: ask whether to start `writing-plan`, unless the current user request already explicitly asks to write the plan.
- Only a `spec.md` or other noncanonical spec-like file exists: do not silently treat it as a completed AsUsual requirements artifact. Ask whether to synthesize canonical `requirements.md` first or to treat the file as external input for a new requirements pass.
- `plan.md` exists and derived status is `plan-review` with next action `approve-execute`: ask for execution approval unless the current user request explicitly approves or requests execution.
- `plan.md` exists and implementation-like changes or task evidence already exist: say "작업 완료 여부를 확인해보겠습니다." Then compare the plan tasks, audit evidence, working tree changes, and verification evidence. If work is incomplete or evidence is missing, invoke `executing-plan` to finish the plan, verification, and audit records. If execution is complete but not recorded, record only evidence you personally verified through `scripts/topic-log.py` macros before moving on.
- Derived status is `execution-complete` or next action is `review-execution`: invoke `review-execution`.
- Derived status is `review-complete` with next action `decide-code-cleanup`: continue through `review-execution` so the user gets the normal cleanup decision prompt.
- Derived status is `review-complete` or `cleanup-complete` with next action `finalize`: invoke `finalize`.
- Topic is finalized and the next action is `git-action-decision`: invoke `git-action` only after the user selects a git action.
- Topic is blocked: read the blocker evidence and ask only for the concrete missing decision or action needed to unblock.

When the next phase is unclear after first reads, invoke `start-work` instead of inventing a new hand-off-specific route.

## Audit Rules

Do not hand-edit `topic.md` or `audit.jsonl`.

- Once a topic is selected, record a short hand-off note with `scripts/topic-log.py note` when it helps future resume context.
- Use the existing phase macro commands for real workflow transitions.
- If the helper cannot express a transition, stop and report the missing helper capability.

## User-Facing Behavior

Be brief and concrete.

- With no path, ask for confirmation before continuing from the latest topic.
- With a supplied topic path, start the resume check immediately and report the selected path.
- When plan execution may already be done, say that you will verify completion before continuing.
- Do not claim that another session completed work until you have checked artifacts, diffs, and verification evidence yourself.
