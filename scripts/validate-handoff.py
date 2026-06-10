#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["jsonschema>=4.21"]
# ///
"""KEEL Handoff Validator — structural checks on pipeline handoff files.

Two layouts, one entrypoint:

* LEGACY single-file handoffs (`WI##-<slug>.md`) — the pre-Option-H shape,
  still found under `completed/handoffs/`. Validated by the
  `HandoffValidator` class. This path is **pure stdlib** (no jsonschema)
  so it keeps working under a bare `python3` invocation — the stdlib test
  suite shells the script out with `[sys.executable, ...]`.
* OPTION H per-feature directories (`WI##-<slug>/` containing
  `routing.json` + `resolved-work-item.json` + agent `.md` files). Validated
  by `_validate_h_handoff`, which lazily imports `jsonschema` (so the
  legacy path above stays stdlib-only). Run this path under `uv run`.

`source_hash` recompute MUST stay byte-identical to the resolver
(`scripts/keel-work-item-resolve.py`). To guarantee that, this validator
IMPORTS the shared canonical-form helpers from `scripts/keel_work_items.py`
rather than reimplementing them.

Usage:
    uv run scripts/validate-handoff.py <handoff-file-or-directory>

Examples:
    uv run scripts/validate-handoff.py docs/exec-plans/completed/handoffs/WI13-fetch.md
    uv run scripts/validate-handoff.py docs/exec-plans/completed/handoffs/
    uv run scripts/validate-handoff.py docs/exec-plans/active/handoffs/

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
    2 — usage error
"""

import fnmatch
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# --- Colors ---
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"

OK = f"{GREEN}✓{RESET}"
FAIL = f"{RED}✗{RESET}"
WARN = f"{YELLOW}!{RESET}"


# --- YAML frontmatter parsing (no dependencies) ---

