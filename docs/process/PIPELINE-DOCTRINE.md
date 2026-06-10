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

## Feature input canon — single path, JSON Binders only

The KEEL pipeline accepts **one shape** of feature input: a structured
JSON Binder at `docs/exec-plans/binders/<slug>.json` validated against
`schemas/binder.schema.json`. Every pipeline agent — `pre-check`,
`test-writer`, `spec-reviewer`, `safety-auditor`, `backlog-drafter`,
`doc-gardener` — reads JSON fields directly via `jq`. There is no
markdown-Binder path, no legacy-spec path, no second pipeline that walks a
different artifact shape.

Structured Binders are a KEEL-internal artifact. Agents generate them
(`/keel-refine`), agents read them, and a synthesizer can render them to
markdown for human reading on demand. Humans do not author the JSON by
hand.

Any non-JSON input is **raw material for `/keel-refine`**, not pipeline
input. Markdown specs, prose descriptions, Binders from other systems,
bundles with wireframes, images — all feed into `/keel-refine`, which is
the conversion hub. `/keel-refine` produces a structured JSON Binder;
`/keel-pipeline` reads only that JSON.

Direct consequences:

- `/keel-pipeline WI## <binder-path>` expects `<binder-path>` to end in
  `.json`. A `.md` path is a routing error — halt with a CTA to run
  `/keel-refine` first. The halt message in
  the keel-pipeline skill cites this section.
- Agent prompts do not contain dispatch logic on backlog fields to
  select between JSON and markdown reading. There is one reading path.
- Features predating structured Binders (`Binder-exempt:` entries,
  pre-invariant-7 grandfathered entries) do not flow through
  `/keel-pipeline` as markdown. They are migrated via `/keel-refine`
  before the pipeline sees them, or they run outside the pipeline.
- `validate-binders.py` enforces invariant 7 on the backlog (`Binder: <slug>`
  link integrity). The `<slug>.json` file the link points at is the
  only artifact `/keel-pipeline` reads.

The structural contract lives in `schemas/binder.schema.json`. The single
dispatch path lives in the pre-check agent master. The conversion-hub
behavior lives in the keel-refine skill.

## The maintenance lane

Not every change is a feature. Dependency and lockfile bumps,
tooling-generated config, formatter runs, `.gitignore`/editor-config edits,
license headers, and typo sweeps are repo maintenance: they carry no product
behavior to spec and no test to write beyond "the repo still builds and
passes." Forcing them through a Binder is ceremony out of proportion to the
change — and that pressure is what drives the ad-hoc commits the operating
contract forbids.

So maintenance has its own sanctioned path, the **maintenance lane**. It is
**not** ad-hoc: it runs a gate, commits on a branch, and leaves a typed
record. It is a *sibling to* the feature pipeline, **not a pipeline variant** —
the four variants (`bootstrap`, `backend`, `frontend`, `cross-cutting`) are
the feature-execution paths recorded in `routing.json`; the maintenance lane
records nothing in `routing.json` because it runs no agent handoff. Its record
is the git commit (P5).

This is the lane that `Binder-exempt: infra` and `Binder-exempt: trivial` backlog
cards land through. A card is **not required** — incidental churn (e.g. a CLI
that rewrote a tracked config) lands with no card; a deliberately tracked
maintenance card is consumed if one exists.

### What qualifies (the admissibility boundary)

This boundary is the load-bearing safety property: it is the only thing
between the maintenance lane and a backdoor that lands a product feature while
skipping spec and test discipline. It is conjunctive — a change qualifies only
if **every** clause holds:

1. It adds **no product behavior** — no new endpoint, UI behavior, public API
   or CLI surface, data model, permission, auth or security rule, domain
   invariant, or schema migration.
2. Its code changes are **mechanical and behavior-preserving** — a true no-op
   to how the software runs (formatter output, a renamed local, a config value
   a tool writes).
3. The diff is one of: a dependency/lockfile refresh within existing intent;
   tool, CI, or package-manager config; a formatter or whitespace run; a
   `.gitignore`/editor-config/license-header edit; or a comment/doc/typo fix.
4. It is **not** a bug fix whose correctness depends on what the product is
   meant to do. Those are features — they need a spec and a test.

