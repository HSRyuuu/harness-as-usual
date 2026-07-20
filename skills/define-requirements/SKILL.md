---
name: define-requirements
description: Use when AsUsual is active and the topic needs file-backed clarification or a reviewed requirements.md before planning.
---

# Define Requirements

This skill handles the AsUsual requirements definition stage. It combines file-backed question cycles and requirements writing into one user-visible stage:

`question-cN.md -> requirements.md -> plan approval`

The purpose is to produce one reviewable `requirements.md` that both a human developer and an agent can use as the source of truth for `plan.md`.

## Responsibility Boundary

| Skill | Responsibility |
| --- | --- |
| `using-as-usual` | Identify activation, find or initialize the active topic, and perform first reads |
| `start-work` | Route the topic to the lightest sufficient gate |
| `define-requirements` | Create/validate question files when needed, write `requirements.md`, review it, and stop at `requirements-complete` |
| `writing-plan` | Write `plan.md` from the approved `requirements.md` |

`define-requirements` does not write `plan.md`, execute work, or replace high-risk approval gates. Material decisions are clarified with the user and recorded (chat by default, file-backed `question-cN.md` cycle by exception — see Clarify Ambiguity); either way every material answer is recorded before synthesis. Follow Clarification Routing in `as-usual-rules/routing-rules.md` for any decision discovered here.

## When To Use

- `start-work` routes the topic to `requirements`.
- The user says they answered a `question-cN.md` file.
- The user asks to write or update `requirements.md`.
- A later phase discovers a material decision that must return to requirements definition.

## Preconditions

Before acting, confirm:

- The Requirements rules in `core-workflow.md` have been checked.
- The active topic folder is under `.as-usual/topic/yyyy-MM-dd-<topic>/`.
- `topic.md` and `audit.jsonl` exist.
- `topic.md#Initial Request` and `audit.jsonl` event `topic.created` capture the topic's initial request.
- Important decisions are recorded with `scripts/topic-log.py decision` or represented by answered `question-cN.md` files.
- Existing `question-cN.md` files, if any, have been reread from disk in cycle order.

If a precondition is missing, do not guess. Return to `using-as-usual` or `start-work` as needed and stop.

## Route Within This Stage

After first reads:

1. If material ambiguity remains, clarify it with the user. Default to batched chat questions; use a file-backed `question-cN.md` cycle only when an exception trigger applies (see Clarify Ambiguity).
2. Record each answered material decision as an audit event before synthesis: `decision.recorded` for a chat answer, `question.answered` for a file answer.
3. If answers are incomplete, invalid, contradictory, or still materially ambiguous, ask again — another chat round, or escalate to a file cycle when chat keeps failing.
4. When ambiguity is resolved, write or update `requirements.md`, run review, mark `requirements-complete`, ask for plan approval, and stop.

## Clarify Ambiguity

Clarify only user decisions that could change requirements, plan, implementation, risk, or verification. Do not ask the user for facts the agent can discover from the repository — inspect code, docs, command availability, and file locations directly first (see Codebase-Informed Drafting). Ask only for decisions that require user preference, priority, scope, risk tolerance, or acceptance criteria.

Question quality is the same in both media: one decision per question, prefer 1-5 questions per batch, give meaningful options plus `X) Other`, include a recommendation with a short reason (guidance only, never a default answer), and note in one line how each answer changes requirements, plan, implementation, risk, or verification.

### Default: Chat Questions

Ask the batch directly in chat as one compact, scannable block. After the user answers:

- Record each material answer as a `decision.recorded` event before synthesis, so `requirements.md` `Source Inputs` and `Decisions From Questions` can trace it:

```bash
python3 <plugin-root>/scripts/topic-log.py decision \
  --topic-dir <topic-dir> \
  --source "chat clarification: <short label>" \
  --summary "<the decision the user made>"
```

