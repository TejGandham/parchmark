# KEEL for Existing Projects

How to adopt KEEL when you already have a codebase.

---

## The Key Difference

Greenfield KEEL starts from an empty directory — `/keel-setup` drafts docs,
then you build. Brownfield KEEL does the opposite: you already have code,
and `/keel-adopt` backfills enough context that agents can safely build
what comes *next*.

You are NOT documenting everything that exists. The existing code IS the
documentation of what exists. You're teaching the agent where things are,
what the rules are, and what not to break.

## What You Need (and What You Don't)

| You need | You don't need |
|-|-|
| CLAUDE.md as entry point | To document every past feature |
| ARCHITECTURE.md showing current structure | A product spec for existing functionality |
| Core beliefs and domain invariants | Handoff files for past work |
| A feature backlog of *upcoming* work | To retrofit the testing layers onto existing tests |
| Safety-auditor configured for your domain | To rewrite existing code to match KEEL patterns |

The goal is minimum viable context: enough for an agent to build the next
feature safely without breaking what exists.

---

## Step-by-Step Adoption

### 1. Have the agent read your codebase

Before writing any docs, let the agent explore. Point it at your codebase
and ask it to describe what it finds:

```
Read the entire codebase. Describe:
- What this project does
- The architecture (layers, modules, dependencies)
- Key patterns and conventions
- Where the tests are and what framework they use
- What the build/run/test commands are
```

This gives you a draft for CLAUDE.md and ARCHITECTURE.md written from the
code's perspective, not from memory.

### 2. Write CLAUDE.md

Use the agent's output as a starting point. Keep it under 100 lines:

```markdown
# Project Name

[One paragraph: what this does]

## Quick Facts
- Stack: [from agent's analysis]
- Runtime: [Docker / local / cloud]
- Tests: [framework, how to run]

## Safety Rules
[Your domain's non-negotiable invariants — see step 4]

## Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md)

## Development
[Build, run, test commands — 4-6 lines]
```

The agent already read the code, so CLAUDE.md confirms and organizes what
it learned rather than introducing new information.

### 3. Write ARCHITECTURE.md

Again, start from the agent's analysis. What matters:

- **Module map** — what calls what. The agent can generate this from imports.
- **Layer diagram** — which direction do dependencies flow?
- **Key design decisions** — why things are the way they are (this is the
  part only you know — encode it now or the agent will guess wrong later).

You don't need to fill every section of the template. An ARCHITECTURE.md
with a module map and a 3-line layer diagram is infinitely better than none.

### 4. Define your domain invariants

This is the most important step. Every codebase has rules that must not be
broken. They're usually enforced by convention and tribal knowledge. Encode
them now:

Ask yourself: **"What would cause a production incident if an agent got it wrong?"**

Examples by domain:
- **Financial:** Never use floating-point for money. Every transaction is double-entry.
- **API:** Never expose raw SQL. Auth on every endpoint. No secrets in responses.
- **Data pipeline:** Transforms must be idempotent. Never silently drop records.
- **Git operations:** Never force-push. Always --ff-only. Never modify working tree.

Write these in `docs/design-docs/core-beliefs.md`. Configure the
safety-auditor agent with grep patterns that detect violations.
See `examples/domain-invariants/` for templates.

### 5. Configure the safety-auditor

Edit `.claude/agents/safety-auditor.md`:
- Add your invariant rules
- Add grep patterns that detect violations
- Add your critical file paths

Edit `.claude/hooks/safety-gate.py`:
- Set the file patterns that trigger safety reminders before edits

This is your mechanical enforcement layer. It catches violations that
code review misses.

### 6. Write a feature backlog of upcoming work

Open `docs/exec-plans/active/feature-backlog.md`. List the next features
you want to build — not past features. Format:

```markdown
## Next Features

- [ ] **F01 [Feature name]**
  Spec: [where the requirements are, even if informal]
  Test: [how you'll know it's done]

- [ ] **F02 [Feature name]**
  Needs: F01
  Test: [acceptance criteria]
```

