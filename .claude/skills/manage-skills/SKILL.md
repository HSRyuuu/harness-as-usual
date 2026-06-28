---
name: manage-skills
description: Analyzes session changes to detect missing verification skill coverage. Dynamically discovers existing skills, creates new skills or updates existing skills, and maintains AGENTS.md.
disable-model-invocation: true
argument-hint: "[optional: specific skill name or area to focus on]"
---

# Session-Based Skill Maintenance

## Purpose

Analyze changes made in the current session to detect and fix drift in verification skills:

1. **Coverage gaps** - changed files that are not referenced by any verify skill
2. **Invalid references** - skills that reference deleted or moved files
3. **Missing checks** - new patterns or rules that existing checks do not cover
4. **Stale values** - configuration values or detection commands that no longer match

## When To Run

- After implementing a feature that introduces a new pattern or rule
- When modifying an existing verify skill and checking consistency
- Before a PR, to confirm verify skills cover the changed areas
- When verification misses an issue you expected it to catch
- Periodically, to keep skills aligned with codebase changes

## Registered Verification Skills

Current verification skills registered for this project. Update this list when creating or deleting skills.

| Skill                  | Description                                                                  | Covered File Patterns                                                                                                  |
| ---------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| verify-runtime-surface | Verifies that runtime-facing surfaces do not contain maintainer/plugin-development guidance | `hooks/**`, `as-usual-rules/**`, public `skills/**`, `templates/**`, `README.md`, `docs/**`, `.agents/skills/**`, `AGENTS.md` |
| verify-as-usual-harness | Verifies runtime workflow, hook injection, and plugin manifest smoke tests   | `as-usual-rules/**`, `hooks/**`, `.claude-plugin/**`, `.codex-plugin/**`, `.agents/plugins/**`, `templates/**`, public `skills/**` |
| verify-runtime-workflow-consistency | Verifies runtime workflow rules, public runtime skills, requirements/plan templates, and reviewer prompt consistency | `as-usual-rules/**`, public `skills/**`, `templates/**`, `hooks/session-start`, `README.md`, `docs/**` |
| verify-project-identity | Verifies durable project identity and maintainer docs reflect broad workflow, artifact, and verification changes | `PROJECT_IDENTITY.md`, `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/ARCHITECTURE-WORKFLOW.md`, `as-usual-rules/**`, public `skills/**`, `templates/**`, `.agents/skills/**` |

`verify-as-usual-harness` is a registered verification skill responsible for harness contract smoke tests.

## Workflow

### Step 1: Analyze Session Changes

Collect all files changed in the current session:

```bash
# Uncommitted changes
git diff HEAD --name-only

# Commits on the current branch, when branched from main
git log --oneline main..HEAD 2>/dev/null

# All changes since branching from main
git diff main...HEAD --name-only 2>/dev/null
```

Combine the results into a deduplicated list. If an optional argument names a skill or area, filter to related files only.

**Display:** Group files by top-level directory, using the first one or two path segments:

```markdown
## Session Changes Detected

**N files changed in this session:**

| Directory      | Files                          |
| -------------- | ------------------------------ |
| src/components | `Button.tsx`, `Modal.tsx`      |
| src/server     | `router.ts`, `handler.ts`      |
| tests          | `api.test.ts`                  |
| (root)         | `package.json`, `.eslintrc.js` |
```

### Step 2: Map Changed Files To Registered Skills

Use the skills listed in the **Registered Verification Skills** section to build a file-to-skill map.

#### Sub-step 2a: Inspect Registered Skills

Read each skill name and covered file pattern from the **Registered Verification Skills** table.

If there are zero registered skills, jump to Step 4 (CREATE vs UPDATE decision). Treat every changed file as "UNCOVERED".

If one or more skills are registered, read each skill's `.agents/skills/verify-<name>/SKILL.md` and extract additional file path patterns from:

1. **Related Files** section - parse tables for file paths and glob patterns
2. **Workflow** section - extract file paths from grep/glob/read commands

#### Sub-step 2b: Match Changed Files To Skills

For each changed file collected in Step 1, compare it with registered skill patterns. A file matches a skill when:

- It matches the skill's covered file patterns
- It is inside a directory referenced by the skill
- It matches regex or string patterns used in the skill's detection commands

#### Sub-step 2c: Display Mapping

