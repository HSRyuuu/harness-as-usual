#!/usr/bin/env bash
# Run a real AsUsual E2E test inside the hardcoded Java/React sandbox.

set -u -o pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
as_usual_repo="$(cd "$script_dir/../../../.." && pwd)"
expected_sandbox_repo="/Users/happyhsryu/dev/personal/as-usual-test-project"
sandbox_repo="$expected_sandbox_repo"

host="codex"
claude_model="sonnet"
claude_setting_sources="project"
claude_plugin_dir="$as_usual_repo"
claude_preflight="true"
scenario="scenario_1_priority"
test_name=""
reset_sandbox="true"
allow_dirty_baseline="false"
preclean_sandbox="true"
sandbox_precleaned="false"
agent_failed="false"
topic_dir=""
idle_timeout_seconds=90
idle_timeout_user_set="false"
max_step_timeout_seconds=900
progress_heartbeat_seconds=30
pre_run_topic_archived="false"

usage() {
  cat <<'USAGE'
Usage:
  run-sandbox-e2e.sh [--scenario NAME] [--test-name NAME] [--host codex|claude] [--claude-model MODEL] [--claude-setting-sources SOURCES] [--claude-plugin-dir PATH] [--skip-claude-preflight] [--no-reset] [--no-preclean] [--allow-dirty-baseline] [--idle-timeout SECONDS] [--max-step-timeout SECONDS] [--progress-interval SECONDS]

Defaults:
  --scenario scenario_1_priority
  --test-name <scenario>
  --host codex
  --claude-model sonnet
  --claude-setting-sources project
  --claude-plugin-dir <as-usual repo>
  Claude preflight is enabled by default; pass --skip-claude-preflight to disable it.
  Precleaning the hardcoded sandbox is enabled by default; pass --no-preclean to preserve it.
  --idle-timeout 90
  --max-step-timeout 900
  --progress-interval 30

Notes:
  - Scenarios:
    scenario_1_priority           Existing task priority E2E baseline.
    scenario_2_complex_workflow   More complex scheduling/status workflow.
    scenario_3_self_improvement   Self-improvement memory candidate/finalize path.
  - The sandbox path is intentionally hardcoded:
    /Users/happyhsryu/dev/personal/as-usual-test-project
  - Existing sandbox changes are snapshotted into the report directory before precleaning.
  - Existing sandbox .as-usual artifacts are archived into the report directory unless --no-reset is used.
  - --allow-dirty-baseline disables precleaning and preserves the current sandbox diff for analysis.
  - --step-timeout is accepted as a deprecated alias for --max-step-timeout.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --scenario)
      shift || {
        usage >&2
        exit 2
      }
      scenario="$1"
      ;;
    --test-name)
      shift || {
        usage >&2
        exit 2
      }
      test_name="$1"
      ;;
    --host)
      shift || {
        usage >&2
        exit 2
      }
      host="$1"
      ;;
    --claude-model)
      shift || {
        usage >&2
        exit 2
      }
      claude_model="$1"
      ;;
    --claude-setting-sources)
      shift || {
        usage >&2
        exit 2
      }
      claude_setting_sources="$1"
      ;;
    --claude-plugin-dir)
      shift || {
        usage >&2
        exit 2
      }
      claude_plugin_dir="$1"
      ;;
    --skip-claude-preflight)
      claude_preflight="false"
      ;;
    --no-reset)
      reset_sandbox="false"
      ;;
    --no-preclean)
      preclean_sandbox="false"
      ;;
    --allow-dirty-baseline)
      allow_dirty_baseline="true"
      preclean_sandbox="false"
      ;;
    --idle-timeout)
      shift || {
        usage >&2
        exit 2
      }
      idle_timeout_seconds="$1"
      idle_timeout_user_set="true"
      ;;
    --max-step-timeout|--step-timeout)
      shift || {
        usage >&2
        exit 2
      }
      max_step_timeout_seconds="$1"
      ;;
    --progress-interval)
      shift || {
        usage >&2
        exit 2
      }
      progress_heartbeat_seconds="$1"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      echo "[ERROR] Unknown argument: $1" >&2
      exit 2
      ;;
  esac
  shift
done

if [ "$host" != "codex" ] && [ "$host" != "claude" ]; then
  echo "[ERROR] Unsupported host: $host (expected codex or claude)" >&2
  exit 2
fi

if [ "$host" = "claude" ] && ! command -v claude >/dev/null 2>&1; then
  echo "[ERROR] claude CLI not found" >&2
  exit 2
fi
if [ "$host" = "claude" ] && [ ! -d "$claude_plugin_dir" ]; then
  echo "[ERROR] Claude plugin dir not found: $claude_plugin_dir" >&2
  exit 2
fi
if [ "$host" = "codex" ] && ! command -v codex >/dev/null 2>&1; then
  echo "[ERROR] codex CLI not found" >&2
  exit 2
fi
if [ "$host" = "claude" ] && [ "$idle_timeout_user_set" = "false" ]; then
  idle_timeout_seconds=600
fi

case "$scenario" in
  1|scenario_1|scenario_1_priority)
    scenario="scenario_1_priority"
    ;;
  2|scenario_2|scenario_2_complex|scenario_2_complex_workflow)
    scenario="scenario_2_complex_workflow"
    ;;
  3|scenario_3|scenario_3_self_improvement)
    scenario="scenario_3_self_improvement"
    ;;
  *)
    echo "[ERROR] Unsupported scenario: $scenario" >&2
    usage >&2
    exit 2
    ;;
esac

if [ -z "$test_name" ]; then
  test_name="$scenario"
fi

if [ ! -d "$sandbox_repo" ]; then
  echo "[ERROR] Sandbox project not found: $sandbox_repo" >&2
  exit 1
fi
if [ "$sandbox_repo" != "$expected_sandbox_repo" ]; then
  echo "[ERROR] Refusing to run outside the dedicated sandbox: $sandbox_repo" >&2
  exit 1
fi
sandbox_git_root="$(git -C "$sandbox_repo" rev-parse --show-toplevel 2>/dev/null || true)"
if [ "$sandbox_git_root" != "$expected_sandbox_repo" ]; then
  echo "[ERROR] Sandbox git root mismatch: ${sandbox_git_root:-missing} (expected $expected_sandbox_repo)" >&2
  exit 1
fi

run_date="$(date +%F)"
run_id="$(date +%Y%m%d-%H%M%S)"
report_dir="$as_usual_repo/docs/test/${run_date}-${test_name}-${host}"
if [ -e "$report_dir" ]; then
  report_dir="${report_dir}-${run_id}"
fi

mkdir -p \
  "$report_dir/logs/terminal" \
  "$report_dir/logs/$host" \
  "$report_dir/logs/backend" \
  "$report_dir/logs/artifacts/copied-topic-files" \
  "$report_dir/logs/sandbox-snapshots"
exec > >(tee "$report_dir/logs/run.log") 2>&1

echo "[INFO] AsUsual repo: $as_usual_repo"
echo "[INFO] Sandbox repo: $sandbox_repo"
echo "[INFO] Host: $host"
echo "[INFO] Scenario: $scenario"
if [ "$host" = "claude" ]; then
  echo "[INFO] Claude model: $claude_model"
  echo "[INFO] Claude setting sources: $claude_setting_sources"
  echo "[INFO] Claude plugin dir: $claude_plugin_dir"
fi
echo "[INFO] Report dir: $report_dir"
echo "[INFO] Idle timeout seconds: $idle_timeout_seconds"
echo "[INFO] Max step timeout seconds: $max_step_timeout_seconds"
echo "[INFO] Progress heartbeat seconds: $progress_heartbeat_seconds"
echo "[INFO] Sandbox preclean enabled: $preclean_sandbox"

run_logged() {
  local name="$1"
  shift

  local started_label started_iso started_epoch log_file status finished_iso duration
  started_label="$(date +%Y%m%d-%H%M%S)"
  started_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  started_epoch="$(date +%s)"
  log_file="$report_dir/logs/terminal/${started_label}-${name}.log"

  {
    echo "cwd: $(pwd)"
    echo "started_at: $started_iso"
    echo "command: $*"
    echo "--- output ---"
  } >"$log_file"

  set +e
  "$@" >>"$log_file" 2>&1
  status="$?"
  set -e

  finished_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  duration="$(( $(date +%s) - started_epoch ))"
  {
    echo "--- result ---"
    echo "exit_code: $status"
    echo "finished_at: $finished_iso"
    echo "duration_seconds: $duration"
  } >>"$log_file"

  return "$status"
}

run_claude_preflight() {
  echo "[INFO] Running Claude preflight"
  if ! run_logged "claude-preflight" \
    claude -p \
      --model "$claude_model" \
      --setting-sources "$claude_setting_sources" \
      --plugin-dir "$claude_plugin_dir" \
      --permission-mode bypassPermissions \
      --output-format text \
      "AsUsual sandbox E2E preflight. Do not edit files. Reply OK only."; then
    echo "[ERROR] Claude preflight failed. Skipping sandbox reset so the current sandbox artifacts remain intact." >&2
    agent_failed="true"
    exit 1
  fi
}

file_signature() {
  local path="$1"
  if [ -e "$path" ]; then
    stat -f '%m:%z' "$path" 2>/dev/null || echo "unknown"
  else
    echo "missing"
  fi
}

