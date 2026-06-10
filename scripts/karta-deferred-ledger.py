#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
"""karta-deferred-ledger — the Karta deferred-debt ledger scanner.

Walks the tree for deferred-debt markers (KARTA-DEFER / KARTA-PLACEHOLDER /
KARTA-GUARD), parses each, and DERIVES the ledger view. It stores nothing: the
markers in the tree are the sole source of truth (P4); this script is the
synthesizer P3 requires only be *possible*, realized as a script.

Marker grammar (one line, in a code comment, at the site of the cut):

    KARTA-DEFER: <what was cut>        | real: <what right looks like> | finish: <hint>
    KARTA-PLACEHOLDER: <what is faked> | real: <the real thing>        | finish: <hint>
    KARTA-GUARD: <destructive/irreversible effect, any owner> | real: <safe form> | finish: <hint>

  - `what`   — free text between the token's `:` and the first ` | `; required.
  - `real:`  — required; the intended behavior hardening targets.
  - `finish:`— optional hint; shown as "(no finish hint)" when absent.
  - Canonical field separator is ` | ` (space-pipe-space), but parsing is
    robust: a `|` is a field boundary ONLY when it is followed by a `<key>:`
    field; any other `|` is literal. So spacing variants (`|real:`, ` |  finish:`)
    parse fine and a literal `|` inside a value (`real: choose A | B`) stays
    text — neither is mistaken for malformed. An unknown field key (anything but
    `real`/`finish`) is malformed.

A marker is recognized only when its token follows a comment leader on the
line (`//`, `#`, `--`, `/*`, `<!--`, `;`, `%`, and the Python/Batch leaders).
A bare line at column zero — e.g. a grammar example in fenced doctrine prose —
is NOT a marker, and markdown (`.md`) is skipped entirely: markers live in CODE
comments, never docs. A standalone `*` is deliberately not a leader, so a
markdown bullet (`* KARTA-DEFER: ...`) is never a marker. The scanner keys off
the marker token, not any one comment syntax. Because a decoy token can appear
earlier on a line (e.g. inside a string literal) before the real comment
marker, the per-line scan inspects EVERY occurrence of every kind token and
parses the first one that is genuinely inside a comment — not merely the first
occurrence of the token text.

Modes:
  (default)  report — print the ledger view grouped by file, with the
             git-blame-derived age of each marker line. Always exits 0.
  --lint     reject malformed markers; exit 1 if any marker is malformed.
  --check    assert clean; exit 1 if ANY marker survives (the clean-ledger
             exit-check). Names each surviving marker file:line.

  --format text|json   human-readable (default) or machine output.
  --root <dir>         tree root to scan (default: cwd).

Exit codes:
  0  report printed, or the requested check passed
  1  check failed — malformed marker (--lint) or surviving marker (--check)
  2  operational error — bad arguments, unreadable path

Honest limit: a marker-walking scanner detects only *declared* debt. A
shortcut taken with NO marker is invisible by construction; this script does
not close the silent-debt hole and must not be described as if it does. See
docs/process/PIPELINE-DOCTRINE.md §Declared-debt markers.

Cross-platform: path-anchored, pathlib throughout, no POSIX-only assumptions.
Stdlib-only (declared in the PEP 723 header above with no `dependencies`).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

KINDS = ("KARTA-DEFER", "KARTA-PLACEHOLDER", "KARTA-GUARD")

# The blind-spot caveat. A marker-walking scanner sees only DECLARED debt; a
# shortcut taken with no marker is invisible by construction. A clean scan (zero
# markers) is the moment that limit most needs restating — "clean" reads as "no
# debt" unless the consumer is reminded the ledger records only declared debt.
# Emitted on the zero-marker report and on a passing `--check`, so the blind
# spot is legible at the point of consumption, not only in doctrine.
ZERO_MARKER_CAVEAT = (
    "0 declared markers — undeclared shortcuts are invisible by construction "
    "(the ledger records only declared debt)."
)

# A line is a marker only when the token follows a comment leader. We do not
# parse comment syntax per language; we just require *some* leader before the
# token so bare prose (a fenced grammar example at column 0) is not a marker.
#
# Bare `*` is deliberately NOT a leader: a markdown bullet (`* KARTA-DEFER: ...`)
# is prose, not a code comment, and markers live in CODE comments per the
# doctrine. Including `*` would let a bullet in tech-debt-tracker.md, a doctrine
# grammar example, or user markdown read as a real marker and block --check.
# The cost is that a marker on a JSDoc/C block-comment continuation
# line (` * KARTA-DEFER: ...`) is no longer recognized — author it on the `/*`
# opener line or with `//` instead. That trade favors not blocking the
# clean-ledger check on a doc bullet over catching the rare continuation-line marker. Markdown is
# further excluded by suffix (see _SKIP_SUFFIXES) — the two cuts are
# belt-and-suspenders for the same "markers belong in code, not docs" rule.
# Symbolic comment openers. A marker token counts as "in a comment" when one of
# these appears ANYWHERE in the run of text before the token — the comment
# opened earlier on the line. Containment (not endswith) so a leader followed by
# other text is still caught: `// TODO: KARTA-DEFER`, `/** KARTA-DEFER */` (JSDoc
# — `/**` would fail an endswith("/*") test), `//! ...` (Rust doc). A debt
# scanner must bias toward detection: a rare non-comment false positive blocks
# --check with a fixable CTA, whereas a MISSED declared marker is silent debt
# that survives undetected.
_SYMBOLIC_LEADERS = ("//", "#", "/*", "<!--", "--", ";", "%", "'''", '"""')
# Word comment openers (Batch). Matched only at line start with a word boundary,
# so `lorem` / `theorem` do NOT match `rem`.
_WORD_LEADERS = ("rem", "REM")

