#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["jsonschema>=4.25"]
# ///
"""Resolve a feature's invariant-7 classification, Binder, and per-feature
content in ONE deterministic call.

Replaces ~15 steps of prose-described work across `.claude/agents/pre-check.md`
and `.claude/skills/keel-refine/SKILL.md` with a single invocation that
emits structured JSON on stdout (success) or a P7 CTA on stderr (halt).

Typical invocation from an agent prompt:

    uv run scripts/keel-work-item-resolve.py \\
      --backlog docs/exec-plans/active/backlog.md \\
      --feature WI04 \\
      --binder docs/exec-plans/binders/my-feature.json

Exit codes encode halt class; see `HaltCode` in `scripts/keel_work_items.py`.

On exit 0, stdout is a JSON document with the fields every downstream agent
needs: `feature_index`, `feature_pointer_base`, `oracle`, `contract`,
`needs`, `layer`, `title`, `binder_invariants_exercised`, `backlog_fields`,
`classification`. Agents carry these verbatim in the handoff brief.

On any non-zero exit, stderr is a human-readable P7 halt message with
specific cause + concrete fix.

Usage:
    uv run scripts/keel-work-item-resolve.py --backlog <path> --feature WI## \\
        [--binder <binder-path>] [--repo <repo-root>]

`--v2-schema --output <path>` switches to Option H mode: instead of the
legacy JSON on stdout, the script writes a
`schemas/resolved-work-item.schema.json` conformant document (carrying
`source_hash` + `pretriage_inputs`) atomically to <path>. The default
stdout path is byte-identical to today's so the legacy pipeline keeps
working.

See docs/design-docs/2026-04-24-structured-prds.md (direction),
`.claude/agents/pre-check.md` (primary caller),
and `scripts/keel_work_items.py` (domain logic)."""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
import tempfile
from pathlib import Path

# Path-anchored import of the helper module (scripts/ ships as standalone
# files, not a Python package; see AGENTS.md §Python conventions).
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from jsonschema import Draft202012Validator  # noqa: E402

from keel_work_items import (  # noqa: E402
    BacklogEntry,
    BacklogParser,
    FeatureResolver,
    FeatureResolution,
    FileBacklogSource,
    FileBinderJsonSource,
    Halt,
    HaltCode,
    Invariant7Classifier,
    ResolveRequest,
    backlog_entry_to_canonical_dict,
    compute_source_hash,
    extract_binder_slice,
    load_schema,
    map_binder_layer,
    parse_complexity_hint,
    parse_structured_dependencies,
    parse_structured_frozen_seams,
    binder_invariant_ids,
    slugify,
)

# Constant: where the project-root security config lives. Optional file;
# absent → empty security list (projects opt in). See schemas/keel.schema.json
# and the design doc's "New structured contracts" section.
_KEEL_JSON_REL = Path("keel.json")
_KEEL_SCHEMA_REL = Path("schemas") / "keel.schema.json"
_RESOLVED_WORK_ITEM_SCHEMA_REL = Path("schemas") / "resolved-work-item.schema.json"
_RESOLVED_WORK_ITEM_SCHEMA_VERSION = 6


def _render_halt(halt: Halt) -> str:
    """Halts always render in human form on stderr. The message itself
    is the P7 CTA; wrapping it in a JSON envelope would defeat verbatim
    emission upstream (agents forward stderr directly)."""
    return (
        f"halt: [{halt.code.name}] {halt.message}\n\n"
        f"Exit code: {halt.code.value}"
    )


def _render_resolution_json(resolution: FeatureResolution) -> str:
    payload = {"ok": True, **dataclasses.asdict(resolution)}
    return json.dumps(payload, indent=2, sort_keys=False)


# --- v2 (resolved-work-item.json) mode helpers -------------------------------


def _read_keel_security_list(repo_root: Path) -> list[str]:
    """Load `keel.json:.security_sensitive_invariants` from the repo root.

    Returns [] when keel.json is absent (the common case — projects opt
    in). When present, the file is schema-validated against
    schemas/keel.schema.json; a malformed keel.json is a hard error (the
    caller turns the raised ValueError into a P7 INVOCATION halt) rather
    than silently degrading the security signal."""
    keel_path = repo_root / _KEEL_JSON_REL
    if not keel_path.is_file():
        return []
    try:
        doc = json.loads(keel_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"keel.json is not readable UTF-8 JSON: {e}") from e
    schema_path = repo_root / _KEEL_SCHEMA_REL
    if schema_path.is_file():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        errors = sorted(
            Draft202012Validator(schema).iter_errors(doc),
            key=lambda err: list(err.absolute_path),
        )
        if errors:
            joined = "; ".join(
                f"{'/' + '/'.join(str(p) for p in e.absolute_path)}: "
                f"{e.message.splitlines()[0]}"
                for e in errors
            )
            raise ValueError(f"keel.json failed schema validation: {joined}")
    sec = doc.get("security_sensitive_invariants", [])
    return list(sec) if isinstance(sec, list) else []