def parse_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter between --- delimiters. Returns dict or None."""
    match = re.search(r"^---\s*\n(.*?)\n---\s*$", text, re.MULTILINE | re.DOTALL)
    if not match:
        return None

    data = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.split("#")[0].strip()  # strip inline comments
            data[key] = value
    return data


def extract_sections(text: str) -> dict[str, str]:
    """Extract ## sections and their content from markdown.

    Fence-aware via `strip_fenced_code_blocks` — `##` headings inside
    fenced code blocks (``` or ~~~) are treated as ordinary content, not
    new sections. Section bodies include fence content verbatim from the
    original text.

    NOTE: duplicate `##` headings collapse silently — the last occurrence wins.
    For duplicate detection, use `extract_section_headings` which preserves
    every `##` heading in document order.
    """
    masked = strip_fenced_code_blocks(text)
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_start: int | None = None  # body start in original text

    pos = 0
    text_len = len(text)
    while pos < text_len:
        nl = text.find("\n", pos)
        line_end = nl if nl != -1 else text_len
        terminator_end = nl + 1 if nl != -1 else text_len

        masked_line = masked[pos:line_end]
        heading_match = re.match(r"^## (.+)$", masked_line)
        if heading_match:
            if current_heading is not None and current_start is not None:
                # Slice body from original text up to (not including) this heading.
                body = text[current_start:pos].rstrip("\n")
                sections[current_heading] = body
            current_heading = heading_match.group(1).strip()
            current_start = terminator_end

        pos = terminator_end

    if current_heading is not None and current_start is not None:
        sections[current_heading] = text[current_start:].rstrip("\n")

    return sections


def extract_section_headings(text: str) -> list[str]:
    """Return every `##` heading text in document order, preserving duplicates.

    Skips headings inside markdown fenced code blocks (``` or ~~~ regions) so
    code samples that quote `## name (revised)` don't generate false positives.
    """
    cleaned = strip_fenced_code_blocks(text)
    return [
        m.group(1).strip()
        for m in re.finditer(r"^## (.+)$", cleaned, re.MULTILINE)
    ]


def extract_subsection_blocks(body: str, level: int) -> list[tuple[str, str]]:
    """Return [(heading, sub-body)] pairs for each level-N heading inside `body`.

    sub-body is the content from after the heading line up to (but not including)
    the next heading at this level OR any higher level (lower `#` count) OR EOF.

    Skips headings inside fenced code blocks. Sub-bodies, however, are returned
    verbatim from the original `body` so downstream slicing (e.g., further
    subsection extraction) sees real content; fence-stripping is only applied
    when locating heading boundaries.
    """
    prefix = "#" * level + " "
    heading_re = re.compile(rf"^{re.escape(prefix)}(.+)$", re.MULTILINE)
    same_or_higher_alt = "|".join(re.escape("#" * lvl + " ") for lvl in range(1, level + 1))
    boundary_re = re.compile(rf"^(?:{same_or_higher_alt})", re.MULTILINE)

    cleaned = strip_fenced_code_blocks(body)

    result: list[tuple[str, str]] = []
    for m in heading_re.finditer(cleaned):
        heading = m.group(1).strip()
        start = m.end()
        next_boundary = boundary_re.search(cleaned, pos=start)
        end = next_boundary.start() if next_boundary else len(cleaned)
        # Slice from the original body so nested fenced content survives in
        # sub-bodies handed to recursive callers.
        result.append((heading, body[start:end]))
    return result


def section_has_content(body: str) -> bool:
    """Check if a section has real content (not just HTML comments and whitespace)."""
    stripped = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    stripped = re.sub(r"###\s+\w.*", "", stripped)  # remove sub-headings
    stripped = stripped.strip()
    return len(stripped) > 0


# --- Pipeline variant definitions ---

REQUIRED_SECTIONS = {
    "bootstrap": ["landing-verifier"],
    "backend": ["pre-check", "test-writer", "implementer", "spec-reviewer", "landing-verifier"],
    "frontend": ["pre-check", "frontend-designer", "test-writer", "implementer", "spec-reviewer", "landing-verifier"],
    "cross-cutting": ["pre-check", "test-writer", "implementer", "landing-verifier"],
    # Karta is the lean MVP lane (spec-first): pre-check → implementer →
    # karta-spec-reviewer → safety-auditor → green gate → land. One WI per run.
    # The green gate is a direct orchestrator command (the project's own
    # tests/build), NOT a landing-verifier dispatch — so no landing-verifier.md
    # is written and it is not a required section. It drops the
    # design/code-reviewer/keel-spec-reviewer/arch-advisor/review-panel sections
    # of the full lane; test-writer is optional (tests are secondary in the
    # spec-first lane). karta-spec-reviewer (the structural conformance gate)
    # and safety-auditor are the mandatory review gates.
    "karta": ["pre-check", "implementer", "karta-spec-reviewer", "safety-auditor"],
}

CONDITIONAL_SECTIONS = {
    "researcher_needed": "researcher",
    # designer_needed is variant-aware: backend pipeline → backend-designer,
    # frontend pipeline → frontend-designer. Handled directly in
    # _check_conditional_sections, not by this dict.
    "safety_auditor_needed": "safety-auditor",
    "arch_advisor_needed": "arch-advisor-consultation",
    # The landing review always runs (review panel is the default), so the
    # `landing-review` section is gated on review_panel being resolved.
    # Handled directly in _check_conditional_sections, not by this dict.
}

VALID_INTENTS = {"refactoring", "build", "mid-sized", "architecture", "research"}
VALID_COMPLEXITIES = {"trivial", "standard", "complex", "architecture-tier"}
VALID_YES_NO = {"YES", "NO"}
VALID_SPEC_VERDICTS = {"CONFORMANT", "DEVIATION"}
VALID_SAFETY_VERDICTS = {"PASS", "VIOLATION"}
VALID_ARCH_VERDICTS = {"SOUND", "UNSOUND"}
VALID_REVIEW_VERDICTS = {"APPROVED", "CONCERNS"}
VALID_REVIEW_PANELS = {"personas", "roundtable"}


# --- Snapshot/append rule definitions ---
#
# Agent output sections are SNAPSHOT — overwritten on re-run. Sibling
# parenthesized headings (e.g. `## pre-check (revised, attempt 2)`) are
# forbidden. Review-panel deliberation sections are APPEND-only, with each
# attempt becoming a `### Attempt N — <verdict>` block. Under the roundtable
# panel each attempt carries tool-paired `####` subsections; under the
# persona panel an attempt is one line per lens plus synthesized findings
# (no required `####` subsections).

AGENT_OUTPUT_SECTIONS: frozenset[str] = frozenset({
    "pre-check",
    "test-writer",
    "implementer",
    "code-reviewer",
    "spec-reviewer",
    "karta-spec-reviewer",
    "safety-auditor",
    "landing-verifier",
    "researcher",
    "arch-advisor-consultation",
    "arch-advisor-verification",
    "backend-designer",
    "frontend-designer",
})

# Review-panel deliberation sections. The mapped value is the set of `####`
# subsections the ROUNDTABLE panel emits per attempt; the persona panel emits
# one line per lens plus synthesized findings and has no required `####`
# subsections (so the subsection check applies only when review_panel:
# roundtable).
REVIEW_DELIBERATION_SECTIONS: dict[str, frozenset[str]] = {
    "precheck-review": frozenset({"Critique", "Canvass"}),
    "design-review": frozenset({"Blueprint", "Critique"}),
    "landing-review": frozenset({"Crosscheck", "Critique"}),
}

# Heading names that may legitimately appear as "parents" of forbidden
# parenthesized siblings. AGENT_OUTPUT_SECTIONS carries the split designer
# forms; REVIEW_DELIBERATION_SECTIONS adds the deliberation headings.
# The legacy slash form is included so that a still-active handoff
# carrying `## backend-designer / frontend-designer (revised, attempt 2)`
# from before the disambiguation is still flagged as a forbidden sibling
# rather than silently slipping past the snapshot rule.
_PARENT_HEADING_NAMES: frozenset[str] = (
    AGENT_OUTPUT_SECTIONS
    | frozenset({"backend-designer / frontend-designer"})  # legacy
    | frozenset(REVIEW_DELIBERATION_SECTIONS.keys())
)
_PARENT_NAMES_ALT: str = "|".join(
    re.escape(n) for n in sorted(_PARENT_HEADING_NAMES, key=len, reverse=True)
)
FORBIDDEN_SIBLING_RE: re.Pattern[str] = re.compile(
    rf"^({_PARENT_NAMES_ALT}) \(.+\)$"
)
ATTEMPT_BLOCK_RE: re.Pattern[str] = re.compile(r"^Attempt (\d+) — .+$")


def is_archived_handoff(filepath: Path) -> bool:
    """True if the handoff sits under an adjacent `completed/handoffs/` pair.

    Archived handoffs predate the snapshot rule and are grandfathered (P5:
    don't retroactively rewrite archived content). Snapshot-rule structural
    checks only apply to active handoffs.

    Adjacency matters: a non-archived path like
    `~/work/completed/myrepo/docs/exec-plans/active/handoffs/WI01.md`
    contains both segments but is NOT a `completed/handoffs/` archive.

    Inspects the path components as written — does NOT call `.resolve()`,
    so symlinks pointing into / out of `completed/handoffs/` are evaluated
    by the literal path the user passed, not by the symlink target.
    """
    parts = filepath.parts
    return any(
        a == "completed" and b == "handoffs"
        for a, b in zip(parts, parts[1:])
    )


def _detect_fence_marker(stripped_line: str) -> str | None:
    r"""Return ``` or ~~~ if the line opens/closes a fence, else None.

    Matches CommonMark info-string semantics: the line starts with the
    marker; trailing characters (info string after `\`\`\`python`) are
    accepted on the opener. Closing lines must consist of just the marker
    (with optional trailing whitespace) — enforced by callers that compare
    the stripped line to the stored marker.
    """
    if stripped_line.startswith("```"):
        return "```"
    if stripped_line.startswith("~~~"):
        return "~~~"
    return None


def strip_fenced_code_blocks(text: str) -> str:
    """Mask fenced code blocks while preserving every byte position.

    Line-based scanner: a line whose stripped form starts with ``` or ~~~
    opens a fence; the next line whose stripped form equals the opening
    marker closes it. Unclosed fences mask all the way to EOF (matching
    `extract_sections`'s state machine — single source of truth for fence
    semantics in this validator).

    Inside fenced regions, non-newline bytes become spaces; newlines stay
    intact. `len(strip_fenced_code_blocks(text)) == len(text)`, so match
    offsets on the masked text correctly index into the original.

    Limitations (documented; not addressed):
    - Same-marker nested fences: an inner ``` closes the outer ``` (first
      match wins). CommonMark requires the closer to have ≥ as many backticks
      as the opener; this validator does not.
    - 4+ backtick fences: matched at ``` (3-backtick) prefix; the 4th+
      backtick is treated as info-string. Closing 3-backtick line ends the
      fence even if the original opener used 4. Agent-generated handoffs
      use 3-backtick fences.
    """
    out: list[str] = []
    in_fence = False
    fence_marker: str | None = None
    pos = 0
    text_len = len(text)

    while pos < text_len:
        nl = text.find("\n", pos)
        line_end = nl if nl != -1 else text_len
        terminator_end = nl + 1 if nl != -1 else text_len
        chunk = text[pos:terminator_end]
        stripped = text[pos:line_end].strip()

        if not in_fence:
            marker = _detect_fence_marker(stripped)
            if marker is not None:
                out.append("".join(c if c == "\n" else " " for c in chunk))
                in_fence = True
                fence_marker = marker
            else:
                out.append(chunk)
        else:
            out.append("".join(c if c == "\n" else " " for c in chunk))
            if stripped == fence_marker:
                in_fence = False
                fence_marker = None

        pos = terminator_end

    return "".join(out)


# --- Validator ---

class HandoffValidator:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.text = filepath.read_text(encoding="utf-8")
        self.frontmatter = parse_frontmatter(self.text)
        self.sections = extract_sections(self.text)
        self.section_headings = extract_section_headings(self.text)
        self.archived = is_archived_handoff(filepath)
        self.passed = 0
        self.failed = 0
        self.warned = 0

    def ok(self, msg: str):
        print(f"  {OK} {msg}")
        self.passed += 1

    def fail(self, msg: str):
        print(f"  {FAIL} {msg}")
        self.failed += 1

    def warn(self, msg: str):
        print(f"  {WARN} {msg}")
        self.warned += 1

    def validate(self) -> bool:
        print(f"\n{BOLD}Validating:{RESET} {self.filepath}")

        if not self._check_frontmatter():
            return False

        pipeline = self.frontmatter.get("pipeline", "")
        status = self.frontmatter.get("status", "")

        self._check_pipeline(pipeline)

        if pipeline != "bootstrap":
            self._check_routing_fields()

        self._check_branching_fields(self.frontmatter)
        self._check_required_sections(pipeline)
        self._check_conditional_sections()

        # Snapshot/append rule structural checks. Skipped for archived
        # handoffs (P5: don't retroactively rewrite pre-rule history).
        if not self.archived:
            self._check_no_forbidden_siblings()
            self._check_no_duplicate_canonical_sections()
            self._check_attempt_block_format()

        if status == "LANDED":
            self._check_verdicts()

        self._check_status_consistency(status)

        total = self.passed + self.failed
        result = "PASS" if self.failed == 0 else "FAIL"
        color = GREEN if self.failed == 0 else RED
        warnings = f" ({self.warned} warnings)" if self.warned else ""
        print(f"\n  {color}{BOLD}Result: {result}{RESET} ({self.passed}/{total} checks){warnings}\n")
        return self.failed == 0

    def _check_frontmatter(self) -> bool:
        if self.frontmatter is None:
            self.fail("No YAML frontmatter found (missing --- delimiters)")
            return False
        self.ok("YAML frontmatter found")

        if not self.frontmatter.get("status"):
            self.fail("Missing required field: status")
        if not self.frontmatter.get("pipeline"):
            self.fail("Missing required field: pipeline")

        return self.frontmatter.get("status") and self.frontmatter.get("pipeline")

    def _check_pipeline(self, pipeline: str):
        if pipeline in REQUIRED_SECTIONS:
            self.ok(f"Pipeline: {pipeline}")
        elif pipeline:
            self.fail(f"Unknown pipeline variant: {pipeline} (expected: {', '.join(REQUIRED_SECTIONS.keys())})")
        # empty already caught by _check_frontmatter

    def _check_routing_fields(self):
        fm = self.frontmatter

        intent = fm.get("intent", "")
        if intent in VALID_INTENTS:
            self.ok(f"Intent: {intent}")
        elif intent:
            self.fail(f"Invalid intent: {intent} (expected: {', '.join(sorted(VALID_INTENTS))})")
        else:
            self.fail("Missing routing field: intent")

        complexity = fm.get("complexity", "")
        if complexity in VALID_COMPLEXITIES:
            self.ok(f"Complexity: {complexity}")
        elif complexity:
            self.fail(f"Invalid complexity: {complexity} (expected: {', '.join(sorted(VALID_COMPLEXITIES))})")
        else:
            self.fail("Missing routing field: complexity")

        for flag in ["designer_needed", "researcher_needed", "safety_auditor_needed", "arch_advisor_needed"]:
            val = fm.get(flag, "")
            if val in VALID_YES_NO:
                pass  # valid, don't clutter output
            elif val:
                self.fail(f"Invalid {flag}: {val} (expected: YES or NO)")
            else:
                self.warn(f"{flag} not set")

    def _check_branching_fields(self, fm: dict) -> None:
        """parent_branch and parent_sha must appear together or not at all."""
        has_branch = bool(fm.get("parent_branch"))
        has_sha = bool(fm.get("parent_sha"))
        if has_branch != has_sha:
            missing = "parent_sha" if has_branch else "parent_branch"
            present = "parent_branch" if has_branch else "parent_sha"
            self.fail(
                f"YAML frontmatter has {present} but is missing {missing}. "
                f"These two fields are populated together when /keel-pipeline runs "
                f"in stack mode; the pair encodes which branch the feature was "
                f"stacked on (parent_branch) and the SHA of the parent's tip at "
                f"branch-creation time (parent_sha, used for restack detection)."
            )

    def _check_required_sections(self, pipeline: str):
        required = REQUIRED_SECTIONS.get(pipeline, [])
        for section_name in required:
            found = self._find_section(section_name)
            if found and section_has_content(found):
                self.ok(f"{section_name}: non-empty")
            elif found:
                self.fail(f"{section_name}: section exists but is empty")
            else:
                self.fail(f"{section_name}: section missing")

    def _check_conditional_sections(self):
        fm = self.frontmatter
        true_values = {"YES", "true"}

        # Designer is variant-aware. Frontend pipeline already requires
        # frontend-designer unconditionally via REQUIRED_SECTIONS — skip
        # to avoid double-counting. Backend pipeline gates the
        # backend-designer section on designer_needed. Other pipelines
        # (bootstrap, cross-cutting) don't run designers; designer_needed=YES
        # on those is a contract error.
        if fm.get("designer_needed") in true_values:
            pipeline = fm.get("pipeline", "")
            flag_val = fm.get("designer_needed")
            if pipeline == "backend":
                section_name = "backend-designer"
                found = self._find_section(section_name)
                if found and section_has_content(found):
                    self.ok(f"{section_name}: non-empty (required by designer_needed)")
                elif found:
                    self.warn(f"{section_name}: section exists but empty (designer_needed={flag_val})")
                else:
                    self.warn(f"{section_name}: section missing (designer_needed={flag_val})")
            elif pipeline == "frontend":
                pass  # REQUIRED_SECTIONS already enforces frontend-designer
            else:
                self.fail(
                    f"designer_needed={flag_val} is illegal on pipeline={pipeline!r} "
                    f"(only backend and frontend pipelines run designers). "
                    f"Fix: set designer_needed: NO, or change the pipeline variant."
                )

        for flag, section_name in CONDITIONAL_SECTIONS.items():
            if fm.get(flag) in true_values:
                found = self._find_section(section_name)
                flag_val = fm.get(flag)
                if found and section_has_content(found):
                    self.ok(f"{section_name}: non-empty (required by {flag})")
                elif found:
                    self.warn(f"{section_name}: section exists but empty ({flag}={flag_val})")
                else:
                    self.warn(f"{section_name}: section missing ({flag}={flag_val})")

        # The landing review always runs (the review panel is the default),
        # so its deliberation section is expected once review_panel resolves.
        if fm.get("review_panel") in VALID_REVIEW_PANELS:
            found = self._find_section("landing-review")
            panel = fm.get("review_panel")
            if found and section_has_content(found):
                self.ok("landing-review: non-empty (required by review_panel)")
            elif found:
                self.warn(f"landing-review: section exists but empty (review_panel={panel})")
            else:
                self.warn(f"landing-review: section missing (review_panel={panel})")

    def _check_verdicts(self):
        fm = self.frontmatter

        # Karta drops the keel spec-reviewer; its structural conformance gate
        # (karta-spec-reviewer) is enforced via the routing.gates landing floor
        # (_karta_conformance_landing_finding), not this flat-frontmatter check.
        if fm.get("pipeline") != "karta":
            spec_verdict = fm.get("spec_review_verdict", "")
            spec_attempt = fm.get("spec_review_attempt", "0")

            if spec_verdict == "CONFORMANT":
                self.ok(f"spec-reviewer verdict: CONFORMANT (attempt {spec_attempt})")
            elif spec_verdict == "DEVIATION":
                self.fail("spec-reviewer verdict: DEVIATION — cannot land with deviation")
            elif spec_verdict:
                self.fail(f"spec-reviewer verdict invalid: {spec_verdict}")
            else:
                self.fail("spec-reviewer verdict not set (status is LANDED)")

            if spec_attempt not in ("0", ""):
                try:
                    n = int(spec_attempt)
                    if n < 1 or n > 2:
                        self.warn(f"spec_review_attempt={n} (expected 1 or 2)")
                except ValueError:
                    self.fail(f"spec_review_attempt not a number: {spec_attempt}")

        safety_needed = fm.get("safety_auditor_needed", "")
        safety_verdict = fm.get("safety_verdict", "")
        if safety_needed == "YES":
            if safety_verdict == "PASS":
                self.ok("safety-auditor verdict: PASS")
            elif safety_verdict == "VIOLATION":
                self.fail("safety-auditor verdict: VIOLATION — cannot land with violation")
            elif safety_verdict:
                self.fail(f"safety-auditor verdict invalid: {safety_verdict}")
            else:
                self.fail("safety-auditor verdict not set (needed=YES, status=LANDED)")

        arch_needed = fm.get("arch_advisor_needed", "")
        arch_verdict = fm.get("arch_advisor_verdict", "")
        if arch_needed == "YES":
            if arch_verdict == "SOUND":
                self.ok("arch-advisor verdict: SOUND")
            elif arch_verdict == "UNSOUND":
                self.fail("arch-advisor verdict: UNSOUND — cannot land with unsound")
            elif arch_verdict:
                self.fail(f"arch-advisor verdict invalid: {arch_verdict}")
            else:
                self.warn("arch-advisor verdict not set (needed=YES, status=LANDED)")

        # Review-panel verdicts (advisory — warn on CONCERNS, don't fail).
        # The panel always runs (personas by default), so these are checked
        # whenever review_panel resolved to a valid value.
        panel = fm.get("review_panel", "")
        if panel and panel not in VALID_REVIEW_PANELS:
            self.fail(f"review_panel invalid: {panel} (expected: personas or roundtable)")
        elif panel in VALID_REVIEW_PANELS:
            rv_precheck = fm.get("review_precheck_verdict", "")
            if rv_precheck and rv_precheck not in VALID_REVIEW_VERDICTS:
                self.fail(f"review_precheck_verdict invalid: {rv_precheck}")
            elif rv_precheck == "CONCERNS":
                self.warn("pre-check review had unresolved concerns")

            rv_design = fm.get("review_design_verdict", "")
            if rv_design and rv_design not in VALID_REVIEW_VERDICTS:
                self.fail(f"review_design_verdict invalid: {rv_design}")
            elif rv_design == "CONCERNS":
                self.warn("design review had unresolved concerns")

            rv_landing = fm.get("review_landing_verdict", "")
            if rv_landing and rv_landing not in VALID_REVIEW_VERDICTS:
                self.fail(f"review_landing_verdict invalid: {rv_landing}")
            elif rv_landing == "CONCERNS":
                self.warn("landing review had unresolved concerns")

    def _check_status_consistency(self, status: str):
        pipeline = self.frontmatter.get("pipeline", "")
        required = REQUIRED_SECTIONS.get(pipeline, [])
        all_filled = all(
            self._find_section(s) and section_has_content(self._find_section(s))
            for s in required
        )

        if status == "LANDED":
            self.ok("Status: LANDED")
        elif status == "READY-TO-LAND":
            self.ok("Status: READY-TO-LAND")
        elif status == "VERIFIED":
            self.ok("Status: VERIFIED")
        elif status == "IN-PROGRESS" and all_filled:
            self.warn("Status still IN-PROGRESS but all required sections are filled")
        elif status == "IN-PROGRESS":
            self.ok("Status: IN-PROGRESS")
        elif status:
            self.warn(f"Unexpected status: {status}")

    def _check_no_forbidden_siblings(self):
        """Reject `## <agent> (...)` siblings of canonical agent/deliberation sections.

        Under the snapshot rule, agents overwrite their own section on re-run;
        sibling parenthesized headings (e.g. `## pre-check (revised, attempt 2)`)
        are forbidden. Roundtable deliberation sections accumulate
        `### Attempt N` blocks INSIDE the section, not as sibling `##` headings.
        """
        forbidden = []
        for heading in self.section_headings:
            m = FORBIDDEN_SIBLING_RE.match(heading)
            if m:
                forbidden.append((heading, m.group(1)))
        if forbidden:
            for heading, parent in forbidden:
                self.fail(
                    f"Forbidden sibling section: `## {heading}`. Under the snapshot "
                    f"rule, `{parent}` overwrites its own section on re-run; sibling "
                    f"parenthesized headings are not allowed. Fix: REPLACE the "
                    f"contents of `## {parent}` with the latest output and DELETE "
                    f"`## {heading}`."
                )
        else:
            self.ok("No forbidden sibling agent-section headings")

    def _check_no_duplicate_canonical_sections(self):
        """Reject any canonical section appearing more than once at the `##` level.

        The duplicate set covers the same surface as `_PARENT_HEADING_NAMES`
        used by the forbidden-sibling check — including split designer forms
        (`backend-designer`, `frontend-designer`) so a future-disambiguated
        slash heading is also covered.
        """
        canonical = _PARENT_HEADING_NAMES
        counts: dict[str, int] = {}
        for heading in self.section_headings:
            if heading in canonical:
                counts[heading] = counts.get(heading, 0) + 1
        duplicates = {h: n for h, n in counts.items() if n > 1}
        if duplicates:
            for heading, n in duplicates.items():
                self.fail(
                    f"Duplicate section: `## {heading}` appears {n} times. Under "
                    f"the snapshot rule, each agent output section appears exactly "
                    f"once and is overwritten on re-run. Fix: keep the most recent "
                    f"`## {heading}` block (the agent's latest output) and DELETE "
                    f"the {n - 1} earlier duplicate(s)."
                )
        else:
            self.ok("No duplicate canonical sections")

    def _check_attempt_block_format(self):
        """Verify `### Attempt N — <verdict>` block format inside deliberation sections.

        Each `## *-review` section that has any `###` children must have all of
        them match `### Attempt N — <verdict>`. Under the ROUNDTABLE panel
        (`review_panel: roundtable`) each attempt must also carry the panel's
        expected `####` subsections (e.g. Critique + Canvass). The persona panel
        records one line per lens plus synthesized findings with no required
        `####` subsections, so the subsection check is skipped for it.

        A deliberation section with no `###` children at all passes silently.
        Note: `section_has_content` is intentionally NOT used here because it
        strips `### foo` lines before measuring emptiness, which would silently
        skip a malformed attempt block (e.g., `### Attempt 1` with no `####`
        children) — exactly the case this check is meant to catch.
        """
        is_roundtable = self.frontmatter.get("review_panel") == "roundtable"
        any_checked = False
        any_failed = False
        for section_name, expected_subsections in REVIEW_DELIBERATION_SECTIONS.items():
            body = self.sections.get(section_name)
            if body is None:
                continue
            attempt_blocks = extract_subsection_blocks(body, level=3)
            if not attempt_blocks:
                continue  # no `### ` children — empty/note state, allowed
            any_checked = True
            for attempt_heading, attempt_body in attempt_blocks:
                m = ATTEMPT_BLOCK_RE.match(attempt_heading)
                if not m:
                    self.fail(
                        f"`## {section_name}` has `### {attempt_heading}` — does not "
                        f"match `### Attempt N — <verdict>` format. Fix: rename to "
                        f"`### Attempt <number> — APPROVED` (or `CONCERNS`)."
                    )
                    any_failed = True
                    continue
                if not is_roundtable:
                    continue  # persona panel: no required `####` subsections
                actual_subsections = {
                    h for h, _ in extract_subsection_blocks(attempt_body, level=4)
                }
                missing = expected_subsections - actual_subsections
                if missing:
                    needed = sorted(missing)
                    self.fail(
                        f"`## {section_name}` `### {attempt_heading}` is missing "
                        f"required `####` subsections: {needed}. Fix: add "
                        f"{', '.join(f'`#### {s}`' for s in needed)} under this "
                        f"attempt block (each roundtable attempt must carry all of "
                        f"{sorted(expected_subsections)})."
                    )
                    any_failed = True
        if any_checked and not any_failed:
            self.ok("Review-panel deliberation sections: Attempt N block format correct")

    def _find_section(self, name: str) -> str | None:
        """Find a section by exact name. Designer headings are split into
        `## backend-designer` and `## frontend-designer` — direct lookup.

        Legacy fallback (archived handoffs only): a handoff predating the
        slash-heading disambiguation may carry
        `## backend-designer / frontend-designer`. The fallback is
        deliberately gated to `self.archived` so an active handoff with
        only the legacy heading fails its required-section check (forces
        the migration), rather than silently passing under the old shape.
        """
        if name in self.sections:
            return self.sections[name]
        if self.archived and name in ("backend-designer", "frontend-designer"):
            legacy = self.sections.get("backend-designer / frontend-designer")
            if legacy is not None:
                return legacy
        return None


# --- Option H per-directory validation ------------------------------------
#
# A finding is a single structural problem on an Option H handoff directory.
# The legacy single-file path uses HandoffValidator's print-as-you-go ok/
# fail/warn counters; the H path collects HALT findings into a list so a
# directory can report every problem in one pass. Both paths funnel into
# the same exit-code contract in main().


@dataclass(slots=True, frozen=True)
class Finding:
    """One structural problem found on an Option H handoff directory.

    `level` is always "HALT" today (every H-mode check is hard — see the
    design's fail-closed posture); the field exists so a future advisory
    level can be added without reshaping callers. `message` is a P7 CTA:
    it names the cause AND the concrete next step."""
    level: str
    message: str


# Schema files live under <repo_root>/schemas/. Loaded lazily (only the H
# path needs them) and cached per process so a directory-of-dirs sweep does
# not re-read+re-parse the same schema for every child.
_SCHEMA_REL = Path("schemas")
_BACKLOG_REL = Path("docs") / "exec-plans" / "active" / "backlog.md"
_KEEL_JSON_REL = Path("keel.json")
_KEEL_SCHEMA_REL = Path("schemas") / "keel.schema.json"

# Pretriage weighted-scoring rule (design doc §"Pre-triage rule"). MUST stay
# in sync with the resolver's signal vocabulary; recomputed here only to
# verify routing.pretriage consistency against resolved-work-item signals.
_PRETRIAGE_WEIGHTS = {
    "cross_module_touch": 1,
    "security_sensitive_inv": 2,
    "novel_dependency": 2,
    "frozen_seam_impact": 1,
    "architecture_tier_hint": 3,
}
_PRETRIAGE_OPUS_THRESHOLD = 2

_schema_cache: dict[str, dict] = {}


class SchemaNotFound(Exception):
    """Raised when a shipped schema is absent from the resolved repo root.

    Carries a P7 message (cause + concrete next step). _validate_h_handoff
    catches it and renders it as a HALT Finding so an out-of-tree invocation
    exits nonzero with a clean call-to-action instead of a Python traceback.
    `_find_repo_root` documents this as the intended out-of-tree surface."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _load_schema(repo_root: Path, name: str) -> dict:
    """Load and cache a JSON schema by filename from <repo_root>/schemas/.

    Mirrors keel-routing.py's `_load_validator` fail-closed pattern: an
    absent schema is a P7 halt (names the missing file + repo root + the
    concrete next step), not an uncaught FileNotFoundError. This is the
    out-of-tree H-mode surface `_find_repo_root` promises."""
    if name in _schema_cache:
        return _schema_cache[name]
    schema_path = repo_root / _SCHEMA_REL / name
    if not schema_path.is_file():
        raise SchemaNotFound(
            f"schemas/{name} not found from {repo_root}. Run "
            f"validate-handoff.py from a KEEL framework source tree or an "
            f"installed repo where schemas/{name} exists (Option H validation "
            f"recomputes against the shipped schemas).")
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SchemaNotFound(
            f"schemas/{name} not found from {repo_root}. Run "
            f"validate-handoff.py from a KEEL framework source tree or an "
            f"installed repo where schemas/{name} exists (Option H validation "
            f"recomputes against the shipped schemas).")
    _schema_cache[name] = schema
    return schema


def _validate_json_schema(doc: dict, schema_name: str, repo_root: Path) -> None:
    """Validate `doc` against <repo_root>/schemas/<schema_name>.

    Lazy-imports jsonschema so the legacy single-file path stays stdlib-only
    (the stdlib test suite shells this script out under bare python). Raises
    jsonschema.ValidationError on the first error so callers render a HALT.
    """
    import jsonschema  # lazy — H-mode only (see module docstring)

    schema = _load_schema(repo_root, schema_name)
    jsonschema.validators.validator_for(schema)(schema).validate(doc)


def _load_keel_json(repo_root: Path) -> list[str]:
    """Return keel.json's `security_sensitive_invariants`, or [] when absent.

    Mirrors keel-work-item-resolve.py's `_read_keel_security_list` so the
    third source_hash input is byte-identical to what the resolver hashed.
    A present-but-malformed keel.json is schema-validated; a schema failure
    raises (the caller turns it into a HALT) rather than silently degrading
    the security signal. Absent file → [] (the common opt-in case)."""
    keel_path = repo_root / _KEEL_JSON_REL
    if not keel_path.is_file():
        return []
    doc = json.loads(keel_path.read_text(encoding="utf-8"))
    schema_path = repo_root / _KEEL_SCHEMA_REL
    if schema_path.is_file():
        _validate_json_schema(doc, "keel.schema.json", repo_root)
    sec = doc.get("security_sensitive_invariants", [])
    return list(sec) if isinstance(sec, list) else []


def _binder_path_from_ref(binder_ref: str | None, repo_root: Path) -> Path | None:
    """Resolve routing.binder_ref ('…/foo.json#WI22') to an absolute Binder path.

    The `#WI##` fragment is stripped (it names the feature, not a file part).
    Relative refs resolve against repo_root. Returns None when binder_ref is
    null/empty (caller decides whether that is a halt)."""
    if not binder_ref:
        return None
    file_part = binder_ref.split("#", 1)[0]
    p = Path(file_part)
    return p if p.is_absolute() else repo_root / p


def _compute_source_hash(routing: dict, repo_root: Path) -> str:
    """Recompute the resolved-work-item source_hash from current repo state.

    Byte-for-byte mirror of keel-work-item-resolve.py: imports the SAME
    canonical-form helpers from keel_work_items (extract_binder_slice,
    backlog_entry_to_canonical_dict, compute_source_hash) so the three
    inputs and their canonical JSON serialization cannot drift from the
    writer. Reads the Binder from routing.binder_ref and the backlog from the
    canonical active location; the security list from keel.json.

    A missing Binder/backlog yields an empty slice/{} entry — the hash will
    then differ from the stored one, surfacing the staleness as a clear
    mismatch HALT rather than a crash."""
    _SCRIPT_DIR = Path(__file__).resolve().parent
    if str(_SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPT_DIR))
    from keel_work_items import (  # noqa: E402
        BacklogParser,
        Halt,
        backlog_entry_to_canonical_dict,
        compute_source_hash,
        extract_binder_slice,
    )

    feature_id = routing["work_item"]["id"]

    # CONTRACT: routing.binder_ref's file part MUST equal the resolver's canonical
    # Binder path. If it points at a different Binder, this reads a different slice
    # than Step 0 hashed and every validation HALTs on a permanent source_hash
    # mismatch. keel-routing.py init enforces a non-null binder_ref for the same
    # reason (see cmd_init's --binder requirement).
    binder_path = _binder_path_from_ref(routing.get("binder_ref"), repo_root)
    binder_doc: dict = {}
    if binder_path is not None and binder_path.is_file():
        try:
            binder_doc = json.loads(binder_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            binder_doc = {}
    binder_slice = extract_binder_slice(binder_doc, feature_id)

    backlog_path = repo_root / _BACKLOG_REL
    backlog_entry: dict = {}
    if backlog_path.is_file():
        backlog_text = backlog_path.read_text(encoding="utf-8")
        parsed = BacklogParser().parse_entry(backlog_text, feature_id)
        if parsed is not None and not isinstance(parsed, Halt):
            backlog_entry = backlog_entry_to_canonical_dict(parsed)

    security_list = _load_keel_json(repo_root)
    return compute_source_hash(binder_slice, backlog_entry, security_list)


def _score_from_signals(signals: dict) -> int:
    """Weighted pretriage score from resolved-work-item pretriage_inputs.

    Implements the design doc's weighted rule (NOT a flat OR). A truthy
    signal contributes its weight; absent/false contributes 0."""
    return sum(
        weight for key, weight in _PRETRIAGE_WEIGHTS.items()
        if signals.get(key)
    )


def _karta_landing_reached(routing: dict) -> bool:
    """True once a karta handoff has reached Step 9's completion procedure.

    Under repo-local done (schema v5) the routing status enum is only
    IN-PROGRESS|BLOCKED — READY-TO-LAND/LANDED are retired, so the old
    status-based 'landing reached' test is permanently false. Step 9's
    completion procedure records `doc_garden` as its first-instance act
    (sub-step 1, doc-gardener GC), so `doc_garden` present is the
    recorded signal that completion has begun. The karta floors fire from
    this point: a karta handoff that has entered completion must carry its
    recorded safety PASS and conformance CONFORMANT verdicts. (P4: reads a
    first-instance record, not a status cache; the green gate writes no
    routing verdict, so it is not an anchor.)"""
    return "doc_garden" in routing


def _compute_expected_file_set(routing: dict, handoff_dir: Path) -> dict[Path, str]:
    """Return Path → 'why expected' for the routing state's stage.

    STAGE-AWARE: only expects files for stages the routing state shows have
    actually run. Early in the pipeline most files are NOT yet expected, so
    the validator does not fail at Step 0 just because pre-check.md has not
    been written yet.

    Stage signals:
    - routing.routing present      → pre-check has run
    - routing.gates.<name>         → that gate has run
    - routing.review.<tp>.attempt  → that touchpoint's panel ran N times
    - routing.doc_garden present   → completion reached (v5; READY/LANDED retired)
    - routing.doc_garden present   → doc-gardener has run
    """
    expected: dict[Path, str] = {handoff_dir / "routing.json": "always required"}
    pipeline = routing["pipeline"]

    if pipeline == "bootstrap":
        # Bootstrap names its agent in routing.bootstrap_agent (schema makes
        # it required for pipeline=bootstrap). Read it to know which of the
        # three bootstrap agent files to expect.
        bootstrap_agent = routing.get("bootstrap_agent")
        if not bootstrap_agent:
            return expected  # corruption; schema check already flagged it
        if (handoff_dir / f"{bootstrap_agent}.md").exists():
            expected[handoff_dir / f"{bootstrap_agent}.md"] = f"bootstrap_agent: {bootstrap_agent}"
        if routing.get("status") in ("READY-TO-LAND", "LANDED"):
            expected[handoff_dir / "landing-verifier.md"] = "post-bootstrap"
            expected[handoff_dir / "doc-gardener.md"] = "Step 9 sub-step 1"
        return expected

    expected[handoff_dir / "resolved-work-item.json"] = "non-bootstrap"

    # The routing block is written by `keel-routing.py init` as a neutral
    # PLACEHOLDER (all flags false) BEFORE pre-check runs — the schema
    # requires it for non-bootstrap (see keel-routing.py _build_fresh and the
    # schema allOf). So `"routing" in routing` is NOT a reliable "pre-check
    # ran" signal: it is present from Step 0. (The plan sketch keyed on it,
    # but the authoritative init code — P6: code wins — always seeds it.)
    #
    # `pre-check.md` is therefore DEMANDED only once the pipeline has
    # demonstrably progressed past pre-check — i.e. any downstream artifact
    # exists, any gate/review/doc-garden ran, or status reached
    # READY-TO-LAND/LANDED. In the bare Step-0 state (init done, pre-check
    # pending) it is not yet demanded, avoiding a false HALT (P7).
    r = routing.get("routing", {})
    rev = routing.get("review", {})
    g = routing.get("gates", {})
    # Karta (the lean MVP lane) runs no designer; backend → backend-designer,
    # any other designer-running pipeline (frontend) → frontend-designer.
    designer = (
        None if pipeline == "karta"
        else "backend-designer.md" if pipeline == "backend"
        else "frontend-designer.md"
    )
    _progress_artifacts = (
        "pre-check.md", "researcher.md", "arch-advisor-consult.md",
        "test-writer.md", "implementer.md",
        "landing-verifier.md", "doc-gardener.md",
    ) + ((designer,) if designer else ())
    _progressed = (
        bool(g)
        or "doc_garden" in routing
        or routing.get("status") in ("READY-TO-LAND", "LANDED")
        or any(rev.get(tp, {}).get("attempt", 0) >= 1 for tp in ("precheck", "design", "landing"))
        or any((handoff_dir / name).exists() for name in _progress_artifacts)
    )
    if not _progressed:
        return expected  # bare Step-0 state: only routing + resolved-work-item

    expected[handoff_dir / "pre-check.md"] = "pre-check ran (pipeline progressed past Step 1)"

    # Review subdirs are expected only AFTER first attempt.
    if rev.get("precheck", {}).get("attempt", 0) >= 1:
        expected[handoff_dir / "precheck-review"] = "precheck attempt >= 1"
    if rev.get("design", {}).get("attempt", 0) >= 1:
        expected[handoff_dir / "design-review"] = "design attempt >= 1"
    if rev.get("landing", {}).get("attempt", 0) >= 1:
        expected[handoff_dir / "landing-review"] = "landing attempt >= 1"

    if r.get("researcher_needed") and (handoff_dir / "researcher.md").exists():
        expected[handoff_dir / "researcher.md"] = "researcher ran"
    if r.get("arch_advisor_needed") and (handoff_dir / "arch-advisor-consult.md").exists():
        expected[handoff_dir / "arch-advisor-consult.md"] = "arch-advisor-consult ran"
    if designer and (handoff_dir / designer).exists():
        expected[handoff_dir / designer] = "designer ran"
    if (handoff_dir / "test-writer.md").exists():
        expected[handoff_dir / "test-writer.md"] = "test-writer ran"

    if r.get("implementer_needed") and (handoff_dir / "implementer.md").exists():
        expected[handoff_dir / "implementer.md"] = "implementer ran"
    if "code_review" in g:
        expected[handoff_dir / "code-reviewer.md"] = "gate verdict recorded"
    if "spec_review" in g:
        expected[handoff_dir / "spec-reviewer.md"] = "gate verdict recorded"
    if "safety" in g:
        expected[handoff_dir / "safety-auditor.md"] = "gate verdict recorded"
    if "conformance" in g:
        expected[handoff_dir / "karta-spec-reviewer.md"] = "gate verdict recorded"
    if "arch_verify" in g:
        expected[handoff_dir / "arch-advisor-verify.md"] = "gate verdict recorded"

    # Karta: safety-auditor is the lane's one mandatory review gate, and there
    # is no landing-verifier to vouch for it. Demand its evidence once the
    # feature reaches Step 9's completion procedure (doc_garden recorded),
    # even if routing.gates.safety was not recorded — a karta handoff must not
    # complete without it. (v5: status no longer latches READY-TO-LAND/LANDED;
    # the recorded completion signal is doc_garden — see _karta_landing_reached.)
    if pipeline == "karta" and _karta_landing_reached(routing):
        expected[handoff_dir / "karta-spec-reviewer.md"] = "karta: structural conformance gate mandatory before landing"
        expected[handoff_dir / "safety-auditor.md"] = "karta: safety gate mandatory before landing"
        expected[handoff_dir / "implementer.md"] = "karta: the implementer is the lane's build step, required at landing"

    if (handoff_dir / "landing-verifier.md").exists():
        expected[handoff_dir / "landing-verifier.md"] = "landing-verifier ran"

    if "doc_garden" in routing:
        expected[handoff_dir / "doc-gardener.md"] = "doc-gardener ran"

    return expected


def _karta_safety_landing_finding(routing: dict, handoff_dir: Path) -> "Finding | None":
    """Karta's mechanical safety floor at landing.

    The lean karta lane drops `landing-verifier`, so nothing else mechanically
    re-checks the safety verdict before landing. Its one mandatory review gate
    is `safety-auditor`; a karta handoff must therefore not reach
    completion (doc_garden recorded) unless `routing.gates.safety.verdict` is a recorded
    `PASS`. (Other pipelines lean on landing-verifier + the orchestrator for
    this; karta has neither backstop.) Returns a HALT Finding if the floor is
    not met, else None. Pure — unit-tested directly."""
    if routing.get("pipeline") != "karta":
        return None
    if not _karta_landing_reached(routing):
        return None
    verdict = routing.get("gates", {}).get("safety", {}).get("verdict")
    if verdict == "PASS":
        return None
    return Finding("HALT",
        f"{handoff_dir}: karta handoff has reached completion (doc_garden "
        f"recorded) but routing.gates.safety.verdict is {verdict!r}, not 'PASS'. The karta "
        f"lane cannot land without a passing safety-auditor verdict (it has no "
        f"landing-verifier backstop). Fix: resolve the violation and re-run "
        f"safety-auditor, or do not advance the status.")


def _karta_conformance_landing_finding(routing: dict, handoff_dir: Path) -> "Finding | None":
    """Karta's mechanical structural-conformance floor at landing.

    The spec-first karta lane makes karta-spec-reviewer (the structural
    conformance gate) a mandatory blocking gate. Like the safety floor, nothing
    else mechanically re-checks it before landing (no landing-verifier). A karta
    handoff must therefore not reach completion (doc_garden recorded) unless
    `routing.gates.conformance.verdict` is a recorded `CONFORMANT`. A DEVIATION
    loops back to the implementer and a SPEC-SUSPECT halts for human
    adjudication — neither is a landing state. Returns a HALT Finding if the
    floor is not met, else None. Pure — unit-tested directly."""
    if routing.get("pipeline") != "karta":
        return None
    if not _karta_landing_reached(routing):
        return None
    verdict = routing.get("gates", {}).get("conformance", {}).get("verdict")
    if verdict == "CONFORMANT":
        return None
    return Finding("HALT",
        f"{handoff_dir}: karta handoff has reached completion (doc_garden "
        f"recorded) but routing.gates.conformance.verdict is {verdict!r}, not 'CONFORMANT'. The "
        f"spec-first karta lane cannot land without a CONFORMANT structural "
        f"conformance verdict from karta-spec-reviewer (it has no landing-verifier "
        f"backstop). A DEVIATION must be fixed and re-reviewed; a SPEC-SUSPECT must "
        f"be adjudicated via /keel-refine. Fix the verdict or do not advance the status.")


def _parse_attempt_n(filename: str) -> int:
    m = re.match(r"attempt-(\d+)\.md", filename)
    return int(m.group(1)) if m else -1


def _validate_deliberation_subdir(sub: Path, expected_attempts: int) -> list[Finding]:
    """Validate one review-panel deliberation subdir (append-only contract).

    FAIL-CLOSED (design §"Append-only invariant"): the "enforced by content
    hash" guarantee is only real if a missing sidecar OR a missing per-attempt
    entry HALTs. A fail-open check that skips when the sidecar is absent is
    silently defeated by deleting the sidecar; short-circuiting on un-recorded
    entries leaves a crash-window attempt unprotected. The orchestrator records
    each attempt's hash as the very next action after writing attempt-NN.md, so
    a missing hash means a crash between those two steps or a non-compliant
    writer — both real integrity failures. Each HALT carries a heal CTA (P7)."""
    findings: list[Finding] = []
    files = sorted(sub.glob("attempt-*.md"), key=lambda p: _parse_attempt_n(p.name))
    n_actual = len(files)
    if n_actual != expected_attempts:
        findings.append(Finding("HALT",
            f"{sub}: expected {expected_attempts} attempt file(s) "
            f"(routing.review.<tp>.attempt), found {n_actual}. Fix: re-run "
            f"the touchpoint so each attempt appends an attempt-NN.md, or "
            f"correct routing's attempt count via keel-routing.py."))
    # Filenames zero-padded; body opens with the canonical attempt heading.
    for i, f in enumerate(files, start=1):
        expected_name = f"attempt-{i:02d}.md"
        if f.name != expected_name:
            findings.append(Finding("HALT",
                f"{f}: expected name {expected_name} (zero-padded, "
                f"gap-free). Fix: rename so attempt files run "
                f"attempt-01.md, attempt-02.md, … with no gaps."))
        first_line = f.read_text(encoding="utf-8").splitlines()[0] if f.stat().st_size > 0 else ""
        if not re.match(rf"^### Attempt {i} — (APPROVED|CONCERNS)$", first_line):
            findings.append(Finding("HALT",
                f"{f}: first line must be '### Attempt {i} — <VERDICT>' "
                f"(VERDICT one of APPROVED, CONCERNS). Fix: set the opening "
                f"heading to match the attempt number and a valid verdict."))

    # Content-hash sidecar check (append-only contract; fail-closed).
    touchpoint = sub.name.rsplit("-", 1)[0]  # "precheck-review" -> "precheck"
    sidecar = sub / ".attempt-hashes.json"
    if files and not sidecar.exists():
        findings.append(Finding("HALT",
            f"{sub}: {len(files)} attempt file(s) present but no "
            f".attempt-hashes.json integrity record (crash between the "
            f"attempt write and the hash record, or a non-compliant writer). "
            f"Heal: re-run `uv run scripts/keel-routing.py record-attempt-hash "
            f"{sub.parent} {touchpoint} <N>` for each attempt N."))
        return findings  # can't verify individual hashes without the sidecar
    recorded = json.loads(sidecar.read_text(encoding="utf-8")) if sidecar.exists() else {}
    for f in files:
        if f.name not in recorded:
            findings.append(Finding("HALT",
                f"{f}: no recorded hash in .attempt-hashes.json (crash "
                f"between the attempt write and the hash record?). Heal: "
                f"re-run `uv run scripts/keel-routing.py record-attempt-hash "
                f"{sub.parent} {touchpoint} {_parse_attempt_n(f.name)}`."))
            continue
        if recorded[f.name] != hashlib.sha256(f.read_bytes()).hexdigest():
            # Past attempt was modified — append-only violation.
            findings.append(Finding("HALT",
                f"{f}: content changed since first write (append-only "
                f"violation). Restore the original from git history; if the "
                f"change is intended, re-run the touchpoint to produce a NEW "
                f"attempt block rather than editing a past one."))
    return findings


def _validate_h_handoff(handoff_dir: Path, repo_root: Path) -> list[Finding]:
    """Validate one Option H per-feature handoff directory.

    Returns a list of HALT Findings (empty = clean). A SchemaNotFound (raised
    when run out-of-tree, where no ancestor ships `schemas/`) is rendered as a
    single HALT Finding so the caller exits nonzero with a P7 call-to-action
    instead of a Python traceback — the out-of-tree surface `_find_repo_root`
    promises."""
    try:
        return _validate_h_handoff_inner(handoff_dir, repo_root)
    except SchemaNotFound as e:
        return [Finding("HALT", f"{handoff_dir}: {e.message}")]


def _validate_h_handoff_inner(handoff_dir: Path, repo_root: Path) -> list[Finding]:
    """Run the structural checks for one Option H handoff directory.

    Returns a list of HALT Findings (empty = clean). jsonschema is imported
    lazily inside _validate_json_schema so this module's legacy single-file
    path stays stdlib-only."""
    import jsonschema  # lazy — H-mode only (see module docstring)

    findings: list[Finding] = []

    # 1. routing.json exists.
    routing_path = handoff_dir / "routing.json"
    if not routing_path.exists():
        return [Finding("HALT",
            f"{handoff_dir}: missing routing.json (required for every Option "
            f"H handoff directory). Fix: run `uv run scripts/keel-routing.py "
            f"init {handoff_dir} …` to materialize it.")]
    # P5: archived handoffs under completed/handoffs/ are frozen history. A
    # frozen v4 routing.json (status LANDED, pr_url, branch.remote_name) is
    # validated for JSON well-formedness only — NOT re-judged against current
    # floors: not the v5 routing schema, not the source_hash recompute, and not
    # the stage-aware expected-file-set (a LANDED archive trips _progressed and
    # would demand pre-check.md/landing-verifier.md that the frozen dir need not
    # carry). Done-ness is the path (completed/handoffs/), not the schema. Same
    # grandfather the legacy .md path applies (is_archived_handoff + the
    # self.archived structural-check skip).
    archived = is_archived_handoff(handoff_dir)
    try:
        routing = json.loads(routing_path.read_text(encoding="utf-8"))
        if not archived:
            _validate_json_schema(routing, "routing.schema.json", repo_root)
    except (json.JSONDecodeError, jsonschema.ValidationError) as e:
        return [Finding("HALT",
            f"{routing_path}: failed routing.schema.json validation: {e}. "
            f"Fix: repair routing.json (it is mutated only via "
            f"keel-routing.py; a hand-edit likely broke the shape).")]
    if archived:
        return findings  # frozen: well-formed JSON is the only floor (P5)

    pipeline = routing["pipeline"]

    # 2. resolved-work-item.json exists + schema-validates (skip bootstrap).
    rf: dict = {}
    if pipeline != "bootstrap":
        rf_path = handoff_dir / "resolved-work-item.json"
        if not rf_path.exists():
            return [Finding("HALT",
                f"{handoff_dir}: missing resolved-work-item.json (required for "
                f"non-bootstrap pipelines). Fix: run `uv run "
                f"scripts/keel-work-item-resolve.py … --v2-schema --output "
                f"{rf_path}` (Step 0), then re-run keel-routing.py init.")]
        try:
            rf = json.loads(rf_path.read_text(encoding="utf-8"))
            _validate_json_schema(rf, "resolved-work-item.schema.json", repo_root)
        except (json.JSONDecodeError, jsonschema.ValidationError) as e:
            return [Finding("HALT",
                f"{rf_path}: failed resolved-work-item.schema.json validation: "
                f"{e}. Fix: re-run Step 0 (keel-work-item-resolve.py "
                f"--v2-schema --output) to regenerate; do not hand-edit.")]

        # 3. Source-hash recompute — HALT on mismatch (not warn).
        try:
            actual_hash = _compute_source_hash(routing, repo_root)
        except (ValueError, json.JSONDecodeError) as e:
            findings.append(Finding("HALT",
                f"{handoff_dir}: could not recompute source_hash ({e}). "
                f"Fix: ensure keel.json (if present) validates against "
                f"schemas/keel.schema.json, then re-run Step 0."))
        else:
            stored = rf.get("source_hash", "")
            if actual_hash != stored:
                findings.append(Finding("HALT",
                    f"{handoff_dir}: source_hash mismatch (expected "
                    f"{actual_hash[:12]}, stored {stored[:12]}). The Binder slice, "
                    f"backlog entry, or keel.json security list changed since "
                    f"Step 0. Fix: re-run `uv run scripts/keel-work-item-resolve.py "
                    f"… --v2-schema --output {handoff_dir / 'resolved-work-item.json'}`, "
                    f"then re-run keel-routing.py init (which invalidates stale "
                    f"derived state)."))

    # 4. File existence + non-empty consistency (stage-aware).
    expected = _compute_expected_file_set(routing, handoff_dir)
    for path, why in expected.items():
        if not path.exists():
            findings.append(Finding("HALT",
                f"{handoff_dir}: missing {path.name} (expected because {why}). "
                f"Fix: re-run the stage that writes it, or correct routing.json "
                f"if the stage did not actually run."))
        elif path.is_file() and path.stat().st_size == 0:
            findings.append(Finding("HALT",
                f"{handoff_dir}: {path.name} exists but is empty (expected "
                f"because {why}). Fix: re-run the stage that writes it so the "
                f"file carries real output."))

    # 4b. Karta safety floor: no landing without a recorded safety PASS.
    if (f := _karta_safety_landing_finding(routing, handoff_dir)) is not None:
        findings.append(f)

    # 4c. Karta structural-conformance floor: no landing without a recorded
    #     CONFORMANT verdict from karta-spec-reviewer (spec-first lane).
    if (f := _karta_conformance_landing_finding(routing, handoff_dir)) is not None:
        findings.append(f)

    # 5. No stray files (sensible exclusions: dotfiles, editor swap/backup,
    #    and the deliberation hash sidecar live inside subdirs anyway).
    ignore_patterns = (".*", "*.swp", "*.swo", "*.tmp", "*.bak", "*~")
    for child in handoff_dir.iterdir():
        if any(fnmatch.fnmatch(child.name, pat) for pat in ignore_patterns):
            continue
        if child not in expected:
            findings.append(Finding("HALT",
                f"{handoff_dir}: stray file/dir {child.name} (not expected "
                f"for pipeline={pipeline} at this stage). Fix: remove it, or "
                f"if it is a real artifact, record the stage in routing.json "
                f"so the expected-file-set accounts for it."))

    # 6. Deliberation subdir structure (append-only, fail-closed).
    for touchpoint in ("precheck-review", "design-review", "landing-review"):
        sub = handoff_dir / touchpoint
        if not sub.exists():
            continue
        tp_key = touchpoint.split("-")[0]  # "precheck-review" -> "precheck"
        attempts = routing.get("review", {}).get(tp_key, {}).get("attempt", 0)
        findings.extend(_validate_deliberation_subdir(sub, attempts))

    # 7. Pretriage consistency (with bypass sentinels).
    pretriage = routing.get("pretriage")
    if pretriage and pipeline != "bootstrap":
        reason = pretriage.get("reason", "")
        if "self-escalated" in reason or "backlog missing" in reason:
            pass  # legitimate override — skip the recompute check
        else:
            computed_score = _score_from_signals(rf.get("pretriage_inputs", {}))
            computed_model = "opus" if computed_score >= _PRETRIAGE_OPUS_THRESHOLD else "sonnet"
            if computed_model != pretriage["recommended_model"]:
                findings.append(Finding("HALT",
                    f"{handoff_dir}: pretriage inconsistency — routing stores "
                    f"recommended_model={pretriage['recommended_model']} "
                    f"(score {pretriage['score']}), but recomputing from "
                    f"resolved-work-item.pretriage_inputs yields {computed_model} "
                    f"(score {computed_score}). Fix: re-run keel-routing.py "
                    f"set-pretriage from the resolved-work-item signals, or add a "
                    f"bypass reason ('self-escalated'/'backlog missing') if this "
                    f"is a deliberate override."))

    return findings


def _print_h_result(handoff_dir: Path, findings: list[Finding]) -> bool:
    """Print the H-mode result for one directory; return True iff clean."""
    print(f"\n{BOLD}Validating (Option H):{RESET} {handoff_dir}")
    if not findings:
        print(f"  {OK} all structural checks passed")
        print(f"\n  {GREEN}{BOLD}Result: PASS{RESET}\n")
        return True
    for f in findings:
        print(f"  {FAIL} {f.message}")
    print(f"\n  {RED}{BOLD}Result: FAIL{RESET} ({len(findings)} halt(s))\n")
    return False


# --- Layout detection ------------------------------------------------------


def _is_h_handoff_dir(path: Path) -> bool:
    """True if `path` is an Option H per-feature directory (has routing.json)."""
    return path.is_dir() and (path / "routing.json").is_file()


def _find_repo_root(start: Path) -> Path:
    """Walk up from `start` to the directory containing `schemas/`.

    Option H handoff dirs live at <repo>/docs/exec-plans/active/handoffs/WI##-…/,
    so the repo root is the nearest ancestor that holds the shipped `schemas/`
    directory. Falls back to `start` (the deepest candidate) when no ancestor
    qualifies — the schema load then HALTs with a clear file-not-found, which
    is the correct P7 surface for an out-of-tree invocation."""
    cur = start if start.is_dir() else start.parent
    cur = cur.resolve()
    for candidate in (cur, *cur.parents):
        if (candidate / "schemas" / "routing.schema.json").is_file():
            return candidate
    return cur


# --- Main ---


def _validate_legacy_file(path: Path) -> bool:
    """Run the legacy single-file (`.md`) validator. Pure stdlib."""
    return HandoffValidator(path).validate()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)

    target = Path(sys.argv[1])

    # Build the list of (kind, path) units to validate.
    units: list[tuple[str, Path]] = []

    if target.is_file():
        units.append(("legacy", target))
    elif _is_h_handoff_dir(target):
        # A single Option H per-feature directory.
        units.append(("h", target))
    elif target.is_dir():
        # A directory of handoffs. Each child is either an H per-feature dir
        # (contains routing.json) or a legacy single-file .md handoff.
        for child in sorted(target.iterdir()):
            if _is_h_handoff_dir(child):
                units.append(("h", child))
            elif child.is_file() and child.suffix == ".md" and child.name != "_TEMPLATE.md":
                units.append(("legacy", child))
        if not units:
            print(
                f"No handoff files or Option H directories found in {target}. "
                f"Fix: pass a single handoff (`WI##-<slug>.md` or `WI##-<slug>/` "
                f"with routing.json) or a directory containing them."
            )
            sys.exit(2)
    else:
        print(
            f"Not found: {target}. Fix: pass a path to a handoff file, an "
            f"Option H handoff directory, or a directory of handoffs."
        )
        sys.exit(2)

    all_passed = True
    for kind, path in units:
        if kind == "legacy":
            if not _validate_legacy_file(path):
                all_passed = False
        else:
            repo_root = _find_repo_root(path)
            findings = _validate_h_handoff(path, repo_root)
            if not _print_h_result(path, findings):
                all_passed = False

    if len(units) > 1:
        color = GREEN if all_passed else RED
        print(f"{color}{BOLD}{'All passed' if all_passed else 'Some failed'}{RESET} ({len(units)} handoffs)\n")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
