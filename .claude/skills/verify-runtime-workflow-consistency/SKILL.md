---
name: verify-runtime-workflow-consistency
description: Verifies that AsUsual runtime rules, the entry skill, the `run-work` owner matrix, the shared step skills, and the artifact templates stay semantically aligned. Use after changing anything under as-usual-rules/, skills/, templates/, or scripts/.
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
| `as-usual-rules/core-rules.md` | the work model, the request boundary, the seven core rules, record layer, completion, follow-up work, autopilot |
| `as-usual-rules/safety-rules.md` | trust boundary, high-risk gate, read-only default for investigation |
| `as-usual-rules/record-commands.md` | `as-usual-record.py` command reference |
| `hooks/session-start` | one-sentence entry announcement |
| `skills/using-as-usual/SKILL.md` | activation, folder creation, request boundary, resume (legacy folders too), hand-off |
| `skills/run-work/SKILL.md` | the one application matrix, a condition per row |
| `skills/gathering-context/SKILL.md` | all user-facing context gathering |
| `skills/investigate`, `write-requirements`, `write-plan`, `execute-plan`, `review-execution`, `cleanup-code`, `finalize`, `git-action` | shared step skills; `investigate` owns the investigation loop and its endings |
| `skills/*/…-quality-reference.md`, `…-reviewer-prompt.md` | quality references and reviewer prompts |
| `templates/**` | artifact shapes |
| `scripts/as_usual_record/constants.py`, `gates.py` | the vocabularies and gates everything else describes |

## Checks

### 1. Vocabulary matches the script

`constants.py` is the authority. Every phase, kind, verdict, approval action, and
next-action value named in rules, skills, or templates must exist there — and every
phase in `PHASES` except `blocked` must be a row in `run-work`'s matrix. There are
no per-unit phase subsets. A skill that documents a phase the script would reject
is a defect.

`UNITS` is `{"work"}`; `LEGACY_UNITS` (`inbox`, `topic`, `direct-work`, `issue`)
stay readable and resumable. Runtime surfaces offer only `work` for new folders
and never present the legacy labels as a choice — but resuming a legacy folder
must still be described as supported.

Two vocabularies, not one: `KINDS`/`LIFECYCLE_EVENTS` are what `add` may write,
and `AUDITABLE_*` add the retired values that `validate` still accepts. Runtime
surfaces describe the writable set — a retired value offered as a live choice is
a defect, but finding one in an existing record is not.

### 2. Gates match `gates.py`

Every gate the docs describe as enforced must actually be enforced, and every
refusal the script can produce should be documented where an agent would hit it.
Current set:

- the closed vocabulary (one phase set; `investigating`/`concluding` and
  `lifecycle:unit-selected` retired — `validate` accepts, `add` refuses)
- `--verdict` required on verification, `--evidence` on confirm, `--reason` on cancel
- a plan review before execution approval, **newer than the previous execution
  approval** — one review does not license every later approval — and only a
  `review` with `--phase write-plan --status success` counts, with `plan.md` on
  disk. The three refusals are distinct: no plan file, no review at all, and
  reviews that are not successful plan reviews
- every approval action — `execution`, `high-risk`, `reproduction`,
  `git-action` — recorded with `--actor user --status success`, and the same for
  the `--reason` that closes a record over an open verification. This is a floor,
  not proof: the docs must say so rather than presenting it as evidence the user
  decided. `reproduction` needs no plan review
- finalize judges record content, not the unit label:
  - refused as "nothing to finalize" when the record holds neither an
    `execution` approval nor `conclusion.md`
  - with an approved execution: a recorded verification, **with no open
    verification left** — an `INCONCLUSIVE` or `FAIL` stays open until a later
    verification names its seq with `--resolves`, and closing with one open needs
    an explicit `--reason`, while a missing verification is refused outright and
    no reason overrides that — plus `verification.md` on disk when
    `requirements.md` exists
  - with `conclusion.md`: at least one confirmed entry
  - both sets when one folder investigated and implemented; a `cancelled` close
    is unaffected
- two legacy shims only: a legacy `issue`'s `execution` approval is a
  reproduction script (not plan-gated, not a code change), and a legacy `topic`
  always needs `verification.md` to finalize. Any other branch on the unit label
  in `gates.py` or `records.py` is a defect
