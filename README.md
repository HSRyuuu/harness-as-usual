<div align="center">

<h1>AsUsual</h1>

<p><strong><em>Controlled</em> AI-assisted development — from requirements to tests to done, in one workflow.</strong></p>

<p>
  <img alt="version" src="https://img.shields.io/badge/version-0.1.0-2563EB?style=flat-square">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-2563EB?style=flat-square">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude_Code-ready-2563EB?style=flat-square&logo=anthropic&logoColor=white">
  <img alt="Codex" src="https://img.shields.io/badge/Codex-ready-2563EB?style=flat-square&logo=openai&logoColor=white">
  <img alt="surface" src="https://img.shields.io/badge/hooks-SessionStart-1E40AF?style=flat-square">
</p>

<p>
  <a href="#-install"><b>Install</b></a> ·
  <a href="#-why-asusual"><b>Why</b></a> ·
  <a href="#-how-it-works"><b>Workflow</b></a> ·
  <a href="#-topic-artifacts"><b>Artifacts</b></a>
</p>

</div>

---

<table>
<tr>
<td width="60" align="center">💡</td>
<td>
AsUsual is designed for <strong>controlled AI-assisted development</strong> on work that may eventually affect real, always-on production services. It is intentionally <em>not</em> a pure vibe-coding harness — it keeps topic-level decisions in files so the agent never has to guess your existing work style.
</td>
</tr>
</table>

> The harness succeeds when you can understand **what was decided, why, what changed, what was verified, what risk remains, and what action is still waiting.**
>
> See [`PROJECT_IDENTITY.md`](PROJECT_IDENTITY.md) for the full project identity and design principles.

<br>

## 🚀 Install

**Just paste this to your coding agent (Claude Code or Codex) — it does the rest:**

```text
This project, "AsUsual", is an agent harness for controlled AI-assisted development —
it moves one work topic through requirements → plan → execute → review → finalize.
Please install it for me on this machine:

  1. git clone https://github.com/HSRyuuu/harness-as-usual.git
  2. cd harness-as-usual && bash docs/INSTALL.sh
  3. Run the smoke test in docs/DEVELOPMENT.md, report the result,
     and tell me to restart my Claude Code / Codex session.
```

Prefer to do it by hand? Follow [`docs/INSTALL.md`](docs/INSTALL.md) — remove later with [`docs/UNINSTALL.md`](docs/UNINSTALL.md).

<table>
<tr><th align="left">Host</th><th align="left">Setup detail &amp; troubleshooting</th></tr>
<tr><td>🤖 <b>Claude Code</b></td><td><a href="docs/CLAUDE-PLUGIN-SETTING.md"><code>docs/CLAUDE-PLUGIN-SETTING.md</code></a></td></tr>
<tr><td>🧠 <b>Codex</b></td><td><a href="docs/CODEX-PLUGIN-SETTING.md"><code>docs/CODEX-PLUGIN-SETTING.md</code></a></td></tr>
</table>

<br>

## ✨ Why AsUsual

<table>
<thead>
<tr><th align="left">Guarantee</th><th align="left">What it prevents</th></tr>
</thead>
<tbody>
<tr><td>🛑 <strong>Stop before guessing</strong></td><td>Unclear intent is never silently turned into implementation — broad ambiguity goes through file-backed <code>define-requirements</code> questions.</td></tr>
<tr><td>📌 <strong>Durable decisions</strong></td><td>User decisions are preserved as topic artifacts on disk, not lost in chat memory.</td></tr>
<tr><td>🔌 <strong>Impact, surfaced early</strong></td><td>DB / API / external-behavior impact is exposed <em>before</em> code is written.</td></tr>
<tr><td>🔐 <strong>Explicit approval</strong></td><td>High-risk operations require fresh approval — appearing in an approved plan is not enough.</td></tr>
<tr><td>🧪 <strong>Evidence over optimism</strong></td><td>Verification evidence is recorded instead of relying on a hopeful "looks done" summary.</td></tr>
<tr><td>🔍 <strong>Review before finalize</strong></td><td>Actual changes are reviewed against recorded evidence before a topic is closed.</td></tr>
</tbody>
</table>

