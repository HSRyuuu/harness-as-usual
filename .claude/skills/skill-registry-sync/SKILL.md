---
name: skill-registry-sync
description: Use when project-local AsUsual maintainer skills may be out of sync across .agents/skills and .claude/skills, or after creating, deleting, renaming, or editing maintainer skills.
---

# Skill Registry Sync

## Purpose

Keep AsUsual maintainer-only skills synchronized between the Codex-facing `.agents/skills/` tree and the Claude-facing `.claude/skills/` tree.

This is a maintainer skill. Do not move it into public plugin `skills/`, and do not register it as a verification skill.

## When To Use

- After creating, deleting, renaming, or editing `.agents/skills/**`
- After creating, deleting, renaming, or editing `.claude/skills/**`
- Before committing project-local maintainer skill changes
- When `manage-skills`, `verify-implementation`, or `AGENTS.md` skill lists may be stale

## Related Files

| File Or Directory | Purpose |
| --- | --- |
| `.agents/skills/` | Codex-facing maintainer skill source tree |
| `.claude/skills/` | Claude-facing maintainer skill mirror tree |
| `.agents/skills/manage-skills/SKILL.md` | registered verification skill list |
| `.agents/skills/verify-implementation/SKILL.md` | aggregate verification skill list |
| `AGENTS.md` | project-local skill and verification registry |

## Workflow

### Step 1: Inspect Skill Trees

**Tool:** Bash

Run:

```bash
find .agents/skills .claude/skills -mindepth 2 -maxdepth 3 -type f | sort
comm -3 \
  <(find .agents/skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sed 's#^\.agents/skills/##' | sort) \
  <(find .claude/skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sed 's#^\.claude/skills/##' | sort)
```

PASS: every maintainer skill has the same relative `SKILL.md` path in both trees.

FAIL: a skill exists on only one side.

Fix: create or remove the matching skill folder on the other side based on the intended latest tree.

### Step 2: Choose The Latest Copy

For each relative file that exists in both trees but differs, choose the source copy using this order:

1. If only one side is modified relative to `HEAD`, use the modified side.
2. If both sides are modified and one has a newer filesystem mtime, use the newer side only when the diff clearly shows the same intended change.
3. If both sides are modified with different substantive changes, stop and ask the user which side is canonical.
4. If neither side is modified relative to `HEAD` but files differ, prefer `.agents/skills/` and record the reason.

Commands:

```bash
git status --short -- .agents/skills .claude/skills
for left in .agents/skills/*/SKILL.md; do
  rel="${left#.agents/skills/}"
  right=".claude/skills/$rel"
  test -f "$right" || continue
  cmp -s "$left" "$right" || printf 'DIFF: %s\n' "$rel"
done
```

### Step 3: Update The Stale Side

**Tool:** Bash

After choosing the source copy, update the other side from the latest copy. Preserve executable helper scripts.

For a single skill:

```bash
rsync -a --delete ".agents/skills/<skill-name>/" ".claude/skills/<skill-name>/"
```

or, if `.claude/skills/<skill-name>/` is newer:

```bash
rsync -a --delete ".claude/skills/<skill-name>/" ".agents/skills/<skill-name>/"
```

PASS: the stale skill folder now matches the chosen latest source.

FAIL: files still differ after sync.

Fix: inspect the diff and rerun sync from the correct source.

### Step 4: Verify Byte-For-Byte Sync

**Tool:** Bash

Run:

```bash
for left in .agents/skills/*; do
  test -d "$left" || continue
  name="${left##*/}"
  right=".claude/skills/$name"
  if [ ! -d "$right" ]; then
    echo "MISSING_CLAUDE_SKILL: $name"
    continue
  fi
  diff -qr "$left" "$right" || true
done
```

PASS: no missing skills and no `diff -qr` output.

FAIL: any missing or differing file remains.

Fix: repeat Step 2 and Step 3 for each differing skill.

### Step 5: Update Registries

When a maintainer skill is created, deleted, or renamed, update:

- `AGENTS.md` `WHERE TO LOOK`, `CODE MAP`, or project-local verification sections when relevant.
- `.agents/skills/manage-skills/SKILL.md` only for registered verification skills.
- `.agents/skills/verify-implementation/SKILL.md` only for registered verification skills.

After registry edits, rerun this skill so `.claude/skills/**` mirrors `.agents/skills/**`.

## Output Format

```markdown
## skill-registry-sync Report

| Check | Status | Evidence |
| --- | --- | --- |
| Skill tree shape | PASS/FAIL | ... |
| Latest copy chosen | PASS/FAIL | ... |
| Sync applied | PASS/FAIL | ... |
| Byte-for-byte sync | PASS/FAIL | ... |
| Registries | PASS/FAIL | ... |

### Synced Skills

- `<skill-name>`: `.agents -> .claude` or `.claude -> .agents`
```

## Exceptions

1. Public runtime skills under `skills/**` are not mirrored by this skill.
2. Plugin manifests and marketplace JSON files are not mirrored by this skill.
3. If both sides changed differently and the correct source is unclear, stop for user confirmation instead of guessing.