- `--resolves` only on `verification` and `blocker`, closing one still-open entry
  of its own kind; a target of another kind, a passing verification, a target that
  something already resolved, and any other kind carrying the flag are refused.
  Whether a resolving `blocker` is itself open in the derived status is decided by
  its `--status`: `success` means it closed something and introduced nothing, so
  it drops off; `warning` or `error` means something still blocks, so it stays
- sealed records reject non-link appends
- `init` creates only `work`, refuses a folder that already holds `contexts.md`
  or `audit.jsonl`, and **adopts** one holding only artifacts — that folder was
  never a record, so there is nothing to reset
- no `move` command exists; `status --json` carries no `moveAllowed`

`add` is the only path that tightened. `validate` must stay as permissive as it
was: a value that was legal when it was written keeps auditing clean, so a gate
added here that also rejects existing records is a defect.

A rule described as enforced but not implemented is worse than one described as
discretionary — it teaches the agent to rely on something that will not stop it.

### 3. The seven core rules appear once

`core-rules.md` §4 owns them. Other files may reference a rule by number or name,
but must not restate its conditions. Check especially that the skills do not grow
their own copies of the high-risk list or the completion criteria.

One narrow exception: a `*-prompt.md` dispatched to a subagent may restate what
the child genuinely cannot reach, because the rule being enforced is single
ownership among files the *same reader* reads. Restating in a file the controller
itself reads is still a violation.

What the child cannot reach is now smaller than it was. `code-reviewer-prompt.md`
takes `{SAFETY_RULES_PATH}` as a required input and makes the reviewer read the
authority itself, returning `blocked` when it cannot — so a copy of the high-risk
list or of the carve-outs in that prompt is a defect, not an exception. Check that
`review-execution` actually fills the placeholder with a resolved installed path,
and that the `blocked` verdict has a handler on the caller's side. A prompt that
demands a file nobody passes is the same failure wearing better prose.

### 4. The owner matrix is complete

`run-work` declares every step with a condition and a strength, and contains no
procedure. A step skill that exists but appears in no row is unreachable; a row
naming a skill that does not exist is a dangling route. `write-plan` must carry
both strengths (full with `requirements.md`, checklist otherwise), since it
carries core rule 7 for both. `investigate` must appear with its three endings
owned by `investigate` itself, not restated in the matrix.

### 5. Step skills stay unit-agnostic

`gathering-context`, `investigate`, `write-requirements`, `write-plan`,
`execute-plan`, `review-execution`, `cleanup-code`, `finalize`, and `git-action`
must not branch on a unit label. Strength differences belong in the matrix and in
what the caller passes. Conditions a step reads from the record — whether
`requirements.md` or `conclusion.md` exists — are content, not a label, and are
fine.

### 6. Templates match the skills that write them

Section lists in `templates/**` match what the writing skill describes. No
template carries a review status block, an execution mode field, or a `[Answer]:`
marker — those were removed with the gates that required them.

### 6a. Verification has one owner and one vocabulary

`verification.md` is the evidence document for any executed change. Check
that one story is told everywhere:

- The condition that keeps an `INCONCLUSIVE` or `FAIL` open, and what `--resolves`
  does about it, is **defined** only in `core-rules.md` §6. `record-commands.md`,
  the skills, and `templates/**` may reference it but must not restate the
  condition. Two definitions is the failure to look for.
- `record-commands.md` no longer keeps a table of refusals and their fixes: the
  script's own messages carry the recovery, so a second copy would drift. Any
  refusal wording that reappears there must match what the script actually prints
  — run the command and compare the string.
- `templates/report.md` §Verification links `verification.md` and states the
  outcome; it does not carry a per-criterion table. Its wording parallels
  §Review, which solved the same problem earlier.
- Verdicts are only `PASS`, `FAIL`, `INCONCLUSIVE`. No template or skill offers a
  softer word for a gap, and none carries an emoji verdict column.
- Two bands are described as changing after sealing, and no others:
  `verification.md`, marked as outside the record, and `contexts.md`'s
  `## Linked Work`, which `link` writes on both sides whether or not the record is
  closed. The second exists because a sealed record cannot retract its own decision,
  so the link is its only correction channel. The script's sealing behaviour is
  unchanged either way: `check_not_closed` still admits only `lifecycle:linked`.

