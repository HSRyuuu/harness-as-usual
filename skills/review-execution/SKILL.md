---
name: review-execution
description: Use when AsUsual is active and plan execution has completed or execution review follow-up is needed.
---

# Review Execution

This skill handles the mandatory post-execution review gate. It reviews completed implementation against the topic `requirements.md`, `plan.md`, recorded execution evidence, and actual code changes before the topic can be finalized.

Use it only after `using-as-usual` has completed activation and first reads, and after `executing-plan` has recorded execution completion, after review follow-up is needed, or after the user responds to the optional code cleanup prompt.

## Responsibility Boundary

| Skill | Responsibility |
| --- | --- |
| `executing-plan` | Implement the approved plan inline and record task-level test/verification evidence |
| `review-execution` | Review execution results and changed code, record findings, and ask whether to run optional code cleanup |
| `cleanup-code` | Run approved cleanup review and apply safe behavior-preserving simplifications |
| `finalize` | Close the topic record and ask which git action to run |
| `git-action` | Run the selected post-finalize git action |

`review-execution` does not replace task-level verification. It checks the completed work after execution evidence exists. It may recommend fixes. Critical and Important findings must be fixed and re-reviewed to a passing result before `complete` or `follow-up-needed` finalization. If the user chooses not to fix a Critical or Important finding, record the decision and route finalization to `blocked` under the current helper validation model.

## Preconditions

Before reviewing, confirm:

- The Review Execution rules in `core-workflow.md` have been checked.
- `topic.md`, `audit.jsonl`, `requirements.md`, and `plan.md` have been read from disk.
- Derived status or `audit.jsonl` shows execution is complete, review follow-up is needed, or the current request answers the optional code cleanup prompt after review.
- Execution evidence exists in `verification.recorded` or `task.completed` events, or skipped verification is explicitly recorded with a reason.

If execution did not complete, return to `executing-plan` or the necessary earlier phase. Do not review from chat memory alone.

## Inputs

Read and use these sources in this order:

1. `topic.md`
2. `audit.jsonl`
3. Derived status from `scripts/topic-log.py status --json`, when available
4. `requirements.md`
5. `plan.md`
6. The current diff or changed files, using git when available
7. Relevant test or verification output already recorded in `audit.jsonl`

If git is unavailable, review the changed files named in `audit.jsonl`, `plan.md`, or the user's current request, and record the limitation.

## Hard Gates

- Do not review only summaries; inspect the actual diff or changed files when available.
- Do not ask about code cleanup or finalize as `complete` or `follow-up-needed` while Critical or Important findings remain unresolved.
- Do not let Important findings proceed toward commit/PR without a fix and passing re-review. If the user declines the fix, record a blocker and finalize as `blocked`.
- Do not treat code cleanup as a replacement for correctness review.

## Preferences

- Prefer narrow review evidence: topic artifacts, diff/range, and recorded execution evidence.
- Prefer file/line findings when possible.
- Prefer routing fixes back to the owning phase instead of editing implementation inside this review skill.
- Prefer fewer, higher-confidence findings over speculative review noise.

## Workflow

### Step 1: Review Actual Changes

Inspect the implementation directly. Do not rely only on execution summaries; review the actual diff or changed files.

Use `code-reviewer-prompt.md` from this skill directory as the canonical review checklist and finding quality gate. Do not maintain a second copy of the review criteria in this skill. The reviewer prompt owns:

- the review categories (requirements/plan alignment, correctness and risk, silent failure, prompt-injection/trust boundary, secret leaks, high-risk operation evidence, verification quality, source traceability, code quality),
- the Finding Quality Gate every finding must pass before it is recorded,
- the reviewer output format (strengths, findings by severity, silent failure assessment, verification assessment, verdict).

A no-finding review is valid when the implementation satisfies the requirements, plan, verification evidence, and surrounding code.

