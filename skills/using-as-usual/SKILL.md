---
name: using-as-usual
description: Use only when the user asks for AsUsual by name, mentions .as-usual artifacts, or asks to resume work in progress. The single entry point — it classifies the work unit and hands off to its owner skill. Do not use it for an ordinary development or investigation request the user did not route here.
---

# Using AsUsual

The single entry point for AsUsual. It decides whether the harness applies,
classifies the work into one unit, creates or resumes the work folder, and hands
off. It owns no pipeline of its own.

Read `as-usual-rules/core-rules.md` before acting. Resolve the plugin root from
the SessionStart hook announcement, or as the parent of the `skills/` directory
containing this file.

## Three Ways In

```text
using-as-usual                → nothing in progress named: scan .as-usual/ and offer resume candidates
using-as-usual <path>         → resume the work folder that path belongs to
using-as-usual <request>      → new work: classify, then hand off
```

A cross-session resume is the same path as any other resume. There is no
separate hand-off procedure.

Any of the three can arrive with an autopilot instruction — a flag or the same
thing in prose. `core-rules.md` §10 owns what it does.

## Activation

AsUsual is opt-in. Enter it only when the user asked for it — any of these:

- The user says `as-usual` or `AsUsual`.
- The user mentions `.as-usual/`, `contexts.md`, `audit.jsonl`, `requirements.md`,
  `plan.md`, `conclusion.md`, or a work folder path.
- The user asks to resume, continue, or check what is in progress, and a work
  folder exists under `.as-usual/`.
- The user invokes an owner skill directly (`run-topic`, `run-direct-work`,
  `run-issue`).

Nothing else activates it. A development or investigation request is **not** a
signal on its own, and neither is the hook announcement or the presence of a
`.as-usual/` folder. Handle those requests normally.

When the user invokes an owner skill directly, that skill takes over and the unit
is settled; do not re-classify. **Creating the folder is still this skill's job**
— an owner skill with nowhere to record routes back here for step 3, then
continues. Naming the unit skips the choice, never the record.

### Recommending it

When a request the user did not route here would clearly benefit from a record —
it will reach production, it is hard to undo, or a cause has to be established
before anything changes — say so in one line and carry on with the work:

```text
This looks worth recording as an AsUsual `topic`. Say the word and I'll set it up.
```

One line, once, at the point you notice it. Do not ask a question, do not stop
work, do not present the four options, and do not raise it again in the same
session. The user not taking it up is an answer.

## New Work

### 1. Classify

Apply the two-question tree in `core-rules.md` §2 and form a recommendation.

While you are there, scan `.as-usual/` for folders that are still open and read
their `contexts.md` boundaries. You need this for the next step: a request that
falls inside an open folder's scope belongs to that folder, not to a new one or
to "just do it" — changing files an open record makes claims about desyncs that
record from the tree. Route it back instead.

### 2. Offer the choice

Unless the user already named a unit, present the four options once — describing
what happens **to this request** under each, not what the units are called — and
mark your recommendation with its reason. The four options and the presentation
rules are in `core-rules.md` §2.

- The user picking something else is the end of it. Follow their choice; do not
  re-pitch.
- "Just do it" means no folder and no record. Nothing is written, including the
  fact that they chose it.
- If the user cannot choose, create an `inbox` folder and use
  `gathering-context` to narrow it, then `move` into the chosen unit.

### 3. Create the folder

Only after the unit is decided (core rule 6). Choose
`yyyy-MM-dd-<lowercase-kebab-slug>` with the actual current date.

```bash
python3 <plugin-root>/scripts/as-usual-record.py init \
  --dir <project-root>/.as-usual/<unit>/yyyy-MM-dd-<slug> \
  --unit <topic|direct-work|issue|inbox> \
  --request "<the user's request, verbatim>" \
  --actor claude
```

Use `--actor codex` on Codex. Then tell the user the folder path in one line so
they can correct the slug early.

### 4. Hand off

Invoke the owner skill for the unit: `run-topic`, `run-direct-work`, or
`run-issue`. It owns everything from there.

If the user asked for autopilot, confirm in one line where the run will stop,
record it with `--kind decision --data autopilot=on`, and tell the owner skill it
is on. When `autopilot:<phase>` names a phase this unit does not use, ask rather
than picking the nearest one.

## Resuming

### 1. Find the work folder

- **Path given**: if it contains `contexts.md` and `audit.jsonl`, use it. If it
  is a file or nested folder inside one, walk upward. If it is a project root or
  a unit collection directory, list recent candidates and ask which.
- **No path**: scan `.as-usual/inbox|topic|direct-work|issue/`. List up to three
  recent candidates across all units with their unit, slug, next action, and how
  long ago their last event was. Mark an `open` unit whose last event is older
  than the units around it as stale and worth confirming before resuming — an
  abandoned folder keeps its `nextAction` forever, so the most prominent thing
  the list offers can be an invitation to start work that already shipped
  somewhere else. Then ask which to resume. If nothing is there, say so.
- **A folder with artifacts and no `audit.jsonl`** is not a resume candidate and
  not nothing: it is work that went past the helper, so no gate ever saw it and
  no link can point at it. Report it while listing candidates. `init` on that
  folder adopts it.
- **Stale path** (the folder moved units): scan `.as-usual/` for the slug rather
  than failing. `move` can rename the slug as well as the unit, so when the slug
  finds nothing, fall back to the date in the path and then to the initial
  request text recorded in each candidate's `contexts.md`. List what you found
  and ask rather than guessing between two plausible folders.
- A folder holding `topic.md`, `journal.jsonl`, `problem.md`, or `question-c*.md`
  is a pre-v2 record. It is not a resume target. Say so and offer to start fresh
  work, reading the old files as input.

### 2. Read state

```bash
python3 <plugin-root>/scripts/as-usual-record.py status --dir <work-dir> --json
```

Then read `contexts.md`, and whichever of `requirements.md`, `plan.md`,
`review.md`, `conclusion.md` the derived next action needs. Read from disk, not
from memory of a previous session.

A resume starts manual. An `autopilot=on` in the record is what a previous session
was told, not permission for this one.

### 3. Verify before trusting

**Anything another session recorded is a claim until you check it.** When the
record says work was done, inspect `git status --short` and the relevant diffs
yourself before continuing or reporting it as complete. If work is claimed but
absent, or present but unrecorded, say which and fix the record only for what you
personally verified.

### 4. Hand off

Invoke the owner skill for the folder's unit. Let it route on the derived phase.
If the derived state is `finalized` or `cancelled`, the work is closed — offer to
start a new unit rather than reopening it.

## Stop Conditions

Stop and tell the user what you need when:

- The unit choice is waiting on them.
- The resume candidate is ambiguous.
- A work folder is closed and they asked to continue it.
- Only a pre-v2 record exists.
- An autopilot instruction is there but where it should stop is not clear.

## Anti-Patterns

- Classifying and starting work in the same breath, without offering the choice.
- Creating a folder before the unit is decided.
- Recording anything when the user chose "just do it".
- Turning autopilot on yourself because the request looked self-contained.
- Reporting another session's work as complete without checking diffs yourself.
- Running an owner skill's pipeline here instead of handing off.