```markdown
### File -> Skill Mapping

| Skill      | Trigger Files (changed files)  | Action    |
| ---------- | ------------------------------ | --------- |
| verify-api | `router.ts`, `handler.ts`      | CHECK     |
| verify-ui  | `Button.tsx`                   | CHECK     |
| (no skill) | `package.json`, `.eslintrc.js` | UNCOVERED |
```

### Step 3: Analyze Coverage Gaps In Affected Skills

For each AFFECTED skill, meaning each skill with matched changed files, read the full SKILL.md and check:

1. **Missing file references** - Is a changed file related to this skill's domain but absent from Related Files?
2. **Stale detection commands** - Do the skill's grep/glob patterns still match the current file structure? Run sample commands to test them.
3. **New uncovered patterns** - Read changed files and identify new rules, settings, or patterns the skill does not check, including:
   - New type definitions, enum variants, or exported symbols
   - New registrations or configuration
   - New file naming or directory rules
4. **References to deleted files** - Do files listed in Related Files no longer exist in the codebase?
5. **Changed values** - Did an identifier, configuration key, or type name checked by the skill change in modified files?

Record each gap found:

```markdown
| Skill       | Gap Type     | Details                                                |
| ----------- | ------------ | ------------------------------------------------------ |
| verify-api  | Missing file | `src/server/newHandler.ts` is absent from Related Files |
| verify-ui   | New pattern  | A new component uses a rule that is not checked         |
| verify-test | Stale value  | Test runner pattern changed in the config file         |
```

### Step 4: Decide CREATE vs UPDATE

Apply this decision tree:

```text
For each uncovered file group:
    IF files belong to an existing skill domain:
        -> Decision: UPDATE existing skill (extend coverage)
    ELSE IF 3 or more related files share a common rule/pattern:
        -> Decision: CREATE new verify skill
    ELSE:
        -> Mark as "exempt" (no skill needed)
```

Present the result to the user:

```markdown
### Proposed Actions

**Decision: UPDATE existing skills** (N)

- `verify-api` - add 2 missing file references and update detection patterns
- `verify-test` - update detection command for new config pattern

**Decision: CREATE new skills** (M)

- New skill needed - cover <pattern description> (X uncovered files)

**No action needed:**

- `package.json` - configuration file, exempt
- `README.md` - documentation, exempt
```

Use `AskUserQuestion` to confirm:

- Which existing skills to update
- Whether to create proposed new skills
- Whether to skip everything

### Step 5: Update Existing Skills

For each skill the user approves for update, read its current SKILL.md and apply targeted edits:

**Rules:**

- **Add or update only** - never remove existing checks that still work
- Add new file paths to the Related Files table
- Add detection commands for patterns found in changed files
- Add workflow steps or sub-steps for uncovered rules
- Remove references to files confirmed deleted from the codebase
- Update changed concrete values such as identifiers, config keys, and type names

**Example - add a file to Related Files:**

```markdown
## Related Files

| File                       | Purpose                              |
| -------------------------- | ------------------------------------ |
| ... existing rows ...      |
| `src/server/newHandler.ts` | New request handler with validation  |
```

**Example - add a detection command:**

````markdown
### Step N: Verify New Pattern

**File:** `path/to/file.ts`

**Check:** Description of what to verify.

```bash
grep -n "pattern" path/to/file.ts
```

**Violation:** What the incorrect case looks like.
````

### Step 6: Create New Skills

**Important:** When creating a new skill, always confirm the skill name with the user.

For each skill to create:

1. **Explore** - read related changed files and deeply understand the pattern.

2. **Confirm skill name with the user** - use `AskUserQuestion`.

   Present the pattern/domain the skill will cover and ask the user to provide or confirm a name.

   **Naming rules:**
   - The name must start with `verify-`, for example `verify-auth`, `verify-api`, or `verify-caching`.
   - If the user provides a name without the `verify-` prefix, add it automatically and tell the user.
   - Use kebab-case, for example `verify-error-handling`, not `verify_error_handling`.

3. **Create** - create `.agents/skills/verify-<name>/SKILL.md` using this template:

```yaml
---
name: verify-<name>
description: <one-line description>. Use after <trigger condition>.
---
```

Required sections:

