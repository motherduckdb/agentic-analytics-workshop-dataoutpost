-- Reference build: data/raw -> raw -> staging -> marts. Facilitator only.
-- Full refresh from files on every run: idempotent, picks up late and re-delivered files.
-- Run from the repo root:  duckdb facilitator/solution/solution.duckdb -f facilitator/solution/build.sql
.bail on

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- ---------------------------------------------------------------------------------------------
-- raw: land everything as text, keep the source file name
-- ---------------------------------------------------------------------------------------------
CREATE OR REPLACE TABLE raw.venues AS
SELECT * FROM read_csv('data/raw/venues.csv', all_varchar = true);

CREATE OR REPLACE TABLE raw.squareduck_lines AS
SELECT * FROM read_csv('data/raw/pos/squareduck/*/*.csv',
                       union_by_name = true, filename = true, all_varchar = true, header = true);
-- the landing contract: columns that newer exports add or rename always exist, even before they show up
ALTER TABLE raw.squareduck_lines ADD COLUMN IF NOT EXISTS quantity VARCHAR;
ALTER TABLE raw.squareduck_lines ADD COLUMN IF NOT EXISTS tip_cents VARCHAR;

CREATE OR REPLACE TABLE raw.kassa_lines AS
SELECT * FROM read_csv('data/raw/pos/kassa/*/*.csv',
                       delim = ';', header = true, encoding = 'latin-1', union_by_name = true,
                       filename = true, all_varchar = true, null_padding = true);

CREATE OR REPLACE TABLE raw.fx AS
SELECT * FROM read_csv('data/raw/fx/ecb_eurusd_daily.csv', all_varchar = true);

CREATE OR REPLACE TABLE raw.menu AS
SELECT * FROM read_json('data/raw/catalog/menu.json');

CREATE OR REPLACE TABLE raw.conferences AS
SELECT * FROM read_parquet('data/raw/conferences/conferences.parquet');

CREATE OR REPLACE TABLE raw.loyalty_members AS
SELECT * FROM read_json('data/raw/loyalty/members.ndjson', format = 'newline_delimited');

-- ---------------------------------------------------------------------------------------------
-- staging
-- ---------------------------------------------------------------------------------------------
CREATE OR REPLACE TABLE staging.venues AS
SELECT venue_id, venue_name, city, country, timezone, currency, pos_system,
       opened_on::DATE AS opened_on, nullif(closed_on, '')::DATE AS closed_on
FROM raw.venues;

CREATE OR REPLACE TABLE staging.products AS
SELECT i.sku, i.name AS product_name, c.category, i.kassa_article_no::VARCHAR AS kassa_article_no,
       i.unit_cost_eur, i.tags
FROM raw.menu, unnest(categories) AS u(c), unnest(c.items) AS v(i);

CREATE OR REPLACE TABLE staging.fx_usd_per_eur AS
SELECT TIME_PERIOD::DATE AS rate_date, OBS_VALUE::DOUBLE AS usd_per_eur
FROM raw.fx WHERE CURRENCY = 'USD' AND CURRENCY_DENOM = 'EUR' AND OBS_VALUE IS NOT NULL;

-- Kassa files carry a 'Summe' control total. A file is complete only if it has one and it reconciles.
CREATE OR REPLACE TABLE staging.kassa_file_audit AS
SELECT filename,
       count(*) FILTER (WHERE Bon_Nr = 'Summe') AS footer_rows,
       sum(replace(Gesamt, ',', '.')::DECIMAL(14, 2)) FILTER (WHERE Bon_Nr = 'Summe') AS footer_total,
       sum(try_cast(replace(Gesamt, ',', '.') AS DECIMAL(14, 2))) FILTER (WHERE Bon_Nr <> 'Summe') AS lines_total,
       count(*) FILTER (WHERE Bon_Nr <> 'Summe' AND (Storno IS NULL OR Gesamt IS NULL)) AS broken_rows
FROM raw.kassa_lines GROUP BY filename;

CREATE OR REPLACE TABLE staging.quarantined_files AS
SELECT filename, 'kassa file incomplete: no reconciling Summe footer' AS reason
FROM staging.kassa_file_audit
WHERE footer_rows <> 1 OR broken_rows > 0 OR footer_total IS DISTINCT FROM lines_total;

