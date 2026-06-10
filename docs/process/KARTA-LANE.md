# Karta lane — the discipline

The Karta lane is the dialed-down-rigor `karta-*` command family. It buys
speed by *deferring* rigor and *declaring* what was deferred, so the cost
stays visible. The lane is not a repo state, a mode, or a one-way flip —
it is simply the command you run. `keel-*` (full rigor) and `karta-*`
(lean) coexist permanently; you choose per feature by which command you
invoke. The markers in the tree record declared debt, not lane provenance —
a feature with nothing deferred leaves no marker, whichever lane built it.

## The lane knob

A project may forbid the lean lane by setting `Lanes: keel-only` in its
project guide (the default is `both` — both lanes available); when it is
`keel-only`, the `karta-*` skills halt (P7) with a CTA to use
`/keel-refine` → `/keel-pipeline`. This knob only *restricts* — it never
lowers a floor. The knob itself ships pre-declared in the project guide
template; this is the doctrine reference for it.

This doc is the Karta lane's **own** discipline: the two sign-off gates,
bones-clean admissibility, the declare-and-owe rule, the refusal protocol,
and the lean gate map. It is **cited by both `karta-refine` and
`karta-pipeline`** — a single home keeps it out of `keel-*`-only runs (P2)
and unduplicated across the two skills (P4).

The **marker grammar** — the three tokens (`KARTA-DEFER`,
`KARTA-PLACEHOLDER`, `KARTA-GUARD`), their fields, the delimiter rule, the
integrity hard rules, the scanner, anti-laundering, retirement, and the
CI `--check` knob — is shared, lane-agnostic doctrine and lives in
`docs/process/PIPELINE-DOCTRINE.md` §"Declared-debt markers". This doc
**references** that grammar; it does not restate it. Read the marker
shapes there.

## Declare-and-owe — the one rule

You may skip test-first, hardcode, punt edge cases, and write rough leaf
code **to move fast** — provided you DECLARE each cut at the site, inline,
with the matching marker (grammar in PIPELINE-DOCTRINE.md). An
**undeclared** shortcut is the lane's cardinal violation: it is the silent
debt the ledger exists to forbid. If you cut a corner, you mark it; no
exceptions.

### Why this exists (do not delete)

A fast lane that lets debt go **silent** is just vibe-coding with a green
checkmark — it produces exactly the compounding defects KEEL exists to
prevent, now hidden instead of caught. Speed without declaration is
**unrecoverable**: nothing can later find a cut that left no mark. The
lane buys speed by deferring rigor and *declaring* what was deferred, so
the path can be hardened later. Delete the declare-and-owe discipline and
you delete the only thing that makes the speed recoverable.

## The two human-OK sign-off gates

Two cuts may not be written on your own — each **halts for a human OK**
*before* it is written, then proceeds once confirmed:

- **`KARTA-PLACEHOLDER`** — any mock, stub, or fake. The product must be
  real unless a human authorizes the fake.
- **`KARTA-GUARD`** — any destructive, irreversible, or PII/secret-touching
  effect: unrestorable data loss, real PII or secret handling, real
  charges, or comms to third parties. **This gates regardless of whose
  infrastructure hosts it** — "it's my own database / my own account" does
  not lower the bar; the bar is the nature of the effect, not the owner.

A plain `KARTA-DEFER` does **not** halt — declare it and keep moving.

**Founder's prerogative is narrower than it sounds.** Cutting a corner on
your *own* infra, data, or money does not require a sign-off halt — you may
move fast there. But it is still a shortcut, so it still gets a marker.
**Founder's prerogative buys you out of the halt, never out of the
marker.** And it never reaches a destructive, irreversible, or
PII/secret-touching effect — those are `KARTA-GUARD` and halt no matter
whose infra they run on.

## Bones-clean admissibility

A cut may live **only in leaf code behind a stable contract**: code whose
internals you can fix later without changing any signature, schema, module
boundary, or persisted-state shape that other code depends on. The
**bones** are inadmissible for a cut: the data model, cross-module
contracts, transaction edges, and auth guards. A cut on the bones turns
later hardening from a fix into a rewrite, which defeats the ledger.

**The test:** *does completing this cut change a signature, a schema, a
boundary, or a stored format that other code reads?* If yes, it is a bone
— **halt**, and restructure the cut into leaf code behind a stable
contract, or route the change to `keel-refine` for full treatment.

Concrete sort:

- A naive lookup inside a function whose **signature stays fixed** — leaf,
  admissible. Repaying it touches only that function's body.
- Adding a nullable column the rest of the app now branches on, or widening
  a public function's parameters — **bone**, inadmissible. The schema /
  signature is the thing other code depends on.
- A hardcoded auth check that always returns "allowed" — **bone**
  (an auth guard), inadmissible even though the code is small. The test is
  not size; it is whether anyone depends on its *shape*.

