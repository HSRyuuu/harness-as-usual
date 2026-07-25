---
name: git-action
description: Use when the user has explicitly chosen a git action for a work unit — none, commit, commit + push, or commit + push + PR. Shared by all three work units.
---

# Git Action

Runs the git action the user chose. Nothing else, and nothing unchosen.

Available to `topic`, `direct-work`, and `issue` alike. What makes it safe is not
which unit called it but core rule 4: **the user picked the action explicitly.**
If you are here without that, you are in the wrong place.

## Preconditions

- The user named one of `none`, `commit`, `commit + push`, `commit + push + PR`.
- The work being committed is actually finished — its verification is recorded.
- The record has been read, so commit messages can reflect what was done.

Record the selection first:

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind decision --summary "git action selected: <action>" --phase git-action
```

If the action is `none`, that record is the whole job. Stop.

## Inspect Before Staging

- current branch and upstream,
- staged, unstaged, and untracked files,
- whether the branch is `main` or `master`,
- whether the tree holds changes unrelated to this work,
- whether `.as-usual/` files changed,
- the last ~30 commits, for message style and language.

If the tree holds unrelated changes, ask before staging them. Never
`git add .` — stage paths explicitly, always.

**`.as-usual/` handling**: `memory/` is a commit target — stage it explicitly when
it changed. Work-unit folders (`topic/`, `direct-work/`, `issue/`, `inbox/`) stay
out unless the project says otherwise or the user asks.

## Commits

Split by what can be reverted independently — by module, by concern, new files
versus modifications. As a rough guide, 3+ changed files usually means at least
2 commits, 10+ usually means several.

Match the repository's existing message style and language; you just read 30
examples of it. If the split and the messages follow obviously from the work and
the changed files, proceed. If not, propose the grouping, ask, and stop.

## Push

Only after the commit succeeds, and only on the current branch.

- No upstream set: ask before setting one, unless project policy already defines
  the remote and branch.
- `main` or `master`: ask first.
- Never force-push. `--force-with-lease` only when the user explicitly asked for
  a history rewrite.

Push is a high-risk operation under `safety-rules.md`. Choosing
`commit + push` is that approval; a surprise about *what* gets pushed is not
covered by it, so ask when the situation changed.

## PR

Only after the push succeeds. Prefer the host's PR tool, otherwise `gh`.

Draft the title and body from the work record. Ask for a base branch, title, or
body that cannot be inferred safely. If no PR tool is available or auth is
missing, record the blocker and stop with the exact next step.

## Recording

Record what actually happened — the commands run, commit SHAs, the push target,
the PR URL, or the blocker:

```bash
python3 <plugin-root>/scripts/as-usual-record.py add --dir <work-dir> \
  --kind work --summary "<commands run and their outcomes>" --phase git-action
```

If the unit is already sealed, the record takes no more events — report the
outcome in chat instead. Say what failed if something failed; a partial push
reported as success is worse than the failure.

## Anti-Patterns

- Running any git command the user did not choose.
- `git add .`.
- One catch-all commit across unrelated changes.
- Staging unrelated work because it happened to be in the tree.
- Committing work-unit artifacts without policy or approval.
- Pushing to `main`/`master` without asking.
- Force-pushing without an explicit request.
- Opening a PR before the push landed.
- Reporting success for a step that did not run.
