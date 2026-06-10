"""Domain logic for feature resolution: backlog parse, invariant 7 classify,
Binder JSON read, feature extraction, JSON Pointer escaping.

Imported by scripts/keel-work-item-resolve.py (CLI). Not a bootstrap module.

Design (SOLID):
- Single responsibility per class. Narrow interfaces (Protocols).
- Readers (BacklogSource, BinderJsonSource) separate from classifiers
  (Invariant7Classifier) separate from orchestrator (FeatureResolver).
- Open to extension (new classifier implementations) closed to modification.
- Main CLI depends on abstractions (Protocols + dataclasses), not on
  file-system specifics; tests substitute in-memory sources.

Declared-external deps: `jsonschema` (for structural Binder validation).
The CLI script carries the PEP 723 metadata; this module is imported.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Literal, Protocol, TypedDict

from jsonschema import Draft202012Validator

# --- Constants --------------------------------------------------------------

CANONICAL_BINDER_DIR = Path("docs") / "exec-plans" / "binders"
ALLOWED_EXEMPT_REASONS = frozenset({"legacy", "bootstrap", "infra", "trivial"})
SCHEMA_REL = Path("schemas") / "binder.schema.json"

# Grandfather marker on the backlog preamble. Matches:
#   <!-- KEEL-INVARIANT-7: legacy-through=WI<N> -->
_GRANDFATHER_RE = re.compile(
    r"<!--\s*KEEL-INVARIANT-7:\s*legacy-through=WI(\d+)\s*-->"
)

# Backlog entry field extractors — each pattern matches its field name
# either at start-of-line OR after a pipe, to support KEEL's canonical
# inline format (e.g. `Spec: <path> | Needs: WI02, WI03`). Values end at
# the next pipe or end-of-line, whichever comes first.
#
# Example canonical entry (from /keel-refine output):
#   - [ ] **WI02 Feature title**
#     Spec: path#anchor | Needs: WI01
#     Binder: some-slug
_BINDER_RE = re.compile(
    r"(?:^|\|)\s*Binder:\s*([a-z0-9](?:[a-z0-9-]*[a-z0-9])?)\s*(?=\||$)",
    re.MULTILINE,
)
_BINDER_EXEMPT_RE = re.compile(
    r"(?:^|\|)\s*Binder-exempt:\s*(\S+?)\s*(?=\||$)",
    re.MULTILINE,
)
_SPEC_RE = re.compile(
    r"(?:^|\|)\s*Spec:\s*([^|\n]+?)\s*(?=\||$)",
    re.MULTILINE,
)
_DESIGN_RE = re.compile(
    r"(?:^|\|)\s*Design:\s*([^|\n]+?)\s*(?=\||$)",
    re.MULTILINE,
)
# Optional disposition marker prefixed to the Design: content when one or
# more listed paths point at a working-prototype directory under
# `<slug>/prototype/`. Examples:
#     Design: [prototype:reference] docs/exec-plans/binders/auth/prototype/index.html
#     Design: [prototype:seed] foo.html, bar.html
# The marker is parsed-and-stripped here so design-ref validation
# (Stage 6) sees only paths. Disposition is propagated to the brief
# as `backlog_fields.prototype_mode` so frontend-designer reads
# disposition without re-parsing the manifest at prototype/prototype.json.
_PROTOTYPE_MARKER_RE = re.compile(r"^\[prototype:(reference|seed)\]\s*")
_NEEDS_RE = re.compile(
    r"(?:^|\|)\s*Needs:\s*([^|\n]+?)\s*(?=\||$)",
    re.MULTILINE,
)
# Optional per-feature review-panel override. Selects which review panel
# serves this feature's three pipeline touchpoints, overriding the
# project default (`Review panel:` in the project guide). Examples:
#     Review: roundtable
#     Spec: path#anchor | Needs: WI01 | Review: personas
# Surfaced to the orchestrator as `backlog_fields.review_panel`; the
# pipeline writes it into the handoff's `review_panel` YAML at Step 0.5.
_REVIEW_RE = re.compile(
    r"(?:^|\|)\s*Review:\s*([^|\n]+?)\s*(?=\||$)",
    re.MULTILINE,
)
_VALID_REVIEW_PANELS = ("personas", "roundtable")
_HUMAN_MARKER_RE = re.compile(r"<!--\s*HUMAN:\s*(.+?)\s*-->")


# --- Halt codes -------------------------------------------------------------

class HaltCode(int, Enum):
    """Exit codes the CLI returns. Encode the halt class so the invoker
    can route without parsing the stderr text.

    Stable integers — never reassign; add new codes at the end."""
    OK = 0
    INVOCATION = 2            # bad CLI args, missing file, unreadable
    BACKLOG_NOT_FOUND = 3
    FEATURE_NOT_IN_BACKLOG = 4
    HUMAN_MARKER_UNRESOLVED = 5
    INVARIANT7_XOR = 6        # both Binder: and Binder-exempt:
    INVARIANT7_MULTIPLICITY = 7  # multiple Binder: or multiple Binder-exempt:
    INVARIANT7_EXEMPT_REASON = 8
    INVARIANT7_VIOLATION = 9    # post-cutoff, missing both
    BINDER_EXEMPT_NOT_PIPELINE = 10
    BINDER_GRANDFATHERED_NO_LINK = 11
    BINDER_FORMAT_NOT_JSON = 12
    BINDER_PATH_MISMATCH = 13    # supplied != canonical
    BINDER_FILE_MISSING = 14
    BINDER_SCHEMA_INVALID = 15
    BINDER_SLUG_ID_MISMATCH = 16
    FEATURE_NOT_IN_BINDER = 17
    FEATURE_DUPLICATE_IN_BINDER = 18
    DESIGN_REF_INVALID = 19
    FEATURE_DUPLICATE_IN_BACKLOG = 20  # backlog has >1 entries for same WI##
    REVIEW_PANEL_INVALID = 21  # `Review:` value not in {personas, roundtable}


class Classification(str, Enum):
    """Invariant 7 classification outcome. JSON_BINDER_PATH is the only
    pipeline-eligible state; all others halt with a specific code."""
    JSON_BINDER_PATH = "JSON_BINDER_PATH"
    EXEMPT = "EXEMPT"
    GRANDFATHERED_NO_LINK = "GRANDFATHERED_NO_LINK"
    PREADOPTION_NO_LINK = "PREADOPTION_NO_LINK"
    VIOLATION = "VIOLATION"
    XOR_CONFLICT = "XOR_CONFLICT"
    MULTIPLICITY_CONFLICT = "MULTIPLICITY_CONFLICT"


# --- Typed records ----------------------------------------------------------

class Oracle(TypedDict, total=False):
    """Mirrors schema v1 oracle shape. Fields vary in nullability per schema."""
    type: str
    setup: str | None
    actions: list[str]
    assertions: list[str]
    tooling: str
    gating: str


class InvariantRef(TypedDict):
    invariant_id: str
    name: str
    how_exercised: str


@dataclass(slots=True, frozen=True)
class BacklogEntry:
    """Parsed backlog entry for one WI## feature."""
    feature_id: str         # e.g. "WI04"
    feature_id_num: int     # e.g. 4
    binder_slugs: tuple[str, ...]
    binder_exempt_reasons: tuple[str, ...]
    spec_ref: str | None
    design_refs: tuple[str, ...]
    needs_ids: tuple[str, ...]
    human_markers: tuple[str, ...]
    prototype_mode: str | None  # "reference" | "seed" | None (no marker)
    review_panel: str | None  # "personas" | "roundtable" | None (no override)
    raw_block: str          # the raw text block this entry came from


