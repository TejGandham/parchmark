# Pipeline Failure Playbook

What to do when the pipeline doesn't produce a clean landing. This is a
decision tree, not a troubleshooting guide — follow the first matching case.

---

## Decision Tree

```
Pipeline stalls or produces bad output
  │
  ├─ spec-reviewer finds CRITICAL deviation?
  │    ├─ Spec is correct, code is wrong
  │    │    → Send back to implementer with reviewer's findings
  │    │    → Max 2 attempts. If still failing → Escalate (see below)
  │    │
  │    └─ Spec is wrong or incomplete
  │         → STOP pipeline. Fix the spec first.
  │         → Restart from pre-check after spec update.
  │
  ├─ Implementer can't make tests pass?
  │    ├─ Tests are correct (match spec)
  │    │    → Loop to implementer once with specific guidance
  │    │    → If still failing → the feature is too large. Decompose it.
  │    │
  │    └─ Tests are wrong (don't match spec, impossible assertions, bad mocks)
  │         → Send back to test-writer with implementer's findings
  │         → Test-writer rewrites, implementer retries
  │
  ├─ safety-auditor finds violations?
  │    → NEVER skip. Fix the violation.
  │    → Send back to implementer with auditor's findings
  │    → Re-run safety-auditor after fix. No shortcuts.
  │    → If 3+ loops: escalate to human. The invariant may need review.
  │
  ├─ Arch-advisor verification returns UNSOUND?
  │    → Send architecture findings to implementer
  │    → Implementer fixes, re-run spec-reviewer + safety-auditor + Arch-advisor
  │    → Max 1 Arch-advisor retry. If still UNSOUND → Escalate to human.
  │    → This is an architecture-level problem, not a code-level one.
  │
  ├─ Roundtable pre-check review raises concerns? (Step 1.3)
  │    → Send consensus findings back to pre-check for revision
  │    → Max 2 roundtable pre-check attempts
  │    → If still CONCERNS after 2 attempts: proceed with pre-check's
  │      latest classification (advisory, not blocking)
  │    → Roundtable is advisory — pre-check remains the authoritative router
  │
  ├─ Roundtable design review raises concerns? (Step 2.5)
  │    → Send findings back to designer for revision
  │    → Max 2 roundtable design attempts
  │    → If still CONCERNS after 2 attempts: proceed anyway (advisory)
  │    → Roundtable is advisory — it does not block the pipeline
  │
  ├─ Roundtable landing review raises concerns? (Step 8.5)
  │    → Send findings back to implementer
  │    → Implementer fixes, re-run the review gates concurrently:
  │      [code-reviewer ∥ spec-reviewer ∥ safety-auditor? ∥ arch-advisor-verify?] → landing-verifier
  │    → Max 1 roundtable-triggered gate re-run per gate
  │    → Re-run roundtable landing review (attempt 2)
  │    → If still CONCERNS after 2 attempts: proceed anyway (advisory)
  │    → If a roundtable-triggered gate re-run itself fails: escalate to human
  │
  ├─ Push or PR-create fails during `/keel-submit`? (NOT the pipeline)
  │    → Step 9 is repo-local: the pipeline commits + archives, never
  │      pushes or opens a PR. Publishing is the separate `/keel-submit`
  │      skill, run by the human.
  │    → `/keel-submit` is fail-fast and idempotent: it STOPs on the raw
  │      error, names the pushed-branch fact and the resume command, and
  │      re-running skips the already-published WIs.
  │    → The feature is already done repo-locally (committed + archived) —
  │      a submit failure loses no work.
  │
  ├─ pre-check routed wrong? (skipped designer when one was needed)
  │    → Insert the missing stage now
  │    → Designer reads the handoff, produces design brief
  │    → Resume pipeline from test-writer
  │
  ├─ landing-verifier reports BLOCKED?
  │    → Read the BLOCKED reason — it tells you which upstream stage failed
  │    → Fix that stage, re-run landing-verifier
  │
  ├─ /keel-refine preflight fails (bootstrap gate not satisfied)?
  │    → Skill prints an A/B/C remediation message; follow it.
  │    → [A] Greenfield, bootstrap not yet run: run each bootstrap feature
  │        in backlog.md in order (/keel-pipeline WI01, then WI02, …);
  │        each ticks its own box on landing (you never tick by hand).
  │        Re-run /keel-refine once every bootstrap box is [x]. If the
  │        Bootstrap section is still the shipped bootstrap template, run
  │        /keel-setup first to adapt it to your stack.
  │    → [B] Brownfield (primary path for an already-adopted repo):
  │        paste `<!-- KEEL-BOOTSTRAP: not-applicable -->` on its own line
  │        between the **Architecture:** preamble and the first `---`
  │        divider in backlog.md. Re-run /keel-refine.
  │    → [C] Brownfield, first-time adoption: run /keel-adopt.
  │        Phase 6e stamps the marker automatically.
  │    → WARNING: if /keel-adopt has already run once, do NOT re-run it
  │      (it will overwrite the project guide and ARCHITECTURE.md). Use [B].
  │    → Full context: docs/process/BROWNFIELD.md §6.
  │
  ├─ Maintenance-lane change can't be explained as maintenance? (a hunk adds product behavior)
  │    → Halt. Route to /keel-refine and run it as a feature.
  │    → "When in doubt, it is a feature." See PIPELINE-DOCTRINE.md §"The maintenance lane".
  │
  └─ Agent produces garbled or off-topic output?
       → Re-run the same agent (model hiccup, not a process failure)
       → If still garbled → the handoff context may be too large
       → Summarize the handoff, keeping only the current agent's inputs
```

