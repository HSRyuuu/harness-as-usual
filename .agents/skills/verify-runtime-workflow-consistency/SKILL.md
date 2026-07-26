---
name: verify-runtime-workflow-consistency
description: Verifies that AsUsual runtime rules, the entry skill, the three unit owners, the shared step skills, and the artifact templates stay semantically aligned. Use after changing anything under as-usual-rules/, skills/, templates/, or scripts/.
---

# Verify Runtime Workflow Consistency

## Purpose

The runtime contract is spread across rules, skills, templates, and the record
helper. This verification checks they still describe the same system.

Read the files and judge the semantics. This is not a grep pass — a stale rule
that uses current vocabulary is exactly what this exists to catch.

## When To Run

- After changing `as-usual-rules/**`
- After changing any public skill under `skills/**`
- After changing `templates/**`
- After changing `scripts/as_usual_record/**` — especially the vocabularies or gates
- After changing `hooks/session-start`

## Surface

| File | Owns |
| --- | --- |
| `as-usual-rules/core-rules.md` | unit definitions, classification, the seven core rules, record layer, completion, transitions |
| `as-usual-rules/safety-rules.md` | trust boundary, high-risk gate, issue read-only default |
| `as-usual-rules/record-commands.md` | `as-usual-record.py` command reference |
| `hooks/session-start` | one-sentence entry announcement |
| `skills/using-as-usual/SKILL.md` | activation, classification, folder creation, resume, hand-off |
| `skills/run-topic`, `run-direct-work`, `run-issue` | per-unit application matrices; `run-issue` also owns the investigation loop |
| `skills/gathering-context/SKILL.md` | all user-facing context gathering |
| `skills/write-requirements`, `write-plan`, `execute-plan`, `review-execution`, `cleanup-code`, `finalize`, `git-action` | shared step skills |
| `skills/*/…-quality-reference.md`, `…-reviewer-prompt.md` | quality references and reviewer prompts |
| `templates/**` | artifact shapes |
| `scripts/as_usual_record/constants.py`, `gates.py` | the vocabularies and gates everything else describes |

## Checks

### 1. Vocabulary matches the script

`constants.py` is the authority. Every phase, kind, verdict, approval action, and
next-action value named in rules, skills, or templates must exist there — and each
unit's phase subset in `UNIT_PHASES` must match what its owner skill's matrix
claims. A skill that documents a phase the script would reject is a defect.

### 2. Gates match `gates.py`

Every gate the docs describe as enforced must actually be enforced, and every
refusal the script can produce should be documented where an agent would hit it.
Current set: closed vocabulary and per-unit phase subsets, verdict required on
verification, evidence required on confirm, reason required on cancel, review
required before execution approval, a recorded verification required to finalize
a `topic` or `direct-work`, `conclusion.md` plus at least one confirmed entry
required to finalize an `issue`, sealed records reject non-link appends, blocked
files reject `move`.

A rule described as enforced but not implemented is worse than one described as
discretionary — it teaches the agent to rely on something that will not stop it.

### 3. The seven core rules appear once

`core-rules.md` §4 owns them. Other files may reference a rule by number or name,
but must not restate its conditions. Check especially that the skills do not grow
their own copies of the high-risk list or the completion criteria.

One exception, and only one: a `*-prompt.md` dispatched to a subagent may restate
whatever it needs, because the child cannot read the rules files. A reviewer told
to check that high-risk operations were approved is useless without knowing what
counts as high-risk. The rule being enforced is single ownership among files the
*same reader* reads — a subagent is a different reader with no access. Restating
in a file the controller itself reads is still a violation.

### 4. Owner matrices are complete and mutually consistent

Each of the three owners declares every step it uses, with a strength. A step
skill that exists but appears in no matrix is unreachable; a matrix entry naming a
skill that does not exist is a dangling route. `write-plan` must appear for both
`topic` and `direct-work` with different strengths, since it carries core rule 7
for both.

### 5. Step skills stay unit-agnostic

`gathering-context`, `write-plan`, `execute-plan`, `review-execution`,
`cleanup-code`, `finalize`, and `git-action` must not branch on the calling unit.
Strength differences belong in the owner's matrix and in what the caller passes,
not in `if unit == topic` inside the step. This was the original defect being
refactored away; it regresses easily.

### 6. Templates match the skills that write them

Section lists in `templates/**` match what the writing skill describes. No
template carries a review status block, an execution mode field, or a `[Answer]:`
marker — those were removed with the gates that required them.

### 7. Deleted concepts have not returned

None of these should appear as live guidance anywhere in the runtime surface:
`topic.md`, `question-cN.md`, `problem.md`, `journal.jsonl`,
`code-review-report.md`, `execute/`, `clean-up/`, `topic-log.py`,
`journal-log.py`, `start-work`, `hand-off`, `find-cause`, `direct-execute`,
`routed-to-find-cause`, `-complete` phases, execution-mode selection, the
question-file cycle.

`using-as-usual` may name the old artifacts in exactly one place: detecting a
pre-v2 folder to refuse resuming it.

### 8. Records and transitions are described identically everywhere

The `move`-versus-new-folder rule, the blocked-file list, and the "if a linked
unit exists, go back to it" rule appear in `core-rules.md` §7. Owner skills may
reference it; none should restate the conditions.

### 9. Safety survives the trimming

The trust boundary, the high-risk list, secret handling, and the issue read-only
default are unchanged in substance. The refactor deliberately loosened the
judgment layer — verify it did not loosen these.

### 10. Language and artifact conventions hold

User-facing prose follows the user's language; identifiers, commands, and paths
stay canonical. Structural headings stay canonical English and keep their order;
a section that would be empty is omitted and anything extra goes last. Every
artifact opens with `unit`/`slug`/`created` frontmatter filled with real values —
an unreplaced `<…>` placeholder in a work folder is a defect.

## Report

```markdown
## Runtime Workflow Consistency

- Result: pass | issues-found
- Checked: <files>

### Issues

- <file:line> — <what is inconsistent, and with what>
```

Report what is actually inconsistent. A check that passes needs no evidence
paragraph.
