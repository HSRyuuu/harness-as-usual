#!/usr/bin/env bash
# Toggle the local AsUsual plugin for Claude Code and Codex.

set -euo pipefail

PLUGIN_ID="as-usual@harness-as-usual"
MARKETPLACE_NAME="harness-as-usual"
CODEX_CACHE_ROOT="${HOME}/.codex/plugins/cache/harness-as-usual/as-usual"

ACTION=""
SCOPE="all"
REPO=""

usage() {
  cat <<'USAGE'
Usage:
  as-usual-toggle.sh on|off|reload|status [--all|--codex|--claude] [--repo PATH]

Examples:
  .agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh status
  .agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh off --all
  .agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh on --codex
  .agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh reload --codex

Notes:
  - "off" disables the local plugin for future sessions.
  - "on" enables the plugin and reloads Codex's installed cache snapshot.
  - "reload" refreshes installed plugin state without first disabling Claude settings.
  - Existing Claude Code or Codex sessions keep already-loaded hook context.
  - Run "on" from the AsUsual repository to re-enable the local plugin.
USAGE
}

info() {
  printf '[INFO] %s\n' "$*"
}

warn() {
  printf '[WARN] %s\n' "$*" >&2
}

fail() {
  printf '[ERROR] %s\n' "$*" >&2
  exit 1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    on|off|reload|status)
      [ -z "$ACTION" ] || fail "action is already set to $ACTION"
      ACTION="$1"
      ;;
    --all)
      SCOPE="all"
      ;;
    --codex)
      SCOPE="codex"
      ;;
    --claude)
      SCOPE="claude"
      ;;
    --repo)
      shift || fail "--repo requires a path"
      REPO="$1"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      fail "unknown argument: $1"
      ;;
  esac
  shift
done

[ -n "$ACTION" ] || {
  usage >&2
  fail "missing action: on, off, reload, or status"
}

resolve_repo() {
  if [ -n "$REPO" ]; then
    (cd "$REPO" 2>/dev/null && pwd) || fail "cannot access repo: $REPO"
    return
  fi

  if command -v git >/dev/null 2>&1; then
    git rev-parse --show-toplevel 2>/dev/null && return
  fi

  pwd
}

repo_root="$(resolve_repo)"
claude_settings="${HOME}/.claude/settings.json"

validate_repo() {
  [ -f "$repo_root/.codex-plugin/plugin.json" ] || fail "missing .codex-plugin/plugin.json in $repo_root"
  [ -f "$repo_root/.agents/plugins/marketplace.json" ] || fail "missing .agents/plugins/marketplace.json in $repo_root"
  [ -f "$repo_root/.claude-plugin/plugin.json" ] || fail "missing .claude-plugin/plugin.json in $repo_root"
  [ -f "$repo_root/.claude-plugin/marketplace.json" ] || fail "missing .claude-plugin/marketplace.json in $repo_root"
  [ -f "$repo_root/hooks/hooks-codex.json" ] || fail "missing hooks/hooks-codex.json in $repo_root"
  [ -f "$repo_root/hooks/hooks.json" ] || fail "missing hooks/hooks.json in $repo_root"
}

validate_json_file() {
  local file="$1"
  if command -v jq >/dev/null 2>&1; then
    jq empty "$file" >/dev/null
  else
    python3 -m json.tool "$file" >/dev/null
  fi
}

prepare_repo_for_codex() {
  validate_repo
  validate_json_file "$repo_root/.codex-plugin/plugin.json"
  validate_json_file "$repo_root/.agents/plugins/marketplace.json"
  validate_json_file "$repo_root/hooks/hooks-codex.json"

  mkdir -p "$repo_root/plugins"
  ln -sfn .. "$repo_root/plugins/as-usual"
  chmod +x "$repo_root/hooks/session-start" "$repo_root/hooks/run-hook.cmd"
}

codex_status() {
  info "Codex status"
  if ! command -v codex >/dev/null 2>&1; then
    warn "codex CLI not found"
    return
  fi

  codex plugin marketplace list 2>/dev/null | grep -E 'as-usual|harness-as-usual' || true
  codex plugin list 2>/dev/null | grep -E 'as-usual|harness-as-usual' || true

  if [ -f "${HOME}/.codex/config.toml" ]; then
    grep -E 'harness-as-usual|as-usual' "${HOME}/.codex/config.toml" || true
  fi
}

prune_codex_cache() {
  if [ -d "$CODEX_CACHE_ROOT" ]; then
    info "Removing Codex cache snapshots under $CODEX_CACHE_ROOT"
    rm -rf "$CODEX_CACHE_ROOT"
  fi
}

codex_reload() {
  if ! command -v codex >/dev/null 2>&1; then
    warn "codex CLI not found; skipping Codex"
    return
  fi

  prepare_repo_for_codex
  info "Registering Codex marketplace from $repo_root"
  codex plugin marketplace add "$repo_root" --json

  info "Refreshing Codex plugin snapshot for $PLUGIN_ID"
  codex plugin remove "$PLUGIN_ID" --json >/dev/null 2>&1 || true
  prune_codex_cache
  codex plugin add "$PLUGIN_ID" --json
}

codex_on() {
  codex_reload
}

