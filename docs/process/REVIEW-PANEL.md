# Review Panel — doctrine

The pipeline pauses at three checkpoints to subject a decision to
adversarial, multi-perspective review before committing to it: after
**pre-check** (is the feature understood and routed correctly?), after
**design** (is the blueprint sound?), and after **landing** (did the
feature land correctly and safely?). This doc defines how that review
runs.

Two panels can serve those checkpoints, and **exactly one of them runs
for a given feature — personas or roundtable, never both.** The choice
is resolved once (Step 0.5) and governs all three of that feature's
checkpoints; the panels are alternatives, never combined or run in
sequence. They are interchangeable at the verdict boundary — each emits
the same `APPROVED | CONCERNS` verdict and the same kickback semantics —
so the pipeline steps cite this doc and stay panel-agnostic.

- **Persona panel (default).** In-process review by independent
  reviewer personas, each dispatched as a parallel sub-agent. Needs
  nothing but your agent host, so it is always available.
- **Roundtable (opt-in).** External multi-model review over the
  `roundtable` MCP server. Adds cross-vendor diversity at the cost of
  external round-trips and probe latency. Selected per project or per
  feature; falls back to the persona panel when unavailable.

The panel is **advisory**. The authoritative author of each artifact —
pre-check for routing, the designer for the blueprint, the landed code
itself for landing — remains in charge. Review surfaces concerns; it
never overwrites the artifact or halts the pipeline on its own.

## The personas

A fixed panel of four **functional review lenses**. They are lenses,
not domain experts: each adapts its focus to whatever artifact the
touchpoint puts in front of it (a routing decision, a design blueprint,
a landed diff). A lens with nothing to flag says so in one line — silence
is a signal, not a quota to fill.

| Lens | Asks | Primary at |
|-|-|-|
| **Skeptic** | What is unstated or assumed? What is missing? Which edge cases break this? Is this the smallest testable unit, or is something hiding inside it? | pre-check, landing |
| **Architect** | Is the structure sound and as simple as the problem allows? Does it fit existing patterns? What will be painful to change later? | design |
| **Adversary** | How does this fail in production? Where are the trust boundaries, the unvalidated inputs, the fail-open paths, the abuse cases? | design, landing |
| **Pragmatist** | Is this the right scope — no more, no less? What is over-built (YAGNI) or under-specified? What is the shipping risk? | pre-check, design |

"Primary at" is guidance, not a gate: every lens reviews every
touchpoint. The column says where each tends to carry the most weight,
so the synthesizer can weight a tie accordingly.

## Protocol

1. **Dispatch in parallel.** Launch one `review-panelist` agent per
   persona, concurrently, each with: the artifact under review, the
   review question for this touchpoint, the persona definition, and the
   relevant handoff context. Parallel dispatch is the point — wall-clock
   is roughly one reviewer's time, not the sum.
2. **Review in character.** Each panelist returns a natural-language
   review through its lens — top findings first, each with `file:line`
   (or the specific decision), *why* it matters, and a concrete
   suggestion; then lesser observations; then what is genuinely sound.
   No rigid schema — forcing structure costs insight. Each finding
   carries a severity: `critical` / `major` / `minor` / `style`.
3. **Synthesize.** The orchestrator reconciles the reviews into one
   prioritized findings list:
   - tag each finding `agreed` (≥2 lenses), `solo` (one), or `tension`
     (lenses disagree — note both positions in one line, and which the
     artifact's context favours);
   - order by severity, ranking `agreed` above `solo` at equal severity.
4. **Verdict.** Emit `APPROVED` when no `critical` or `major` finding
   stands unresolved; otherwise `CONCERNS`, naming the specific findings
   the authoritative stage must address. This is the same verdict
   contract the roundtable emits, so downstream routing is identical.

## Verdict, loop, and kickback

- A `CONCERNS` verdict kicks back to the artifact's authoritative stage
  (pre-check re-routes; the designer revises; for landing, the
  orchestrator opens a fix cycle). The stage revises, then the panel
  re-reviews.
- **Two attempts.** If concerns persist after a second review, the
  orchestrator records the unresolved concern and **proceeds** — review
  is advisory and must not deadlock the pipeline (P7: it does not halt
  silently; it logs the override with its reason). The escalation path
  is the human, not an infinite loop.
- Panel deliberation is written as a new file
  `<touchpoint>-review/attempt-NN.md` per attempt (the file body begins
  `### Attempt N — <verdict>`), exactly as the roundtable's deliberation
  is recorded. Earlier attempt files stay; the authoritative agent output
  file is still snapshot-overwritten on revision.

## When the panel splits

*Applies to the roundtable panel's convergence path. The persona panel
uses the two-attempt loop above and has no convergence step.*

`roundtable-canvass` is a single-round consensus synthesis: when the
panel reaches a clear majority or unanimous view it returns a clean
recommendation. When the panel **genuinely splits** — different models
defending incompatible positions on the same prompt — canvass surfaces
the disagreement without resolving it.

`roundtable-converge` is the reactive second round. It replays the prior
dispatch back through the same panel with each panelist's prior answer
relabelled under peer-redacted aliases (`peer-1`, `peer-2`, …); each
model re-evaluates with full visibility of the others' reasoning but no
provider-identity bias, and returns (a) a hold-or-revise stance, (b) an
agreement list, and (c) a draft converged recommendation.

**Opt-in, not prescribed.** At any roundtable call site — pipeline Steps
1.3 / 2.5 / 8.5, plus the `/keel-setup` architecture and invariants
gates, the `/keel-adopt` invariants gate, and the `/keel-refine`
backlog-decomposition gate (seven sites total) — if the orchestrator
cannot reconcile the canvass output before declaring `CONCERNS` or
handing off to the human, it **MAY** invoke `roundtable-converge` on the
prior dispatch as a final reconciliation pass.

**Skip convergence when:**
- the panel already agreed — there is nothing to resolve;
- the panel has a single model — no peers to redact, so the tool is a
  structural no-op;
- time or token budget would not afford a second round — proceeding with
  `CONCERNS` is the right call;
- the split is stakes-free (cosmetic, framing-only) — pick one and move on;
- the orchestrator can confidently resolve the split itself from the
  canvass output.

Convergence does **not** change the halt-with-CTA contract (P7): it runs
*before* the human handoff, not instead of it. If convergence still
leaves the panel split, the existing `CONCERNS` / human-handoff path
applies — convergence cannot block the CTA.

## Selecting the panel

Resolved once, at Step 0.5, into `routing.json`'s `review_panel` field:

1. **Per-feature override wins.** A `Review: roundtable` (or
   `Review: personas`) field on the backlog entry selects the panel for
   that feature. Use it to give one high-stakes feature the external
   panel, or to pin one feature to personas regardless of the project
   default.
2. **Else the project default.** `Review panel: personas|roundtable` in
   the project guide. Absent ⇒ `personas`.
3. **Fallback.** If `roundtable` is selected but the MCP server is
   unavailable at run time, fall back to the **persona panel** and log
   the fallback. Review always happens; it is never silently skipped.

Default is `personas` because it assumes only your agent host — the common
install — and gives a single-host project *more* review than the old
default did (external roundtable skipped entirely when its CLIs were
absent). A project with Gemini/Codex CLIs that values cross-vendor
diversity opts into `roundtable`.
