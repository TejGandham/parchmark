# The KEEL Process Guide

**KEEL -- Knowledge-Encoded Engineering Lifecycle**

A structured process for agent-driven software development where humans steer
and agents execute through specialized pipelines.

Adapted from OpenAI's "Harness Engineering" article (February 2026, Ryan
Lopopolo), where a team shipped a product with zero manually-written code
using Codex agents. KEEL adapts those principles into concrete, repeatable
mechanics that any supported agent host can run.

> All decisions below are anchored to the seven KEEL framework
> principles at [`KEEL-PRINCIPLES.md`](KEEL-PRINCIPLES.md).

---

## What is KEEL?

KEEL is a lifecycle for building software with AI agents as the primary
implementers. The three words in the name each carry weight:

**Knowledge-Encoded.** The repository is truth. Docs drive code. Everything the
agent needs is committed as versioned artifacts -- specs, plans, architecture
docs, testing strategies, handoff files. If it is not in the repo, it does not
exist to the agent. External knowledge (Google Docs, Slack threads, verbal
decisions, tacit expertise) is invisible until someone encodes it as a markdown
file and commits it.

**Engineering.** This is not prompt engineering. It is a structured engineering
process with specialized agents, pipelines, testing doctrine, and mechanical
enforcement. Agents have defined roles, bounded responsibilities, and explicit
inputs and outputs. Quality is enforced by structure, not by hoping the model
gets it right.

**Lifecycle.** KEEL covers the build arc from vision to landed feature:

```
north star --> spec --> backlog --> pipeline --> landed feature --> garbage collection
```

Every phase produces versioned artifacts. Every artifact feeds the next phase.
The repo accumulates institutional knowledge that compounds over time.

**Scope boundary:** KEEL's coverage ends at the git commit. It ensures the code
entering your CI/CD pipeline is spec-conformant, tested, and safe. It does not
cover deployment, infrastructure, monitoring, or incident response — those are
downstream concerns that take over where KEEL leaves off.

### Where KEEL Came From

The name comes from a ship's [keel](https://en.wikipedia.org/wiki/Keel) —
the structural spine laid down first, before any hull goes on top. Lay it
straight and the ship holds. Same idea here: encode the structure, and
every feature built on top inherits it.

In February 2026, Ryan Lopopolo's team at OpenAI published "Harness
Engineering" describing how they shipped a product with Codex agents writing
all the code. Their key insight: the repository must be the complete system of
record for agent work. Docs written for agent legibility. Mechanical
enforcement of invariants. Progressive disclosure of context. Background agents
for garbage collection.

KEEL takes those principles and makes them operational for your agent host: concrete
file structures, named agent roles, pipeline definitions, handoff formats,
testing layers, and a commit ritual that keeps the repo honest.

---

## 1. Philosophy and Principles

Six core beliefs govern every decision in a KEEL project. Each one
operationalizes a principle from the OpenAI article.

| KEEL Belief | OpenAI Principle | What It Means |
|---|---|---|
| Repo is truth | Repository as system of record | If it is not committed, it does not exist to agents |
| Docs drive code | Agent legibility is the goal | Specs written for agent comprehension, not humans |
| Coding comes last | Spec-first workflow | Spec, then test, then code, then verify. Always. |
| Progressive disclosure | Map not manual | the project guide is ~80 lines as table of contents; knowledge lives in docs/ |
| Smallest testable units | Depth-first bootstrap | Break goals into building blocks; use them to unlock complexity |
| Garbage collect | Entropy management | Golden principles, recurring cleanup, fix doc lies immediately |

### The Knowledge Boundary Principle

Anything the agent cannot see does not exist. Your agent host reads files from
the repository. It does not read Google Docs, hear Slack conversations, or
know what you decided over lunch. The only way to make external knowledge
visible: encode it as a versioned markdown artifact in the repo.

This is the foundational principle. Everything else in KEEL follows from it.

### Who KEEL Is For

- Solo developers or small teams (1-3 people) using an AI agent as primary implementer
- Projects that grow organically — where today's 3 features become next month's 30
- Long-lived projects where institutional knowledge must compound, not evaporate
- Projects where safety invariants must be mechanically enforced
- A supported agent host as the runtime

### When KEEL Is Right

- Multi-feature projects that will grow in scope over time
- Agent-driven development (agent writes the code, human steers)
- Projects where a single rules file (AGENTS.md, .cursorrules) has stopped scaling
- Projects where correctness, spec conformance, and safety matter

### When KEEL Is Overkill

- One-off scripts or quick fixes (just write the code)
- Tight human feedback loops where you are pair-programming with the agent
- Throwaway prototypes you will discard next week
- Projects with fewer than 5 planned features

If a feature feels too heavy for full rigor but you still want a gated, recorded
build — not an ungated hack — use the **lean Karta lane** instead of abandoning
KEEL (see §8, "Agent Roles and Pipelines", and `docs/process/KARTA-LANE.md`).

### The Human-Steers / Agent-Executes Contract

The human decides what to build, in what order, and whether the result is
acceptable. The human writes the north star, approves specs, kicks off
pipeline stages, reviews output, commits code, and updates the backlog.

The agent reads specs, writes tests, writes code, reviews its own work, and
reports results. The agent never decides what to build next.

After `landing-verifier` reports VERIFIED, the orchestrator runs the
landing review (always — the review panel is the default) and a
deterministic completion procedure — doc-gardener, tech-debt log, backlog
tick + commit, and handoff archive — without per-step approval. Completion
is repo-local: the feature commit, the archived handoff, and the backlog
`[x]`. Pushing to a remote and opening a PR are a separate, human-invoked
`/keel-submit` step for forge users. Escalations (gate ceilings tripped)
halt in-session and surface to the human immediately.

The human provides taste, judgment, and strategic direction. The agent provides
speed, consistency, and tireless attention to spec conformance.

---

## 2. The Knowledge Boundary

The "K" in KEEL deserves its own section because it is the hardest principle
to internalize and the easiest to violate.