def _classify_dependencies(binder_needs: list[str]) -> dict:
    """Split a feature's dependencies into intra_binder and cross_binder.

    The resolver is deterministic and has NO git/branch knowledge, so every
    dependency status is `unknown` at resolve time — downstream tooling
    (which CAN see branch state) refines it.

    - `intra_binder`: the Binder feature's own `needs[]` — these always resolve
      to features in the same Binder (the Binder xref validator already
      guaranteed this upstream).
    - `cross_binder`: empty in PR A. A cross-Binder edge requires a `binder_ref`
      (the OTHER Binder's path), which the deterministic resolver cannot know
      from prose `Needs:` alone. The structured backlog `dependencies[]`
      field (PR B) is the future source; until it carries binder_ref, the
      resolver does not fabricate cross-Binder edges with a guessed binder_ref.
      The `cross_module_touch` signal therefore keys on `layer ==
      cross-cutting` (reliable) rather than on a fabricated cross_binder.
    """
    intra = [{"id": nid, "status": "unknown"} for nid in binder_needs]
    return {"intra_binder": intra, "cross_binder": []}


def _compute_pretriage_inputs(
    *,
    resolved_layer: str,
    cross_binder: list,
    invariant_ids: list[str],
    security_list: list[str],
    structured_deps: list[dict] | None,
    structured_frozen_seams: list[dict] | None,
    needs_ids: list[str],
    complexity_hint: str | None,
) -> dict:
    """All five pretriage signals, computed from STRUCTURED inputs only.

    Mirrors the design doc's signal table. The pretriage OUTCOME
    (recommended_model / score / reason) is NOT computed here — it is
    derived later by keel-routing.py init from these inputs (P4: outcome
    lives in routing.json, raw inputs live in resolved-work-item.json)."""
    # cross_module_touch: cross-cutting layer OR a cross-Binder edge.
    cross_module_touch = resolved_layer == "cross-cutting" or len(cross_binder) > 0

    # security_sensitive_inv: any Binder invariant in the keel.json security set.
    security_sensitive_inv = bool(set(security_list) & set(invariant_ids))

    # novel_dependency: any structured library/protocol/prototype dep marked
    # novel. FAIL-SAFE to True when the structured `dependencies:` field is
    # absent (the universal pre-PR-B case) — a missing signal must escalate,
    # never silently clear.
    if structured_deps is None:
        novel_dependency = True
    else:
        novel_dependency = any(
            dep.get("kind") in ("library", "protocol", "prototype")
            and dep.get("novel") is True
            for dep in structured_deps
        )

    # frozen_seam_impact: any structured frozen_seams entry references a
    # feature in this feature's Needs: line. Absent field → False (a frozen
    # seam the backlog never recorded is not an impact we can assert).
    needs_set = set(needs_ids)
    if structured_frozen_seams is None:
        frozen_seam_impact = False
    else:
        frozen_seam_impact = any(
            seam.get("referenced_in") in needs_set
            for seam in structured_frozen_seams
        )

    architecture_tier_hint = complexity_hint == "architecture-tier"

    return {
        "cross_module_touch": cross_module_touch,
        "security_sensitive_inv": security_sensitive_inv,
        "novel_dependency": novel_dependency,
        "frozen_seam_impact": frozen_seam_impact,
        "architecture_tier_hint": architecture_tier_hint,
    }