@dataclass(slots=True, frozen=True)
class ClassificationResult:
    classification: Classification
    halt_code: HaltCode
    halt_message: str | None   # None when classification is JSON_BINDER_PATH


@dataclass(slots=True, frozen=True)
class Halt:
    """A non-OK outcome. Encapsulates exit code + human-readable CTA."""
    code: HaltCode
    message: str


@dataclass(slots=True, frozen=True)
class FeatureResolution:
    """Successful pipeline-ready resolution of a feature.

    Emitted as stdout JSON on exit code 0.

    Note on `binder_invariants_exercised`: this is the Binder-level
    `invariants_exercised` array carried verbatim from the Binder root
    (schemas/binder.schema.json places this field at the Binder level, not
    per-feature). Consumers that need to decide *which features* are
    exercising which invariants must inspect the contract/oracle of
    the specific feature, not treat this array as a per-feature claim.
    Named with the `binder_` prefix to prevent that misreading downstream.
    """
    feature_id: str
    feature_index: int
    feature_pointer_base: str
    binder_path: str
    canonical_binder_path: str
    title: str
    layer: str
    oracle: dict
    contract: dict
    needs: list[str]
    binder_invariants_exercised: list[dict]
    backlog_fields: dict
    classification: str


# --- Protocols (Interface Segregation) --------------------------------------

class BacklogSource(Protocol):
    """Narrow interface: read backlog text + parse into entries.

    `grandfather_cutoff` takes the already-read text so callers don't
    pay a second disk round-trip per resolve() call."""
    def read(self) -> str: ...
    def grandfather_cutoff(self, text: str) -> int | None: ...


class BinderJsonSource(Protocol):
    """Narrow interface: read a single Binder JSON file + normalize path."""
    def canonical_path(self, slug: str) -> Path: ...
    def read_json(self, path: Path) -> dict: ...
    def exists(self, path: Path) -> bool: ...
    def resolve(self, path: Path) -> Path: ...


# --- Concrete file-backed sources ------------------------------------------

@dataclass(slots=True, frozen=True)
class FileBacklogSource:
    """BacklogSource backed by a filesystem path."""
    backlog_path: Path

    def read(self) -> str:
        return self.backlog_path.read_text(encoding="utf-8")

    def grandfather_cutoff(self, text: str) -> int | None:
        match = _GRANDFATHER_RE.search(text)
        return int(match.group(1)) if match else None


@dataclass(slots=True, frozen=True)
class FileBinderJsonSource:
    """BinderJsonSource backed by the filesystem at repo_root/<CANONICAL_BINDER_DIR>."""
    repo_root: Path

    def canonical_path(self, slug: str) -> Path:
        return (self.repo_root / CANONICAL_BINDER_DIR / f"{slug}.json").resolve()

    def read_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def exists(self, path: Path) -> bool:
        return path.is_file()

    def resolve(self, path: Path) -> Path:
        return path.resolve()


# --- Backlog parsing (Single Responsibility) -------------------------------

