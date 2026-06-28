---
name: git-action
description: Use when an AsUsual topic is finalized and the user chooses none, commit, commit plus push, or commit plus push plus PR.
---

# Git Action

This skill performs the user-selected git action after an AsUsual topic is finalized. It is separate from `finalize`: finalization closes the topic record, while this skill handles the chosen repository action.

Use it only after `using-as-usual` has completed activation and first reads, `finalize` has recorded topic finalization, and the user has explicitly selected a git action.

## Responsibility Boundary

| Skill | Responsibility |
| --- | --- |
| `finalize` | Close the topic record and ask which git action to run |
| `git-action` | Run the selected git action and record the outcome |

`git-action` does not implement new work, run execution review, rewrite topic history, release, deploy, or choose a git action for the user.

## Supported Actions

| Action | Meaning |
| --- | --- |
| `none` | Record that the user chose no git action and stop. |
| `commit` | Create one or more atomic commits for the finalized work. |
| `commit + push` | Commit, then push the current branch. |
| `commit + push + PR` | Commit, push, then create a PR when the host/project tools support it. |

## Preconditions

Before running a git action, confirm:

- The Git Action rules in `core-workflow.md` have been checked.
- `topic.md`, `audit.jsonl`, `requirements.md`, and `plan.md` have been read from disk.
- Derived status or `audit.jsonl` shows the topic is finalized.
- The user selected one supported action in the current turn or the selected action is already recorded in `audit.jsonl`.
- A git repository is available.

If the topic is not finalized, return to `finalize`. If the requested action is ambiguous, ask the user to choose one supported action and stop.

## Inputs

Read and use these sources in this order:

1. `topic.md`
2. `audit.jsonl`
3. Derived status from `scripts/topic-log.py status --json`, when available
4. `requirements.md`
5. `plan.md`
6. `git status --short --branch`
7. `git log -30 --oneline`
8. `git log -30 --pretty=format:%s`
9. Current diff and changed-file list

## Workflow

### Step 1: Record Selection

Record the selected git action with:

```bash
python3 scripts/topic-log.py select-git-action \
  --topic-dir <topic-dir> \
  --action <none|commit|commit + push|commit + push + PR>
```

This appends typed audit metadata for the selection.

If the action is `none`:

1. Record the `none` selection through `select-git-action`.
2. Stop.

### Step 2: Inspect Repository State

Check:

- current branch and upstream,
- staged, unstaged, and untracked files,
- whether the branch is `main` or `master`,
- whether the working tree contains unrelated changes,
- whether `.as-usual/` artifacts are changed,
- recent commit language and style from the last 30 commits.

Do not use broad `git add .`.

If changes appear unrelated to the finalized topic, ask the user before staging them. If `.as-usual/` artifacts are changed, include them only when project policy or the user explicitly says to commit them.

### Step 3: Plan Atomic Commits

Use git-master commit discipline:

- 3+ changed files require considering at least 2 commits.
- 5+ changed files require considering at least 3 commits.
- 10+ changed files require considering at least 5 commits.
- Split by directory/module, component type, independent revertability, concern, and new-file versus modification when that produces clearer history.

If the split or commit message is obvious from `requirements.md`, `plan.md`, changed files, and recent commit style, proceed. If not, propose the commit grouping and messages, ask for confirmation, and stop.

Stage paths explicitly for each commit. Keep commit messages consistent with the detected recent style and language.

### Step 4: Push When Selected

For `commit + push` and `commit + push + PR`:

1. Push only after commit succeeds.
2. Use the current branch.
3. If there is no upstream, ask before setting upstream unless the host/project policy clearly defines the remote and branch.
4. Do not force-push. Use `--force-with-lease` only if the user explicitly requests a history rewrite.
5. Ask before pushing directly to `main` or `master`.

Record the push command and outcome in `audit.jsonl`.

### Step 5: Create PR When Selected

For `commit + push + PR`:

1. Create a PR only after push succeeds.
2. Prefer the host PR tool when available; otherwise use the project-standard CLI such as `gh`.
3. Use the finalized topic record to draft the PR title and body.
4. Ask for missing title/body/base-branch information when it cannot be inferred safely.
5. If no PR tool is available or authentication is missing, record the blocker and stop with the exact next action.

Record the PR URL or blocker in `audit.jsonl`.

## Topic Log And Audit

Use `scripts/topic-log.py` from the plugin root for every audit update, including commit splits, SHAs, push results, and PR URLs. Prefer `select-git-action` for the initial selection. Do not hand-edit `audit.jsonl`; if the helper cannot express the update, stop and report the missing helper capability.

Record:

- selected action,
- changed files considered,
- commit grouping,
- commit message style source,
- commands run and outcomes,
- commit SHAs,
- push remote/branch,
- PR URL or blocker,
- remaining issues.

## Anti-Patterns

- Running without an explicit selected action.
- Creating a single catch-all commit for unrelated changes.
- Using `git add .`.
- Staging unrelated work because it is present in the working tree.
- Committing `.as-usual/` artifacts without project policy or user approval.
- Pushing `main` or `master` without explicit user approval.
- Force-pushing without explicit user approval.
- Creating a PR before push succeeds.
- Releasing or deploying as part of a git action.
