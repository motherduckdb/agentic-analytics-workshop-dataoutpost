# Agentic analytics workshop

**The Next Data Stack Has No UI: Building Analytics Agents with Ducks.** A 90-minute hands-on
workshop by Mehdi Ouazza and Jacob Matson (MotherDuck), prepared for Data Outpost.

Text to SQL is solved. Any model writes a valid query. What breaks analytics agents is context,
access and trust. In this workshop you build an analytics agent in four levels, and at each level
one more part of the agent becomes yours.

**Status: draft.** The exercises run end to end. The deck, the generator for level 4 and the
facilitator material are still in progress. See [PLAN.md](PLAN.md).

## The four levels

| Level | What becomes yours | Folder | Hands-on |
|---|---|---|---|
| 1 Local | a skill file, data on your laptop | [`exercises/1-local/`](exercises/1-local/) | Claude Code and the DuckDB CLI load Parquet from S3, answer a question, build a local HTML dashboard |
| 2 Remote MCP | data and compute in MotherDuck, anyone can query | [`exercises/2-remote-mcp/`](exercises/2-remote-mcp/) | Same agent on the MotherDuck remote MCP server: attach the share, write a guide, save a Dive |
| 3 Custom MCP | the tool surface | [`exercises/3-custom-mcp/`](exercises/3-custom-mcp/) | A FastMCP server in front of MotherDuck's: forward three tools, add a domain tool, log every question |
| 4 Custom agent | the loop and the model | [`exercises/4-custom-agent/`](exercises/4-custom-agent/) | A 60-line agent loop on any OpenRouter model, using your level 3 tools |

Run instructions, measured turns and cost per level, and what is not tested yet:
[`exercises/README.md`](exercises/README.md).

## What you need

- A terminal and [Claude Code](https://docs.claude.com/en/docs/claude-code). The workshop
  OpenRouter key works with it (setup in [`exercises/README.md`](exercises/README.md)).
- The [DuckDB CLI](https://duckdb.org/docs/installation/) for level 1.
- A free [MotherDuck](https://motherduck.com) account for levels 2 to 4.
- [uv](https://docs.astral.sh/uv/) for the Python in levels 3 and 4.

Keys are read from the environment (`OPENROUTER_API_KEY`, `MOTHERDUCK_TOKEN`). Never commit them.
`.env` files are ignored.

## The data

Every participant draws a fictional company from the
[duckgen API](https://motherduck.com/duckgen/api/v1) (public, read-only, no auth). Each dataset
ships as Parquet on public S3 (level 1) and as a MotherDuck share (levels 2 to 4), with questions
and answer keys for grading. The exercises were tested on Gloamwick Studios
(`gaming-gloamwick-liveops`, S tier).

## Slides

**View the slides:** [symmetrical-barnacle-rkwr531.pages.github.io](https://symmetrical-barnacle-rkwr531.pages.github.io/)
(GitHub Pages, private: you need access to this repo). Every push to `main` that touches
`slides/` rebuilds it. The public copy will be
[mehdio.com/talks/next-data-stack-has-no-ui](https://mehdio.com/talks/next-data-stack-has-no-ui)
once the deck is merged on mehdio.com.

The source of truth is [`slides/`](slides/) in this repo. The mehdio.com deck
(`src/talks/no-ui-data-stack/` in the mehdio-website repo) is a copy: edit here, then copy
`slides/src/` and `slides/assets/` over.

```bash
cd slides
npm install
npm run build        # or: npm run watch
open dist/index.html
```

Keys: arrows to navigate, N for speaker notes, G to pick a slide, F for full screen, H to step
through code lines, R to reveal the guess slides. Slide text is in `slides/src/slides.json`,
visuals in `slides/src/Visuals.tsx`.

[`dive-deck/`](dive-deck/) holds the same deck as a MotherDuck Dive, with live charts on the
Gloamwick share.

## Repo layout

| Path | What it is |
|---|---|
| [`exercises/`](exercises/) | One folder per level, each run end to end |
| [`slides/`](slides/) | The workshop deck (React + esbuild, 1600 x 900) |
| [`dive-deck/`](dive-deck/) | The deck as a MotherDuck Dive |
| [`PLAN.md`](PLAN.md) | Organizers: abstract, agenda, checked facts, decisions, open questions |
| [`HANDOFF.md`](HANDOFF.md) | Organizers: how the plan evolved and where the facts came from |
| [`parked/duckoffee/`](parked/duckoffee/) | An earlier dataset kit for a longer data engineering format, set aside |
