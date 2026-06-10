#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "jsonschema>=4.21",
#   "filelock>=3.16",
#   "pyyaml>=6.0",
# ]
# ///
"""KEEL routing.json update helper.

All routing.json mutations route through this script:
- init           — create or safe-merge routing.json at pipeline start
- set-status     — set top-level status field
- set-routing    — full-block replace routing.routing.* from an envelope
- merge-routing-flag — single-field merge into routing.routing.*
- set-gate       — set a gate verdict + attempt
- set-review     — set a review touchpoint verdict + attempt
- set-pretriage  — set the pretriage outcome block
- set-doc-garden — set the doc-garden verdict + drift_count
- set-branch     — set branch.parent_branch + parent_sha
- incr-escalation — atomically increment precheck_escalation_count;
                    HALT if it would exceed 1
- clear-derived-state — clear routing-STATE only (gates/review/arch_retry/
                    review_retry/doc_garden + reset escalation count +
                    status). The CALLER is responsible for the matching
                    on-disk file wipe: per the route-reset ordering, delete
                    the stale files FIRST, then clear routing-state. (init
                    does its own reset via _build_fresh + _wipe_derived_files;
                    it does NOT call this.)
- clear-gate     — delete routing.gates.<name> (route-reset on flag flip)
- clear-review   — reset routing.review.<touchpoint> to attempt 0
- record-attempt-hash — sha256 an attempt-NN.md, merge into the
                    touchpoint review's .attempt-hashes.json sidecar

There is intentionally no `set-pr-url` (and no `--remote` on `init`): done is
repo-local, so the schema carries no `pr_url`/`branch.remote_name`. Pushing and
opening a PR are forge ceremony handled by the separate `/keel-submit` skill, which
derives the remote at submit time from git state. See
docs/design-docs/mvp-lane/2026-06-03-repo-local-done-design.md.

Every routing.json write:
1. Takes exclusive filelock on routing.json (timeout 5s).
2. Reads + parses current state (or starts empty for init).
3. Applies transform.
4. Validates against schemas/routing.schema.json.
5. Atomic write: tmp + os.replace.
6. Releases lock.

Exit codes:
  0 — success
  1 — schema validation failure
  2 — lock acquisition timeout (>5s)
  3 — operation rejected (e.g., incr-escalation would exceed budget)
  4 — operation argument error
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import yaml
from filelock import FileLock, Timeout
from jsonschema import Draft202012Validator

LOCK_TIMEOUT_S = 5
ESCALATION_BUDGET = 1

# Keys that count as "derived" pipeline state — wiped on source change /
# clear-derived-state, preserved on identity-equivalent safe-merge.
DERIVED_KEYS = ("gates", "arch_retry", "review", "review_retry", "doc_garden")

# routing.routing.* envelope fields (pre-check metadata block).
ROUTING_BOOL_FLAGS = (
    "designer_needed",
    "researcher_needed",
    "safety_auditor_needed",
    "arch_advisor_needed",
    "implementer_needed",
)
ROUTING_ENUM_FLAGS = ("intent", "complexity")

GATE_NAMES = ("spec_review", "safety", "code_review", "arch_verify", "conformance")
REVIEW_TOUCHPOINTS = ("precheck", "design", "landing")

# Canonical per-gate verdict sets — the file-body **Verdict:** word each
# gate agent emits and the orchestrator mirrors here via set-gate. Mirrors
# the enums in schemas/routing.schema.json gates.*.verdict; kept here so
# set-gate can HALT with a gate-specific P7 message naming the allowed
# verdicts (friendlier than the generic post-write schema-fail). The schema
# is the enforcing authority; this is a fast-fail courtesy.
GATE_VERDICTS = {
    "spec_review": ("CONFORMANT", "DEVIATION"),
    "safety":      ("PASS", "VIOLATION"),
    "code_review": ("APPROVED", "CONCERNS"),
    "arch_verify": ("SOUND", "UNSOUND"),
    # Karta lean lane structural conformance gate (karta-spec-reviewer).
    "conformance": ("CONFORMANT", "DEVIATION", "SPEC-SUSPECT"),
}

SCHEMA_REL = Path("schemas") / "routing.schema.json"


# --- halts -----------------------------------------------------------------

class Halt(Exception):
    """Carries an exit code + a P7 message (cause + concrete next step)."""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _halt(code: int, message: str) -> "Halt":
    return Halt(code, message)


# --- schema ----------------------------------------------------------------

def _schema_path() -> Path:
    """Anchor schema lookup to the repo root (script's parent's parent).

    KEEL scripts ship as standalone files — a path-anchored lookup is the
    right tool (AGENTS.md §Python conventions). NOT cwd-relative.
    """
    return Path(__file__).resolve().parent.parent / SCHEMA_REL


def _load_validator() -> Draft202012Validator:
    path = _schema_path()
    if not path.is_file():
        raise _halt(
            4,
            f"routing schema not found at {path}. "
            f"Run from a KEEL framework source tree or installed repo where "
            f"schemas/routing.schema.json exists.",
        )
    return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")))


def _validate(state: dict) -> None:
    validator = _load_validator()
    errors = sorted(validator.iter_errors(state), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        loc = "/" + "/".join(str(p) for p in first.absolute_path)
        raise _halt(
            1,
            f"routing.json failed schema validation at {loc}: "
            f"{first.message.splitlines()[0]}. "
            f"This is a keel-routing.py bug or a corrupted routing.json; "
            f"fix the offending field and re-run the same command.",
        )


# --- io --------------------------------------------------------------------

def _atomic_write(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".routing.", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _routing_path(handoff_dir: Path) -> Path:
    return handoff_dir / "routing.json"


def _lock_for(target: Path) -> FileLock:
    return FileLock(str(target) + ".lock", timeout=LOCK_TIMEOUT_S)


def _read_source_hash(resolved_path: Path) -> str:
    doc = _read_json(resolved_path)
    sh = doc.get("source_hash")
    if not isinstance(sh, str):
        raise _halt(
            4,
            f"resolved-work-item.json at {resolved_path} has no string source_hash. "
            f"Re-run keel-work-item-resolve.py --v2-schema --output to regenerate it.",
        )
    return sh


# --- mutate-under-lock harness ---------------------------------------------

def _mutate(handoff_dir: Path, transform) -> None:
    """Acquire lock on routing.json, read, transform, validate, atomic-write.

    `transform(state: dict) -> dict` returns the new state. It may raise
    Halt for operation-specific rejections (e.g. escalation budget).
    """
    routing_path = _routing_path(handoff_dir)
    if not routing_path.exists():
        raise _halt(
            4,
            f"routing.json not found at {routing_path}. "
            f"Run `keel-routing.py init {handoff_dir} ...` before any other "
            f"routing command.",
        )
    try:
        with _lock_for(routing_path):
            state = _read_json(routing_path)
            new_state = transform(state)
            _validate(new_state)
            _atomic_write(routing_path, new_state)
    except Timeout as exc:
        raise _halt(
            2,
            f"could not acquire lock on {routing_path} within {LOCK_TIMEOUT_S}s "
            f"({exc}). Another keel-routing.py write is in progress; retry once "
            f"it completes, or remove a stale {routing_path}.lock if no writer "
            f"is running.",
        )


# --- init ------------------------------------------------------------------

def _build_fresh(args, new_source_hash: str | None) -> dict:
    state: dict = {
        "schema_version": 5,
        "work_item": {"id": args.feature, "slug": args.slug},
        "status": "IN-PROGRESS",
        "pipeline": args.pipeline,
        "binder_ref": args.binder,
        "branch": {
            "parent_branch": args.parent_branch,
            "parent_sha": args.parent_sha,
        },
        "review_panel": args.review_panel,
        "precheck_escalation_count": 0,
    }
    if args.pipeline == "bootstrap":
        state["bootstrap_agent"] = args.bootstrap_agent
    else:
        # REQUIRED for non-bootstrap (schema allOf) — load-bearing write-back.
        state["source_hash"] = new_source_hash
        # The schema also REQUIRES the routing block for non-bootstrap, and
        # `init` schema-validates its own output (design §"First-write of
        # routing.json"). The pre-check (Step 1) is the authoritative writer
        # of these flags via `set-routing`, which ALWAYS runs before any
        # consumer reads routing.routing.*; this neutral placeholder only
        # exists to keep init's output schema-valid in the gap between
        # Step 0 (init) and Step 1 (pre-check). Not a P4 cache — it is a
        # required-shape field pending its authoritative writer (cf. a required-shape scalar).
        state["routing"] = {
            "intent": "build",
            "complexity": "standard",
            "designer_needed": False,
            "researcher_needed": False,
            "safety_auditor_needed": False,
            "arch_advisor_needed": False,
            "implementer_needed": False,
        }
    return state


def _safe_merge(existing: dict, args, new_source_hash: str | None) -> dict:
    """Re-seed identity fields from args; preserve status + derived state."""
    state = _build_fresh(args, new_source_hash)
    # Preserve everything derived from the prior run.
    state["status"] = existing.get("status", "IN-PROGRESS")
    state["precheck_escalation_count"] = existing.get("precheck_escalation_count", 0)
    for key in DERIVED_KEYS:
        if key in existing:
            state[key] = existing[key]
    if "routing" in existing:
        state["routing"] = existing["routing"]
    if "pretriage" in existing:
        state["pretriage"] = existing["pretriage"]
    return state


def _wipe_derived_files(handoff_dir: Path) -> None:
    """Delete all derived state: agent .md files + deliberation subdirs.

    Preserve only routing.json (about to be overwritten) and
    resolved-work-item.json (the source of the new identity), plus any
    dotfiles.
    """
    preserve = {"routing.json", "resolved-work-item.json"}
    for child in handoff_dir.iterdir():
        if child.name in preserve or child.name.startswith("."):
            continue
        if child.is_file():
            child.unlink()
        elif child.is_dir():
            shutil.rmtree(child)


def _emit_invalidation_notice(routing_path: Path, old_hash: str | None, new_hash: str | None) -> None:
    print(
        f"init: source_hash changed for {routing_path.parent} "
        f"(was {old_hash}, now {new_hash}). Derived state and stale physical "
        f"files have been wiped; status reset to IN-PROGRESS. The pipeline "
        f"will re-run all gates against the new source.",
        file=sys.stderr,
    )


def cmd_init(args) -> None:
    handoff_dir = Path(args.handoff_dir)
    handoff_dir.mkdir(parents=True, exist_ok=True)
    routing_path = _routing_path(handoff_dir)

    is_bootstrap = args.pipeline == "bootstrap"

    if not is_bootstrap and args.binder is None:
        raise _halt(
            4,
            "init: --binder is required for non-bootstrap pipelines. The handoff "
            "validator recomputes source_hash from routing.binder_ref, so a null "
            "ref reads an empty Binder slice and guarantees a permanent source_hash "
            "mismatch HALT on every validation. Pass the same Binder ref you gave "
            "keel-work-item-resolve.py (e.g. "
            "docs/exec-plans/binders/<slug>.json#WI##) and re-run init.",
        )

    new_source_hash: str | None = None
    if is_bootstrap:
        if not args.bootstrap_agent:
            raise _halt(
                4,
                "init: --bootstrap-agent is required for pipeline=bootstrap "
                "(one of scaffolder, config-writer). Pass the "
                "agent named in the backlog Agent: field and re-run.",
            )
    else:
        resolved_path = (
            handoff_dir / "resolved-work-item.json"
            if args.pretriage_from is None
            else Path(args.pretriage_from)
        )
        if not resolved_path.exists():
            raise _halt(
                4,
                f"init: resolved-work-item.json not found at {resolved_path}. "
                f"Run keel-work-item-resolve.py --v2-schema --output "
                f"{resolved_path} first, then re-run init.",
            )
        new_source_hash = _read_source_hash(resolved_path)

    try:
        with _lock_for(routing_path):
            if not routing_path.exists():
                state = _build_fresh(args, new_source_hash)
            else:
                existing = _read_json(routing_path)
                old_source_hash = existing.get("source_hash")
                if is_bootstrap or old_source_hash == new_source_hash:
                    state = _safe_merge(existing, args, new_source_hash)
                else:
                    state = _build_fresh(args, new_source_hash)
                    _wipe_derived_files(handoff_dir)
                    _emit_invalidation_notice(routing_path, old_source_hash, new_source_hash)
            _validate(state)
            _atomic_write(routing_path, state)
    except Timeout as exc:
        raise _halt(
            2,
            f"could not acquire lock on {routing_path} within {LOCK_TIMEOUT_S}s "
            f"({exc}). Another keel-routing.py write is in progress; retry once "
            f"it completes.",
        )


# --- simple field setters --------------------------------------------------

def cmd_set_status(args) -> None:
    def t(state: dict) -> dict:
        state["status"] = args.status
        return state
    _mutate(Path(args.handoff_dir), t)


def cmd_set_branch(args) -> None:
    def t(state: dict) -> dict:
        branch = state.setdefault("branch", {})
        if args.parent_branch is not None:
            branch["parent_branch"] = args.parent_branch
        if args.parent_sha is not None:
            branch["parent_sha"] = args.parent_sha
        return state
    _mutate(Path(args.handoff_dir), t)


def cmd_set_pretriage(args) -> None:
    def t(state: dict) -> dict:
        state["pretriage"] = {
            "recommended_model": args.model,
            "score": args.score,
            "reason": args.reason,
        }
        return state
    _mutate(Path(args.handoff_dir), t)


def cmd_set_doc_garden(args) -> None:
    def t(state: dict) -> dict:
        state["doc_garden"] = {"verdict": args.verdict, "drift_count": args.drift_count}
        return state
    _mutate(Path(args.handoff_dir), t)


# --- routing block ---------------------------------------------------------

def _coerce_flag(key: str, raw: str) -> bool | str:
    if key in ROUTING_BOOL_FLAGS:
        low = raw.strip().lower()
        if low in ("true", "1", "yes"):
            return True
        if low in ("false", "0", "no"):
            return False
        raise _halt(4, f"merge-routing-flag: {key} expects a boolean, got '{raw}'.")
    if key in ROUTING_ENUM_FLAGS:
        return raw
    raise _halt(
        4,
        f"merge-routing-flag: unknown routing key '{key}'. Valid keys: "
        f"{', '.join(ROUTING_ENUM_FLAGS + ROUTING_BOOL_FLAGS)}.",
    )


def cmd_set_routing(args) -> None:
    if args.from_envelope is None:
        raise _halt(
            4,
            "set-routing: --from-envelope <path-or-dash> is required. Pass a "
            "file path, or '-' to read the routing envelope (YAML) from stdin.",
        )
    if args.from_envelope == "-":
        raw_text = sys.stdin.read()
    else:
        env_path = Path(args.from_envelope)
        if not env_path.exists():
            raise _halt(
                4,
                f"set-routing: envelope file not found at {env_path}. Write the "
                f"pre-check routing envelope (YAML) there, or pass '-' for stdin.",
            )
        raw_text = env_path.read_text(encoding="utf-8")

    try:
        envelope = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        raise _halt(4, f"set-routing: envelope is not valid YAML: {exc}.")
    if not isinstance(envelope, dict):
        raise _halt(
            4,
            "set-routing: envelope must be a YAML mapping of routing fields "
            "(intent, complexity, *_needed). Got a non-mapping document.",
        )

    block = {k: envelope[k] for k in (ROUTING_ENUM_FLAGS + ROUTING_BOOL_FLAGS) if k in envelope}

    # set-routing is a full-block REPLACE: the envelope must carry every
    # required routing field, since merge-time defaults are deliberately
    # absent. Check here (not at schema-validate time) so the operator gets
    # the accurate cause — an incomplete caller envelope — rather than the
    # generic "keel-routing.py bug or corrupted routing.json" message. This
    # halts before the write, so the on-disk routing block is unchanged.
    missing = [k for k in (ROUTING_ENUM_FLAGS + ROUTING_BOOL_FLAGS) if k not in block]
    if missing:
        raise _halt(
            4,
            f"set-routing: envelope is missing required routing field(s): "
            f"{', '.join(missing)}. set-routing is a full-block replace, so the "
            f"pre-check routing envelope MUST contain all of "
            f"{', '.join(ROUTING_ENUM_FLAGS + ROUTING_BOOL_FLAGS)}. Add the "
            f"missing field(s) to the envelope and re-run; routing.json is "
            f"left unchanged.",
        )

    def t(state: dict) -> dict:
        state["routing"] = block  # full-block replace wipes stale fields
        return state
    _mutate(Path(args.handoff_dir), t)


def cmd_merge_routing_flag(args) -> None:
    updates: dict = {}
    for pair in args.pairs:
        if "=" not in pair:
            raise _halt(4, f"merge-routing-flag: expected key=value, got '{pair}'.")
        key, _, value = pair.partition("=")
        updates[key] = _coerce_flag(key, value)

    def t(state: dict) -> dict:
        routing = state.setdefault("routing", {})
        routing.update(updates)
        return state
    _mutate(Path(args.handoff_dir), t)


# --- gates + review --------------------------------------------------------

def cmd_set_gate(args) -> None:
    allowed = GATE_VERDICTS[args.gate]
    if args.verdict not in allowed:
        raise _halt(
            4,
            f"set-gate: '{args.verdict}' is not a valid verdict for gate "
            f"'{args.gate}'. Allowed: {', '.join(allowed)}. Mirror the gate "
            f"agent's file-body **Verdict:** word exactly (a typo would "
            f"otherwise fail schema validation post-write). routing.json is "
            f"left unchanged.",
        )

    def t(state: dict) -> dict:
        gates = state.setdefault("gates", {})
        gates[args.gate] = {"verdict": args.verdict, "attempt": args.attempt}
        return state
    _mutate(Path(args.handoff_dir), t)


def cmd_set_review(args) -> None:
    def t(state: dict) -> dict:
        review = state.setdefault("review", {})
        review[args.touchpoint] = {"verdict": args.verdict, "attempt": args.attempt}
        return state
    _mutate(Path(args.handoff_dir), t)


def cmd_clear_gate(args) -> None:
    def t(state: dict) -> dict:
        gates = state.get("gates", {})
        gates.pop(args.gate, None)
        if not gates:
            state.pop("gates", None)
        return state
    _mutate(Path(args.handoff_dir), t)


def cmd_clear_review(args) -> None:
    def t(state: dict) -> dict:
        review = state.setdefault("review", {})
        review[args.touchpoint] = {"verdict": None, "attempt": 0}
        return state
    _mutate(Path(args.handoff_dir), t)


# --- escalation + derived-state --------------------------------------------

def cmd_incr_escalation(args) -> None:
    def t(state: dict) -> dict:
        current = state.get("precheck_escalation_count", 0)
        if current + 1 > ESCALATION_BUDGET:
            raise _halt(
                3,
                f"incr-escalation: precheck escalation budget exhausted "
                f"(count={current}, budget={ESCALATION_BUDGET}). The pre-check "
                f"has already re-escalated once; halt the pipeline and route to "
                f"a human reviewer instead of re-escalating again.",
            )
        state["precheck_escalation_count"] = current + 1
        return state
    _mutate(Path(args.handoff_dir), t)


def cmd_clear_derived_state(args) -> None:
    """Clear routing-STATE only: gates/review/arch_retry/review_retry/
    doc_garden + reset escalation count + status to IN-PROGRESS.

    Does NOT touch on-disk files. Per the design's route-reset ordering, the
    CALLER must delete the matching stale files FIRST, then clear routing-
    state. (init takes a different path — _build_fresh + _wipe_derived_files —
    and does NOT call this command.)"""
    def t(state: dict) -> dict:
        for key in DERIVED_KEYS:
            state.pop(key, None)
        state["precheck_escalation_count"] = 0
        state["status"] = "IN-PROGRESS"
        return state
    _mutate(Path(args.handoff_dir), t)


# --- attempt-hash sidecar --------------------------------------------------

def cmd_record_attempt_hash(args) -> None:
    handoff_dir = Path(args.handoff_dir)
    review_dir = handoff_dir / f"{args.touchpoint}-review"
    attempt_name = f"attempt-{args.n:02d}.md"
    attempt_path = review_dir / attempt_name
    if not attempt_path.is_file():
        raise _halt(
            4,
            f"record-attempt-hash: {attempt_path} not found. Write the review "
            f"attempt file before recording its hash (touchpoint "
            f"'{args.touchpoint}', attempt {args.n}).",
        )
    digest = hashlib.sha256(attempt_path.read_bytes()).hexdigest()
    sidecar = review_dir / ".attempt-hashes.json"
    try:
        with _lock_for(sidecar):
            data = _read_json(sidecar) if sidecar.exists() else {}
            data[attempt_name] = digest
            _atomic_write(sidecar, data)
    except Timeout as exc:
        raise _halt(
            2,
            f"could not acquire lock on {sidecar} within {LOCK_TIMEOUT_S}s "
            f"({exc}). Another record-attempt-hash write is in progress; retry.",
        )


# --- CLI -------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="keel-routing.py",
        description="Locked, schema-validated routing.json mutations.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="create or safe-merge routing.json")
    p_init.add_argument("handoff_dir")
    p_init.add_argument("--feature", required=True)
    p_init.add_argument("--slug", required=True)
    p_init.add_argument(
        "--pipeline", required=True,
        choices=["bootstrap", "backend", "frontend", "cross-cutting", "karta"],
    )
    p_init.add_argument("--binder", default=None)
    p_init.add_argument(
        "--review-panel", dest="review_panel", default="personas",
        choices=["personas", "roundtable", "none"],
    )
    p_init.add_argument("--pretriage-from", dest="pretriage_from", default=None)
    p_init.add_argument("--parent-branch", dest="parent_branch", default=None)
    p_init.add_argument("--parent-sha", dest="parent_sha", default=None)
    p_init.add_argument(
        "--bootstrap-agent", dest="bootstrap_agent", default=None,
        choices=["scaffolder", "config-writer"],
    )
    p_init.set_defaults(func=cmd_init)

    p_status = sub.add_parser("set-status", help="set top-level status")
    p_status.add_argument("handoff_dir")
    p_status.add_argument(
        "status", choices=["IN-PROGRESS", "BLOCKED"]
    )
    p_status.set_defaults(func=cmd_set_status)

    p_route = sub.add_parser("set-routing", help="full-block replace routing.routing")
    p_route.add_argument("handoff_dir")
    p_route.add_argument(
        "--from-envelope", dest="from_envelope", default=None,
        help="envelope file path, or '-' to read YAML from stdin",
    )
    p_route.set_defaults(func=cmd_set_routing)

    p_merge = sub.add_parser("merge-routing-flag", help="merge single routing fields")
    p_merge.add_argument("handoff_dir")
    p_merge.add_argument("pairs", nargs="+", metavar="key=value")
    p_merge.set_defaults(func=cmd_merge_routing_flag)

    p_gate = sub.add_parser("set-gate", help="set a gate verdict + attempt")
    p_gate.add_argument("handoff_dir")
    p_gate.add_argument("gate", choices=list(GATE_NAMES))
    p_gate.add_argument("verdict")
    p_gate.add_argument("attempt", type=int)
    p_gate.set_defaults(func=cmd_set_gate)

    p_review = sub.add_parser("set-review", help="set a review touchpoint")
    p_review.add_argument("handoff_dir")
    p_review.add_argument("touchpoint", choices=list(REVIEW_TOUCHPOINTS))
    p_review.add_argument("verdict", choices=["APPROVED", "CONCERNS"])
    p_review.add_argument("attempt", type=int)
    p_review.set_defaults(func=cmd_set_review)

    p_pt = sub.add_parser("set-pretriage", help="set the pretriage block")
    p_pt.add_argument("handoff_dir")
    p_pt.add_argument("model", choices=["sonnet", "opus"])
    p_pt.add_argument("--score", type=int, required=True)
    p_pt.add_argument("--reason", required=True)
    p_pt.set_defaults(func=cmd_set_pretriage)

    p_dg = sub.add_parser("set-doc-garden", help="set the doc-garden block")
    p_dg.add_argument("handoff_dir")
    p_dg.add_argument("verdict", choices=["CLEAN", "DRIFT_FOUND"])
    p_dg.add_argument("drift_count", type=int)
    p_dg.set_defaults(func=cmd_set_doc_garden)

    p_branch = sub.add_parser("set-branch", help="set branch parent fields")
    p_branch.add_argument("handoff_dir")
    p_branch.add_argument("--parent-branch", dest="parent_branch", default=None)
    p_branch.add_argument("--parent-sha", dest="parent_sha", default=None)
    p_branch.set_defaults(func=cmd_set_branch)

    p_incr = sub.add_parser("incr-escalation", help="increment escalation count")
    p_incr.add_argument("handoff_dir")
    p_incr.set_defaults(func=cmd_incr_escalation)

    p_clear = sub.add_parser("clear-derived-state", help="wipe derived state")
    p_clear.add_argument("handoff_dir")
    p_clear.set_defaults(func=cmd_clear_derived_state)

    p_cg = sub.add_parser("clear-gate", help="delete a gate")
    p_cg.add_argument("handoff_dir")
    p_cg.add_argument("gate", choices=list(GATE_NAMES))
    p_cg.set_defaults(func=cmd_clear_gate)

    p_cr = sub.add_parser("clear-review", help="reset a review touchpoint")
    p_cr.add_argument("handoff_dir")
    p_cr.add_argument("touchpoint", choices=list(REVIEW_TOUCHPOINTS))
    p_cr.set_defaults(func=cmd_clear_review)

    p_hash = sub.add_parser("record-attempt-hash", help="hash an attempt file into the sidecar")
    p_hash.add_argument("handoff_dir")
    p_hash.add_argument("touchpoint", choices=list(REVIEW_TOUCHPOINTS))
    p_hash.add_argument("n", type=int)
    p_hash.set_defaults(func=cmd_record_attempt_hash)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except Halt as halt:
        print(f"halt: {halt.message}", file=sys.stderr)
        return halt.code
    return 0


if __name__ == "__main__":
    sys.exit(main())