### 7. Deleted concepts have not returned

None of these should appear as live guidance anywhere in the runtime surface:
`topic.md`, `question-cN.md`, `problem.md`, `journal.jsonl`,
`code-review-report.md`, `execute/`, `clean-up/`, `topic-log.py`,
`journal-log.py`, `start-work`, `hand-off`, `find-cause`, `direct-execute`,
`routed-to-find-cause`, `-complete` phases, execution-mode selection, the
question-file cycle, `run-topic`, `run-direct-work`, `run-issue`, the
four-option classification menu, `move`, `inbox` as a new unit, and the
`investigating`/`concluding` phases.

Legacy unit names may appear only where a legacy folder is being read or resumed.

`using-as-usual` may name the old artifacts in exactly one place: detecting a
pre-v2 folder to refuse resuming it.

### 8. Follow-up work is described identically everywhere

The same-folder carry-on after an investigation, and the "if a linked record
exists, go back to it; otherwise create one and link" rule, appear in
`core-rules.md` §7. `run-work` and `investigate` may reference it; neither should
restate the conditions.

### 9. Safety survives the trimming

The trust boundary, the high-risk list, secret handling, and the read-only
default for investigation (with `reproduction` approval) are unchanged in
substance. The refactor deliberately loosened the
judgment layer — verify it did not loosen these.

`core-rules.md` §4 also states four ceilings, and they must stay readable and
accurate: work that ends without `finalize` records no completion
transition, so rule 3 is prompt-only there; the script checks that
`verification.md` exists but never that a `PASS` was earned; a pointer
`plan.md` satisfies the plan-file check without the script seeing the plan
behind it; and a git action
chosen after sealing leaves no approval event, so rule 4 rests on the user's
choice and git history. A gate claimed but absent is the defect this check
exists to catch — in either direction.

### 10. Language and artifact conventions hold

User-facing prose follows the user's language; identifiers, commands, and paths
stay canonical. Structural headings stay canonical English and keep their order;
a section that would be empty is omitted and anything extra goes last. Every
artifact opens with `unit`/`slug`/`created` frontmatter filled with real values —
an unreplaced `<…>` placeholder in a work folder is a defect.

### 11. Autopilot has one owner and one halt line

`as-usual-rules/` still holds exactly three files, and the whole autopilot rule
lives in `core-rules.md` §10. Skills reference it; none restates the hard-gate
list or the stop conditions in its own words.

Two things the 0.2.2 auto mode got wrong, checked explicitly because they are
what got it reverted:

- Nothing anywhere tells the agent to record an approval on the user's behalf.
  Every `--actor user` in a skill is a real user decision.
- The stop guard survives: approval-shaped actions and facts that cannot be cited
  are stops, and `(autopilot)` decisions are required to name their evidence.

### 12. The document skeleton has one owner

`contexts.md` band headings and their order live in `core-rules.md` §3, and
`scripts/as_usual_record/contexts.py` implements that list as `SECTION_ORDER`.
The two must name the same headings in the same order.

This is a real drift, not a hypothetical one: when `init` stopped writing the
bands as placeholders, the template stopped being the specification and the only
surviving list was the constant in code. A prose list that has fallen behind the
constant sends an agent to invent a heading name, and `append_to_band` then
places a link somewhere the reader does not look — a document and a record
disagreeing, which is the failure the record layer exists to prevent.

```bash
python3 - <<'CHECK'
import re, sys
sys.path.insert(0, "scripts")
from as_usual_record.contexts import SECTION_ORDER

doc = open("as-usual-rules/core-rules.md", encoding="utf-8").read()
block = re.search(r"The bands are these headings.*?```markdown\n(.*?)```", doc, re.S)
named = [line.split("  ")[0].strip() for line in block.group(1).splitlines()
         if line.startswith("## ")] if block else []
print("code :", list(SECTION_ORDER))
print("prose:", named)
print("match" if named == list(SECTION_ORDER) else "DRIFT")
CHECK
```

Also confirm `templates/contexts.md` still ships no band placeholder — a
reintroduced `_Not set._` puts the skeleton back and makes §3 the second answer
rather than the only one.

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
