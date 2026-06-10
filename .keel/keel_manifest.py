# scripts/keel_manifest.py
"""Declared install surface for the current KEEL version.

Consumed by scripts/install.py (what to copy) and
scripts/validate-manifest.py (CI cross-check).

Stdlib-only: this file is pure data. Adding a new agent/skill/hook
requires editing this file — which is the whole point.
"""
from __future__ import annotations

KEEL_VERSION = "2026.06.46"
RECEIPT_SCHEMA_VERSION = 3
# KEEL machinery is host-neutral and lives under `.keel/` in user installs;
# only host-mandated surfaces (settings.json, agents/, skills/) stay in `.claude/`.
RECEIPT_PATH = ".keel/install.json"
BUNDLED_UNINSTALLER = ".keel/uninstall.py"
# A fail-closed compatibility stub kept at the legacy path so a user who runs
# the old command still gets redirected to the real uninstaller (see uninstall.py).
BUNDLED_UNINSTALLER_COMPAT = ".claude/keel-uninstall.py"
SETTINGS_FILE = ".claude/settings.json"

# Single source of truth for the Python floor. Bootstrap scripts duplicate
# the literal `(3, 14)` (they can't safely import this module before their
# own version check runs on ancient Python). PEP 723 headers duplicate
# `">=3.14"`. Both duplicates are lint-checked against this constant by
# scripts/validate-manifest.py — drift fails CI.
PYTHON_FLOOR: tuple[int, int] = (3, 14)
PYTHON_FLOOR_PEP723: str = f">={PYTHON_FLOOR[0]}.{PYTHON_FLOOR[1]}"

# Binder schema version. Bumps when the Binder schema shape breaks. Every Binder
# must declare `schema_version` matching a version the validator supports.
# See docs/design-docs/2026-04-24-structured-prds.md.
BINDER_SCHEMA_VERSION: int = 1

# Prototype manifest schema version. Bumps when the prototype.json shape
# breaks. Carried separately from BINDER_SCHEMA_VERSION because the two
# contracts evolve independently — a prototype-shape change shouldn't
# force Binder revalidation, and vice versa.
PROTOTYPE_SCHEMA_VERSION: int = 1

AGENTS: list[str] = [
    "arch-advisor-consult.md", "arch-advisor-verify.md", "backend-designer.md",
    "backlog-drafter.md", "code-reviewer.md", "config-writer.md",
    "doc-gardener.md", "frontend-designer.md",
    "implementer.md", "karta-spec-reviewer.md", "landing-verifier.md",
    "pre-check.md", "researcher.md", "review-panelist.md",
    "safety-auditor.md", "scaffolder.md", "spec-reviewer.md",
    "test-writer.md",
]  # 18

SKILLS: list[str] = [
    "keel-pipeline", "keel-adopt", "keel-setup", "keel-refine", "keel-safety-check",
    "keel-submit",
    "karta-refine", "karta-pipeline", "karta-drive",
]

# Skills that AUTHOR the KEEL-ROLE dispatch preamble directly (they construct
# agent-master spawn messages, so on Codex they must carry the tag the
# role-injector recovers). The Karta delta skills inherit it by citation
# (karta-refine ← keel-refine §Phase 3; karta-pipeline ← keel-pipeline §per-hop
# protocol); karta-drive dispatches the karta-pipeline skill, not an agent
# master. Gated by scripts/validate-dispatch-tags.py (the preamble fails
# silently on Codex if a dispatching skill forgets it). See
# docs/process/HOST-SURFACES.md §"Subagent dispatch".
DISPATCHING_SKILLS: list[str] = ["keel-pipeline", "keel-safety-check", "keel-refine"]

HOOKS: list[str] = ["keel-safety-gate.py", "keel-doc-gate.py", "keel-timing-hook.py"]

# Hooks shipped ONLY on `--host codex` installs. keel-role-injector.py performs
# the structural role/contract injection that Codex needs and Claude does not
# (Claude loads masters as resident system prompts). Source lives alongside the
# shared hooks in .claude/hooks/; the installer ships it to .keel/hooks/ only on
# codex installs. The timing hook is NOT shipped on codex (Codex skips async
# handlers — blocker B1).
CODEX_ONLY_HOOKS: list[str] = ["keel-role-injector.py"]

