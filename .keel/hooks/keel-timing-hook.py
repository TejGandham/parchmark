#!/usr/bin/env python3
"""KEEL full-lifecycle timing hook.

Records one row per Claude Code lifecycle event to a local, git-ignored
SQLite database so `scripts/keel-timing.py` can break a pipeline run down by
stage (agent · duration · share of total) AND decompose the gaps between
agents — orchestrator turns, context compaction, permission/notification
waits, and session boundaries. Deterministic and zero-token — the harness
fires it, not the model.

Registered (by install.py, via keel_manifest.KEEL_HOOKS_SPEC) as a CATCH-ALL
across the WHOLE lifecycle, not just tool calls. EVERY event uses the standard
`{matcher, hooks:[…]}` settings.json shape with `matcher: ""` (empty = match
all) — the live Claude Code validator rejects a flat command-hook object
placed directly in the event array:
  - tool events (PreToolUse / PostToolUse / PostToolUseFailure):
    EVERY tool call — subagent dispatches (Agent/Task), MCP-backed work
    (roundtable etc.), ordinary tools (Bash, Edit, …).
  - lifecycle events: orchestrator turns (Stop / UserPromptSubmit), context
    compaction (PreCompact / PostCompact), permission and notification waits
    (PermissionRequest / PermissionDenied / Notification), and session
    boundaries (SessionStart / SessionEnd), plus StopFailure / PostToolBatch.
Capturing the full lifecycle is what lets the reporter attribute the ~74% of
wall-clock that lives in the gaps between agents, not just the tool time.

This hook needs no per-event branching: it records whatever fields the
payload carries. Tool events populate tool / tool_use_id / agent; lifecycle
events carry none of those, so those columns are simply NULL — every event
still gets its event name + session + timestamp. The reporter distinguishes
them by the `event` column and the presence/absence of `tool`.

ASYNC: every hook entry carries `"async": true`, so the harness runs this in
the background and does NOT block on it. Telemetry adds zero latency to the
run. The full stdin payload still arrives.

Tool stages pair by `tool_use_id` (present and identical across the Pre/Post
pair). The reporter labels agent stages by `tool_input.subagent_type` and
MCP stages by the tool's last `__`-delimited segment.
SubagentStart/SubagentStop are intentionally NOT used: their input schema
is undocumented (claude-code issue #19170) and SubagentStop has an open
tool-injection bug (#13951); Agent Pre/Post tool events cover the same
dispatch boundary without those hazards.

Storage is SQLite (stdlib `sqlite3`): compact at high event volume,
queryable by the reporter via SQL, no server and no Docker. Each event
opens the DB in WAL mode with a short busy timeout, does one INSERT, and
closes — concurrent async invocations serialize cleanly.

P5 — snapshot, not timeline: timing is runtime measurement, never repo
state. The DB lives in .keel/timing/ (self-ignored on creation)
and is NEVER committed. The hook writes nowhere else.

Robustness: any failure exits 0 silently. A timing hook must never block
or error a pipeline run.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from pathlib import Path

_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS events("
    "ts_ms INTEGER, session TEXT, event TEXT, tool TEXT, "
    "tool_use_id TEXT, agent TEXT, agent_id TEXT)"
)
_INDEX = "CREATE INDEX IF NOT EXISTS ix ON events(session, ts_ms)"
_INSERT = (
    "INSERT INTO events(ts_ms, session, event, tool, tool_use_id, agent, agent_id) "
    "VALUES (?, ?, ?, ?, ?, ?, ?)"
)


def _enabled() -> bool:
    """Telemetry is OPT-IN. The hook ships registered but stays inert —
    zero overhead, no files written — unless KEEL_TIMING is set truthy
    (1/true/yes/on) in the environment of the pipeline run."""
    return os.environ.get("KEEL_TIMING", "").strip().lower() in ("1", "true", "yes", "on")


def main() -> None:
    if not _enabled():
        return
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        data = json.loads(raw) if raw else {}
        if not isinstance(data, dict):
            return
    except Exception:
        return  # malformed input must never break the tool call

    try:
        project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        log_dir = Path(project) / ".keel" / "timing"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Self-ignore the dir so the timing DB is never committed (P5).
        gi = log_dir / ".gitignore"
        if not gi.exists():
            gi.write_text(
                "# KEEL local timing data — runtime measurement, never "
                "committed (P5).\n*\n", encoding="utf-8",
            )

        session = str(data.get("session_id") or "session")
        event = str(data.get("hook_event_name") or data.get("hookEventName") or "")
        tool = data.get("tool_name")
        tool_use_id = data.get("tool_use_id")
        # agent: subagent_type from the dispatch tool's input when present,
        # else the top-level agent_type (some event shapes carry it there).
        agent = None
        ti = data.get("tool_input")
        if isinstance(ti, dict):
            agent = ti.get("subagent_type")
        if not agent:
            agent = data.get("agent_type")
        agent_id = data.get("agent_id")

        def _s(v: object) -> str | None:
            return v if isinstance(v, str) and v else None

        db = log_dir / "timing.db"
        con = sqlite3.connect(str(db), timeout=2.0)
        try:
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA busy_timeout=2000")
            con.execute(_SCHEMA)
            con.execute(_INDEX)
            con.execute(_INSERT, (
                int(time.time() * 1000),
                _s(session) or "session",
                event,
                _s(tool),
                _s(tool_use_id),
                _s(agent),
                _s(agent_id),
            ))
            con.commit()
        finally:
            con.close()
    except Exception:
        return  # telemetry must never break a run


if __name__ == "__main__":
    main()
    sys.exit(0)
