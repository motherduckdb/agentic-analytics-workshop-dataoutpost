# Hands-on 3: your own MCP server

Time: 10 minutes. You need git, uv, `MOTHERDUCK_TOKEN` exported, and the Gloamwick share attached in
your MotherDuck account (step 3 of [hands-on 2A](../2a-mcp/README.md) does it).

[`server.py`](server.py) is a small MCP server that sits in front of MotherDuck's, following the
[MotherDuck white-label guide](https://motherduck.com/docs/key-tasks/ai-and-motherduck/mcp-workflows/white-label-mcp-server/).
Three things to look for:

- **A tool only your server has.** `live_ops_impact` holds the SQL for a question the business asks
  every week. No other MCP server has it. The other tools forward MotherDuck's under your names.
- **The token is yours to pick.** The server calls MotherDuck with whatever is in
  `MOTHERDUCK_TOKEN`, and the agent never sees it. Start it with a
  [service account](https://motherduck.com/docs/key-tasks/service-accounts-guide/create-and-configure-service-accounts/)'s
  token and every user of your server gets exactly that account's rights: only the databases and
  shares it was granted, read-only with a read scaling token, and with a
  [secure view](https://motherduck.com/docs/key-tasks/sharing-data/secure-views/) on the share, only
  the rows and columns it allows.
- **Every question is logged** with its SQL in `questions.jsonl`.

## Steps

The prompts are the same as on the slide. Paste them as they are.

1. Clone the workshop repo, go to the level 3 folder, and read `server.py`. Find `live_ops_impact`,
   the log, and where the token comes from.

   ```sh
   git clone https://github.com/motherduckdb/agentic-analytics-workshop-dataoutpost.git
   cd agentic-analytics-workshop-dataoutpost/exercises/3-custom-mcp
   ```

2. Connect your agent to your local server, and to no other MCP server, so it can only use your
   tools. A local server runs on your laptop over stdio: your agent starts it. That works in agents
   that run on your laptop, like Claude Code, Codex or Cursor. claude.ai on the web and ChatGPT only
   take remote servers, so you would deploy this one first.

   - Claude Code: start it from this folder with the config next to `server.py`, then type `/mcp`:
     `company-data` should be connected. `mcp.json` passes `MOTHERDUCK_TOKEN` to the server.

     ```sh
     claude --strict-mcp-config --mcp-config mcp.json
     ```

   - Codex: add the server to `~/.codex/config.toml`, with the full path of this folder, then start
     `codex`. `env_vars` forwards your token without writing it in the file. From the Codex docs, not
     tested.

     ```toml
     [mcp_servers.company-data]
     command = "uv"
     args = ["run", "-q", "server.py"]
     cwd = "/full/path/to/exercises/3-custom-mcp"
     env_vars = ["MOTHERDUCK_TOKEN", "TRACE_TO_MOTHERDUCK"]
     ```

   - Cursor and others: register `uv run server.py`, run from this folder, as a stdio server with
     `MOTHERDUCK_TOKEN` in its environment.

3. Ask the workshop question. Watch for `live_ops_impact` in the tool calls: only your server has
   it. Count the turns and compare with levels 1 and 2. Paste:

   > Which live-ops changes since spring 2025 moved day-7 retention or revenue per daily active user, and on which platform? Show the SQL.

4. Read your log. Every question and its SQL is there.

   ```sh
   cat questions.jsonl
   ```

5. Add your own tool: copy `live_ops_impact` into a `starter_conversion` tool with the SQL from
   level 2. Restart your agent, then paste:

   > Did the starter pack price cut lift payer conversion? Split by acquisition channel, before and after. Show the SQL.

## Done when

Your agent answered with your tools only, it called `live_ops_impact`, and `questions.jsonl` shows
the question.

## If you finish early

- Create a [service account](https://motherduck.com/docs/key-tasks/service-accounts-guide/create-and-configure-service-accounts/)
  (the free plan allows two), give it the Gloamwick share, and start your server with its token
  instead of yours. Ask the same question: same tools, other rights. Not tested yet.

## Bonus: trace your agent into MotherDuck

Your server can write one [OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/gen-ai/) span
per tool call to MotherDuck, then you look at them in a Dive, like the
[Agent observability Dive](https://motherduck.com/dive-gallery/dives/agent-observability) in the
MotherDuck Dive gallery. [`traces.py`](traces.py) does it: GenAI spans (`execute_tool`,
`gen_ai.tool.name`, the question, the SQL, the duration, the status), written as rows to
`workshop_traces.spans` with the same columns as the gallery Dive's data, plus an `agent_traces` view
with one row per trace. It is off unless you turn it on.

1. Turn tracing on, then restart your agent so it restarts the server:

   ```sh
   export TRACE_TO_MOTHERDUCK=1
   ```

2. Ask the workshop question again. Then look at the spans:

   ```sh
   motherduck query "FROM workshop_traces.spans ORDER BY start_time DESC LIMIT 10"
   ```

3. In an agent connected to the MotherDuck MCP server (level 2), build the Dive:

   > Build a Dive over workshop_traces like the Agent observability Dive in the MotherDuck Dive gallery: a list of traces from agent_traces, the run tree of one trace from spans, tool calls with their status and duration.

Here you only get tool spans: the model runs inside your agent, out of the server's sight. Level 4
traces the whole run, with tokens and cost. Not tested against MotherDuck yet: tested with a local
DuckDB file (`TRACES_DB=traces.duckdb`).

## Notes

- `COMPANY_DB` sets the database name (default `gaming_gloamwick_liveops`), `QUESTION_LOG` the log
  file.
- `how_we_count` and `read_definition` forward `get_query_guide` and `get_guide`, so the guide you
  wrote in 2B still reaches the agent. Without `get_guide` the agent sees guide titles and cannot
  read them.
- Read scaling (read-only) tokens and secure views need a paid plan (secure views: Business or
  Enterprise, trials count). On the free plan the token story stops at the service account: it only
  reaches the shares you grant it.
