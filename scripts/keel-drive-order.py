#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""Pure-graph ordering for /karta-drive. Validates a WI subgraph from a Binder's
needs[] and emits a deterministic topological order. No git, no side effects —
ordering/selection truth is the Binder; merge state is the driver's concern. Halts
(nonzero, structured JSON) on cycle, missing WI, or malformed input (mirrors
keel-work-item-resolve.py's halt discipline)."""
import argparse, json, sys
from pathlib import Path

def _emit(obj, code=0):
    print(json.dumps(obj))
    sys.exit(code)

def _halt(kind, code, **extra):
    _emit({"ok": False, "halt": kind, **extra}, code)

def _load(binder_path):
    try:
        data = json.loads(Path(binder_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        _halt("binder_unreadable", 2, detail=str(e))
    if not isinstance(data, dict) or not isinstance(data.get("work_items"), list):
        _halt("binder_shape", 2, detail="work_items must be a list")
    items = {}
    for w in data["work_items"]:
        wid = w.get("id")
        if not isinstance(wid, str):
            _halt("work_item_no_id", 2)
        if wid in items:
            _halt("duplicate_id", 2, id=wid)
        items[wid] = sorted(set(w.get("needs", [])))  # dedupe needs[] (no uniqueItems in schema)
    return items  # id -> sorted unique needs[]

def _topo(ids, edges):
    indeg = {i: len(edges[i]) for i in ids}  # edges already deduped in _load
    rdeps = {i: [] for i in ids}             # rdeps[n] = nodes that depend on n
    for j in ids:
        for n in edges[j]:
            rdeps[n].append(j)
    order, ready = [], sorted(i for i in ids if indeg[i] == 0)
    while ready:
        i = ready.pop(0)
        order.append(i)
        for j in rdeps[i]:
            indeg[j] -= 1
            if indeg[j] == 0:
                ready = sorted(ready + [j])
    return order  # caller compares len(order) to len(ids) to detect a cycle

def cmd_order(items, wiset):
    missing = [w for w in wiset if w not in items]
    if missing:
        _halt("missing", 3, missing=sorted(missing))
    setlist = sorted(wiset)
    edges = {i: [n for n in items[i] if n in wiset] for i in setlist}
    external = {i: sorted(n for n in items[i] if n not in wiset) for i in setlist}
    external = {k: v for k, v in external.items() if v}
    order = _topo(setlist, edges)
    if len(order) != len(setlist):
        _halt("cycle", 4, cycle_candidates=[i for i in setlist if i not in order])
    _emit({"ok": True, "order": order, "external_needs": external})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--binder", required=True)
    ap.add_argument("--order", action="store_true", required=True)
    ap.add_argument("--set")
    a = ap.parse_args()
    if a.set is None:  # `is None` not `not a.set`: --set "" is a valid empty set (no-op)
        _halt("invocation", 2, detail="--order requires --set")
    items = _load(a.binder)
    cmd_order(items, {s.strip() for s in a.set.split(",") if s.strip()})

if __name__ == "__main__":
    main()
