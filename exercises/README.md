# Exercises

One folder per level. All four were run end to end on 2026-11-02 against Gloamwick Studios, a
duckgen dataset (`gaming-gloamwick-liveops`, S tier), with the question "Which live-ops changes
moved retention and ARPDAU?".

Keys come from the environment: `OPENROUTER_API_KEY` and `MOTHERDUCK_TOKEN`. Neither is written to
a file, and neither reaches the model.

## Claude Code on the workshop key

Claude Code runs on an OpenRouter key through OpenRouter's Anthropic-compatible endpoint:

```sh
export ANTHROPIC_BASE_URL=https://openrouter.ai/api
export ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY"
export ANTHROPIC_API_KEY=""
export ANTHROPIC_MODEL=anthropic/claude-sonnet-5.5
export ANTHROPIC_SMALL_FAST_MODEL=anthropic/claude-haiku-5.5
```

## Levels

| Level | Folder | Run | Measured |
|---|---|---|---|
| 1 Local | `level1/` | `claude` in the folder, with the skill. Needs the DuckDB CLI. | 16 turns, 3.4 min, $0.38 |
| 2 MotherDuck | `level2/` | `claude --mcp-config mcp.json` in the folder | 18 turns, 67 s, $0.22 |
| 3 Your tools | `level3/` | `uv run server.py` as a stdio MCP server, then point the agent at it | 5 turns, 28 s, $0.07 |
| 4 Your agent | `level4/` | `uv run agent.py "your question"`. `MODEL` picks any OpenRouter model. | 5 steps, 62 s |

Level 3 needs the share attached once in the MotherDuck account (level 2 does it). `COMPANY_DB`
sets the database name, `QUESTION_LOG` the log file.

## Findings from the test runs

- All four levels found the same two changes: the level 12 boss rework cut Android D7 retention
  (about 14.5% to 10.7%, iOS flat), and the rewarded chest video raised ARPDAU (about +2 cents).
  The answer key `retention_shift` agrees on the boss rework.
- The domain tool at level 3 cut turns from 16 to 18 down to 5, and cost by 3 to 5 times.
- The level 4 run on Gemini read the guide written by the level 2 run and returned the same
  numbers as level 2.
- Without the MotherDuck token, the level 4 model invented table names instead of stopping. Good
  material for observability.
- Forward `get_guide` in the level 3 server, or the agent sees guide titles and cannot read them.
- DuckDB in the Claude Code sandbox cannot parse the sandbox proxy URL. Run these outside it.

## Not tested yet

- The Flight stretch in level 2.
- The DuckDB 2.0 CLI. Level 1 used the 1.4 CLI, and the 2.0 Python package for the load timing.
- opencode as the harness.
- The draw page (level 0) and the generator around the level 4 loop.