class BacklogParser:
    """Parses the backlog file to extract one feature's entry."""

    _FEATURE_ID_RE = re.compile(r"^WI(\d+)$")
    # A backlog entry block starts at `- [ ] WI##` or `- [x] WI##`, with
    # an optional `**` bold-wrap around the title (KEEL's canonical
    # /keel-refine output is `- [ ] **WI## Title**`). Extends until the
    # next such marker or end of file.
    _ENTRY_START_RE = re.compile(
        r"^[-*]\s+\[[ xX]\]\s+(?:\*\*)?WI(\d+)\b",
        re.MULTILINE,
    )

    def parse_entry(self, backlog_text: str, feature_id: str) -> BacklogEntry | None | Halt:
        """Return the BacklogEntry for `feature_id`, or None if not present,
        or a Halt if the backlog has duplicate entries for the same WI##.

        `feature_id` must be in the form `WI##` (e.g. `WI04`, `WI123`)."""
        m = self._FEATURE_ID_RE.fullmatch(feature_id)
        if not m:
            return None
        target_num = int(m.group(1))

        # Find all entry starts and their positions.
        starts = list(self._ENTRY_START_RE.finditer(backlog_text))
        if not starts:
            return None

        # Collect ALL matching blocks — halt if more than one (duplicate
        # WI## entries with different Binder/exempt markers would silently
        # use the first otherwise).
        matching_blocks: list[tuple[int, str]] = []
        for i, start_match in enumerate(starts):
            entry_num = int(start_match.group(1))
            if entry_num != target_num:
                continue
            block_start = start_match.start()
            block_end = starts[i + 1].start() if i + 1 < len(starts) else len(backlog_text)
            matching_blocks.append((block_start, backlog_text[block_start:block_end]))

        if not matching_blocks:
            return None
        if len(matching_blocks) > 1:
            offsets = [off for off, _ in matching_blocks]
            return Halt(
                HaltCode.FEATURE_DUPLICATE_IN_BACKLOG,
                (
                    f"Backlog has {len(matching_blocks)} entries for "
                    f"feature `{feature_id}` (at byte offsets {offsets}). "
                    f"Each WI## ID must appear exactly once. Fix: "
                    f"consolidate the duplicate entries into one, or "
                    f"rename one of them."
                ),
            )
        target_block = matching_blocks[0][1]

        binder_slugs = tuple(m.group(1) for m in _BINDER_RE.finditer(target_block))
        binder_exempt_reasons = tuple(
            m.group(1) for m in _BINDER_EXEMPT_RE.finditer(target_block)
        )
        spec_match = _SPEC_RE.search(target_block)
        spec_ref = spec_match.group(1) if spec_match else None
        design_match = _DESIGN_RE.search(target_block)
        design_refs: tuple[str, ...] = ()
        prototype_mode: str | None = None
        if design_match:
            content = design_match.group(1).strip()
            marker_match = _PROTOTYPE_MARKER_RE.match(content)
            if marker_match:
                prototype_mode = marker_match.group(1)
                content = content[marker_match.end():]
            design_refs = tuple(
                r.strip() for r in content.split(",") if r.strip()
            )
        needs_match = _NEEDS_RE.search(target_block)
        needs_ids: tuple[str, ...] = ()
        if needs_match:
            needs_ids = tuple(
                n.strip() for n in needs_match.group(1).split(",") if n.strip()
            )
        human_markers = tuple(
            m.group(1).strip() for m in _HUMAN_MARKER_RE.finditer(target_block)
        )

        review_match = _REVIEW_RE.search(target_block)
        review_panel: str | None = None
        if review_match:
            review_panel = review_match.group(1).strip()
            if review_panel not in _VALID_REVIEW_PANELS:
                return Halt(
                    HaltCode.REVIEW_PANEL_INVALID,
                    (
                        f"{feature_id} has an invalid `Review:` value "
                        f"{review_panel!r}. Allowed: "
                        f"{' or '.join(_VALID_REVIEW_PANELS)}. Fix: set "
                        f"`Review: personas` or `Review: roundtable` on the "
                        f"entry, or drop the field to use the project default "
                        f"(`Review panel:` in the project guide)."
                    ),
                )

        return BacklogEntry(
            feature_id=feature_id,
            feature_id_num=target_num,
            binder_slugs=binder_slugs,
            binder_exempt_reasons=binder_exempt_reasons,
            spec_ref=spec_ref,
            design_refs=design_refs,
            needs_ids=needs_ids,
            human_markers=human_markers,
            prototype_mode=prototype_mode,
            review_panel=review_panel,
            raw_block=target_block,
        )


# --- Invariant 7 classification (Single Responsibility) --------------------

