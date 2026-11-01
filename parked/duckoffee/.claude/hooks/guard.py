#!/usr/bin/env python3
"""PreToolUse guard. Blocks (exit 2) the few things the room agreed agents must not do alone.

1. Peek at the answer key (facilitator/) or the grader's source.
2. Touch the raw landing zone (data/raw) or land deliveries (the human does that).
3. Print the MotherDuck token.
4. Delete cloud resources, unless the human unlocked teardown (`make allow-teardown`).

Stdlib only, so it starts fast. Every block is also written to .workshop/trace.jsonl.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
STATE = ROOT / ".workshop"
UNLOCK = STATE / "teardown.unlocked"

READERS = r"\b(cat|head|tail|less|more|sed|awk|grep|rg|ag|bat|nl|strings|xxd|od|cp|mv|tar|zip|open|code|vim?|nano|find|ls|tree|python3?\s+-c|duckdb)\b"
SECRET = "|".join([
    r"(echo|printf|cat|tee)\b[^|;&]*\$\{?motherduck_token",       # echo $motherduck_token
    r"\bprintenv\s+motherduck_token|\bprintenv\s*($|\|)",          # printenv motherduck_token, printenv | ...
    r"(^|[;&|]\s*)(env|export\s+-p|set)\s*($|\|)",                 # env | grep token
    r"print_md_token",                                              # SQL: PRAGMA print_md_token
    r"print\(\s*os\.environ(\.get)?[\[(]\s*['\"]motherduck_token",  # print(os.environ['motherduck_token'])
])
CLOUD_DELETE = [
    r"\bDROP\s+DATABASE\b",
    r"\bDROP\s+SHARE\b",
    r"\bMD_DELETE_\w+",
    r"\bREVOKE\b",
    r"\bDELETE\s+TOKEN\b",
]
MCP_DELETE_TOOLS = re.compile(r"mcp__motherduck__(delete_\w+|revoke_access)")


def log(event: dict) -> None:
    STATE.mkdir(exist_ok=True)
    block = (STATE / "block").read_text().strip() if (STATE / "block").exists() else None
    event = {"ts": datetime.now(timezone.utc).isoformat(), "block": block, **event}
    with (STATE / "trace.jsonl").open("a") as f:
        f.write(json.dumps(event) + "\n")


def deny(reason: str, payload: dict, text: str) -> None:
    log({"event": "Blocked", "session": payload.get("session_id"), "tool": payload.get("tool_name"),
         "summary": text[:500], "reason": reason})
    print(f"Blocked by workshop guard: {reason}", file=sys.stderr)
    sys.exit(2)


def main() -> None:
    payload = json.load(sys.stdin)
    tool = payload.get("tool_name", "")
    tin = payload.get("tool_input", {}) or {}
    text = tin.get("command") if tool == "Bash" else json.dumps(tin)
    text = text or ""

    # 1 + 2: answer key, grader source, raw zone
    if tool == "Bash":
        if re.search(r"facilitator", text) and not re.match(r"\s*make\s", text):
            deny("facilitator/ holds the answer key. It is off limits.", payload, text)
        if re.search(READERS, text) and re.search(r"tools/(check|deliver)\.py", text):
            deny("run tools/check.py, do not read it.", payload, text)
        if re.search(r"tools/deliver\.py|make\s+deliver", text):
            deny("deliveries are landed by the human (make deliver), not the agent.", payload, text)
        if re.search(r"\b(rm|mv|truncate|sed\s+-i|tee|>)\b[^|;&]*data/raw", text):
            deny("data/raw is the landing zone: read it, never change it.", payload, text)
    elif tool in ("Read", "Grep", "Glob", "Edit", "Write", "NotebookEdit"):
        target = " ".join(str(tin.get(k, "")) for k in ("file_path", "path", "pattern", "notebook_path"))
        if "facilitator" in target or re.search(r"tools/(check|deliver)\.py", target):
            deny("facilitator/ and the grader's source are off limits.", payload, target)
        if tool in ("Edit", "Write", "NotebookEdit") and "data/raw" in target:
            deny("data/raw is the landing zone: read it, never change it.", payload, target)

    # 3: secrets
    if tool == "Bash" and re.search(SECRET, text, re.IGNORECASE):
        deny("that would print the MotherDuck token into the transcript.", payload, text)

    # 4: cloud deletes
    if not UNLOCK.exists():
        if MCP_DELETE_TOOLS.match(tool):
            deny("cloud deletes are locked. Ask the human to run `make allow-teardown`.", payload, text)
        cloud_context = tool.startswith("mcp__motherduck") or re.search(r"md:|motherduck", text, re.IGNORECASE)
        if cloud_context:
            for pat in CLOUD_DELETE:
                if re.search(pat, text, re.IGNORECASE):
                    deny("cloud deletes are locked. Ask the human to run `make allow-teardown`.", payload, text)
            if tool.startswith("mcp__motherduck") and re.search(r"\bDROP\s+(TABLE|SCHEMA|VIEW)\b", text, re.IGNORECASE):
                deny("dropping cloud objects is locked. Ask the human to run `make allow-teardown`.", payload, text)

    sys.exit(0)


if __name__ == "__main__":
    main()