```
+-------------------------------+
|    What the agent CAN see     |
|  Code, markdown, schemas,     |
|  exec plans, tests, configs,  |
|  handoff files, AGENTS.md     |
+-------------------------------+
        ^ must encode ^
+-------------------------------+
|   What the agent CAN'T see    |
|  Slack, verbal decisions,     |
|  your head, Google Docs,      |
|  meeting notes, email threads |
+-------------------------------+
```

### Common Knowledge Boundary Violations

| Violation | Symptom | Fix |
|---|---|---|
| Decision made in conversation, not committed | Agent contradicts it next session | Add to relevant spec or design doc |
| Architectural preference in your head | Agent makes a different choice | Write it in core-beliefs.md |
| "Everyone knows" convention | Agent does not know it | Add to the project guide or a referenced doc |
| Spec change discussed but not written down | Agent implements the old spec | Update the spec file first |
| External API behavior learned from docs site | Agent guesses wrong | Add API contract to a reference doc |

Every time you catch yourself saying "the agent should know that," stop and
ask: is it in the repo? If not, it does not exist. Knowledge compounds when
committed. Knowledge evaporates when verbal.

---

## 3. Creating Your North Star

The north star document (`NORTH-STAR.md`, at the project root) encodes the project's vision,
growth stages, operating principles, and definition of success.

### What Goes in the North Star

- **Vision.** What you are building and why. Concrete enough that an agent can
  evaluate whether a design decision aligns with it.
- **Operating principles.** What you adopt fully, what you adapt, what you skip.
  "What we skip" prevents the agent from gold-plating.
- **Growth stages.** A table mapping project maturity to KEEL additions.
- **The four loops.** Validation (write/test/fix), knowledge boundary, layered
  architecture, garbage collection.

### North Star and the project guide

The north star encodes taste before it becomes linters. It answers "how should
this project feel?" while the project guide answers "how is this project structured?"

The project guide points to the north star. Agents read the project guide first, then follow
the pointer when they need to make judgment calls.

---

## 4. Bootstrapping the Repo

From empty directory to first passing test.

### Step-by-Step Bootstrap

```
1. Create directory structure
2. Write north star               (NORTH-STAR.md)
3. Write the project guide        (~80-100 lines, table of contents)
4. Produce product Binders via       (/keel-refine → docs/exec-plans/binders/<slug>.json)
   /keel-refine                   (conversion hub — accepts prose, markdown, bundles, images; emits JSON)
5. Write core beliefs             (docs/design-docs/core-beliefs.md)
6. Write testing strategy         (in core-beliefs or standalone)
7. Define architecture layers     (ARCHITECTURE.md)
8. Configure dev environment      (bring your own runtime — document your local
                                   toolchain: uv/mise/asdf/nix, or a container
                                   setup added later via the feature path)
9. Run bootstrap features:
   (one /keel-pipeline WI## per bootstrap entry, in order; set is stack-dependent)
   scaffolder -> landing-verifier        (one per package)
   config-writer -> landing-verifier     (test infra)
   each ticks its own backlog box on landing
10. Verify: tests pass in your dev environment
```

Steps 1-8 produce documentation. Step 9 produces code. This ratio is
deliberate -- by the time code is written, the agent has comprehensive context.

### The Document Hierarchy

**The project guide** (~80-100 lines) -- The table of contents. Quick facts, safety
rules, workflow overview, pointers to deeper docs. "Map not manual."

```
# Project Name
## Quick Facts       - Stack, runtime, key constraints
## Safety Rules      - Non-negotiable invariants (3-6 bullets)
## Workflow — Mandatory Pipelines  - Pipeline definitions (compact)
## Architecture      - Link to ARCHITECTURE.md
## Binders and specs    - Links to exec-plans/binders/, design-docs/
## Plans             - Links to exec-plans/active/, completed/
## Development       - How to build, run, test (4-6 lines)
```

**ARCHITECTURE.md** -- Process model, module map with dependencies, layer
diagram, key design decisions. Updated as modules are added.

**Structured Binders** (`docs/exec-plans/binders/<slug>.json`) -- What to build.
Schema-validated JSON with `work_items[].contract` + `work_items[].oracle` that
IS the spec. Authored by `/keel-refine`'s card walk.

**Design docs** (`docs/design-docs/`) -- How it looks, core beliefs, testing
strategy. Principles that apply across all features.

**Execution plans** (`docs/exec-plans/`) -- Backlog, handoff files,
tech debt tracker. The operational layer.

```
NORTH-STAR.md                 # vision, principles, growth stages
docs/
  design-docs/
    core-beliefs.md
    ui-design.md
  exec-plans/
    binders/
      <slug>.json
    active/
      backlog.md
      handoffs/
    completed/
      handoffs/
    tech-debt-tracker.md
  references/
```

---

## 5. Writing Specs That Agents Can Execute

A spec exists to eliminate ambiguity. If the agent has to guess, the spec
failed.

### Spec Structure

Every spec answers these questions in order:

1. **What is this?** One paragraph of context.
2. **What does it do?** Concrete behavior as assertions.
3. **What are the inputs and outputs?** Data structures, types, examples.
4. **What are the constraints?** Safety rules, edge cases.
5. **What is explicitly excluded?** Scope boundaries.

### Agent Legibility

| Human-readable | Agent-legible |
|---|---|
| "The button should feel responsive" | "Button click triggers fetch within 100ms; UI shows :fetching state" |
| "Handle errors gracefully" | "On non-zero exit: set operation to :error, store stderr in last_error, broadcast" |
| "Support common git workflows" | Table of 6 states with exact field values for each |

### Spec Consistency Checks

Before writing tests, verify specs agree:

- [ ] Product spec and design doc describe the same behavior
- [ ] Architecture doc lists the modules the feature will touch
- [ ] Backlog entry references correct spec sections
- [ ] Safety rules in core-beliefs match constraints in product spec

Spec drift in an agent-built project is as dangerous as a code bug.

The `### Anti-Pattern:` subsections throughout this document are illustrative,
not exhaustive. Full catalog: `docs/process/ANTI-PATTERNS.md`.

### Anti-Pattern: Vague Specs