If the orchestrator cannot explain why **every** changed hunk is maintenance,
it halts and routes the change to `/keel-refine`. **When in doubt, it is a
feature.** Enforcement is prompt-level (self-classification plus the green gate
plus the typed-commit audit trail), not mechanical — the right property for a
framework with no runtime.

### How it lands

1. Branch.
2. Make the change, or adopt the tooling-generated change already in the tree.
3. Confirm the working-tree delta is solely the maintenance change and meets
   the admissibility boundary above.
4. Run the project's configured gate command (tests + lint). It must pass.
5. Run a `doc-gardener` ad-hoc sweep; fold any drift fixes into the change
   (garbage collection is non-negotiable).
6. Commit with a `chore:` or `infra:` type. Completion is repo-local — the
   typed commit on the branch is the whole record; forge integration is the
   human's separate `/keel-submit` step, exactly as features now complete.

No Binder, no resolved-work-item file, no handoff directory, no required backlog
entry. The commit is the whole record.

### Review (knob)

The green gate plus the admissibility boundary are the safety floor and are
non-negotiable. Whether a code review runs **on top** is a project choice —
`Maintenance review: gate-only | reviewed` in the project guide (absent ⇒
`gate-only`). `reviewed` dispatches `code-reviewer` on the diff before landing.
A regulated shop sets `reviewed`; a small team keeps `gate-only`. The knob can
only **add** review — it can never lower the green gate or admit a change that
fails the admissibility boundary.

## Declared-debt markers — the Karta lane's ledger

The Karta lane (the dialed-down-rigor `karta-*` command family) buys speed by
*deferring* rigor and *declaring* what was deferred. Each cut is recorded as a
**marker at the site of the cut**. The markers are the **ledger** — the record
of what rigor was deferred. They record declared *debt*, not lane provenance:
a karta-lane feature that deferred nothing leaves no marker and is
indistinguishable from — and equivalent to — a full-rigor feature, which is
fine. Absence of markers means no outstanding deferred debt, whichever lane
built it. There is no separate store; the scanner derives the ledger view from
the markers in the tree.

### The markers

Three tokens, one shape. The token encodes the gate, not a severity score:

```
KARTA-DEFER:       <what was cut> | real: <what the right version is> | finish: <hint>
KARTA-PLACEHOLDER: <what is faked> | real: <the real thing> | finish: <hint>
KARTA-GUARD:       <irreversible/sensitive effect> | real: <the safe form> | finish: <hint>
```

- **`KARTA-DEFER`** — a deferred rigor shortcut (skipped test-first, hardcode,
  a punted edge case, leaf-code roughness). Declare and keep moving; **no halt**.
- **`KARTA-PLACEHOLDER`** — a mock, stub, or fake standing in for the real
  thing. Writing one **halts for a human OK first**.
- **`KARTA-GUARD`** — a destructive, irreversible, or PII/secret-touching
  effect (unrestorable data, real charges, real third-party comms), regardless
  of whose infra hosts it. Same **human-OK halt**.

The sign-off-halt mechanics, lane admissibility, and the refusal protocol are
the Karta lane's own discipline (`docs/process/KARTA-LANE.md`); this section
defines the grammar, the integrity rules, and the scanner.

### Fields + the delimiter rule

- **`<what>`** — required; the text before the first ` | <key>:`.
- **`real:`** — required; the *intended* behavior (push toward an executable
  assertion when one exists, prose otherwise).
- **`finish:`** — optional; a hint for completing the cut.
- ` | ` introduces a field **only when followed by `<key>:`** — any other `|`
  is literal, so `<what>`/`real:`/`finish:` may contain pipes. (One
  author-controlled edge: a literal ` | real:` or ` | finish:` inside `<what>`
  would mis-split.) An unknown key makes the marker **malformed**.

### Hard rules (marker integrity)

1. **One marker per cut, at the cut.** The marker is the single source of truth
   for that shortcut (P4) — no second home, no manifest, no stored ledger, and
   **no parallel lane registry** (the lane is the command you ran; the markers
   are the record).
2. **No ID.** No `KARTA-DEFER-001` identifiers; the scanner references a marker
   by `file:line` (a derived coordinate).
3. **No timestamp, age, or approval in the marker** (P5). It states what *is*
   cut. Age is derived from `git blame`; the human OK behind a
   `KARTA-PLACEHOLDER`/`KARTA-GUARD` is a write-time halt recorded by the commit
   (git log), never in the marker.
