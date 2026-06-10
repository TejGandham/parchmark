# KEEL Framework Principles

Canonical source. These principles govern every framework-level
decision in KEEL — agent prompts, skill semantics, file layouts,
validator rules, and everything that ships to user installs. A
proposed change that violates any of these is the change to revisit,
not the principle.

User projects will inherit these principles as operating constraints
for their own KEEL-driven development.

---

## The two foundational principles

From OpenAI's [harness-engineering article](https://openai.com/index/harness-engineering/),
ported directly.

### P1. Agent Legibility is the Goal

**The repo is optimized for agent comprehension, not human
aesthetics.**

Every tree layout, every file naming choice, every comment, every
metadata field is judged on: *can an agent, landing cold with no
prior session context, understand this?* Human ergonomics are a
welcome side-effect — not the decision axis. When the two conflict,
agent legibility wins.

### P2. Progressive disclosure

**Agents start with a small, stable entry point and navigate to
deeper sources as needed.**

The entry point (the project guide for user projects, AGENTS.md for
framework contributors) is a table of contents, not an encyclopedia.
Every deeper source is reachable in O(1) navigation from the entry
point or from a stable predecessor. Agents should never have to
guess where to look next.

---

## The four corollaries

These extend P1 and P2 into specific operational rules. Violating
any of them violates agent legibility or progressive disclosure.

### P3. The repo is self-sufficient

**The repo's current state is always sufficient to reconstruct any
view — Binder, architecture doc, design summary, dependency graph, or
anything else derivable from authored state.**

A reconstruction tool (synthesizer) must be *possible* at any
moment. It does not have to be *implemented* on day 1. The design
must leave all the raw material in the repo so that a year-3 agent host,
landing cold, can reconstruct any view needed.

### P4. No redundant storage

**Stored files are authoritative ONLY for content they uniquely
author. Anything derivable from other repo state shouldn't be stored
redundantly — if it is, it's a cache that can stale.**

Concrete examples:
- Binder files do not carry `feature_ids: [...]` manifests. That list
  is derivable from the backlog via `grep "Binder: <slug>"`.
- Binder files do not declare `state: accepted` or lifecycle fields.
  State is emergent from whether WI## entries reference the Binder and
  whether they're `[ ]` or `[x]`.
- Directory structure does not encode completion status. A
  `completed/` folder that mirrors `active/` is a cache of `[x]`
  markers in the backlog.

When in doubt, ask: *can this be derived from other repo state?* If
yes, don't store it.

### P5. The repo is a snapshot, not a timeline

**History isn't a concern of the repo. `git log` has the evolution;
the repo-as-snapshot doesn't need to narrate how it got here.**

No "changelog" field on artifacts. No "last modified" timestamps
baked into content. No "was originally X, then Y, now Z" commentary
in docs. The repo reflects *what is*, not *how it got here*. If the
reader needs history, they run `git log`. In content we state what
is; version control holds the timeline.