summarize_last_event() {
  local path="$1"
  if [ ! -s "$path" ]; then
    echo "no events captured"
    return 0
  fi

  python3 - "$path" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
line = ""
for candidate in reversed(path.read_text(errors="replace").splitlines()):
    if candidate.strip():
        line = candidate
        break
if not line:
    print("no events captured")
    raise SystemExit(0)
try:
    event = json.loads(line)
except json.JSONDecodeError:
    print(line[:240])
    raise SystemExit(0)

parts = [f"type={event.get('type', 'unknown')}"]
item = event.get("item")
if isinstance(item, dict):
    for key in ("type", "id", "status", "exit_code"):
        value = item.get(key)
        if value is not None:
            parts.append(f"item.{key}={value}")
    text = item.get("text") or item.get("command") or item.get("message")
    if text:
        parts.append("text=" + str(text).replace("\n", " ")[:180])
usage = event.get("usage")
if isinstance(usage, dict):
    output_tokens = usage.get("output_tokens")
    if output_tokens is not None:
        parts.append(f"output_tokens={output_tokens}")
print("; ".join(parts))
PY
}

count_lines() {
  local path="$1"
  if [ -e "$path" ]; then
    wc -l <"$path" 2>/dev/null | tr -d '[:space:]'
  else
    echo "0"
  fi
}

terminate_step_process() {
  local pid="$1"
  local children
  children="$(pgrep -P "$pid" 2>/dev/null || true)"
  for child in $children; do
    kill "$child" >/dev/null 2>&1 || true
  done
  kill "$pid" >/dev/null 2>&1 || true
  sleep 2
  for child in $children; do
    kill -9 "$child" >/dev/null 2>&1 || true
  done
  kill -9 "$pid" >/dev/null 2>&1 || true
}

write_claude_last_message() {
  local json_file="$1"
  local output_file="$2"
  python3 - "$json_file" "$output_file" <<'PY'
import json
import pathlib
import sys

json_file = pathlib.Path(sys.argv[1])
output_file = pathlib.Path(sys.argv[2])
last_text = ""

for line in json_file.read_text(encoding="utf-8", errors="replace").splitlines():
    if not line.strip():
        continue
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        continue
    if event.get("type") == "result" and isinstance(event.get("result"), str):
        last_text = event["result"]
        continue
    message = event.get("message")
    if not isinstance(message, dict):
        continue
    chunks = []
    for block in message.get("content", []):
        if isinstance(block, dict) and block.get("type") == "text":
            chunks.append(str(block.get("text", "")))
    if chunks:
        last_text = "\n".join(chunks)

output_file.write_text((last_text or "").rstrip() + "\n", encoding="utf-8")
PY
}

run_codex_step() {
  local step="$1"
  local prompt="$2"
  local output_file="$report_dir/logs/codex/${step}-last-message.md"
  local json_file="$report_dir/logs/codex/${step}-events.jsonl"
  local stderr_file="$report_dir/logs/codex/${step}-stderr.log"
  local terminal_file started_label started_iso started_epoch status pid elapsed finished_iso
  local last_event_sig last_stderr_sig last_output_sig event_sig stderr_sig output_sig
  local last_activity_epoch last_log_update_iso last_activity_source now idle_elapsed
  local last_heartbeat_epoch event_count last_event_summary progress_line
  started_label="$(date +%Y%m%d-%H%M%S)"
  started_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  started_epoch="$(date +%s)"
  terminal_file="$report_dir/logs/terminal/${started_label}-${step}.log"

  echo "[INFO] Running Codex step: $step"
  {
    echo "cwd: $sandbox_repo"
    echo "started_at: $started_iso"
    echo "provider: $host"
    echo "step: $step"
    echo "idle_timeout_seconds: $idle_timeout_seconds"
    echo "max_step_timeout_seconds: $max_step_timeout_seconds"
    echo "progress_heartbeat_seconds: $progress_heartbeat_seconds"
    echo "command: codex exec -C $sandbox_repo --dangerously-bypass-hook-trust --dangerously-bypass-approvals-and-sandbox --json -o $output_file <prompt>"
    echo "stdout_jsonl: $json_file"
    echo "stderr_log: $stderr_file"
    echo "last_message: $output_file"
    echo "--- prompt ---"
    echo "$prompt"
    echo "--- output ---"
  } >"$terminal_file"

  set +e
  codex exec \
    -C "$sandbox_repo" \
    --dangerously-bypass-hook-trust \
    --dangerously-bypass-approvals-and-sandbox \
    --json \
    -o "$output_file" \
    "$prompt" >"$json_file" 2>"$stderr_file" &
  pid="$!"

  status=0
  last_activity_epoch="$started_epoch"
  last_log_update_iso="$started_iso"
  last_activity_source="start"
  last_heartbeat_epoch="$started_epoch"
  last_event_sig="$(file_signature "$json_file")"
  last_stderr_sig="$(file_signature "$stderr_file")"
  last_output_sig="$(file_signature "$output_file")"
  while kill -0 "$pid" >/dev/null 2>&1; do
    now="$(date +%s)"
    elapsed="$(( now - started_epoch ))"
    event_sig="$(file_signature "$json_file")"
    stderr_sig="$(file_signature "$stderr_file")"
    output_sig="$(file_signature "$output_file")"

    if [ "$event_sig" != "$last_event_sig" ]; then
      last_event_sig="$event_sig"
      last_activity_epoch="$now"
      last_log_update_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      last_activity_source="events.jsonl"
    elif [ "$stderr_sig" != "$last_stderr_sig" ]; then
      last_stderr_sig="$stderr_sig"
      last_activity_epoch="$now"
      last_log_update_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      last_activity_source="stderr.log"
    elif [ "$output_sig" != "$last_output_sig" ]; then
      last_output_sig="$output_sig"
      last_activity_epoch="$now"
      last_log_update_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      last_activity_source="last-message.md"
    fi

    idle_elapsed="$(( now - last_activity_epoch ))"
    if [ "$progress_heartbeat_seconds" -gt 0 ] && [ "$(( now - last_heartbeat_epoch ))" -ge "$progress_heartbeat_seconds" ]; then
      event_count="$(count_lines "$json_file")"
      last_event_summary="$(summarize_last_event "$json_file")"
      progress_line="[INFO] Codex step progress: step=$step elapsed=${elapsed}s idle=${idle_elapsed}s lastLogUpdate=$last_log_update_iso source=$last_activity_source events=$event_count lastEvent=\"$last_event_summary\""
      echo "$progress_line"
      {
        echo "progress_heartbeat_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "progress_elapsed_seconds: $elapsed"
        echo "progress_idle_seconds: $idle_elapsed"
        echo "progress_event_count: $event_count"
        echo "progress_last_log_update_at: $last_log_update_iso"
        echo "progress_last_log_source: $last_activity_source"
        echo "progress_last_event_summary: $last_event_summary"
      } >>"$terminal_file"
      last_heartbeat_epoch="$now"
    fi

    if [ "$elapsed" -ge "$max_step_timeout_seconds" ]; then
      echo "[WARN] Codex step max timeout: $step after ${elapsed}s"
      echo "timeout_kind: max" >>"$terminal_file"
      echo "timeout_after_seconds: $elapsed" >>"$terminal_file"
      echo "idle_seconds: $idle_elapsed" >>"$terminal_file"
      echo "last_log_update_at: $last_log_update_iso" >>"$terminal_file"
      echo "last_log_source: $last_activity_source" >>"$terminal_file"
      echo "last_event_summary: $(summarize_last_event "$json_file")" >>"$terminal_file"
      terminate_step_process "$pid"
      status=124
      wait "$pid" >/dev/null 2>&1 || true
      break
    fi

    if [ "$idle_elapsed" -ge "$idle_timeout_seconds" ]; then
      echo "[WARN] Codex step idle timeout: $step after ${idle_elapsed}s idle (${elapsed}s elapsed)"
      echo "timeout_kind: idle" >>"$terminal_file"
      echo "timeout_after_seconds: $elapsed" >>"$terminal_file"
      echo "idle_seconds: $idle_elapsed" >>"$terminal_file"
      echo "last_log_update_at: $last_log_update_iso" >>"$terminal_file"
      echo "last_log_source: $last_activity_source" >>"$terminal_file"
      echo "last_event_summary: $(summarize_last_event "$json_file")" >>"$terminal_file"
      terminate_step_process "$pid"
      status=124
      wait "$pid" >/dev/null 2>&1 || true
      break
    fi
    sleep 1
  done

  if [ "$status" -eq 0 ]; then
    wait "$pid"
    status="$?"
  fi
  set -e

  finished_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  {
    echo "--- stderr ---"
    cat "$stderr_file" 2>/dev/null || true
    echo "--- result ---"
    echo "exit_code: $status"
    echo "finished_at: $finished_iso"
    echo "duration_seconds: $(( $(date +%s) - started_epoch ))"
    echo "last_log_update_at: $last_log_update_iso"
    echo "last_log_source: $last_activity_source"
    echo "last_event_summary: $(summarize_last_event "$json_file")"
  } >>"$terminal_file"

  echo "$status" >"$report_dir/logs/codex/${step}-exit-code"
  if [ "$status" -ne 0 ]; then
    echo "[WARN] Codex step failed: $step status=$status"
    agent_failed="true"
    return "$status"
  fi
}