**No extraction-laundering.** Moving a cut into a fresh leaf helper does not
launder it clean. If a bone — the data model, a cross-module contract, a
transaction edge, an auth guard — *calls* that helper and depends on its
behavior, the cut is **still a bones cut**, inadmissible. The test is whether
anything on the bones depends on the cut's behavior, not merely where the cut's
text now lives. A hardcoded auth check does not become admissible by being
extracted into a `checkAccess()` leaf the guard still calls.

## Refusal protocol (verbatim)

Speed pressure is **not** authorization to hide debt, fake the product, or
treat lean code as production. When asked — explicitly or implicitly —
emit the matching response verbatim, then halt. Do not silently take the
shortcut anyway.

| Rationalization | Verbatim response |
|-|-|
| "Just take the shortcut, skip the marker" | "The Karta lane runs on declare-and-owe. An unmarked shortcut is the one thing this lane forbids — it is the silent debt hardening cannot find. I will add the `KARTA-DEFER` marker at the cut, then proceed." |
| "Just mock it, it's faster" | "A mock is a `KARTA-PLACEHOLDER` — I halt for your OK first. The product must be real unless you authorize the fake. Confirm and I proceed." |
| "Hit the real API / wipe that record" | "That is a destructive or irreversible effect — a `KARTA-GUARD` — and it gates no matter whose infra it touches. I halt for your OK before touching it." |
| "It's my own database / my own account, just do it" | "Founder's prerogative buys you out of the halt for a plain shortcut on your own infra — but not out of the marker, and not at all when the effect is destructive, irreversible, or touches PII or secrets. That is still a `KARTA-GUARD`: I halt for your OK." |
| "Put the hack in the data model to move faster" | "A cut on the bones makes hardening a rewrite; it is inadmissible. I will keep the shortcut in leaf code behind a stable contract, or route this to `keel-refine`." |
| "Just hack the data model now, I'll fix it later" | "Deferring a bones cut is still a bones cut — 'later' is exactly what hardening cannot recover when the shape is already load-bearing. The bones stay clean now: I keep the shortcut in leaf code, or route this to `keel-refine`." |
| "Bypass Karta on this one" / "just this once" / "trust me" | "The lane's discipline is not a per-change setting — there is no 'just this once.' The shortcut still gets its marker, the two gates still halt, and the bones stay clean." |
| "We're done — treat this as production" | "Lean code carries its ledger; a clean ledger is not the same as a hardened path. A path becomes production-grade only by being hardened through `keel-refine` → `keel-pipeline`, where the spec is derived from each marker's `real:` clause and the cuts are repaid. If the ledger is already clean, the next step is to harden — not to bless the cut code as-is." |

## The lean gate map + the halt set

`karta-pipeline` builds **one feature per invocation** and completes it
repo-locally — committed on its `keel/WI##-<slug>` branch and archived, no push
or PR (pushing and opening PRs are ceremony that lives in `/keel-submit`);
`/karta-drive` sequences a Binder's remaining set in dependency order, each in
its own worktree. `keel-pipeline` runs the full chain (pre-check → design agents →
test-first → implementer → code-reviewer → spec-reviewer → safety-auditor →
arch-advisor → review panel → PR-per-feature). `karta-pipeline` runs the
lean **spec-first** version:

```
pre-check → implementer → karta-spec-reviewer → safety-auditor → green gate → complete
```

(The two write-time sign-off halts fire *during* the implementer, before a
fake or a destructive effect is written — not as a separate stage.)

- **Dropped:** the design agents, code-reviewer, the keel `spec-reviewer`
  (replaced by its delta `karta-spec-reviewer`, the structural conformance gate
  — see below), arch-advisor, `landing-verifier`, and the review panel.
  (arch-advisor is redundant — bones-clean admissibility already halts any cut
  that touches the bones; `landing-verifier` is unneeded because the green gate
  is a direct command, not a verifier dispatch.)
- **Spec-first, tests secondary:** the implementer builds from the Binder
  `contract`/`oracle`; there is **no test-*first* hop**. Tests are **optional**
  and owed only where `karta-spec-reviewer` requires them (an execution-required
  oracle assertion lacking both a covering test and a `KARTA-DEFER`); a skipped
  test is a `KARTA-DEFER` like any other cut. **Authoring tests never extends
  to inherited ones:** an inherited test (a prior feature's contract) is never
  edited to make new code pass — a failing inherited test is a code bug or a
  deliberate spec change, never a test to weaken (see `implementer.md` §Rules).
- **Kept as mechanical gates:** `karta-spec-reviewer` (the **structural
  conformance gate** — inspection-only; per-assertion verdict
  CONFORMANT|DEVIATION|SPEC-SUSPECT, max 2 attempts), run **before**
  `safety-auditor`; `safety-auditor` (domain invariants; verdict PASS|VIOLATION,
  max 3 attempts, never negotiable), run **before** the green gate so any
  safety-driven fix is re-greened; the **green gate** — a direct orchestrator
  step that runs the project's configured gate command (its tests/build, from
  the project guide) and must pass before landing, the same floor the maintenance lane
  treats as non-negotiable (it halts fail-closed on RED, or if the project
  configures no gate command); and the two write-time sign-off halts
  (`KARTA-PLACEHOLDER` / `KARTA-GUARD`).