CREATE OR REPLACE TABLE staging.pos_lines AS
WITH sq AS (
    SELECT
        'squareduck' AS pos_system,
        venue_code AS venue_id,
        order_id,
        line_no::INTEGER AS line_no,
        sold_at_utc::TIMESTAMPTZ AS sold_at,
        sku,
        NULL::VARCHAR AS kassa_article_no,
        coalesce(qty, quantity)::INTEGER AS qty,
        -- one POS firmware sends dollars in *_cents columns; detect by the decimal point
        CASE WHEN unit_price_cents LIKE '%.%' THEN round(unit_price_cents::DECIMAL(12, 2) * 100)
             ELSE unit_price_cents::DECIMAL(12, 2) END / 100 AS unit_price,
        CASE WHEN discount_cents LIKE '%.%' THEN round(discount_cents::DECIMAL(12, 2) * 100)
             ELSE discount_cents::DECIMAL(12, 2) END / 100 AS discount,
        currency,
        staff_id = 'TRAINING' AS is_training,
        nullif(refund_of, '') IS NOT NULL AS is_refund,
        nullif(loyalty_id, '') AS loyalty_id,
        unit_price_cents LIKE '%.%' AS had_unit_fix,
        filename
    FROM raw.squareduck_lines
    QUALIFY row_number() OVER (PARTITION BY venue_code, order_id, line_no ORDER BY filename) = 1
),
kassa AS (
    SELECT
        'kassa' AS pos_system,
        regexp_extract(filename, 'Export_([A-Z]{3})_', 1) AS venue_id,
        Bon_Nr AS order_id,
        Pos::INTEGER AS line_no,
        timezone(v.timezone, strptime(Datum || ' ' || Uhrzeit, '%d.%m.%Y %H:%M:%S')) AS sold_at,
        NULL AS sku,
        Artikel_Nr AS kassa_article_no,
        Menge::INTEGER AS qty,
        replace(Einzelpreis, ',', '.')::DECIMAL(12, 2) AS unit_price,
        replace(Rabatt, ',', '.')::DECIMAL(12, 2) AS discount,
        'EUR' AS currency,
        Training = 'J' AS is_training,
        Storno = 'J' AS is_refund,
        nullif(Kundenkarte, '') AS loyalty_id,
        false AS had_unit_fix,
        filename
    FROM raw.kassa_lines k
    JOIN staging.venues v ON v.venue_id = regexp_extract(k.filename, 'Export_([A-Z]{3})_', 1)
    WHERE Bon_Nr <> 'Summe'
      AND filename NOT IN (SELECT filename FROM staging.quarantined_files)
),
unioned AS (
    SELECT * FROM sq UNION ALL BY NAME SELECT * FROM kassa
)
SELECT u.* EXCLUDE (sku, sold_at),
       coalesce(u.sku, p.sku) AS sku,
       u.sold_at,
       timezone(v.timezone, u.sold_at)::DATE AS business_date,
       u.qty * u.unit_price - u.discount AS net_amount
FROM unioned u
JOIN staging.venues v USING (venue_id)
LEFT JOIN staging.products p ON p.kassa_article_no = u.kassa_article_no;

CREATE OR REPLACE TABLE staging.sales_lines AS
SELECT l.*,
       CASE WHEN l.currency = 'EUR' THEN l.net_amount ELSE l.net_amount / fx.usd_per_eur END AS net_amount_eur
FROM staging.pos_lines l
ASOF LEFT JOIN staging.fx_usd_per_eur fx ON l.business_date >= fx.rate_date
WHERE NOT l.is_training;

-- ---------------------------------------------------------------------------------------------
-- marts
-- ---------------------------------------------------------------------------------------------
CREATE OR REPLACE TABLE marts.daily_venue_revenue AS
SELECT venue_id,
       business_date,
       round(sum(net_amount_eur), 2)::DECIMAL(12, 2) AS net_revenue_eur,
       count(DISTINCT order_id) FILTER (WHERE NOT is_refund) AS order_count
FROM staging.sales_lines
GROUP BY ALL;

CREATE OR REPLACE TABLE marts.product_daily_sales AS
SELECT s.venue_id, s.business_date, coalesce(s.sku, 'UNKNOWN') AS sku,
       coalesce(p.product_name, 'Unknown product') AS product_name, coalesce(p.category, 'Unknown') AS category,
       sum(s.qty) AS units, round(sum(s.net_amount_eur), 2)::DECIMAL(12, 2) AS net_revenue_eur
FROM staging.sales_lines s LEFT JOIN staging.products p USING (sku)
GROUP BY ALL;

CREATE OR REPLACE TABLE marts.venues AS
SELECT venue_id, venue_name, city, country, currency, pos_system, opened_on, closed_on
FROM staging.venues;

CREATE OR REPLACE TABLE marts.conference_days AS
SELECT c.conference_id, c.conference_name, c.venue_id, d::DATE AS business_date, c.expected_attendance, c.tags
FROM raw.conferences c, generate_series(c.start_date, c.end_date, INTERVAL 1 DAY) AS g(d)
WHERE c.status = 'confirmed';