<sub>🌐 Language-neutral by design — AsUsual is not tied to any one stack, framework, or architecture, and it does <strong>not</strong> force the workflow onto every request just because the plugin is installed.</sub>

<br>

## 🔄 How It Works

The runtime workflow rules live in [`as-usual-rules/core-workflow.md`](as-usual-rules/core-workflow.md) — read by the agent on disk, **never copied into target projects**.

<div align="center">
<sub><code>SessionStart</code> → <code>using-as-usual</code> → <code>start-work</code> → <b>route</b> → <code>review-execution</code> → <code>finalize</code> → <code>git-action</code></sub>
</div>

Need to continue a topic from another session? Use <code>/as-usual:hand-off path</code> to rehydrate an existing topic and route back into the normal workflow.

<table>
<thead>
<tr><th align="center" width="48">#</th><th align="left" width="190">Stage</th><th align="left">What happens</th></tr>
</thead>
<tbody>
<tr><td align="center">1</td><td><code>define-requirements</code></td><td>Write <code>question-cN.md</code> only when material ambiguity exists; you answer in <code>[Answer]:</code> fields; the agent synthesizes a single <code>requirements.md</code>.</td></tr>
<tr><td align="center">2</td><td><code>writing-plan</code></td><td>Produce one <code>plan.md</code> from the approved requirements.</td></tr>
<tr><td align="center">3</td><td><code>executing-plan</code></td><td>Implement via <code>inline</code>, <code>subagent-driven</code>, or <code>mixed</code> mode (or <code>direct-execute</code> for trivial work); the main agent stays the controller for order, evidence, and completion claims.</td></tr>
<tr><td align="center">4</td><td><code>review-execution</code></td><td>Mandatory review of real changes against the recorded evidence.</td></tr>
<tr><td align="center">5</td><td><code>cleanup-code</code> &nbsp;<sub><i>optional</i></sub></td><td>User-approved code cleanup after review.</td></tr>
<tr><td align="center">6</td><td><code>finalize</code></td><td>Close the topic record.</td></tr>
<tr><td align="center">7</td><td><code>git-action</code> &nbsp;<sub><i>optional</i></sub></td><td>Pick a post-finalize git action — commit, push, PR, release, or deploy.</td></tr>
</tbody>
</table>

<sub>For the full architecture, stages, and prompt/template path map, see <a href="docs/ARCHITECTURE-WORKFLOW.md"><code>docs/ARCHITECTURE-WORKFLOW.md</code></a>.</sub>

<br>

## 📂 Topic Artifacts

AsUsual uses two branches inside `.as-usual/`: `topic/` for per-work-unit artifacts and `memory/` for curated cross-topic durable knowledge.

```text
.as-usual/
├── topic/
│   └── yyyy-MM-dd-<topic>/
│       ├── topic.md              # agent-first, low-churn resume document
│       ├── audit.jsonl           # canonical append-only event log
│       ├── question-c1.md        # define-requirements clarification cycle
│       ├── question-c2.md
│       ├── requirements.md       # single synthesized requirements doc
│       ├── plan.md               # single execution contract
│       ├── code-review-report.md
│       └── report.md
└── memory/
    ├── MEMORY.md                 # curated cross-topic knowledge; 3000-char budget
    └── *_MEMORY.md               # optional domain-specific memory files
```

> [!NOTE]
> `topic.md` is a low-churn resume document — not a task list. Current phase and next action are **derived** with `scripts/topic-log.py status --json`, not maintained by hand.

> [!NOTE]
> `topic/` artifacts are not committed by default. `.as-usual/memory/` is a commit target — it accumulates durable knowledge across topics and is updated at `finalize` by the `manage-self-improvement` skill.

<br>

<div align="center">
<sub><a href="docs/DEVELOPMENT.md">Development &amp; smoke test</a> · Built as an agent harness for <b>Claude Code</b> and <b>Codex</b> · Licensed under <a href="https://github.com/HSRyuuu/harness-as-usual">MIT</a></sub>
</div>