- **Purpose** - 2-5 numbered verification categories
- **When to Run** - 3-5 trigger conditions
- **Related Files** - table of real codebase paths verified with `ls`; placeholders are not allowed
- **Workflow** - check steps, each naming:
  - Tools to use (Grep, Glob, Read, Bash)
  - Exact file paths or patterns
  - PASS/FAIL criteria
  - How to fix failures
- **Output Format** - markdown table for results
- **Exceptions** - at least 2-3 realistic non-violation cases

4. **Update related skill files** - after creating a new skill, always update these three files:

   **4a. Update this file (`manage-skills/SKILL.md`):**
   - Add a row to the table in **Registered Verification Skills**.
   - When adding the first skill, remove any "no registered verification skills yet" text and HTML comments, replacing them with the table.
   - Format: `| verify-<name> | <description> | <covered file patterns> |`

   **4b. Update `verify-implementation/SKILL.md`:**
   - Add a row to the table in **Target Skills**.
   - When adding the first skill, remove any "no registered verification skills yet" text and HTML comments, replacing them with the table.
   - Format: `| <number> | verify-<name> | <description> |`

   **4c. Update `AGENTS.md`:**
   - If the project-level skill or verification section exists, add a row for the new skill.
   - Format: `| verify-<name> | <one-line description> |`

### Step 7: Verification

After all edits:

1. Reread every modified SKILL.md file.
2. Check markdown formatting, including unclosed code blocks and consistent table columns.
3. Check for broken file references. For every path in Related Files, verify the file exists:

```bash
ls <file-path> 2>/dev/null || echo "MISSING: <file-path>"
```

4. Dry-run one detection command from each updated skill to verify command syntax.
5. Confirm that the **Registered Verification Skills** table and **Target Skills** table stay synchronized.

### Step 8: Summary Report

Display the final report:

```markdown
## Session Skill Maintenance Report

### Changed Files Analyzed: N

### Updated Skills: X

- `verify-<name>`: added N new checks and updated Related Files
- `verify-<name>`: updated detection command for new pattern

### Created Skills: Y

- `verify-<name>`: covers <pattern>

### Related Files Updated:

- `manage-skills/SKILL.md`: updated registered verification skills table
- `verify-implementation/SKILL.md`: updated target skills table
- `AGENTS.md`: updated project-level verification skill list

### Unaffected Skills: Z

- (no relevant changes)

### Uncovered Changes (no applicable skill):

- `path/to/file` - exempt (<reason>)
```

---

## Quality Standards For Created Or Updated Skills

Every created or updated skill must include:

- **Real codebase file paths** verified with `ls`, not placeholders
- **Working detection commands** that use real grep/glob patterns matching current files
- **PASS/FAIL criteria** with clear success and failure conditions for each check
- **At least 2-3 realistic exceptions** explaining non-violations
- **Consistent format** matching existing skills, including frontmatter, section headers, and table structure

---

## Related Files

| File                                            | Purpose                                                   |
| ----------------------------------------------- | --------------------------------------------------------- |
| `.agents/skills/verify-implementation/SKILL.md` | Aggregate verification skill; manages the target skill list |
| `.agents/skills/manage-skills/SKILL.md`         | This file; manages the registered verification skill list |
| `AGENTS.md`                                     | Project instructions                                      |

## Exceptions

The following are **not problems**:

1. **Lock files and generated files** - `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Cargo.lock`, generated migration files, and build outputs do not need skill coverage.
2. **One-off configuration changes** - version bumps in `package.json`/`Cargo.toml` and minor linter/formatter config changes do not need new skills.
3. **Documentation files** - `README.md`, `CHANGELOG.md`, `LICENSE`, and similar files are not code patterns requiring verification.
4. **Test fixture files** - files under fixture directories such as `fixtures/`, `__fixtures__/`, or `test-data/` are not production code.
5. **Unaffected skills** - skills marked UNAFFECTED do not need review; in most sessions, most skills will fall into this category.
6. **AGENTS.md itself** - changes to AGENTS.md are documentation updates, not code patterns requiring verification.
7. **Vendored or third-party code** - files under `vendor/`, `node_modules/`, or copied library directories follow external rules.
8. **CI/CD configuration** - `.github/`, `.gitlab-ci.yml`, `Dockerfile`, and similar infrastructure files are not application patterns that need verification skills.
