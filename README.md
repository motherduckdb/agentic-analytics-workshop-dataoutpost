# Agentic analytics workshop

**The Next Data Stack Has No UI: Building Analytics Agents with Ducks.** A 90-minute hands-on
workshop by Mehdi Ouazza and Jacob Matson (MotherDuck), prepared for Data Outpost.

Text to SQL is solved. Any model writes a valid query. What breaks analytics agents is context,
access and trust. In this workshop you build an analytics agent in four levels, and at each level
one more part of the agent becomes yours.

**Status: draft.** The exercises ran end to end on 2026-11-02. Their prompts were rewritten on
2026-11-03 and need a rerun. Level 2 (2A without a guide, 2B with one) was tested on 2026-11-03. See [PLAN.md](PLAN.md#exercise-runs).

## The four levels

| Level | What becomes yours | Folder | Hands-on |
|---|---|---|---|
| 0 Setup | | [`exercises/0-setup/`](exercises/0-setup/) | Workshop key from the minter, a MotherDuck token, the tools |
| 1 Local | a skill file, data on your laptop | [`exercises/1-local/`](exercises/1-local/) | Your coding agent and the DuckDB CLI load Parquet from S3, answer the question, build a local HTML dashboard |
| 2 MotherDuck | data and compute in MotherDuck, anyone can query | [`exercises/2a-mcp/`](exercises/2a-mcp/), [`exercises/2b-guide/`](exercises/2b-guide/) | 2A: connect your agent to the MotherDuck MCP server and ask with the share in the prompt. 2B: add a guide and ask again |
| 3 Custom MCP | the tool surface | [`exercises/3-custom-mcp/`](exercises/3-custom-mcp/) | A FastMCP server in front of MotherDuck's: forwarded tools, a domain tool, a question log |
| 4 Custom agent | the loop and the model | [`exercises/4-custom-agent/`](exercises/4-custom-agent/) | A 60-line agent loop on the workshop key (GPT-6 Luna by default), using your level 3 tools |

Each folder has a README with the same numbered steps and the same prompts as its slide. The slide
build fails if they disagree. Index, dataset and questions: [`exercises/README.md`](exercises/README.md).

## What you need

- A terminal and the coding agent of your choice, for example
  [Claude Code](https://code.claude.com/docs/en/setup) or [Codex](https://developers.openai.com/codex/cli).
- No AI subscription? A workshop key from the [minter](https://motherduck.com/minter/w/next-data-stack-has-no-ui/):
  an OpenRouter key with $5 of credit for Claude Sonnet 5.5, Claude Haiku 5.5 and GPT-6 Luna. It
  also runs the level 4 agent.
- [uv](https://docs.astral.sh/uv/), which brings Python with it, then the [DuckDB CLI](https://duckdb.org/docs/installation/)
  1.5.6 and the MotherDuck CLI from the MotherDuck installer. MotherDuck does not accept DuckDB 2.0
  clients yet, so do not use Homebrew's DuckDB.
- A free [MotherDuck](https://motherduck.com) account for levels 2 to 4.

Setup steps: [`exercises/0-setup/`](exercises/0-setup/README.md). Keys are read from the environment
(`ANTHROPIC_AUTH_TOKEN`, `OPENROUTER_API_KEY`, `MOTHERDUCK_TOKEN`). Never commit them. `.env` files
are ignored.

## The data

Everyone works on one fictional company from [duckgen](https://motherduck.com/duckgen/api/v1):
Gloamwick Studios (`gaming-gloamwick-liveops`, S tier), a mobile game with a year of installs,
sessions, purchases, ads and live-ops events. All four levels were tested on it, and it ships four
answer keys for grading. It comes as Parquet on public S3 (level 1) and as a MotherDuck share
(levels 2 to 4).

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