```
BAD:  "Display repo status with appropriate colors"
GOOD: "Status priority: error > diverged > dirty > topic > behind > clean.
       Each state maps to exactly one color. See table in Section 4.6."

BAD:  "Pull should be safe"
GOOD: "Pull preconditions (ALL must be true):
       - On default branch, clean tree, not diverged, behind > 0
       If any fails: button disabled, tooltip shows reason."
```

---

## 6. The Backlog

The backlog decomposes the product spec into ordered, independently
testable features.

### Decomposition Principles

- **Smallest testable unit.** If a feature touches more than two system layers,
  split it.
- **Dependency-aware ordering.** Execute top-to-bottom, never cherry-pick.
- **Layer isolation.** Foundation first, then service, then UI.

### Backlog Format

```markdown
- [x] **WI04 Git.repo?/1**
  Needs: WI02, WI03
  Binder: repo-man-mvp
  <!-- DRAFTED: <ISO-date> by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: docs/exec-plans/binders/repo-man-mvp.md -->

- [ ] **WI05 Git branch detection**
  Needs: WI04
  Binder: repo-man-mvp
  <!-- DRAFTED: <ISO-date> by backlog-drafter; 0 markers remain -->
  <!-- SOURCE: docs/exec-plans/binders/repo-man-mvp.md -->
```

Each entry carries: feature ID + name, optional `Needs:` line,
optional `Design:` line for UI-bearing features, mandatory
`Binder: <slug>` (or `Binder-exempt: <reason>`) anchoring it to the JSON
Binder at `docs/exec-plans/binders/<slug>.json`, plus the drafter's
`<!-- DRAFTED: ... -->` and `<!-- SOURCE: ... -->` provenance
comments. The contract and acceptance oracle live in the JSON Binder's
per-feature `contract` + `oracle.assertions[]`, not on the backlog
entry.

### Feature Sizing

`WI##` denotes a **work item** — the smallest independently testable,
vertical-slice node in the dependency DAG declared by `Needs:` lines
in `backlog.md`. The id prefix is `WI`; the unit is a slice,
not a whole product feature.
Cross-slice cohesion comes from the shared Binder (`Binder: <slug>`).

Branching policy for slices with unmerged dependencies is set per-project
in the project guide ("Pipeline Preferences" → `Branching policy: halt | stack`).
See Step 0 of the keel-pipeline skill.

A well-sized feature adds 1-3 modules, has 3-8 tests, completes in one
pipeline run, and has a clear "done" state.

### Anti-Pattern: Cross-Layer Features

Example (from the Repo Man project):
```
BAD:  "WI12 Fetch with UI feedback"  (service + UI — crosses layers)

GOOD: "WI12 RepoServer init"         (service only)
      "WI13 RepoServer fetch"        (service only)
      "WI17 Dashboard LiveView"      (UI, consumes service)
```
Your feature names will reflect your domain, but the principle is the same:
each feature lives in one architectural layer.

### Refining the Backlog from a Binder — `/keel-refine`

The backlog is human-owned, but KEEL ships a drafting aid for the step
before the pipeline runs: turning a Binder, a paragraph of intent, or a
set of wireframes/comps into candidate `WI##` entries.

```
/keel-refine docs/exec-plans/binders/auth-redesign.md       # from a Binder file
/keel-refine docs/exec-plans/binders/auth-redesign/          # from a bundle directory
                                               # (README.md + images/PDFs, or a
                                               #  working UI prototype with
                                               #  index.html + linked CSS/JS)
/keel-refine "let users edit profile inline"  # from prose
/keel-refine                                   # interactive interview
```

You can also paste screenshots, comps, or flow diagrams directly in
chat alongside any of the above invocations. The skill stages pasted
images in `.keel-refine-session/<id>/` (gitignored) and passes them to
the drafter.

**Working UI/UX prototypes.** The bundle-directory shape recognizes
fully working prototypes as a first-class input — single-file HTML
artifacts (e.g. claude.ai web exports) or multi-file directories with
`index.html` + linked CSS/JS. The drafter reads the entry HTML and
optional `prototype.json` manifest to inform decomposition (one WI## per
named screen). Multi-file prototypes are committed under
`docs/exec-plans/binders/<slug>/prototype/` with their internal directory
structure preserved so they remain locally runnable; flat single-file
artifacts go to `<slug>/assets/` like other static comps.

The disposition (`reference` vs `seed`) is captured per-prototype in
`prototype.json` or, on its absence, prompted via the existing card
walk. Default is `reference`: `frontend-designer` extracts visual and
behavioral intent and rebuilds in the target stack, never copying
markup verbatim. `implementer` never reads prototype source under
either disposition. The project-wide default lives in the project guide under
`Prototype mode:`.

