---
name: verify-implementation
description: Runs project verify skills that match the changed surface and produces an aggregate verification report. Use after feature implementation, before a PR, or during code review.
disable-model-invocation: true
argument-hint: "[optional: specific verify skill name | all | full]"
---

# Implementation Verification

## Purpose

Run the verification skills relevant to the changed surface and produce aggregate verification:

- Run the checks defined in each selected skill's Workflow section.
- Use each skill's Exceptions section to avoid false positives.
- Suggest fixes for any issues found.
- Apply fixes after user approval and rerun relevant checks.

## When To Run

- After implementing a new feature
- Before creating a Pull Request
- During code review
- When auditing whether the codebase follows project rules
- When explicitly asked to run all project verification skills

## Target Skills

This is the registry of available verification skills. By default, run only the skills whose covered surfaces match the current session's changed files. Run every skill only when the user explicitly asks for full verification, before a PR/release, or when no reliable changed-file set is available. `/manage-skills` updates this list when verification skills are created or deleted.

| #   | Skill                  | Description                                                                  | Covered Surface |
| --- | ---------------------- | ---------------------------------------------------------------------------- | --------------- |
| 1   | verify-runtime-surface | Verifies that runtime-facing surfaces do not contain maintainer/plugin-development guidance | `hooks/**`, `as-usual-rules/**`, public `skills/**`, `templates/**`, `scripts/**`, public docs |
| 2   | verify-as-usual-harness | Verifies runtime workflow, hook injection, and plugin manifest smoke tests   | `as-usual-rules/**`, `hooks/**`, `.claude-plugin/**`, `.codex-plugin/**`, `.agents/plugins/**`, `templates/**`, public `skills/**`, `scripts/**` |
| 3   | verify-runtime-workflow-consistency | Verifies runtime workflow rules, public runtime skills, requirements/plan templates, and reviewer prompt consistency | `as-usual-rules/**`, public `skills/**`, `templates/**`, `scripts/**`, `hooks/session-start`, public docs |
| 4   | verify-project-identity | Verifies durable project identity and maintainer docs reflect broad workflow, artifact, and verification changes | `PROJECT_IDENTITY.md`, `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/ARCHITECTURE-WORKFLOW.md`, `as-usual-rules/**`, public `skills/**`, `templates/**`, `.agents/skills/**` |
| 5   | sandbox-e2e-test | Verifies sandbox E2E runner and report linter behavior | `.agents/skills/sandbox-e2e-test/**`, `docs/test/**` |

## Workflow

### Step 1: Introduction

Review the skills listed in the **Target Skills** section.

If an optional argument is provided:

- a specific skill name filters to that skill only
- `all` or `full` runs every registered verification skill

If no optional argument is provided, identify the files changed by the current task first. Prefer the files the agent edited in this request. Use git as supporting evidence:

```bash
git diff HEAD --name-only
git diff main...HEAD --name-only 2>/dev/null
```

Do not let unrelated pre-existing dirty files expand the selected verification set. If git output includes files that were already modified before the current task, list them as ambient changes and exclude them from default skill selection unless the user asks for full verification.

Select only skills whose **Covered Surface**, **Related Files**, or Workflow commands match the current task's changed files.

If there are no changed files, or the changed-file set cannot be trusted, run every registered skill and record that reason in the report.

If changed files exist but no registered skill matches them, report that no verification skill applies and end the workflow without running unrelated smoke tests.

**When there are zero registered skills:**

```markdown
## Implementation Verification

No verification skills are registered. Run `/manage-skills` to create project-appropriate verification skills.
```

End the workflow in this case.

**When one or more skills are registered:**

Display only the selected verification skills:

**When no skill is selected:**

```markdown
## Implementation Verification

No registered verification skill matches the changed files.

Changed files: <summary>
Skipped: no unrelated smoke tests were run.
```

End the workflow in this case.

```markdown
## Implementation Verification

Running the following verification skills:

| #   | Skill          | Description    |
| --- | -------------- | -------------- |
| 1   | verify-<name1> | <description1> |
| 2   | verify-<name2> | <description2> |

Selection reason: changed files matched <surface>, or full verification was requested.

Starting verification...
```

### Step 2: Sequential Execution

For each selected skill:

#### 2a. Read the Skill's SKILL.md

