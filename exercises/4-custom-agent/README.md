# Hands-on 4: your own agent

Time: 10 minutes. You need the workshop key, `MOTHERDUCK_TOKEN` and the level 3 server (this
agent starts it for you).

[`agent.py`](agent.py) is the whole agent in about 60 lines: a loop, a model on OpenRouter, and
the tools from your level 3 MCP server. No permissions, no hooks, no memory: that harness is now
yours to write.

## Steps

The prompt is the same as on the slide. Paste it as it is.

1. Point the agent at the workshop key and the default model (the minter page shows the same
   lines):

   ```sh
   cd ../4-custom-agent   # from the level 3 folder of the repo you cloned
   export OPENROUTER_API_KEY=<your workshop key>
   export MODEL=openai/gpt-6-luna
   ```

2. Run your agent on the workshop question:

   ```sh
   uv run agent.py "Which live-ops changes since spring 2025 moved day-7 retention or revenue per daily active user, and on which platform? Show the SQL."
   ```

3. Read the `[step N]` lines. Which tools did it call? Did it call `how_we_count` before writing
   SQL?

4. Swap the model and run the same question again. Compare the steps and the numbers.

   ```sh
   MODEL=anthropic/claude-haiku-5.5 uv run agent.py "Which live-ops changes since spring 2025 moved day-7 retention or revenue per daily active user, and on which platform? Show the SQL."
   ```

5. Change the harness. Run with `MAX_STEPS=2`, or edit `SYSTEM` in `agent.py`. What breaks first?

## Done when

Your agent answers the question on the model you picked, and you can say which tools it called.

## Notes

- The workshop key only allows `openai/gpt-6-luna`, `anthropic/claude-haiku-5.5` and
  `anthropic/claude-sonnet-5.5`. Other models return 403.
- The OpenRouter key never reaches the MCP server, and the MotherDuck token never reaches the
  model.
- The bonus below writes every step to MotherDuck.

## Bonus: the whole run in MotherDuck

`agent.py` uses the same [`traces.py`](../3-custom-mcp/traces.py) as the level 3 server, and here it
sees everything: one `invoke_agent` span per question, a `chat` span per model call with its tokens
and cost (from OpenRouter's usage), and an `execute_tool` span per tool call, nested in one trace.
The rows land in `workshop_traces.spans`, with the same columns as the data behind the
[Agent observability Dive](https://motherduck.com/dive-gallery/dives/agent-observability).

1. Run the agent with tracing on:

   ```sh
   TRACE_TO_MOTHERDUCK=1 uv run agent.py "Which live-ops changes since spring 2025 moved day-7 retention or revenue per daily active user, and on which platform? Show the SQL."
   ```

2. Run it again with another model, so you have two traces to compare.

3. In an agent connected to the MotherDuck MCP server, build the Dive:

   > Build a Dive over workshop_traces like the Agent observability Dive in the MotherDuck Dive gallery: a list of traces from agent_traces with model, latency, tool calls, tokens and cost, and the run tree of one trace from spans.

   Or open the gallery Dive, choose **Copy Dive to My Account**, and ask your agent to point it at
   `workshop_traces`. Its other tables (cases, tools, handoffs) do not exist here, so expect to drop
   those parts.

Tested with a local DuckDB file and a simulated run (`TRACES_DB=traces.duckdb`), not yet against
MotherDuck or on a real OpenRouter run.