class Invariant7Classifier:
    """Classifies a BacklogEntry against invariant 7, given a grandfather cutoff.

    Returns a ClassificationResult. Does not read files or the Binder JSON — that
    is a separate concern handled by the Binder resolver."""

    def classify(
        self,
        entry: BacklogEntry,
        grandfather_cutoff: int | None,
    ) -> ClassificationResult:
        binders = entry.binder_slugs
        exempts = entry.binder_exempt_reasons

        # XOR conflict — both fields present.
        if binders and exempts:
            return ClassificationResult(
                Classification.XOR_CONFLICT,
                HaltCode.INVARIANT7_XOR,
                (
                    f"{entry.feature_id} has both `Binder:` and `Binder-exempt:` "
                    f"lines. Mutually exclusive — pick one. Remove the "
                    f"`Binder-exempt:` line if this feature has a Binder, or "
                    f"remove the `Binder:` line if this is genuinely exempt."
                ),
            )

        # Multiplicity — multiple Binder: or multiple Binder-exempt:.
        if len(binders) > 1 or len(exempts) > 1:
            return ClassificationResult(
                Classification.MULTIPLICITY_CONFLICT,
                HaltCode.INVARIANT7_MULTIPLICITY,
                (
                    f"{entry.feature_id} has multiple `Binder:` or "
                    f"`Binder-exempt:` lines. Only one of each is allowed. "
                    f"Consolidate to a single `Binder: <slug>` or "
                    f"`Binder-exempt: <reason>` line."
                ),
            )

        # Binder present — eligible for pipeline.
        if binders:
            return ClassificationResult(
                Classification.JSON_BINDER_PATH,
                HaltCode.OK,
                None,
            )

        # Binder-exempt only — not pipeline-eligible.
        if exempts:
            reason = exempts[0]
            if reason not in ALLOWED_EXEMPT_REASONS:
                return ClassificationResult(
                    Classification.EXEMPT,
                    HaltCode.INVARIANT7_EXEMPT_REASON,
                    (
                        f"{entry.feature_id} declares `Binder-exempt:` with "
                        f"reason `{reason}`; must be one of "
                        f"{sorted(ALLOWED_EXEMPT_REASONS)}."
                    ),
                )
            return ClassificationResult(
                Classification.EXEMPT,
                HaltCode.BINDER_EXEMPT_NOT_PIPELINE,
                (
                    f"{entry.feature_id} is declared `Binder-exempt: {reason}`. "
                    f"Exempt features do not flow through `/keel-pipeline` "
                    f"(which reads only structured JSON Binders). Either run "
                    f"`/keel-refine` to promote this feature to a structured "
                    f"Binder (replacing `Binder-exempt:` with `Binder: <slug>`), or "
                    f"handle the work outside the pipeline."
                ),
            )

        # Neither Binder: nor Binder-exempt:. Apply grandfather rules.
        if grandfather_cutoff is None:
            # Pre-adoption. Pipeline still requires a Binder.
            return ClassificationResult(
                Classification.PREADOPTION_NO_LINK,
                HaltCode.BINDER_GRANDFATHERED_NO_LINK,
                (
                    f"{entry.feature_id} has neither `Binder:` nor "
                    f"`Binder-exempt:`. `/keel-pipeline` requires a "
                    f"`Binder: <slug>` link pointing at a structured JSON Binder. "
                    f"Run `/keel-refine` to author the Binder and backlog link, "
                    f"then re-invoke `/keel-pipeline`."
                ),
            )

        if entry.feature_id_num <= grandfather_cutoff:
            # Grandfathered; still not pipeline-eligible (no Binder).
            return ClassificationResult(
                Classification.GRANDFATHERED_NO_LINK,
                HaltCode.BINDER_GRANDFATHERED_NO_LINK,
                (
                    f"{entry.feature_id} is grandfathered pre-invariant-7 "
                    f"and carries no `Binder:` link. `/keel-pipeline` requires "
                    f"a structured JSON Binder. Run `/keel-refine` to author a "
                    f"Binder for this feature (it will add `Binder: <slug>` to the "
                    f"backlog entry), then re-invoke `/keel-pipeline`."
                ),
            )

        # Post-cutoff with neither field — invariant 7 violation.
        return ClassificationResult(
            Classification.VIOLATION,
            HaltCode.INVARIANT7_VIOLATION,
            (
                f"{entry.feature_id} is past the legacy cutoff "
                f"WI{grandfather_cutoff:02d} and must carry either "
                f"`Binder: <slug>` or `Binder-exempt: <reason>` (reason: "
                f"legacy / bootstrap / infra / trivial). Run "
                f"`/keel-refine` to author the Binder and backlog link."
            ),
        )


# --- JSON Pointer (RFC 6901) ------------------------------------------------

def jsonptr_escape_segment(segment: str) -> str:
    """Escape one path segment per RFC 6901: `~` → `~0`, `/` → `~1`.

    Order matters: `~` MUST be escaped first, else `/` escapes would be
    double-encoded."""
    return segment.replace("~", "~0").replace("/", "~1")


def jsonptr_build(*segments: str | int) -> str:
    """Build a JSON Pointer from segments. Numeric segments are stringified.

    Examples:
        jsonptr_build("work_items", 0, "contract", "channel")
          → "/work_items/0/contract/channel"
        jsonptr_build("work_items", 0, "contract", "header/x-api-key")
          → "/work_items/0/contract/header~1x-api-key"
    """
    parts: list[str] = []
    for seg in segments:
        if isinstance(seg, int):
            parts.append(str(seg))
        else:
            parts.append(jsonptr_escape_segment(seg))
    return "/" + "/".join(parts)


# --- Binder resolver + schema validation --------------------------------------

@dataclass(slots=True, frozen=True)
class BinderLoadResult:
    """Intermediate product: the Binder JSON + resolved canonical path."""
    doc: dict
    canonical_path: Path


class BinderValidator:
    """Validates a Binder JSON: JSON Schema, then cross-reference integrity.

    Mirrors scripts/validate-binder-json.py's two-stage validation: schema
    first (short-circuits on failure), then XrefValidator for
    work_items[].needs[] and duplicate feature IDs. Duplicated here rather
    than shelled-out because keel-work-item-resolve.py is called
    per-feature inside the pipeline hot path; a subprocess round-trip
    per call is unnecessary overhead.
    """

    def __init__(self, schema: dict) -> None:
        self._validator = Draft202012Validator(schema)

    def validate(self, doc: dict, binder_path: str) -> Halt | None:
        # Stage 1: JSON Schema.
        errors = sorted(
            self._validator.iter_errors(doc),
            key=lambda e: list(e.absolute_path),
        )
        if errors:
            lines = [f"Binder schema validation failed for {binder_path}:"]
            for err in errors:
                path = "/" + "/".join(str(p) for p in err.absolute_path)
                lines.append(f"  {path}: {err.message.splitlines()[0]}")
            lines.append(
                "\nFix: correct each listed finding in the Binder file. If the "
                "Binder was authored by /keel-refine, re-run /keel-refine to "
                "regenerate; if hand-edited, repair the specific fields. "
                "Then re-invoke /keel-pipeline."
            )
            return Halt(HaltCode.BINDER_SCHEMA_INVALID, "\n".join(lines))

        # Stage 2: cross-reference integrity (dangling needs, duplicate IDs,
        # self-deps). Runs only after schema validation passes.
        xref_errors = self._check_xrefs(doc)
        if xref_errors:
            lines = [f"Binder cross-reference validation failed for {binder_path}:"]
            lines.extend(f"  {err}" for err in xref_errors)
            lines.append(
                "\nFix: correct the cross-references in the Binder. Dangling "
                "`needs[]` entries mean a referenced feature doesn't exist "
                "in this Binder (fix the reference or add the feature). "
                "Self-dependency means a feature lists its own ID in "
                "`needs[]` (remove it). Duplicate feature IDs must be "
                "consolidated or renamed."
            )
            return Halt(HaltCode.BINDER_SCHEMA_INVALID, "\n".join(lines))

        return None

    def _check_xrefs(self, doc: dict) -> list[str]:
        """Post-schema cross-reference integrity checks."""
        errors: list[str] = []
        work_items = doc.get("work_items", [])
        if not isinstance(work_items, list):
            return errors  # schema stage would have caught this
        known_ids = {
            f["id"] for f in work_items
            if isinstance(f, dict) and isinstance(f.get("id"), str)
        }
        seen_ids: dict[str, list[int]] = {}
        for i, work_item in enumerate(work_items):
            if not isinstance(work_item, dict):
                continue
            fid = work_item.get("id")
            needs = work_item.get("needs", [])
            if isinstance(needs, list):
                for need in needs:
                    if isinstance(need, str) and need not in known_ids:
                        errors.append(
                            f"/work_items/{i}/needs: '{need}' does not "
                            f"resolve to any feature in this Binder"
                        )
                if isinstance(fid, str) and fid in needs:
                    errors.append(
                        f"/work_items/{i}/needs: feature '{fid}' declares "
                        f"itself as a dependency"
                    )
            if isinstance(fid, str):
                seen_ids.setdefault(fid, []).append(i)
        for fid, positions in seen_ids.items():
            if len(positions) > 1:
                first = positions[0]
                for dup_pos in positions[1:]:
                    errors.append(
                        f"/work_items/{dup_pos}/id: duplicate feature id "
                        f"'{fid}' (already declared at /work_items/{first}/id)"
                    )
        return errors


