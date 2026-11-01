# Handoff

Context for whoever (human or agent) picks this up next, for example on another machine. Read
[PLAN.md](PLAN.md) for the plan itself. This file covers how we got there and what to know before
continuing.

Written 2026-11-01 at the end of the first working session (Mehdi with Claude Code, on the Mac).

## How the plan evolved

1. Started from the abstract (in PLAN.md): an agent builds a full stack from raw files in four
   blocks. Built the Duckoffee kit for that (messy raw exports, six breaks, a grader that names the
   mistake, guard and trace hooks). It works and is tested, now in `parked/duckoffee/`.
2. Mehdi's direction: text to SQL is solved, so teach what an agent is (the loop, the harness, MCP,
   skills, guides), show ingestion and observability, then interfaces. Guides should be a core
   experience.
3. Constraints given: 90 minutes, we hand out temporary AI keys, the abstract can change, local
   DuckDB and DuckDB 2.0 agent mode must be covered, data comes from duckgen on public S3.
4. Mehdi does not want participants deploying anything (no Vercel per person). Instead: one hosted
   "generator" where people tweak the components of their agent, paste a key and get a unique link.
5. Mehdi's field experience: talking about MotherDuck's isolated compute (hypertenancy) and shares
   with row and column security is what turns hesitant people into interested ones. Access and risk
   got its own chapter.
6. Final structure: fundamentals of an analytics agent, each mapped to a MotherDuck feature, with a
   short hands-on. The devrel org holds the shares, secure views and service accounts. No extra
   personal data table: column security uses the café cost columns.
7. Chapter 1 was then expanded on request: chatbot vs workflow vs agent, the parts of an agent, the
   context window, MCP, the five places to put instructions (system prompt, AGENTS.md, skill, MCP
   server instructions, guide), the harness, hooks, and what makes a full agent.

## Where the facts came from

Paths are on Mehdi's Mac. They may not exist on other machines.

- Guides and MCP tools: `~/repos/motherduckdb/mono`, `mcp-server/` on `origin/main` (fetched
  2026-10-26). The local checkout was from June, so files were read with `git show origin/main:...`.
- duckgen: worktrees `~/repos/motherduckdb/motherduck-website-duckgen*`, package
  `packages/duckgen`. The scenarios branch adds the café spec and portable dataset guides. The
  public bucket was listed with DuckDB (`glob('s3://us-prd-motherduck-open-datasets/duckgen/*/*/manifest.json')`).
- /try (the base for the generator): `packages/try-motherduck` in the website repo, README.
- Secure views, hypertenancy, read scaling: `~/repos/motherduckdb/motherduck-docs-secure-views-svg`,
  `documentation/key-tasks/sharing-data/secure-views.md` and `documentation/concepts/`.
- DuckDB 2.0 agent mode: duckdb.org blog post and docs (links in PLAN.md).
- Brand and deck engine: `~/repos/mehd-io/mehdio-website/src/talks/jev-analytics` and
  `system-one-models` (the Oct 29 talk).

## Working preferences

- Writing: no em dashes or en dashes, no LLM-style punchlines, plain sentences. Slide text short,
  details in speaker notes.
- Git: check repo visibility before committing or pushing (`gh repo view --json visibility`).
  Without a remote, treat it as public and get explicit approval of the diff first. Stage explicit
  paths. Never merge PRs.
- Never print or commit a MotherDuck token or AI key.
- Product facts on slides must come from code, docs or a query that was run. Mark untested items as
  drafts (the secure view SQL and the café guide are drafts).

## Environment notes (Mac sandbox)

- `uv` needs `UV_CACHE_DIR=$TMPDIR/uv-cache`, `npm` needs `--cache $TMPDIR/npm-cache`.
- Binding local ports is blocked, so the deck builds as a classic script and opens from disk.
- `herdr-continuity move` packs the repo of the session's first working directory. The first
  session started in `mono`, so it is the wrong tool to move this work. Copy the repo instead.

## Next

The first open item is a one-page generator spec, to agree on before any code. Full list in
PLAN.md under "Next steps" and "Open questions".
