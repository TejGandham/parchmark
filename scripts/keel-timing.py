#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# ///
"""KEEL pipeline timing report — per-stage wall-clock for a feature run.

Reads the local SQLite database written by .keel/hooks/keel-timing-hook.py
and prints where a pipeline run spent its time, stage by stage.

    uv run scripts/keel-timing.py              # latest run (same as --last)
    uv run scripts/keel-timing.py --last       # latest run
    uv run scripts/keel-timing.py --list       # captured sessions
    uv run scripts/keel-timing.py --session ID
    uv run scripts/keel-timing.py --json

Output splits stage time into agent stages (Agent/Task dispatches) vs MCP
stages (mcp__* tool calls, e.g. roundtable reviews) so roundtable cost is
explicit; the split appears in --json under "categories" too. The catch-all
hook also captures every ordinary tool call (Bash, Edit, …); those are
summarized as a single "other tool calls" count for now — full gap-binning
across them is a later iteration.

The hook now fires across the FULL Claude Code lifecycle, not just tool
calls, so the inter-agent gap (where ~74% of wall-clock lives) can be
decomposed. Non-tool lifecycle events — orchestrator turns (Stop), user
prompts, context compaction (Pre/PostCompact), permission/notification waits,
and session boundaries — are tallied in a "lifecycle" section of the summary
(and a "lifecycle" block in --json, with a raw per-event "by_event" map).

Timing is local, ephemeral runtime data (P5) — never committed. The DB
lives at .keel/timing/timing.db. Halts with a call-to-action when
no timing has been captured yet.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

LOG_DIR = Path(".keel/timing")
DB_PATH = LOG_DIR / "timing.db"
SUBAGENT_TOOLS = {"Task", "Agent"}
MCP_PREFIX = "mcp__"
START_EVENT = "PreToolUse"
END_EVENTS = ("PostToolUse", "PostToolUseFailure")
TOOL_EVENTS = frozenset({START_EVENT, *END_EVENTS})

# Stage categories used by the summary split.
CAT_AGENT = "agent"   # subagent dispatches (Agent/Task)
CAT_MCP = "mcp"       # MCP tool calls (mcp__*), e.g. roundtable reviews
CAT_OTHER = "other"   # every other tool call (Bash, Edit, …)

# Lifecycle (non-tool) events — the rest of the Claude Code lifecycle, which
# is where the bulk of the inter-agent "gap" lives. These rows carry NO tool
# (the tool column is NULL); the catch-all hook records them so the reporter
# can decompose orchestrator turns, compaction, waits, and session bounds.
# Grouped for the human summary; raw per-event counts go in --json.
LIFECYCLE_GROUPS: list[tuple[str, str, tuple[str, ...]]] = [
    # (json key, human label, member event names)
    ("turns", "turns (Stop)", ("Stop",)),
    ("prompts", "user prompts", ("UserPromptSubmit",)),
    ("compactions", "compactions (Pre/Post)", ("PreCompact", "PostCompact")),
    ("waits", "permission/notify waits",
     ("PermissionRequest", "PermissionDenied", "Notification")),
    ("session", "session start/end", ("SessionStart", "SessionEnd")),
    ("stop_failures", "stop failures", ("StopFailure",)),
    ("tool_batches", "tool batches", ("PostToolBatch",)),
]
# Every lifecycle event name the reporter recognises (anything else with a
# NULL tool is bucketed under "other lifecycle").
LIFECYCLE_EVENTS = frozenset(
    ev for _k, _l, members in LIFECYCLE_GROUPS for ev in members
)


@dataclass(slots=True, frozen=True)
class Event:
    ts_ms: int
    kind: str          # "start" | "end"
    label: str
    corr: str          # correlation id, or ""
    category: str      # "agent" | "mcp" | "other"


@dataclass(slots=True, frozen=True)
class Stage:
    label: str
    start_ms: int
    end_ms: int
    category: str      # "agent" | "mcp"

    @property
    def dur_ms(self) -> int:
        return max(0, self.end_ms - self.start_ms)


def _category(tool: str | None) -> str:
    if isinstance(tool, str) and tool.startswith(MCP_PREFIX):
        return CAT_MCP
    if tool in SUBAGENT_TOOLS:
        return CAT_AGENT
    return CAT_OTHER


def _label(tool: str | None, agent: str | None) -> str:
    # MCP tools self-describe: label by the tool's last __-delimited segment
    # (e.g. mcp__roundtable__roundtable-critique -> roundtable-critique).
    if isinstance(tool, str) and tool.startswith(MCP_PREFIX):
        seg = tool.rsplit("__", 1)[-1].strip()
        if seg:
            return seg
    if isinstance(agent, str) and agent.strip():
        return agent.strip()
    if isinstance(tool, str) and tool.strip():
        return tool.strip()
    return "agent"


def _kind(event: str, category: str) -> str:
    """Map (hook event, category) to a stage boundary for agent/mcp calls.

    Only agent and mcp calls become stage boundaries; "other" calls are
    counted separately, not paired into stages.
    """
    if category == CAT_OTHER:
        return ""
    if event == START_EVENT:
        return "start"
    if event in END_EVENTS:
        return "end"
    return ""


def _connect(db: Path) -> sqlite3.Connection:
    # Read-only; uri mode avoids creating the file if it's absent.
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _rows(con: sqlite3.Connection, session: str) -> list[sqlite3.Row]:
    cur = con.execute(
        "SELECT ts_ms, event, tool, tool_use_id, agent FROM events "
        "WHERE session = ? ORDER BY ts_ms",
        (session,),
    )
    return cur.fetchall()


def _events(rows: list[sqlite3.Row]) -> tuple[list[Event], int, dict[str, int]]:
    """Build stage-boundary Events and tally non-stage activity.

    Returns (boundary_events, other_tool_calls, lifecycle_counts):
      - boundary_events: agent/mcp start|end Events that pair into stages.
      - other_tool_calls: ordinary tool calls (Bash, Edit, …), one-per-call
        via their PreToolUse event.
      - lifecycle_counts: per-event-name counts of NON-tool lifecycle events
        (Stop, UserPromptSubmit, Pre/PostCompact, waits, session bounds …).

    A row is a tool row iff it carries a tool name. Rows with a NULL tool are
    lifecycle events (the catch-all hook records the whole lifecycle); they
    are tallied by event name, never paired into stages.
    """
    events: list[Event] = []
    other_calls = 0
    lifecycle: dict[str, int] = {}
    for r in rows:
        tool = r["tool"]
        if not (isinstance(tool, str) and tool):
            # No tool → lifecycle event. Count by event name so the reporter
            # can decompose the inter-agent gap (turns, compaction, waits…).
            ev = r["event"]
            if isinstance(ev, str) and ev:
                lifecycle[ev] = lifecycle.get(ev, 0) + 1
            continue
        cat = _category(tool)
        if cat == CAT_OTHER:
            if r["event"] == START_EVENT:
                other_calls += 1
            continue
        kind = _kind(r["event"], cat)
        if not kind:
            continue
        try:
            ts = int(r["ts_ms"])
        except (TypeError, ValueError):
            continue
        events.append(Event(ts, kind, _label(tool, r["agent"]),
                            str(r["tool_use_id"] or ""), cat))
    events.sort(key=lambda e: e.ts_ms)
    return events, other_calls, lifecycle


def _lifecycle_summary(counts: dict[str, int]) -> tuple[list[tuple[str, str, int]], int]:
    """Group raw per-event lifecycle counts into the human summary buckets.

    Returns (rows, other) where rows is [(json_key, human_label, count), …]
    for the known groups (only groups with a nonzero count), and `other` is
    the total count of lifecycle events not in any known group.
    """
    grouped: list[tuple[str, str, int]] = []
    accounted = 0
    for key, label, members in LIFECYCLE_GROUPS:
        n = sum(counts.get(ev, 0) for ev in members)
        accounted += n
        if n:
            grouped.append((key, label, n))
    other = sum(counts.values()) - accounted
    return grouped, other


def _pair(starts: list[Event], ends: list[Event]) -> list[Stage]:
    """Match each end to a start: by correlation id when present, else
    FIFO within the same agent label."""
    by_corr = {e.corr: e for e in starts if e.corr}
    used_corr: set[str] = set()
    fifo: dict[str, list[Event]] = {}
    for s in starts:
        fifo.setdefault(s.label, []).append(s)
    stages: list[Stage] = []
    for e in ends:
        s = None
        if e.corr and e.corr in by_corr and e.corr not in used_corr:
            s = by_corr[e.corr]
            used_corr.add(e.corr)
        elif fifo.get(e.label):
            s = fifo[e.label].pop(0)
        stages.append(Stage(e.label, s.ts_ms if s else e.ts_ms, e.ts_ms, e.category))
    stages.sort(key=lambda st: st.start_ms)
    return stages


def _consecutive(boundaries: list[Event], t0: int) -> list[Stage]:
    stages, prev = [], t0
    for b in boundaries:
        stages.append(Stage(b.label, prev, b.ts_ms, b.category))
        prev = b.ts_ms
    return stages


def _stages(events: list[Event]) -> tuple[list[Stage], str]:
    starts = [e for e in events if e.kind == "start"]
    ends = [e for e in events if e.kind == "end"]
    if starts and ends:
        return _pair(starts, ends), "start/stop pairs (exact)"
    if ends:
        return (_consecutive(ends, events[0].ts_ms),
                "stop-to-stop (approx; stage 1 start uncaptured, includes orchestration gaps)")
    if starts:
        return (_consecutive(starts, events[0].ts_ms),
                "start-to-start (approx; last stage open)")
    return [], "no boundary events"


def _category_split(stages: list[Stage]) -> dict[str, int]:
    """Total stage duration by category, so roundtable (MCP) cost is
    explicit against agent-dispatch cost. Always returns both keys."""
    split = {CAT_AGENT: 0, CAT_MCP: 0}
    for st in stages:
        split[st.category if st.category in split else CAT_AGENT] += st.dur_ms
    return split


def _fmt(ms: int) -> str:
    s = ms // 1000
    if s < 60:
        return f"{s}s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}m{s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m{s:02d}s"


def _sessions() -> list[tuple[str, int, int]]:
    """Return (session, n_boundary_events, span_ms) per session, latest first.

    Latest-first is ordered by the session's max ts_ms. n_boundary_events
    counts agent/mcp boundary rows (the ones that form stages), matching
    what `_events` consumes.
    """
    if not DB_PATH.is_file():
        return []
    try:
        con = _connect(DB_PATH)
    except sqlite3.Error:
        return []
    try:
        sess = [r[0] for r in con.execute(
            "SELECT session FROM events GROUP BY session ORDER BY MAX(ts_ms) DESC"
        ).fetchall()]
        out: list[tuple[str, int, int]] = []
        for s in sess:
            rows = _rows(con, s)
            events, _, _ = _events(rows)
            span = (events[-1].ts_ms - events[0].ts_ms) if events else 0
            out.append((s, len(events), span))
        return out
    except sqlite3.Error:
        return []
    finally:
        con.close()


def _no_data() -> None:
    sys.stderr.write(
        "No KEEL timing data found at .keel/timing/timing.db.\n\n"
        "Timing is opt-in. Enable it in the environment of the pipeline run,\n"
        "then run a feature through the pipeline:\n\n"
        "    KEEL_TIMING=1\n\n"
        "The keel-timing hook then records every tool call and lifecycle\n"
        "event automatically; re-run this report afterward. If a run completed\n"
        "with KEEL_TIMING set but produced no database, confirm the hook is\n"
        "registered in .claude/settings.json (catch-all across tool and\n"
        "lifecycle events — each entry the standard {matcher, hooks:[…]} shape\n"
        "with matcher \"\", all async true) and re-run the installer.\n"
    )
    raise SystemExit(2)


def _report(session: str, as_json: bool) -> None:
    try:
        con = _connect(DB_PATH)
    except sqlite3.Error:
        _no_data()
    try:
        rows = _rows(con, session)
    finally:
        con.close()
    events, other_calls, lifecycle = _events(rows)
    if not events and not other_calls and not lifecycle:
        _no_data()
    stages, method = _stages(events)
    span = (events[-1].ts_ms - events[0].ts_ms) if events else 0
    stage_sum = sum(st.dur_ms for st in stages)
    overlap = max(0, stage_sum - span)
    split = _category_split(stages)
    life_rows, life_other = _lifecycle_summary(lifecycle)

    if as_json:
        import json
        # Lifecycle block: grouped counts (only nonzero groups) + a raw
        # per-event map, so downstream tooling can both read the summary and
        # drill into specific event names.
        life_block: dict[str, object] = {
            key: n for key, _label, n in life_rows
        }
        if life_other:
            life_block["other"] = life_other
        life_block["by_event"] = dict(sorted(lifecycle.items()))
        json.dump({
            "session": session, "method": method, "span_ms": span,
            "stage_sum_ms": stage_sum, "overlap_ms": overlap,
            "categories": {
                "agent_ms": split[CAT_AGENT],
                "mcp_ms": split[CAT_MCP],
            },
            "other_tool_calls": other_calls,
            "lifecycle": life_block,
            "stages": [
                {"n": i + 1, "agent": st.label, "category": st.category,
                 "dur_ms": st.dur_ms, "share": (st.dur_ms / span if span else 0)}
                for i, st in enumerate(stages)
            ],
        }, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return

    print(f"KEEL pipeline timing — session {session}")
    print(f"{len(stages)} stages · total span {_fmt(span)} · method: {method}")
    print()
    print(f"{'#':>2}  {'stage':<24}{'cat':>5}{'duration':>10}{'share':>8}")
    for i, st in enumerate(stages, 1):
        share = f"{(st.dur_ms / span * 100):.0f}%" if span else "-"
        print(f"{i:>2}  {st.label[:24]:<24}{st.category:>5}"
              f"{_fmt(st.dur_ms):>10}{share:>8}")
    print(f"{'':>2}  {'-' * 24}")
    print(f"{'':>2}  {'sum of stages':<24}{'':>5}{_fmt(stage_sum):>10}")
    if overlap:
        print(f"{'':>2}  {'parallel overlap':<24}{'':>5}{_fmt(overlap):>10}")
    print(f"{'':>2}  {'total span':<24}{'':>5}{_fmt(span):>10}")
    print()
    print("category summary")
    print(f"{'':>2}  {'agent stages (Agent/Task)':<24}{'':>5}{_fmt(split[CAT_AGENT]):>10}")
    print(f"{'':>2}  {'mcp stages (roundtable…)':<24}{'':>5}{_fmt(split[CAT_MCP]):>10}")
    print(f"{'':>2}  {'other tool calls':<24}{'':>5}{other_calls:>10}")
    if life_rows or life_other:
        print()
        print("lifecycle (gap decomposition — non-tool events)")
        for _key, label, n in life_rows:
            print(f"{'':>2}  {label:<24}{'':>5}{n:>10}")
        if life_other:
            print(f"{'':>2}  {'other lifecycle':<24}{'':>5}{life_other:>10}")


def main() -> None:
    ap = argparse.ArgumentParser(description="KEEL pipeline per-stage timing report.")
    ap.add_argument("--last", action="store_true",
                    help="report the latest captured session (the default)")
    ap.add_argument("--session", help="session id to report")
    ap.add_argument("--list", action="store_true", help="list captured sessions")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    if not DB_PATH.is_file():
        _no_data()
    sessions = _sessions()
    if not sessions:
        _no_data()

    match (args.list, args.session):
        case (True, _):
            for sid, n, span in sessions:
                print(f"{sid:<40} {n:>4} events  span {_fmt(span)}")
        case (False, None):
            _report(sessions[0][0], args.json)
        case (False, sid):
            known = {s for s, _, _ in sessions}
            if sid not in known:
                sys.stderr.write(f"No session '{sid}'. Try --list.\n")
                raise SystemExit(2)
            _report(sid, args.json)


if __name__ == "__main__":
    main()
