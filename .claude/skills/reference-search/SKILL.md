---
name: reference-search
description: Use only when explicitly requested while developing the AsUsual plugin to search the private reference corpus for design questions, source locations, workflow/hook/skill/artifact differences, and AsUsual adoption decisions.
---

# Reference Search

## Purpose

When developing the AsUsual plugin, answer questions using evidence from the private local reference corpus.

Hardcoded reference root:

```text
/Users/happyhsryu/dev/opensources/ai-opensource-references
```

Treat the reference root's `index.md` and current directory structure as the source of truth for what references exist and how they should be read. Do not assume AsUsual must keep following any one reference project after its own runtime contract has diverged.

This skill is not for running an AsUsual runtime topic in a target project. Use it only when the user explicitly asks for reference search or reference-backed development research inside the AsUsual repository.

## Search Order

1. Set `REFERENCE_ROOT=/Users/happyhsryu/dev/opensources/ai-opensource-references`.
2. Read `$REFERENCE_ROOT/index.md` to understand the reference structure and default reading order.
3. Search the user's core keywords in `$REFERENCE_ROOT` with `rg`.
4. Read the summary file or reference subdirectory that matches the question type first:
   - Cross-reference comparison questions: `$REFERENCE_ROOT/as-usual-design-notes/comparison.md`
   - AsUsual design decisions: `$REFERENCE_ROOT/as-usual-design-notes/`
   - Current AsUsual source locations: `$REFERENCE_ROOT/as-usual-design-notes/source-map.md`
   - Reference-specific artifact, question, state, workflow, hook, prompt, skill analysis, or source map: the relevant `$REFERENCE_ROOT/<reference-name>/` directory
5. Read the relevant `$REFERENCE_ROOT/<reference-name>/source-map.md` when you need original source locations or exact implementation details.
6. Open original local source files from the relevant source-map only when the summaries are insufficient.

## Common Searches

```bash
REFERENCE_ROOT=/Users/happyhsryu/dev/opensources/ai-opensource-references
rg -n "question|Answer|state|audit|artifact" "$REFERENCE_ROOT"
rg -n "hook|SessionStart|activation|skill" "$REFERENCE_ROOT"
rg -n "spec|plan|execute|workflow" "$REFERENCE_ROOT"
rg -n "takeaway|recommend|avoid|decision|tradeoff" "$REFERENCE_ROOT"
```

## Answer Rules

- Identify which reference file or reference family supports each answer.
- State whether the evidence is from a local summary, original source, or an inference that combines them.
- Prefer file links with absolute paths and line numbers when possible.
- When comparing multiple references, name the references that were actually searched and compare their tradeoffs before recommending an AsUsual decision.
- When references make different choices, compare the difference and separately judge whether AsUsual should adopt, adapt, or avoid each pattern.
- If the user asks how to change AsUsual, separate `reference finding` from `proposed AsUsual decision`.
- Do not copy raw reference-analysis text into `as-usual-rules/core-workflow.md`, hook payloads, or runtime skills.
- Old paths in source-map files do not override current repository conventions. Recheck current files before proposing changes.

## When References Are Insufficient

If the local references are insufficient:

1. Say which files you searched and why they were insufficient.
2. Use the relevant `$REFERENCE_ROOT/<reference-name>/source-map.md` to identify original source paths to inspect.
3. If the original local source is unavailable or the user asks for current upstream status, use web search and label web-derived facts.