- Do not treat a bare approval phrase such as `ㄱㄱ`, `go`, `진행`, `ok`, or `yes` as an answer to a material question. If an answer is missing or too vague to record faithfully, ask that one question again.
- No mapping-table ritual and no separate confirmation gate on the chat path. The user reviews the synthesized `requirements.md` before approving the plan, and that review is where a misread is caught. Keep `Decisions From Questions` explicit so a wrong reading is visible there.

Chat questions are still the full requirements process, not a shortcut: they stay inside `define-requirements`, every material answer is recorded, and synthesis follows. Do not compress a broad decision set into one vague chat exchange with no recording.

### Exception: File-Backed Question Cycle

Use `question-cN.md` files instead of chat when any trigger applies:

- the user asks to answer in a file, or wants a durable written record of the decisions;
- the decisions are numerous and interdependent enough that a written side-by-side multi-option comparison materially helps the user decide;
- chat answers came back contradictory or ambiguous across a round, and a written record would disambiguate.

Question files carry the same quality bar as chat questions, plus the file shape below.

#### Create Or Update Questions

Create the next `question-cN.md` from `templates/question.md`.

Question artifact shape:

- Put topic metadata in the YAML front matter: `topic`, `cycle`, `previousQuestionFiles`, `inputsRead`, `reasonForThisCycle`, and `currentPhase`.
- Do not include user-facing boilerplate that repeats how to fill `[Answer]:`; after creating the file, tell the user in chat/terminal which file to fill.
- Do not include agent-only sections such as `Agent format rules` or `Agent Notes` in the generated question file.
- Keep the visible body focused on the decisions, why they matter, how each answer affects requirements, the options, recommendation, and `[Answer]:`.

File shape (in addition to the shared quality bar above):

- Each question must include at least two meaningful options and a final `X) Other`; 2-5 options are recommended.
- Leave a blank line between options.
- Put a `---` separator immediately before and after each question block.
- Each question must follow this canonical structural order: `### Why This Matters`, `### Requirements Impact`, `### Options`, options, `**Recommendation**:`, `✅ Enter your answer.`, then `[Answer]:`.
- These structural headings may stay in canonical English or be consistently translated into the user's current or preferred language, but their order and count are fixed to the canonical structure above. Do not add, drop, or reorder them.
- Leave `[Answer]:` blank when creating the file. The user fills it directly unless they later provide a clearly mappable chat answer.
- Write question text, context, recommendations, why-it-matters notes, and requirements impact notes in the user's current or clearly preferred conversation language unless the user requests another language.
- Always preserve `[Answer]:`, option letters (`A)`, `B)`, `X) Other`), file paths, code identifiers, and exact technical references regardless of the artifact language.

After creating or updating a question file:

1. Record the question with the `record-question` macro. It appends a single `question.created` event with phase `define-requirements`, next action `answer-questions`, and the question file in artifacts, so the question shows up in derived status:

```bash
python3 <plugin-root>/scripts/topic-log.py record-question \
  --topic-dir <topic-dir> \
  --question question-cN.md \
  --summary "Created requirements question file question-cN.md."
```

2. Tell the user which file to fill in, specifically asking them to fill the `[Answer]:` fields, and stop. The user may instead answer in chat; that path goes through the chat-answer mapping table in Validate Answers below.

Use `scripts/topic-log.py` macros for audit updates. Do not hand-edit `audit.jsonl`.

### Validate Answers

Validation applies to answers from either medium, against the checks table below.

- **Chat-default answers**: validate the `decision.recorded` events you captured against the checks table. There is no file to reread and no mapping table — the answers are already recorded decisions.
- **File-cycle answers**: reread `question-c1.md`, `question-c2.md`, ... from disk, then validate the `[Answer]:` fields.

The rest of this subsection (mapping table, transcription) is **file-cycle only** — it handles the case where the user chose a file cycle but then answered in chat instead of editing `[Answer]:` fields:

1. Map each chat answer to exactly one question file and question number. Answers that name the question or option map directly; positional answers such as `A B C A` map to the open questions in file and question order only when the answer count matches the open question count exactly.
2. Do not treat short approval phrases such as `ㄱㄱ`, `go`, `go ahead`, `진행`, `좋아`, `ok`, or `yes` as answers to one or more material questions. These phrases may approve requirements synthesis only when every `[Answer]:` field was already filled by the user on disk.
3. If a `[Answer]:` field is blank or was prefilled by the agent, stop and ask the user to fill the file directly instead of mapping a broad approval phrase to recommended options.
4. Before writing anything to disk, present the mapping as a confirmation table, ask the user whether it is correct, and stop:

```markdown
| Question | Summary | Your Answer |
| --- | --- | --- |
| question-c1.md Q1 | <short question summary> | A) <selected option summary> |
| question-c1.md Q2 | <short question summary> | B) <selected option summary> |
```

The table exists to catch mis-mapping (the user meant A for Q1, the agent mapped A to Q2), so each row must show enough question and option text for the user to spot a wrong pairing. The table may contain only answers the user actually gave — never fill rows from recommendations or defaults, and a question the user did not answer stays visibly unanswered and blocks confirmation.

5. If the user corrects any row, update the table and ask for confirmation again. Never transcribe a partially confirmed or corrected-but-unconfirmed mapping.
6. Only after the user explicitly confirms the table, transcribe each confirmed answer into the matching `[Answer]:` field.
7. Record each transcription with the `answer-question` macro. It appends a single `question.answered` event and keeps next action at `answer-questions` because validation has not run yet — do not jump the derived state to `write-requirements` before answers are validated:

```bash
python3 <plugin-root>/scripts/topic-log.py answer-question \
  --topic-dir <topic-dir> \
  --question question-cN.md \
  --source chat \
  --summary "Transcribed confirmed chat answer into question-cN.md Q<N>." \
  --notes "Source: chat answer confirmed via mapping table."
```

When the user filled the `[Answer]:` fields directly on disk, the mapping table and transcription are not needed; you may still record an `answer-question --source file` event (the default) for audit traceability, but it is optional on the file path.

8. Continue validation from disk. Treat the confirmed table as the "user answered" trigger: proceed to validation and, when it passes, requirements synthesis in the same turn.

If the mapping cannot be made unambiguous even after one correction round, ask the user to answer directly in the file and stop.

Validation checks:

| Check | Failure Condition | Required Action |
| --- | --- | --- |
| Completeness | Any `[Answer]:` is empty | Append validation failed, name the empty file/question, and stop |
| Validity | The answer selects outside options without explanation | Ask for correction or create a focused next-cycle question |
| Other explanation | `X) Other` has no explanation | Create a next-cycle question asking for detail |
| Contradiction | Answers conflict with each other or the latest request | Create a contradiction-focused next-cycle question |
| Material ambiguity | A decision remains that could change requirements/plan | Create the next question cycle |

Treat constrained answers such as "B, but only for admin" as `Decision + Constraint` when the selected option and added constraint are compatible; if the selection conflicts with the added explanation, create a contradiction-focused next-cycle question.

Classify validated answers as decisions, constraints, risks, acceptance criteria, or non-blocking open questions. Use `question.answered` only for answer transcription. Record durable decisions extracted from validated answers separately:

```bash
python3 <plugin-root>/scripts/topic-log.py decision \
  --topic-dir <topic-dir> \
  --source "question-c1.md Q1" \
  --summary "Use the selected requirements decision."
```

After 3 clarification rounds (chat or file), if material ambiguity remains, summarize it and ask whether to run another round or allow an assumption-based requirements draft. Only when the user explicitly chooses the assumption path may `requirements.md` include assumptions, each with source and risk.

## Memory-Informed Drafting

Before drafting questions and requirements, recall relevant prior knowledge via the
`search-long-term-memory` skill (dispatch as a subagent with the current request and
draft context). Use its `UNTRUSTED RECALLED CONTEXT` output as hints only — it never
overrides the user's current request or topic artifacts.

