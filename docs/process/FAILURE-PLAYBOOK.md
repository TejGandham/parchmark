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
  ├─ Roundtable design review raises concerns? (Step 2.5)
  │    → Send findings back to designer for revision
  │    → Max 2 roundtable design attempts
  │    → If still CONCERNS after 2 attempts: proceed anyway (advisory)
  │    → Roundtable is advisory — it does not block the pipeline
  │
  ├─ Roundtable landing review raises concerns? (Step 8.5)
  │    → Send findings back to implementer
  │    → Implementer fixes, re-run full gate chain:
  │      code-reviewer → spec-reviewer → safety-auditor? → arch-advisor? → landing-verifier
  │    → Max 1 roundtable-triggered gate re-run per gate
  │    → Re-run roundtable landing review (attempt 2)
  │    → If still CONCERNS after 2 attempts: proceed anyway (advisory)
  │    → If a roundtable-triggered gate re-run itself fails: escalate to human
  │
  ├─ Push rejected at Step 9?
  │    → STOP, print the raw git error
  │    → Human resolves (e.g., auth, branch protection) and reruns push
  │    → Commit is already local — no work lost
  │
  ├─ gh pr create fails at Step 9?
  │    → Print manual PR instructions — branch is pushed
  │    → Human opens the PR on the forge UI
  │    → Do not fail the pipeline
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
  └─ Agent produces garbled or off-topic output?
       → Re-run the same agent (model hiccup, not a process failure)
       → If still garbled → the handoff context may be too large
       → Summarize the handoff, keeping only the current agent's inputs
```

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
