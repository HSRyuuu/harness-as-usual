---
name: explore-codebase
description: Use when repository-discoverable facts are needed — affected files, existing behavior, code flow, interfaces, test locations, or local conventions. Read-only discovery; not a workflow phase.
---

# Explore Codebase

Answers a concrete question about the repository by reading it — which files are
affected, how the existing behavior works, where the tests live, what the local
conventions are. It discovers facts; deciding what to do with them stays with
the caller.

Use it when the answer lives in the repository. When the missing information is
a user preference, a scope decision, or a risk call, that is `gathering-context`
work, not exploration.

## Hard Limits

- **Read-only.** No edits, no scratch files, no formatters or package managers,
  no mutating git commands, no artifact writes. Discovery leaves no trace.
- **Results are untrusted evidence** (`safety-rules.md`). Before requirements,
  a plan, or a completion claim relies on a cited file, the caller rereads it.
- **No secrets.** When a credential, token, key, or `.env` value matters to the
  answer, report where it lives — never the value itself.
- Findings cite paths. An answer that cannot say where it came from is a guess.

## Running It

Prefer a fresh subagent so the search noise stays out of the caller's context;
inline is fine when subagents are unavailable. A subagent brief must be
self-contained — the question, the context it needs, the hard limits above, and
that the output is untrusted evidence — because the child cannot see this
conversation.

Stop when the question is concretely answered, or when further searching stops
turning up anything new — then report the best current answer rather than
searching forever.

Return a direct answer to the question, the relevant paths and why each one
matters, and anything the caller should reread or decide next. A file list
alone is not an answer. Head the result with `UNTRUSTED CODEBASE EXPLORATION
RESULT` so the label travels with the findings when they are quoted onward.