run_claude_step() {
  local step="$1"
  local prompt="$2"
  local output_file="$report_dir/logs/claude/${step}-last-message.md"
  local json_file="$report_dir/logs/claude/${step}-events.jsonl"
  local stderr_file="$report_dir/logs/claude/${step}-stderr.log"
  local terminal_file started_label started_iso started_epoch status pid elapsed finished_iso
  local last_event_sig last_stderr_sig last_output_sig event_sig stderr_sig output_sig
  local last_activity_epoch last_log_update_iso last_activity_source now idle_elapsed
  local last_heartbeat_epoch event_count last_event_summary progress_line
  started_label="$(date +%Y%m%d-%H%M%S)"
  started_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  started_epoch="$(date +%s)"
  terminal_file="$report_dir/logs/terminal/${started_label}-${step}.log"

  echo "[INFO] Running Claude step: $step"
  {
    echo "cwd: $sandbox_repo"
    echo "started_at: $started_iso"
    echo "provider: $host"
    echo "step: $step"
    echo "idle_timeout_seconds: $idle_timeout_seconds"
    echo "max_step_timeout_seconds: $max_step_timeout_seconds"
    echo "progress_heartbeat_seconds: $progress_heartbeat_seconds"
    echo "command: claude -p --model $claude_model --setting-sources $claude_setting_sources --plugin-dir $claude_plugin_dir --permission-mode bypassPermissions --output-format stream-json --include-hook-events --verbose <prompt>"
    echo "stdout_jsonl: $json_file"
    echo "stderr_log: $stderr_file"
    echo "last_message: $output_file"
    echo "--- prompt ---"
    echo "$prompt"
    echo "--- output ---"
  } >"$terminal_file"

  set +e
  (
    cd "$sandbox_repo" &&
      claude -p \
        --model "$claude_model" \
        --setting-sources "$claude_setting_sources" \
        --plugin-dir "$claude_plugin_dir" \
        --permission-mode bypassPermissions \
        --output-format stream-json \
        --include-hook-events \
        --verbose \
        "$prompt"
  ) >"$json_file" 2>"$stderr_file" &
  pid="$!"

  status=0
  last_activity_epoch="$started_epoch"
  last_log_update_iso="$started_iso"
  last_activity_source="start"
  last_heartbeat_epoch="$started_epoch"
  last_event_sig="$(file_signature "$json_file")"
  last_stderr_sig="$(file_signature "$stderr_file")"
  last_output_sig="$(file_signature "$output_file")"
  while kill -0 "$pid" >/dev/null 2>&1; do
    now="$(date +%s)"
    elapsed="$(( now - started_epoch ))"
    event_sig="$(file_signature "$json_file")"
    stderr_sig="$(file_signature "$stderr_file")"
    output_sig="$(file_signature "$output_file")"

    if [ "$event_sig" != "$last_event_sig" ]; then
      last_event_sig="$event_sig"
      last_activity_epoch="$now"
      last_log_update_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      last_activity_source="events.jsonl"
    elif [ "$stderr_sig" != "$last_stderr_sig" ]; then
      last_stderr_sig="$stderr_sig"
      last_activity_epoch="$now"
      last_log_update_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      last_activity_source="stderr.log"
    elif [ "$output_sig" != "$last_output_sig" ]; then
      last_output_sig="$output_sig"
      last_activity_epoch="$now"
      last_log_update_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      last_activity_source="last-message.md"
    fi

    idle_elapsed="$(( now - last_activity_epoch ))"
    if [ "$progress_heartbeat_seconds" -gt 0 ] && [ "$(( now - last_heartbeat_epoch ))" -ge "$progress_heartbeat_seconds" ]; then
      event_count="$(count_lines "$json_file")"
      last_event_summary="$(summarize_last_event "$json_file")"
      progress_line="[INFO] Claude step progress: step=$step elapsed=${elapsed}s idle=${idle_elapsed}s lastLogUpdate=$last_log_update_iso source=$last_activity_source events=$event_count lastEvent=\"$last_event_summary\""
      echo "$progress_line"
      {
        echo "progress_heartbeat_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "progress_elapsed_seconds: $elapsed"
        echo "progress_idle_seconds: $idle_elapsed"
        echo "progress_event_count: $event_count"
        echo "progress_last_log_update_at: $last_log_update_iso"
        echo "progress_last_log_source: $last_activity_source"
        echo "progress_last_event_summary: $last_event_summary"
      } >>"$terminal_file"
      last_heartbeat_epoch="$now"
    fi

    if [ "$elapsed" -ge "$max_step_timeout_seconds" ]; then
      echo "[WARN] Claude step max timeout: $step after ${elapsed}s"
      echo "timeout_kind: max" >>"$terminal_file"
      echo "timeout_after_seconds: $elapsed" >>"$terminal_file"
      echo "idle_seconds: $idle_elapsed" >>"$terminal_file"
      echo "last_log_update_at: $last_log_update_iso" >>"$terminal_file"
      echo "last_log_source: $last_activity_source" >>"$terminal_file"
      echo "last_event_summary: $(summarize_last_event "$json_file")" >>"$terminal_file"
      terminate_step_process "$pid"
      status=124
      wait "$pid" >/dev/null 2>&1 || true
      break
    fi

    if [ "$idle_elapsed" -ge "$idle_timeout_seconds" ]; then
      echo "[WARN] Claude step idle timeout: $step after ${idle_elapsed}s idle (${elapsed}s elapsed)"
      echo "timeout_kind: idle" >>"$terminal_file"
      echo "timeout_after_seconds: $elapsed" >>"$terminal_file"
      echo "idle_seconds: $idle_elapsed" >>"$terminal_file"
      echo "last_log_update_at: $last_log_update_iso" >>"$terminal_file"
      echo "last_log_source: $last_activity_source" >>"$terminal_file"
      echo "last_event_summary: $(summarize_last_event "$json_file")" >>"$terminal_file"
      terminate_step_process "$pid"
      status=124
      wait "$pid" >/dev/null 2>&1 || true
      break
    fi
    sleep 1
  done

  if [ "$status" -eq 0 ]; then
    wait "$pid"
    status="$?"
  fi
  write_claude_last_message "$json_file" "$output_file" || true
  set -e

  finished_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  {
    echo "--- stderr ---"
    cat "$stderr_file" 2>/dev/null || true
    echo "--- result ---"
    echo "exit_code: $status"
    echo "finished_at: $finished_iso"
    echo "duration_seconds: $(( $(date +%s) - started_epoch ))"
    echo "last_log_update_at: $last_log_update_iso"
    echo "last_log_source: $last_activity_source"
    echo "last_event_summary: $(summarize_last_event "$json_file")"
  } >>"$terminal_file"

  echo "$status" >"$report_dir/logs/claude/${step}-exit-code"
  if [ "$status" -ne 0 ]; then
    echo "[WARN] Claude step failed: $step status=$status"
    agent_failed="true"
    return "$status"
  fi
}

run_agent_step() {
  local step="$1"
  local prompt="$2"
  local full_prompt

  full_prompt="$(compose_agent_prompt "$prompt")"

  case "$host" in
    codex) run_codex_step "$step" "$full_prompt" ;;
    claude) run_claude_step "$step" "$full_prompt" ;;
    *)
      echo "[ERROR] Unsupported host: $host" >&2
      return 2
      ;;
  esac
}

find_topic_dir() {
  find "$sandbox_repo/.as-usual/topic" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort | tail -1 || true
}

fill_question_answers() {
  local topic="$1"
  python3 "$script_dir/fill-question-answers.py" --scenario "$scenario" "$topic"
}