4. **Clearing a cut deletes the marker** — not commented out, not gutted to
   `KARTA-DEFER: [done]`, not replaced with a pointer (P5). git log holds the
   sequence.

### Anti-laundering

Derive the hardening spec from `real:` (the intent), **never** from the cut
body. A stub's `real:` is what it *should* be, not what the stub does.

Extraction does not launder admissibility. Pulling a bones-level cut into a
new leaf helper does not make it admissible — admissibility turns on whether
the bones (data model, cross-module contracts, transaction edges, auth guards)
depend on the cut's behavior, not on which file the cut now lives in.

### The scanner — `scripts/karta-deferred-ledger.py`

PEP 723, `uv run`, stdlib-only, cross-platform. It **derives** the ledger view
and stores nothing. Modes:

- **report** (default) — the ledger view grouped by file (kind, `what`,
  `real`, `finish`, git-blame age); always exits `0`.
- **`--lint`** — reject malformed markers; exits non-zero naming each.
- **`--check`** — assert clean; exits non-zero if any marker survives, listing
  each `file:line — <kind>: <what>` and a next step (P7).

Exit codes: `0` pass/report, `1` check failed, `2` operational error.
`--lint`/`--check` **fail closed** on an unreadable file. Outside a git repo,
age degrades to `unknown` rather than failing.

### What it can and cannot detect (honesty)

It detects **declared** markers only. A shortcut taken with **no marker** is
invisible to a marker-walking scanner by construction; markers are single-line.
The scanner **narrows** the prompt-only enforcement gap — it does not eliminate
it, and the lane owns that residual gap rather than papering over it.

### Retirement

A cut the team consciously decides not to complete leaves the code and becomes
a `docs/exec-plans/tech-debt-tracker.md` entry (the shipped, P5-disciplined
tracker — resolved items are deleted, no log section). Retiring is a small
halt-for-human bar, not an agent self-authorization.

### Defaults + knobs

The marker vocabulary and the report view are universal. The one split is
**whether `--check` is wired into CI**: report-only is the floor (prompts are
the floor *because the environment does not travel*; a required CI check is an
environment dependency and must be opt-in). The knob only **adds** a mechanical
check on top of the prompt floor — it cannot lower P1–P7.

## Frontend acceptance — rendered, not just unit

A `ui`-layer feature is not done when its components pass in isolation. The
pipeline must verify the **composed, rendered** result, because composition,
binding, wiring, and layout defects are invisible to mocked unit tests — a
component can pass every isolated test while being unusable in context (an
unidentifiable card, a list that never loads on mount). This is the UI analog
of spec drift: the gate checks the rendered result against the design intent,
not just that code was written.

It is enforced through the EXISTING oracle + review machinery — no new agent,
no new pipeline stage, no schema change. Two halves:

**Coverage (already enforced).** For every assertion in `oracle.assertions[]`,
`test-writer` produces a test that compiles and FAILS (RED) before
implementation, and `spec-reviewer` reads the test body to confirm it
exercises the assertion (an untested assertion is a MAJOR deviation). An
assertion that exists is verified with real teeth.

**Completeness (the design-fidelity contract).** Coverage verifies assertions
that exist; it cannot invent them. A `ui`-layer feature's oracle MUST carry,
each as a concrete predicate — the **fidelity checklist**:

- **Rendered** — what the user must see (specific text/elements present in the
  rendered output). Always.
- **Identity** — *if* the feature renders an entity, list, or card: the rendered
  output must identify *which* entity (name/id), not only its state.
- **Wiring** — *if* the component owns its data (injects a store, service, or
  router): the data load fires on mount / route-entry.
- **Layout-bound** — *if* the feature renders growable content (list, log,
  feed): the container is height-bounded, not unbounded in normal flow.

`frontend-designer` distills the design mock into these predicates (the mock is
upstream raw material, like prose feeding `/keel-refine` — never a stored golden
image); `backlog-drafter` carries them into `oracle.assertions[]`; the design
review (Step 2.5) and `spec-reviewer` halt with a CTA naming any **applicable**
axis the oracle omits. This is a reviewer judgment over legible assertion text,
not a schema-counted tag — a count of a self-applied label is gameable and would
store a text-derivable cache (P4). Completeness is a universal baseline, not a
knob.