def _build_v2_shape(
    resolution: FeatureResolution,
    entry: BacklogEntry,
    binder_doc: dict,
    security_list: list[str],
) -> dict:
    """Reshape a FeatureResolution into a resolved-work-item.schema.json doc.

    Reads the verbatim Binder slice + structured backlog fields; computes the
    source_hash and pretriage_inputs. Does NOT validate or write — the
    caller does both."""
    feature_id = resolution.feature_id
    binder_slice = extract_binder_slice(binder_doc, feature_id)
    resolved_layer = map_binder_layer(resolution.layer)
    invariant_ids = binder_invariant_ids(resolution.binder_invariants_exercised)
    complexity_hint = parse_complexity_hint(entry.raw_block)

    dependencies = _classify_dependencies(resolution.needs)

    structured_deps = parse_structured_dependencies(entry.raw_block)
    structured_frozen_seams = parse_structured_frozen_seams(entry.raw_block)

    source_hash = compute_source_hash(
        binder_slice,
        backlog_entry_to_canonical_dict(entry),
        security_list,
    )

    pretriage_inputs = _compute_pretriage_inputs(
        resolved_layer=resolved_layer,
        cross_binder=dependencies["cross_binder"],
        invariant_ids=invariant_ids,
        security_list=security_list,
        structured_deps=structured_deps,
        structured_frozen_seams=structured_frozen_seams,
        needs_ids=list(entry.needs_ids),
        complexity_hint=complexity_hint,
    )

    test_tooling: dict = {
        "type": resolution.oracle.get("type"),
    }
    if "tooling" in resolution.oracle and resolution.oracle["tooling"]:
        test_tooling["tooling"] = resolution.oracle["tooling"]

    out: dict = {
        "schema_version": _RESOLVED_WORK_ITEM_SCHEMA_VERSION,
        "source_hash": source_hash,
        "work_item": {
            "id": feature_id,
            "slug": slugify(resolution.title),
            "title": resolution.title,
            "layer": resolved_layer,
            "index": resolution.feature_index,
            "pointer_base": resolution.feature_pointer_base,
            "complexity_hint": complexity_hint,
        },
        "binder": {
            "path": resolution.binder_path,
            "slice": binder_slice,
            "invariants_exercised": invariant_ids,
            "prototype_mode": entry.prototype_mode,
        },
        "dependencies": dependencies,
        "test_tooling": test_tooling,
        "pretriage_inputs": pretriage_inputs,
    }
    # design_refs: a declared Step-0 fact from the backlog entry. Emit only
    # when the entry has them (mirrors the conditional `test_tooling.tooling`
    # above). Production/test file paths are NOT emitted: those are decided
    # during implementation, not knowable by the resolver at Step 0.
    if entry.design_refs:
        out["design_refs"] = list(entry.design_refs)
    return out


