---
name: karta-refine
description: "Lean-lane sibling of /keel-refine. Drafts a structured JSON Binder plus backlog entries for a lower-rigor build, using the SAME `schemas/binder.schema.json` shape — no second schema. Optional Binder-frame fields may be left empty within schema validity (one-line motivation, minimal scope, design_facts/invariants a subset). Skipped IMPLEMENTATION rigor is recorded by code markers at the cut site, never by a placeholder string in the Binder. Presents the same editable cards; commits on an explicit 'commit' verb. Never auto-runs the pipeline."
---

## Framework principles

This skill is a **delta** of `keel-refine`, not a fork. It inherits
`keel-refine`'s entire authoring machinery and authors only the
lower-rigor guidance below. The duplication discipline is P4 (no
redundant storage — the shared phases are authored once, in
`keel-refine`, and cited here; copying them would create a cache that
stales). The lean-authoring delta also leans on P2 (progressive
disclosure — the lane discipline lives in `docs/process/KARTA-LANE.md`,
cited not restated) and P7 (every exit path the inherited skill
produces still halts with a call-to-action). See
[`docs/process/KEEL-PRINCIPLES.md`](../../../docs/process/KEEL-PRINCIPLES.md).

# Karta Refine

The lean-lane drafting hub. `karta-refine` produces the **same artifact**
as `/keel-refine` — a structured JSON Binder at
`docs/exec-plans/binders/<slug>.json` (schema_version 1, validated
against `schemas/binder.schema.json`) plus the matching WI## entries in
`docs/exec-plans/active/backlog.md` — and runs through the same phases,
the same card walk, the same accept gates, the same materialization, and
the same validator. The lane is not a mode, a tag, or a repo flag: it is
**simply the command you run**. See `docs/process/KARTA-LANE.md`.

The only difference between the two skills is *authoring posture*. Where
`/keel-refine` pushes for a fully fleshed Binder frame, `karta-refine`
**permits brevity within schema validity** — a one-line motivation, a
minimal scope, a `design_facts` / `invariants_exercised` subset. Skipped
*implementation* rigor (test-first skipped, a hardcode, a punted edge)
is not recorded in the Binder at all: it is declared at the cut site by
a `KARTA-DEFER` / `KARTA-PLACEHOLDER` / `KARTA-GUARD` **code marker**
when `karta-pipeline` builds the feature. The Binder records *what the
feature is*; the markers record *what was cut building it*.

## Lane gate (first, before any phase)

Before the inherited Phase 0 preflight, read the project guide
§"Pipeline Preferences" for a `Lanes:` key (`keel-only | both`; absent ⇒ `both`,
the least-assuming default — both lanes available is the common case). If
`Lanes: keel-only`, the project restricts work to the full-rigor `keel-*` lane,
so this skill must not run → HALT (P7): *"this project sets `Lanes: keel-only`,
restricting work to the full-rigor `keel-*` lane; run `/keel-refine` (→
`/keel-pipeline`) instead."* Absent or `Lanes: both` → proceed to Phase 0. The
knob only **restricts**; it never lowers a floor. Policy:
`docs/process/KARTA-LANE.md` §"The lane knob".

## Inherited wholesale from `/keel-refine` (cited, not copied)

Read the `keel-refine` skill. Every phase below is executed
**exactly** as that skill specifies — this skill does not restate them:

| Inherited surface | Source section in `keel-refine` SKILL.md |
|-|-|
| Preflight + bootstrap gate + session dir | Phase 0: Preflight |
| Intent ingestion (prose / markdown / bundle / images) | Phase 1: Intent Ingestion |
| Repo-context gathering, `next_free_id` freeze, schema enum preflight | Phase 2: Repo Context Gathering |
| `backlog-drafter` dispatch + output validation | Phase 3: Agent Dispatch |
| Roundtable decomposition review (advisory, opt-in) | Phase 3.5 |
| Interview loop + budgets | Phase 4: Interview Loop |
| Card 0 (the Binder frame) + per-card WI## walk + verbs + accept gates | Phase 5 §Step 2a, §Step 2, §Step 3 |
| Prototype disposition card | Phase 5 §Step 2a-bis |
| Materialize: assemble JSON, write backlog, atomicity/rollback, commit, cleanup | Phase 6: Materialize + Announce-Commit |
| JSON Binder validation | `uv run scripts/validate-binder-json.py` (Phase 6 Step 4) |
| Commit/write/read rules, drafting invariants, failure-mode table | §Rules, §Failure Modes |

If any of these need to change, change them in `keel-refine` — both
skills read the one source. Forking a phase here is the P4 violation this
delta exists to avoid.

## What this skill authors (the lean-authoring delta)

The delta is **guidance that permits brevity** — it loosens nothing in
the schema and adds no new field, marker, or tag. It lives entirely in
how Card 0's Binder-frame fields are drafted and reviewed.

### Lower-rigor authoring guidance for the Binder frame

When seeding and walking **Card 0** (Phase 5 Step 2a in `keel-refine`),
the lean posture is:

- **`motivation` — one line is enough.** A single sentence on why the
  feature exists is a complete lean motivation. Do not pad to a
  paragraph to look thorough. (Schema permits any string ≤ 800 chars;
  brevity is honest, not a gap.)