Read `.agents/skills/<skill-name>/SKILL.md` and parse these sections:

- **Workflow** - checks to run and detection commands
- **Exceptions** - patterns that should not be treated as violations
- **Related Files** - files covered by the checks

#### 2b. Run Checks

Run each check defined in the Workflow section in order:

1. Use the tools named in the check (Grep, Glob, Read, Bash) to detect patterns.
2. Compare detected results with the skill's PASS/FAIL criteria.
3. Exempt patterns covered by the Exceptions section.
4. For FAIL results, record:
   - File path and line number
   - Problem description
   - Recommended fix, including code examples when useful

#### 2c. Record Per-Skill Results

After each skill finishes, show progress:

```markdown
### verify-<name> Verification Complete

- Checks: N
- Passed: X
- Issues: Y
- Exemptions: Z

[Moving to next skill...]
```

### Step 3: Aggregate Report

After all selected skills finish, combine the results into one report:

```markdown
## Implementation Verification Report

### Summary

| Verify Skill   | Status          | Issue Count | Details    |
| -------------- | --------------- | ----------- | ---------- |
| verify-<name1> | PASS / X issues | N           | Details... |
| verify-<name2> | PASS / X issues | N           | Details... |

**Total issues found: X**
```

**When all checks pass:**

```markdown
All verification checks passed.

The implementation follows the selected project rules:

- verify-<name1>: <summary of what passed>
- verify-<name2>: <summary of what passed>

Ready for code review.
```

**When issues are found:**

List each issue with file path, problem description, and recommended fix:

```markdown
### Issues Found

| #   | Skill          | File                  | Problem             | Fix              |
| --- | -------------- | --------------------- | ------------------- | ---------------- |
| 1   | verify-<name1> | `path/to/file.ts:42`  | Problem description | Example fix code |
| 2   | verify-<name2> | `path/to/file.tsx:15` | Problem description | Example fix code |
```

### Step 4: Confirm User Action

If issues are found, use `AskUserQuestion` to confirm how to proceed:

```markdown
---

### Fix Options

**X issues were found. How should we proceed?**

1. **Fix all** - automatically apply all recommended fixes
2. **Fix individually** - review and apply each fix one by one
3. **Skip** - exit without changes
```

### Step 5: Apply Fixes

Apply fixes based on the user's choice.

**When "Fix all" is selected:**

Apply all fixes in order and show progress:

```markdown
## Applying Fixes...

- [1/X] verify-<name1>: `path/to/file.ts` fixed
- [2/X] verify-<name2>: `path/to/file.tsx` fixed

X fixes applied.
```

**When "Fix individually" is selected:**

Show each proposed fix and use `AskUserQuestion` to confirm whether to apply it.

### Step 6: Re-verify After Fixes

If fixes were applied, rerun only the skills that had issues and compare Before/After:

```markdown
## Re-verification After Fixes

Rerunning skills that had issues...

| Verify Skill   | Before   | After |
| -------------- | -------- | ----- |
| verify-<name1> | X issues | PASS  |
| verify-<name2> | Y issues | PASS  |

All verification checks passed.
```

**When issues remain:**

```markdown
### Remaining Issues

| #   | Skill         | File                 | Problem                            |
| --- | ------------- | -------------------- | ---------------------------------- |
| 1   | verify-<name> | `path/to/file.ts:42` | Automatic fix unavailable; manual review needed |

After resolving them manually, run `/verify-implementation` again.
```

---

## Exceptions

The following are **not problems**:

1. **Projects with no registered skills** - show an informational message and exit instead of treating it as an error.
2. **Skill-specific exceptions** - patterns defined in each verify skill's Exceptions section are not reported as issues.
3. **verify-implementation itself** - do not include this skill in its own target skill list.
4. **manage-skills** - this skill manages the verification registry and is not a target verification skill.
5. **Explicitly registered smoke skills** - include a harness smoke skill only when its covered surface changed, full verification was requested, the changed-file set is unavailable, or the run is a final PR/release verification.

## Related Files

| File                                    | Purpose                                                  |
| --------------------------------------- | -------------------------------------------------------- |
| `.agents/skills/manage-skills/SKILL.md` | Skill maintenance; manages this file's target skill list |
| `AGENTS.md`                             | Project instructions                                     |
