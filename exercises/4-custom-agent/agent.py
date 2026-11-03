# /// script
# requires-python = ">=3.11"
# dependencies = ["fastmcp==4.0.3", "httpx"]
# ///
"""Level 4: the whole agent. Your loop, your model, your tools.

The model is any OpenRouter model (OPENROUTER_API_KEY, MODEL).
The tools come from your level 3 MCP server, started as a subprocess.

    uv run agent.py "Which live-ops changes moved retention and ARPDAU?"
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

MODEL = os.environ.get("MODEL", "google/gemini-3.8-flash")
MAX_STEPS = int(os.environ.get("MAX_STEPS", "12"))
SERVER = Path(__file__).parent.parent / "3-custom-mcp" / "server.py"
SYSTEM = "You answer business questions with the tools you have. Show the numbers and the SQL you relied on."


def as_openai_tool(tool) -> dict:
    return {
        "type": "function",
        "function": {"name": tool.name, "description": tool.description or "", "parameters": tool.inputSchema},
    }


async def model(messages: list, tools: list) -> dict:
    async with httpx.AsyncClient(timeout=120) as http:
        r = await http.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
            json={"model": MODEL, "messages": messages, "tools": tools},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]


async def main(question: str) -> None:
    # The server gets the MotherDuck token. The model never sees it.
    env = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}
    server = StdioTransport(command="uv", args=["run", "-q", str(SERVER)], env=env)
    async with Client(server) as mcp:
        tools = [as_openai_tool(t) for t in await mcp.list_tools()]
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
        for step in range(MAX_STEPS):
            reply = await model(messages, tools)
            messages.append(reply)
            if not reply.get("tool_calls"):
                print(reply.get("content"))
                return
            for call in reply["tool_calls"]:
                name, args = call["function"]["name"], json.loads(call["function"]["arguments"] or "{}")
                print(f"[step {step + 1}] {name}({json.dumps(args)[:120]})", file=sys.stderr)
                result = await mcp.call_tool(name, args, raise_on_error=False)
                text = "\n".join(c.text for c in result.content if hasattr(c, "text"))
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": text[:20000]})
        print(f"Stopped after {MAX_STEPS} steps without an answer.")


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "What tables do we have?"))
