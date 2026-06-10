# Host surfaces — KEEL's host-neutral process vocabulary

KEEL's agent-facing content — the agent masters, the skills, and
`KEEL-CONTRACT.md` — is **host-neutral by design**. It names *process
verbs* ("dispatch a subagent", "the project guide", "the high-reasoning
tier"), not one agent host's API. The canonical content is therefore not
coupled to one host's mechanics — each process verb resolves to whatever
mechanism the running host provides (mapped below).

This file is the canonical glossary of those process verbs and how each
maps to the concrete mechanism a host provides. Agent masters and skills
**use the neutral verb** and link here once (P4) rather than restating a
host mechanism inline.

**Authority (P6).** Canonical install paths and the on-disk layout are
owned by `scripts/keel_manifest.py`. This file describes *meaning and
mechanism*, never path constants — duplicating a path string here would be
a cache that stales (P4). Where a verb resolves to a path, the manifest
is the source of truth.

## Supported hosts

| Host | Entry point | Agent masters | Skills |
|-|-|-|-|
| Claude Code | `CLAUDE.md` → `@AGENTS.md` (content root) | `.claude/agents/<role>.md` (resident) | `.claude/skills/<name>/SKILL.md` |
| Codex CLI | `AGENTS.md` (repo root, native) | `.keel/agents/<role>.md` (injected/read per spawn) | `.agents/skills/<name>/SKILL.md` |

## Process verbs → host mechanism

| KEEL process verb | What the neutral phrasing means | Claude Code mechanism | Codex CLI mechanism |
|-|-|-|-|
| **Dispatch a subagent** (`dispatch a subagent named <role>`) | Hand a scoped task to a fresh agent operating under role `<role>`'s contract | Orchestrator calls the Task tool with `subagent_type: <role>`; the host loads `.claude/agents/<role>.md` as the subagent's resident system prompt | Orchestrator spawns a generic worker (Codex binds no named agent); the spawn message opens with `[KEEL-ROLE <role>]`, the `keel-role-injector` SubagentStart hook recovers `<role>` and injects the master, else the worker reads it. See [§Subagent dispatch](#subagent-dispatch--the-keel-role-preamble) |
| **The role contract** (`your role contract`, `the master for <role>`) | The full instructions an agent operates under | Resident — the host loads the master automatically as the subagent's system prompt; the subagent does not re-read it | Delivered per spawn: the injector hook places `.keel/agents/<role>.md` as a developer message, or the in-message pointer triggers a blocking read. Never resident (workers are generic) |
| **The project guide** (`the project guide`) | The per-project file holding domain invariants, gate/test commands, review policy, and KEEL knobs | `AGENTS.md` at the repo root (the host-neutral content root, read verbatim by any host); it `@`-imports `.keel/KEEL-CONTRACT.md`. Claude Code auto-loads `CLAUDE.md`, which ships as a thin `@AGENTS.md` pointer. See [the project-guide locator](#the-project-guide-locator) | `AGENTS.md` at the repo root (Codex's native instructions file). No `@`-transclusion — AGENTS.md instructs a first-action read of `.keel/KEEL-CONTRACT.md` |
| **The gate command** (`the gate command configured in the project guide`) | The project's tests / build / lint that must pass for work to land | Read from the project guide (above); no host-specific mechanism of its own | Same — read from the project guide |
| **Reasoning tier** (`the standard tier`, `the high-reasoning tier`) | Per-agent reasoning effort, chosen by task criticality | Bound by the `model:` frontmatter (high → Opus, standard → Sonnet) plus an inline `# reasoning:` note. See [reasoning tiers](#reasoning-tiers) | Advisory only — a spawned worker inherits the session model + `model_reasoning_effort`; `model:` / `# reasoning:` survive as text but do not bind (the documented loss). Concurrency is set in `.codex/config.toml` (`agents.max_threads`, `max_depth`) |
| **Persisted runtime state** (`under .keel/`) | Worktrees, opt-in timing, the install receipt, the bundled uninstaller — KEEL's own machinery and state | `.keel/` (host-neutral home). Host-mandated surfaces stay host-side: agent/skill dirs above, hooks registered in `.claude/settings.json` | Same `.keel/` home. The generated host surface is `.codex/` (hooks.json, config.toml) + per-skill `.agents/skills/<name>/agents/openai.yaml`; no settings.json |
| **Hooks** (`KEEL's hook scripts under .keel/hooks/`) | Safety gate, doc gate, opt-in timing | Registered in `.claude/settings.json`; fire on tool-use lifecycle events. Scripts are host-neutral and live at `.keel/hooks/` | Registered in `.codex/hooks.json` (generated). The gates are dual-payload; the codex-only `keel-role-injector` runs on SubagentStart + SessionStart. No timing hook (Codex skips async handlers) |
| **Image input** (`your host's image input (where supported)`) | Read image/PDF design assets visually (PNG/JPG/GIF/SVG/PDF); other formats read as text source | Claude vision, via the `Read` tool — the listed formats render visually | The host's native image input where supported; otherwise the asset reads as text source |
| **Ask the human** (`ask the human`, `HALT and ask`) | Surface a decision the human must make | Present a structured question (AskUserQuestion) or an inline prompt | An inline prompt (Codex has no structured-question tool) |
| **Halt with a call-to-action** (`HALT (P7) with a concrete next step`) | Stop, name the exact cause, emit one actionable next step | Host-neutral. When the CTA references project config, it names **the project guide**, never a host filename | Host-neutral (identical) |

## The project-guide locator

Several shipped readers need the project guide — not just as an entry-point
filename, but because they read it for domain invariants, the gate command,
and review policy (`validate-binder-json.py`, the safety tooling, the
pipeline skills). The project guide **content** is the same file on every
host:

- **`AGENTS.md` at the repo root** — the host-neutral content root, preferred
  by every reader.
- **`CLAUDE.md`** — Claude Code's native auto-load file; on KEEL installs it is
  a thin `@AGENTS.md` pointer. Readers fall back to it only for a repo that
  keeps its rules in `CLAUDE.md` directly.

No shipped script may hardcode a single filename; each resolves the guide
through this locator (AGENTS.md preferred, CLAUDE.md fallback) so one rule
governs every reader.

## The master-directory locator

The agent masters install to a per-host directory (see the
[Supported hosts](#supported-hosts) table): `.claude/agents/` on Claude Code
(resident system prompts), `.keel/agents/` on Codex (injected or read per
spawn). An install is single-host, so exactly one of these directories holds
the masters.

A skill that **edits** masters — the onboarding ceremonies (`/keel-setup`,
`/keel-adopt`) fill each agent's `<!-- CUSTOMIZE -->` blanks — resolves the
directory **by presence**: use whichever of `.claude/agents/` or
`.keel/agents/` is present, and treat every agent path as
`<that dir>/<role>.md`. This is the onboarding ceremonies' single host-variant;
their other paths (the project guide, `.keel/hooks/keel-safety-gate.py`,
`docs/...`) are already host-neutral. The role-injector hook — the only other
resolver (§5.7 of the Codex design) — is Codex-only and uses `.keel/agents/`
unconditionally. No reader hardcodes a single agent directory.

## Reasoning tiers

KEEL assigns each agent one of two reasoning tiers by task criticality:

- **standard** — pattern-matching, verification, template execution, config
  generation.
- **high-reasoning** — architecture and design decisions, decomposition,
  adversarial review, accuracy-critical gates.

The canonical per-agent tier assignments and the escalation rules
(pretriage `recommended_model`, self-escalation, always-high agents) live
in [`HANDOFF-CONTRACT.md`](HANDOFF-CONTRACT.md) — that file is authoritative;
this section only names the vocabulary.

On Claude Code the tier binds through the `model:` frontmatter (high →
Opus, standard → Sonnet); the orchestrator may override `model:` per
dispatch when pretriage recommends the high tier, and an agent may
self-escalate. The structured `recommended_model` field in
`resolved-work-item.json` carries the orchestrator's tier recommendation.

On Codex the tier does **not** bind: a spawned worker inherits the session's
model and `model_reasoning_effort`, so `model:` and the `# reasoning:` note
survive as advisory text only (the documented loss). The vocabulary and the
`recommended_model` routing field are unchanged — they just don't drive a
per-agent model swap on Codex.

## Subagent dispatch — the KEEL-ROLE preamble

A dispatched subagent must operate under its role's contract. How that contract
reaches it differs per host: Claude Code loads the master as the subagent's
resident system prompt; Codex spawns a generic worker with no role identity, so
KEEL's role-injector hook delivers the contract (or, when the hook is inactive
or the master is over budget, the subagent reads it). To make every KEEL skill's
dispatch work identically on both hosts, **every spawn message a KEEL skill
constructs OPENS with the KEEL-ROLE preamble** — substitute `<role>` with the
exact name of the agent being dispatched (which must be an installed master):

```
[KEEL-ROLE <role>] Operate as the `<role>` role. Acquire your role contract by
the FIRST route that applies, then carry out the task that follows:
1. RESIDENT — your system prompt already identifies you as the `<role>` agent
   and contains its contract (your host loaded the master as your system
   prompt): you have it — proceed, do not re-read.
2. INJECTED — your context contains a line starting with `[KEEL-ROLE-INJECTED
   <role> complete=true`: that injected text IS your complete contract — do not
   re-read.
3. POINTER — neither applies: execute a BLOCKING READ of `.keel/agents/<role>.md`
   in full and follow it as your complete contract; if it cannot be read in
   full, STOP and report. Never improvise the role.
```

This is **load-bearing and host-agnostic**: route 1 makes it a clean no-op on
Claude Code (the master is already resident), route 2 consumes the injector's
delivery on Codex, and route 3 is the behavioral safety net when injection is
inactive or the master exceeds the hook's output budget. The `[KEEL-ROLE <role>]`
tag is also what the Codex role-injector recovers to know which master to
inject. A skill that dispatches without this preamble fails silently on Codex —
so it is gated by `validate-dispatch-tags.py`, not trusted.