def load_schema(repo_root: Path) -> dict:
    """Load `schemas/binder.schema.json` strictly from repo_root.

    Does NOT walk up the tree — if repo_root is a subdirectory of the
    real repo (e.g. agent invoked from `scripts/`), we want the
    INVOCATION halt to fire rather than silently succeeding on a
    grandparent's schema while `FileBinderJsonSource` resolves Binder paths
    against the wrong root (which would then surface as a confusing
    `BINDER_FILE_MISSING` downstream).

    Symlinks are rejected to prevent schema hijacks in vendored/monorepo
    layouts where `schemas/` could be a symlink to an unexpected
    location.
    """
    schema_path = repo_root / SCHEMA_REL
    if not schema_path.is_file():
        raise FileNotFoundError(
            f"Could not locate {SCHEMA_REL} at {schema_path}."
        )
    if schema_path.is_symlink():
        raise FileNotFoundError(
            f"{schema_path} is a symlink; resolve and commit the real "
            f"file in-tree to prevent schema hijack."
        )
    return json.loads(schema_path.read_text(encoding="utf-8"))


# --- Feature extraction (Single Responsibility) ----------------------------

@dataclass(slots=True, frozen=True)
class FeatureExtraction:
    """The per-feature product of an already-validated Binder."""
    feature_index: int
    title: str
    layer: str
    oracle: dict
    contract: dict
    needs: list[str]


class FeatureExtractor:
    """Extracts per-feature fields from a validated Binder JSON document.

    Count-gates on the feature ID: must be exactly one match."""

    def extract(self, doc: dict, feature_id: str) -> FeatureExtraction | Halt:
        work_items = doc.get("work_items")
        if not isinstance(work_items, list):
            # Schema validation should have caught this; defensive guard.
            return Halt(
                HaltCode.BINDER_SCHEMA_INVALID,
                "Binder `work_items` is not an array after schema validation — "
                "this indicates a validator bug. Re-run `validate-binder-json.py` "
                "directly to reproduce.",
            )

        matches = [
            (i, f) for i, f in enumerate(work_items)
            if isinstance(f, dict) and f.get("id") == feature_id
        ]
        if len(matches) == 0:
            return Halt(
                HaltCode.FEATURE_NOT_IN_BINDER,
                (
                    f"Feature `{feature_id}` not present in Binder. Either add "
                    f"the work item object to `work_items[]` with "
                    f"`id: \"{feature_id}\"`, or correct the backlog entry's "
                    f"ID to match an existing feature."
                ),
            )
        if len(matches) > 1:
            return Halt(
                HaltCode.FEATURE_DUPLICATE_IN_BINDER,
                (
                    f"Duplicate feature ID `{feature_id}` in Binder. Feature "
                    f"IDs must be unique per Binder — remove duplicates. (The "
                    f"XrefValidator should have caught this; if you see "
                    f"this message, flag a validator bug.)"
                ),
            )

        idx, feat = matches[0]
        return FeatureExtraction(
            feature_index=idx,
            title=feat.get("title", ""),
            layer=feat.get("layer", ""),
            oracle=feat.get("oracle", {}),
            contract=feat.get("contract", {}),
            needs=list(feat.get("needs", [])),
        )


# --- Orchestrator -----------------------------------------------------------

@dataclass(slots=True, frozen=True)
class ResolveRequest:
    """Input to FeatureResolver.resolve — one feature + optional Binder path."""
    repo_root: Path
    backlog_path: Path
    feature_id: str
    supplied_binder_path: Path | None