codex_off() {
  if ! command -v codex >/dev/null 2>&1; then
    warn "codex CLI not found; skipping Codex"
    return
  fi

  info "Removing Codex plugin $PLUGIN_ID"
  codex plugin remove "$PLUGIN_ID" --json >/dev/null 2>&1 || warn "Codex plugin was not installed or could not be removed"
}

claude_status() {
  info "Claude Code status"
  if [ -f "$claude_settings" ] && command -v node >/dev/null 2>&1; then
    SETTINGS_PATH="$claude_settings" PLUGIN_ID="$PLUGIN_ID" MARKETPLACE_NAME="$MARKETPLACE_NAME" node <<'NODE'
const fs = require('fs');
const settingsPath = process.env.SETTINGS_PATH;
const pluginId = process.env.PLUGIN_ID;
const marketplaceName = process.env.MARKETPLACE_NAME;
const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
const enabled = settings.enabledPlugins && Object.prototype.hasOwnProperty.call(settings.enabledPlugins, pluginId)
  ? settings.enabledPlugins[pluginId]
  : undefined;
const marketplace = settings.extraKnownMarketplaces && settings.extraKnownMarketplaces[marketplaceName];
console.log(`settings.enabledPlugins["${pluginId}"] = ${JSON.stringify(enabled)}`);
console.log(`settings.extraKnownMarketplaces["${marketplaceName}"] = ${marketplace ? JSON.stringify(marketplace.source || marketplace) : 'undefined'}`);
NODE
  else
    warn "Claude settings not readable with node"
  fi

  if command -v claude >/dev/null 2>&1; then
    claude plugin marketplace list 2>/dev/null | grep -E 'as-usual|harness-as-usual' || true
    claude plugin list 2>/dev/null | grep -E 'as-usual|harness-as-usual' || true
  else
    warn "claude CLI not found"
  fi
}

set_claude_enabled() {
  local enabled="$1"

  if ! command -v node >/dev/null 2>&1; then
    warn "node not found; skipping Claude settings update"
    return
  fi

  validate_repo
  validate_json_file "$repo_root/.claude-plugin/plugin.json"
  validate_json_file "$repo_root/.claude-plugin/marketplace.json"
  validate_json_file "$repo_root/hooks/hooks.json"
  chmod +x "$repo_root/hooks/session-start" "$repo_root/hooks/run-hook.cmd"

  mkdir -p "${HOME}/.claude"
  if [ ! -f "$claude_settings" ]; then
    printf '{}\n' > "$claude_settings"
  fi

  local backup="${claude_settings}.as-usual-toggle.$(date +%Y%m%d%H%M%S).bak"
  cp "$claude_settings" "$backup"
  info "Backed up Claude settings to $backup"

  SETTINGS_PATH="$claude_settings" REPO_ROOT="$repo_root" PLUGIN_ID="$PLUGIN_ID" MARKETPLACE_NAME="$MARKETPLACE_NAME" ENABLED="$enabled" node <<'NODE'
const fs = require('fs');
const settingsPath = process.env.SETTINGS_PATH;
const repo = process.env.REPO_ROOT;
const pluginId = process.env.PLUGIN_ID;
const marketplaceName = process.env.MARKETPLACE_NAME;
const enabled = process.env.ENABLED === 'true';
const settings = fs.existsSync(settingsPath)
  ? JSON.parse(fs.readFileSync(settingsPath, 'utf8'))
  : {};
settings.extraKnownMarketplaces = settings.extraKnownMarketplaces && typeof settings.extraKnownMarketplaces === 'object'
  ? settings.extraKnownMarketplaces
  : {};
settings.extraKnownMarketplaces[marketplaceName] = {
  source: {
    source: 'directory',
    path: repo
  }
};
settings.enabledPlugins = settings.enabledPlugins && typeof settings.enabledPlugins === 'object'
  ? settings.enabledPlugins
  : {};
settings.enabledPlugins[pluginId] = enabled;
fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + '\n');
NODE

  validate_json_file "$claude_settings"
  info "Set Claude Code $PLUGIN_ID enabled=$enabled"
}

claude_reload() {
  info "Claude Code loads this local plugin from the repository path; ensuring it is enabled"
  set_claude_enabled true
}

run_for_scope() {
  local target="$1"
  case "$ACTION:$target" in
    status:codex) codex_status ;;
    status:claude) claude_status ;;
    on:codex) codex_on ;;
    on:claude) set_claude_enabled true ;;
    reload:codex) codex_reload ;;
    reload:claude) claude_reload ;;
    off:codex) codex_off ;;
    off:claude) set_claude_enabled false ;;
    *) fail "unsupported action/scope: $ACTION:$target" ;;
  esac
}

info "Repository: $repo_root"

case "$SCOPE" in
  all)
    run_for_scope codex
    run_for_scope claude
    ;;
  codex|claude)
    run_for_scope "$SCOPE"
    ;;
  *)
    fail "invalid scope: $SCOPE"
    ;;
esac

if [ "$ACTION" = "on" ] || [ "$ACTION" = "off" ] || [ "$ACTION" = "reload" ]; then
  info "Start a fresh Claude Code or Codex session for plugin hook changes to take effect."
fi