# Known field keys after `what`. An unknown key makes the marker malformed.
_KNOWN_FIELDS = ("real", "finish")

# Field boundary: a pipe that introduces a `<key>:` field. The canonical
# separator is ` | ` (space-pipe-space), but we parse robustly so spacing
# variants (`|real:`, ` |  finish:`) do not produce false-malformed verdicts and
# a bare `|` inside a free-text value (`real: choose A | B`) stays literal. A
# pipe counts as a field boundary ONLY when the run after it (whitespace
# stripped) begins with an identifier-shaped key followed by `:`; any other pipe
# is part of the current field's value. The key word is captured so an unknown
# key (e.g. `owner:`) is still detected as malformed rather than swallowed.
_FIELD_BOUNDARY = re.compile(r"\s*\|\s*([A-Za-z][\w-]*)\s*:")

# Directories never worth walking. `.git` is the VCS store; the rest are
# conventional vendor/build/cache trees. This is a coarse floor; the
# authoritative ignore surface is the project's own .gitignore, honored via
# `git check-ignore` when the tree is a git repo (see _gitignored).
_SKIP_DIRS = frozenset({
    ".git", ".hg", ".svn", "node_modules", ".venv", "venv",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "dist", "build", ".tox", ".idea", ".gradle", "target",
})

# Files we never read as text. Two reasons live here:
#   - binary by extension — a cheap pre-filter; a UnicodeDecodeError on read is
#     the real backstop for anything that slips through;
#   - markdown (`.md`) — markers belong in CODE comments per the doctrine, so a
#     `KARTA-DEFER:` token in a doc is prose, never a real marker: a grammar
#     example in PIPELINE-DOCTRINE.md, a bullet in
#     tech-debt-tracker.md, or any user markdown. Skipping `.md` keeps those out
#     of --check. (Bare `*` is also absent from the symbolic leaders
#     so a bullet in a non-.md doc is still not a marker.)
_SKIP_SUFFIXES = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".pdf", ".zip", ".gz", ".tar", ".whl", ".so", ".dylib", ".dll",
    ".pyc", ".pyo", ".class", ".jar", ".bin", ".lock", ".woff", ".woff2",
    ".ttf", ".otf", ".eot", ".mp4", ".mov", ".mp3", ".wav",
    ".md",
})


