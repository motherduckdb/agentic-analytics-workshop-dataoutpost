# Plan

Status: draft, last updated 2026-11-01. Owners: Mehdi Ouazza and Jacob Matson (MotherDuck).

This file holds the original abstract, what we changed and why, the current agenda, the facts we
checked, the decisions taken and what is still open. The draft deck in `slides/` follows the same
agenda, and its speaker notes (press N) carry the same details per slide.

## The original abstract

> **The Next Data Stack Has No UI: Building End-to-End Analytics with Agents and Ducks**
> Mehdi Ouazza (MotherDuck) · Jacob Matson (MotherDuck)
>
> What if your next data platform is a conversation instead of a pile of dashboards and config
> screens? I'm not talking about a simple agent that runs SQL queries and returns answers.
>
> Today an agent can do much more: look at raw files, design a schema, deploy infrastructure, ingest
> the data, write transformations, run quality checks, answer questions, publish results, and tear
> down the infrastructure when it's done. So what are we actually building here: a data agent
> sitting on top of an existing stack, or a data stack that an agent builds and operates itself?
>
> In this hands-on workshop, you'll test that distinction yourself by getting an agent to build a
> working analytics stack from scratch, on your own laptop. No slides-only sections. You bring a
> terminal, an agent (Claude Code or similar), and a MotherDuck account. I bring the raw data, the
> prompts, and the failure modes.
>
> We'll work through it in four blocks:
>
> - **Local first.** Point the agent at a few raw files and DuckDB. Let it profile the data, propose
>   a schema, and ingest it. We'll compare what it came up with across the room.
> - **Transform and test.** Have the agent write the transformation layer and its own quality
>   checks, then break the data on purpose and watch how it recovers (or doesn't).
> - **Go to the cloud.** Move the data and workloads to MotherDuck when you need persistence or
>   collaboration, without opening a traditional data platform UI.
> - **Ship and tear down.** Publish something useful, then have the agent discard the
>   infrastructure it created.
>
> Between blocks we'll step back and look at why the DuckDB ecosystem works well for agentic
> workflows and where it falls apart: state, context, reproducibility, permissions, and
> observability. Each of these will show up in your own session, so we'll discuss them from what
> just happened on your screen rather than in the abstract.
>
> You'll leave with a working end-to-end stack you built through conversation, a repo of the
> prompts and guardrails that worked, and a clear opinion on which parts of the stack humans should
> still operate directly, and which parts can become an implementation detail the agent takes care
> of.

## What changed, and why

- **The slot is 90 minutes.** Four build blocks with an agent building ingestion, transforms and
  tests do not fit, and setup alone would eat a third of it.
- **Text to SQL is solved.** Every model writes valid SQL. What breaks analytics agents is
  context, access and trust. So the workshop teaches the fundamentals of an analytics agent and maps
  each one to a MotherDuck feature, with a short hands-on per fundamental.
- **The dataset comes from duckgen** (public S3, with answer keys) instead of the Duckoffee raw
  files built earlier. Duckoffee is kept in `parked/duckoffee/` for a longer data engineering format.
- **Hands-on runs in a hosted generator** after chapter 1, so nobody installs or deploys anything
  past the first 15 minutes. People tweak the components of their agent, paste a temporary key and
  get a unique link.
- **Access and risk management gets a full chapter.** When MotherDuck's isolated compute and shares
  with row and column security come up, people who were hesitant about AI on their data get
  interested. That reaction is the hook.

What still matches the abstract: local first with DuckDB, MotherDuck without a traditional UI,
shipping something (the agent link), teardown, the discussion themes (state, context,
reproducibility, permissions, observability) and the closing question about what humans should
still operate.

What no longer matches: "no slides-only sections" (each chapter opens with about 4 minutes of
talk), and the agent no longer builds the pipeline itself (Flights get one slide). The abstract can
change; a proposed version is at the end of this file.

## Agenda (90 minutes)

Two ideas first (what an agent is, what an analytics agent has to do), then four levels. At each
level one more part of the agent becomes the participant's own. Every level ends with a hands-on.

| Time | Part | What becomes yours | MotherDuck / DuckDB features | Hands-on |
|---|---|---|---|---|
| 0:00 | Intro | | duckgen API | 0. Draw your company: a duckgen dataset and one question |
| 0:06 | 01 The agent | | | Talk only. Sourced definitions, loop, anatomy, levels map |
| 0:18 | 02 The analytics job | | Flights, Dives, Guides, storage, MCP apps | Guess slides |
| 0:26 | Level 1 · Local | a skill file, data on your laptop | DuckDB 2.0 agent mode | 1. Load your Parquet from S3 into local DuckDB, transform, answer, local HTML dashboard |
| 0:40 | Level 2 · MotherDuck | data and compute in MotherDuck, anyone can query | remote MCP, Guides, Dives, Flights, Ducklings, shares, secure views | 2. Remote MCP, attach the share, write a guide, save a Dive, stretch: a Flight |
| 1:00 | Level 3 · Your tools | the tool surface | white-label MCP pattern | 3. FastMCP proxy: forward 3 tools, rename, add a domain tool, log the question |
| 1:12 | Level 4 · Your agent | the loop and the model | the generator, traces in MotherDuck | 4. Generator: pick model and tools, deploy a link, red team the neighbor, traces Dive |
| 1:24 | Wrap | | | Recap, discussion, references |

Between level 1 and level 2, two slides adapted from the self-hosting DuckDB talk: the boxes you
build to let anyone query (storage, compute, identity, access, context, pipelines, apps,
observability), then the same boxes run by MotherDuck.

| Level | Harness | Model | Tools | Data + compute | Who can use it |
|---|---|---|---|---|---|
| 1 Local | Claude Code (or opencode + workshop key) | managed | DuckDB CLI + skill | laptop | you |
| 2 MotherDuck | managed | managed | MotherDuck remote MCP + skill | MotherDuck | anyone you share with |
| 3 Your tools | managed | managed | your MCP server in front of MotherDuck's | MotherDuck | your users |
| 4 Your agent | your loop | any model, workshop OpenRouter key | your tools | MotherDuck | anyone with the link |

The six fundamentals from the previous plan are covered inside the levels: pipelines and storage in
level 1, context, data apps and access in level 2 (sharing is what makes them necessary),
observability in levels 3 and 4.

### Exercises from the duckgen API

`https://motherduck.com/duckgen/api/v1` is public, read-only, no auth. `/datasets/` lists 19
fictional companies (all `ready`, none `endorsed` on 2026-11-02), each with S3 Parquet
(`tiers[].s3.prefix`, for level 1) and a MotherDuck share (`tiers[].motherduck.attach`, for level
2). `/prompts/?slug=…&tier=s` returns questions with an `answerKey` pointer for grading. Each
participant draws a company and a question. The café stays the shared demo on the projector, so
the "same question, how many answers" comparison still works.

Rule: the agent never sees the answer key URL or the dataset `guide.md`. The guide contains the
answers. The grader fetches the key on its side.

### Where things live

The deck source moved to the mehdio-website repo (`src/talks/no-ui-data-stack/`, output at
`/talks/next-data-stack-has-no-ui`, PR #38 for previews). `slides/` in this repo is the older copy
and is no longer edited.

## Chapter 1 in detail: what an agent is

Chapter 1 takes 16 minutes (about 9 of talk, 7 of hands-on) because it builds the
vocabulary the rest of the workshop uses. Slide order: chatbot vs workflow vs agent, the loop, the
loop in pseudo code, the parts of an agent, the context window, MCP, the five places to put
instructions, a skill example, the harness, a hook example, what makes a full agent, DuckDB agent
mode, then two hands-on.

**Chatbot, workflow, agent.** The question that separates them: who decides the next step? A chatbot
is one model call and the human acts. A workflow is code with fixed steps that calls a model for
some of them. An agent lets the model pick the next step, call a tool, read the result and loop
until it is done. Anthropic's
[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) uses the
same split.

**The parts of an agent.**

| Part | What it is | In Claude Code | In the generator |
|---|---|---|---|
| Model | Writes the next message: text, or a tool call | Opus, Sonnet, Haiku | Model knob |
| Loop | Runs the tool call, sends the result back, repeats until the model answers | built in | the app server |
| Tools | Functions with a name, a description and an input schema | Bash, Read, Edit, MCP tools | MotherDuck MCP tools you enable |
| System prompt | Instructions sent first on every call | its own, plus CLAUDE.md | Prompt knob |
| Context | Everything in the window this turn | `/context` shows it | prompt, guide, chat, results |
| Harness | The program around the loop: permissions, hooks, sandbox, memory, compaction, subagents | Claude Code itself | the generator |
| Interface | Where a human talks to it | terminal, IDE, web | a chat page with a link |

**The context window.** The model is stateless. Each turn the harness sends the system prompt, the
tool definitions (every MCP tool adds its name, description and schema), memory files, skill
descriptions, the conversation and every tool result so far. Tool results are usually the biggest
part, which is why returning 10,000 rows hurts and why DuckDB's agent mode matters.

**MCP.** The Model Context Protocol is a standard way for a server to expose tools (plus resources
and prompts) to any client. The client lists the tools, puts their definitions in the context and
calls them when the model asks. MotherDuck's remote server (`api.motherduck.com/mcp`) works from
Claude Code, claude.ai, ChatGPT, Cursor or your own app. It also sends instructions at connect time,
with client-specific dive guides in the server code.

**Five places to tell an agent something.**

| Where you write it | Lives | Loaded | Written by |
|---|---|---|---|
| System prompt | in the app | every turn | the app builder |
| AGENTS.md / CLAUDE.md | in the repo | at session start | the team |
| Skill (`SKILL.md` folder, optional scripts) | in the harness | description always, body when needed | you, or a plugin |
| MCP server instructions | in the tool server | when the client connects | the tool vendor |
| Guide | in MotherDuck, next to the data | when the agent asks | the data owners |

Only the guide travels with the data to every agent that can query it. A skill is procedure (how to
work), a guide is meaning (what the data says). Skill plus guide is the smallest useful context
layer. Rules written in any of these five are text the model can ignore, which sets up chapter 5.

**The harness.** Permissions (allow, ask, deny), hooks (code before and after each tool call that
can block it), sandbox, memory files, context compaction, subagents. Same model, different harness,
different agent. Example on the slides: the PreToolUse guard from `parked/duckoffee` that blocks
cloud deletes until a human unlocks teardown (exit code 2 blocks the call and the model reads why).

**What makes a full agent.** Six checks, one per chapter: it picks its next step and acts through
tools; it knows what your business means; it lives where your users are; it can't slow down or break
anyone else; it only sees what it should; it leaves a trace you can check. A demo has the first one.
Production needs all six.

**Hands-on.** First the DuckDB CLI on the café Parquet from S3. Then in Claude Code: `/context`,
add the MotherDuck MCP (`claude mcp add MotherDuck --transport http
https://api.motherduck.com/mcp`), `/mcp` to sign in, `/context` again to see the tool definitions
grow, and ask the café question through MotherDuck. Check `/context` and `/mcp` on the Claude Code
version used on the day.

## Chapter 2 in detail: the analytics job and "no UI"

This chapter keeps the workshop about analytics, and it carries the title's thesis. Guess slides:
the room answers first, then the presenter presses R (or clicks REVEAL).

**Six tasks of an analytics agent, mapped to MotherDuck.**

| Task | What it covers | MotherDuck feature |
|---|---|---|
| Pipelines | Ingest and transform, on a schedule | Flights (Python runs on MotherDuck, scheduled or on demand; free plan is on demand only) |
| Data apps | Dashboards, charts, small tools | Dives |
| Context | What the data means | Guides |
| Storage | Where the data lives | MotherDuck databases, fully managed DuckLake, local DuckDB |
| Permissions & sandbox | What it can see, touch and break | Per-agent Ducklings, service accounts, read-only tokens, shares with secure views. Each Flight run gets its own isolated runtime |
| Observability | Covers all five | Flight Explainer, query history, traces stored in MotherDuck |

**The next data stack has no UI.** Each layer of the modern data stack ships two UIs: one to build
(connector screens, model editors, DAG editors, dashboard editors) and one to watch (sync status,
run history, dashboards, lineage). When an agent builds, the build UIs collapse into chat: in data,
describing the connector, the SQL, the schedule or the chart is enough. Some domains still need a
custom builder (video editing, visual design). The watch UIs stay, and three matter: dashboards,
pipeline runs (DAG style) and agent traces.

**MotherDuck's answer: chat to build, MCP apps to watch.** The MotherDuck MCP server ships MCP apps,
UIs rendered inside the chat client: the Dive viewer (`view_dive`) and the Flight Explainer run
viewer (`view_flight_run`, opened from `run_flight`, enabled for everyone in prod per the mono
history). Agent traces have no dedicated app: we store them in MotherDuck and read them with a Dive
(chapter 6). Demo idea: run a Flight from chat, watch it in the Flight Explainer, then open a Dive.

## The dataset: duckgen café

- Release `cafe-juniper-decisions`, S tier (about 100 MB):
  `s3://us-prd-motherduck-open-datasets/duckgen/cafe-juniper-decisions/20261025-a5155411-s-r1/`.
  An M tier exists (`20261026-7ea103ae-m-r1`).
- Tables: `shops`, `menu_items`, `item_daily`, `pilot_customer_daily`, `neighborhoods`, plus the
  derived `neighborhood_demand_daily`.
- Checked on the S tier: 1,764 shops, 7,726,320 `item_daily` rows from 2024-10-07 to 2026-10-06,
  176,400 pilot customers. Enough shops for a row filter per participant.
- Four questions with answer keys (`answer-keys.json` next to the Parquet): weekdays losing money
  to waste or stockouts, requested products missing from the menu, whether the loyalty pilot paid
  off, which neighborhood to expand into.
- Context traps already in the data: money is integer USD cents, Sunday rows exist with zero
  activity, pilot customer-days include zero visits, pilot visits are a separate sample and must not
  be added to shop revenue.
- `guide.md` ships with each release but contains the answer SQL and the planted stories. We write
  our own guide with definitions only and keep the answer keys for grading.
- No personal data in this dataset. Column security uses the cost columns instead
  (`unit_cost_cents`, `food_cost_cents`, `contribution_cents`, `commission_percent`): shop managers
  see revenue, HQ keeps the margins.
- 61 duckgen releases sit in the bucket, 24 of them with a `guide.md`. duckgen itself is internal
  (Google sign-in).

## How guides reach an agent today

Read from `mcp-server` on `origin/main` of the mono repo (fetched 2026-10-26).

- A guide is a markdown document stored in MotherDuck, with an optional topic folder. Private by
  default, shared with `set_guide_access` or `grant_access`. Underneath it is SQL:
  `MD_CREATE_GUIDE`, `MD_LIST_GUIDES` and friends.
- Nothing is injected into the agent's context. The agent has to ask, and the server points it
  there in four places:
  - `get_query_guide`: its description says "Call this before writing SQL to answer a data
    question". It returns the catalog of guides.
  - The `query` tool's description starts with a nudge toward guides.
  - `list_tables` returns `relatedGuides` (guides that reference objects in that database).
    `search_catalog` returns guides that match the search.
  - `get_flight_guide` and `get_dive_guide` include guides under the reserved `flights` and `dives`
    topics.
- The guide tools sit behind a feature flag. It is on for Mehdi's account (the claude.ai MotherDuck
  connector lists them). To confirm for the devrel org and participant accounts.
- Consequences for the workshop: whether a guide is read depends on the model following the nudge,
  which the trace shows live. A guide under `flights` is procedure ("how we ingest here"), which
  answers "can a guide act as a harness?" for ingestion. A custom app can load guides with SQL and
  put them in its system prompt, which the generator's Context knob demonstrates.

## DuckDB 2.0 agent mode

Source: [Agent Mode in the DuckDB CLI](https://duckdb.org/2026/10/09/agent-mode),
[docs](https://duckdb.org/docs/2.0/clients/cli/agent_mode).

- The 2.0 CLI detects an agent (Claude Code, Codex, Cursor, Gemini CLI, Copilot, or `AI_AGENT`
  set) and switches to compact Markdown tables, JSON errors, explicit truncation notices and a cost
  estimate before long queries. `-agent` and `-no-agent` force it, `DUCKDB_AGENT_MODE` also works.
- DuckDB's TPC-H test: 123.6k to 50.8k tokens of DuckDB output read by the agent (59% less), all 132
  runs correct, slightly more turns.
- Needs a 2.0 binary. The repo pins DuckDB 1.5.x in `pyproject.toml` until MotherDuck supports 2.0
  clients (open question).

## The generator

One hosted app where each participant builds an analytics agent and gets a unique link. Nobody
deploys anything.

- **Built from /try patterns** (`packages/try-motherduck` in the website repo): server-side loop
  with a per-session MotherDuck MCP client authed by a bearer token, secrets in an encrypted cookie
  or encrypted in Postgres, seven-day share links backed by an encrypted capability, a live panel
  built from streamed tool calls, temporary orgs via `new.motherduck.com`.
- **Knobs**, one per component:

  | Component | Knob | What people learn |
  |---|---|---|
  | Model | Haiku, Sonnet, Opus | Cost and speed vs answer quality |
  | Data | Which database or share | The agent only knows what it can reach |
  | Context | No guide, guide as a tool, guide in the system prompt | Why guides change the number |
  | Tools | query, list_tables, dives, query_rw | What the agent can do is set by its tool list |
  | Harness | Max steps, row cap, read-only, confirm before writes | Limits enforced by the app |
  | Identity | HQ or shop manager | Who it runs as decides what it sees |
  | Interface | Name, starter questions, look | What the end user sees |
  | Prompt | Editable, final assembled prompt shown | What the model actually receives |

- **Preview** next to the editor, with a trace panel showing every turn of the loop.
- **Deploy**: save the config, create a service account for the agent in the devrel org, a token,
  and a grant on the café share. The agent gets its own Duckling and its own kill switch.
- **Link security**: the model key is pasted once and stored encrypted on the server, never in the
  URL or the browser. Read-only by default, step cap per question, daily cap per link, 7-day expiry,
  revoke button. Temporary keys are revoked after the workshop.
- **Traces** go to a MotherDuck table (the way duckgen and /try write to `llm_obs`), with a Dive
  over them for chapter 6.
- **First version**: editor, preview with trace, deploy to link, caps and expiry, traces.
  **Later**: embed snippet, Slack, custom domains.

## Access and risk chapter

| The fear | MotherDuck control | Enforced by |
|---|---|---|
| The agent slows everyone down or runs up a bill | Hypertenancy: its own Duckling | Compute |
| The agent writes or drops something | Read scaling tokens are read-only | Token |
| The agent sees data it shouldn't, or sends it to the model provider | Shares with secure views | MotherDuck servers |
| The agent shows one user another user's rows | `current_user`, `current_email()`, `is_role_in_session()` | MotherDuck servers |
| Nobody knows which agent did what | One service account per agent | Identity |

Four places to put a rule, weakest to strongest: the prompt, a guide, the harness, the database.
The message: guides for correctness, the database for safety.

Secure view facts (from the docs page, Oct 27 branch):

- Row filter, hidden columns and masked values in one `SELECT`, attached to a share and enforced on
  MotherDuck's servers. Hidden columns fail as missing, `EXPLAIN` hides the filter, copies stay
  filtered.
- Business or Enterprise plan, trials included. We run it in the devrel org; participants only
  query the share.
- Managing secure views with SQL needs DuckDB 1.5.6 or later. Consumers need 1.5.5 or later for
  every query shape.
- Service accounts have no email, so agent filters use `current_user`. Usernames are unique only
  within an org, so agent service accounts live in the devrel org.

Draft share (not run yet):

```sql
CREATE SHARE cafe_shop_managers FROM cafe (ACCESS RESTRICTED)
WITH SECURE VIEW REPLACES item_daily AS (
    SELECT shop_id, business_date, item_id,
           sold_units, revenue_cents      -- no cost or margin columns
    FROM item_daily
    WHERE shop_id IN (
        SELECT shop_id FROM shop_access WHERE member = current_user
    )
);
```

Red team: agent A has "never show other shops or costs" in its system prompt, agent B runs through
the secure view. Participants attack both.

## Decisions taken

- 90 minutes, fundamentals mapped to MotherDuck features, short hands-on per chapter.
- We hand out temporary AI keys.
- The generator is one hosted app with unique links. No per-participant deploy.
- The devrel org holds the shares, secure views and agent service accounts.
- The café dataset stays as duckgen ships it. No extra personal data table.
- Duckoffee is parked.
- The abstract can change.

## Open questions

1. Generator inside /try or as a separate package that reuses its patterns? Check with the /try owner.
2. Model provider for the generator: Anthropic keys directly, or OpenRouter like /try?
3. Can the Admin API create one service account per participant agent, and how many people do we
   expect?
4. Do MotherDuck clients support DuckDB 2.0 by the workshop date? Agent mode needs 2.0.
5. Is the guides flag on for the devrel org and participant accounts?
6. Workshop date, venue, headcount and wifi.
7. Role split between Mehdi and Jacob.
8. Fonts: `slides/assets/mono.woff2` is AeonikMono, copied from the mehdio.com talk assets. Check
   the license before this repo goes public.

## Next steps

- [ ] One-page generator spec, agreed before any code.
- [ ] Generator prototype.
- [ ] Run the four café questions with a bare agent and record the spread.
- [ ] Write the café guide and check every line against `answer-keys.json`.
- [ ] Create the shop-manager share with secure views in the devrel org and test the red team.
- [ ] Script the noisy neighbor demo.
- [ ] Traces table and the Dive over it.
- [ ] Replace the pseudo code on slide 6 with the real loop once the generator code exists.
- [ ] Exercise notes per chapter.
- [ ] Demo for chapter 2: a small café ingestion Flight run from chat, shown in the Flight Explainer.
- [ ] Full dry run with timings.
- [ ] Update the abstract.

## Proposed abstract (draft)

> **The Next Data Stack Has No UI: Building Analytics Agents with Ducks**
> Mehdi Ouazza (MotherDuck) · Jacob Matson (MotherDuck)
>
> Text to SQL is solved. Any model can write a query. Getting the right number, for the right
> person, without putting your warehouse at risk is where analytics agents still fail.
>
> In this 90-minute hands-on workshop you build an analytics agent end to end and look at each
> piece it needs: the loop, context, an interface, isolated compute, access control and
> observability. For each one we show what MotherDuck gives you, then you try it.
>
> You start local, with DuckDB and a coding agent on a public dataset. You move to MotherDuck,
> write a guide that fixes your agent's answers, and turn it into your own chat agent with a link
> you can share. Then you try to break your neighbor's agent and see which rules hold: the ones in
> the prompt, or the ones in the database.
>
> Bring a laptop. We bring the data, the API keys and the failure modes. You leave with a working
> agent, the guide and guardrails that worked, and an opinion on what humans should still operate.