**Rationale is not timeline.** P5 bans *timeline* — how a thing
came to be ("was X, now Y", changelogs, dates, commit SHAs,
migration narratives) — not *present-tense design rationale*. A
statement of *why a current constraint exists* is allowed and often
load-bearing: "the bootstrap is stdlib-only because it runs before
deps exist" is a fact about what IS, stated so a cold-landing agent
does not "fix" a counterintuitive but deliberate design (a P1 /
Chesterton's-fence concern). The rule of thumb: **state what IS and
why it IS; never how it came to be.** This does not open the
no-agent-authorized-exceptions door below — it draws the line
between rationale (allowed, snapshot) and history (forbidden,
timeline), so neither swallows the other.

This principle unlocks principle P4 — much of what contributors
might otherwise want to store redundantly is actually history
masquerading as state.

**Concretely forbidden patterns.** Any of these in a tracked
markdown file is a P5 violation and must not land:

- Strikethrough-landed lists: `~~**item**~~ (landed abc1234)`, or
  a "Remaining work" list where completed items are struck through
  with commit SHAs appended. When an item lands, it leaves the
  list — git log holds the landing record.
- Retroactive notes: "Note (YYYY-MM-DD): this has since been
  closed", "as of <date>", "since the initial write-up". If the
  doc's content is stale, fix the content; don't bolt a patch on
  top narrating the drift.
- Commit SHAs in prose: "fixed in commit abc1234", "see f00b4r7
  for the rationale". The doc should describe what IS; readers
  who need rationale use `git log` / `git blame` against the
  lines in question.
- Timestamped status lines: "**Status:** direction accepted
  2026-MM-DD", "Done 2026-MM-DD", "Landed 2026-MM-DD". If the
  direction is current, just state the direction; if the direction
  was superseded, update the doc to the current direction.
- Progress-log sections: "## Resolved", "## Done", "## Changelog",
  "## History". Resolved items disappear; they don't accumulate
  in a section.
- "Forthcoming" / "will land" / "pending" references to work
  already in the repo. When the work lands, remove the promise.

**No agent-authorized exceptions.** The first move on encountering
timeline-in-content — a historical reason for a decision, a "how it
was achieved" note, a migration narrative, a maintained CHANGELOG — is
always the default: delete it or rewrite to current state, and let
`git log` carry the why. An agent never grants itself an exception. The
exception path opens only when rewriting to a current-state snapshot
would lose meaning the repo genuinely needs; even then the agent does
not decide. It halts, names the specific content and why a snapshot
loses it, and surfaces the call to the human responsible for the repo —
the user in this framework's own repo, the project owner in an
installed one — proceeding only on their explicit sign-off for that one
instance. Absent that sign-off, the snapshot rule wins.

**Archival docs use dated filenames.** Historical design reviews,
snapshots, and retrospectives that are intrinsically dated go
under `docs/design-docs/YYYY-MM-DD-<slug>.md` (or the equivalent).
The dated filename IS the snapshot timestamp — readers know the
doc is an archival record from its filename alone, and no
in-content dating or retroactive annotation is needed. Internal
references to other archival docs by their dated filenames are
fine; they are pointers to identified artifacts, not timeline
annotations.

### P6. Code, specs, and backlog win

**What delivered code, committed specs, and the backlog say is true
trumps any document that says otherwise. If a Binder claims WI12 ships
something but WI12's spec/code shipped something different, the
spec/code win — the Binder is stale or wrong.**

This establishes the authority hierarchy when artifacts disagree.
The validator and agents resolve conflicts by trusting the
lowest-level artifact that carries the disputed fact:

| Conflict | Winner |
|-|-|
| Binder narrative vs. backlog state | Backlog |
| Backlog entry vs. spec content | Spec |
| Spec vs. delivered code | Code |
| Delivered code vs. test outcomes | Test outcomes |

A Binder claiming a feature that was never implemented is a stale Binder,
not a missing feature. The validator and agents flag this but do
not "correct" the upstream artifact by inventing work.

---

## The execution principle

### P7. Halt with call-to-action

**Pipeline halts are features, not bugs, when paired with specific
actionable next-step messages. Silent halts and blind continuation
are the failure modes to avoid.**

When any gate, validator, agent, or skill cannot proceed, it must:

- **Halt explicitly.** Not silently exit. Not fall through to the
  next stage. Not invent a recovery path.
- **Emit a specific, actionable message** telling the next actor
  (usually the human) exactly what to do to unblock. Not just
  *"validation failed"* — a *concrete* next step.
- **Name the specific cause.** Not *"invalid state"* — the exact
  field, entry, or condition.

Examples of correct halts:

> *"Feature WI11 has no `Binder:` or `Binder-exempt:` field, and the
> KEEL-INVARIANT-7 cutoff is WI10. Add `Binder: <slug>` pointing to an
> existing Binder at `docs/exec-plans/binders/<slug>.json`, or add
> `Binder-exempt: <reason>` where reason is one of legacy, bootstrap,
> infra, or trivial."*

> *"Walk complete. 8 cards drafted for Binder: user-password-auth. Are
> all WI08-WI15 from this Binder ready? Verbs: commit, revisit WI##,
> abort."*

> *"WI26 has 2 unresolved HUMAN markers blocking the pipeline.
> Resolve them in `backlog.md` by editing the entry, then
> re-run `/keel-pipeline WI26`. See marker-resolution workflow in
> the project guide."*

Examples of failures the principle forbids:

- Exiting a skill without a final message because "the user can
  figure out what to do."
- Continuing past a failed validation "to be helpful."
- Retrying a failing operation in a loop without new information.
- Guessing at a recovery path (e.g., auto-creating a missing Binder
  file with a placeholder).

Required steps halt rather than fall through. When a pipeline verb
cannot proceed, the correct behavior is to halt with a call-to-action,
never silent fallthrough.

---

## Using these principles

### In framework-level decisions

Every design conversation around KEEL edits — new agents, new
skills, new validator rules, new file conventions — must weigh the
proposed change against these principles. If the change violates
one:

1. Restate the problem. Often the original frame is the issue, not
   the design.
2. Check if a sibling design satisfies the principle without losing
   the motivation.
3. If no sibling satisfies the principle, the principle wins.
   Principles override convenience.

Maintainers running roundtable deliberations should paste the
principles into the prompt so the panel attacks proposals under the
same framing.

A complementary proposal-evaluation gate lives in `AGENTS.md`
§"Framework proposal design: defaults + knobs" (two-org test,
least-assuming default, knobs-cannot-override-P1–P7, knob altitude
table). P1–P7 audit the resulting artifact; that section audits the
proposal that produces it. Both apply to any framework-level edit.

### In agent and skill prompts

Agents that make decisions about storage, derivation, or halt
behavior should reference this doc in their prompt headers:

- `pre-check` — applies P6 (authority hierarchy) and P7 (halt-with-CTA)
  on every gate.
- `backlog-drafter` — applies P4 (no redundant storage) when deciding
  what goes in drafted entries vs. derived.
- `safety-auditor` — applies P6 (artifact authority) when reconciling
  drift between specs and code.
- `doc-gardener` — applies P4 and P5 when sweeping for drift.

Skills that halt conditionally — `/keel-refine`, `/keel-pipeline`,
`/keel-adopt` — should reference P7 in their halt semantics: every
exit path must produce an actionable message.

The canonical reference path in every user install is
`docs/process/KEEL-PRINCIPLES.md`. It ships via `PROCESS_DOCS` in
`scripts/keel_manifest.py` and is copied by `scripts/install.py`.

### When principles conflict

They are designed to be orthogonal. If a real conflict arises:

- **P1 (legibility) + P4 (no redundant storage) conflict** when
  making a fact self-legible would require storing it redundantly.
  **Resolution:** prefer the form that is legible *given P2
  (progressive disclosure)*. Agents can follow a pointer cheaply;
  caches stale expensively. Pointers over inline redundancy.
- **P5 (snapshot, not timeline) + P3 (self-sufficient) conflict**
  when a view requires knowing when something happened.
  **Resolution:** the view is a timeline view, not a snapshot
  view, and belongs in `git log` output, not in the repo snapshot.
- **P6 (artifact authority) + P4 (no redundant storage) conflict**
  when an artifact encodes a fact that's derivable from a
  lower-authority one. **Resolution:** the lower-authority
  derivation wins, per P6 itself. The higher-authority artifact is
  storing a cached assertion.
- **P1 (legibility) + P4 (no redundant storage) conflict** when a
  derivable fact would aid legibility if cached inline at the point
  of use. **Resolution:** prefer a *pointer* to the source over an
  inline cache, per P2 — a cache stales expensively, a pointer is
  cheap to follow. This is the same resolution direction the first
  pair above takes; stated here as its own pair because the
  temptation recurs (a derivable-but-legibility-helpful cache) and
  the answer is always the pointer.

Conflicts are rare. Most apparent conflicts are false — one frame
satisfies all principles; finding it is the design work.

---

## Framework fidelity

These principles are the framework's own contract. If a KEEL
maintainer proposes a change to the framework itself (to agents,
skills, validators, scripts, or this file), that change goes through
the same principles-governed design process. The framework
dogfoods its own rules.

This doc is stable. Major edits to the principles warrant
multi-perspective review (e.g. roundtable) and a note in `git log`
explaining the shift. Minor edits (clarifying examples, fixing typos)
can land directly.