@dataclass(slots=True, frozen=True)
class LedgerEntry:
    """One parsed deferred-debt marker. `file` is repo-root-relative POSIX.
    `malformed` carries the reason text when the marker is malformed (else
    empty). `real`/`finish` are None when absent."""
    file: str
    line: int
    kind: str
    what: str
    real: str | None
    finish: str | None
    malformed: str  # empty string = well-formed


# --- parsing ---------------------------------------------------------------

def _in_comment(text: str, token_idx: int) -> bool:
    """True if the marker token at `token_idx` sits in a comment — i.e. a comment
    opener appears in the run of text before the token. Containment (not
    endswith) for symbolic openers, so a leader followed by other text still
    counts (`// TODO: KARTA-DEFER`, `/** KARTA-DEFER */`, `//! ...`). Word openers
    (Batch rem/REM) match only at line start with a word boundary, so
    `lorem`/`theorem` do not. A whitespace-only prefix (column-zero token — e.g.
    a fenced grammar example in doctrine prose) has no opener and is not a
    comment."""
    prefix = text[:token_idx]
    if any(sym in prefix for sym in _SYMBOLIC_LEADERS):
        return True
    head = prefix.lstrip()
    return any(
        head[: len(w)] == w and (len(head) == len(w) or not head[len(w)].isalnum())
        for w in _WORD_LEADERS
    )


def parse_marker_line(rel_file: str, lineno: int, text: str) -> LedgerEntry | None:
    """Parse a single physical line into a LedgerEntry, or None if the line
    carries no recognized marker token in a comment. A recognized token with a
    broken body yields a LedgerEntry with `malformed` set (so --lint can report
    it).

    Find-all, not find-once: a kind token can appear MORE THAN ONCE on a line —
    a string-literal decoy (`log("KARTA-DEFER:")`) ahead of the real comment
    marker, or a token of one kind outside a comment ahead of a real marker of
    another kind. We must inspect EVERY occurrence of EVERY kind token, checking
    `_in_comment` per occurrence, and parse the FIRST occurrence that is
    genuinely inside a comment — leftmost wins among the in-comment hits, since
    that is the marker the comment opener governs. A naive `text.find(needle)`
    that bailed on the first occurrence (in or out of a comment) silently missed
    the real marker hidden behind a decoy — silent deferred debt that survives
    undetected, which is exactly what this scanner exists to prevent."""
    best: tuple[int, str] | None = None  # (token_idx, kind) of leftmost in-comment hit
    for kind in KINDS:
        needle = kind + ":"
        pos = text.find(needle)
        while pos != -1:
            if _in_comment(text, pos):
                if best is None or pos < best[0]:
                    best = (pos, kind)
                break  # for this kind, the leftmost in-comment hit is enough
            pos = text.find(needle, pos + 1)  # decoy (not in comment) — keep scanning
    if best is None:
        return None  # no kind token sits in a comment — not a marker
    idx, kind = best
    body = text[idx + len(kind) + 1:].rstrip("\n").rstrip("\r")  # +1 for the `:`
    return _parse_body(rel_file, lineno, kind, body)


def _parse_body(rel_file: str, lineno: int, kind: str, body: str) -> LedgerEntry:
    """Parse the post-token body: `<what> | real: <r> | finish: <p>`.

    Robust to spacing variants around the pipe separator and to a literal `|`
    inside a free-text value. A pipe is a field boundary only when it introduces
    a `<key>:` field (see _FIELD_BOUNDARY); any other pipe stays literal, so it
    never produces a false-malformed verdict."""
    boundaries = list(_FIELD_BOUNDARY.finditer(body))
    what = (body[: boundaries[0].start()] if boundaries else body).strip()

    fields: dict[str, str] = {}
    bad_keys: list[str] = []
    for i, match in enumerate(boundaries):
        key = match.group(1).strip().lower()
        val_end = boundaries[i + 1].start() if i + 1 < len(boundaries) else len(body)
        val = body[match.end():val_end].strip()
        if key not in _KNOWN_FIELDS:
            bad_keys.append(key)
            continue
        fields[key] = val

    reasons: list[str] = []
    if not what:
        reasons.append("empty `what`")
    if "real" not in fields or not fields["real"]:
        reasons.append("missing required `real:`")
    if bad_keys:
        reasons.append("unknown field(s): " + ", ".join(sorted(set(bad_keys))))

    return LedgerEntry(
        file=rel_file,
        line=lineno,
        kind=kind,
        what=what,
        real=fields.get("real"),
        finish=fields.get("finish"),
        malformed="; ".join(reasons),
    )


