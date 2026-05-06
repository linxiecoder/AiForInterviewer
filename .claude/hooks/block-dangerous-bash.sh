#!/usr/bin/env bash
set -euo pipefail

INPUT="$(cat)"

INPUT_JSON="$INPUT" python3 - <<'PY'
import json
import os
import re
import sys

try:
    payload = json.loads(os.environ.get("INPUT_JSON", "") or "{}")
except Exception:
    sys.exit(0)

cmd = payload.get("tool_input", {}).get("command", "")
if not isinstance(cmd, str) or not cmd.strip():
    sys.exit(0)

normalized = " ".join(cmd.split())

patterns = [
    r"(^|[;&|]\s*)rm\s+-(?=[A-Za-z-]*r)(?=[A-Za-z-]*f)[A-Za-z-]*\b",
    r"(^|[;&|]\s*)kubectl\s+delete\b",
    r"(^|[;&|]\s*)terraform\s+apply\b",
    r"(^|[;&|]\s*)pulumi\s+up\b",
    r"(^|[;&|]\s*)aws\b.*\bdelete\b",
    r"(^|[;&|]\s*)gcloud\b.*\bdelete\b",
    r"(^|[;&|]\s*)az\b.*\bdelete\b",
    r"\b(drop|truncate)\s+(database|table)\b",
    r"(^|[;&|]\s*)git\s+push\b",
    r"(^|[;&|]\s*)git\s+reset\s+--hard\b",
    r"(^|[;&|]\s*)git\s+clean\s+-fd\b",
]

for pattern in patterns:
    if re.search(pattern, normalized, flags=re.IGNORECASE):
        print(f"Blocked dangerous command: {normalized}", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
PY