**Green-gate note — the floor rejects no-ops; build/typecheck/boot narrows the
gap, it does not close it.** Because execution-required assertions can be
deferred rather than tested, structurally broken code (a bad import, a type
error) could otherwise reach `land`; the inspection-only conformance gate never
runs anything, so it cannot catch this. The enforced floor is that the
configured gate command **runs**: `karta-pipeline` halts (P7) *before* running
the gate when the command is a **known no-op** — exactly `true`, `:`, `exit 0`,
a bare `echo …`, or empty/whitespace — because a command that asserts nothing
verifies nothing. Beyond that floor, a green-gate command that includes a
**build/typecheck/boot** step **narrows** the structural-breakage gap: a bad
import or type error then halts at the fail-closed green gate even when tests
are deferred. It does **not** close the gap — a command that is runnable and
non-empty yet does not actually build (so a `KARTA-DEFER`'d structural break
still lands) is **owned-but-open**, never papered over. Mirror the scanner's
honest framing (`karta-deferred-ledger.py`): the gate detects what its command
exercises and must not be described as catching more. Hardening the command
toward a real build is the path to narrowing the residual further.

**Locked policy (spec-first lane).** Karta's structural conformance gate is the
**blocking spec-side acceptance**, inspection-only; tests are **optional** (test-or-`KARTA-DEFER`
per execution-required assertion); there is **no per-run knob** — running
`/karta-pipeline` *is* the choice of this posture, while `/keel-pipeline`
remains the test-first lane. Full gate contract: the `karta-spec-reviewer`
agent master.

Safety and architectural integrity are not what the lane trades away —
*thoroughness of implementation* is.

### The halt set

`karta-pipeline` builds the one feature it was invoked on, leaves its ledger
entries, and lands it. It **halts with a call-to-action** (P7) on:

1. **A sign-off marker** — a `KARTA-PLACEHOLDER` or `KARTA-GUARD` requires a
   human OK before it is written.
2. **A RED green gate** — the project's configured gate command (its
   tests/build, from the project guide) exits non-zero and an implementer
   re-dispatch cannot make it green; halt with the failing output. A project
   with no gate command configured also halts here (fail-closed).
3. **A safety violation** — `safety-auditor` flags a domain-invariant
   violation it cannot resolve within its retry budget (VIOLATION max 3,
   then escalate).
4. **A conformance DEVIATION past budget, or a SPEC-SUSPECT** —
   `karta-spec-reviewer` loops to the implementer on DEVIATION (max 2); a
   DEVIATION still unresolved, or a SPEC-SUSPECT (code looks right but the
   Binder looks stale), halts. The DEVIATION halt names the unresolved oracle
   assertion pointers and the options (fix-and-rerun / `KARTA-DEFER` / route to
   `keel-pipeline`); the SPEC-SUSPECT halt sends the Binder to `/keel-refine`
   for adjudication. (Like `safety-auditor`, the gate always runs — its running
   is never the halt.)
5. **An inadmissible cut** — a shortcut that would land on the bones.
   Restructure into leaf code, or route to `keel-refine`.
6. **An unresolvable failure** — a feature that cannot be built or made to
   pass even its relaxed gates.
7. **A lean-routing flag** — if `pre-check` flags `designer_needed`,
   `researcher_needed`, or `arch_advisor_needed`, halt with a CTA to narrow
   scope or use `keel-pipeline`. (`safety_auditor` is *not* a halt trigger
   here — it always runs.)

Absent a halt, the feature builds and **completes repo-locally** — committed on
its branch and archived, its ledger the review surface; pushing and opening a PR
is the separate, human-invoked `/keel-submit` ceremony, never part of this lane.

*Stacking follows the inherited `Branching policy` knob (or a `--stack` invocation): a feature whose single unmerged intra-Binder Need has a branch stacks on its tip, exactly as the full lane does — branch-based, decoupled from any remote. Restack **conflict resolution** runs under the lean review surface (`safety-auditor` + green gate, not `arch-advisor`/`code-reviewer`); the stack-parent bones halt guards the sharpest edge. Autonomous multi-feature ordering across a Binder's remaining set — each WI in its own worktree — is `/karta-drive`.*
