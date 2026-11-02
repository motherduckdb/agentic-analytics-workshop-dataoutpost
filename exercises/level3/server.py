# /// script
# requires-python = ">=3.11"
# dependencies = ["fastmcp==4.0.3"]
# ///
"""Level 3 starter: your own MCP server in front of MotherDuck's.

It follows the MotherDuck white-label guide: forward a few tools, rename them,
rewrite their descriptions, add your own tool, and log every question.

Run it as a stdio MCP server:   uv run server.py
The MotherDuck token comes from MOTHERDUCK_TOKEN and never reaches the agent.
"""

import json
import os
import sys
import time
from typing import Any

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport

UPSTREAM = "https://api.motherduck.com/mcp"
DATABASE = os.environ.get("COMPANY_DB", "gaming_gloamwick_liveops")
LOG = os.environ.get("QUESTION_LOG", "questions.jsonl")

mcp = FastMCP(
    "company-data",
    instructions=(
        "Data for Gloamwick Studios. Call how_we_count before writing SQL. "
        "Every ask_data call needs the user's question in plain words."
    ),
)


async def upstream(tool: str, args: dict[str, Any]) -> Any:
    # One session per call, so no client is shared between users.
    transport = StreamableHttpTransport(
        url=UPSTREAM,
        headers={"Authorization": f"Bearer {os.environ['MOTHERDUCK_TOKEN']}"},
    )
    async with Client(transport) as client:
        result = await client.call_tool_mcp(tool, args)
        return result.model_dump(by_alias=True, exclude_none=True)


def log(question: str, sql: str, outcome: str) -> None:
    with open(LOG, "a") as f:
        f.write(json.dumps({"ts": time.time(), "question": question, "sql": sql, "outcome": outcome}) + "\n")


@mcp.tool
async def ask_data(question: str, sql: str) -> Any:
    """Run one read-only DuckDB SQL query on the company database.

    question: the user's question, in their words. It is logged with the SQL.
    sql: DuckDB SQL. Money columns are integer cents.
    """
    result = await upstream("query", {"database": DATABASE, "sql": sql})
    log(question, sql, "error" if result.get("isError") else "ok")
    return result


@mcp.tool
async def list_company_tables() -> Any:
    """List the company's tables and what they hold."""
    return await upstream("list_tables", {"database": DATABASE})


@mcp.tool
async def describe_table(table: str) -> Any:
    """List the columns of one company table."""
    return await upstream("list_columns", {"database": DATABASE, "table": table})


@mcp.tool
async def how_we_count() -> Any:
    """Read the company's metric definitions before writing SQL."""
    return await upstream("get_query_guide", {})


@mcp.tool
async def read_definition(guide_uuid: str) -> Any:
    """Read one guide listed by how_we_count, by its UUID."""
    return await upstream("get_guide", {"uuid": guide_uuid})


# Your own tool: the SQL for a question the business asks every week.
@mcp.tool
async def live_ops_impact(question: str, days: int = 14) -> Any:
    """D7 retention and ARPDAU in the N days before and after each live-ops change, by platform.

    question: the user's question, in their words. It is logged.
    """
    sql = f"""
    SELECT e.event_name, e.start_date, m.platform,
           CASE WHEN m.metric_date < e.start_date THEN 'before' ELSE 'after' END AS period,
           round(100.0 * sum(d7_retained) FILTER (WHERE d7_matured)
                 / nullif(sum(installs) FILTER (WHERE d7_matured), 0), 2) AS d7_retention_pct,
           round((sum(iap_gross_cents) + sum(ad_revenue_millicents) / 1000.0) / sum(dau), 2) AS arpdau_cents
    FROM live_ops_events e
    JOIN daily_player_metrics m
      ON m.metric_date >= e.start_date - {int(days)} AND m.metric_date < e.start_date + {int(days)}
    GROUP BY ALL
    ORDER BY e.start_date, m.platform, period DESC
    """
    result = await upstream("query", {"database": DATABASE, "sql": sql})
    log(question, sql, "error" if result.get("isError") else "ok")
    return result


if __name__ == "__main__":
    print(f"company-data MCP server, upstream {UPSTREAM}, database {DATABASE}", file=sys.stderr)
    mcp.run()
