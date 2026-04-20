#!/usr/bin/env python3
"""KEEL Uninstall — Remove KEEL artifacts from your project.

ONLY removes files installed by KEEL. Never touches your application
code, git history, or files you created yourself.

Usage (from your project root):
    python3 .claude/keel-uninstall.py
    OR
    python3 /path/to/keel/scripts/uninstall.py
"""

import os
import sys
from pathlib import Path


KEEL_AGENTS = [
    "pre-check.md", "arch-advisor.md", "researcher.md",
    "backend-designer.md", "frontend-designer.md",
    "test-writer.md", "implementer.md",
    "code-reviewer.md", "spec-reviewer.md", "safety-auditor.md",
    "landing-verifier.md", "doc-gardener.md",
    "docker-builder.md", "scaffolder.md", "config-writer.md",
]

KEEL_SKILLS = ["keel-pipeline", "keel-adopt", "safety-check"]

KEEL_HOOKS = ["safety-gate.py", "doc-gate.py"]

KEEL_PROCESS_DOCS = [
    "THE-KEEL-PROCESS.md", "QUICK-START.md", "BROWNFIELD.md",
    "GLOSSARY.md", "ANTI-PATTERNS.md", "FAILURE-PLAYBOOK.md",
    "AUTONOMY-PROGRESSION.md",
]


def rmdir_if_empty(path: Path):
    """Remove directory only if it's empty."""
    try:
        if path.is_dir():
            path.rmdir()
            print(f"  Removed empty {path}/")
    except OSError:
        pass  # not empty


def main():
    project_dir = Path.cwd()

    print("=" * 48)
    print("  KEEL — Uninstall")
    print(f"  Project: {project_dir}")
    print("=" * 48)
    print()

    # --- Count what will be removed ---
    agents = [a for a in KEEL_AGENTS if (project_dir / ".claude" / "agents" / a).exists()]
    skills = [s for s in KEEL_SKILLS if (project_dir / ".claude" / "skills" / s).is_dir()]
    hooks = [h for h in KEEL_HOOKS if (project_dir / ".claude" / "hooks" / h).exists()]
    docs = [d for d in KEEL_PROCESS_DOCS if (project_dir / "docs" / "process" / d).exists()]

    if not agents and not skills and not hooks and not docs:
        print(f"No KEEL artifacts found in {project_dir}. Nothing to remove.")
        sys.exit(0)

    print("Found KEEL artifacts:")
    if agents:
        print(f"  {len(agents)} agents in .claude/agents/")
    if skills:
        print(f"  {len(skills)} skills in .claude/skills/")
    if hooks:
        print(f"  {len(hooks)} hooks in .claude/hooks/")
    if docs:
        print(f"  {len(docs)} process docs in docs/process/")

    print()
    print("This will NOT touch:")
    print("  - Your application code")
    print("  - Your git history")
    print("  - CLAUDE.md, ARCHITECTURE.md (your project docs)")
    print("  - docs/product-specs/, docs/exec-plans/ (your content)")
    print("  - Dockerfile, docker-compose.yml (your config)")
    print()

    confirm = input("Remove KEEL artifacts? (y/n): ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        sys.exit(0)

    # --- Remove agents ---
    for a in agents:
        path = project_dir / ".claude" / "agents" / a
        path.unlink()
        print(f"  Removed .claude/agents/{a}")

    # --- Remove skills ---
    import shutil
    for s in skills:
        path = project_dir / ".claude" / "skills" / s
        shutil.rmtree(path)
        print(f"  Removed .claude/skills/{s}/")

    # --- Remove hooks ---
    for h in hooks:
        path = project_dir / ".claude" / "hooks" / h
        path.unlink()
        print(f"  Removed .claude/hooks/{h}")

    # --- Remove process docs ---
    for d in docs:
        path = project_dir / "docs" / "process" / d
        path.unlink()
        print(f"  Removed docs/process/{d}")

    # --- Remove bundled uninstall script ---
    for name in ("keel-uninstall.py", "keel-uninstall.sh"):
        path = project_dir / ".claude" / name
        if path.exists():
            path.unlink()
            print(f"  Removed .claude/{name}")

    # --- Clean up empty directories ---
    rmdir_if_empty(project_dir / ".claude" / "agents")
    rmdir_if_empty(project_dir / ".claude" / "skills")
    rmdir_if_empty(project_dir / ".claude" / "hooks")
    rmdir_if_empty(project_dir / ".claude")
    rmdir_if_empty(project_dir / "docs" / "process")

    print()
    print("=" * 48)
    print("  KEEL artifacts removed.")
    print()
    print("  Kept (if present):")
    print("    CLAUDE.md, ARCHITECTURE.md")
    print("    docs/product-specs/, docs/exec-plans/")
    print("    docs/design-docs/, docs/north-star.md")
    print("    Dockerfile, docker-compose.yml")
    print("    All your application code")
    print("=" * 48)


if __name__ == "__main__":
    main()
