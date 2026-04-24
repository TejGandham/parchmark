# scripts/keel_manifest.py
"""Declared install surface for the current KEEL version.

Consumed by scripts/install.py (what to copy) and
scripts/validate-manifest.py (CI cross-check).

Stdlib-only: this file is pure data. Adding a new agent/skill/hook
requires editing this file — which is the whole point.
"""
from __future__ import annotations

KEEL_VERSION = "0.10.0"
RECEIPT_SCHEMA_VERSION = 1
RECEIPT_PATH = ".claude/.keel-install.json"
BUNDLED_UNINSTALLER = ".claude/keel-uninstall.py"
SETTINGS_FILE = ".claude/settings.json"

AGENTS: list[str] = [
    "arch-advisor.md", "backend-designer.md", "backlog-drafter.md",
    "code-reviewer.md", "config-writer.md", "doc-gardener.md",
    "docker-builder.md", "frontend-designer.md", "implementer.md",
    "landing-verifier.md", "pre-check.md", "researcher.md",
    "safety-auditor.md", "scaffolder.md", "spec-reviewer.md", "test-writer.md",
]  # 16

SKILLS: list[str] = [
    "keel-pipeline", "keel-adopt", "keel-setup", "keel-refine", "keel-safety-check",
]

HOOKS: list[str] = ["keel-safety-gate.py", "keel-doc-gate.py"]

PROCESS_DOCS: list[str] = [
    "THE-KEEL-PROCESS.md", "QUICK-START.md", "BROWNFIELD.md", "GLOSSARY.md",
    "ANTI-PATTERNS.md", "FAILURE-PLAYBOOK.md", "AUTONOMY-PROGRESSION.md",
    "KEEL-PRINCIPLES.md",
]

# User-facing framework scripts shipped into installs under scripts/.
# Iterated by install.py's _copy_scripts. Invoked from the user's repo
# root (e.g. `python3 scripts/validate-prds.py --repo .`). Install-time
# entrypoints (install.py, uninstall.py) and stdlib helper modules
# (keel_manifest.py, keel_receipt.py, keel_settings.py) are tracked
# separately via their own call sites and are NOT in this list.
#
# Framework-only scripts (validate-handoff.py, validate-bootstrap-gate.py,
# validate-manifest.py) run against this repo and are intentionally NOT
# shipped — they would be noise in a user install.
SCRIPTS: list[str] = [
    "validate-prds.py",
    "keel-prd-view.py",
    "upgrade-invariant-7.py",
]

# KEEL-internal scripts under scripts/ that are NOT shipped to installs.
# Install-time entrypoints (install.py, uninstall.py), framework-only
# validators (validate-handoff.py, validate-bootstrap-gate.py,
# validate-manifest.py), and stdlib helper modules (keel_manifest.py,
# keel_receipt.py, keel_settings.py). Consumed by
# scripts/validate-manifest.py's disk↔SCRIPTS cross-check so adding a new
# internal utility requires editing this list — the validator will flag
# any un-declared .py under scripts/ that isn't in SCRIPTS either.
INTERNAL_SCRIPTS: set[str] = {
    "install.py",
    "uninstall.py",
    "validate-handoff.py",
    "validate-bootstrap-gate.py",
    "validate-manifest.py",
    "keel_manifest.py",
    "keel_receipt.py",
    "keel_settings.py",
}

TEMPLATE_ROOT_FILES: list[str] = [
    "CLAUDE.md", "ARCHITECTURE.md", "Dockerfile", "docker-compose.yml",
]

TEMPLATE_DOCS: list[str] = [
    "docs/north-star.md",
    "docs/design-docs/core-beliefs.md",
    "docs/design-docs/ui-design.md",
    "docs/design-docs/index.md",
    "docs/product-specs/_TEMPLATE.md",
    "docs/exec-plans/active/feature-backlog.md",
    "docs/exec-plans/active/handoffs/_TEMPLATE.md",
    "docs/exec-plans/prds/.gitkeep",
    "docs/exec-plans/tech-debt-tracker.md",
    "docs/references/README.md",
]

HOOK_COMMAND_SIGNATURES: list[str] = [
    # KEEL-owned entries in settings.json.
    ".claude/hooks/keel-safety-gate.py",
    ".claude/hooks/keel-doc-gate.py",
]

# Hook specs that install.py inserts into .claude/settings.json.
# Each entry's `signature` must also appear in HOOK_COMMAND_SIGNATURES
# above; CI enforces this (see scripts/validate-manifest.py).
KEEL_HOOKS_SPEC: list[dict[str, str]] = [
    {
        "event": "PreToolUse",
        "matcher": "Edit|Write",
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/keel-safety-gate.py"',
        "signature": ".claude/hooks/keel-safety-gate.py",
    },
    {
        "event": "PostToolUse",
        "matcher": "Bash",
        "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/keel-doc-gate.py"',
        "signature": ".claude/hooks/keel-doc-gate.py",
    },
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