def _atomic_write_json(path: Path, doc: dict) -> None:
    """Write `doc` as pretty JSON to `path` atomically (tmp + os.replace).

    Creates parent dirs. The temp file is created in the destination
    directory so os.replace is a same-filesystem atomic rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, sort_keys=False)
            f.write("\n")
        os.replace(tmp_name, path)
    except BaseException:
        # Clean up the temp file on any failure so we don't leave a stray.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _emit_v2(
    args: argparse.Namespace,
    resolution: FeatureResolution,
    backlog_text: str,
    binder_doc: dict,
    repo_root: Path,
) -> int:
    """v2 path: build, schema-validate, and atomically write
    resolved-work-item.json. Returns an exit code (OK or a halt code)."""
    # Re-parse the backlog entry for the structured fields (the resolver's
    # FeatureResolution flattens backlog_fields into a dict but does not
    # carry the raw block needed for source_hash + structured-field parse).
    parse_result = BacklogParser().parse_entry(backlog_text, resolution.feature_id)
    if isinstance(parse_result, Halt):
        print(_render_halt(parse_result), file=sys.stderr)
        return parse_result.code.value
    if parse_result is None:  # unreachable: resolve() already found it
        print(
            f"halt: [FEATURE_NOT_IN_BACKLOG] {resolution.feature_id} vanished "
            f"from backlog between resolve and v2 emit. Fix: re-run Step 0.",
            file=sys.stderr,
        )
        return HaltCode.FEATURE_NOT_IN_BACKLOG.value
    entry = parse_result

    try:
        security_list = _read_keel_security_list(repo_root)
    except ValueError as e:
        print(
            f"halt: [INVOCATION] {e}\n\n"
            f"Fix: repair keel.json (it must validate against "
            f"schemas/keel.schema.json), or remove it to fall back to an "
            f"empty security list.",
            file=sys.stderr,
        )
        return HaltCode.INVOCATION.value

    out = _build_v2_shape(resolution, entry, binder_doc, security_list)

    schema_path = repo_root / _RESOLVED_WORK_ITEM_SCHEMA_REL
    if not schema_path.is_file():
        print(
            f"halt: [INVOCATION] resolved-work-item schema not found at "
            f"{schema_path}.\n\nFix: invoke from the repo root (where "
            f"schemas/ lives), or pass --repo. The schema ships with KEEL — "
            f"reinstall if it is missing.",
            file=sys.stderr,
        )
        return HaltCode.INVOCATION.value
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(out),
        key=lambda e: list(e.absolute_path),
    )
    if errors:
        lines = ["halt: [INVOCATION] resolved-work-item output failed schema validation:"]
        for err in errors:
            ptr = "/" + "/".join(str(p) for p in err.absolute_path)
            lines.append(f"  {ptr}: {err.message.splitlines()[0]}")
        lines.append(
            "\nFix: this is a resolver bug (the script produced output that "
            "violates schemas/resolved-work-item.schema.json). File it against "
            "keel-work-item-resolve.py; do not hand-edit the output."
        )
        print("\n".join(lines), file=sys.stderr)
        return HaltCode.INVOCATION.value

    _atomic_write_json(args.output, out)
    print(
        f"wrote {args.output} ({out['source_hash'][:12]})",
        file=sys.stderr,
    )
    return HaltCode.OK.value


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve a feature's invariant-7 classification, Binder, and "
            "per-feature content in one call."
        )
    )
    parser.add_argument(
        "--backlog",
        type=Path,
        required=True,
        help="Path to the backlog file (e.g. docs/exec-plans/active/backlog.md).",
    )
    parser.add_argument(
        "--feature",
        required=True,
        help="Feature ID, e.g. WI04.",
    )
    parser.add_argument(
        "--binder",
        type=Path,
        default=None,
        help=(
            "Path supplied by the caller (e.g. the /keel-pipeline argument). "
            "If omitted, the canonical path is derived from the backlog's "
            "Binder: slug."
        ),
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Repo root (default: cwd). Design refs and canonical Binder paths resolve against this.",
    )
    parser.add_argument(
        "--v2-schema",
        action="store_true",
        help=(
            "Emit a schemas/resolved-work-item.schema.json conformant document "
            "(with source_hash + pretriage_inputs) to --output instead of the "
            "legacy JSON on stdout. Requires --output."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write output to this path (atomic). Required with --v2-schema.",
    )
    args = parser.parse_args()

    # P7: name the cause + concrete fix. --v2-schema has no useful behavior
    # without a destination, and we never overwrite stdout in v2 mode.
    if args.v2_schema and args.output is None:
        print(
            "halt: [INVOCATION] --v2-schema requires --output.\n\n"
            "Fix: pass --output <path> (e.g. "
            "--output docs/exec-plans/active/handoffs/WI##-<slug>/resolved-work-item.json).",
            file=sys.stderr,
        )
        return HaltCode.INVOCATION.value

    # Validate --feature format at the CLI boundary so malformed input
    # routes to INVOCATION, not FEATURE_NOT_IN_BACKLOG.
    if not re.fullmatch(r"WI\d{2,}", args.feature):
        print(
            f"halt: [INVOCATION] --feature must match `WI\\d{{2,}}` (e.g. WI04). "
            f"Got: {args.feature!r}. Fix: pass the feature ID with a "
            f"`WI` prefix and at least two digits.",
            file=sys.stderr,
        )
        return HaltCode.INVOCATION.value

    try:
        schema = load_schema(args.repo)
    except (OSError, ValueError) as e:
        # OSError covers FileNotFoundError + PermissionError; ValueError
        # covers json.JSONDecodeError (subclass) if the schema file
        # exists but is corrupt. All route to INVOCATION so the caller
        # fixes the invocation or the schema file itself.
        print(
            f"halt: [INVOCATION] {e}\n\n"
            f"Fix: invoke from the repo root (where `schemas/binder.schema.json` "
            f"lives), or pass `--repo <path-to-repo-root>`. If the schema "
            f"file exists but is unreadable/corrupt, repair it (it ships "
            f"with KEEL — reinstall if needed).",
            file=sys.stderr,
        )
        return HaltCode.INVOCATION.value

    resolver = FeatureResolver(
        backlog_parser=BacklogParser(),
        classifier=Invariant7Classifier(),
        binder_source=FileBinderJsonSource(repo_root=args.repo),
        schema=schema,
    )

    backlog_source = FileBacklogSource(backlog_path=args.backlog)
    request = ResolveRequest(
        repo_root=args.repo,
        backlog_path=args.backlog,
        feature_id=args.feature,
        supplied_binder_path=args.binder,
    )

    result = resolver.resolve(request, backlog_source)

    if isinstance(result, Halt):
        print(_render_halt(result), file=sys.stderr)
        return result.code.value

    if args.v2_schema:
        # v2 mode: reshape into resolved-work-item.json and write atomically.
        # The legacy stdout path below is untouched (byte-equivalence).
        backlog_text = backlog_source.read()
        try:
            binder_doc = json.loads(
                Path(result.canonical_binder_path).read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
            # resolve() already read+validated this file, so a failure here
            # means it changed underfoot between resolve and re-read.
            print(
                f"halt: [BINDER_SCHEMA_INVALID] Binder at {result.canonical_binder_path} "
                f"became unreadable after resolution: {e}. Fix: re-run Step 0.",
                file=sys.stderr,
            )
            return HaltCode.BINDER_SCHEMA_INVALID.value
        return _emit_v2(args, result, backlog_text, binder_doc, args.repo)

    print(_render_resolution_json(result))
    return HaltCode.OK.value


if __name__ == "__main__":
    sys.exit(main())