## Binder-scope halts

### pre-check blocks on missing Binder link

**Symptom:** `/keel-pipeline WI##` halts with *"WI## references Binder 'X' but `docs/exec-plans/binders/X.json` does not exist."*

**Cause:** Typo in `Binder:` field, or Binder file was renamed/deleted.

**Fix:**
- If the Binder should exist: create the file at the referenced path (narrative only, no feature list).
- If the slug was a typo: correct the WI## entry's `Binder:` field in the backlog.
- If the WI## is legacy work: change `Binder: <slug>` to `Binder-exempt: legacy`.

### pre-check blocks on invalid Binder-exempt reason

**Symptom:** `/keel-pipeline WI##` halts with *"WI## declares Binder-exempt with reason '<x>'; must be one of legacy/bootstrap/infra/trivial."*

**Cause:** Free-form reason used instead of one of the four allowed values.

**Fix:** Edit the WI## entry to use one of the four allowed reasons. If none fit, the feature likely should have a Binder — author one.

### validate-binders.py reports orphaned Binder file

**Symptom:** CI validator reports *"Binder file `docs/exec-plans/binders/<slug>.json` is not referenced by any WI##."*

**Cause:** A Binder was drafted but all its WI## were dropped or never added.

**Fix:** Either delete the orphaned Binder file (git log preserves history) or add WI## entries that reference it.

### validate-binders.py reports WI## ID mentioned in Binder prose

**Symptom:** Validator reports *"Binder prose `<slug>.md` contains WI## reference — narrative must use theme-level language, not IDs."*

**Cause:** Someone pasted a WI## list into the Binder narrative (common drift toward Jira-docification).

**Fix:** Rewrite the prose to describe themes/scope, not IDs. The feature list lives on `docs/exec-plans/active/backlog.md` (WI## entries tagged `Binder: <slug>`) — don't cache it in the Binder file. For a JSON Binder, `uv run scripts/keel-binder-view.py docs/exec-plans/binders/<slug>.json` renders the canonical view.

## Halt: WI## has unmerged Needs (halt-mode default)

**Symptom:** `/keel-pipeline WI02` halts at Step 0 with "WI02 requires
WI01 (intra-Binder). WI01 status: ... not an ancestor of <base>."

**Cause:** WI02 declares WI01 in its `Needs:` and WI01 has not yet been
merged to base. The default `Branching policy: halt` refuses to start
on unmerged Needs.

**Resolution:** One of:
1. Merge or integrate WI01 to trunk (locally, or via its PR if you use a forge), then re-run `/keel-pipeline WI02`.
2. Set `Branching policy: stack` in the project guide (intra-Binder only —
   cross-Binder always halts) and re-run. WI02 will branch from WI01's
   tip; on WI01's eventual merge, the next /keel-pipeline WI02
   invocation restacks onto base.

## Halt: stacked-branch restack hit conflicts

**Symptom:** `/keel-pipeline WI02` halts at re-invocation with
"Restack of keel/WI02-<slug> onto <base> halted with conflicts."

**Cause:** WI02's commits touch files that WI01 modified after WI02
branched. `git rebase --update-refs --onto` cannot resolve the
overlap automatically.

**Resolution:** Human resolves the conflicts:
1. `git status` to see conflicted paths.
2. Edit each conflicted file, `git add <path>`.
3. `git rebase --continue` to complete the restack, then re-run
   `/keel-pipeline WI02`.
4. Or `git rebase --abort` to undo; the pipeline halts and the
   handoff stays in `active/`.

## Rules

1. **Never "try harder."** If the implementer fails twice on the same tests,
   the problem is upstream — wrong spec, wrong tests, or feature too large.

2. **Max 2 implementation loops.** Implementer gets the initial attempt plus
   one retry with specific guidance. After that, decompose the feature or
   fix upstream.

3. **Spec changes restart the pipeline.** If you modify the spec mid-pipeline,
   go back to pre-check. Don't patch downstream — the whole chain depends on
   spec accuracy.

4. **Safety violations are never negotiable.** The safety-auditor is a hard
   gate. You fix the code, not the rule. If the rule itself is wrong, that's
   a core-beliefs discussion — update the invariant deliberately, not as a
   pipeline workaround.

5. **Test-writer can be sent backwards.** If the implementer identifies that
   tests are wrong (impossible contract, incorrect mock setup), the handoff
   file gets a `BLOCKED: test-issue` entry and routes back to test-writer.
   This is the one sanctioned backward path in the pipeline.

6. **Decompose before you thrash.** If a feature touches 3+ layers and
   the implementer can't satisfy tests after 2 attempts, the feature may
   be too large. Split it into smaller independently testable units.

## Escalation

When to involve the human orchestrator directly:

- Spec is ambiguous and two valid interpretations exist
- Feature requires a design decision not in any existing doc
- Agent consistently produces off-topic output (model capability gap)
- Domain invariant needs updating (core-beliefs change)
- Feature is blocked by external dependency (API not ready, library missing)

The orchestrator's job at escalation is to **make a decision and encode it
in the repo** — update a spec, add a design doc, modify core-beliefs — then
restart the pipeline from the appropriate stage.