topic_log_prompt_contract() {
  cat <<'EOF' | sed "s/__AS_USUAL_HOST__/$host/g"

AsUsual sandbox runner contract:
- Use the audit-first helper exactly as implemented at `/Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py`.
- Never invent topic-log event names, artifact names, command aliases, or flags.
- New topics use `topic.md` plus append-only `audit.jsonl`. Do not create or update the removed legacy state artifact.
- Valid artifact names are exactly: `question`, `requirements`, `plan`, `codeReviewReport`, `report`, `topic`, `audit`.
  - For question files, always use `--name question --value question-c1.md --append`.
  - Never use artifact names such as `questionsC1`, `questions`, `question-c1`, or `audit.jsonl`.
  - Do not set `audit` with the artifact command; audit is fixed as `audit.jsonl`.
- Valid statuses are derived from audit events: `active`, `blocked`, `complete`, `follow-up-needed`, `cancelled`.
- Valid phases are exactly: `start-work`, `define-requirements`, `requirements-complete`, `writing-plan`, `plan-review`, `executing`, `execution-complete`, `review-execution`, `review-complete`, `review-fixes-needed`, `cleanup-code`, `cleanup-complete`, `finalized`, `git-action`, `git-action-complete`, `direct-execute-complete`, `blocked`.
- Valid next actions are exactly: `route`, `answer-questions`, `write-requirements`, `approve-plan`, `write-plan`, `approve-execute`, `execute`, `review-execution`, `address-review-findings`, `decide-code-cleanup`, `cleanup-code`, `finalize`, `git-action-decision`, `git-action`, `none`.
- For this __AS_USUAL_HOST__ E2E run, use actor `__AS_USUAL_HOST__` in audit and approval helper calls.
- Before inventing flags, run the helper with `--help` or use these known forms:
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py route-start-work --topic-dir <topicDir> --route define-requirements --summary <text>`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py artifact --topic-dir <topicDir> --name <artifactName> --value <file>`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py artifact --topic-dir <topicDir> --name question --value question-c1.md --append --actor __AS_USUAL_HOST__`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py decision --topic-dir <topicDir> --summary <text>`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py verification --topic-dir <topicDir> --command <command> --result <result> --verdict PASS --summary "Final command: <command> -> exit 0."`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py approve-execution --topic-dir <topicDir> --approved-by user --source <source>`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py approve-high-risk --topic-dir <topicDir> --operation-id <id> --description <description> --rollback <rollback> --approved-by user`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py dispatch-task --topic-dir <topicDir> --task <task> --mode subagent-driven --role implementer --context requirements.md,plan.md --summary <text> --actor __AS_USUAL_HOST__`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py record-task-review --topic-dir <topicDir> --task <task> --review-type requirements --status passed --critical 0 --important 0 --minor 0 --summary <text> --actor __AS_USUAL_HOST__`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py record-task-review --topic-dir <topicDir> --task <task> --review-type quality --status passed --critical 0 --important 0 --minor 0 --summary <text> --actor __AS_USUAL_HOST__`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py complete-task --topic-dir <topicDir> --task <task> --mode tdd --test-target <test> --red-evidence <red-command-and-result> --green-evidence <green-command-and-result> --verification <text> --result PASS --artifacts <commaFiles> --actor __AS_USUAL_HOST__`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py complete-execution --topic-dir <topicDir> --summary <text> --actor __AS_USUAL_HOST__`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py record-review --topic-dir <topicDir> --mode self --status passed --critical 0 --important 0 --minor <count> --reason <text> --actor __AS_USUAL_HOST__`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py skip-code-cleanup --topic-dir <topicDir> --reason <text> --actor __AS_USUAL_HOST__`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py finalize-topic --topic-dir <topicDir> --status complete --summary <text> --report report.md --actor __AS_USUAL_HOST__`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py status --topic-dir <topicDir> --json`
  - `python3 /Users/happyhsryu/dev/personal/as-usual/scripts/topic-log.py validate --topic-dir <topicDir>`
- Do not use unsupported aliases or fields: `current`, `append`, `check`, `--field`, `--key`, `--note`, `--value true` for removed state-field booleans, `append-audit`, `questionsC1`, `question-c1`, the removed legacy state artifact, or `audit.jsonl` as an artifact name.
- If a topic-log command exits nonzero, fix the command and rerun it before moving on. Avoid leaving recoverable helper-usage failures in the transcript.
- During plan writing, choose `subagent-driven` for isolated bounded tasks when the host exposes subagent tools. If the host cannot dispatch a fresh bounded subagent, use `mixed` and make at least one implementation task `subagent-driven`; only fall back to pure `inline` after recording the host limitation as a blocker.
- During execute, verify the subagent path by recording at least one `task.dispatched` event with mode `subagent-driven`, followed by task-level requirements and quality review events.
- During execute, every implementation task must use `complete-task --mode tdd` with non-empty `--test-target`, `--red-evidence`, and `--green-evidence`; do not use `approved-tdd-exception` for this sandbox scenario.
- During execute, record at least one `complete-task` verification containing both `Final command:` and the exact substrings `mvn test` and `npm run build`, and make sure the matching command actually exits 0.
- Before finalizing, run `validate` and ensure `status --json` derives phase `finalized`, next action `git-action-decision`, and a `topic.finalized` event.

EOF
}

compose_agent_prompt() {
  local prompt="$1"
  printf '%s\n\n%s' "$(topic_log_prompt_contract)" "$prompt"
}

copy_if_exists() {
  local source="$1"
  local destination="$2"
  if [ -e "$source" ]; then
    mkdir -p "$(dirname "$destination")"
    cp -R "$source" "$destination"
  fi
}

preclean_sandbox_repo() {
  echo "[INFO] Precleaning dedicated sandbox before E2E run"

  git -C "$sandbox_repo" status --short --untracked-files=all >"$report_dir/logs/artifacts/sandbox-status-before-preclean.txt" || true
  git -C "$sandbox_repo" diff --stat >"$report_dir/logs/artifacts/sandbox-diff-stat-before-preclean.txt" || true
  git -C "$sandbox_repo" diff >"$report_dir/logs/artifacts/sandbox.diff-before-preclean" || true
  git -C "$sandbox_repo" ls-files --others --exclude-standard >"$report_dir/logs/artifacts/sandbox-untracked-before-preclean.txt" || true

  if [ "$reset_sandbox" = "true" ] && [ -d "$sandbox_repo/.as-usual" ]; then
    echo "[INFO] Archiving existing sandbox .as-usual into report before preclean"
    copy_if_exists "$sandbox_repo/.as-usual" "$report_dir/logs/sandbox-snapshots/pre-run-dot-as-usual"
    pre_run_topic_archived="true"
  fi

  run_logged "sandbox-preclean-restore" git -C "$sandbox_repo" restore --worktree --staged .
  run_logged "sandbox-preclean-clean" git -C "$sandbox_repo" clean -fd

  if [ "$reset_sandbox" = "true" ]; then
    rm -rf "$sandbox_repo/.as-usual"
  fi
  if [ -d "$sandbox_repo/backend/logs" ]; then
    find "$sandbox_repo/backend/logs" -maxdepth 1 -type f -name 'as-usual-backend-*.log' -delete
  fi

  git -C "$sandbox_repo" status --short --untracked-files=all >"$report_dir/logs/artifacts/sandbox-status-after-preclean.txt" || true
  sandbox_precleaned="true"
}

