#!/usr/bin/env bash
# AsUsual local plugin installer for Claude Code and Codex.
#
# Usage:
#   bash docs/INSTALL.sh
#
# Run it from anywhere inside a clone of the AsUsual repository, or set
# AS_USUAL_REPO to the repository root before running. Hosts whose CLI
# (claude / codex) is not installed are skipped automatically.
#
# Reference: docs/INSTALL.md (manual steps), docs/UNINSTALL.md (removal).
set -euo pipefail

PLUGIN_ID="as-usual@as-usual-local"
MARKETPLACE="as-usual-local"

# Resolve the repository root: prefer AS_USUAL_REPO, else the parent of this script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AS_USUAL_REPO="${AS_USUAL_REPO:-$(cd "$SCRIPT_DIR/.." && pwd)}"

cd "$AS_USUAL_REPO"
echo "==> AsUsual repository: $AS_USUAL_REPO"

# 1. Validate manifests and make hooks executable.
echo "==> Validating plugin manifests"
manifests=(
  .claude-plugin/plugin.json .claude-plugin/marketplace.json
  .codex-plugin/plugin.json .agents/plugins/marketplace.json
  hooks/hooks.json hooks/hooks-codex.json
)
if command -v jq >/dev/null 2>&1; then
  jq empty "${manifests[@]}"
else
  for f in "${manifests[@]}"; do python3 -m json.tool "$f" >/dev/null; done
fi
chmod +x hooks/session-start hooks/run-hook.cmd

# 2. Install for Claude Code (marketplace source is the repo root).
if command -v claude >/dev/null 2>&1; then
  echo "==> Installing for Claude Code"
  claude plugin marketplace add "$AS_USUAL_REPO" || true
  claude plugin install "$PLUGIN_ID"
  claude plugin enable "$PLUGIN_ID"
  claude plugin details "$PLUGIN_ID" || true
else
  echo "==> Skipping Claude Code (claude CLI not found)"
fi

# 3. Install for Codex (marketplace source is the plugins/as-usual symlink).
if command -v codex >/dev/null 2>&1; then
  echo "==> Installing for Codex"
  mkdir -p plugins
  ln -sfn .. plugins/as-usual
  test "$(readlink plugins/as-usual)" = ".."
  codex plugin marketplace add "$AS_USUAL_REPO" --json || true
  codex plugin add "$PLUGIN_ID" --json
  codex plugin list | grep -E 'as-usual' || true
else
  echo "==> Skipping Codex (codex CLI not found)"
fi

echo "==> Done. Restart your Claude Code / Codex session to load AsUsual ($MARKETPLACE)."