Prefer a separate code-review agent or subagent when the host supports it. Fill the reviewer prompt with the topic artifact paths and the diff or changed-file list, and give the reviewer only the topic files, diff/range, and execution evidence needed for review, not the whole conversation history.

For `independent` review mode, treat the reviewer response as a receipt: `Verdict: passed | findings | blocked`, `Report: code-review-report.md | none`, and severity counts. If a report is written, confirm the report frontmatter `verdict` matches the receipt verdict before recording `record-review`.

For `local-prompt` review mode, apply the same file/frontmatter rule directly in this session: when a report is created, its frontmatter `verdict` must match the `record-review --status` value.

### Step 2: Record Review Result

Record the review outcome with `scripts/topic-log.py record-review`.

Use these severity buckets:

- `Critical`: must be addressed before the topic can honestly be considered complete.
- `Important`: must be fixed and re-reviewed before `complete` or `follow-up-needed` finalization under the current helper validation model.
- `Minor`: polish or follow-up.

If findings exist, list file/line references when possible, why each issue matters, and the recommended next action. If the reviewer is wrong, record the technical reason for rejecting the finding.

When any Critical, Important, or Minor finding exists:

1. Create or update `code-review-report.md` in the topic folder using `templates/code-review-report.md`.
2. Fill the YAML front matter with review input provenance: `topic`, `topicFile`, `audit`, `statusCommand`, `requirements`, `plan`, `diffOrChangedFiles`, `verificationEvidence`, `findingQualityGateApplied`, and `verdict`.
3. Write user-facing prose in the user's current or clearly preferred language. Preserve exact file paths, line numbers, commands, severity labels, and disposition values.
4. Fill the report body sections defined by `templates/code-review-report.md`; that template owns the report's section list and order. Do not redefine the report body shape here.
5. Confirm `code-review-report.md` frontmatter `verdict` matches the `record-review --status` value.
6. Include `code-review-report.md` through the `record-review --report code-review-report.md` artifact field.
7. Include `code-review-report.md` in the `review.completed` audit event artifacts.

When there are no findings, do not create an empty `code-review-report.md` and do not pass `--report`. Record the no-finding result in `audit.jsonl`.

### Step 3: Handle Review Findings

Allowed dispositions by severity:

| Severity | Allowed dispositions |
| --- | --- |
| Critical | `fixed` (and re-reviewed to passed), `rejected` (with technical reason, re-reviewed to passed), `blocked` |
| Important | `fixed` (and re-reviewed to passed), `rejected` (with technical reason, re-reviewed to passed), `blocked` |
| Minor | `fixed`, `rejected`, `deferred` (non-blocking follow-up), `user-accepted-risk` (user explicitly accepts, recorded in `audit.jsonl`) |

`user-accepted-risk` and `deferred` are never valid for Critical or Important findings. If the user declines to fix a Critical or Important finding, the topic finalizes as `blocked`.

If Critical findings exist, record the finding disposition needed through `record-review --status findings --report code-review-report.md` and `blocker`, then stop before code cleanup or finalize.

If Important findings exist, ask the user whether to fix them now or block the topic. Record the decision in `audit.jsonl`. Do not route to code cleanup or non-blocked finalization until the decision is recorded and the finding is fixed plus re-reviewed, or the topic is blocked.

If the current request addresses review findings:

1. Confirm each Critical and Important finding has one disposition: fixed and re-reviewed, rejected with technical reason and re-reviewed to `passed`, or blocked.
2. If fixes require implementation, route back to `executing-plan` when the existing plan covers them; otherwise route to `writing-plan` or `define-requirements` as needed.
3. If all Critical and Important findings are resolved and the latest `review.completed` event has `status=passed`, `critical=0`, and `important=0`, continue to the code cleanup decision. Minor findings may remain as non-blocking follow-up.
4. If any Critical or Important finding is not fixed or re-reviewed to a passing result, route finalization to `blocked`.

### Step 4: Ask About Code Cleanup

After execution review is recorded, ask the user whether to run optional code cleanup through `cleanup-code`.

