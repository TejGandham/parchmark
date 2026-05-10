# Team Scaling

KEEL is designed for a single orchestrator — one human (or automated
pipeline) driving features through the pipeline sequentially. This
document defines where that model works, where it breaks, and what
to do when you outgrow it.

## Where Single-Orchestrator Works

```
 1 person + 1 agent          1-3 people + agents
 ┌──────────────────┐       ┌──────────────────────────┐
 │ Sequential features│       │ Sequential features      │
 │ One handoff file   │       │ Non-overlapping modules   │
 │ One backlog        │       │ Shared backlog, take turns│
 │ No conflicts       │       │ Rare conflicts            │
 └──────────────────┘       └──────────────────────────┘
```

This covers most KEEL projects. Features run one at a time through
the pipeline. The backlog is the serialization point — whoever picks
the next feature owns it until it lands.

## Where It Breaks

```
 2+ people, parallel features, overlapping modules
 ┌──────────────────────────────────────────────┐
 │ Person A: F12 touches auth.ts + api.ts       │
 │ Person B: F13 touches api.ts + db.ts         │
 │                                              │
 │ Both have handoff files. Both modify api.ts. │
 │ Whose spec-reviewer verdict wins?            │
 │ Whose safety-auditor findings apply?         │
 └──────────────────────────────────────────────┘
```

KEEL has no answer for this today. The handoff file is per-feature
(agent output sections snapshot, deliberation sections append-only) —
there's no merge strategy for concurrent handoffs touching the same
modules.

## Signs You're Approaching the Limit

- Features blocked waiting for another feature to land
- Multiple people editing the backlog simultaneously
- Handoff files referencing code that changed since pre-check ran
- Spec-reviewer finding deviations caused by a parallel feature, not
  the current one

## What To Do

### Short term: serialize

The simplest fix is also the most effective: don't run parallel
pipelines on overlapping modules. Use the backlog as a lock:

```
 Feature backlog:
 - [x] F11 Auth middleware        ← landed
 - [ ] F12 Auth token refresh     ← Person A (in pipeline)
 - [ ] F13 API rate limiting      ← Person B (waiting — touches api.ts)
 - [ ] F14 Dashboard UI           ← Person B (can start — no overlap)
```

If F12 and F14 don't share modules, they can run in parallel safely.
If F12 and F13 overlap, F13 waits.

### Medium term: branch isolation

Each feature runs in its own git branch. The pipeline operates on
that branch. Merge conflicts are resolved at PR time, not during
the pipeline.

```
 main ──────────────────────────────────────────▶
   ├── feature/F12-auth-refresh ──▶ PR
   └── feature/F14-dashboard-ui ──▶ PR
```

This works if features are well-decomposed (minimal overlap). It
breaks if two features modify the same functions.

### Long term: not KEEL's problem (yet)

True parallel orchestration — multiple pipelines running concurrently
with conflict resolution, shared state, and distributed handoffs —
is a different system. KEEL may evolve there, but it's not the
current goal.

If you need this today:
- Use git branches + PR-based review as the serialization point
- Keep features small and layer-isolated (the existing decomposition
  principles handle this)
- Accept that the human resolves merge conflicts — KEEL handles
  spec conformance within a feature, not across features
