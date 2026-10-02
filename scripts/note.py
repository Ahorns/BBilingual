#!/usr/bin/env python3
"""Add a note about a bug to the BBilingual log, with the latest batch attached.

Usage: note.py "what looked wrong"
Inside Claude Code you can run it with the ! prefix:  ! python3 /path/to/scripts/note.py "..."
The log must be enabled (BBILINGUAL_LOG=1), otherwise nothing is recorded.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bilingual  # noqa: E402

if len(sys.argv) < 2:
    sys.exit(__doc__)
if os.environ.get("BBILINGUAL_LOG") != "1":
    sys.exit("The log is off. Start Claude Code with BBILINGUAL_LOG=1 first.")
last = None
try:
    with open(bilingual.LOG_PATH, encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("event") == "batch":
                last = entry
except OSError:
    pass
bilingual.log(event="note", note=" ".join(sys.argv[1:]), last_batch=last)
print("noted in", bilingual.LOG_PATH)