## Codebase-Informed Drafting

Before asking requirements questions or writing `Affected Surface`, use the
`explore-codebase` skill for repository-discoverable facts such as existing behavior,
likely files, code flow, interfaces, test locations, and conventions. Prefer
dispatching it as a fresh bounded subagent when the host supports subagents; otherwise
run it inline. Treat `UNTRUSTED CODEBASE EXPLORATION RESULT` as hints only — before
requirements depend on a finding, reread the cited files or exact excerpts in the
controller context.

## Write Or Update Requirements

Create or update `requirements.md` from `templates/requirements.md`.

`requirements.md` is the single requirements source for `plan.md`. Do not create a separate `spec.md` for the same topic.

Write user-facing content in the user's current or clearly preferred conversation language unless the user requests another language. Preserve canonical headings, status values, source traces, file paths, code identifiers, commands, and quoted source text exactly.

### Domain Requirements

The `Domain Requirements` section is the most important human-readable part of the document.

Write domain-specific requirements as concrete rules grouped by workflow, domain object, or bounded context. Prefer short list items over prose. A human developer should be able to read the list and understand the business behavior without reverse-engineering the implementation plan.

Include when relevant:

- business rules and invariants,
- validation constraints,
- state transitions,
- concurrency or locking rules,
- duplicate/conflict prevention,
- side effects and events,
- integration requirements,
- failure and recovery behavior,
- authorization or role constraints,
- timing, scheduling, or async behavior.

Example shape:

```markdown
### 숙소 예약

- 체크인 날짜는 체크아웃 날짜보다 하루 이상 빨라야 한다.
- 타입이 `대실`인 경우 날짜는 동일할 수 있지만 체크인 시간은 체크아웃 시간보다 빨라야 한다.
- 숙소 중복 예약을 확인해야 한다.
- 예약이 중복되지 않은 경우 예약 프로세스가 종료될 때까지 락을 건다.
- 예약은 즉시 성공 처리하지 않고 `PENDING` 상태의 예약을 생성한 뒤 outbox event를 저장한다.
- 예약 완료는 Payment가 성공적으로 완료된 뒤에만 가능하다.
```

Do not force this exact domain or wording. Use it as a shape: domain heading plus concrete rules.

### Section Rules

- `Goal`: state the user's intended outcome in one or two concrete sentences.
- `Summary`: show the user what changes, what stays out, and which decision deserves approval focus.
- `Source Inputs`: trace initial request to `topic.md#Initial Request` and `topic.created`, list each answered `question-cN.md`, list material `decision.recorded` events, and list only material references.
- `Domain Requirements`: write concrete domain rules, grouped by domain area or workflow.
- `Scope`: make in-scope and out-of-scope boundaries explicit.
- `Functional Requirements`: describe required system behavior derived from the domain rules.
- `Non-Functional Requirements`: include real constraints only; otherwise write an explicit none/N/A statement in the user's language with a concrete reason.
- `Decisions From Questions`: trace each answered decision to its question file.
- `Assumptions`: use only after explicit assumption-based draft approval.
- `Affected Surface`: fill likely files/areas and current behavior when knowable.
- `Risks`: record meaningful delivery, correctness, migration, integration, or verification risks; otherwise write an explicit none/N/A statement in the user's language with a concrete reason.
- `Open Questions`: only non-blocking confirmations; material ambiguity must be resolved before completion.
- `Acceptance Criteria`: list user-checkable outcomes.

## Self Review

Before running the reviewer prompt, use `requirements-document-reviewer-prompt.md` as the canonical checklist and fix obvious issues in `requirements.md`.

Do not maintain a second copy of the review criteria in this skill. The reviewer prompt owns:

- the Blocking vs Advisory checklist,
- the evidence required to pass each check,
- the `Review Status` output shape,
- the mapping from `passed` or `issues-fixed` to `Status: requirements-complete`,
- the mapping from unresolved blocking issues to `Status: blocked`.