write_report() {
  local latest_topic="$1"
  REPORT_DIR="$report_dir" \
  AS_USUAL_REPO="$as_usual_repo" \
  SANDBOX_REPO="$sandbox_repo" \
  HOST="$host" \
  TEST_NAME="$test_name" \
  SCENARIO="$scenario" \
  RUN_ID="$run_id" \
  TOPIC_DIR="${latest_topic:-}" \
  AGENT_FAILED="$agent_failed" \
  PRE_RUN_TOPIC_ARCHIVED="$pre_run_topic_archived" \
  SANDBOX_PRECLEANED="$sandbox_precleaned" \
python3 <<'PY'
import json
import os
import pathlib
import re
import subprocess
import sys

report_dir = pathlib.Path(os.environ["REPORT_DIR"])
as_usual_repo = pathlib.Path(os.environ["AS_USUAL_REPO"])
sandbox_repo = pathlib.Path(os.environ["SANDBOX_REPO"])
topic_dir_value = os.environ.get("TOPIC_DIR", "")
topic_dir = pathlib.Path(topic_dir_value) if topic_dir_value else None
host = os.environ["HOST"]
test_name = os.environ["TEST_NAME"]
scenario = os.environ["SCENARIO"]
run_id = os.environ["RUN_ID"]
agent_failed = os.environ["AGENT_FAILED"] == "true"
pre_run_topic_archived = os.environ["PRE_RUN_TOPIC_ARCHIVED"] == "true"
sandbox_precleaned = os.environ["SANDBOX_PRECLEANED"] == "true"

def read(path: pathlib.Path) -> str:
    if path and path.exists():
        return path.read_text(errors="replace")
    return ""

def parse_json(path: pathlib.Path):
    text = read(path)
    if not text.strip():
        return {}, f"missing: {path}"
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        return {}, f"invalid JSON: {path}: {exc}"
    if not isinstance(value, dict):
        return {}, f"expected JSON object: {path}"
    return value, None

def parse_jsonl(path: pathlib.Path):
    events = []
    for line in read(path).splitlines():
        if not line.strip():
            continue
        events.append(json.loads(line))
    return events

def derive_status():
    if not topic_dir:
        return {}, "missing topic dir"
    helper = as_usual_repo / "scripts/topic-log.py"
    completed = subprocess.run(
        [sys.executable, str(helper), "status", "--topic-dir", str(topic_dir), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return {}, (completed.stderr or completed.stdout).strip()
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return {}, f"invalid topic status JSON: {exc}"
    if not isinstance(value, dict):
        return {}, "topic status JSON root is not an object"
    return value, None

def exists(name: str) -> bool:
    return bool(topic_dir and (topic_dir / name).exists())

topic_text = read(topic_dir / "topic.md") if topic_dir else ""
audit = read(topic_dir / "audit.jsonl") if topic_dir else ""
requirements = read(topic_dir / "requirements.md") if topic_dir else ""
plan_text = read(topic_dir / "plan.md") if topic_dir else ""
plan = read(topic_dir / "plan.md") if topic_dir else ""
questions = sorted(topic_dir.glob("question-c*.md")) if topic_dir and topic_dir.exists() else []

question_text = "\n".join(read(path) for path in questions)
answer_markers = re.findall(r"^\[Answer\]:(.*)$", question_text, flags=re.MULTILINE)
unanswered = [value for value in answer_markers if not value.strip()]

audit_parse_ok = True
audit_events = 0
audit_event_data = []
for line in audit.splitlines():
    if not line.strip():
        continue
    try:
        audit_event_data.append(json.loads(line))
        audit_events += 1
    except json.JSONDecodeError:
        audit_parse_ok = False
        break

derived_status, status_error = derive_status()
phase = derived_status.get("phase", "unknown") if not status_error else "unknown"
next_action = derived_status.get("nextAction", "unknown") if not status_error else "unknown"
status = derived_status.get("status", "unknown") if not status_error else "unknown"
created_event = next((event for event in audit_event_data if event.get("event") == "topic.created"), {})
current_topic_created_at = created_event.get("timestamp", "unknown") if isinstance(created_event, dict) else "unknown"

checks = []
def check(name: str, passed: bool, evidence: str):
    checks.append((name, "PASS" if passed else "FAIL", evidence))

check("Agent steps", not agent_failed, f"all {host} steps exited 0" if not agent_failed else f"one or more {host} steps failed")
check("Topic folder", bool(topic_dir and topic_dir.exists()), str(topic_dir) if topic_dir else "missing")
check("Canonical path", bool(topic_dir and ".as-usual/topic/" in str(topic_dir)), str(topic_dir) if topic_dir else "missing")
check("Topic MD", exists("topic.md"), "topic.md exists" if exists("topic.md") else "missing")
check("Topic status", not status_error, "topic-log.py status derived status" if not status_error else status_error)
check("Audit JSONL", exists("audit.jsonl"), "audit.jsonl exists" if exists("audit.jsonl") else "missing")
check("Audit JSONL parse", audit_parse_ok, f"{audit_events} audit event line(s) parsed" if audit_parse_ok else "audit.jsonl contains invalid JSONL")
check("Questions", bool(questions), f"{len(questions)} question file(s)")
check("Answers filled", bool(answer_markers) and not unanswered, f"{len(answer_markers)} answer marker(s), {len(unanswered)} empty")
check("Requirements", exists("requirements.md"), "requirements.md exists" if exists("requirements.md") else "missing")
check("Plan", exists("plan.md"), "plan.md exists" if exists("plan.md") else "missing")
combined_topic = (topic_text + "\n" + audit).lower()
check("Execution evidence", "execution" in combined_topic or "verification" in combined_topic or "execute" in combined_topic, "topic.md/audit.jsonl mention execution or verification")
check("Review/finalize evidence", any(word in combined_topic for word in ["review", "finalize", "finalized"]), "topic.md/audit.jsonl mention review or finalize")
plan_lower = plan_text.lower()
dispatch_events = [
    event for event in audit_event_data
    if isinstance(event, dict)
    and event.get("event") == "task.dispatched"
    and isinstance(event.get("data"), dict)
    and event["data"].get("mode") == "subagent-driven"
]
task_reviews = [
    event for event in audit_event_data
    if isinstance(event, dict)
    and event.get("event") == "task.review_completed"
    and isinstance(event.get("data"), dict)
]
review_types = {event["data"].get("reviewType") for event in task_reviews}
tdd_tasks = [
    event for event in audit_event_data
    if isinstance(event, dict)
    and event.get("event") == "task.completed"
    and isinstance(event.get("data"), dict)
    and event["data"].get("mode") == "tdd"
]
tdd_evidence_tasks = [
    event for event in tdd_tasks
    if event["data"].get("testTarget")
    and event["data"].get("redEvidence")
    and event["data"].get("greenEvidence")
]
check(
    "Subagent execution design",
    "subagent-driven" in plan_lower,
    "plan.md declares subagent-driven execution" if "subagent-driven" in plan_lower else "plan.md does not mention subagent-driven",
)
check(
    "Subagent dispatch evidence",
    bool(dispatch_events),
    f"{len(dispatch_events)} task.dispatched event(s) with mode=subagent-driven",
)
check(
    "Task review evidence",
    {"requirements", "quality"}.issubset(review_types),
    f"task review types recorded: {', '.join(sorted(str(item) for item in review_types if item)) or 'none'}",
)
check(
    "TDD RED/GREEN evidence",
    bool(tdd_evidence_tasks),
    f"{len(tdd_evidence_tasks)} tdd task(s) with testTarget/redEvidence/greenEvidence",
)

artifacts_dir = report_dir / "logs" / "artifacts"
agent_logs_dir = report_dir / "logs" / host
terminal_logs_dir = report_dir / "logs" / "terminal"

diff_stat = read(artifacts_dir / "sandbox-diff-stat.txt").strip()
lint_result, lint_error = parse_json(artifacts_dir / "e2e-lint-result.json")
if lint_error:
    lint_result = {
        "segments": {
            "workflowResult": "PASS" if not agent_failed else "FAIL",
            "artifactIntegrity": "WARNING",
            "evidenceIntegrity": "WARNING",
            "environmentCleanliness": "WARNING",
        },
        "overallResult": "PASS" if not agent_failed else "FAIL",
        "checks": [
            {
                "id": "linter.available",
                "segment": "artifactIntegrity",
                "status": "WARNING",
                "message": lint_error,
            }
        ],
        "changedFiles": {"baseline": [], "after": [], "agentProduced": [], "untracked": []},
    }
if agent_failed:
    lint_result.setdefault("segments", {})["workflowResult"] = "FAIL"
    lint_result["overallResult"] = "FAIL"
backend_logs_dir = report_dir / "logs" / "backend"
backend_logs = sorted(backend_logs_dir.glob("*.log")) if backend_logs_dir.exists() else []
log_evidence = ""
if backend_logs:
    latest_log = backend_logs[-1]
    log_evidence = "\n".join(read(latest_log).splitlines()[-12:])

step_summaries = []
for terminal_log in sorted(terminal_logs_dir.glob("*.log")):
    text = read(terminal_log)
    step_match = re.search(r"^step: (.+)$", text, flags=re.MULTILINE)
    if not step_match:
        continue
    step = step_match.group(1)
    timeout = re.search(r"^timeout_seconds: (.+)$", text, flags=re.MULTILINE)
    idle_timeout = re.search(r"^idle_timeout_seconds: (.+)$", text, flags=re.MULTILINE)
    max_step_timeout = re.search(r"^max_step_timeout_seconds: (.+)$", text, flags=re.MULTILINE)
    timeout_kind = re.search(r"^timeout_kind: (.+)$", text, flags=re.MULTILINE)
    timed_out = re.search(r"^timeout_after_seconds: (.+)$", text, flags=re.MULTILINE)
    idle_seconds = re.search(r"^idle_seconds: (.+)$", text, flags=re.MULTILINE)
    last_log_update_at = re.search(r"^last_log_update_at: (.+)$", text, flags=re.MULTILINE)
    last_event_summary = re.search(r"^last_event_summary: (.+)$", text, flags=re.MULTILINE)
    exit_code = re.search(r"^exit_code: (.+)$", text, flags=re.MULTILINE)
    duration = re.search(r"^duration_seconds: (.+)$", text, flags=re.MULTILINE)
    step_summaries.append(
        {
            "step": step,
            "exitCode": exit_code.group(1) if exit_code else "unknown",
            "durationSeconds": duration.group(1) if duration else "unknown",
            "timeoutSeconds": timeout.group(1) if timeout else "unknown",
            "idleTimeoutSeconds": idle_timeout.group(1) if idle_timeout else "",
            "maxStepTimeoutSeconds": max_step_timeout.group(1) if max_step_timeout else "",
            "timeoutKind": timeout_kind.group(1) if timeout_kind else "",
            "timedOutAfterSeconds": timed_out.group(1) if timed_out else "",
            "idleSeconds": idle_seconds.group(1) if idle_seconds else "",
            "lastLogUpdateAt": last_log_update_at.group(1) if last_log_update_at else "",
            "lastEventSummary": last_event_summary.group(1) if last_event_summary else "",
            "terminalLog": str(terminal_log.relative_to(report_dir)),
        }
    )

if agent_failed:
    overall_result = "FAIL"
elif phase == "finalized" and next_action == "git-action-decision":
    overall_result = "PASS"
else:
    overall_result = "BLOCKED"

overall_result = lint_result.get("overallResult", overall_result)

problems = []
for name, status_value, evidence in checks:
    if status_value == "FAIL":
        problems.append(f"- {name}: {evidence}")
for item in lint_result.get("checks", []):
    status_value = item.get("status")
    if status_value not in {"FAIL", "WARNING"}:
        continue
    check_id = item.get("id", "unknown")
    message = str(item.get("message", "")).replace("\n", " ")
    prefix = "Linter failure" if status_value == "FAIL" else "Linter warning"
    problems.append(f"- {prefix} `{check_id}`: {message}")
command_issues = (
    lint_result.get("commandFailures", {}).get("nonBlocking")
    or lint_result.get("commandFailures", {}).get("fatal", [])
)
if command_issues:
    problems.append("- Non-blocking agent command issues:")
    for event in command_issues[:5]:
        command = str(event.get("command", "")).replace("\n", " ")
        output = str(event.get("output", "")).replace("\n", " ")
        problems.append(
            f"  - {event.get('id') or 'unknown'} exit={event.get('exitCode')}: "
            f"{command[:180]} -> {output[:180] or 'no output'}"
        )
if overall_result == "BLOCKED":
    problems.append(f"- Workflow did not reach finalized state: phase={phase}, nextAction={next_action}.")
if not problems:
    problems.append("- No blocking harness failures detected by static artifact analysis.")
if "direct-execute" in combined_topic and exists("requirements.md"):
    problems.append("- Topic evidence mentions direct-execute despite requirements/plan artifacts; review phase routing consistency.")
if topic_dir and not backend_logs:
    problems.append("- No backend AOP log files were copied; execution may not have exercised the running backend.")

improvements = [
    "- Add a first-class deterministic E2E harness mode that can emit machine-readable phase status.",
    "- Keep the sandbox clean by default; use --allow-dirty-baseline only for intentionally noisy comparison runs.",
    "- Add report-level session metadata from agent session ids so host/session comparison is complete.",
    "- Promote recurring fatal command patterns into targeted runtime helper tests.",
]

report = []
report.append(f"# {test_name} Sandbox E2E Report")
report.append("")
report.append("```yaml")
report.append(f"provider: {host}")
report.append(f"scenario: {scenario}")
report.append(f"sandboxProject: {sandbox_repo}")
report.append(f"asUsualRepo: {as_usual_repo}")
report.append(f"startedAt: {run_id}")
report.append(f"topicDir: {topic_dir if topic_dir else 'missing'}")
report.append(f"preRunTopicArchived: {str(pre_run_topic_archived).lower()}")
report.append(f"sandboxPrecleaned: {str(sandbox_precleaned).lower()}")
report.append(f"currentTopicCreatedAt: {current_topic_created_at}")
report.append("```")
report.append("")
report.append(f"## Result")
report.append("")
report.append(f"- Overall Result: `{overall_result}`")
report.append("- Overall result is based on user-task outcome; non-blocking agent/process issues are listed below.")
report.append("")
report.append("## Result Segments")
report.append("")
report.append("| Segment | Status |")
report.append("| --- | --- |")
for segment, value in lint_result.get("segments", {}).items():
    report.append(f"| {segment} | {value} |")
report.append("")
report.append("## Metadata")
report.append("")
report.append(f"- Host: `{host}`")
report.append(f"- Run ID: `{run_id}`")
report.append(f"- AsUsual Repo: `{as_usual_repo}`")
report.append(f"- Sandbox Repo: `{sandbox_repo}`")
report.append(f"- Topic Dir: `{topic_dir if topic_dir else 'missing'}`")
report.append(f"- Pre-run Topic Archived: `{str(pre_run_topic_archived).lower()}`")
report.append(f"- Sandbox Precleaned: `{str(sandbox_precleaned).lower()}`")
report.append(f"- Current Topic Created At: `{current_topic_created_at}`")
report.append(f"- Topic Status: `{status}`")
report.append(f"- Topic Phase: `{phase}`")
report.append(f"- Next Action: `{next_action}`")
report.append("")
report.append("## Step Summary")
report.append("")
report.append("| Step | Exit Code | Duration | Timeout | Last Log Update |")
report.append("| --- | --- | --- | --- | --- |")
for item in step_summaries:
    if item["timeoutKind"]:
        timeout_text = f"{item['timeoutKind']} after {item['timedOutAfterSeconds']}s"
        if item["idleSeconds"]:
            timeout_text += f" (idle {item['idleSeconds']}s)"
    elif item["idleTimeoutSeconds"] or item["maxStepTimeoutSeconds"]:
        timeout_text = f"idle {item['idleTimeoutSeconds'] or 'unknown'}s / max {item['maxStepTimeoutSeconds'] or 'unknown'}s"
    else:
        timeout_text = f"{item['timeoutSeconds']}s"
    report.append(f"| {item['step']} | {item['exitCode']} | {item['durationSeconds']}s | {timeout_text} | {item['lastLogUpdateAt'] or 'unknown'} |")
if not step_summaries:
    report.append("| missing | unknown | unknown | unknown | unknown |")
report.append("")
report.append("## Checks")
report.append("")
report.append("| Check | Status | Evidence |")
report.append("| --- | --- | --- |")
for name, status_value, evidence in checks:
    report.append(f"| {name} | {status_value} | {evidence.replace('|', '/')} |")
report.append("")
report.append("## Sandbox Diff")
report.append("")
report.append("```text")
report.append(diff_stat or "No sandbox diff captured.")
report.append("```")
report.append("")
stderr_summary = lint_result.get("stderrSummary", {})
report.append("## Stderr Summary")
report.append("")
report.append(f"- Known host telemetry warnings: `{len(stderr_summary.get('skillTelemetryWarnings', []))}`")
report.append(f"- Unrelated plugin manifest warnings: `{len(stderr_summary.get('unrelatedManifestWarnings', []))}`")
report.append(f"- Other warnings/errors: `{len(stderr_summary.get('otherWarnings', []))}`")
if stderr_summary.get("skillTelemetryWarnings"):
    report.append("")
    report.append("Known Codex telemetry noise; retained here as host/tooling evidence.")
    report.append("")
    report.append("```text")
    report.extend(stderr_summary["skillTelemetryWarnings"][:12])
    report.append("```")
report.append("")
report.append("## Backend Log Evidence")
report.append("")
report.append("```text")
report.append(log_evidence or "No backend log evidence copied.")
report.append("```")
report.append("")
report.append("## Linter Checks")
report.append("")
report.append("| Check | Segment | Status | Evidence |")
report.append("| --- | --- | --- | --- |")
for item in lint_result.get("checks", []):
    message = str(item.get("message", "")).replace("|", "/")
    report.append(f"| {item.get('id', 'unknown')} | {item.get('segment', 'unknown')} | {item.get('status', 'UNKNOWN')} | {message} |")
report.append("")
report.append("## Issues And Warnings")
report.append("")
report.extend(problems)
report.append("")
report.append("## Improvement Ideas")
report.append("")
report.extend(improvements)
report.append("")
report.append("## Artifacts")
report.append("")
report.append("- Logs: `logs/`")
report.append("- Terminal logs: `logs/terminal/`")
report.append(f"- Agent transcript logs: `logs/{host}/`")
report.append("- Topic snapshot: `logs/artifacts/copied-topic-files/`")
report.append("- Memory snapshot: `logs/artifacts/copied-memory-files/` when `.as-usual/memory/` exists")
report.append("- Sandbox preclean status: `logs/artifacts/sandbox-status-before-preclean.txt`")
report.append("- Sandbox diff: `logs/artifacts/sandbox.diff`")
report.append("- Backend logs: `logs/backend/`")
report.append("- Important excerpts: `evidence.md`")
report.append("- Improvement plan: `improvement-plan.md`")
report.append("")

report_path = report_dir / "report.md"
report_path.write_text("\n".join(report) + "\n")

def fenced(lang: str, content: str) -> list[str]:
    return [f"```{lang}", content.rstrip() or "(empty)", "```"]

topic_status_subset = {
    "status": status,
    "phase": phase,
    "nextAction": next_action,
    "lastEventSeq": derived_status.get("lastEventSeq") if isinstance(derived_status, dict) else None,
    "lastEvent": derived_status.get("lastEvent") if isinstance(derived_status, dict) else None,
    "preRunTopicArchived": pre_run_topic_archived,
    "sandboxPrecleaned": sandbox_precleaned,
    "artifacts": derived_status.get("artifacts", {}) if isinstance(derived_status, dict) else {},
    "blockers": derived_status.get("blockers", []) if isinstance(derived_status, dict) else [],
    "verification": derived_status.get("verification", []) if isinstance(derived_status, dict) else [],
    "review": derived_status.get("review") if isinstance(derived_status, dict) else None,
}
audit_tail = "\n".join(audit.splitlines()[-8:])
step_summary_text = "\n".join(
    f"{item['step']}: exit={item['exitCode']} duration={item['durationSeconds']}s"
    + (
        f" idleTimeout={item['idleTimeoutSeconds']}s maxStepTimeout={item['maxStepTimeoutSeconds']}s"
        if item["idleTimeoutSeconds"] or item["maxStepTimeoutSeconds"]
        else f" timeout={item['timeoutSeconds']}s"
    )
    + (f" timeoutKind={item['timeoutKind']} timedOutAfter={item['timedOutAfterSeconds']}s" if item["timeoutKind"] else "")
    + (f" idleSeconds={item['idleSeconds']}s" if item["idleSeconds"] else "")
    + (f" lastLogUpdateAt={item['lastLogUpdateAt']}" if item["lastLogUpdateAt"] else "")
    + (f" lastEventSummary={item['lastEventSummary']}" if item["lastEventSummary"] else "")
    for item in step_summaries
)
last_messages = []
for path in sorted(agent_logs_dir.glob("*-last-message.md")):
    text = read(path).strip()
    if not text:
        continue
    excerpt = "\n".join(text.splitlines()[:80])
    last_messages.append(f"## {path.name}\n\n{excerpt}")

evidence = []
evidence.append(f"# {test_name} Sandbox E2E Evidence")
evidence.append("")
evidence.append(f"- Scenario: `{scenario}`")
evidence.append("")
evidence.append("## Step Durations And Exit Codes")
evidence.append("")
evidence.extend(fenced("text", step_summary_text or "No step summaries captured."))
evidence.append("")
evidence.append("## Final Topic Status")
evidence.append("")
evidence.extend(fenced("json", json.dumps(topic_status_subset, ensure_ascii=False, indent=2)))
evidence.append("")
evidence.append("## Last Audit Events")
evidence.append("")
evidence.extend(fenced("jsonl", audit_tail or "No audit events captured."))
evidence.append("")
evidence.append("## Sandbox Diff Stat")
evidence.append("")
evidence.extend(fenced("text", diff_stat or "No sandbox diff captured."))
evidence.append("")
evidence.append("## Backend Log Excerpt")
evidence.append("")
evidence.extend(fenced("text", log_evidence or "No backend log evidence copied."))
evidence.append("")
evidence.append("## Issues And Warnings")
evidence.append("")
evidence.extend(problems)
evidence.append("")
evidence.append(f"## {host.title()} Last Message Excerpts")
evidence.append("")
evidence.extend(fenced("markdown", "\n\n---\n\n".join(last_messages) or f"No {host} last messages captured."))
evidence.append("")
evidence.append("## Raw Evidence Location")
evidence.append("")
evidence.append("- Raw logs and copied artifacts are under `logs/` and are gitignored.")
evidence.append("")

evidence_path = report_dir / "evidence.md"
evidence_path.write_text("\n".join(evidence) + "\n")

issue_actions = [
    problem for problem in problems
    if "No blocking harness failures detected" not in problem
]
if not issue_actions:
    issue_actions = [
        "- Keep the next E2E run as a regression baseline and compare any new warnings against this run.",
    ]

improvement_plan = []
improvement_plan.append(f"# {test_name} Sandbox E2E Improvement Plan")
improvement_plan.append("")
improvement_plan.append("```yaml")
improvement_plan.append(f"provider: {host}")
improvement_plan.append(f"scenario: {scenario}")
improvement_plan.append(f"runId: {run_id}")
improvement_plan.append(f"sourceReport: report.md")
improvement_plan.append(f"sourceEvidence: evidence.md")
improvement_plan.append(f"overallResult: {overall_result}")
improvement_plan.append(f"topicPhase: {phase}")
improvement_plan.append(f"nextAction: {next_action}")
improvement_plan.append("```")
improvement_plan.append("")
improvement_plan.append("## Priority")
improvement_plan.append("")
if overall_result == "FAIL":
    priority = "P0: fix blocking E2E or harness failures before using this run as release evidence."
elif overall_result == "BLOCKED":
    priority = "P0: unblock the workflow path and rerun the scenario to finalized state."
elif any("Linter warning" in item or "No backend AOP log files" in item for item in problems):
    priority = "P1: address evidence-quality warnings and preserve this run as a passing baseline."
else:
    priority = "P2: no blocking issue found; use the ideas below for the next harness hardening pass."
improvement_plan.append(f"- {priority}")
improvement_plan.append("")
improvement_plan.append("## Issue-Linked Actions")
improvement_plan.append("")
improvement_plan.extend(issue_actions)
improvement_plan.append("")
improvement_plan.append("## Suggested Improvements")
improvement_plan.append("")
improvement_plan.extend(improvements)
improvement_plan.append("")
improvement_plan.append("## Evidence To Recheck")
improvement_plan.append("")
improvement_plan.append("- `report.md` for result segments, checks, and linter messages.")
improvement_plan.append("- `evidence.md` for compact raw excerpts and final topic status.")
improvement_plan.append("- `logs/artifacts/e2e-lint-result.json` for machine-readable lint details.")
improvement_plan.append("- `logs/terminal/` for step durations, command exits, and timeout details.")
improvement_plan.append("- `logs/artifacts/copied-topic-files/` for copied runtime topic artifacts.")
improvement_plan.append("")

improvement_plan_path = report_dir / "improvement-plan.md"
improvement_plan_path.write_text("\n".join(improvement_plan) + "\n")

print(f"[INFO] Wrote report: {report_path}")
print(f"[INFO] Wrote evidence: {evidence_path}")
print(f"[INFO] Wrote improvement plan: {improvement_plan_path}")
PY
}

collect_outputs() {
  local latest_topic="$1"

  if [ -n "$latest_topic" ]; then
    rm -rf "$report_dir/logs/artifacts/copied-topic-files"
    copy_if_exists "$latest_topic" "$report_dir/logs/artifacts/copied-topic-files"
  fi

  if [ -d "$sandbox_repo/.as-usual/memory" ]; then
    mkdir -p "$report_dir/logs/artifacts"
    rm -rf "$report_dir/logs/artifacts/copied-memory-files"
    copy_if_exists "$sandbox_repo/.as-usual/memory" "$report_dir/logs/artifacts/copied-memory-files"
  fi

  if [ -d "$sandbox_repo/backend/logs" ]; then
    mkdir -p "$report_dir/logs/backend"
    find "$sandbox_repo/backend/logs" -maxdepth 1 -type f -name 'as-usual-backend-*.log' -exec cp {} "$report_dir/logs/backend/" \;
  fi

  git -C "$sandbox_repo" status --short --untracked-files=all >"$report_dir/logs/artifacts/sandbox-status-after.txt" || true
  git -C "$sandbox_repo" diff --stat >"$report_dir/logs/artifacts/sandbox-diff-stat.txt" || true
  git -C "$sandbox_repo" diff >"$report_dir/logs/artifacts/sandbox.diff" || true
  git -C "$sandbox_repo" ls-files --others --exclude-standard >"$report_dir/logs/artifacts/sandbox-untracked-after.txt" || true
  while IFS= read -r untracked_path; do
    [ -n "$untracked_path" ] || continue
    mkdir -p "$report_dir/logs/artifacts/untracked-files/$(dirname "$untracked_path")"
    cp "$sandbox_repo/$untracked_path" "$report_dir/logs/artifacts/untracked-files/$untracked_path" 2>/dev/null || true
  done <"$report_dir/logs/artifacts/sandbox-untracked-after.txt"

  local linter_args
  linter_args=(--report-dir "$report_dir" --json-output "$report_dir/logs/artifacts/e2e-lint-result.json")
  if [ "$allow_dirty_baseline" = "true" ]; then
    linter_args+=(--allow-dirty-baseline)
  fi
  python3 "$script_dir/e2e-report-linter.py" "${linter_args[@]}" || true
}

scenario_start_prompt() {
  case "$scenario" in
    scenario_1_priority)
      cat <<'EOF'
AsUsual로 task priority를 추가하는 작업을 시작해.
EOF
      ;;
    scenario_2_complex_workflow)
      cat <<'EOF'
AsUsual로 더 복잡한 task scheduling/status workflow를 추가하는 작업을 시작해.

목표는 task에 due date, reminder flag, overdue 표시, status 전환 규칙을 추가해서 backend/API/frontend가 함께 바뀌는 복합 변경을 검증하는 거야. 요구사항 질문 단계에서 scope, data model, default behavior, overdue 계산 기준, frontend 표시/검증 범위를 명확히 물어봐.
EOF
      ;;
    scenario_3_self_improvement)
      cat <<'EOF'
