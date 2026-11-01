#!/usr/bin/env python3
"""Append every prompt and tool call to .workshop/trace.jsonl so you can query your agent with DuckDB.

  make trace        summary per block
  duckdb -c "FROM read_json('.workshop/trace.jsonl')"

Stdlib only. Never fails the agent: any error is swallowed.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
STATE = ROOT / ".workshop"


def summarize(tool: str, tin: dict) -> str:
    if tool == "Bash":
        return tin.get("command", "")
    for k in ("file_path", "path", "pattern", "url", "query", "sql"):
        if k in tin:
            return str(tin[k])
    return json.dumps(tin)


def outcome(resp) -> tuple[bool | None, str]:
    if isinstance(resp, dict):
        if resp.get("is_error") or resp.get("isError") or resp.get("error"):
            return False, str(resp.get("error") or resp)[:300]
        if resp.get("interrupted"):
            return False, "interrupted"
        stderr = resp.get("stderr") or ""
        if stderr and any(w in stderr for w in ("Error", "error:", "Traceback", "Exception")):
            return False, stderr[:300]
        return True, ""
    if isinstance(resp, str) and resp.lower().startswith("error"):
        return False, resp[:300]
    return None, ""


def main() -> None:
    p = json.load(sys.stdin)
    STATE.mkdir(exist_ok=True)
    block = (STATE / "block").read_text().strip() if (STATE / "block").exists() else None
    ev = p.get("hook_event_name")
    row = {"ts": datetime.now(timezone.utc).isoformat(), "block": block, "event": ev, "session": p.get("session_id")}
    if ev == "UserPromptSubmit":
        row["summary"] = (p.get("prompt") or "")[:2000]
    elif ev in ("PreToolUse", "PostToolUse", "PostToolUseFailure"):
        tool = p.get("tool_name", "")
        row["tool"] = tool
        row["tool_use_id"] = p.get("tool_use_id")
        row["summary"] = summarize(tool, p.get("tool_input") or {})[:2000]
        if ev != "PreToolUse":
            ok, err = outcome(p.get("tool_response"))
            if ev == "PostToolUseFailure":
                ok, err = False, str(p.get("error") or "")[:300]
            row["ok"], row["error"] = ok, err
    with (STATE / "trace.jsonl").open("a") as f:
        f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
