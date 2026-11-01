# Data contract: Duckoffee daily venue revenue

This is the business side of the deal. It says what the numbers mean. It does not say how the raw
files are shaped or what is wrong with them: finding that out is the job.

`uv run tools/check.py` grades your warehouse against this contract.

## The table

`marts.daily_venue_revenue`, a table or a view. One row per venue per business date with any sales.

| column | type | meaning |
|---|---|---|
| `venue_id` | VARCHAR | Venue code as in `venues.csv` (`AMS`, `NYC`, ...) |
| `business_date` | DATE | Calendar date at the venue, in the venue's own time zone |
| `net_revenue_eur` | DECIMAL(12,2) | Net revenue for that venue and date, in euros |
| `order_count` | BIGINT | Number of customer sales transactions |

## Definitions

**Net revenue** is what customers paid for goods:

- quantity times unit price, minus discounts
- minus refunds, booked on the date the refund happened
- excluding tips
- excluding staff training transactions (they are not real sales)
- each sale counted once, however many times it appears in the exports

**Currency.** Report in EUR. Convert other currencies with the ECB reference rate of the business
date. On days without a published rate (weekends, holidays), use the latest rate published before it.

**Order count** counts sales transactions: not refunds, not training transactions.

**Completeness.** Never publish a venue-day you know is incomplete. A missing row is better than a
wrong one. Say what you held back and why.

## Out of scope

Loyalty members, product margins and conference attendance are available for analysis, but they are
not part of this contract. Customer personal data (names, emails) must never leave the local warehouse.