For brownfield, you skip the bootstrap features (F01-F03 in greenfield).
Your project already has Docker, a framework, and test infrastructure.
Start directly with real features.

### 7. Write a spec for your first feature

Pick the next feature you want to build. Write a spec for it — even a
rough one. The spec doesn't need to be as detailed as a greenfield MVP spec.
It needs to answer:

- What does this feature do?
- What inputs does it take?
- What outputs does it produce?
- What are the edge cases?
- What invariants must it respect?

Put it in `docs/product-specs/` or wherever makes sense for your project.

**Have a PRD already?** Brownfield projects often do — an existing
product document, an internal wiki page, wireframes, hi-fi comps, or a
paragraph from a teammate. Run `/keel-refine` with the PRD path, a
bundle directory (README + sibling images/PDFs), a prose description,
or nothing — then paste screenshots directly in chat. `backlog-drafter`
will draft candidate `F##` backlog entries with dependency edges,
optional `Design:` refs on UI entries, and `<!-- HUMAN: ... -->`
markers where it couldn't resolve a field. The skill presents the
drafts as editable cards in chat; edit in plain English, type
`commit` to write and auto-commit, `abort` to discard. Then write
the spec file(s) the drafted entries point at. See
[QUICK-START.md](QUICK-START.md#optional-draft-the-backlog-from-a-prd--keel-refine)
or [THE-KEEL-PROCESS §6](THE-KEEL-PROCESS.md#6-the-feature-backlog)
for the full flow.

### 8. Run your first feature through the pipeline

```
/keel-pipeline F01 docs/product-specs/your-feature-spec.md
```

The pipeline will:
1. **pre-check** — verify the spec is consistent, identify what's needed
2. **test-writer** — write tests from the spec (your existing test patterns)
3. **implementer** — make the tests pass (following your existing code patterns)
4. **spec-reviewer** — verify the implementation matches the spec
5. **landing-verifier** — verify everything lands clean

The agent already has context from CLAUDE.md and ARCHITECTURE.md. It will
follow your existing patterns because it read your codebase in step 1.

---

## What About Existing Tests?

Don't touch them. KEEL's testing layers (Layer 0-5) are a guide for new
code, not a mandate to restructure existing tests. Your existing tests
continue to run as-is. New features written through the pipeline will
follow the layer model naturally.

Over time, if you want to backfill safety invariant tests (Layer 1) for
existing critical paths, that's a valuable investment — but it's not a
prerequisite for adopting KEEL.

## What About Existing Architecture That Doesn't Match KEEL Patterns?

KEEL doesn't prescribe architecture. It prescribes a process for building
features. Your existing architecture stays. ARCHITECTURE.md describes what
IS, not what KEEL thinks should be.

If you want to refactor toward cleaner layers, treat each refactoring as
a feature in the backlog and run it through the pipeline.

## What About a Team Already Using the Codebase?

KEEL docs live in the repo alongside your existing docs. They don't
conflict with READMEs, wikis, or existing CONTRIBUTING.md files. The
`.claude/` directory contains agent-specific configuration that doesn't
affect other tools.

Team members who don't use KEEL can ignore the docs directory. Team
members who do use KEEL benefit from the accumulated context.

---

## Brownfield Checklist

```
[ ] Agent has read the full codebase
[ ] CLAUDE.md written (under 100 lines)
[ ] ARCHITECTURE.md written (module map + layers at minimum)
[ ] Domain invariants defined in core-beliefs.md
[ ] Safety-auditor configured with grep patterns
[ ] Safety-gate hook configured with critical file patterns
[ ] Feature backlog created with upcoming features
[ ] First feature spec written
[ ] First feature run through pipeline
```

Time to first pipeline run: **2-4 hours** (mostly writing core-beliefs and
the first spec). After that, each feature follows the same pipeline as
greenfield.
