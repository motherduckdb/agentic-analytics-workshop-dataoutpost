# Duckoffee (parked)

The first dataset kit for this workshop, set aside when the format moved to 90 minutes. It fits a
longer data engineering workshop where the agent builds the pipeline itself.

Duckoffee is a fictional coffee chain with six venues at tech conferences. The kit has:

- `facilitator/generate.py`: a deterministic generator for messy raw exports. Two POS systems (one
  exports latin-1, semicolon-delimited German files with a total row at the bottom), UTC
  timestamps, cents and dollars, duplicates, training sales, refunds, a misleading ops note.
- `facilitator/breaks/`: six deliveries that break the pipeline on purpose (resent file, renamed
  columns, silent unit change, unknown product, late file, truncated file).
- `tools/check.py`: grades `marts.daily_venue_revenue` against the answer key and names the mistake.
- `tools/deliver.py`: lands the next break into `data/raw`.
- `facilitator/solution/build.sql`: reference pipeline. Scores 100% on the base data and after
  every break.
- `facilitator/selftest.py`: runs the reference through every break plus 15 planted mistakes.
- `AGENTS.md`, `CLAUDE.md`, `.mcp.json`, `.claude/`: participant rules and hooks (answer key
  lock, token guard, cloud delete lock, trace log).

Generated data (`data/`, `facilitator/breaks/`, `facilitator/answer_key/`) is not in git. The
generator is deterministic, so run it first. Run from this folder (the Python project is at the repo
root, `uv` finds it):

```bash
uv run python facilitator/generate.py
duckdb facilitator/solution/solution.duckdb -f facilitator/solution/build.sql
uv run tools/check.py --db facilitator/solution/solution.duckdb
uv run python facilitator/selftest.py
```
