# Workshop rules for agents

You are helping a workshop participant build an analytics stack for Duckoffee, a coffee chain with
venues at tech conferences. Everything starts from the raw exports in `data/raw/`.

These are the house rules of the workshop room. Everything else (schema, tools, transformations,
tests, publishing) is yours to propose. The participant will add their own guardrails below as the
session goes.

## Off limits

- `facilitator/` holds the answer key and a reference solution. Do not read, list, grep or open
  anything in it. Using it would make the exercise pointless.
- `tools/check.py` and `tools/deliver.py` are for running, not reading. Run
  `uv run tools/check.py` to grade the warehouse, but do not open its source or the files it reads.
- Never modify, move or delete anything in `data/raw/`. It is the landing zone. New files arrive
  there when the human runs `make deliver`.

## Local warehouse

- DuckDB file: `workshop.duckdb` at the repo root. CLI: `duckdb workshop.duckdb`.
- Python: `uv run python ...` (DuckDB is already a dependency).

## Cloud (MotherDuck), from block 3 on

- The token is in the environment as `motherduck_token`. Never print it, echo it, or write it to a file.
- Prefix every MotherDuck resource you create (databases, shares, Flights, Dives, Guides) with
  `duckoffee`.
- Append one JSON line per cloud resource you create to `.workshop/ledger.jsonl`:
  `{"ts": "...", "type": "database|share|flight|dive|guide|token", "name": "...", "id": "...", "block": 3}`
- Deleting cloud resources is locked until the human runs `make allow-teardown`. If a delete is
  blocked, stop and ask. Do not look for a workaround.

## Participant guardrails

<!-- Add the rules you wish your agent had followed. Keep them short and testable. -->