User-facing response shape:

1. Summarize implemented changes, verification, and execution review result first.
2. Put the workflow status and next user choice at the bottom of the response.
3. Do not lead with the phase/next-action sentence. If included, place it in the final decision block.
4. Ask the user to choose between running code cleanup and skipping cleanup to finalize.
5. Use the user's current or clearly preferred language for the final decision prompt.

Canonical prompt, English:

```text
Execution review is complete. Would you like me to run optional code cleanup now, or skip cleanup and finalize?
```

Canonical prompt, Korean:

```text
실행 리뷰까지 완료했습니다. Optional code cleanup을 진행할까요, 아니면 cleanup 없이 finalize로 마무리할까요?
```

Treat it as cleanup/optimization, not bug review: reuse existing helpers, simplify code, improve efficiency, and check abstraction level. Do not call a host slash command such as Claude Code `/simplify`; invoke the AsUsual `cleanup-code` skill when the user approves.

Do not run code cleanup automatically. Stop after asking unless the user already answered in the current turn.

### Step 5: Handle Code Cleanup Decision

If the user declines code cleanup:

1. Record `code cleanup skipped` with `scripts/topic-log.py skip-code-cleanup --topic-dir <topic-dir> --reason <reason>`.
2. Invoke `finalize` in the same turn.

If the user approves code cleanup:

1. Invoke `cleanup-code`.
2. `cleanup-code` runs the four cleanup reviews, applies safe behavior-preserving cleanup, reruns relevant verification when files change, records `code cleanup completed`, and routes to `finalize`.

If code cleanup finds a correctness bug, route that issue back through normal review findings rather than treating code cleanup as the bug-review source of truth.

## State And Audit

Use `scripts/topic-log.py` from the plugin root for every audit update. Record review results as structured entries through the helper; prefer `record-review` and `skip-code-cleanup` over low-level edits when they match the transition. If the helper cannot express the update, stop and report the missing helper capability.

Record execution review mode:

Clean review, no report artifact:

```bash
python3 <plugin-root>/scripts/topic-log.py record-review \
  --topic-dir .as-usual/topic/2026-06-24-task-priority \
  --mode self \
  --status passed \
  --critical 0 \
  --important 0 \
  --minor 0 \
  --reason "Codex subagent spawning requires explicit user request."
```

Review with findings and report artifact:

```bash
python3 <plugin-root>/scripts/topic-log.py record-review \
  --topic-dir .as-usual/topic/2026-06-24-task-priority \
  --mode self \
  --status findings \
  --critical 0 \
  --important 1 \
  --minor 0 \
  --reason "Important finding recorded in code-review-report.md." \
  --report code-review-report.md
```

Allowed review modes:

- `independent`: a separate reviewer or subagent inspected the artifacts and diff
- `self`: the same agent reviewed the execution directly
- `local-prompt`: a local reviewer prompt was applied without a separate agent

Use the actual mode. Do not imply independent review when the host only allowed self-review.

Derived status should route as follows:

- After review completes and before code cleanup decision: phase `review-complete`, next action `decide-code-cleanup`.
- After code cleanup is skipped: phase `review-complete`, next action `finalize`.
- After code cleanup runs: phase `cleanup-complete`, next action `finalize`.
- If significant review findings need work: phase `review-fixes-needed`, next action `address-review-findings`.

## Anti-Patterns

- Treating task-level verification as a substitute for post-execution review.
- Reviewing only the implementer's summary instead of actual changed code.
- Calling a host `/simplify` slash command instead of the AsUsual `cleanup-code` skill.
- Running code cleanup before correctness review.
- Asking about code cleanup before Critical and Important findings are fixed and re-reviewed, or the topic is blocked.
- Treating code cleanup as a bug finder; use review for correctness bugs.
- Forcing fixes for Minor findings or optional cleanup after required Critical/Important fixes already have a passing re-review.
- Finalizing without recording review outcome and code cleanup decision.
