# scripts/keel_settings.py
"""KEEL settings.json surgery — merge hook entries; remove by exact command.

Stdlib-only. Identifies KEEL-owned hook entries by exact match on the
`command` string the install receipt recorded. Substring/signature
matching is not used — a user hook that happens to reference the KEEL
script path via a different command string must not be treated as
KEEL-owned.
"""
from __future__ import annotations

import copy
import json
from typing import Any


HookSpec = dict[str, str]


def _find_matcher_entry(matcher_array: list[dict], matcher: str) -> dict | None:
    for entry in matcher_array:
        if entry.get("matcher") == matcher:
            return entry
    return None


def _hook_has_command(hook: dict, command: str) -> bool:
    return hook.get("command") == command


def _make_hook_obj(spec: HookSpec, command: str) -> dict[str, Any]:
    """Build the settings.json command-hook object from a spec.

    Nested under a `{matcher, hooks:[…]}` wrapper. Preserves the optional
    `async` flag verbatim (carried through, not hardcoded, so non-timing
    hooks stay synchronous). Spec fields `event`, `matcher`, and `signature`
    are installer/manifest metadata, not part of the hook object.
    """
    hook_obj: dict[str, Any] = {"type": "command", "command": command}
    if spec.get("async"):
        hook_obj["async"] = spec["async"]
    return hook_obj


def _check_command_str(cmd: object, where: str) -> None:
    if cmd is not None and not isinstance(cmd, str):
        raise ValueError(f"{where}['command'] must be a string")


def _validate_hooks_shape(settings: dict) -> None:
    """Raise TypeError/ValueError on unexpected shape at any level.

    Called at the top of merge_hooks / remove_hooks_by_command so
    malformed nested structures can't slip past a shallow guard and
    crash mid-mutation. Validates that `command`, when present on a
    hook entry, is a string — otherwise downstream exact-match
    comparisons would raise TypeError deep inside the walk.

    Every entry in settings['hooks'][event] is a matcher-wrapper
    `{matcher, hooks: [{type, command, async}, …]}`. This is the only
    shape the Claude Code event-config contract accepts; `matcher: ""`
    is the catch-all matcher (a normal matcher string, not a special case).
    """
    if not isinstance(settings, dict):
        raise TypeError("settings must be a dict")
    hooks_root = settings.get("hooks")
    if hooks_root is None:
        return
    if not isinstance(hooks_root, dict):
        raise ValueError("settings['hooks'] must be a dict or absent")
    for event, arr in hooks_root.items():
        if not isinstance(arr, list):
            raise ValueError(
                f"settings['hooks'][{event!r}] must be a list")
        for i, entry in enumerate(arr):
            if not isinstance(entry, dict):
                raise ValueError(
                    f"settings['hooks'][{event!r}][{i}] must be a dict")
            where = f"settings['hooks'][{event!r}][{i}]"
            inner = entry.get("hooks")
            if inner is not None and not isinstance(inner, list):
                raise ValueError(f"{where}['hooks'] must be a list or absent")
            for j, h in enumerate(inner or []):
                if not isinstance(h, dict):
                    raise ValueError(f"{where}['hooks'][{j}] must be a dict")
                _check_command_str(h.get("command"), f"{where}['hooks'][{j}]")


def merge_hooks(settings: dict,
                specs: list[HookSpec]) -> tuple[dict, list[str]]:
    """Insert each spec into settings['hooks'][event] under matching matcher.

    Idempotent: if an entry already has a hook with the spec's exact
    command, no change. Returns (new_settings, newly_inserted_commands).
    `newly_inserted_commands` is the exact command string KEEL added —
    used by the receipt for exact-match removal at uninstall time.

    Raises TypeError if `settings` is not a dict, or ValueError if any
    nested shape deviates from the documented schema. Callers should
    treat those as "unexpected shape, leave file alone".
    """
    _validate_hooks_shape(settings)

    new = copy.deepcopy(settings)
    new.setdefault("hooks", {})
    inserted_cmds: list[str] = []

    for spec in specs:
        event = spec["event"]
        command = spec["command"]
        event_arr = new["hooks"].setdefault(event, [])

        # Every spec carries a `matcher` and uses the nested matcher-wrapper
        # shape. `matcher: ""` is the catch-all matcher (a normal matcher
        # string) — no special-casing.
        matcher = spec["matcher"]
        matcher_entry = _find_matcher_entry(event_arr, matcher)
        if matcher_entry is None:
            matcher_entry = {"matcher": matcher, "hooks": []}
            event_arr.append(matcher_entry)
        hooks_list = matcher_entry.setdefault("hooks", [])
        # Exact-command idempotency check: a pre-existing hook at this
        # matcher with KEEL's exact command is considered already
        # present. User hooks that coincidentally reference the same
        # script path via a different command string are NOT treated as
        # duplicates; KEEL adds its own entry alongside them.
        if not any(_hook_has_command(h, command) for h in hooks_list):
            hooks_list.append(_make_hook_obj(spec, command))
            inserted_cmds.append(command)

    return new, inserted_cmds


def remove_hooks_by_command(settings: dict, commands: list[str]) -> tuple[dict, int]:
    """Remove every hook entry whose command is EXACTLY in `commands`.

    Exact-match removal is the receipt-model ownership semantics: KEEL
    removes only the hooks it recorded inserting, even if a user later
    adds their own hook whose command happens to reference the KEEL
    script path (substring-collision). Prunes empty matcher arrays and
    empty event sections. Returns (new_settings, n_hooks_removed).
    """
    _validate_hooks_shape(settings)
    new = copy.deepcopy(settings)
    removed = 0
    hooks_root = new.get("hooks")
    if not isinstance(hooks_root, dict):
        return new, 0

    cmd_set = set(commands)
    for event in list(hooks_root.keys()):
        event_arr = hooks_root.get(event, [])
        kept_entries: list[dict] = []
        for entry in event_arr:
            hooks_list = entry.get("hooks", [])
            kept: list[dict] = []
            for h in hooks_list:
                if h.get("command") in cmd_set:
                    removed += 1
                else:
                    kept.append(h)
            if kept:
                new_entry = dict(entry)
                new_entry["hooks"] = kept
                kept_entries.append(new_entry)
        if kept_entries:
            hooks_root[event] = kept_entries
        else:
            del hooks_root[event]

    if not hooks_root:
        new.pop("hooks", None)
    return new, removed


def has_non_keel_content(settings: dict, owned_commands: list[str]) -> bool:
    """True if settings has non-hook keys OR hook entries unrelated to KEEL.

    A hook is considered KEEL-owned only when its command is EXACTLY in
    `owned_commands`. Exact match prevents a user-added hook that
    coincidentally references the KEEL script path from being treated
    as KEEL-owned, which would cause a mode=created settings.json to be
    deleted when it should be preserved.

    Defensive on shape: if the structure is malformed we return True so
    the caller won't delete the file (can't confirm it's pure KEEL).
    """
    try:
        _validate_hooks_shape(settings)
    except (TypeError, ValueError):
        return True
    for k in settings:
        if k != "hooks":
            return True
    hooks_root = settings.get("hooks", {})
    if not isinstance(hooks_root, dict):
        return False
    cmd_set = set(owned_commands)
    for event, entries in hooks_root.items():
        for entry in entries or []:
            for h in entry.get("hooks", []) or []:
                if h.get("command") not in cmd_set:
                    return True
    return False


def serialize_stable(settings: dict) -> str:
    """Deterministic JSON: sorted keys, 2-space indent, trailing newline."""
    return json.dumps(settings, indent=2, sort_keys=True) + "\n"
