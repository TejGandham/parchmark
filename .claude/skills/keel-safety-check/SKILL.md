---
name: keel-safety-check
description: "Quick safety audit — scans current changes against domain invariant rules. Use after editing critical modules."
---

# Safety Check

Run an immediate safety audit on the current working tree changes. Dispatches the `safety-auditor` agent against the unstaged/staged diff.

## When to Use

- After editing files that touch domain-critical operations — the
  critical paths/patterns defined in the safety-auditor agent master
  §What to Scan
- Before committing changes that touch invariant-protected code
- When the PreToolUse hook reminds you to

## What It Does

This is an **ad-hoc check** for use outside the pipeline (e.g., during manual editing).
Inside the pipeline, `safety-auditor` is dispatched by `keel-pipeline` with handoff context.

1. Runs `git diff` to identify changed files
2. Filters for files that touch domain-critical operations
3. Scans those files against the domain invariant rules below
4. Reports PASS or VIOLATIONS

## Domain Invariant Rules

This quick-check audits the changes against the project's invariant rules
registered in the project guide §Safety Rules — the canonical registry.
The safety-auditor agent master carries the matching scan expressions
for each rule.

## Execution

Dispatch the `safety-auditor` agent (read-only; reports findings). Its spawn
message MUST open with the KEEL-ROLE preamble (canonical text:
`docs/process/HOST-SURFACES.md` §"Subagent dispatch"), substituting
`safety-auditor` for `<role>`:

> `[KEEL-ROLE safety-auditor]` Operate as the `safety-auditor` role. Acquire
> your role contract by the FIRST route that applies, then do the audit:
> (1) RESIDENT — your system prompt already identifies you as the
> `safety-auditor` agent and contains its contract: proceed, do not re-read;
> (2) INJECTED — your context contains a line starting with
> `[KEEL-ROLE-INJECTED safety-auditor complete=true`: that injected text IS
> your contract, do not re-read; (3) POINTER — neither applies: execute a
> BLOCKING READ of `.keel/agents/safety-auditor.md` in full and follow it; if
> it cannot be read in full, STOP and report. Never improvise the role.
> THEN: audit the working-tree diff against the domain invariant rules and
> report PASS or VIOLATIONS.

If violations are found, fix them before committing.
