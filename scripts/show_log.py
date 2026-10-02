#!/usr/bin/env python3
"""Print the BBilingual log (enable it with BBILINGUAL_LOG=1).

Usage: show_log.py [-n BATCHES] [--flagged]
  -n N         show the last N entries (default 20)
  --flagged    only show lines with automatic problem flags
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bilingual import LOG_PATH  # noqa: E402

args = sys.argv[1:]
flagged = "--flagged" in args
limit = int(args[args.index("-n") + 1]) if "-n" in args else 20
try:
    with open(LOG_PATH, encoding="utf-8") as f:
        entries = [json.loads(line) for line in f]
except OSError:
    sys.exit("No log yet at %s. Start Claude Code with BBILINGUAL_LOG=1 to record one." % LOG_PATH)

shown = 0
for e in reversed(entries):
    event = e.get("event")
    if event == "batch":
        bad = [p for p in e["pairs"] if p[2]]
        if flagged and not bad:
            continue
        print("[%s v%s %s] batch %s: %s lines, %s prose, ctx %s, %ss%s" % (
            e["t"], e["v"], e.get("model") or e["backend"], e["index"], e["lines"], e["prose"],
            e["ctx"], e["secs"], "  <final>" if e["final"] else ""))
        for source, translation, flags in (bad if flagged else e["pairs"]):
            print("  SRC:", source)
            print("  TRG:", translation or "(none)")
            if flags:
                print("  !!", "; ".join(flags))
    else:
        details = {k: v for k, v in e.items() if k not in ("t", "v", "event")}
        print("[%s v%s] %s: %s" % (e["t"], e["v"], event.upper(), details))
    shown += 1
    if shown >= limit:
        break