- **`scope.included` — minimal and concrete.** One or two bullets
  naming what ships. The schema requires at least one included bullet
  (`minItems: 1`); a lean Binder gives exactly the bullets that are
  true and stops. `scope.excluded` may be empty.
- **`design_facts` — a subset, or empty.** Record only the decisions
  that are *already made and load-bearing*. A lean feature legitimately
  has few or none; leave the array empty rather than inventing facts to
  fill it. (Empty `design_facts` is schema-valid.)
- **`invariants_exercised` — only what genuinely applies.** Cite the
  domain invariants this feature actually touches. If it touches none,
  the array is empty — the same honest-empty rule as the full lane.
  (Empty `invariants_exercised` is schema-valid; the
  zero-registered-invariants advisory from `keel-refine` Phase 2 still
  fires.)

The WI## cards (`contract`, `oracle`) are **not** relaxed here. A lean
feature still needs a real contract and at least one oracle assertion —
that is what makes the feature buildable and verifiable at all. The lean
lane defers *implementation thoroughness*, not the acceptance spec; the
oracle is the spec. The card-walk accept gates from `keel-refine` Phase 5
apply unchanged.

### Where skipped implementation rigor is recorded

**Never in the Binder.** A skipped test, a hardcode, a punted edge, a
mock, or a sensitive effect is recorded by a **code marker at the cut
site** — `KARTA-DEFER`, `KARTA-PLACEHOLDER`, or `KARTA-GUARD` — written
by `karta-pipeline` when it builds the feature, per
`docs/process/PIPELINE-DOCTRINE.md` §"Declared-debt markers" (grammar,
fields, delimiter rule, scanner) and `docs/process/KARTA-LANE.md`
(declare-and-owe, the two sign-off halts, bones-clean admissibility).

There are exactly **three** markers — `KARTA-DEFER`,
`KARTA-PLACEHOLDER`, `KARTA-GUARD` — and they live only in code, never in
a Binder field. This skill does **not** introduce:

- a `KARTA-MINIMAL` marker, or any fourth marker — the lane records
  nothing on the Binder, so it needs no "this is a lean Binder" token;
- a placeholder string (e.g. `"KARTA-DEFER: ..."`) stuffed into a Binder
  `motivation` / `design_facts` / `contract` — an empty optional field
  is the lean signal, and the schema permits it (P4: a placeholder
  string is derivable cruft that stales);
- a `Lane:` / `--lane` config, a `Binder-exempt` lane tag, or a
  parallel lane registry — the lane is the command you ran, and the code
  markers are the sole record of declared *debt*, not of lane provenance
  (`KARTA-LANE.md`).

A Binder drafted here is **indistinguishable in shape** from one drafted
by `/keel-refine`. That is intentional: it lets a lean feature be
hardened later by re-running `/keel-refine` → `/keel-pipeline` over the
exact same Binder, with the `real:` clause of each marker driving the
hardening spec. No Binder-side bookkeeping needs to be unwound.

## Lean specs and the Binder schema

The lean posture reuses the shared Binder schema unchanged — it already
permits honest emptiness: `motivation`, `design_facts`, and
`invariants_exercised` may be present-but-empty and still validate. A lean
feature needs no schema fork, no placeholder strings, and no per-field
annotation.

The one floor the schema (and the `keel-refine` Card 0 accept gate) holds:
a feature needs a non-empty `motivation` and at least one `scope.included`
bullet. A truly minimal feature can state one included bullet; a feature
that cannot state even one is not yet specifiable — write a little more
before refining it.

## When to use

Use `karta-refine` instead of `/keel-refine` when you are deliberately
building this feature in the **lean lane** — speed bought by deferring
implementation rigor and declaring each cut at its site. The choice is
the command; nothing in the repo records it but the eventual code
markers. The lane discipline — declare-and-owe, the two sign-off halts,
bones-clean admissibility, the refusal protocol — is in
`docs/process/KARTA-LANE.md`. Read it before running the lane.

**Not for:**

- A feature you want built at full rigor → use `/keel-refine`.
- Initial project setup → `/keel-setup` (greenfield) or `/keel-adopt`
  (brownfield). The inherited Phase 0 bootstrap gate enforces this.
- Hand-editing the JSON Binder → it is KEEL-authored; steer via the
  card walk, same as `/keel-refine`.

## Rules (delta only — all `keel-refine` §Rules apply unchanged)

- This skill **never** runs `karta-pipeline` or `/keel-pipeline`. Like
  `/keel-refine`, it drafts and commits; building is a separate,
  human-initiated command. (Inherits `keel-refine` §Rules "Never run the
  pipeline.")
- This skill writes **no** code and therefore writes **no** markers. The
  three code markers are written by `karta-pipeline` at build time, not
  here. `karta-refine`'s write surface is identical to `keel-refine`'s:
  `<slug>.json`, the backlog, session workspace, and the one-time
  `.gitignore` line.
- The lean posture relaxes only the four Binder-frame fields named above.
  It never relaxes a WI## card's `contract` or `oracle`, never relaxes a
  schema constraint, and never relaxes an inherited accept gate.
