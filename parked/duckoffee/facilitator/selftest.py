#!/usr/bin/env python3
"""Self-test for the workshop tooling. Facilitator only.

1. Reference solution scores 100% on the base drop and after every delivery.
2. The checker names the right mistake for marts built with known mistakes.

Run from the repo root: uv run facilitator/selftest.py
Leaves data/raw back on the base drop.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import time

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check  # noqa: E402

SOLUTION_DB = ROOT / "facilitator" / "solution" / "solution.duckdb"


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


def check_json(db: Path) -> dict:
    p = run([sys.executable, "tools/check.py", "--db", str(db), "--json"])
    return json.loads(p.stdout)


def build_reference() -> None:
    p = run(["duckdb", str(SOLUTION_DB), "-f", "facilitator/solution/build.sql"])
    if p.returncode != 0:
        raise SystemExit(f"reference build failed:\n{p.stderr}")


def reference_suite() -> None:
    run([sys.executable, "tools/deliver.py", "--reset"])
    manifest = json.loads((check.KEY / "manifest.json").read_text())
    steps = ["base"] + [k for k in manifest if k != "base"]
    for step in steps:
        if step != "base":
            run([sys.executable, "tools/deliver.py", step])
        build_reference()
        r = check_json(SOLUTION_DB)
        n = r["venue_days_expected"]
        ok = r["revenue_ok"] == n and r["orders_ok"] == n and not r["extra"] and not r["missing"]
        print(f"  reference after {step:<16} {'PASS' if ok else 'FAIL'} ({r['revenue_ok']}/{n} revenue, {r['orders_ok']}/{n} orders)")
        if not ok:
            raise SystemExit(json.dumps(r, indent=2, default=str))
    run([sys.executable, "tools/deliver.py", "--reset"])


def fake_mart(flags_by_pos: dict, fx_mode: str, toggles: dict) -> Path:
    files = check.present_files()
    truth, buckets, footers, _ = check.load_key(files)
    meta = {b[0]: (b[1], b[2]) for b in buckets}
    rows = []
    for venue, (pos, cur) in meta.items():
        vals = check.variant_values(buckets, footers, venue, flags_by_pos.get(pos, {}),
                                    fx_mode if cur == "USD" else "asof", toggles)
        # a broken build still emits a row for every day it saw, often with a 0 or NULL amount
        days = set(vals) | {d for (v, d) in truth if v == venue}
        for d in days:
            n = truth.get((venue, d), (0, 0))[1]
            rows.append((venue, d, round(vals.get(d, 0.0), 2), n))
    path = Path(tempfile.mkdtemp()) / "fake.duckdb"
    con = duckdb.connect(str(path))
    con.execute("CREATE SCHEMA marts")
    con.execute("CREATE TABLE marts.daily_venue_revenue (venue_id VARCHAR, business_date DATE, net_revenue_eur DOUBLE, order_count BIGINT)")
    con.executemany("INSERT INTO marts.daily_venue_revenue VALUES (?, ?, ?, ?)", rows)
    con.close()
    return path


CASES = [
    # name, flags per pos system, fx mode, break toggles, venue -> substring expected in looks_like
    ("dups kept", {"squareduck": {"keep_dups": True}}, "asof", {}, {"SFO": "duplicate"}),
    ("training counted", {"squareduck": {"keep_tests": True}, "kassa": {"keep_tests": True}}, "asof", {},
     {"AMS": "training", "BER": "training"}),
    ("utc dates", {"squareduck": {"utc_date": True}}, "asof", {}, {"SFO": "UTC"}),
    ("cents", {"squareduck": {"cents": True}}, "asof", {}, {"AMS": "cents"}),
    ("no fx", {}, "none", {}, {"NYC": "no FX"}),
    ("fx exact join", {}, "exact_only", {}, {"NYC": "weekend"}),
    ("kassa footer", {"kassa": {"kassa_footer": True}}, "asof", {}, {"BER": "Summe"}),
    ("refunds ignored", {"squareduck": {"drop_refunds": True}, "kassa": {"drop_refunds": True}}, "asof", {},
     {"AMS": "refunds", "VIE": "refunds"}),
    ("one-shot agent", {"squareduck": {"keep_dups": True, "keep_tests": True, "utc_date": True},
                        "kassa": {"keep_tests": True, "kassa_footer": True}}, "none", {},
     {"SFO": "UTC", "NYC": "no FX", "BER": "Summe"}),
]

BREAK_CASES = [
    ("resend double counted", "01-resend", {"resend_double": True}, "AMS 2026-11-01", "twice"),
    ("tips included", "02-schema-drift", {"tips_included": True}, "AMS 2026-11-02", "tips"),
    ("renamed column", "02-schema-drift", {"renamed_qty_null": True}, "AMS 2026-11-02", "quantity"),
    ("silent units", "03-silent-units", {"units_unfixed": True}, "NYC 2026-11-03", "dollars"),
    ("orphan dropped", "04-new-product", {"orphan_dropped": True}, "BER 2026-11-04", "menu.json"),
    ("truncated published", "06-truncated", {"truncated_published": True}, "BER 2026-11-05", "truncated"),
]


def diagnosis_suite() -> None:
    run([sys.executable, "tools/deliver.py", "--reset"])
    failures = 0
    for name, flags, fx_mode, toggles, expect in CASES:
        r = check_json(fake_mart(flags, fx_mode, toggles))
        bad = []
        for venue, needle in expect.items():
            reasons = " | ".join(r["venues"][venue]["looks_like"])
            if needle.lower() not in reasons.lower():
                bad.append(f"{venue}: wanted '{needle}', got '{reasons}'")
        failures += bool(bad)
        print(f"  diagnose {name:<22} {'PASS' if not bad else 'FAIL ' + '; '.join(bad)}")

    for name, delivery, toggles, cell, needle in BREAK_CASES:
        run([sys.executable, "tools/deliver.py", "--reset"])
        # land everything up to and including this delivery
        for d in json.loads((check.KEY / "manifest.json").read_text()):
            if d == "base":
                continue
            run([sys.executable, "tools/deliver.py", d])
            if d == delivery:
                break
        r = check_json(fake_mart({}, "asof", toggles))
        why = " | ".join(r["breaks"].get(cell, {}).get("why", []))
        ok = needle.lower() in why.lower()
        failures += not ok
        print(f"  diagnose {name:<22} {'PASS' if ok else f'FAIL: {cell} -> {why!r}'}")
    run([sys.executable, "tools/deliver.py", "--reset"])
    if failures:
        raise SystemExit(f"{failures} diagnosis case(s) failed")


if __name__ == "__main__":
    t0 = time.time()
    print("Reference solution")
    reference_suite()
    print(f"Checker diagnoses ({time.time() - t0:.0f}s so far)")
    diagnosis_suite()
    print(f"All good in {time.time() - t0:.0f}s.")
