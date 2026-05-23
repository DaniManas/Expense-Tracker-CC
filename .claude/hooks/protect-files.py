#!/usr/bin/env python3
import sys
import json

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")

protected = ["spendly.db", ".env", "migrations/"]
dangerous = ["rm ", "rm -", "unlink ", "truncate "]

for d in dangerous:
    if d in cmd:
        for p in protected:
            if p in cmd:
                print(f"BLOCKED: destructive command on protected file: {p}", file=sys.stderr)
                sys.exit(2)

sys.exit(0)