AsUsual로 task note/source label을 추가하는 작업을 시작해. 이 E2E는 자기개선 경로도 검증해야 해.

작업 중 사용자가 명시한 장기 규칙을 `memory.candidate`로 포착하고, finalize에서 `manage-self-improvement`가 승인된 memory를 `.as-usual/memory/MEMORY.md`에 기록하는지 확인해.

장기 규칙: 이 sandbox project의 E2E report에는 앞으로 항상 scenario id와 scenario 목적을 남긴다.
EOF
      ;;
  esac
}

scenario_requirements_prompt() {
  cat <<'EOF'
답변했어. AsUsual topic의 question-c1.md를 디스크에서 다시 읽고, 답변을 바탕으로 requirements.md를 작성해. requirements 작성과 리뷰 상태 기록까지 완료하고 plan 승인 요청 단계에서 멈춰. plan 작성이나 구현은 아직 하지마.
EOF
}

scenario_plan_prompt() {
  case "$scenario" in
    scenario_1_priority)
      cat <<'EOF'
requirements을 승인해. AsUsual workflow에 따라 requirements.md를 다시 읽고 plan.md를 작성해. 이번 E2E는 execute 단계의 subagent-driven + TDD 동작을 검증해야 하므로, host가 fresh bounded subagent dispatch를 지원하면 plan의 Execution Mode를 subagent-driven으로 두고, 지원 여부가 애매하면 mixed로 두되 최소 1개 구현 task는 subagent-driven으로 지정해. 모든 구현 task의 Test Strategy는 tdd로 작성하고 RED/GREEN evidence를 기록할 test target과 verification command를 구체화해. plan review 상태와 실행 승인 요청을 audit.jsonl에 기록하고 멈춰. 아직 구현하지마.
EOF
      ;;
    scenario_2_complex_workflow)
      cat <<'EOF'
