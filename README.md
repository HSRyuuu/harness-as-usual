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
AsUsual is designed for <strong>controlled AI-assisted development</strong> on work that may eventually affect real, always-on production services. It is intentionally <em>not</em> a pure vibe-coding harness — it keeps decisions and evidence in files so the agent never has to guess your existing work style.
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
<tr><td>🛑 <strong>Stop before guessing</strong></td><td>Unclear intent is never silently turned into implementation — it goes through <code>gathering-context</code>, and every agreed decision is written down.</td></tr>
<tr><td>📌 <strong>Durable decisions</strong></td><td>User decisions are preserved as topic artifacts on disk, not lost in chat memory.</td></tr>
<tr><td>🔌 <strong>Impact, surfaced early</strong></td><td>DB / API / external-behavior impact is exposed <em>before</em> code is written.</td></tr>
<tr><td>🔐 <strong>Explicit approval</strong></td><td>High-risk operations require fresh approval — appearing in an approved plan is not enough.</td></tr>
<tr><td>🧪 <strong>Evidence over optimism</strong></td><td>Verification evidence is recorded instead of relying on a hopeful "looks done" summary.</td></tr>
<tr><td>🔍 <strong>Review the diff, not the summary</strong></td><td>What was actually built is reviewed against what was asked, before the work closes.</td></tr>
</tbody>
</table>

<sub>🌐 Language-neutral by design — AsUsual is not tied to any one stack, framework, or architecture, and it does <strong>not</strong> force the workflow onto every request just because the plugin is installed.</sub>

<br>

## 🔄 How It Works

Every request that AsUsual picks up is classified once, at the door, into one of
three **peer work units**. They are not stages of one pipeline — they are
different kinds of work, each with its own shape.

<div align="center">
<sub><code>SessionStart</code> → <code>using-as-usual</code> → <b>classify</b> → <code>run-topic</code> | <code>run-direct-work</code> | <code>run-issue</code></sub>
</div>

<table>
<thead>
<tr><th align="left" width="150">Unit</th><th align="left">The work is</th><th align="left" width="230">Ends with</th></tr>
</thead>
<tbody>
<tr><td><code>topic</code></td><td>development that needs the requirements agreed first</td><td>code change + <code>report.md</code></td></tr>
<tr><td><code>direct-work</code></td><td>development where what to do is already settled</td><td>code change + verification record</td></tr>
<tr><td><code>issue</code></td><td>confirming a cause or direction <strong>without changing code</strong></td><td><code>conclusion.md</code></td></tr>
</tbody>
</table>

The agent classifies and recommends, then shows you all the options — including
**"just do it"**, which uses no harness and records nothing. You pick; it does not
argue. Ask to resume anything and `using-as-usual` finds it, whether this session
started it or another one did.

The runtime rules live in [`as-usual-rules/core-rules.md`](as-usual-rules/core-rules.md)
and are read from disk by the agent — **never copied into your project**.

<table>
<thead>
<tr><th align="center" width="48">#</th><th align="left" width="200">Stage</th><th align="left">What happens</th></tr>
</thead>
<tbody>
<tr><td align="center">1</td><td><code>gathering-context</code></td><td>The agent interviews you — recommending an answer with every question, batching independent facts, asking judgment calls one at a time. Answers are written down for you, never typed into a form. Zero questions is a normal outcome when nothing is open.</td></tr>
<tr><td align="center">2</td><td><code>write-requirements</code> &nbsp;<sub><i>topic only</i></sub></td><td>The agreed context becomes one <code>requirements.md</code> — outcomes, not tasks.</td></tr>
<tr><td align="center">3</td><td><code>write-plan</code></td><td>One <code>plan.md</code> (a checklist for <code>direct-work</code>), then <strong>critically reviewed and fixed before you are asked to approve it</strong>.</td></tr>
<tr><td align="center">4</td><td><code>execute-plan</code></td><td>The plan is executed and each task's verification evidence recorded. Delegation and test strategy are the agent's call; the evidence is not optional.</td></tr>
<tr><td align="center">5</td><td><code>review-execution</code></td><td>The real diff is reviewed — not the summary of it. Findings land in <code>review.md</code> and reach a disposition before the work closes.</td></tr>
<tr><td align="center">6</td><td><code>cleanup-code</code> &nbsp;<sub><i>optional</i></sub></td><td>Approved, behavior-preserving cleanup, re-verified.</td></tr>
<tr><td align="center">7</td><td><code>finalize</code></td><td>Memory pass, <code>report.md</code>, and the record is sealed.</td></tr>
<tr><td align="center">8</td><td><code>git-action</code> &nbsp;<sub><i>on request</i></sub></td><td>Only the git action you explicitly chose — never one you did not.</td></tr>
</tbody>
</table>

An `issue` runs a different middle: an investigation loop of hypotheses,
evidence, and confirmations that can be retracted when later evidence contradicts
them — ending in a `conclusion.md` that cites what established each claim.

<sub>For the full architecture, stages, and prompt/template path map, see <a href="docs/ARCHITECTURE-WORKFLOW.md"><code>docs/ARCHITECTURE-WORKFLOW.md</code></a>.</sub>

<br>

## 📂 Work-Unit Artifacts

Each unit gets its own branch inside `.as-usual/`. Two files are common to all
three; the rest depends on the unit.

```text
.as-usual/
├── inbox/                        # unit not chosen yet — moved out once it is
│   └── yyyy-MM-dd-<slug>/
│       ├── contexts.md
│       └── audit.jsonl
├── topic/
│   └── yyyy-MM-dd-<slug>/
│       ├── contexts.md           # every agreed decision, whenever it was made
│       ├── audit.jsonl           # append-only evidence trail
│       ├── requirements.md
│       ├── plan.md
│       ├── review.md
│       └── report.md
├── direct-work/
│   └── yyyy-MM-dd-<slug>/
│       ├── contexts.md
│       ├── audit.jsonl
│       └── plan.md               # checklist strength
├── issue/
│   └── yyyy-MM-dd-<slug>/
│       ├── contexts.md           # also the living investigation snapshot
│       ├── audit.jsonl
│       ├── evidence/
│       └── conclusion.md
└── memory/
    ├── MEMORY.md                 # curated cross-unit knowledge; 3000-char budget
    └── *_MEMORY.md               # optional domain-specific memory files
```

> [!NOTE]
> `contexts.md` has three bands: a near-fixed header, a **freely updated** decision
> section — when a later decision reverses an earlier one, the earlier entry is
> edited so it always reads as the current agreement — and an **append-only** Q&A
> log. Nothing is lost by editing: `audit.jsonl` keeps the history.

> [!NOTE]
> Current phase and next action are **derived** with
> `scripts/as-usual-record.py status --json`, never maintained by hand. That script
> is the only writer of `audit.jsonl`, and it refuses rather than warns — no verdict
> on a verification, no execution approval without a plan review, no move once the
> unit has produced its own output.

> [!NOTE]
> Work-unit artifacts are not committed by default. `.as-usual/memory/` is a commit
> target — it accumulates durable knowledge across units and is updated at `finalize`
> by the `manage-self-improvement` skill.

> [!NOTE]
> A concluded `issue` does not become the follow-up implementation — it links to a
> new `topic` or `direct-work` unit through `scripts/as-usual-record.py link`, in
> both directions.

<br>

<div align="center">
<sub><a href="docs/DEVELOPMENT.md">Development &amp; smoke test</a> · Built as an agent harness for <b>Claude Code</b> and <b>Codex</b> · Licensed under <a href="https://github.com/HSRyuuu/harness-as-usual">MIT</a></sub>
</div>