PROCESS_DOCS: list[str] = [
    "THE-KEEL-PROCESS.md", "QUICK-START.md", "BROWNFIELD.md", "GLOSSARY.md",
    "ANTI-PATTERNS.md", "FAILURE-PLAYBOOK.md", "AUTONOMY-PROGRESSION.md",
    "KEEL-PRINCIPLES.md", "PIPELINE-DOCTRINE.md", "REVIEW-PANEL.md",
    "HANDOFF-CONTRACT.md", "KARTA-LANE.md", "HOST-SURFACES.md",
]

# User-facing framework scripts shipped into installs under scripts/.
# Iterated by install.py's _copy_scripts. Invoked from the user's repo
# root (e.g. `python3 scripts/validate-binders.py --repo .`). Install-time
# entrypoints (install.py, uninstall.py) and stdlib helper modules
# (keel_manifest.py, keel_receipt.py, keel_settings.py) are tracked
# separately via their own call sites and are NOT in this list.
#
# Framework-only scripts (validate-bootstrap-gate.py, validate-manifest.py)
# run against this repo and are intentionally NOT shipped — they would be
# noise in a user install. validate-handoff.py ships: the pipeline skills
# cite it for installed-repo handoff validation, so it must travel with them.
SCRIPTS: list[str] = [
    "validate-binders.py",
    "validate-binder-json.py",
    "validate-prototype-json.py",
    "keel-binder-view.py",
    "keel-work-item-resolve.py",
    "keel_work_items.py",
    "upgrade-invariant-7.py",
    "keel-timing.py",
    "keel-routing.py",
    "keel-query.py",
    "keel-backlog-migrate.py",
    "karta-deferred-ledger.py",
    "keel-drive-order.py",
    "validate-handoff.py",
]

# Schema files under schemas/ shipped into user installs. Loaded by
# validate-binder-json.py at runtime. Binder schema validates framework frame
# (Binder shape, feature shape, oracle shape, cross-refs); feature `contract`
# is intentionally open-shape per docs/design-docs/2026-04-24-structured-prds.md.
SCHEMAS: list[str] = [
    "binder.schema.json",
    "prototype.schema.json",
    "routing.schema.json",
    "resolved-work-item.schema.json",
    "keel.schema.json",
]

# KEEL-internal scripts under scripts/ that are NOT shipped to installs.
# Install-time entrypoints (install.py, uninstall.py), framework-only
# validators (validate-bootstrap-gate.py, validate-manifest.py), and
# stdlib helper modules (keel_manifest.py, keel_receipt.py,
# keel_settings.py). Consumed by scripts/validate-manifest.py's
# disk↔SCRIPTS cross-check so adding a new internal utility requires
# editing this list — the validator will flag any un-declared .py under
# scripts/ that isn't in SCRIPTS either.
INTERNAL_SCRIPTS: set[str] = {
    "install.py",
    "uninstall.py",
    "derive_codex_surface.py",
    "validate-bootstrap-gate.py",
    "validate-manifest.py",
    "validate-onboarding-parity.py",
    "validate-dispatch-tags.py",
    "validate-taxonomy.py",
    "validate-doc-consistency.py",
    "migrate-binder-to-json.py",
    "keel_manifest.py",
    "keel_receipt.py",
    "keel_settings.py",
}

# AGENTS.md is the project operating-guide content root (host-neutral, read
# verbatim by any host). CLAUDE.md is Claude Code's native auto-load file and
# ships as a thin `@AGENTS.md` pointer so the single content source never
# duplicates (P4). The project-guide locator resolves to AGENTS.md on every
# host; see docs/process/HOST-SURFACES.md.
TEMPLATE_ROOT_FILES: list[str] = [
    "NORTH-STAR.md", "AGENTS.md", "CLAUDE.md", "ARCHITECTURE.md",
]

# Optional root files — installed only when the user opts in at install
# time. Currently empty: KEEL ships no opinionated runtime scaffolding.
# Containerization, like any other runtime concern, is a product feature
# authored via /keel-refine -> /keel-pipeline, not install-time scaffolding.
OPTIONAL_TEMPLATE_ROOT_FILES: dict[str, list[str]] = {}

TEMPLATE_DOCS: list[str] = [
    # KEEL-owned operating contract — heavy enforcement language for any
    # agent working in the installed repo. CLAUDE.md @-imports it. Lives
    # under host-neutral .keel/ (was .claude/) — KEEL machinery, not a host
    # surface — and avoids collision with the user's own CLAUDE.md/AGENTS.md.
    ".keel/KEEL-CONTRACT.md",
    "docs/design-docs/core-beliefs.md",
    "docs/design-docs/ui-design.md",
    "docs/design-docs/index.md",
    "docs/exec-plans/active/backlog.md",
    "docs/exec-plans/binders/.gitkeep",
    "docs/exec-plans/tech-debt-tracker.md",
    "docs/references/README.md",
]