class FeatureResolver:
    """Orchestrates backlog → classification → Binder → feature-extraction,
    short-circuiting on the first halt. Single responsibility: orchestration."""

    def __init__(
        self,
        backlog_parser: BacklogParser,
        classifier: Invariant7Classifier,
        binder_source: BinderJsonSource,
        schema: dict,
    ) -> None:
        self._backlog_parser = backlog_parser
        self._classifier = classifier
        self._binder_source = binder_source
        self._binder_validator = BinderValidator(schema)
        self._feature_extractor = FeatureExtractor()

    def resolve(
        self,
        req: ResolveRequest,
        backlog_source: BacklogSource,
    ) -> FeatureResolution | Halt:
        # --- Stage 1: backlog
        if not req.backlog_path.is_file():
            return Halt(
                HaltCode.BACKLOG_NOT_FOUND,
                (
                    f"Backlog not found at {req.backlog_path}. "
                    f"Fix: pass --backlog with the correct path (default "
                    f"lives at docs/exec-plans/active/backlog.md), "
                    f"or initialize the backlog via /keel-adopt or "
                    f"/keel-setup if this is a new project."
                ),
            )
        backlog_text = backlog_source.read()
        parse_result = self._backlog_parser.parse_entry(backlog_text, req.feature_id)
        if isinstance(parse_result, Halt):
            return parse_result
        if parse_result is None:
            return Halt(
                HaltCode.FEATURE_NOT_IN_BACKLOG,
                (
                    f"Feature `{req.feature_id}` not found in backlog at "
                    f"{req.backlog_path}. Fix: add a `- [ ] {req.feature_id}: "
                    f"...` entry to the backlog, or correct the feature ID "
                    f"passed to `--feature`."
                ),
            )
        entry = parse_result

        if entry.human_markers:
            markers = "; ".join(entry.human_markers)
            # Substitute the concrete slug when the entry has exactly
            # one — gives the user a copy-pasteable invocation. Other
            # slug counts (zero, multiple) are classified as halts at
            # Stage 2, so the fallback placeholder only surfaces when
            # those classifier halts were suppressed upstream.
            refine_target = (
                entry.binder_slugs[0] if len(entry.binder_slugs) == 1 else "<slug>"
            )
            return Halt(
                HaltCode.HUMAN_MARKER_UNRESOLVED,
                (
                    f"{req.feature_id} carries unresolved `<!-- HUMAN: ... -->` "
                    f"marker(s): {markers}. Drafts must be resolved before "
                    f"pipeline entry. Run `/keel-refine {refine_target}` to "
                    f"walk the open question as a card — the skill auto-enters "
                    f"re-run mode when the Binder exists on disk. Then re-invoke "
                    f"`/keel-pipeline`."
                ),
            )

        # --- Stage 2: invariant 7 classification (reuses already-read text)
        cutoff = backlog_source.grandfather_cutoff(backlog_text)
        classification = self._classifier.classify(entry, cutoff)
        if classification.classification is not Classification.JSON_BINDER_PATH:
            assert classification.halt_message is not None
            return Halt(classification.halt_code, classification.halt_message)

        slug = entry.binder_slugs[0]
        canonical = self._binder_source.canonical_path(slug)

        # --- Stage 3: Binder-format gate
        if req.supplied_binder_path is not None:
            # Resolve relative --binder against the repo root, not cwd, so
            # `--repo /x/repo --binder docs/exec-plans/binders/y.json` matches
            # the canonical path regardless of where the CLI was invoked.
            supplied = req.supplied_binder_path
            if not supplied.is_absolute():
                supplied = req.repo_root / supplied
            supplied_resolved = self._binder_source.resolve(supplied)
            if supplied_resolved.suffix != ".json":
                return Halt(
                    HaltCode.BINDER_FORMAT_NOT_JSON,
                    (
                        f"Binder path `{req.supplied_binder_path}` is not a "
                        f"structured JSON Binder. `/keel-pipeline` reads JSON "
                        f"only. Run `/keel-refine` to produce "
                        f"`docs/exec-plans/binders/{slug}.json`, then re-invoke."
                    ),
                )
            if supplied_resolved != canonical:
                return Halt(
                    HaltCode.BINDER_PATH_MISMATCH,
                    (
                        f"Binder path supplied (`{req.supplied_binder_path}`) does "
                        f"not match the canonical path for slug `{slug}` "
                        f"(`{canonical}`). Use the canonical path, or "
                        f"reconcile the backlog's `Binder:` slug."
                    ),
                )

        if not self._binder_source.exists(canonical):
            return Halt(
                HaltCode.BINDER_FILE_MISSING,
                (
                    f"Binder file `{canonical}` does not exist. Run "
                    f"`/keel-refine` to author the structured JSON Binder, "
                    f"then re-invoke `/keel-pipeline`."
                ),
            )

        # --- Stage 4: read + schema-validate Binder
        try:
            doc = self._binder_source.read_json(canonical)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
            return Halt(
                HaltCode.BINDER_SCHEMA_INVALID,
                (
                    f"Binder at `{canonical}` is not readable UTF-8 JSON: {e}. "
                    f"Fix: repair the file to be valid UTF-8 JSON. If "
                    f"authored by /keel-refine, re-run /keel-refine to "
                    f"regenerate. If hand-edited, check for unterminated "
                    f"strings, trailing commas, or encoding issues."
                ),
            )

        schema_halt = self._binder_validator.validate(doc, str(canonical))
        if schema_halt is not None:
            return schema_halt

        # --- Stage 5: slug/id cross-check
        doc_id = doc.get("id")
        if doc_id != slug:
            return Halt(
                HaltCode.BINDER_SLUG_ID_MISMATCH,
                (
                    f"Binder slug mismatch: backlog says `Binder: {slug}` but the "
                    f"JSON file's `.id` is `{doc_id}`. Either rename the "
                    f"backlog slug, rename the JSON's `.id`, or correct the "
                    f"Binder file path."
                ),
            )

        # --- Stage 6: design-ref validation (guards: no URL, no absolute
        # paths, no escape-from-repo via `..` traversal or out-of-tree
        # symlink target)
        repo_root_resolved = req.repo_root.resolve()
        for ref in entry.design_refs:
            if ref.startswith(("http://", "https://")):
                return Halt(
                    HaltCode.DESIGN_REF_INVALID,
                    (
                        f"Design reference `{ref}` on backlog entry "
                        f"`{req.feature_id}` is an external URL. Design "
                        f"refs must be committed files. Commit the design "
                        f"to the repo and update the `Design:` field."
                    ),
                )
            ref_path_raw = Path(ref)
            if ref_path_raw.is_absolute():
                return Halt(
                    HaltCode.DESIGN_REF_INVALID,
                    (
                        f"Design reference `{ref}` on backlog entry "
                        f"`{req.feature_id}` is an absolute path. Design "
                        f"refs must be repo-relative. Fix: rewrite as a "
                        f"path relative to the repo root."
                    ),
                )
            ref_path = (req.repo_root / ref).resolve()
            if not ref_path.is_file():
                return Halt(
                    HaltCode.DESIGN_REF_INVALID,
                    (
                        f"Design reference `{ref}` on backlog entry "
                        f"`{req.feature_id}` does not resolve to a committed "
                        f"file under the repo. Commit the file or correct "
                        f"the `Design:` field."
                    ),
                )
            if not ref_path.is_relative_to(repo_root_resolved):
                return Halt(
                    HaltCode.DESIGN_REF_INVALID,
                    (
                        f"Design reference `{ref}` on backlog entry "
                        f"`{req.feature_id}` resolves outside the repo "
                        f"(to `{ref_path}`). Design refs must be committed "
                        f"files under the repo — no `..` traversal or "
                        f"symlinks pointing outside the tree."
                    ),
                )

        # --- Stage 7: feature extraction
        extraction = self._feature_extractor.extract(doc, req.feature_id)
        if isinstance(extraction, Halt):
            return extraction

        # --- Stage 8: assemble result
        return FeatureResolution(
            feature_id=req.feature_id,
            feature_index=extraction.feature_index,
            feature_pointer_base=jsonptr_build("work_items", extraction.feature_index),
            # Both `binder_path` and `canonical_binder_path` are resolved
            # absolute paths so downstream agents (who forward these
            # verbatim in handoff briefs) see a stable form regardless
            # of whether the caller supplied --binder.
            binder_path=str(canonical),
            canonical_binder_path=str(canonical),
            title=extraction.title,
            layer=extraction.layer,
            oracle=extraction.oracle,
            contract=extraction.contract,
            needs=extraction.needs,
            binder_invariants_exercised=list(doc.get("invariants_exercised", [])),
            backlog_fields={
                "binder_slug": slug,
                "binder_exempt_reason": None,
                "spec_ref": entry.spec_ref,
                "design_refs": list(entry.design_refs),
                "needs_ids": list(entry.needs_ids),
                "human_markers": list(entry.human_markers),
                "prototype_mode": entry.prototype_mode,
                "review_panel": entry.review_panel,
            },
            classification=classification.classification.value,
        )


