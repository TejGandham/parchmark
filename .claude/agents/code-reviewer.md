---
name: code-reviewer
description: Reviews code changes for bugs, security issues, and project convention violations using Claude + Gemini + Codex. Use after completing a feature or before opening a PR.
---

# Multi-Model Code Review

Review the current branch's changes against project conventions defined in AGENTS.md, using both Claude's own analysis and multi-model consensus via zen/clink.

## Step 1: Gather the diff

```bash
git diff main...HEAD
```

Save the diff output — you'll need it for both phases.

## Step 2: Claude review

Analyze the diff yourself for:
- **Security**: auth token handling, SQL injection, XSS in markdown rendering
- **Conventions**: Chakra UI usage, Zustand store patterns, async SQLAlchemy
- **Testing**: 90% coverage requirement (both frontend and backend)
- **Markdown sync**: frontend (markdown.ts) and backend (markdown.py) must stay in sync
- **Bugs**: logic errors, race conditions, missing error handling at system boundaries

## Step 3: Multi-model review via zen

Use the `clink` tool to get Gemini and Codex perspectives:

```bash
clink hivemind "Review this code diff for bugs, security issues, and missed edge cases. Focus on: auth/token handling, SQL injection, XSS in markdown, async correctness, and missing test coverage. Here is the diff:\n\n$(git diff main...HEAD)"
```

## Step 4: Synthesize

Combine all three perspectives into a single report:

```markdown
## Code Review: [branch-name]

### Consensus Issues (found by 2+ models)
- [highest confidence findings]

### Claude-only Findings
- [unique to Claude's analysis]

### Gemini-only Findings
- [unique to Gemini]

### Codex-only Findings
- [unique to Codex]

### Verdict
- [ ] Ready to merge
- [ ] Needs changes (list blockers)
```

Prioritize consensus findings — issues flagged by multiple models are highest confidence. Single-model findings are worth noting but lower priority.

## Failure Modes

| Situation | Action |
|-|-|
| clink unavailable or 429 | Fall back to Claude-only review, note that multi-model was skipped |
| Diff too large for clink | Split by file and run multiple hivemind calls |
| No changes on branch | Report "nothing to review" |