# --- walking ---------------------------------------------------------------

def _is_git_repo(root: Path) -> bool:
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, check=False,
        )
        return r.returncode == 0 and r.stdout.strip() == "true"
    except (OSError, ValueError):
        return False


def _gitignored(root: Path, paths: list[Path]) -> set[Path]:
    """Return the subset of `paths` git considers ignored. Empty set if not a
    git repo or git is unavailable — the walk then relies on _SKIP_* only."""
    if not paths:
        return set()
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "--stdin"],
            input="\n".join(str(p) for p in paths),
            capture_output=True, text=True, check=False,
        )
    except (OSError, ValueError):
        return set()
    if r.returncode not in (0, 1):  # 0=some ignored, 1=none ignored
        return set()
    ignored = {Path(line) for line in r.stdout.splitlines() if line.strip()}
    return ignored


# The scanner's own source documents the marker grammar with the literal
# KARTA-DEFER / KARTA-PLACEHOLDER / KARTA-GUARD tokens (its docstring +
# explanatory comments), so it must not scan itself — a tool does not flag its
# own self-documentation. This is the one code file that ships into installs
# carrying the literal tokens (the `.md` docs are skipped by suffix; `tests/`
# is not installed), so exempting it keeps a user's `--check` clean.
_SELF_PATH = Path(__file__).resolve()


def iter_text_files(root: Path, use_git: bool) -> Iterator[Path]:
    """Yield candidate text files under `root`, pruning skip-dirs, binary
    suffixes, the scanner's own source, and (when in git) gitignored paths.

    Uses `os.walk` with IN-PLACE directory pruning so huge ignored trees
    (node_modules, .venv, .git, …) are never descended — `rglob("*")` would
    materialize every path under them before filtering, an OOM/slowdown risk on
    real repos."""
    candidates: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skip-dirs in place: os.walk will not descend what we remove.
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            if not path.is_file():
                continue  # skip broken symlinks / special files
            if path.suffix.lower() in _SKIP_SUFFIXES:
                continue
            if path.resolve() == _SELF_PATH:
                continue  # never scan the scanner's own source (self-documentation)
            candidates.append(path)
    candidates.sort()
    ignored = _gitignored(root, candidates) if use_git else set()
    for path in candidates:
        if path in ignored:
            continue
        yield path


def scan(root: Path) -> tuple[list[LedgerEntry], bool, list[str]]:
    """Walk `root` and return (entries, used_git, unreadable). `used_git`
    reflects whether git enrichment (blame age, ignore) is available.
    `unreadable` lists files that could not be read at all (OSError, e.g. a
    permission error) — those could HIDE a surviving marker, so --lint/--check
    treat them as an operational error rather than skipping them. Stray
    non-UTF-8 bytes do NOT make a file unreadable: we decode with
    errors="replace" so the file is still scanned for markers (replacement
    chars don't perturb ASCII marker tokens). A clean decode would have let a
    single bad byte silently skip a whole file and any marker it carries — a
    hole in the fail-closed design."""
    use_git = _is_git_repo(root)
    entries: list[LedgerEntry] = []
    unreadable: list[str] = []
    for path in iter_text_files(root, use_git):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            unreadable.append(path.relative_to(root).as_posix())
            continue
        rel = path.relative_to(root).as_posix()
        for lineno, line in enumerate(text.splitlines(), start=1):
            m = parse_marker_line(rel, lineno, line)
            if m is not None:
                entries.append(m)
    return entries, use_git, unreadable


