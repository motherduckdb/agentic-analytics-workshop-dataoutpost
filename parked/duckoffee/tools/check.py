#!/usr/bin/env python3
"""Contract checker for marts.daily_venue_revenue.

Compares your table with the answer key for whatever deliveries currently sit in data/raw,
then tries to explain every mismatch by matching your numbers against known mistakes
(duplicates kept, UTC dates, cents, missing FX conversion, ...).

Usage:
  uv run tools/check.py                           # local workshop.duckdb
  uv run tools/check.py --db md:duckoffee         # MotherDuck (needs motherduck_token)
  uv run tools/check.py --json                    # machine-readable result

Agents: run this, read the output, do not read the answer key it uses.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
KEY = ROOT / "facilitator" / "answer_key"
BASE_END = date(2026, 10, 31)

REQUIRED = {"venue_id", "business_date", "net_revenue_eur", "order_count"}

SQ_FLAGS = ["keep_dups", "keep_tests", "drop_refunds", "cents", "utc_date"]
KASSA_FLAGS = ["keep_tests", "drop_refunds", "kassa_x100", "kassa_footer"]
FX_MODES = ["asof", "none", "inverted", "exact_only"]
BREAK_TOGGLES = ["resend_double", "tips_included", "renamed_qty_null", "units_unfixed", "orphan_dropped",
                 "truncated_published"]

EXPLAIN = {
    "keep_dups": "duplicate POS lines kept (export overlap + sync retries; dedupe on order_id + line_no)",
    "keep_tests": "staff training transactions counted as sales",
    "drop_refunds": "refunds ignored (net revenue must subtract them)",
    "cents": "SquareDuck amounts are cents and were not divided by 100",
    "utc_date": "business_date taken from the UTC timestamp instead of the venue's local time",
    "kassa_x100": "Kassa decimal-comma amounts parsed as cents (x100)",
    "kassa_footer": "Kassa 'Summe' total row loaded as a sale",
    "fx:none": "USD amounts summed as if they were EUR (no FX conversion)",
    "fx:inverted": "FX applied the wrong way round (multiplied by USD per EUR instead of dividing)",
    "fx:exact_only": "FX joined on exact date only: weekend USD sales lost (use the latest rate on or before the date)",
    "resend_double": "the re-delivered AMS file '2026-11-01 (1).csv' was counted twice",
    "tips_included": "tips counted as revenue (contract excludes tips)",
    "renamed_qty_null": "SquareDuck renamed qty to quantity: new files loaded with NULL quantities",
    "units_unfixed": "NYC 2026-11-03 file sends dollars in unit_price_cents: silent 100x drop not caught",
    "orphan_dropped": "sales of a SKU missing from menu.json were dropped (inner join to the catalog?)",
    "truncated_published": "a truncated file (BER 2026-11-05) was published as if complete",
}


def tolerance(truth: float) -> float:
    return max(1.0, abs(truth) * 0.001)


def connect(db: str):
    if db.startswith("md:"):
        if not (os.environ.get("motherduck_token") or os.environ.get("MOTHERDUCK_TOKEN")):
            sys.exit("motherduck_token is not set: export it before checking a MotherDuck database")
        return duckdb.connect(db)
    path = Path(db)
    if not path.exists():
        sys.exit(f"{db} does not exist yet. Build your warehouse first.")
    return duckdb.connect(str(path), read_only=True)


def present_files() -> set[str]:
    manifest = json.loads((KEY / "manifest.json").read_text())
    files = set()
    for d in manifest.values():
        for f in d["files"]:
            if (RAW / f).exists():
                files.add(f)
    return files


def applied_deliveries(files: set[str]) -> list[str]:
    manifest = json.loads((KEY / "manifest.json").read_text())
    return [name for name, d in manifest.items() if all(f in files for f in d["files"])]


def load_key(files: set[str]):
    k = duckdb.connect()
    k.execute("CREATE TABLE present_files (f VARCHAR)")
    k.executemany("INSERT INTO present_files VALUES (?)", [[f] for f in sorted(files)])
    k.execute(f"""
        CREATE TABLE lines AS
        SELECT l.*,
               row_number() OVER (PARTITION BY venue_id, order_id, line_no
                                  ORDER BY is_resend_copy, is_dup, file_rel) > 1 AS extra_copy
        FROM read_parquet('{KEY / 'lines.parquet'}') l
        WHERE file_rel IN (SELECT f FROM present_files)
    """)
    k.execute(f"""
        CREATE TABLE footers AS
        SELECT * FROM read_parquet('{KEY / 'footers.parquet'}') WHERE file_rel IN (SELECT f FROM present_files)
    """)
    truth = {}
    for v, d, rev, n in k.execute("""
        SELECT venue_id, local_date,
               round(sum(CASE WHEN currency = 'USD' THEN net_minor / 100.0 / fx_asof_local ELSE net_minor / 100.0 END), 2),
               count(DISTINCT order_id) FILTER (WHERE NOT is_refund)
        FROM lines
        WHERE NOT extra_copy AND NOT is_test AND NOT quarantine_expected
        GROUP BY ALL
    """).fetchall():
        truth[(v, d)] = (float(rev), int(n))
    buckets = k.execute("""
        SELECT venue_id, pos_system, currency, local_date, utc_date, extra_copy, is_resend_copy, is_test, is_refund,
               raw_major_units, is_orphan_sku, quarantine_expected, schema_v2,
               fx_asof_local, fx_exact_local, fx_asof_utc, fx_exact_utc,
               sum(net_minor)::BIGINT, sum(tip_minor)::BIGINT
        FROM lines GROUP BY ALL
    """).fetchall()
    footers = k.execute("SELECT venue_id, local_date, total_minor FROM footers").fetchall()
    order_variants = {}
    for name, where, date_col in [
        ("keep_tests", "NOT extra_copy AND NOT quarantine_expected", "local_date"),
        ("count_refunds", "NOT extra_copy AND NOT is_test AND NOT quarantine_expected", "local_date"),
        ("utc_date", "NOT extra_copy AND NOT is_test AND NOT quarantine_expected", "utc_date"),
        ("line_count", "NOT extra_copy AND NOT is_test AND NOT quarantine_expected", "local_date"),
    ]:
        if name == "count_refunds":
            sql = f"SELECT venue_id, {date_col}, count(DISTINCT order_id) FROM lines WHERE {where} GROUP BY ALL"
        elif name == "line_count":
            sql = f"SELECT venue_id, {date_col}, count(*) FILTER (WHERE NOT is_refund) FROM lines WHERE {where} GROUP BY ALL"
        else:
            sql = f"SELECT venue_id, {date_col}, count(DISTINCT order_id) FILTER (WHERE NOT is_refund) FROM lines WHERE {where} GROUP BY ALL"
        order_variants[name] = {(v, d): n for v, d, n in k.execute(sql).fetchall()}
    return truth, buckets, footers, order_variants


def variant_values(buckets, footers, venue, flags: dict, fx_mode: str, toggles: dict) -> dict:
    """Revenue per date for one venue under a given set of mistakes."""
    out = defaultdict(float)
    for (v, pos, cur, ld, ud, extra, resend, test, refund, major, orphan, quarantine, v2,
         fx_al, fx_el, fx_au, fx_eu, net, tip) in buckets:
        if v != venue:
            continue
        if quarantine and not toggles.get("truncated_published"):
            continue
        if extra:
            if resend and toggles.get("resend_double"):
                pass
            elif not resend and flags.get("keep_dups"):
                pass
            else:
                continue
        if test and not flags.get("keep_tests"):
            continue
        if refund and flags.get("drop_refunds"):
            continue
        if orphan and toggles.get("orphan_dropped"):
            continue
        if v2 and pos == "squareduck" and toggles.get("renamed_qty_null"):
            continue
        amount = net + (tip if toggles.get("tips_included") else 0)
        val = amount / 100.0
        if pos == "squareduck" and flags.get("cents"):
            val = float(amount)
        if pos == "kassa" and flags.get("kassa_x100"):
            val = float(amount)
        if major and toggles.get("units_unfixed"):
            val = val / 100.0
        use_utc = pos == "squareduck" and flags.get("utc_date")
        d = ud if use_utc else ld
        if cur == "USD":
            asof, exact = (fx_au, fx_eu) if use_utc else (fx_al, fx_el)
            if fx_mode == "asof":
                val = val / asof
            elif fx_mode == "inverted":
                val = val * asof
            elif fx_mode == "exact_only":
                if exact is None:
                    continue
                val = val / exact
        out[d] += val
    if flags.get("kassa_footer"):
        for v, d, total in footers:
            if v == venue:
                out[d] += total / 100.0 if not flags.get("kassa_x100") else float(total)
    return out


def l1(mine: dict, other: dict, dates) -> float:
    return sum(abs(mine.get(d, 0.0) - other.get(d, 0.0)) for d in dates)


def diagnose_venue(buckets, footers, venue, pos, currency, mine: dict, base_dates) -> list[str]:
    flag_names = SQ_FLAGS if pos == "squareduck" else KASSA_FLAGS
    modes = FX_MODES if currency == "USD" else ["asof"]
    best, best_d = None, None
    truth_d = None
    for bits in itertools.product([False, True], repeat=len(flag_names)):
        flags = dict(zip(flag_names, bits))
        for mode in modes:
            vals = variant_values(buckets, footers, venue, flags, mode, {})
            dates = set(base_dates) | {d for d in vals if d <= BASE_END} | {d for d in mine if d is not None and d <= BASE_END}
            dist = l1(mine, vals, dates)
            if not any(bits) and mode == "asof":
                truth_d = dist
            if best_d is None or dist < best_d - 1e-6:
                best, best_d = (flags, mode), dist
    if best is None or truth_d is None or best_d >= truth_d * 0.5:
        return []
    flags, mode = best
    reasons = [EXPLAIN[f] for f, on in flags.items() if on]
    if mode != "asof":
        reasons.append(EXPLAIN[f"fx:{mode}"])
    return reasons, best


def explain_cell(buckets, footers, venue, d, mine_val, base_combo) -> list[str]:
    flags, mode = base_combo
    found = []
    for bits in itertools.product([False, True], repeat=len(BREAK_TOGGLES)):
        toggles = dict(zip(BREAK_TOGGLES, bits))
        val = variant_values(buckets, footers, venue, flags, mode, toggles).get(d, 0.0)
        if abs(val - mine_val) <= tolerance(val):
            found.append([t for t, on in toggles.items() if on])
    if not found:
        return []
    found.sort(key=len)
    return found[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=os.environ.get("WORKSHOP_DB", "workshop.duckdb"))
    ap.add_argument("--table", default="marts.daily_venue_revenue")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    files = present_files()
    deliveries = applied_deliveries(files)
    truth, buckets, footers, order_variants = load_key(files)
    venue_meta = {}
    for b in buckets:
        venue_meta[b[0]] = (b[1], b[2])

    con = connect(args.db)
    qualified = args.table
    if args.db.startswith("md:") and args.db != "md:" and args.table.count(".") == 1:
        qualified = f"{args.db[3:].split('?')[0]}.{args.table}"
    try:
        cols = {r[0] for r in con.execute(f"DESCRIBE {qualified}").fetchall()}
    except duckdb.Error as e:
        print(f"[FAIL] {qualified} not found in {args.db}: {str(e).splitlines()[0]}")
        print("       The contract (contract/CONTRACT.md) expects a table or view named marts.daily_venue_revenue.")
        sys.exit(1)
    missing_cols = REQUIRED - cols
    if missing_cols:
        print(f"[FAIL] {qualified} is missing columns: {', '.join(sorted(missing_cols))}")
        sys.exit(1)

    rows = con.execute(f"""
        SELECT venue_id::VARCHAR, business_date::DATE, net_revenue_eur::DOUBLE, order_count::BIGINT
        FROM {qualified}
    """).fetchall()
    mine_rev, mine_n, null_rows, dup_keys = {}, {}, 0, 0
    for v, d, rev, n in rows:
        if v is None or d is None:
            null_rows += 1
            continue
        if (v, d) in mine_rev:
            dup_keys += 1
            mine_rev[(v, d)] += rev or 0.0
            mine_n[(v, d)] = (mine_n.get((v, d)) or 0) + (n or 0)
        else:
            mine_rev[(v, d)] = rev or 0.0
            mine_n[(v, d)] = n

    all_keys = set(truth) | set(mine_rev)
    ok_rev = sum(1 for k in truth if k in mine_rev and abs(mine_rev[k] - truth[k][0]) <= tolerance(truth[k][0]))
    ok_n = sum(1 for k in truth if k in mine_n and mine_n[k] == truth[k][1])
    missing = sorted(k for k in truth if k not in mine_rev)
    extra = sorted(k for k in mine_rev if k not in truth)

    result = {
        "db": args.db, "table": qualified, "deliveries": deliveries,
        "venue_days_expected": len(truth), "revenue_ok": ok_rev, "orders_ok": ok_n,
        "missing": [[v, d.isoformat()] for v, d in missing], "extra": [[v, d.isoformat()] for v, d in extra],
        "null_key_rows": null_rows, "duplicate_key_rows": dup_keys, "venues": {}, "breaks": {},
    }

    # per venue diagnosis on the base period
    base_combo = {}
    for venue in sorted({v for v, _ in truth}):
        pos, cur = venue_meta[venue]
        keys = [k for k in truth if k[0] == venue]
        ok = sum(1 for k in keys if k in mine_rev and abs(mine_rev[k] - truth[k][0]) <= tolerance(truth[k][0]))
        mine_total = sum(mine_rev.get(k, 0.0) for k in keys)
        truth_total = sum(truth[k][0] for k in keys)
        mine_v = {d: val for (v, d), val in mine_rev.items() if v == venue}
        base_dates = [d for (v, d) in keys if d <= BASE_END]
        reasons, combo = [], ({}, "asof")
        base_ok = all(abs(mine_v.get(d, 0.0) - truth[(venue, d)][0]) <= tolerance(truth[(venue, d)][0]) for d in base_dates)
        if not base_ok:
            diag = diagnose_venue(buckets, footers, venue, pos, cur, mine_v, base_dates)
            if diag:
                reasons, combo = diag
        base_combo[venue] = combo
        result["venues"][venue] = {
            "pos_system": pos, "currency": cur, "ok": ok, "expected": len(keys),
            "total_diff_pct": round((mine_total - truth_total) / truth_total * 100, 2) if truth_total else None,
            "looks_like": reasons,
        }

    # break-specific cells (after the base period, plus the late VIE file)
    break_cells = sorted({k for k in all_keys if k[1] > BASE_END} | {("VIE", date(2026, 10, 12))})
    for venue, d in break_cells:
        if venue not in venue_meta:
            continue
        t = truth.get((venue, d))
        m = mine_rev.get((venue, d))
        if t is not None and m is not None and abs(m - t[0]) <= tolerance(t[0]):
            continue
        if t is None and m is None:
            continue
        key = f"{venue} {d.isoformat()}"
        if m is None:
            reason = ["not loaded (late-arriving file skipped?)" if (venue, d) == ("VIE", date(2026, 10, 12))
                      else "not loaded: delivery not processed yet, or the build stopped"]
        else:
            toggles = explain_cell(buckets, footers, venue, d, m, base_combo.get(venue, ({}, "asof")))
            reason = [EXPLAIN[t_] for t_ in toggles] if toggles else ["unexplained difference"]
        result["breaks"][key] = {"mine": m, "expected": t[0] if t else None, "why": reason}

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return

    print(f"Contract check: {qualified} in {args.db}")
    print(f"Deliveries in data/raw: {', '.join(deliveries)}")
    print()
    status = "PASS" if ok_rev == len(truth) and not extra and not null_rows and not dup_keys else "FAIL"
    print(f"[{status}] net_revenue_eur: {ok_rev}/{len(truth)} venue-days match (tolerance: max EUR 1, 0.1%)")
    for venue, info in result["venues"].items():
        mark = "ok " if info["ok"] == info["expected"] else "!! "
        diff = f"{info['total_diff_pct']:+.2f}%" if info["total_diff_pct"] is not None else "n/a"
        print(f"   {mark}{venue} ({info['pos_system']}, {info['currency']}): {info['ok']}/{info['expected']} days, total {diff}")
        for r in info["looks_like"]:
            print(f"        looks like: {r}")
    n_status = "PASS" if ok_n == len(truth) else "FAIL"
    print(f"[{n_status}] order_count: {ok_n}/{len(truth)} venue-days match")
    if ok_n != len(truth):
        for name, label in [("keep_tests", "training transactions counted as orders"),
                            ("count_refunds", "refund receipts counted as orders"),
                            ("utc_date", "orders bucketed by UTC date"),
                            ("line_count", "counting lines instead of distinct orders")]:
            variant = order_variants[name]
            hits = sum(1 for k, n in mine_n.items() if k in variant and n == variant[k] and truth.get(k, (0, -1))[1] != n)
            if hits:
                print(f"        {hits} days look like: {label}")
    if missing:
        print(f"[FAIL] {len(missing)} venue-days missing, e.g. {', '.join(f'{v} {d}' for v, d in missing[:5])}")
    if extra:
        print(f"[FAIL] {len(extra)} unexpected venue-days, e.g. {', '.join(f'{v} {d}' for v, d in extra[:5])}")
    if null_rows:
        print(f"[FAIL] {null_rows} rows with NULL venue_id or business_date (Kassa 'Summe' rows?)")
    if dup_keys:
        print(f"[FAIL] {dup_keys} duplicate (venue_id, business_date) rows: the grain is one row per venue per day")
    if result["breaks"]:
        print()
        print("Late or broken deliveries:")
        for key, info in result["breaks"].items():
            mine = "absent" if info["mine"] is None else f"{info['mine']:.2f}"
            exp = "absent (quarantine)" if info["expected"] is None else f"{info['expected']:.2f}"
            print(f"   {key}: yours {mine}, expected {exp}")
            for r in info["why"]:
                print(f"        why: {r}")
    print()
    score = ok_rev + ok_n
    print(f"Score: {score}/{2 * len(truth)}")
    sys.exit(0 if status == "PASS" and n_status == "PASS" else 1)


if __name__ == "__main__":
    main()