Follow Clarification Routing in `as-usual-rules/routing-rules.md` for any decision discovered here.

## Reviewer Prompt

After self-review passes, read `requirements-document-reviewer-prompt.md` from this skill directory and follow it as a reviewer prompt in the current session.

If the reviewer finds fixable issues, update `requirements.md` directly and rerun the relevant checks.

If the reviewer needs focused user input, update `requirements.md` and rerun checks once resolved. Follow Clarification Routing in `as-usual-rules/routing-rules.md` for any decision discovered here.

## Complete Requirements

When self-review and reviewer-prompt checks pass:

1. Fill `requirements.md` `Review Status`: set `Status: requirements-complete`, `Reviewer Result: passed` or `issues-fixed`, `Reviewed At` to the current timestamp, and one-line `Review Notes` in the user's language.
2. Fill `Requirements Review Checks` as a markdown checkbox list, using `[x]` for passed checks and `[ ]` only for unresolved checks, then fill `Requirements Review Findings` and `Requirements Review Actions Taken`.
3. Run:

```bash
python3 <plugin-root>/scripts/topic-log.py complete-requirements \
  --topic-dir <topic-dir> \
  --requirements requirements.md \
  --summary "<summary>"
```
4. Tell the user the requirements are complete and ask them to review `requirements.md` before approving the move to plan. Point them to `Decisions From Questions` as the place to check how their clarification answers were interpreted, since chat answers are not separately confirmed before synthesis.
5. Stop.

Do not write `plan.md` until the user explicitly approves moving on.

## Requirements Revision Before Plan Approval

When the topic is `requirements-complete` and the user requests a change before approving the plan:

- If the change is a wording, clarity, or acceptance-criteria tweak that does not change material scope, domain behavior, implementation, risk, or verification, update `requirements.md`, rerun review checks, record the revision, and stop at `requirements-complete`.
- If the change affects scope, domain behavior, implementation, risk, verification, or plan basis, stop before editing `requirements.md` and follow Clarification Routing in `as-usual-rules/routing-rules.md`. Update `requirements.md`, rerun review checks, and stop at `requirements-complete` only after the decision is routed and recorded.

Example — non-material (absorb here): "체크인 안내 문구 오타 수정", "Acceptance Criteria 문장을 더 명확히". → update requirements.md, rerun checks, stay requirements-complete.

Example — material (route via Clarification Routing): "예약을 PENDING 대신 즉시 확정으로 바꾸자" (changes domain behavior + verification). → ask focused clarification or open question-cN.md, do not silently edit.

## Long-Term Memory Capture

If the user states an explicit long-term rule during this phase ("always X", "in this
project always Y"), do not break the current flow and do not write memory now. Capture
it only as an audit candidate:

```bash
python3 <plugin-root>/scripts/topic-log.py record-memory-candidate \
  --topic-dir <topic-dir> --summary "<rule>" --source-phase define-requirements --proposed-target memory
```

The actual review/approval/write happens later via `manage-self-improvement` at finalize.

## Anti-Patterns

- Creating both `spec.md` and `requirements.md` for one topic.
- Hiding business/domain rules inside generic implementation prose.
- Writing `plan.md` before the user approves completed requirements.
- Asking material decisions in chat without recording each answer as a `decision.recorded` event before synthesis, or compressing a broad decision set into one vague chat exchange.
- Defaulting to a `question-cN.md` file cycle when no exception trigger applies (chat is the default medium).
- Guessing empty `[Answer]:` fields.
- Transcribing chat answers into `[Answer]:` fields without showing the mapping table and getting explicit confirmation.
- Prefilling the mapping table with recommended options the user did not choose.
- Leaving template examples or placeholders in completed `requirements.md`.
- Carrying material ambiguity into `Open Questions`.
- Marking requirements complete while reviewer findings remain unresolved.