requirements을 승인해. AsUsual workflow에 따라 requirements.md를 다시 읽고 plan.md를 작성해. 이번 복합 workflow E2E는 backend data model/API/service/frontend 표시와 status rule을 여러 task로 나누는 계획을 검증해야 해. host가 fresh bounded subagent dispatch를 지원하면 plan의 Execution Mode를 subagent-driven으로 두고, 지원 여부가 애매하면 mixed로 두되 최소 1개 구현 task는 subagent-driven으로 지정해. 모든 구현 task의 Test Strategy는 tdd로 작성하고, due date/reminder/status/overdue 각각의 RED/GREEN evidence를 기록할 test target과 verification command를 구체화해. plan review 상태와 실행 승인 요청을 audit.jsonl에 기록하고 멈춰. 아직 구현하지마.
EOF
      ;;
    scenario_3_self_improvement)
      cat <<'EOF'
requirements을 승인해. AsUsual workflow에 따라 requirements.md를 다시 읽고 plan.md를 작성해. 이번 E2E는 구현뿐 아니라 self-improvement memory candidate 경로도 검증해야 하므로, plan에는 일반 구현 task와 함께 "명시된 장기 규칙을 memory.candidate로 포착했는지 확인"하는 검증 관점을 포함해. host가 fresh bounded subagent dispatch를 지원하면 plan의 Execution Mode를 subagent-driven으로 두고, 지원 여부가 애매하면 mixed로 두되 최소 1개 구현 task는 subagent-driven으로 지정해. 모든 구현 task의 Test Strategy는 tdd로 작성하고 RED/GREEN evidence를 기록할 test target과 verification command를 구체화해. plan review 상태와 실행 승인 요청을 audit.jsonl에 기록하고 멈춰. 아직 구현하지마.
EOF
      ;;
  esac
}

