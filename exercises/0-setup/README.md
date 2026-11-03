# Hands-on 0: set up

Time: 5 minutes. Do it before the workshop if you can.

Everyone works on the same data: **Gloamwick Studios**, a fictional mobile game from duckgen. See
[the exercises index](../README.md) for the dataset and the questions.

What you need: a coding agent (Claude Code, Codex…) and [uv](https://docs.astral.sh/uv/). uv
brings Python with it, so there is nothing else to install for the Python parts. Already have an
agent? Ask it to install uv for you.

Setup adds the [DuckDB CLI](https://duckdb.org/docs/installation/) at version 1.5.6 (the latest
version MotherDuck supports) and the
[MotherDuck CLI](https://motherduck.com/docs/getting-started/interfaces/connect-query-from-duckdb-cli/).

## Steps

The prompt is the same as on the slide. Paste it as it is.

1. Install uv, then DuckDB 1.5.6 and the MotherDuck CLI with the
   [MotherDuck installer](https://motherduck.com/docs/getting-started/interfaces/connect-query-from-duckdb-cli/),
   then put DuckDB 1.5.6 on your PATH for good:

   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   curl -s https://install.motherduck.com | sh
   echo 'export PATH="$HOME/.duckdb/cli/1.5.6:$PATH"' >> ~/.zshrc
   ```

   When the installer offers to fetch a MotherDuck token, say yes. It opens MotherDuck in your
   browser (create a [free account](https://app.motherduck.com) there if you have none) and saves
   the token in your shell profile. On bash, write the last line to `~/.bashrc` instead.

2. Install a coding agent, any one you like, for example
   [Claude Code](https://code.claude.com/docs/en/setup) or
   [Codex](https://developers.openai.com/codex/cli). You do not need this repo yet: levels 1 and 2
   link to the files they use, and level 3 clones it.

3. Open a new terminal, so it loads your profile. No AI subscription? Claim a workshop key at
   [the minter](https://motherduck.com/minter/w/next-data-stack-has-no-ui/) and paste its exports
   in that terminal. The key is an OpenRouter key with $5 of credit, for three models only: Claude
   Sonnet 5.5, Claude Haiku 5.5 and GPT-6 Luna. The minter page shows the exports for Claude Code:

   ```sh
   export ANTHROPIC_BASE_URL=https://openrouter.ai/api
   export ANTHROPIC_AUTH_TOKEN=<your workshop key>
   export ANTHROPIC_API_KEY=""
   export ANTHROPIC_MODEL=anthropic/claude-sonnet-5.5
   export ANTHROPIC_SMALL_FAST_MODEL=anthropic/claude-haiku-5.5
   export ANTHROPIC_DEFAULT_HAIKU_MODEL=anthropic/claude-haiku-5.5
   ```

4. Make a folder for the workshop, start your agent in it, and let it check your setup:

   ```sh
   mkdir gloamwick && cd gloamwick
   ```

   Paste:

   > Check my workshop setup. Use the DuckDB CLI to print its version and to run SHOW DATABASES on md:, then run uv --version and motherduck status. Tell me what is missing. Never print a token.

## Done when

Your agent reports DuckDB v1.5.6, lists your MotherDuck databases, finds uv, and
`motherduck status` shows you signed in.

## Why the PATH line goes in your profile

`export` only lasts for the terminal you type it in. Coding agents run commands in shells they
start themselves, from your shell profile, so a PATH set by hand in one terminal may not reach
them. The line in `~/.zshrc` does. The installer needs it because 1.5.6 is not DuckDB's latest
release: it lands in `~/.duckdb/cli/1.5.6` and is not put on your PATH.

The workshop key exports are different: the agent itself reads them when it starts, so pasting
them in the terminal you start the agent from is enough.

## Prefer Homebrew?

- `brew install uv` works instead of the uv install script.
- Do not `brew install duckdb`: Homebrew ships DuckDB 2.0, and MotherDuck does not accept 2.0
  clients yet. Use the MotherDuck installer above.
- On Windows, run the installer from PowerShell: `irm https://install.motherduck.com | iex`.

## Notes

- Never paste a key into a prompt or a file in this repo. Keys stay in environment variables.
- If you skipped the token in the installer, run `motherduck login`, or create an
  [access token](https://app.motherduck.com/settings/tokens) and export it as `MOTHERDUCK_TOKEN`.
- Your agent may ask before it runs `duckdb`, `uv` or `motherduck`. Allow it.
- Sonnet 5.5 costs 20 times more than Haiku 5.5 and GPT-6 Luna. If your credit runs low, switch
  `ANTHROPIC_MODEL` to `anthropic/claude-haiku-5.5`.
- Keys expire when the workshop window ends. Save your work.