# --- Shared v2 (resolved-work-item.json) derivation + source_hash ------------
#
# These helpers are imported by BOTH `keel-work-item-resolve.py` (writer, A.6)
# and `validate-handoff.py` (recomputing validator, A.7). Single-sourcing
# them here is the P4-correct way to guarantee the source_hash canonical
# form is byte-identical across writer and validator — copy-pasting the
# logic into two scripts would let it drift.

# Resolver output uses a 3-value layer vocabulary (ui / backend /
# cross-cutting); the Binder schema uses a 4-value vocabulary
# (service / ui / cross-cutting / foundation). Map the Binder layer onto the
# resolved-work-item enum. Non-UI, non-cross-cutting layers collapse to
# `backend` (the least-surprising bucket for service/foundation/anything
# else, since the resolved-work-item consumer only distinguishes UI work,
# cross-cutting work, and "everything else").
_BINDER_TO_RESOLVED_LAYER = {
    "ui": "ui",
    "cross-cutting": "cross-cutting",
    "service": "backend",
    "foundation": "backend",
}


def map_binder_layer(binder_layer: str) -> str:
    """Map a Binder-schema layer value onto the resolved-work-item layer enum
    (ui | backend | cross-cutting). Unknown values fall back to `backend`."""
    return _BINDER_TO_RESOLVED_LAYER.get(binder_layer, "backend")


def slugify(text: str) -> str:
    """Kebab-case a feature title into a resolved-work-item `feature.slug`.

    Matches the schema pattern `^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$`:
    lowercase, alphanumerics + hyphens, no leading/trailing/double hyphen.
    Falls back to `feature` when the input has no alphanumeric content
    (e.g. a punctuation-only title) so the slug is always schema-valid."""
    cleaned = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return cleaned or "feature"


def binder_invariant_ids(binder_invariants_exercised: list) -> list[str]:
    """Extract the string invariant IDs from a Binder's `invariants_exercised`.

    The Binder schema places `invariants_exercised` at the Binder root as a list
    of OBJECTS (`{invariant_id, name?, how_exercised}`). The
    resolved-work-item schema's `binder.invariants_exercised` is a list of
    STRING IDs. Reconcile by pulling each `invariant_id`; entries without
    one are dropped (defensive — schema validation upstream guarantees the
    field, but a malformed/partial Binder should not crash the resolver).
    Returns [] when the source list is empty or not derivable."""
    ids: list[str] = []
    for item in binder_invariants_exercised or ():
        if isinstance(item, dict) and isinstance(item.get("invariant_id"), str):
            ids.append(item["invariant_id"])
    return ids


def extract_binder_slice(binder_doc: dict, feature_id: str) -> dict:
    """Return the verbatim `work_items[id==WI##]` subtree from a Binder document.

    Used for BOTH the resolved-work-item `binder.slice` field and the
    source_hash `binder_slice` input. Defined here (not in the writer script)
    so the validator recomputes an IDENTICAL slice. Returns {} when the
    feature is absent (the writer reaches this only after the resolver has
    already confirmed the feature exists; the validator tolerates a stale
    Binder gracefully and lets the hash mismatch surface the staleness)."""
    for feat in binder_doc.get("work_items", []):
        if isinstance(feat, dict) and feat.get("id") == feature_id:
            return feat
    return {}