# --- git-blame-derived age -------------------------------------------------

def blame_age(root: Path, rel_file: str, lineno: int) -> str:
    """Derive the age of a marker line from `git blame --porcelain`. Returns a
    human string like '3d' / '2mo' / '1y', or 'unknown' when git is
    unavailable, the line is uncommitted, or blame fails. NEVER stored."""
    try:
        r = subprocess.run(
            ["git", "-C", str(root), "blame", "--porcelain",
             "-L", f"{lineno},{lineno}", "--", rel_file],
            capture_output=True, text=True, check=False,
        )
    except (OSError, ValueError):
        return "unknown"
    if r.returncode != 0:
        return "unknown"
    author_time: int | None = None
    for line in r.stdout.splitlines():
        if line.startswith("author-time "):
            try:
                author_time = int(line.split()[1])
            except (IndexError, ValueError):
                return "unknown"
            break
    if author_time is None:
        return "unknown"  # uncommitted line (zero-SHA blame carries no time)
    committed = datetime.fromtimestamp(author_time, tz=timezone.utc)
    delta = datetime.now(tz=timezone.utc) - committed
    days = delta.days
    if days < 0:
        return "unknown"
    if days == 0:
        return "today"
    if days < 30:
        return f"{days}d"
    if days < 365:
        return f"{days // 30}mo"
    return f"{days // 365}y"


# --- rendering -------------------------------------------------------------

def _group_by_file(entries: list[LedgerEntry]) -> dict[str, list[LedgerEntry]]:
    grouped: dict[str, list[LedgerEntry]] = defaultdict(list)
    for m in entries:
        grouped[m.file].append(m)
    for v in grouped.values():
        v.sort(key=lambda m: m.line)
    return dict(sorted(grouped.items()))


def render_report_text(root: Path, entries: list[LedgerEntry], used_git: bool) -> str:
    if not entries:
        return ("karta-deferred-ledger: no declared-debt markers found.\n"
                f"{ZERO_MARKER_CAVEAT}\n")
    out: list[str] = []
    out.append(f"karta-deferred-ledger: {len(entries)} declared-debt marker(s) "
               f"across {len({m.file for m in entries})} file(s).\n")
    for rel_file, file_entries in _group_by_file(entries).items():
        out.append(f"\n{rel_file}")
        for m in file_entries:
            age = blame_age(root, m.file, m.line) if used_git else "unknown"
            out.append(f"  {m.line}: {m.kind}  (age: {age})")
            if m.malformed:
                out.append(f"      MALFORMED: {m.malformed}")
            out.append(f"      what:   {m.what or '(empty)'}")
            out.append(f"      real:   {m.real if m.real else '(MISSING)'}")
            out.append(f"      finish: {m.finish if m.finish else '(no finish hint)'}")
    out.append("")
    return "\n".join(out) + "\n"


def render_report_json(root: Path, entries: list[LedgerEntry], used_git: bool) -> str:
    payload = {
        "marker_count": len(entries),
        "file_count": len({m.file for m in entries}),
        "git_enrichment": used_git,
        "markers": [
            {
                "file": m.file,
                "line": m.line,
                "kind": m.kind,
                "what": m.what,
                "real": m.real,
                "finish": m.finish,
                "age": blame_age(root, m.file, m.line) if used_git else "unknown",
                "malformed": m.malformed or None,
            }
            for m in sorted(entries, key=lambda x: (x.file, x.line))
        ],
    }
    return json.dumps(payload, indent=2) + "\n"


# --- gating modes ----------------------------------------------------------