HOOK_COMMAND_SIGNATURES: list[str] = [
    # KEEL-owned entries in settings.json.
    ".keel/hooks/keel-safety-gate.py",
    ".keel/hooks/keel-doc-gate.py",
    ".keel/hooks/keel-timing-hook.py",
]

# Hook specs that install.py inserts into .claude/settings.json.
# Each entry's `signature` must also appear in HOOK_COMMAND_SIGNATURES
# above; CI enforces this (see scripts/validate-manifest.py). Value type is
# `object` because the timing entries carry a boolean `async` alongside the
# string fields; keel_settings.merge_hooks preserves the `async` key into
# settings.json.
#
# ONE SETTINGS.JSON SHAPE for every event (the Claude Code event-config
# contract requires it). merge_hooks writes the nested matcher-wrapper shape
# for EVERY entry:
#     settings.hooks[event] = [{matcher, hooks:[{type,command,async}]}].
# `matcher: ""` means match-all — it captures BOTH tool events (Read/Bash via
# PreToolUse/PostToolUse) AND lifecycle events (Stop/UserPromptSubmit/
# PostToolBatch). The live Claude Code validator REJECTS a flat command-hook
# object placed directly in the event array ("hooks: Expected array, but
# received undefined"), so there is no matcher-less shape — every event,
# including the lifecycle events, carries an explicit `matcher` (empty string
# for the catch-all timing entries).
KEEL_HOOKS_SPEC: list[dict[str, object]] = [
    {
        "event": "PreToolUse",
        "matcher": "Edit|Write",
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-safety-gate.py"',
        "signature": ".keel/hooks/keel-safety-gate.py",
    },
    {
        "event": "PostToolUse",
        "matcher": "Bash",
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-doc-gate.py"',
        "signature": ".keel/hooks/keel-doc-gate.py",
    },
    # Full-lifecycle pipeline timing (opt-in via the KEEL_TIMING env var; the
    # hook is inert otherwise). Registered as a CATCH-ALL across the entire
    # Claude Code lifecycle so the reporter can decompose the gaps between
    # agents — where ~74% of wall-clock lives. EVERY entry uses `matcher: ""`
    # (empty = match all): this captures both tool events — every tool call:
    # subagent dispatches (Agent/Task), MCP-backed work (roundtable etc.),
    # ordinary tools (Bash, Edit, …) — and lifecycle events: orchestrator
    # turns (Stop / UserPromptSubmit), context compaction (Pre/PostCompact),
    # permission and notification waits (PermissionRequest/Denied,
    # Notification), session boundaries (SessionStart/End), plus StopFailure /
    # PostToolBatch. For lifecycle events the hook records the event name +
    # session + timestamp; tool/agent columns are NULL.
    #
    # ALL entries carry `"async": true`, so the harness runs the hook in the
    # background and never blocks on it — zero added latency. The reporter
    # pairs tool stages by tool_use_id and counts lifecycle events separately.
    # One registration per event: a second matcher matching the same event
    # would double-log it.
    #
    # The standard `{matcher, hooks:[…]}` shape is required for EVERY event,
    # including the lifecycle events — the live Claude Code validator rejects a
    # flat command-hook object placed directly in the event array. `matcher: ""`
    # is the catch-all matcher for all 14 timing events.
    {
        "event": "PreToolUse",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
    {
        "event": "PostToolUse",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
    {
        "event": "PostToolUseFailure",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
    {
        "event": "PermissionRequest",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
    {
        "event": "PermissionDenied",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
    {
        "event": "PreCompact",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
    {
        "event": "PostCompact",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
    {
        "event": "SessionStart",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
    {
        "event": "Notification",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
    # Lifecycle events that carry no tool — same standard shape, `matcher: ""`.
    {
        "event": "UserPromptSubmit",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
    {
        "event": "Stop",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
    {
        "event": "StopFailure",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
    {
        "event": "PostToolBatch",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
    {
        "event": "SessionEnd",
        "matcher": "",
        "async": True,
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.keel/hooks/keel-timing-hook.py"',
        "signature": ".keel/hooks/keel-timing-hook.py",
    },
]

# --- Codex host surface (derived; host=codex) -------------------------------
# Codex support generates a small host surface instead of committing any
# Codex-shaped files to this repo. derive_codex_surface.py emits it; the
# installer writes it on `--host codex`; validate-manifest.py executes the
# rules below and asserts completeness. No `.codex/agents/*.toml` is generated
# — Codex binds no named agent (Phase 0.5 spike); identity rides the
# `[KEEL-ROLE]` tag + the role-injector hook. See docs/process/HOST-SURFACES.md.

# Which KEEL hooks register on Codex and with what event/matcher. A SUBSET of
# the Claude wiring: the safety + doc gates (shared, dual-payload scripts) plus
# the codex-only role injector. The timing hook is intentionally absent — Codex
# skips async handlers (blocker B1), so it has nothing to register. The hook
# SCRIPTS are the same `.keel/hooks/*.py` that serve Claude; only the
# registration format differs per host (settings.json vs .codex/hooks.json) —
# that is inherent, not redundant storage (P4). The Edit|Write and Bash matchers
# are Codex apply_patch / shell aliases pending Phase 5 live re-verification.
CODEX_HOOK_SPEC: list[dict[str, str]] = [
    {"event": "PreToolUse", "matcher": "Edit|Write", "script": "keel-safety-gate.py"},
    {"event": "PostToolUse", "matcher": "Bash", "script": "keel-doc-gate.py"},
    {"event": "SubagentStart", "matcher": ".*", "script": "keel-role-injector.py"},
    {"event": "SessionStart", "matcher": "startup", "script": "keel-role-injector.py"},
]

# Codex subagent concurrency, written to project-scoped `.codex/config.toml`.
# The unset agents.max_threads default rejected the 4th concurrent spawn in the
# Phase 0.5 spike; KEEL's 4-lens review panel + pipeline fan-out need headroom.
# max_depth pinned to 1 (KEEL never nests subagents; Codex default is also 1,
# pinned so a host default change cannot silently break the bound). Phase 5
# quantifies the thread-budget lifecycle.
CODEX_AGENT_LIMITS: dict[str, int] = {"max_threads": 8, "max_depth": 1}

# Declarative derivation rules: transform name → canonical source → target
# PATTERN. Targets are patterns over the canonical lists, never stored derived
# filenames (P4 — a stored derived name is a cache that stales). The validator
# runs derive_codex_surface and asserts its outputs match the targets these
# rules imply (completeness): add a skill and its policy file is covered with
# no manifest edit here.
CODEX_DERIVATIONS: list[dict[str, str]] = [
    {"transform": "skill_policy", "source": "SKILLS",
     "target": ".agents/skills/{skill}/agents/openai.yaml"},
    {"transform": "codex_hooks", "source": "CODEX_HOOK_SPEC",
     "target": ".codex/hooks.json"},
    {"transform": "codex_config", "source": "CODEX_AGENT_LIMITS",
     "target": ".codex/config.toml"},
]

# Skills/hooks that CI's prefix lint must ignore (third-party assets
# users install alongside KEEL that live in the same directories).
THIRD_PARTY_ALLOWLIST: set[str] = {
    "roundtable",   # MCP roundtable skill (example — confirm at lint time)
}

# Skills/agents present in the repo but intentionally NOT installed
# (framework-internal). CI cross-checks exclude these.
FRAMEWORK_INTERNAL: set[str] = {
    ".claude/skills/dev-up",
}


def install_dirs() -> set[str]:
    """POSIX-relative directories a full KEEL install creates, derived from
    the manifest path lists so the set never drifts from what install
    actually writes. The uninstaller prunes these bottom-up when empty (see
    scripts/uninstall.py) — deriving from the manifest, not a hardcoded
    list, is why an added agent/doc can't leave an empty shell behind, and
    why the set is stable even when a prior partial uninstall trimmed the
    receipt's managed_paths."""
    files = (
        [f".claude/agents/{n}" for n in AGENTS]
        + [f".claude/skills/{n}" for n in SKILLS]
        + [f".keel/hooks/{n}" for n in HOOKS]
        + [f"scripts/{n}" for n in SCRIPTS]
        + [f"schemas/{n}" for n in SCHEMAS]
        + [f"docs/process/{n}" for n in PROCESS_DOCS]
        + list(TEMPLATE_DOCS)
        + [RECEIPT_PATH, SETTINGS_FILE, BUNDLED_UNINSTALLER, BUNDLED_UNINSTALLER_COMPAT]
    )
    dirs: set[str] = set()
    for rel in files:
        parts = rel.split("/")
        for i in range(1, len(parts)):
            dirs.add("/".join(parts[:i]))
    return dirs