def backlog_entry_to_canonical_dict(entry: BacklogEntry) -> dict:
    """Stable dict form of a parsed backlog entry for source_hash input.

    Only the SEMANTIC fields are included (the ones that, if edited,
    should invalidate downstream verdicts): Binder slug(s), exempt
    reason(s), spec ref, design refs, needs, prototype mode, review
    panel. The `raw_block` text is deliberately EXCLUDED — it carries
    incidental whitespace/formatting that would make the hash sensitive
    to cosmetic backlog edits (violating the schema's
    whitespace-insensitive contract). `feature_id` is included so the
    hash is feature-specific. Tuples become sorted-stable lists; the
    final canonicalization (sort_keys) is applied by the caller."""
    return {
        "feature_id": entry.feature_id,
        "binder_slugs": list(entry.binder_slugs),
        "binder_exempt_reasons": list(entry.binder_exempt_reasons),
        "spec_ref": entry.spec_ref,
        "design_refs": list(entry.design_refs),
        "needs_ids": list(entry.needs_ids),
        "prototype_mode": entry.prototype_mode,
        "review_panel": entry.review_panel,
    }


# --- Structured backlog pretriage fields (PR-B authored, PR-A consumed) ----
#
# `backlog-drafter` (PR B, plan §B.3) emits optional structured YAML arrays
# under a feature's backlog entry:
#
#     dependencies:
#       - id: WI22
#         kind: feature
#       - id: angular-21-signals
#         kind: library
#         novel: true
#     frozen_seams:
#       - referenced_in: WI22
#         name: streamBulkEvents-return-type
#     complexity: architecture-tier
#
# These are the deterministic inputs for the `novel_dependency`,
# `frozen_seam_impact`, and `architecture_tier_hint` pretriage signals.
# Today's backlogs (pre-PR-B) carry NONE of these — so the parser must
# distinguish "field absent" (→ None / fail-safe) from "field present and
# empty". We parse them from the entry's raw markdown block with a tiny
# indentation-aware reader rather than taking a pyyaml dependency (keeping
# this module's declared-external surface to jsonschema only, per the
# resolver script's PEP 723 header).

_COMPLEXITY_RE = re.compile(
    r"(?:^|\|)\s*complexity:\s*([a-z][a-z-]*)\s*(?=\||$)",
    re.MULTILINE | re.IGNORECASE,
)


def _parse_yaml_listblock(raw_block: str, key: str) -> list[dict] | None:
    """Parse `key:`-introduced YAML list-of-mappings from a backlog entry.

    Returns the list of dicts (scalar values coerced: true/false → bool,
    bare numbers left as strings, everything else stripped string), or
    None when the `key:` header is absent from the block (the fail-safe
    discriminator). An empty list is returned when the header is present
    but has no `- ` items.

    Deliberately narrow: handles the exact shape `backlog-drafter` emits
    (a top-level `key:` line, then `  - field: value` / `    field: value`
    continuation lines at deeper indent). Not a general YAML parser."""
    lines = raw_block.splitlines()
    header_idx = None
    header_indent = 0
    for i, line in enumerate(lines):
        m = re.match(rf"^(\s*){re.escape(key)}:\s*$", line)
        if m:
            header_idx = i
            header_indent = len(m.group(1))
            break
    if header_idx is None:
        return None

    items: list[dict] = []
    current: dict | None = None
    for line in lines[header_idx + 1:]:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= header_indent:
            break  # dedented out of the block
        stripped = line.strip()
        if stripped.startswith("- "):
            current = {}
            items.append(current)
            stripped = stripped[2:].strip()
            if not stripped:
                continue
        if current is None:
            # a continuation line before any `- ` — malformed; ignore.
            continue
        if ":" in stripped:
            field_name, _, value = stripped.partition(":")
            current[field_name.strip()] = _coerce_scalar(value.strip())
    return items


def _coerce_scalar(value: str):
    low = value.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    return value


def parse_structured_dependencies(raw_block: str) -> list[dict] | None:
    """Return the backlog entry's structured `dependencies:` list, or None
    when the field is absent (the fail-safe discriminator for the
    `novel_dependency` signal — see compute_pretriage_inputs)."""
    return _parse_yaml_listblock(raw_block, "dependencies")


def parse_structured_frozen_seams(raw_block: str) -> list[dict] | None:
    """Return the backlog entry's structured `frozen_seams:` list, or None
    when the field is absent."""
    return _parse_yaml_listblock(raw_block, "frozen_seams")


def parse_complexity_hint(raw_block: str) -> str | None:
    """Return the backlog entry's `complexity:` value (e.g.
    `architecture-tier`), or None when the field is absent."""
    m = _COMPLEXITY_RE.search(raw_block)
    return m.group(1).strip() if m else None


def compute_source_hash(
    binder_slice: dict,
    backlog_entry: dict,
    security_list: list[str],
) -> str:
    """SHA-256 of the canonical JSON of the three resolution inputs.

    ## SOURCE_HASH CANONICAL FORM — mirrored verbatim by
    ## validate-handoff.py (A.7). Do not change one without the other.
    ##
    ## canonical = json.dumps(
    ##     {"binder_slice": <dict>, "backlog_entry": <dict>,
    ##      "security_list": <list[str]>},
    ##     sort_keys=True, separators=(",", ":"),
    ## )
    ## source_hash = sha256(canonical.encode("utf-8")).hexdigest()
    ##
    ## - The OUTER dict keys are exactly: binder_slice, backlog_entry,
    ##   security_list (sort_keys re-orders them, so author order is
    ##   irrelevant — but the NAMES are load-bearing).
    ## - sort_keys=True makes nested key order irrelevant; separators
    ##   strip all whitespace, so Binder/backlog pretty-print reformats do
    ##   NOT change the hash (the schema's whitespace-insensitive
    ##   contract).
    ## - security_list is passed THROUGH as given (not sorted here);
    ##   callers pass keel.json's security_sensitive_invariants verbatim.
    """
    canonical = json.dumps(
        {
            "binder_slice": binder_slice,
            "backlog_entry": backlog_entry,
            "security_list": security_list,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