The `backlog-drafter` agent reads the Binder, `ARCHITECTURE.md`,
the project guide, the current `backlog.md`, and any UI design assets
(via your host's image input where supported, shallow-read only — for mapping which asset belongs
to which WI##, not for transcribing colors or copy). It returns a
structured proposal: new entries with `WI##` ids, layer sections,
`Needs:` edges, one-line acceptance criteria, optional `Design:` fields
on UI entries, and `<!-- HUMAN: ... -->` markers everywhere it couldn't
derive a field unambiguously.

When one ask carries several cohesion themes, the skill surfaces a
partition card first — N Binders with a dependency order — before
drafting anything. The human steers the split (merge, rename, drop, or
collapse to a single Binder) and confirms; only then does drafting
begin. Each accepted Binder walks its cards and commits separately, one
deterministic commit per Binder in dependency order. Single-theme asks
are unchanged.

**Per-card walkthrough.** The skill first prints an orientation summary
of the full slate, then walks each drafted entry individually before
accepting `commit`. The walk is mandatory — even zero-marker cards are
acknowledged — because `docs/process/PIPELINE-DOCTRINE.md` §"Autonomy
Ceiling" requires per-card conversational review.

```
Card 1 of 3:

WI12 Login screen with validation      → service
  Needs (intra-Binder):  WI08
  Needs (cross-Binder):  —
  Design:             login-flow.png

  Contract:
    route: /login
    request_fields: [email, password]

  Oracle:
    type:       integration
    assertions:
      [1] Valid credentials redirect to /home with a session cookie set.
      [2] Invalid credentials return 401 and surface "Email or password incorrect".

  Open markers:
    [1] Should rate-limit thresholds live in this contract or a shared `auth-policy`?

Verbs:
  accept                              — commit this card, advance
  edit title: <text>                  — set/replace title
  edit layer: <enum>                  — service|ui|cross-cutting|foundation
  edit needs: <comma-joined WI##>      — full list replace
  set contract.<key>: <value>         — set/replace a contract key
  drop contract.<key>                 — remove a contract key
  edit oracle.type: <enum>            — unit|integration|e2e|smoke
  add oracle.assertion: <text>        — append an assertion
  edit oracle.assertion <n>: <text>   — replace assertion n
  drop oracle.assertion <n>           — remove assertion n
  answer marker <n>: <text>           — record answer (apply via follow-up edit)
  skip marker <n>                     — ship marker as-is (pre-check blocks)
  drop WI##                            — remove card, advance
  back                                — revisit prior card
```

The full verb set lives in the keel-refine skill §"Phase 5 Step 2".

You walk one card at a time. Advancing verbs (`accept`, `drop`, `back`)
move between cards; field edits and marker answers stay on the active
card. After every card has been advanced at least once, the skill
enters post-walk state:

```
Walk complete. 3 cards ready to commit.

Verbs:
  commit        — materialize + git commit
  revisit WI##   — re-open a card for editing
  abort         — discard session
```

`commit` is only valid after the walk completes. Attempting it earlier
re-points to the current unwalked card. `commit` then materializes the
backlog entries, moves pasted images to `docs/exec-plans/binders/<slug>/assets/`,
and runs `git add` + `git commit` with a deterministic message.
No confirmation prompt; feature-branch commits are trivially reversible
(`git commit --amend`). `abort` deletes the session workspace — zero
pollution of tracked territory.

After the commit lands, run
`/keel-pipeline WI## docs/exec-plans/binders/<slug>.json` when ready —
the JSON Binder written at commit time IS the spec (its `contract` +
`oracle` are what `pre-check` and `test-writer` consume). Nothing
auto-chains. You still choose the order.

**What the drafter will not do:**
- Emit bootstrap-pipeline tasks (the scaffold/test-infra bootstrap features are `/keel-setup`'s territory — it authors them in Phase 6).
  Instead, it returns `status: bootstrap_gap` and routes the human to
  `/keel-adopt` to extend architecture first.
- Write separate spec files. The JSON Binder's per-feature `contract` and
  `oracle` are the spec; no markdown spec stub is created.
- Pick priority. Drafted entries appear in Binder-encounter order; the human
  decides what ships first.
- Modify existing entries. Strict append-only.
- Run the pipeline.
- Transcribe visual tokens (colors, exact spacing, typography) from
  UI design assets. That's `frontend-designer`'s job later in the pipeline.

**Why the marker convention matters.** Pre-check refuses to enter the
pipeline on any entry that still contains `<!-- HUMAN: -->`. The marker
IS the gate between "drafted" and "ready." Pre-check also verifies that
every `Design:` path on a UI entry resolves to a real file (no live
Figma/Miro URLs — committed assets only). Doc-gardener sweeps stale
`<!-- DRAFTED: -->` comments off shipped (`[x]`) entries during the
post-landing pass.

**Format and size caps for pasted/bundled assets:** PNG, JPG, GIF, SVG,
PDF, HTML. Per-file cap 20 MB. PDF cap 20 pages **at paste time** —
this matches your host's file-read per-request page limit so shallow
consumers can fetch the whole doc in one call; PDFs longer than 20
pages can still be consumed by agents that paginate (`pages: "1-20"`,
`"21-40"`, …), but the paste gate is conservative on purpose.
Bundle-directory mode additionally accepts CSS, JS/MJS, fonts
(WOFF/WOFF2/TTF/OTF), and JSON (`prototype.json` only) — these support
working-prototype bundles and are never standalone pasted attachments.
Bundle-total caps: 50 files and 100 MB; ignore-list filters
`node_modules`, `dist`, `build`, `.next`, `.vite`, `.git`, `coverage`,
`out`. The 20 MB / 20-page / 50-file / 100 MB numbers are heuristics
(not measurements) — see the keel-refine skill Phase 1
for provenance and tuning guidance. Other formats rejected at paste
time.

`backlog-drafter` is the first KEEL agent that returns structured YAML
to a skill instead of self-writing a file in a handoff directory, and `/keel-refine`
is the first KEEL skill that commits on the user's behalf (on explicit
`commit` verb). Both are deliberate — the drafting phase is iterative
and benefits from a chat-based review surface, while the pipeline
completes work repo-locally on its feature branch — the human reviews the
landed diff there, and opens a PR for it via `/keel-submit` when their
workflow uses a forge. See
the backlog-drafter agent's master and
the keel-refine skill for the full I/O contracts.

## The Binder lifecycle (informal, derived from artifacts)

KEEL does not declare Binder states machine-readably — state is
emergent from artifacts (principle P4: no redundant storage). In
narrative terms:

- **Draft.** A Binder file exists at `docs/exec-plans/binders/<slug>.json`;
  the human is iterating on it. No WI## in the backlog reference
  this slug yet.
- **Accepted.** `/keel-refine` committed a WI## slate referencing
  the Binder. Phase 5 Step 3 is the explicit human-confirmation
  moment.
- **In-flight.** At least one WI## from the slate is in pipeline
  (handoff exists in `docs/exec-plans/active/handoffs/`), HUMAN
  markers are being resolved, specs are being authored.
- **Complete.** Every WI## with `Binder: <slug>` is `[x]` in the
  backlog. The Binder file stays at its canonical path (no
  active/completed split — completion is derivable from backlog
  state, not directory location).

No frontmatter field declares these states. Tooling infers them
when needed (`uv run scripts/keel-binder-view.py docs/exec-plans/binders/<slug>.json`
renders a JSON Binder as deterministic markdown for human read-access).

---

## 7. Defining Architecture and Invariants

### The Layered Architecture Pattern

Dependencies flow in one direction only: downward.

```
Layer 5: UI (views, components, templates)
    |
Layer 4: Runtime (supervisors, coordinators, event bus)
    |
Layer 3: Service (stateful processes, orchestration)
    |
Layer 2: Domain (pure logic, derived fields)
    |
Layer 1: Foundation (external interfaces, types, structs)
    |
Layer 0: Config (application config, environment)
```

Enforced by convention early, by structural tests as the project matures.

### Domain-Specific Invariants

Every project has invariants -- correctness constraints, not style preferences.
Register them with `INV-###` IDs in the project guide §Safety Rules (the registry
`/keel-refine` parses and Binders cite), and elaborate them in `core-beliefs.md`.

**Git operations:**
```
- No git command uses --force
- Pull always uses --ff-only
- Pull rejected when dirty, diverged, not on default branch, or not behind
- Fetch is always safe (no preconditions)
```

**REST API:**
```
- All endpoints return JSON; errors include an "error" key
- No state modification on GET
- Auth required on all endpoints except /health
```

**Data pipeline:**
```
- No step mutates its input
- Failed steps produce dead-letter records, never silent drops
- Schema validation at ingestion, not mid-pipeline
```

### Mechanical Enforcement

| Level | When to add | Example |
|---|---|---|
| Convention | Day one | "Dependencies flow downward" |
| Formatter/linter | After scaffold | Auto-format check (e.g., `prettier --check`, `mix format --check-formatted`) |
| Structural tests | Module layout stabilizes | "No module in src/ui/ imports src/data/" |
| Pre-commit hooks | Patterns emerge | "Tests must pass before commit" |

**Enforce invariants, not implementations.** "Pull must use --ff-only" is an
invariant. "Use this exact shell command with these exact arguments" is an
implementation detail. The agent has freedom in how, not whether.

### Anti-Pattern: Style as Invariants

```
BAD:  "All modules must have a docstring"   (style)
GOOD: "All data-access modules go through the repository interface"  (architecture)
```

---

## 8. Agent Roles and Pipelines

Eighteen specialized agents, each with bounded responsibility.

### Agent Roster

| Agent | Purpose | Input | Output | Never Does |
|---|---|---|---|---|
| **scaffolder** | Project skeleton | Stack, structure spec | Scaffolded project | Write business logic |
| **config-writer** | Test infra, configs, behaviours | Architecture, testing strategy | Config files, helpers | Write feature code |
| **backlog-drafter** | Draft backlog entries from a Binder/prose/bundle (upstream of the pipeline, invoked via `/keel-refine`) | Binder, prose, or pasted images + repo context | Structured YAML proposal with candidate `WI##` entries, `Design:` refs, and HUMAN markers | Write specs, emit bootstrap tasks, auto-run the pipeline |
| **pre-check** | Classify intent, evaluate readiness, route pipeline | Backlog entry, Binder JSON | Execution brief with intent, complexity, constraints | Write code or tests |
| **researcher** | Investigate unknowns | Pre-check questions | Research findings | Make design decisions |
| **backend-designer** | Module interfaces, data flow | Resolved JSON, architecture | Signatures, integration points | Write implementation |
| **frontend-designer** | Component hierarchy | Resolved JSON, UI design doc | Component tree, event flow | Write backend code |
| **test-writer** | Failing tests from oracle | Resolved JSON, designer output | Test files (all RED) | Write implementation |
| **implementer** | Code to pass tests | Failing tests, resolved JSON | Implementation (all GREEN) | Modify tests |
| **code-reviewer** | Review code quality | Git diff, architecture | Verdict: APPROVED or CONCERNS | Modify code |
| **spec-reviewer** | Verify contract + oracle match | Resolved JSON, implementation | Verdict: CONFORMANT or DEVIATION | Modify code |
| **karta-spec-reviewer** | Karta lean-lane spec-first structural conformance gate (inspection-only, per-assertion) | Resolved JSON, implementation | Verdict: CONFORMANT, DEVIATION, or SPEC-SUSPECT | Execute, build, or modify code |
| **safety-auditor** | Verify invariants | Core-beliefs, implementation | Verdict: PASS or VIOLATION | Modify code |
| **arch-advisor-consult** | Architecture consultation (sequential, Step 1.7) | Resolved JSON, handoff, ARCHITECTURE.md | Guidance brief | Modify code |
| **arch-advisor-verify** | Structural soundness gate (parallel, Step 5) | Resolved JSON, implementation diff, ARCHITECTURE.md | Verdict: SOUND or UNSOUND | Modify code |
| **landing-verifier** | Verify completeness | All handoff entries | VERIFIED or BLOCKED | Write code or tests |
| **doc-gardener** | Fix doc drift | All docs, codebase | Updated docs, drift report | Write feature code |
| **review-panelist** | One lens of the in-process review panel (Skeptic / Architect / Adversary / Pragmatist) | Artifact under review (routing, blueprint, or landed feature) | Per-lens findings (advisory) | Modify code; block landing |

### Reasoning Tiers

Each agent is assigned one of two reasoning tiers — **standard** or
**high** — based on the cognitive demands of its task. On Claude Code,
each tier binds to a model name in the agent's `model:` frontmatter; the
Claude binding also runs some high-reasoning agents on the lighter model
where generation cost, not reasoning depth, is the variable (these agents
weigh existing code or decisions against a contract, oracle, or review lens
rather than authoring new code):

| Tier | Intent | Claude Code model |
|-|-|-|
| **high** | Design decisions, novel work, deep analysis | opus |
| **high, lighter model** | Gate verdicts — pattern matching against existing code or contract/oracle | sonnet (`reasoning: high`) |
| **standard** | Routing, pattern-following, verification | sonnet |

**High-reasoning tier:** arch-advisor-consult, arch-advisor-verify,
backend-designer, frontend-designer, safety-auditor, backlog-drafter,
code-reviewer, spec-reviewer, karta-spec-reviewer, review-panelist (10 agents)

**Standard tier:** pre-check, researcher, implementer, test-writer,
scaffolder, config-writer, landing-verifier, doc-gardener (8 agents)

### The Four Pipeline Variants

**Bootstrap** (project setup)

```
scaffolder    --> landing-verifier --> review? --> complete
config-writer --> landing-verifier --> review? --> complete
```

**Backend** (foundation and service features)

```
pre-check --> review-precheck? --> researcher? --> arch-advisor-consult? --> backend-designer? --> review? --> test-writer --> implementer --> [code-reviewer ∥ spec-reviewer ∥ safety-auditor? ∥ arch-advisor-verify?] --> landing-verifier --> review? --> complete
```

`?` = conditionally included. Pre-check classifies intent and complexity,
then decides which optional agents run. Designer skipped for trivial features.
Safety-auditor only for domain-critical modules. Arch-advisor runs for
architecture-tier complexity (consultation before design, verification before
landing).

**Frontend** (UI features)

```
pre-check --> review-precheck? --> researcher? --> arch-advisor-consult? --> frontend-designer --> review? --> test-writer --> implementer --> [code-reviewer ∥ spec-reviewer ∥ arch-advisor-verify?] --> landing-verifier --> review? --> complete
```

Frontend-designer always included. No safety-auditor (UI does not execute
domain-critical operations directly). Arch-advisor for architecture-tier only.

**Cross-cutting** (test infrastructure, fixtures)

```
pre-check --> review-precheck? --> test-writer --> implementer --> code-reviewer --> landing-verifier --> review? --> complete
```

**Maintenance lane** (non-feature repo work — *not a variant, a sibling*)

```
adopt-or-make change --> green gate (tests + lint) --> doc-gardener ad-hoc --> commit (chore:/infra:)
```

For `Binder-exempt: infra`/`trivial` cards and incidental tooling churn
(dependency/lockfile bumps, formatter runs, tooling config, typo sweeps). No
Binder, designer, test-writer, implementer, or handoff directory; its record is
the commit, not `routing.json`. Qualification (the admissibility boundary) and
procedure: `docs/process/PIPELINE-DOCTRINE.md` §"The maintenance lane".
Anything that adds product behavior is a feature — route it to `/keel-refine`.

**Karta lean lane** (dialed-down rigor with a visible debt ledger — *a sanctioned lane, not a variant*)

```
pre-check --> implementer --> karta-spec-reviewer --> safety-auditor --> green gate --> complete
```

The `karta-*` command family (`/karta-refine` --> `/karta-pipeline WI##` -->
`/karta-drive`, one feature per `karta-pipeline` run; `/karta-drive` sequences a
human-selected set of them in dependency order as a stacked PR chain, fail-fast)
coexists permanently with the full-rigor `keel-*` lane — you
choose per feature by which command you run; there is no graduation. It drops
the design agents, code-reviewer, the keel `spec-reviewer` (replaced by its
delta `karta-spec-reviewer`), arch-advisor, `landing-verifier`, and the review
panel; it is **spec-first** — tests are secondary (declared with `KARTA-DEFER`
where skipped). It keeps a **non-negotiable floor**: the **`karta-spec-reviewer`**
structural conformance gate, the **green gate**
(your project's configured tests/build command must pass — run directly by the
orchestrator, the same command the maintenance lane uses; halts fail-closed on
red or if none is configured), the `safety-auditor` gate, two write-time human
sign-off halts (`KARTA-PLACEHOLDER` / `KARTA-GUARD`), and bones-clean
admissibility (a cut may live only in leaf code behind a stable contract). Every
cut is declared inline with a `KARTA-DEFER` / `KARTA-PLACEHOLDER` /
`KARTA-GUARD` marker, and `scripts/karta-deferred-ledger.py` scans for them — the
ledger. Discipline + halt set: `docs/process/KARTA-LANE.md`; marker grammar:
`docs/process/PIPELINE-DOCTRINE.md` §"Declared-debt markers". Choosing it is a
lane, not a bypass.

### The Handoff Mechanism

A feature's handoff is a per-feature **directory** at
`docs/exec-plans/active/handoffs/WI##-<slug>/` — not a single file. It holds:

- **`routing.json`** — the orchestrator-owned pipeline control plane
  (status, variant, routing flags, gate and review verdicts, attempt
  counters, branch metadata). Only the orchestrator writes it, and only
  through `scripts/keel-routing.py`, which validates against the schema on
  every write. Agents may read it; they never write it.
- **`resolved-work-item.json`** — the resolver's deterministic Step 0 output
  (Binder slice, dependency classification, invariants, file paths, test
  tooling). Written once and immutable; fix the source and re-run Step 0 if
  it is wrong.
- **One `<agent>.md` per contributing agent** — each agent self-writes its
  own file with the `Write` tool, a full-file overwrite. There is no shared
  file and no transcribed `## <agent>` section. Agent files are SNAPSHOT:
  overwritten whole on re-run (e.g. after a review-panel kickback,
  spec-reviewer DEVIATION, or BLOCKED landing).
- **`<touchpoint>-review/` deliberation subdirs** (`precheck-review/`,
  `design-review/`, `landing-review/`) — APPEND-only; each panel pass writes
  a new `attempt-NN.md`.

Each agent uses the `Read` tool to pull the sibling files it needs —
`resolved-work-item.json` for the structured feature data, any upstream
`<agent>.md` for prior decisions and constraints — then writes only its own
file and returns a terse envelope to the orchestrator. This wisdom
accumulation prevents downstream agents from repeating upstream mistakes or
violating upstream design choices, while keeping each agent's context lean
(it reads only what it needs). Revision history lives in the deliberation
attempts plus `git log`, not in duplicate sibling agent files — timeline
stays out of snapshot content (KEEL P5).

The directory is the serialization surface between agents; the full
who-writes-what contract is `docs/process/HANDOFF-CONTRACT.md`.
`scripts/validate-handoff.py` enforces the directory shape (expected files
per routing flags, `attempt-NN.md` sequencing, hash integrity).

On completion, move the directory from `active/handoffs/` to
`completed/handoffs/`.

### The Orchestrator Role

The human kicks off features. The `keel-pipeline` skill handles the
mechanics: dispatching agents, running the review panel (the persona
sub-agents by default, or the roundtable MCP when opted in),
reading gate verdicts, looping on spec-review/safety/arch-advisor findings
within their ceilings, and running the completion procedure automatically —
landing review, doc-gardener, tech-debt log, backlog tick + commit, handoff
archive. The orchestrator steers; the pipeline executes on their
behalf end-to-end without per-step approval, escalating to the human only
on gate ceilings. Integration through a forge (push + PR) is the human's
separate `/keel-submit` step.

**The orchestrator does not write code.** When code quality issues are found
(Step 5), findings are sent back to the implementer agent for fixing. When
spec-reviewer returns DEVIATION or safety-auditor returns VIOLATION, the
orchestrator routes findings to the implementer — it does not fix code itself.

### The Missing Capability Principle

From the OpenAI article: "When something failed, the fix was never 'try
harder.'"

| Failure | Root cause | Fix |
|---|---|---|
| Wrong module structure | No architecture doc | Write ARCHITECTURE.md |
| Misunderstands scope | Vague spec | Rewrite spec with assertions |
| Violates safety rule | Rule not in core-beliefs | Add the rule |
| Inconsistent design | No designer ran | Add designer to pipeline |
| Cannot test its work | No test infrastructure | Run config-writer first |

Build the missing capability. Do not retry the same prompt.

---

## 9. Testing Doctrine

Tests enforce spec conformance, not discover design. Every spec assertion has
a corresponding test. When specs change, tests change first.

### The Six-Layer Model

| Layer | Name | I/O | Speed | Mocking | What It Tests |
|---|---|---|---|---|---|
| 0 | Spec consistency | None | Instant | N/A | Docs agree with each other |
| 1 | Safety invariants | Real | Slow | None | Non-negotiable constraints under real conditions |
| 2a | Integration | Real | Slow | None | External interfaces work correctly |
| 2b | Pure logic | None | Fast | None | Domain computations, derived fields |
| 3 | Service behavior | Mocked | Fast | External deps | Stateful processes, supervisors, orchestration |
| 4a | UI presentational | Mocked | Fast | Service layer | Component renders; DOM reflects inputs |
| 4b | UI container | Real collaborator, mocked boundary | Fast | Store/service/router | On-mount wiring fires; composed render |

**Layer 0: Spec Consistency.** Before writing tests, verify specs agree.
Product spec, design doc, architecture doc, and backlog must describe the same
system.

**Layer 1: Safety Invariants.** First tests written, last deleted. Real I/O
against real systems -- no mocking. Mocking safety tests means testing your
mock, not your safety. Tag `@tag :integration` for conditional execution.

```
Example: create temp repo, set up diverged state, attempt pull, verify:
  - Pull fails cleanly
  - No --force flag used
  - Working tree unchanged
```

**Layer 2a: Integration (Slow).** Real I/O against controlled environments.
Temp dirs, temp repos, real shell commands. Tag `@tag :integration`.

**Layer 2b: Pure Domain Logic (Fast).** No I/O. Data structures, derived
fields, state machines. Millisecond execution. The fast feedback loop.

**Layer 3: Service Behavior.** External deps mocked.
Process serialization, event broadcasts, crash isolation.

**Layer 4a: UI presentational.** Service layer mocked; component driven by
inputs. Assert the rendered DOM reflects the inputs.

**Layer 4b: UI container.** Real store/service/router, only the external
boundary (HTTP/clock/storage) mocked. Assert the on-mount wiring fires AND the
composed render — a 4a test cannot see on-mount wiring. See
`docs/process/PIPELINE-DOCTRINE.md` §"Frontend acceptance".

### The RED to GREEN Flow

```
test-writer writes tests  -->  all RED
implementer writes code   -->  all GREEN
spec-reviewer verifies    -->  matches spec
```

Test-writer never writes implementation. Implementer never modifies tests.
Tests come from the spec, not the implementation. And an **inherited test** —
one a prior feature wrote — is a prior contract: neither agent edits it to make
new code pass. A failing inherited test means the code is wrong (fix the code)
or the behavior is a deliberate spec change (halt, update the owning spec; the
test follows) — P6: spec > test > code.

### Anti-Pattern: Testing Implementation Details

```
BAD:  "Verify fetch() calls the async helper with exact internal arguments"
GOOD: "Verify fetch() sets state to :fetching, completes async, broadcasts update"
```

Tests should break when behavior changes, not when implementation details
change.

---

## 10. Operating the Pipeline Day-to-Day

### Kicking Off a Feature

1. Identify next unchecked feature in backlog.
2. Verify dependencies are complete.
3. Read referenced spec sections.
4. Create handoff directory: `docs/exec-plans/active/handoffs/WI{id}-{feature-name}/` (the pipeline scaffolds `routing.json` + `resolved-work-item.json` inside it; each agent self-writes its own `<agent>.md`).
5. Run pipeline stages sequentially, reviewing each output.
6. Continue until landing-verifier reports VERIFIED.

### What the Human Does at Each Stage

| Stage | Human action |
|---|---|
| Pre-check | Does intent/complexity classification make sense? Routing correct? |
| Researcher | Are findings relevant? Missing context? |
| Arch-advisor (consult) | Does architecture guidance align with your vision? |
| Designer | Does the design match your mental model? |
| Test-writer | Do tests cover spec assertions? |
| Implementer | Do tests pass? Is code reasonable? |
| Spec-reviewer | CONFORMANT or DEVIATION — do you agree? |
| Safety-auditor | PASS or VIOLATION — comfortable with the analysis? |
| Arch-advisor (verify) | SOUND or UNSOUND — architecture still solid after implementation? |
| Landing-verifier | Is the feature complete? |

At each stage: **proceed**, **redo** (with more context), **fix** (update
spec), or **abort** (rare).

### Structured Verdicts and Loop Control

The read-only review gates (code-reviewer, spec-reviewer, safety-auditor,
Arch-advisor verify) run **concurrently** on the same implementer diff —
Step 5 of the `keel-pipeline` skill dispatches the applicable ones together,
consolidates their findings, and routes any failures back to the implementer
as one fix cycle. Each gate outputs a structured `**Verdict:**` as its first
line and keeps its own retry budget; the pipeline branches per gate:

- **Spec-reviewer:** max 2 loops. DEVIATION sends findings to implementer.
  After 2 attempts, escalate to human — decompose the feature or fix the spec.
- **Safety-auditor:** max 3 loops. VIOLATION is never negotiable — fix the code.
  After 3 attempts, escalate — the invariant rule itself may need review.
- **Arch-advisor (verify):** max 1 retry. UNSOUND sends architecture findings to
  implementer, then re-runs spec-reviewer, safety-auditor, and Arch-advisor
  concurrently (a structural fix can ripple into conformance and safety). If
  still UNSOUND, escalate.

See `docs/process/FAILURE-PLAYBOOK.md` for the full decision tree.

### The Commit Ritual

After landing-verifier reports VERIFIED (and the landing review completes — it always runs):

```
1. doc-gardener sweep: apply drift fixes in the working tree
2. Log new shortcuts / delete resolved items from tech-debt-tracker.md (git log is the landing record; do not check off with [x] or accumulate a "Resolved" section)
3. Check off feature in backlog (the [ ] -> [x] tick the pipeline owns)
4. Stage files: git add -A (clean tree enforced at pipeline start)
5. Commit: feat(WI{id}): {feature name} with verdict table
6. Move handoff: active/handoffs/ -> completed/handoffs/, folded into the feature commit with a plain local `git commit --amend` (no push, no PR — integration is the human's separate /keel-submit step)
```

Maintenance-lane changes use a `chore:`/`infra:` commit type instead of
`feat(WI##):`, with no verdict table or handoff move — see
`docs/process/PIPELINE-DOCTRINE.md` §"The maintenance lane".

### Garbage Collection

**When:** After every 5-10 features, after refactoring, at session start, when
an agent produces surprising output.

**Checklist:**

- [ ] The project guide still accurate?
- [ ] ARCHITECTURE.md matches code?
- [ ] Product spec describes what was built (not what was planned)?
- [ ] Core beliefs still hold?
- [ ] Tech debt tracker updated?
- [ ] Backlog accurate?
- [ ] Completed handoffs archived (active → completed)?

Docs that lie are worse than no docs. A missing doc causes the agent to ask.
A lying doc causes the agent to act on false information with confidence.

### Tech Debt Tracking

Three sections in `docs/exec-plans/tech-debt-tracker.md`:

- **Pre-Implementation** -- spec drift, open questions
- **During Implementation** -- shortcuts, workarounds, deferred bugs
- **Post-MVP** -- improvement opportunities

Each entry: checkbox, source, enough context for a future agent. (Don't bake the date into the entry — `git blame` has it.)

---

## 11. Increasing Agent Autonomy Over Time

### The Autonomy Progression

| Stage | Human involvement | Agent capability | What enables it |
|---|---|---|---|
| **1. Full review** | Reviews every output | Single pipeline stages | Base pipeline |
| **2. Agent-to-agent review** | Reviews final output only | Spec-reviewer + safety-auditor catch issues | Reliable gate agents over 5-10 features |
| **3. Self-correcting pipeline** | Reviews escalations only | Pipeline diagnoses failures and reroutes | Structured rejection, wisdom accumulation, intent classification |
| **4. Agent end-to-end** | Reviews the completed feature (commit + archived handoff); integrates via /keel-submit | Drives features pre-check to repo-local completion, review-panel integration | Mechanical enforcement + Arch-advisor + review panel |

### What Enables Each Transition

**1 to 2:** Spec-reviewer and safety-auditor produce reliable verdicts over
5-10 features. Human trusts review agents.

**2 to 3:** The pipeline gains self-correction through three OMA-derived
patterns:
- **Structured rejection:** Gate agents output machine-readable verdicts
  (CONFORMANT/DEVIATION, PASS/VIOLATION). The pipeline branches on these and
  routes failures back to the implementer with specific findings. Bounded
  loops prevent infinite thrashing (max 2 spec-review, max 3 safety).
- **Wisdom accumulation:** Each agent propagates Decisions and Constraints
  downstream through its own file in the handoff directory. Downstream agents
  read upstream context before starting — preventing repeated mistakes and
  contradictory choices.
- **Intent classification:** Pre-check classifies work intent (refactoring,
  build, mid-sized, architecture, research) and complexity tier (trivial →
  architecture-tier). This drives routing: trivial features skip the designer,
  architecture-tier features invoke Arch-advisor.

**3 to 4:** The agent orchestrates its own pipeline. Arch-advisor provides
architecture-level verification for complex features. Reads backlog, identifies
next feature, runs stages, reports results. Human reviews in batch.

From the OpenAI article: "single Codex runs work on a task for upwards of six
hours while humans sleep." This is the end state -- but it requires the
mechanical enforcement built in stages 1-3.

### When to Promote Manual Checks to Automated

A check is ready when: performed consistently 5+ times, criteria are objective,
testable without false positives, failure mode understood.

```
Manual:     "No UI module calls external APIs directly"
Automated:  Structural test that fails if API calls found in src/ui/

Manual:     "ARCHITECTURE.md lists all modules"
Automated:  Test comparing module map to actual source files
```

### Guardrails That Enable Autonomy

- [ ] Safety invariants have Layer 1 tests (real I/O)
- [ ] Structural tests enforce layer boundaries
- [ ] Formatter/linter on every test run
- [ ] Spec-reviewer has track record
- [ ] Garbage collection scheduled
- [ ] Tech debt tracker maintained

The goal: move human oversight from "review every line" to "review every
decision." Mechanical enforcement handles correctness. The human handles taste.

---

## Summary

KEEL is a lifecycle, not a checklist. The principles compound: knowledge
boundary feeds spec quality, spec quality feeds test quality, test quality
feeds agent autonomy, agent autonomy feeds development speed.

The minimum viable KEEL setup:

```
1. Write the project guide (~80 lines, table of contents)
2. Write NORTH-STAR.md (vision, principles, growth stages)
3. Write one product spec (what to build)
4. Write core-beliefs.md (invariants and testing strategy)
5. Write ARCHITECTURE.md (layers and module map)
6. Define the backlog (ordered, dependency-aware)
7. Run the first pipeline
```

Everything else -- handoffs, garbage collection, safety audits, autonomy
progression -- builds on this foundation as the project grows.

The repo is truth. Docs drive code. Coding comes last.
