<div align="center">

<h1>AsUsual</h1>

<p><strong><em>Controlled</em> AI-assisted development — from requirements to tests to done, in one workflow.</strong></p>

<p>
  <img alt="version" src="https://img.shields.io/badge/version-0.1.1-2563EB?style=flat-square">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-2563EB?style=flat-square">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude_Code-ready-2563EB?style=flat-square&logo=anthropic&logoColor=white">
  <img alt="Codex" src="https://img.shields.io/badge/Codex-ready-2563EB?style=flat-square&logo=openai&logoColor=white">
  <img alt="surface" src="https://img.shields.io/badge/hooks-SessionStart-1E40AF?style=flat-square">
</p>

<p>
  <a href="#-install"><b>Install</b></a> ·
  <a href="#-why-asusual"><b>Why</b></a> ·
  <a href="#-how-it-works"><b>Workflow</b></a> ·
  <a href="#-work-unit-artifacts"><b>Artifacts</b></a>
</p>

</div>

---

<table>
<tr>
<td width="60" align="center">💡</td>
<td>
AsUsual is designed for <strong>controlled AI-assisted development</strong> on work that may eventually affect real, always-on production services. It is intentionally <em>not</em> a pure vibe-coding harness — it keeps coding-topic decisions and find-cause investigation evidence in files so the agent never has to guess your existing work style.
</td>
</tr>
</table>

> The harness succeeds when you can understand **what was decided, why, what changed, what was verified, what risk remains, and what action is still waiting.**
>
> See [`PROJECT_IDENTITY.md`](PROJECT_IDENTITY.md) for the full project identity and design principles.

<br>

## 🚀 Install

Marketplace name: `harness-as-usual` · plugin id: `as-usual@harness-as-usual`.

**Claude Code** — paste these commands into Claude Code:

```text
/plugin marketplace add HSRyuuu/harness-as-usual
/plugin install as-usual@harness-as-usual
```

**Codex** — run these commands in a terminal:

```bash
codex plugin marketplace add HSRyuuu/harness-as-usual
codex plugin add as-usual@harness-as-usual
```

Both hosts cache installed plugins. Start a new session after installation. For a GitHub-installed plugin update, run:

```bash
claude plugin marketplace update harness-as-usual
claude plugin update as-usual@harness-as-usual
codex plugin marketplace upgrade harness-as-usual
```

Maintaining AsUsual from a local clone? Use the local-directory flow in [`docs/INSTALL.md`](docs/INSTALL.md). Do not register both the GitHub and local-directory source on one machine under different marketplace names; that loads the same plugin twice.

**Or paste this to your coding agent:**

```text
This project, "AsUsual", is an agent harness for controlled AI-assisted development —
it moves one work topic through requirements → plan → execute → review → finalize.
Install it from the HSRyuuu/harness-as-usual marketplace for Claude Code and Codex.
Use plugin id as-usual@harness-as-usual, verify both plugin lists, and tell me to
start new sessions after installation.
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

AsUsual has two parallel runtime work units, both read by the agent on disk and **never copied into target projects**:

- Coding `topic`: [`as-usual-rules/core-workflow.md`](as-usual-rules/core-workflow.md) for requirements → plan → implementation → review → finalize.
- Find-cause `issue`: [`as-usual-rules/find-cause-workflow.md`](as-usual-rules/find-cause-workflow.md) for evidence-backed root-cause or solution-direction investigation without production-code changes.

<div align="center">
<sub><code>SessionStart</code> → <code>using-as-usual</code> → <code>start-work</code> → <b>route</b> → <code>review-execution</code> → <code>finalize</code> → <code>git-action</code></sub>
</div>

Need to continue a topic or issue from another session? Use <code>/as-usual:hand-off path</code> to rehydrate it and route back to its current owner.

<table>
<thead>
<tr><th align="center" width="48">#</th><th align="left" width="190">Stage</th><th align="left">What happens</th></tr>
</thead>
<tbody>
<tr><td align="center">1</td><td><code>define-requirements</code></td><td>Write <code>question-cN.md</code> only when material ambiguity exists; you answer in <code>[Answer]:</code> fields, or in chat — the agent then confirms a question-to-answer mapping table with you before writing the file; the agent synthesizes a single <code>requirements.md</code>.</td></tr>
<tr><td align="center">2</td><td><code>writing-plan</code></td><td>Produce one <code>plan.md</code> from the approved requirements.</td></tr>
<tr><td align="center">3</td><td><code>executing-plan</code></td><td>Implement via <code>inline</code>, <code>subagent-driven</code>, or <code>mixed</code> mode; trivial work can use the <code>direct-execute</code> skill, including its recordless direct invocation. The main agent stays the controller for order, evidence, and completion claims.</td></tr>
<tr><td align="center">4</td><td><code>review-execution</code></td><td>Mandatory review of real changes against the recorded evidence.</td></tr>
<tr><td align="center">5</td><td><code>cleanup-code</code> &nbsp;<sub><i>optional</i></sub></td><td>User-approved code cleanup after review.</td></tr>
<tr><td align="center">6</td><td><code>finalize</code></td><td>Close the topic record.</td></tr>
<tr><td align="center">7</td><td><code>git-action</code> &nbsp;<sub><i>optional</i></sub></td><td>Pick a post-finalize git action — commit, push, PR, release, or deploy.</td></tr>
</tbody>
</table>

<sub>For the full architecture, stages, and prompt/template path map, see <a href="docs/ARCHITECTURE-WORKFLOW.md"><code>docs/ARCHITECTURE-WORKFLOW.md</code></a>.</sub>

<br>

## 📂 Work-Unit Artifacts

AsUsual uses three branches inside `.as-usual/`: `topic/` for coding work, `issue/` for find-cause investigations, and `memory/` for curated cross-topic durable knowledge.

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
│       ├── execute/
│       │   ├── task-<N>-requirements-review.md
│       │   └── task-<N>-quality-review.md
│       ├── clean-up/
│       │   └── review-result-<type>.md
│       ├── code-review-report.md
│       └── report.md
├── issue/
│   └── yyyy-MM-dd-<slug>/
│       ├── problem.md             # living investigation snapshot
│       ├── journal.jsonl          # append-only reasoning and lifecycle log
│       ├── evidence/              # optional captured evidence
│       └── conclusion.md          # confirmed result and provenance
└── memory/
    ├── MEMORY.md                 # curated cross-topic knowledge; 3000-char budget
    └── *_MEMORY.md               # optional domain-specific memory files
```

> [!NOTE]
> `topic.md` is a low-churn resume document — not a task list. Current phase and next action are **derived** with `scripts/topic-log.py status --json`, not maintained by hand.

> [!NOTE]
> `topic/` artifacts are not committed by default. `.as-usual/memory/` is a commit target — it accumulates durable knowledge across topics and is updated at `finalize` by the `manage-self-improvement` skill.

> [!NOTE]
> `issue/` artifacts are also not committed by default. A concluded issue can link a separate coding topic through `scripts/journal-log.py link-follow-up`.

<br>

<div align="center">
<sub><a href="docs/DEVELOPMENT.md">Development &amp; smoke test</a> · Built as an agent harness for <b>Claude Code</b> and <b>Codex</b> · Licensed under <a href="https://github.com/HSRyuuu/harness-as-usual">MIT</a></sub>
</div>