**Served-bundle verification (the Stage-4 upgrade).** True viewport layout,
console errors, and real-network behavior need a running browser against the
served bundle. KEEL ships no browser, so this is an opt-in capability at the
Stage-4 autonomy rung (see `AUTONOMY-PROGRESSION.md`). It is **derived, not a
knob**: a project has it when a served verify command is configured (its own
e2e/serve harness — Playwright/Cypress/etc.) and a `ui` feature opts in via
`oracle.type ∈ {e2e, smoke}`. Then:
- `test-writer` authors the rendered/layout criteria as **structural** served
  assertions (a11y tree, computed styles such as overflow/max-height,
  bounding-box ≤ viewport, no console errors) in that harness — never
  pixel-diff against a stored golden (P4/P5).
- `landing-verifier` builds + serves + drives the bundle and, on pass, reports
  the viewport/layout/console surface as VERIFIED (upgrading the qualified
  verdict). The build writes to a gitignored/temp output path in the working
  tree; if the build tool rewrites a **tracked** file, that churn is surfaced
  and routed to the maintenance lane — `landing-verifier` never `git restore`s
  the live tree, because the feature's own uncommitted code lives there.
- If a `ui` oracle is `e2e`/`smoke` but **no** served command is configured,
  `landing-verifier` HALTS with a CTA (add the harness, or downgrade the oracle
  to the rendered floor) — never a silent downgrade (P7).

In the default (no served harness) mode the rendered floor stands and
`landing-verifier` reports the served/viewport surface as **not** verified, so
the pipeline never overclaims coverage it lacks.

The framework-agnostic outcome lives here; the per-stack testing mechanism (how
a component is rendered with or without its real collaborators — Layer 4a vs 4b)
lives in the project's `core-beliefs.md` and in the test-writer agent master.

## Autonomy Ceiling

The end state KEEL aims for: human feeds a feature spec (or a Binder that
`/keel-refine` turns into draft backlog entries the human edits into
specs); KEEL completes the feature repo-locally (committed on its branch,
handoff archived, backlog `[x]`). Publishing — push + PR — is the separate
`/keel-submit` ceremony the human runs when using a forge.

| What KEEL does autonomously | What the human does |
|-|-|
| Pick pipeline variant based on intent | Write the Binder or edit from a `/keel-refine` draft; author each feature spec |
| Route to optional agents | Define domain invariants |
| Self-correct on spec deviation (max 2) | Resolve escalations |
| Self-correct on safety violation (max 3) | Update north star / specs |
| Self-correct on architecture issues (max 1) | Review the completed feature; submit + merge via `/keel-submit` when using a forge |
| Garbage collect docs after landing | |
| Commit on the feature branch + archive the handoff for every feature (repo-local completion) | |
| Review panel every feature (personas default; roundtable opt-in) | |

What KEEL does **not** do autonomously:

- Pick the next feature from the backlog (human decides priority).
- Modify specs or invariants (human decides what to build).
- Push, open, or merge a PR — publishing is the human's `/keel-submit` ceremony, the human reviews and merges on their forge.

`/keel-refine` is the **Binder-scope gate** and **conversion hub** — not
an expansion of this ceiling. Given prose, legacy markdown, a bundle
directory, or images, it drafts WI## entries linked to a new or existing
structured JSON Binder file (`docs/exec-plans/binders/<slug>.json`), reviews
each card conversationally with the human, and commits only when the
human types `commit`. The skill performs the `git add` + `git commit`
on that verb with a deterministic message. When one ask carries several
cohesion themes, the skill first proposes a partition — N Binders with
a dependency order — that the human reviews and edits as a card before
anything is drafted; each accepted Binder then walks and commits
separately through the same per-card gates. The split is proposed by
KEEL, decided by the human. The human steers via Q&A;
`/keel-refine` writes the JSON and the backlog entry. Invariant 7
enforces that every WI## traces back to a Binder (or declares
`Binder-exempt: <reason>`).

Per-card review is non-negotiable. There is no block-review escape
hatch and no "accept all" shortcut in `/keel-refine` Phase 5. This gate's
guarantee is never traded for speed (NORTH-STAR §The Principle); this is
the load-bearing reason `/keel-refine` is the only
agent in the pipeline that walks every drafted artifact individually
before commit.
