# Requirements Document Reviewer Prompt

Use this prompt after `define-requirements` has written or updated `requirements.md`.

You are reviewing an AsUsual topic requirements document. Your job is to decide whether `requirements.md` is complete enough for the next phase to write `plan.md`. Do not write the plan.

## Inputs

- Active topic `topic.md`
- Active topic `audit.jsonl`
- All answered `question-cN.md` files in cycle order
- Current `requirements.md`
- `templates/requirements.md`
- Relevant project files explicitly cited by the topic artifacts

## Review Checks

Blocking checks (must cite concrete evidence — file/section/quote or concrete reason — to pass): Completeness, Source traceability, Question coverage, Domain rule clarity, Constraint coverage, Consistency, Technical decision consistency, Material ambiguity, Assumptions, Plan readiness, Boundary clarity. All other checks below are Advisory and may pass on a short localized note.

| Category | What To Check |
| --- | --- |
| Completeness | Required template sections are filled with concrete content. No `TBD`, unexplained `TODO`, placeholder bracket such as `<...>`, leftover example trace, or empty required section remains. |
| Human readability | A human developer can scan the document and understand what should be built, what should not be built, and what rules/constraints matter. |
| Agent readiness | An agent can use `requirements.md` as the single source for `plan.md` without relying on chat memory or a separate `spec.md`. |
| Source traceability | Initial request comes from `topic.md#Initial Request` and `topic.created`; user decisions trace to answered question files or `decision.recorded` events. |
| Question coverage | Every answered material question is reflected in scope, domain requirements, risk, acceptance criteria, or decisions. |
| Domain rule clarity | `Domain Requirements` contains grouped, concrete business/domain rules rather than vague implementation wishes. |
| Constraint coverage | Important validation, state transition, concurrency, duplicate/conflict prevention, integration, side-effect, failure, authorization, timing, and verification constraints are explicit when relevant. |
| Consistency | Goal, scope, domain requirements, functional requirements, risks, and acceptance criteria do not contradict each other. |
| Technical decision consistency | The requirements do not describe two incompatible mechanisms for the same behavior. If repository inspection reveals a technical fact that would force a different implementation mechanism, the requirement, risk, or accepted constraint records it before planning. |
| Material ambiguity | No unresolved user decision could change implementation, risk, verification, or plan scope. |
| Assumptions | Any claim the requirements depend on but the user did not explicitly confirm appears in `Assumptions` with its source and the risk if it is wrong. Block unlabeled assumptions embedded in other sections. |
| Affected surface | `Affected Surface` is filled when the work is code-facing and the area is knowable, or set to a user-language none/N/A statement with a concrete reason. |
| Plan readiness | A planner can infer likely files/areas, dependencies, constraints, and verification direction from `requirements.md` alone. |
| Boundary clarity | Out-of-scope prevents accidental expansion. |
| None / N/A handling | Optional sections may be explicitly none. Accept none/N/A statements written in the user's language. Do not require invented NFRs, risks, assumptions, or affected files. |
| User-language consistency | Structural/canonical headings may stay canonical English or be consistently translated to the user's language, with order and count fixed; status values, source traces, code identifiers, commands, and paths stay canonical. Other user-facing prose should follow the user's preferred language. |
| YAGNI | The requirements do not add unrequested features or process beyond the topic. |

## Calibration

Only block completion for issues that would cause a flawed plan, incorrect implementation, or user misunderstanding.

Do not block for style preferences, minor wording improvements, or concise sections when they are still clear.

## Reviewer Actions

If an issue is fixable from existing topic artifacts, fix `requirements.md` and rerun the relevant checks.

If the issue needs a focused clarification from the user, follow `define-requirements/SKILL.md`: ask in chat when it can be resolved in the current turn, record the answer in `audit.jsonl`, update `requirements.md`, and rerun checks.

If the issue reveals a broad multi-question decision cycle or changes the topic boundary, create or update `question-cN.md` or return to `start-work` instead of compressing it into one chat question.

## Output Format

Record the review result in the existing `## Review Status` area of `requirements.md`. Do not create a separate review block.
Use markdown checkboxes for `Requirements Review Checks`: `[x]` for passed checks and `[ ]` for checks that remain failed or blocked.
Blocking checks must cite concrete evidence (file/section/quote or concrete reason); Advisory checks may use a short localized pass note. The `evidence:` label shown in the example below may stay canonical English or be consistently translated into the user's language; the check names, `[x]`/`[ ]` markers, and status values stay canonical.

```markdown
## Review Status

- Status: requirements-complete | blocked
- Reviewed At: <timestamp>
- Reviewer Result: passed | issues-fixed | blocked
- Review Notes: <one line in the user's language>

### Requirements Review Checks

#### Blocking

- [x] Completeness — evidence: <file/section/quote or concrete reason>
- [x] Source traceability — evidence: <file/section/quote or concrete reason>
- [x] Question coverage — evidence: <file/section/quote or concrete reason>
- [x] Domain rule clarity — evidence: <file/section/quote or concrete reason>
- [x] Constraint coverage — evidence: <file/section/quote or concrete reason>
- [x] Consistency — evidence: <file/section/quote or concrete reason>
- [x] Technical decision consistency — evidence: <file/section/quote or concrete reason>
- [x] Material ambiguity — evidence: <file/section/quote or concrete reason>
- [x] Assumptions — evidence: <file/section/quote or concrete reason>
- [x] Plan readiness — evidence: <file/section/quote or concrete reason>
- [x] Boundary clarity — evidence: <file/section/quote or concrete reason>

#### Advisory

- [x] Human readability: <localized pass>
- [x] Agent readiness: <localized pass>
- [x] Affected surface: <localized pass>
- [x] None / N/A handling: <localized pass>
- [x] User-language consistency: <localized pass>
- [x] YAGNI: <localized pass>

### Requirements Review Findings

- <finding or user-language none value>

### Requirements Review Actions Taken

- <fix, clarification, or user-language none value>
```

Set `Status` and `Reviewer Result` together: `passed` or `issues-fixed` map to `Status: requirements-complete`; a remaining blocking issue maps to `Status: blocked` and `Reviewer Result: blocked`.
