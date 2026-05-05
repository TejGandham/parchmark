# KEEL Pipeline Doctrine

This document is the canonical statement of two pipeline contracts that
KEEL agents and skills cite by name:

1. The shape of feature input the pipeline accepts.
2. The autonomy ceiling — what KEEL does on its own and what stays with the human.

Both contracts are enforced operationally by skill behavior and validators
in this install. This file is the prose source of truth that those agents
and skills point at when they need a name to cite.

This file ships unchanged in every install. Do not edit it locally — fork
KEEL if you need to change pipeline doctrine.

## Feature input canon — single path, JSON PRDs only

The KEEL pipeline accepts **one shape** of feature input: a structured
JSON PRD at `docs/exec-plans/prds/<slug>.json` validated against
`schemas/prd.schema.json`. Every pipeline agent — `pre-check`,
`test-writer`, `spec-reviewer`, `safety-auditor`, `backlog-drafter`,
`doc-gardener` — reads JSON fields directly via `jq`. There is no
markdown-PRD path, no legacy-spec path, no second pipeline that walks a
different artifact shape.

Structured PRDs are a KEEL-internal artifact. Agents generate them
(`/keel-refine`), agents read them, and a synthesizer can render them to
markdown for human reading on demand. Humans do not author the JSON by
hand.

Any non-JSON input is **raw material for `/keel-refine`**, not pipeline
input. Markdown specs, prose descriptions, PRDs from other systems,
bundles with wireframes, images — all feed into `/keel-refine`, which is
the conversion hub. `/keel-refine` produces a structured JSON PRD;
`/keel-pipeline` reads only that JSON.

Direct consequences:

- `/keel-pipeline F## <prd-path>` expects `<prd-path>` to end in
  `.json`. A `.md` path is a routing error — halt with a CTA to run
  `/keel-refine` first. The halt message in
  `.claude/skills/keel-pipeline/SKILL.md` cites this section.
- Agent prompts do not contain dispatch logic on backlog fields to
  select between JSON and markdown reading. There is one reading path.
- Features predating structured PRDs (`PRD-exempt:` entries,
  pre-invariant-7 grandfathered entries) do not flow through
  `/keel-pipeline` as markdown. They are migrated via `/keel-refine`
  before the pipeline sees them, or they run outside the pipeline.
- `validate-prds.py` enforces invariant 7 on the backlog (`PRD: <slug>`
  link integrity). The `<slug>.json` file the link points at is the
  only artifact `/keel-pipeline` reads.

The structural contract lives in `schemas/prd.schema.json`. The single
dispatch path lives in `.claude/agents/pre-check.md`. The conversion-hub
behavior lives in `.claude/skills/keel-refine/SKILL.md`.

## Autonomy Ceiling

The end state KEEL aims for: human feeds a feature spec (or a PRD that
`/keel-refine` turns into draft backlog entries the human edits into
specs); KEEL produces a PR.

| What KEEL does autonomously | What the human does |
|-|-|
| Pick pipeline variant based on intent | Write the PRD or edit from a `/keel-refine` draft; author each feature spec |
| Route to optional agents | Define domain invariants |
| Self-correct on spec deviation (max 2) | Resolve escalations |
| Self-correct on safety violation (max 3) | Update north star / specs |
| Self-correct on architecture issues (max 1) | Review and merge the PR |
| Garbage collect docs after landing | |
| Commit, push, open PR for every feature | |
| Roundtable review when available | |

What KEEL does **not** do autonomously:

- Pick the next feature from the backlog (human decides priority).
- Modify specs or invariants (human decides what to build).
- Merge the PR (human reviews on their forge).

`/keel-refine` is the **PRD-scope gate** and **conversion hub** — not
an expansion of this ceiling. Given prose, legacy markdown, a bundle
directory, or images, it drafts F## entries linked to a new or existing
structured JSON PRD file (`docs/exec-plans/prds/<slug>.json`), reviews
each card conversationally with the human, and commits only when the
human types `commit`. The skill performs the `git add` + `git commit`
on that verb with a deterministic message. The human steers via Q&A;
`/keel-refine` writes the JSON and the backlog entry. Invariant 7
enforces that every F## traces back to a PRD (or declares
`PRD-exempt: <reason>`).

Per-card review is non-negotiable. There is no block-review escape
hatch and no "accept all" shortcut in `/keel-refine` Phase 5. Accuracy
over speed; this is the load-bearing reason `/keel-refine` is the only
agent in the pipeline that walks every drafted artifact individually
before commit.