def run_lint(entries: list[LedgerEntry], fmt: str) -> int:
    bad = [m for m in entries if m.malformed]
    if fmt == "json":
        print(json.dumps({
            "mode": "lint",
            "malformed_count": len(bad),
            "malformed": [
                {"file": m.file, "line": m.line, "kind": m.kind,
                 "reason": m.malformed}
                for m in sorted(bad, key=lambda x: (x.file, x.line))
            ],
        }, indent=2))
        return 1 if bad else 0
    if not bad:
        print("karta-deferred-ledger --lint: all markers well-formed.")
        return 0
    print(f"karta-deferred-ledger --lint: {len(bad)} malformed marker(s).\n",
          file=sys.stderr)
    for m in sorted(bad, key=lambda x: (x.file, x.line)):
        print(f"  {m.file}:{m.line} — {m.kind}: {m.malformed}", file=sys.stderr)
    print("\nNext step: fix each marker so it carries a non-empty `what` and a "
          "`real:` clause, with no unknown fields.", file=sys.stderr)
    return 1


def run_check(entries: list[LedgerEntry], fmt: str) -> int:
    if fmt == "json":
        print(json.dumps({
            "mode": "check",
            "surviving_count": len(entries),
            "surviving": [
                {"file": m.file, "line": m.line, "kind": m.kind, "what": m.what}
                for m in sorted(entries, key=lambda x: (x.file, x.line))
            ],
        }, indent=2))
        return 1 if entries else 0
    if not entries:
        print("karta-deferred-ledger --check: clean — no declared-debt markers survive.")
        print(ZERO_MARKER_CAVEAT)
        return 0
    print(f"karta-deferred-ledger --check: {len(entries)} declared-debt marker(s) "
          f"still standing — the ledger is not clean.\n", file=sys.stderr)
    for m in sorted(entries, key=lambda x: (x.file, x.line)):
        print(f"  {m.file}:{m.line} — {m.kind}: {m.what or '(empty)'}",
              file=sys.stderr)
    print("\nNext step: finish each marker through /keel-refine -> /keel-pipeline, "
          "or consciously retire it (tech-debt-tracker.md). `--check` passes "
          "only when the ledger is clean.", file=sys.stderr)
    return 1


# --- entrypoint ------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="karta-deferred-ledger",
        description="Scan the tree for deferred-debt markers and derive the "
                    "ledger view.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--lint", action="store_true",
                      help="exit nonzero if any marker is malformed")
    mode.add_argument("--check", action="store_true",
                      help="exit nonzero if ANY marker survives (clean-ledger check)")
    parser.add_argument("--format", choices=("text", "json"), default="text",
                        help="output format (default: text)")
    parser.add_argument("--root", default=".",
                        help="tree root to scan (default: current directory)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"karta-deferred-ledger: not a directory: {args.root}", file=sys.stderr)
        return 2

    try:
        entries, used_git, unreadable = scan(root)
    except OSError as exc:
        print(f"karta-deferred-ledger: scan failed: {exc}", file=sys.stderr)
        return 2

    # --lint/--check are pass/fail checks: an unreadable file could hide a marker,
    # so refuse to assert a clean/well-formed result over files we could not read
    # (fail-closed, not fail-open). Report mode notes them but still prints.
    if unreadable and (args.lint or args.check):
        print(f"karta-deferred-ledger: {len(unreadable)} file(s) could not be read; "
              f"cannot assert a result over them (a surviving marker could be "
              f"hidden):", file=sys.stderr)
        for p in unreadable:
            print(f"  {p}", file=sys.stderr)
        print("Fix permissions or exclude them (.gitignore), then re-run.",
              file=sys.stderr)
        return 2

    if args.lint:
        return run_lint(entries, args.format)
    if args.check:
        return run_check(entries, args.format)

    if unreadable:
        print(f"karta-deferred-ledger: note — {len(unreadable)} file(s) skipped as "
              f"unreadable (not scanned for markers).", file=sys.stderr)

    if args.format == "json":
        sys.stdout.write(render_report_json(root, entries, used_git))
    else:
        sys.stdout.write(render_report_text(root, entries, used_git))
    return 0


if __name__ == "__main__":
    sys.exit(main())
