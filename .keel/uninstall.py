#!/usr/bin/env python3
"""KEEL Uninstall — Remove KEEL artifacts from your project.

Receipt-driven: reads .keel/install.json and removes only paths
KEEL actually wrote. Files modified since install are preserved unless
--purge. Without a receipt, exits 1 — there is nothing to do.

Flags:
  --purge       Delete receipt-owned paths regardless of hash drift.
  --dry-run     Print the plan; exit without touching disk.
  -y, --yes     Skip confirmation prompt.

Exit codes: 0 success; 1 no receipt (not a KEEL install); 2 user declined;
10 receipt schema too new; 11 receipt corrupt; 20 partial I/O failure
(re-runnable).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

if sys.version_info < (3, 14):
    sys.exit(
        "KEEL requires Python 3.14+ "
        f"(found {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}).\n"
        "Install a supported Python and re-run, e.g.:\n"
        "  uv python install 3.14 && uv run --python 3.14 .keel/uninstall.py -y\n"
        "  (or install 3.14 system-wide and invoke with python3.14)"
    )

_script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_script_dir))
from keel_manifest import (
    SETTINGS_FILE, RECEIPT_PATH,
    RECEIPT_SCHEMA_VERSION,
    install_dirs,
    AGENTS, SKILLS, HOOKS,
)
import keel_receipt as kr
import keel_settings as ksj

# Receipt schemas this uninstaller can read. The bundled uninstaller is
# install-time-frozen, so it normally meets its own receipt — but it tolerates
# every prior schema so a newer uninstaller can still clean an older install
# (§2). v2 predates the `host` field; absence reads as host=claude.
SUPPORTED_RECEIPT_SCHEMAS = (2, 3)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Remove KEEL artifacts from a project.")
    p.add_argument("--purge", action="store_true",
                   help="Delete receipt-owned paths regardless of hash drift.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print plan; do not modify.")
    p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation.")
    return p.parse_args(argv)


_GITIGNORE_BEGIN = "# >>> KEEL-managed gitignore exceptions — DO NOT EDIT this block >>>"
_GITIGNORE_END = "# <<< KEEL-managed gitignore exceptions <<<"

_WORKTREE_GITIGNORE_BEGIN = "# >>> KEEL-managed worktree exclusion — DO NOT EDIT this block >>>"
_WORKTREE_GITIGNORE_END = "# <<< KEEL-managed worktree exclusion <<<"


def _strip_keel_gitignore_block(project_dir: Path) -> bool:
    """Remove the marker-bracketed exception block install.py inserted.
    Returns True if .gitignore was modified. No-op if the block is
    absent or .gitignore doesn't exist (the install never had to add
    it — nothing was gitignoring KEEL paths).
    """
    gitignore = project_dir / ".gitignore"
    if not gitignore.exists():
        return False
    content = gitignore.read_text("utf-8")
    block_re = re.compile(
        re.escape(_GITIGNORE_BEGIN) + r"\n.*?\n" + re.escape(_GITIGNORE_END) + r"\n?",
        re.DOTALL,
    )
    new = block_re.sub("", content)
    # Collapse the doubled blank line we'd leave behind.
    new = re.sub(r"\n\n\n+", "\n\n", new)
    if new == content:
        return False
    gitignore.write_text(new, encoding="utf-8")
    return True


def _strip_keel_worktree_gitignore_block(project_dir: Path) -> bool:
    """Remove the marker-bracketed worktree-exclusion block install.py
    inserted (the `.keel/worktrees/` scaffolding exclusion). Mirrors
    `_strip_keel_gitignore_block` exactly, matching the worktree markers.
    Returns True if .gitignore was modified. No-op if the block is
    absent or .gitignore doesn't exist.
    """
    gitignore = project_dir / ".gitignore"
    if not gitignore.exists():
        return False
    content = gitignore.read_text("utf-8")
    block_re = re.compile(
        re.escape(_WORKTREE_GITIGNORE_BEGIN) + r"\n.*?\n"
        + re.escape(_WORKTREE_GITIGNORE_END) + r"\n?",
        re.DOTALL,
    )
    new = block_re.sub("", content)
    # Collapse the doubled blank line we'd leave behind.
    new = re.sub(r"\n\n\n+", "\n\n", new)
    if new == content:
        return False
    gitignore.write_text(new, encoding="utf-8")
    return True


def _path_hash(p: Path) -> str:
    return kr.hash_dir(p) if p.is_dir() else kr.hash_file(p)


def _rmpath(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _plan_receipt_mode(project_dir: Path, receipt: dict, purge: bool):
    to_delete: list[tuple[str, str]] = []
    preserved: list[tuple[str, str]] = []
    missing: list[str] = []

    for rel, entry in receipt.get("managed_paths", {}).items():
        abs_p = project_dir / rel
        if not abs_p.exists():
            missing.append(rel)
            continue
        expected = entry["installed_hash"]
        actual = _path_hash(abs_p)
        if purge:
            to_delete.append((rel, entry.get("kind", "unknown")))
        elif actual == expected:
            to_delete.append((rel, entry.get("kind", "unknown")))
        else:
            preserved.append((rel, "modified_since_install"))
    return to_delete, preserved, missing


def _managed_prefixes() -> set[str]:
    """Namespace prefixes KEEL ships, derived from the manifest's own
    AGENTS/SKILLS/HOOKS entry names (the leading token before the first
    `-`). Covers both `keel-` and `karta-` without a second literal, so a
    new shipped namespace is picked up by adding its manifest entry alone.
    """
    prefixes: set[str] = set()
    for name in (*AGENTS, *SKILLS, *HOOKS):
        head = name.split("-", 1)[0]
        if head:
            prefixes.add(head)
    return prefixes


def _orphan_scan(project_dir: Path, managed_rels: set[str]) -> list[str]:
    """Advisory: report shipped-namespace (e.g. `keel-*`, `karta-*`) files
    in .claude/ and .keel/ NOT in the receipt."""
    candidates: list[Path] = []
    for prefix in _managed_prefixes():
        for pattern in (f".claude/agents/{prefix}-*.md",
                        f".claude/skills/{prefix}-*",
                        f".keel/hooks/{prefix}-*.py"):
            candidates.extend(project_dir.glob(pattern))
    orphans = []
    for c in candidates:
        rel = c.relative_to(project_dir).as_posix()
        if rel not in managed_rels:
            orphans.append(rel)
    return sorted(orphans)


def _handle_settings(project_dir: Path, receipt: dict,
                     dry_run: bool) -> tuple[str, tuple[str, str] | None]:
    """Surgically remove KEEL hook entries.

    Uses the exact commands the install receipt recorded as KEEL-owned,
    so we only remove hooks KEEL actually inserted — not coincidental
    user hooks at the same command path.

    Returns (summary, error). `error` is None on success, else a tuple
    (SETTINGS_FILE, reason) for the caller to append to its errors list.

    On `JSONDecodeError`, if the receipt recorded hook ownership, we
    return a partial-failure error so the caller retains the receipt —
    the user can fix the JSON and re-run to complete uninstall rather
    than losing ownership metadata to a clean-run receipt deletion.
    """
    sp = project_dir / SETTINGS_FILE
    if not sp.exists():
        return "settings.json: absent", None
    receipt_settings = receipt.get("settings_json") or {}
    owned_cmds = list(receipt_settings.get("inserted_hook_commands") or [])
    mode = receipt_settings.get("mode")
    try:
        settings = json.loads(sp.read_text("utf-8"))
    except json.JSONDecodeError as e:
        if owned_cmds:
            return (f"settings.json: invalid JSON ({e}), KEEL hooks may "
                    "remain; fix JSON and retry"), (SETTINGS_FILE,
                                                    f"invalid JSON: {e}")
        return "settings.json: invalid JSON, left untouched", None
    except OSError as e:
        return f"settings.json: read failed ({e})", (SETTINGS_FILE, f"read: {e}")

    # Shape-guard both read paths. `has_non_keel_content` and
    # `remove_hooks_by_command` both call _validate_hooks_shape which
    # raises on valid-JSON-but-weird structures. Treat as partial
    # failure when ownership is recorded so the user can fix and retry.
    def _shape_error(e: Exception):
        msg = (f"settings.json: unexpected shape ({e}), KEEL hooks may "
               "remain; fix and retry") if owned_cmds else (
               f"settings.json: unexpected shape ({e}), left untouched")
        err = (SETTINGS_FILE, f"shape: {e}") if owned_cmds else None
        return msg, err

    try:
        is_keel_only = not ksj.has_non_keel_content(settings, owned_cmds)
    except (ValueError, TypeError) as e:
        return _shape_error(e)

    if mode == "created" and is_keel_only:
        if dry_run:
            return "settings.json: would delete (mode=created, no non-KEEL content)", None
        try:
            sp.unlink()
        except OSError as e:
            return (f"settings.json: delete failed ({e})",
                    (SETTINGS_FILE, f"delete: {e}"))
        return "settings.json: deleted (was KEEL-created)", None

    if not owned_cmds:
        return "settings.json: no KEEL-owned hooks recorded (nothing to remove)", None

    try:
        cleaned, removed = ksj.remove_hooks_by_command(settings, owned_cmds)
    except (ValueError, TypeError) as e:
        return _shape_error(e)
    if removed == 0:
        return "settings.json: no KEEL hooks found (nothing to remove)", None
    if dry_run:
        return f"settings.json: would remove {removed} KEEL hook entries", None
    try:
        sp.write_text(ksj.serialize_stable(cleaned), encoding="utf-8")
    except OSError as e:
        return (f"settings.json: write failed ({e})",
                (SETTINGS_FILE, f"write: {e}"))
    return f"settings.json: removed {removed} KEEL hook entries", None


def _run_receipt_mode(project_dir: Path, receipt: dict, args) -> int:
    schema = receipt.get("receipt_schema_version")
    if schema not in SUPPORTED_RECEIPT_SCHEMAS:
        print(f"Receipt schema {schema} unknown to this uninstaller "
              f"(supports {', '.join(map(str, SUPPORTED_RECEIPT_SCHEMAS))}). "
              f"Aborting.")
        return 10

    to_delete, preserved, missing = _plan_receipt_mode(
        project_dir, receipt, args.purge)
    managed_rels = set(receipt.get("managed_paths", {}).keys())
    orphans = _orphan_scan(project_dir, managed_rels)

    print("=" * 48)
    print("  KEEL — Uninstall (receipt mode)")
    print(f"  Project: {project_dir}")
    print("=" * 48)
    print()
    print(f"  Delete:    {len(to_delete)} paths recorded in receipt")
    print(f"  Preserve:  {len(preserved)} paths modified since install")
    if missing:
        print(f"  Missing:   {len(missing)} paths recorded but gone from disk")
    if orphans:
        print(f"  Advisory:  {len(orphans)} possible orphan keel-*/karta-* paths not in receipt")
        for o in orphans:
            print(f"             {o}")
        print("             (NOT deleted; review and remove manually if unwanted)")
    print()

    if args.dry_run:
        print("--dry-run: exiting without changes.")
        return 0

    if not args.yes:
        ans = input("Proceed? (y/n): ").strip().lower()
        if ans != "y":
            print("Aborted.")
            return 2

    errors: list[tuple[str, str]] = []
    for rel, _kind in to_delete:
        p = project_dir / rel
        try:
            if p.exists():
                _rmpath(p)
                print(f"  Removed {rel}")
        except OSError as e:
            errors.append((rel, str(e)))

    settings_summary, settings_error = _handle_settings(
        project_dir, receipt, dry_run=False)
    print("  " + settings_summary)
    if settings_error is not None:
        errors.append(settings_error)

    if _strip_keel_gitignore_block(project_dir):
        print("  .gitignore — removed KEEL-managed exception block")

    if _strip_keel_worktree_gitignore_block(project_dir):
        print("  .gitignore — removed KEEL-managed worktree block")

    if errors:
        # Rewrite the receipt to contain ONLY the paths that failed
        # deletion plus the preserved entries, so re-running uninstall
        # resumes from this state instead of exiting 1 with "no receipt".
        managed = receipt.get("managed_paths", {})
        remaining_rels = {rel for rel, _ in errors} | {rel for rel, _ in preserved}
        receipt["managed_paths"] = {k: v for k, v in managed.items() if k in remaining_rels}
        kr.save(project_dir, receipt)
    else:
        # Delete receipt before pruning so .keel/ (and .claude/) can be rmdir'd.
        try:
            (project_dir / RECEIPT_PATH).unlink()
        except OSError:
            pass

    # Clear any Python bytecode cache the bundled uninstaller created while
    # importing its sibling modules — otherwise __pycache__ lingers and blocks
    # the parent rmdir below. Siblings live in .keel/ now; clear the legacy
    # .claude/ location too in case an older install left one behind.
    for cache_parent in (".keel", ".claude"):
        pycache = project_dir / cache_parent / "__pycache__"
        if pycache.is_dir():
            try:
                shutil.rmtree(pycache)
            except OSError:
                pass

    # Remove now-empty dirs left behind by the uninstall. The directory set
    # comes from the manifest (install_dirs) — the single source of truth
    # for an install's directory skeleton — unioned with the parents of
    # this install's receipt paths. Manifest-derived so it can't drift from
    # what install writes (the old hardcoded list left empty docs/ shells),
    # and stable across a retry where a prior partial run trimmed the
    # receipt's managed_paths. Deepest first; rmdir only when empty
    # (best-effort — the empty-check preserves any dir holding user content).
    prune = set(install_dirs())
    for rel in receipt.get("managed_paths", {}):
        parts = str(rel).split("/")
        for i in range(1, len(parts)):
            prune.add("/".join(parts[:i]))
    for rel in sorted(prune, key=lambda s: s.count("/"), reverse=True):
        d = project_dir / rel
        try:
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
        except OSError:
            pass

    print()
    print("=" * 48)
    # Path-delete errors are a subset of `errors`; `errors` may also
    # include settings.json failures, which are not in `to_delete`.
    # Count deletions as to_delete rels that are NOT in the error set.
    error_rels = {rel for rel, _ in errors}
    deleted_count = sum(1 for rel, _ in to_delete if rel not in error_rels)
    print(f"  Deleted: {deleted_count} paths")
    if errors:
        print(f"  Failed: {len(errors)} (receipt retained; rerun to resume)")
        for rel, reason in errors:
            print(f"    {rel}  ({reason})")
    print(f"  Preserved (modified): {len(preserved)}")
    if preserved:
        receipt_still_exists = (project_dir / RECEIPT_PATH).exists()
        for rel, _ in preserved:
            if receipt_still_exists:
                print(f"    {rel}  (use --purge to force delete)")
            else:
                print(f"    {rel}  (now untracked — delete manually if unwanted)")
    if orphans:
        print(f"  Advisory orphans reported: {len(orphans)} (not touched)")
    print("=" * 48)
    return 20 if errors else 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project_dir = Path.cwd()
    try:
        receipt = kr.load(project_dir)
    except json.JSONDecodeError:
        print("Receipt corrupt (JSON parse error). Refusing to proceed.")
        print("Try: python3 /path/to/install.py --repair-receipt (deferred).")
        return 11
    if receipt is None:
        print(f"No KEEL install receipt at {RECEIPT_PATH}. "
              "Not a KEEL install — nothing to uninstall.")
        return 1
    return _run_receipt_mode(project_dir, receipt, args)


if __name__ == "__main__":
    sys.exit(main())
