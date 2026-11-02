---
name: company-analytics
description: Answer business questions on a duckgen dataset with DuckDB, locally.
---

# Company analytics

1. Load the Parquet tables you need from S3 into a local DuckDB file (company.duckdb) with the DuckDB CLI. Set s3_region to us-east-1.
2. Read the tables and their columns before writing SQL.
3. Keep money in cents until the final SELECT.
4. Show the SQL you ran under every answer.
5. Build dashboards as one local HTML file (dashboard.html) with the numbers inlined.