scenario_execute_prompt() {
  case "$scenario" in
    scenario_1_priority)
      cat <<'EOF'
plan을 승인해. 이 sandbox E2E 테스트를 집도하는 runner/agent로서, 테스트용 프로젝트에 한해 plan에 포함된 task priority 관련 high-risk schema operation도 지금 fresh approval 한다: TaskPriority enum 추가, Task.priority persisted field/default/mapping 추가, DTO priority field 추가, service mapping, seed/default behavior, controller test expectation 변경을 승인한다. 롤백은 해당 backend/frontend 변경 파일을 되돌리고, 실제 persistent DB가 연결된 경우 tasks.priority 컬럼을 DB migration 정책에 따라 제거/롤백하는 방식이다. AsUsual workflow에 따라 plan.md를 다시 읽고 구현을 실행해. 이번 execute 검증의 핵심은 subagent-driven + TDD다. subagent task는 fresh bounded implementer로 dispatch하고 task.dispatched를 기록해. 구현 task는 RED 실패 테스트 evidence를 먼저 기록한 뒤 최소 구현으로 GREEN evidence를 기록하고, complete-task --mode tdd에 test target, red evidence, green evidence를 남겨. subagent 결과는 controller가 직접 diff와 검증을 확인하고 task-level requirements review와 quality review를 기록해. 백엔드 테스트와 프론트 빌드 같은 검증을 수행하고 audit.jsonl에 evidence를 기록해. 실행 완료 후 mandatory review-execution까지 수행하고, optional code cleanup 여부를 물어보는 단계에서 멈춰.
EOF
      ;;
    scenario_2_complex_workflow)
      cat <<'EOF'
plan을 승인해. 이 sandbox E2E 테스트를 집도하는 runner/agent로서, 테스트용 프로젝트에 한해 plan에 포함된 scheduling/status 관련 high-risk schema operation도 지금 fresh approval 한다: Task dueDate/reminder/status/overdue 계산에 필요한 backend field/default/mapping 추가, DTO/API 변경, service rule 변경, controller/service test expectation 변경, frontend form/list 표시 변경을 승인한다. 롤백은 해당 backend/frontend 변경 파일을 되돌리고, 실제 persistent DB가 연결된 경우 추가 컬럼을 DB migration 정책에 따라 제거/롤백하는 방식이다. AsUsual workflow에 따라 plan.md를 다시 읽고 구현을 실행해. 이번 execute 검증의 핵심은 복합 변경을 task 단위로 나누고 subagent-driven + TDD evidence를 남기는 것이다. subagent task는 fresh bounded implementer로 dispatch하고 task.dispatched를 기록해. 구현 task는 RED 실패 테스트 evidence를 먼저 기록한 뒤 최소 구현으로 GREEN evidence를 기록하고, complete-task --mode tdd에 test target, red evidence, green evidence를 남겨. subagent 결과는 controller가 직접 diff와 검증을 확인하고 task-level requirements review와 quality review를 기록해. 백엔드 테스트와 프론트 빌드 같은 검증을 수행하고 audit.jsonl에 evidence를 기록해. 실행 완료 후 mandatory review-execution까지 수행하고, optional code cleanup 여부를 물어보는 단계에서 멈춰.
EOF
      ;;
    scenario_3_self_improvement)
      cat <<'EOF'
plan을 승인해. 이 sandbox E2E 테스트를 집도하는 runner/agent로서, 테스트용 프로젝트에 한해 plan에 포함된 task note/source label 관련 backend/frontend 변경과 필요한 test expectation 변경을 지금 fresh approval 한다. 롤백은 해당 backend/frontend 변경 파일을 되돌리는 방식이다. AsUsual workflow에 따라 plan.md를 다시 읽고 구현을 실행해. 이번 execute 검증의 핵심은 subagent-driven + TDD와 self-improvement 후보 포착이다. 사용자가 명시한 장기 규칙("이 sandbox project의 E2E report에는 앞으로 항상 scenario id와 scenario 목적을 남긴다")을 아직 `memory.candidate`로 기록하지 않았다면 구현 흐름을 깨지 말고 audit에 candidate로 기록해. subagent task는 fresh bounded implementer로 dispatch하고 task.dispatched를 기록해. 구현 task는 RED 실패 테스트 evidence를 먼저 기록한 뒤 최소 구현으로 GREEN evidence를 기록하고, complete-task --mode tdd에 test target, red evidence, green evidence를 남겨. subagent 결과는 controller가 직접 diff와 검증을 확인하고 task-level requirements review와 quality review를 기록해. 백엔드 테스트와 프론트 빌드 같은 검증을 수행하고 audit.jsonl에 evidence를 기록해. 실행 완료 후 mandatory review-execution까지 수행하고, optional code cleanup 여부를 물어보는 단계에서 멈춰.
EOF
      ;;
  esac
}

scenario_finalize_prompt() {
  case "$scenario" in
    scenario_3_self_improvement)
      cat <<'EOF'
optional code cleanup은 생략해. AsUsual workflow에 따라 code cleanup decision을 audit.jsonl에 기록하고 finalize까지 진행해. finalize의 self-improvement pass에서 memory 후보가 제안되면, "이 sandbox project의 E2E report에는 앞으로 항상 scenario id와 scenario 목적을 남긴다" 항목은 승인된 것으로 처리해 `manage-self-improvement` apply pass로 `.as-usual/memory/MEMORY.md`에 기록해. 보류할 skill 후보가 있으면 audit에 candidate로만 남겨. commit, PR, push, deploy 같은 git action은 하지 말고 git action decision requested 상태에서 멈춰.
EOF
      ;;
    *)
      cat <<'EOF'
optional code cleanup은 생략해. AsUsual workflow에 따라 code cleanup decision을 audit.jsonl에 기록하고 finalize까지 진행해. commit, PR, push, deploy 같은 git action은 하지 말고 git action decision requested 상태에서 멈춰.
EOF
      ;;
  esac
}

finish_report() {
  local status="$?"
  set +e
  local latest_topic
  latest_topic="$(find_topic_dir)"
  collect_outputs "$latest_topic"
  write_report "$latest_topic"
  echo "[INFO] Report: $report_dir/report.md"
  exit "$status"
}

trap finish_report EXIT

set -e

echo "[INFO] Reloading $host AsUsual plugin"
run_logged "reload-$host" "$as_usual_repo/.agents/skills/turn-on-off-as-usual/scripts/as-usual-toggle.sh" reload "--$host" --repo "$as_usual_repo"

if [ "$host" = "claude" ] && [ "$claude_preflight" = "true" ]; then
  run_claude_preflight
fi

if [ "$preclean_sandbox" = "true" ]; then
  preclean_sandbox_repo
elif [ "$reset_sandbox" = "true" ] && [ -d "$sandbox_repo/.as-usual" ]; then
  echo "[INFO] Archiving existing sandbox .as-usual into report"
  copy_if_exists "$sandbox_repo/.as-usual" "$report_dir/logs/sandbox-snapshots/pre-run-dot-as-usual"
  pre_run_topic_archived="true"
  rm -rf "$sandbox_repo/.as-usual"
fi

run_logged "sandbox-status-before" git -C "$sandbox_repo" status --short --untracked-files=all
git -C "$sandbox_repo" status --short --untracked-files=all >"$report_dir/logs/artifacts/sandbox-status-before.txt" || true

git -C "$sandbox_repo" diff --stat >"$report_dir/logs/artifacts/sandbox-baseline-diff-stat.txt" || true
git -C "$sandbox_repo" diff >"$report_dir/logs/artifacts/sandbox-baseline.diff" || true
git -C "$sandbox_repo" ls-files --others --exclude-standard >"$report_dir/logs/artifacts/sandbox-untracked-before.txt" || true
if [ "$allow_dirty_baseline" != "true" ] && [ -s "$report_dir/logs/artifacts/sandbox-status-before.txt" ]; then
  echo "[ERROR] Sandbox started dirty. Re-run with --allow-dirty-baseline to preserve and classify baseline noise." >&2
  agent_failed="true"
  exit 1
fi

run_agent_step "01-start-topic" "$(scenario_start_prompt)"

topic_dir="$(find_topic_dir)"
if [ -n "$topic_dir" ]; then
  echo "[INFO] Topic dir: $topic_dir"
  fill_question_answers "$topic_dir"
else
  echo "[WARN] Topic dir not found after start step"
fi

run_agent_step "02-write-requirements" "$(scenario_requirements_prompt)"

run_agent_step "03-write-plan" "$(scenario_plan_prompt)"

run_agent_step "04-execute" "$(scenario_execute_prompt)"

run_agent_step "05-finalize" "$(scenario_finalize_prompt)"

topic_dir="$(find_topic_dir)"
collect_outputs "$topic_dir"
write_report "$topic_dir"
trap - EXIT

echo "[INFO] Sandbox E2E complete"
echo "[INFO] Report: $report_dir/report.md"
