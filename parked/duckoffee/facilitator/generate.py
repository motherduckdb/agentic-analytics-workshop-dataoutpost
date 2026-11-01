#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["duckdb>=1.5,<1.6"]
# ///
"""Deterministic generator for the Duckoffee raw drop, the break deliveries and the answer key.

Facilitator only. Participants' agents must not read this file: it documents every trap.

Outputs:
  data/raw/                         the base delivery (committed, what participants start with)
  facilitator/breaks/<name>/        files a break copies into data/raw (tools/break.py)
  facilitator/answer_key/lines.parquet    one row per raw POS line copy, with truth flags
  facilitator/answer_key/footers.parquet  Kassa summary rows ("Summe") per file
  facilitator/answer_key/manifest.json    delivery name -> files it adds

Run: uv run facilitator/generate.py
"""

from __future__ import annotations

import csv
import json
import random
import shutil
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb

SEED = 20261117
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FAC = ROOT / "facilitator"
BREAKS = FAC / "breaks"
KEY = FAC / "answer_key"

UTC = ZoneInfo("UTC")
BASE_START = date(2026, 9, 1)
BASE_END = date(2026, 10, 31)
LAST_DAY = date(2026, 11, 5)

# Break deliveries, one per day after the base period. Each SquareDuck file is a UTC day,
# each Kassa file a local day. Deliveries are named so they sort in the intended order.
DAY_BREAKS = {
    date(2026, 11, 1): "01-resend",
    date(2026, 11, 2): "02-schema-drift",
    date(2026, 11, 3): "03-silent-units",
    date(2026, 11, 4): "04-new-product",
    date(2026, 11, 5): "06-truncated",
}
LATE_FILE = ("VIE", date(2026, 10, 12))  # withheld from base, delivered by 05-late-file
SCHEMA_V2_FROM = date(2026, 11, 2)  # SquareDuck renames qty->quantity, adds tip_cents; Kassa adds Trinkgeld
SILENT_UNITS = ("NYC", date(2026, 11, 3))  # unit_price_cents holds dollars in this file
NEW_PRODUCT_FROM = date(2026, 11, 4)
TRUNCATED = ("BER", date(2026, 11, 5))

VENUES = [
    dict(venue_id="AMS", venue_name="The Pond Stage", city="Amsterdam", country="NL", timezone="Europe/Amsterdam",
         currency="EUR", pos_system="squareduck", opened_on="2024-03-01", closed_on="", open_h=7, close_h=19, base=190),
    dict(venue_id="NYC", venue_name="Quack Quarter", city="New York", country="US", timezone="America/New_York",
         currency="USD", pos_system="squareduck", opened_on="2024-09-15", closed_on="", open_h=7, close_h=19, base=230),
    dict(venue_id="SFO", venue_name="Lake View Brew", city="San Francisco", country="US", timezone="America/Los_Angeles",
         currency="USD", pos_system="squareduck", opened_on="2025-02-01", closed_on="", open_h=7, close_h=20, base=170),
    dict(venue_id="BER", venue_name="Nest Lounge", city="Berlin", country="DE", timezone="Europe/Berlin",
         currency="EUR", pos_system="kassa", opened_on="2023-11-01", closed_on="", open_h=7, close_h=19, base=210),
    dict(venue_id="VIE", venue_name="Feather & Bean", city="Vienna", country="AT", timezone="Europe/Vienna",
         currency="EUR", pos_system="kassa", opened_on="2025-06-01", closed_on="", open_h=8, close_h=18, base=120),
    dict(venue_id="LIS", venue_name="The Waddle Inn", city="Lisbon", country="PT", timezone="Europe/Lisbon",
         currency="EUR", pos_system="squareduck", opened_on="2025-01-10", closed_on="2026-10-15", open_h=8, close_h=18, base=100),
]
VENUE = {v["venue_id"]: v for v in VENUES}

# sku, name, german name (Kassa), category, kassa article, popularity,
# price history [(valid_from, eur_cents, usd_cents)], unit cost eur cents, tags
PRICE_BUMP = "2026-10-01"
PRODUCTS = [
    ("BEV-001", "Quackuccino", "Quackuccino", "Beverage", 1001, 18, [("2025-01-01", 380, 450), (PRICE_BUMP, 410, 475)], 95, ["hot", "dairy"]),
    ("BEV-002", "Flat Wing White", "Flat White", "Beverage", 1002, 14, [("2025-01-01", 360, 425), (PRICE_BUMP, 390, 450)], 90, ["hot", "dairy"]),
    ("BEV-003", "Pond Water Espresso", "Espresso", "Beverage", 1003, 10, [("2025-01-01", 240, 300)], 45, ["hot"]),
    ("BEV-004", "Mallard Matcha Latte", "Matcha Latte", "Beverage", 1004, 7, [("2025-01-01", 420, 525)], 120, ["hot", "dairy"]),
    ("BEV-005", "Cold Brew Paddle", "Cold Brew", "Beverage", 1005, 8, [("2025-01-01", 390, 475)], 70, ["cold"]),
    ("BEV-006", "Duckling Hot Chocolate", "Heiße Schokolade", "Beverage", 1006, 5, [("2025-01-01", 340, 400)], 80, ["hot", "dairy"]),
    ("BEV-007", "Sparkling Lake Water", "Mineralwasser", "Beverage", 1007, 6, [("2025-01-01", 220, 275)], 30, ["cold"]),
    ("BEV-008", "Oat Quackuccino", "Hafer-Quackuccino", "Beverage", 1008, 9, [("2025-01-01", 430, 500), (PRICE_BUMP, 460, 525)], 110, ["hot", "vegan"]),
    ("FOD-001", "Butter Croissant", "Butter-Croissant", "Food", 2001, 9, [("2025-01-01", 260, 325)], 70, ["bakery"]),
    ("FOD-002", "Cheesecake Slice", "Käsekuchen", "Food", 2002, 4, [("2025-01-01", 420, 525)], 130, ["bakery"]),
    ("FOD-003", "Pretzel", "Laugenbrezel", "Food", 2003, 5, [("2025-01-01", 210, 275)], 40, ["bakery", "vegan"]),
    ("FOD-004", "Avocado Toast", "Avocado-Brötchen", "Food", 2004, 4, [("2025-01-01", 650, 850)], 210, ["savory", "vegan"]),
    ("FOD-005", "Banana Bread", "Bananenbrot", "Food", 2005, 5, [("2025-01-01", 320, 395)], 75, ["bakery"]),
    ("FOD-006", "Granola Pot", "Müsli-Becher", "Food", 2006, 3, [("2025-01-01", 480, 595)], 140, ["breakfast"]),
    ("FOD-007", "Cinnamon Bun", "Zimtschnecke", "Food", 2007, 5, [("2025-01-01", 310, 375)], 65, ["bakery"]),
    ("MER-001", "Rubber Duck (Keynote Edition)", "Quietscheente", "Merch", 3001, 2, [("2025-01-01", 900, 1000)], 180, ["merch"]),
    ("MER-002", "Duckoffee Mug", "Tasse", "Merch", 3002, 1, [("2025-01-01", 1400, 1600)], 420, ["merch"]),
    ("MER-003", "Tote Bag", "Stofftasche", "Merch", 3003, 1, [("2025-01-01", 1200, 1400)], 300, ["merch"]),
    ("MER-004", "Sticker Pack", "Aufkleber-Set", "Merch", 3004, 2, [("2025-01-01", 300, 350)], 40, ["merch"]),
]
NEW_PRODUCT = ("BEV-099", "Pumpkin Spice Quackuccino", "Kürbis-Quackuccino", "Beverage", 1099, 0,
               [("2026-11-04", 460, 550)], 120, ["hot", "dairy", "seasonal"])

CONFERENCES = [
    ("CNF-01", "PondConf 2026", "AMS", "2026-09-08", "2026-09-10", 2400, ["data", "ai"], "confirmed"),
    ("CNF-02", "Feathers & Frameworks", "BER", "2026-09-15", "2026-09-16", 1800, ["frontend"], "confirmed"),
    ("CNF-03", "DataFlock Summit", "NYC", "2026-09-22", "2026-09-24", 3500, ["data", "analytics"], "confirmed"),
    ("CNF-04", "Wing Dev Days", "SFO", "2026-09-29", "2026-10-01", 2800, ["devtools", "ai"], "confirmed"),
    ("CNF-05", "Nested Loops Conf", "VIE", "2026-10-06", "2026-10-07", 900, ["languages"], "confirmed"),
    ("CNF-06", "Paddle.js", "LIS", "2026-10-07", "2026-10-09", 1500, ["javascript"], "confirmed"),
    ("CNF-07", "Small Batch Analytics", "AMS", "2026-10-13", "2026-10-14", 1200, ["data"], "confirmed"),
    ("CNF-08", "Quackathon", "BER", "2026-10-20", "2026-10-22", 2000, ["hackathon", "ai"], "confirmed"),
    ("CNF-09", "Bay Area Data Brunch", "SFO", "2026-10-21", "2026-10-21", 600, ["data"], "confirmed"),
    ("CNF-10", "Lisbon Data Weekend", "LIS", "2026-10-24", "2026-10-25", 1100, ["data"], "cancelled"),
    ("CNF-11", "Lakehouse Leaders", "NYC", "2026-10-27", "2026-10-29", 4200, ["data", "lakehouse"], "confirmed"),
    ("CNF-12", "Late Binding Days", "VIE", "2026-11-03", "2026-11-04", 800, ["languages"], "confirmed"),
    ("CNF-13", "Webfoot Summit", "AMS", "2026-11-04", "2026-11-05", 2100, ["frontend"], "confirmed"),
]

FIRST = ["Ana", "Ben", "Chloe", "Dmitri", "Elif", "Farah", "Gus", "Hana", "Ines", "Jonas", "Kofi", "Lena", "Mateo",
         "Noor", "Omar", "Priya", "Quinn", "Rosa", "Sven", "Tomas", "Uma", "Vera", "Wei", "Ximena", "Yusuf", "Zoe"]
LAST = ["Andersen", "Bakker", "Costa", "Dubois", "Eriksen", "Fischer", "Garcia", "Huber", "Ito", "Jansen", "Kowalski",
        "Lopez", "Meyer", "Novak", "Okafor", "Pereira", "Quispe", "Rossi", "Schmidt", "Tanaka", "Ueda", "Visser",
        "Weber", "Yilmaz", "Zimmermann"]

KASSA_HEADER_V1 = ["Bon_Nr", "Pos", "Datum", "Uhrzeit", "Artikel_Nr", "Artikelbezeichnung", "Menge", "Einzelpreis",
                   "Rabatt", "Gesamt", "Zahlart", "Kundenkarte", "Training", "Storno"]
KASSA_HEADER_V2 = KASSA_HEADER_V1 + ["Trinkgeld"]
SQ_HEADER_V1 = ["order_id", "line_no", "sold_at_utc", "venue_code", "sku", "qty", "unit_price_cents", "discount_cents",
                "currency", "payment_method", "loyalty_id", "staff_id", "refund_of"]
SQ_HEADER_V2 = ["order_id", "line_no", "sold_at_utc", "venue_code", "sku", "quantity", "unit_price_cents",
                "discount_cents", "tip_cents", "currency", "payment_method", "loyalty_id", "staff_id", "refund_of"]

rng = random.Random(SEED)


def daterange(a: date, b: date):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


def price_minor(prod, currency: str, d: date) -> int:
    hist = prod[6]
    chosen = hist[0]
    for row in hist:
        if date.fromisoformat(row[0]) <= d:
            chosen = row
    return chosen[1] if currency == "EUR" else chosen[2]


def conference_on(venue_id: str, d: date):
    for c in CONFERENCES:
        if c[2] == venue_id and c[7] == "confirmed" and date.fromisoformat(c[3]) <= d <= date.fromisoformat(c[4]):
            return c
    return None


def is_open(v, d: date) -> bool:
    if v["closed_on"] and d >= date.fromisoformat(v["closed_on"]):
        return False
    return True


def euro(minor: int) -> str:
    """Kassa money format: decimal comma, no thousands separator."""
    sign = "-" if minor < 0 else ""
    minor = abs(minor)
    return f"{sign}{minor // 100},{minor % 100:02d}"


def dollars(minor: int) -> str:
    sign = "-" if minor < 0 else ""
    minor = abs(minor)
    return f"{sign}{minor // 100}.{minor % 100:02d}"


# ---------------------------------------------------------------------------------------------
# Members (loyalty)
# ---------------------------------------------------------------------------------------------

def make_members(n=3000):
    weights = [v["base"] for v in VENUES]
    members = []
    for i in range(1, n + 1):
        fn, ln = rng.choice(FIRST), rng.choice(LAST)
        home = rng.choices(VENUES, weights=weights)[0]["venue_id"]
        joined = datetime(2023, 11, 1) + timedelta(minutes=rng.randrange(0, 60 * 24 * 1030))
        members.append({
            "member_id": f"LM-{i:06d}",
            "email": f"{fn.lower()}.{ln.lower()}{rng.randrange(1, 99)}@example.com",
            "first_name": fn,
            "home_venue": home.lower() if rng.random() < 0.06 else home,
            "joined_at": joined.strftime("%Y-%m-%dT%H:%M:%S"),
            "tier": rng.choices(["bronze", "silver", "gold"], weights=[70, 22, 8])[0],
            "marketing_opt_in": rng.random() < 0.41,
            "preferences": {
                "milk": rng.choice(["dairy", "oat", "soy", "none"]),
                "favorite_sku": rng.choice([p[0] for p in PRODUCTS[:8]]),
            },
        })
    return members


# ---------------------------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------------------------

HOUR_WEIGHTS = {7: 2.0, 8: 3.5, 9: 3.0, 10: 2.0, 11: 1.6, 12: 2.4, 13: 2.0, 14: 1.3, 15: 1.8, 16: 1.4,
                17: 1.0, 18: 0.8, 19: 0.6, 20: 0.5, 21: 0.4}


def sample_local_time(open_h: int, close_h: int) -> time:
    hours = list(range(open_h, close_h))
    h = rng.choices(hours, weights=[HOUR_WEIGHTS.get(x, 0.5) for x in hours])[0]
    return time(h, rng.randrange(60), rng.randrange(60))


def pick_products(d: date, conf, k: int):
    pool = list(PRODUCTS)
    weights = [p[5] * (4 if (conf and p[3] == "Merch") else 1) for p in pool]
    if d >= NEW_PRODUCT_FROM:
        pool.append(NEW_PRODUCT)
        weights.append(9)
    chosen = []
    while len(chosen) < k:
        p = rng.choices(pool, weights=weights)[0]
        if p not in chosen:
            chosen.append(p)
    return chosen


class Ids:
    def __init__(self):
        self.seen = set()
        self.kassa = {"BER": 10500, "VIE": 12000}

    def sq(self) -> str:
        while True:
            x = f"sq_{rng.getrandbits(40):010x}"
            if x not in self.seen:
                self.seen.add(x)
                return x

    def bon(self, venue_id: str) -> str:
        self.kassa[venue_id] += 1
        return str(self.kassa[venue_id])


def make_orders(members_by_venue, ids: Ids):
    """Returns a list of orders. Each order: dict with venue, order_id, local_ts (aware), lines, flags."""
    orders = []
    for v in VENUES:
        tz = ZoneInfo(v["timezone"])
        staff = [f"S{rng.randrange(100, 999)}" for _ in range(6)]
        for d in daterange(BASE_START, LAST_DAY):
            if not is_open(v, d):
                continue
            conf = conference_on(v["venue_id"], d)
            factor = 0.55 if d.weekday() >= 5 else 1.0
            if conf:
                factor *= 1 + min(conf[5] / 2500, 1.2)
            n = int(v["base"] * factor * rng.uniform(0.85, 1.15))
            close_h = v["close_h"] + (2 if conf else 0)
            day_orders = []
            for _ in range(n):
                t = sample_local_time(v["open_h"], close_h)
                local_ts = datetime.combine(d, t, tzinfo=tz)
                k = rng.choices([1, 2, 3, 4], weights=[55, 30, 11, 4])[0]
                member = None
                if rng.random() < 0.30:
                    pool = members_by_venue.get(v["venue_id"]) or members_by_venue["AMS"]
                    member = rng.choice(pool)["member_id"]
                lines = []
                for p in pick_products(d, conf, k):
                    qty = rng.choices([1, 2, 3], weights=[85, 12, 3])[0]
                    unit = price_minor(p, v["currency"], d)
                    disc = round(qty * unit * 0.10) if (member and rng.random() < 0.30) else 0
                    lines.append(dict(sku=p[0], article=p[4], name_de=p[2], qty=qty, unit=unit, disc=disc))
                if v["pos_system"] == "squareduck":
                    pay = rng.choices(["card", "apple_pay", "google_pay", "cash"],
                                      weights=[60, 20, 8, 12 if v["currency"] == "EUR" else 5])[0]
                else:
                    pay = rng.choices(["EC-Karte", "Bar", "Kreditkarte", "Mobil"], weights=[45, 30, 10, 15])[0]
                tip_total = 0
                if d >= SCHEMA_V2_FROM and rng.random() < 0.4:
                    tip_total = rng.choice([50, 100, 100, 150, 200])
                day_orders.append(dict(venue=v["venue_id"], local_ts=local_ts, lines=lines, member=member, pay=pay,
                                       staff=rng.choice(staff), is_test=False, refund_of=None, tip=tip_total))

            # training transactions before opening
            if rng.random() < 0.30:
                for _ in range(rng.choice([1, 1, 2])):
                    t = time(v["open_h"] - 1, rng.randrange(25, 55), rng.randrange(60))
                    merch = [p for p in PRODUCTS if p[3] == "Merch"]
                    lines = []
                    for p in rng.sample(merch, 2):
                        qty = rng.randrange(5, 13)
                        lines.append(dict(sku=p[0], article=p[4], name_de=p[2], qty=qty,
                                          unit=price_minor(p, v["currency"], d), disc=0))
                    day_orders.append(dict(venue=v["venue_id"], local_ts=datetime.combine(d, t, tzinfo=tz),
                                           lines=lines, member=None, pay="card" if v["pos_system"] == "squareduck" else "Bar",
                                           staff="TRAINING", is_test=True, refund_of=None, tip=0))

            # refunds: a few sales get (partially) refunded later the same day
            sales = [o for o in day_orders if not o["is_test"]]
            for o in rng.sample(sales, max(1, int(len(sales) * 0.012))):
                rt = o["local_ts"] + timedelta(minutes=rng.randrange(10, 180))
                if rt.date() != d or rt.hour >= close_h:
                    continue
                refunded = o["lines"] if rng.random() < 0.5 else [rng.choice(o["lines"])]
                lines = [dict(l, qty=-l["qty"], disc=-l["disc"]) for l in refunded]
                day_orders.append(dict(venue=v["venue_id"], local_ts=rt, lines=lines, member=o["member"], pay=o["pay"],
                                       staff=o["staff"], is_test=False, refund_of=o, tip=0))

            day_orders.sort(key=lambda o: o["local_ts"])
            for o in day_orders:
                o["order_id"] = ids.sq() if v["pos_system"] == "squareduck" else ids.bon(v["venue_id"])
            orders.extend(day_orders)
    return orders


# ---------------------------------------------------------------------------------------------
# Writing deliveries
# ---------------------------------------------------------------------------------------------

def delivery_for_day(d: date) -> str | None:
    if BASE_START <= d <= BASE_END:
        return "base"
    return DAY_BREAKS.get(d)


def target_dir(delivery: str) -> Path:
    return RAW if delivery == "base" else BREAKS / delivery


def flatten(orders):
    """One record per logical POS line (no duplicates yet)."""
    recs = []
    for o in orders:
        v = VENUE[o["venue"]]
        utc_ts = o["local_ts"].astimezone(UTC)
        for i, l in enumerate(o["lines"], start=1):
            recs.append(dict(
                venue_id=o["venue"], pos_system=v["pos_system"], currency=v["currency"],
                order_id=o["order_id"], line_no=i,
                local_ts=o["local_ts"].replace(tzinfo=None), utc_ts=utc_ts.replace(tzinfo=None),
                local_date=o["local_ts"].date(), utc_date=utc_ts.date(),
                sku=l["sku"], article=l["article"], name_de=l["name_de"], qty=l["qty"], unit=l["unit"], disc=l["disc"],
                tip=o["tip"] if i == 1 else 0,
                member=o["member"] or "", pay=o["pay"], staff=o["staff"],
                is_test=o["is_test"], is_refund=o["refund_of"] is not None,
                refund_of=o["refund_of"]["order_id"] if o["refund_of"] else "",
            ))
    return recs


def sq_row(r, v2: bool, dollars_mode: bool):
    unit = dollars(r["unit"]) if dollars_mode else str(r["unit"])
    disc = dollars(r["disc"]) if dollars_mode else str(r["disc"])
    base = [r["order_id"], r["line_no"], r["utc_ts"].strftime("%Y-%m-%dT%H:%M:%SZ"), r["venue_id"], r["sku"], r["qty"],
            unit, disc]
    tail = [r["currency"], r["pay"], r["member"], r["staff"], r["refund_of"]]
    if v2:
        tip = dollars(r["tip"]) if dollars_mode else str(r["tip"])
        return base + [tip] + tail
    return base + tail


def kassa_row(r, v2: bool):
    row = [r["order_id"], r["line_no"], r["local_ts"].strftime("%d.%m.%Y"), r["local_ts"].strftime("%H:%M:%S"),
           r["article"], r["name_de"], r["qty"], euro(r["unit"]), euro(r["disc"]), euro(r["qty"] * r["unit"] - r["disc"]),
           r["pay"], r["member"], "J" if r["is_test"] else "N", "J" if r["is_refund"] else "N"]
    if v2:
        row.append(euro(r["tip"]))
    return row


def write_squareduck(recs, key_rows):
    """SquareDuck: one CSV per venue per UTC day. Export windows overlap by 10 minutes and the sync
    occasionally retries a whole order, both producing exact duplicate lines."""
    by_venue = {}
    for r in recs:
        if r["pos_system"] == "squareduck":
            by_venue.setdefault(r["venue_id"], []).append(r)
    for venue_id, rows in by_venue.items():
        rows.sort(key=lambda r: (r["utc_ts"], r["order_id"], r["line_no"]))
        days = sorted({r["utc_date"] for r in rows})
        for d in days:
            delivery = delivery_for_day(d)
            if delivery is None:
                continue
            start = datetime.combine(d, time(0)) - timedelta(minutes=10)
            end = datetime.combine(d + timedelta(days=1), time(0))
            in_file = [r for r in rows if start <= r["utc_ts"] < end]
            out = []
            for r in in_file:
                is_dup = r["utc_date"] != d  # overlap window copy, original lives in the previous file
                out.append((r, is_dup))
            # whole-order sync retries
            order_ids = sorted({r["order_id"] for r, dup in out if not dup})
            retried = set(rng.sample(order_ids, max(0, int(len(order_ids) * 0.006))))
            retries = [(r, True) for r, dup in out if not dup and r["order_id"] in retried]
            for item in retries:
                out.insert(rng.randrange(len(out) + 1), item)

            v2 = d >= SCHEMA_V2_FROM
            dollars_mode = (venue_id, d) == SILENT_UNITS
            rel = f"pos/squareduck/{venue_id}/{d.isoformat()}.csv"
            path = target_dir(delivery) / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, lineterminator="\n")
                w.writerow(SQ_HEADER_V2 if v2 else SQ_HEADER_V1)
                for r, dup in out:
                    w.writerow(sq_row(r, v2, dollars_mode))
            for r, dup in out:
                key_rows.append(key_row(r, delivery, rel, dup, raw_major_units=dollars_mode, schema_v2=v2))

            # 01-resend: the same AMS file delivered a second time under a browser-style name
            if delivery == "01-resend" and venue_id == "AMS":
                rel2 = f"pos/squareduck/{venue_id}/{d.isoformat()} (1).csv"
                shutil.copyfile(path, target_dir(delivery) / rel2)
                for r, dup in out:
                    key_rows.append(key_row(r, delivery, rel2, True, raw_major_units=dollars_mode, schema_v2=v2,
                                            resend_copy=True))


def write_kassa(recs, key_rows, footers):
    """Kassa: one latin-1, semicolon, decimal-comma CSV per venue per local day, with a 'Summe' total row."""
    by_key = {}
    for r in recs:
        if r["pos_system"] == "kassa":
            by_key.setdefault((r["venue_id"], r["local_date"]), []).append(r)
    for (venue_id, d), rows in sorted(by_key.items()):
        rows.sort(key=lambda r: (r["local_ts"], int(r["order_id"]), r["line_no"]))
        delivery = delivery_for_day(d)
        if (venue_id, d) == LATE_FILE:
            delivery = "05-late-file"
        if delivery is None:
            continue
        v2 = d >= SCHEMA_V2_FROM
        rel = f"pos/kassa/{venue_id}/Export_{venue_id}_{d.strftime('%d%m%Y')}.csv"
        path = target_dir(delivery) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        header = KASSA_HEADER_V2 if v2 else KASSA_HEADER_V1
        truncated = (venue_id, d) == TRUNCATED
        lines = [";".join(header)]
        for r in rows:
            lines.append(";".join(str(x) for x in kassa_row(r, v2)))
        total = sum(r["qty"] * r["unit"] - r["disc"] for r in rows)
        footer = ["Summe"] + [""] * 8 + [euro(total)] + [""] * (len(header) - 10)
        present = rows
        if truncated:
            cut = int(len(lines) * 0.55)
            present = rows[: cut - 1]
            partial = lines[cut]
            lines = lines[:cut] + [partial[: len(partial) // 2]]
        else:
            lines.append(";".join(footer))
            footers.append(dict(venue_id=venue_id, local_date=d, delivery=delivery, file_rel=rel, total_minor=total))
        with path.open("w", newline="", encoding="latin-1") as f:
            f.write("\r\n".join(lines) + ("" if truncated else "\r\n"))
        for r in present:
            key_rows.append(key_row(r, delivery, rel, False, quarantine=truncated, schema_v2=v2))


def key_row(r, delivery, rel, is_dup, raw_major_units=False, quarantine=False, schema_v2=False, resend_copy=False):
    return dict(
        venue_id=r["venue_id"], pos_system=r["pos_system"], currency=r["currency"], delivery=delivery, file_rel=rel,
        order_id=r["order_id"], line_no=r["line_no"], sku=r["sku"], qty=r["qty"], unit_price_minor=r["unit"],
        discount_minor=r["disc"], tip_minor=r["tip"], net_minor=r["qty"] * r["unit"] - r["disc"],
        local_ts=r["local_ts"], utc_ts=r["utc_ts"], local_date=r["local_date"],
        utc_date=r["utc_date"] if r["pos_system"] == "squareduck" else r["local_date"],
        is_dup=is_dup, is_test=r["is_test"], is_refund=r["is_refund"], is_orphan_sku=r["sku"] == NEW_PRODUCT[0],
        raw_major_units=raw_major_units, quarantine_expected=quarantine, schema_v2=schema_v2,
        is_resend_copy=resend_copy,
    )


# ---------------------------------------------------------------------------------------------
# Reference files
# ---------------------------------------------------------------------------------------------

def write_venues():
    path = RAW / "venues.csv"
    cols = ["venue_id", "venue_name", "city", "country", "timezone", "currency", "pos_system", "opened_on", "closed_on"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for v in VENUES:
            w.writerow([v[c] for c in cols])


def catalog_item(p):
    return {
        "sku": p[0], "name": p[1], "kassa_article_no": p[4],
        "prices": [{"valid_from": h[0], "eur": h[1] / 100, "usd": h[2] / 100} for h in p[6]],
        "unit_cost_eur": p[7] / 100, "tags": p[8], "active": True,
    }


def write_catalog():
    cats = {}
    for p in PRODUCTS:
        cats.setdefault(p[3], []).append(catalog_item(p))
    doc = {
        "catalog_version": "2026-08-28",
        "exported_by": "menu-service v3.2",
        "notes": "List prices per currency. Venue POS may apply local discounts.",
        "categories": [{"category": c, "items": items} for c, items in cats.items()],
    }
    path = RAW / "catalog" / "menu.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def make_fx():
    """ECB-style SDMX CSV, USD per 1 EUR, business days only."""
    rates = {}
    r = 1.1052
    for d in daterange(date(2026, 8, 24), date(2026, 11, 6)):
        if d.weekday() >= 5:
            continue
        r = round(r + rng.gauss(0, 0.0032), 4)
        rates[d] = r
    path = RAW / "fx" / "ecb_eurusd_daily.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = ["KEY", "FREQ", "CURRENCY", "CURRENCY_DENOM", "EXR_TYPE", "EXR_SUFFIX", "TIME_PERIOD", "OBS_VALUE",
            "OBS_STATUS", "OBS_CONF", "TITLE"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for d, val in rates.items():
            w.writerow(["EXR.D.USD.EUR.SP00.A", "D", "USD", "EUR", "SP00", "A", d.isoformat(), f"{val:.4f}", "A", "F",
                        "US dollar/Euro"])
    return rates


def write_conferences(con):
    path = RAW / "conferences" / "conferences.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    con.execute("CREATE OR REPLACE TEMP TABLE conf (conference_id VARCHAR, conference_name VARCHAR, venue_id VARCHAR, "
                "start_date DATE, end_date DATE, expected_attendance INTEGER, tags VARCHAR[], status VARCHAR)")
    con.executemany("INSERT INTO conf VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [list(c) for c in CONFERENCES])
    con.execute(f"COPY conf TO '{path}' (FORMAT parquet)")


def write_members(members):
    path = RAW / "loyalty" / "members.ndjson"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for m in members:
            f.write(json.dumps(m) + "\n")


def write_ops_note():
    (RAW / "FROM_OPS.md").write_text(
        "Hey!\n\n"
        "As promised, here is the dump. Everything from September 1 to the end of October:\n\n"
        "- POS exports for all six venues (we run two different POS systems, sorry)\n"
        "- the menu export\n"
        "- the conference calendar\n"
        "- loyalty members\n"
        "- ECB exchange rates, in case you need them\n\n"
        "Amounts are in euros. Should be pretty clean.\n\n"
        "Ping me if anything looks off.\n\n"
        "Jo (Ops)\n",
        encoding="utf-8",
    )


def main():
    for d in (RAW, BREAKS, KEY):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)

    con = duckdb.connect()
    members = make_members()
    by_venue = {}
    for m in members:
        by_venue.setdefault(m["home_venue"].upper(), []).append(m)

    write_venues()
    write_catalog()
    fx = make_fx()
    write_conferences(con)
    write_members(members)
    write_ops_note()

    ids = Ids()
    orders = make_orders(by_venue, ids)
    recs = flatten(orders)

    key_rows, footers = [], []
    write_squareduck(recs, key_rows)
    write_kassa(recs, key_rows, footers)

    # answer key
    fx_rows = sorted(fx.items())
    con.execute("CREATE TEMP TABLE fx (d DATE, usd_per_eur DOUBLE)")
    con.executemany("INSERT INTO fx VALUES (?, ?)", [[d, r] for d, r in fx_rows])
    cols = list(key_rows[0].keys())
    con.execute(
        "CREATE TEMP TABLE k (venue_id VARCHAR, pos_system VARCHAR, currency VARCHAR, delivery VARCHAR, file_rel VARCHAR, "
        "order_id VARCHAR, line_no INTEGER, sku VARCHAR, qty INTEGER, unit_price_minor INTEGER, discount_minor INTEGER, "
        "tip_minor INTEGER, net_minor INTEGER, local_ts TIMESTAMP, utc_ts TIMESTAMP, local_date DATE, utc_date DATE, "
        "is_dup BOOLEAN, is_test BOOLEAN, is_refund BOOLEAN, is_orphan_sku BOOLEAN, raw_major_units BOOLEAN, "
        "quarantine_expected BOOLEAN, schema_v2 BOOLEAN, is_resend_copy BOOLEAN)"
    )
    # executemany is row-by-row in DuckDB; stage through a temp CSV instead (seconds vs minutes)
    tmp = KEY / "_lines.csv"
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        for r in key_rows:
            w.writerow([r[c] for c in cols])
    con.execute(f"INSERT INTO k SELECT * FROM read_csv('{tmp}', header=false, columns={{"
                + ", ".join(f"'{c}': '{t}'" for c, t in con.execute("SELECT column_name, data_type FROM duckdb_columns() WHERE table_name='k'").fetchall())
                + "}, quote='\"')")
    tmp.unlink()
    con.execute("""
        CREATE TEMP TABLE k2 AS
        SELECT k.*,
               a.usd_per_eur AS fx_asof_local, e.usd_per_eur AS fx_exact_local,
               au.usd_per_eur AS fx_asof_utc, eu.usd_per_eur AS fx_exact_utc
        FROM k
        ASOF LEFT JOIN fx a ON k.local_date >= a.d
        LEFT JOIN fx e ON e.d = k.local_date
        ASOF LEFT JOIN fx au ON k.utc_date >= au.d
        LEFT JOIN fx eu ON eu.d = k.utc_date
    """)
    con.execute(f"COPY (SELECT * FROM k2 ORDER BY venue_id, utc_ts, order_id, line_no) TO '{KEY / 'lines.parquet'}' (FORMAT parquet, COMPRESSION zstd)")
    con.execute("CREATE TEMP TABLE f (venue_id VARCHAR, local_date DATE, delivery VARCHAR, file_rel VARCHAR, total_minor BIGINT)")
    con.executemany("INSERT INTO f VALUES (?, ?, ?, ?, ?)", [[x[c] for c in ("venue_id", "local_date", "delivery", "file_rel", "total_minor")] for x in footers])
    con.execute(f"COPY f TO '{KEY / 'footers.parquet'}' (FORMAT parquet)")

    manifest = {}
    for row in con.execute("SELECT DISTINCT delivery, file_rel FROM k2 UNION SELECT DISTINCT delivery, file_rel FROM f ORDER BY 1, 2").fetchall():
        manifest.setdefault(row[0], []).append(row[1])
    descriptions = {
        "base": "September 1 to October 31 drop described in FROM_OPS.md",
        "01-resend": "Nov 1 files. The AMS file is delivered twice ('2026-11-01 (1).csv').",
        "02-schema-drift": "Nov 2 files. SquareDuck renames qty to quantity and adds tip_cents mid-row; Kassa adds Trinkgeld.",
        "03-silent-units": "Nov 3 files. NYC unit_price_cents/discount_cents/tip_cents now hold dollars (4.75), header unchanged.",
        "04-new-product": "Nov 4 files. New SKU BEV-099 / Kassa article 1099 sold everywhere, absent from menu.json.",
        "05-late-file": "VIE Oct 12 Kassa file that was missing from the base drop.",
        "06-truncated": "Nov 5 files. The BER file is cut mid-row with no Summe footer. Expected: quarantine, do not publish.",
    }
    (KEY / "manifest.json").write_text(json.dumps(
        {k: {"description": descriptions[k], "files": sorted(set(v))} for k, v in sorted(manifest.items())}, indent=2) + "\n")

    n = con.execute("SELECT count(*), count(*) FILTER (WHERE delivery='base') FROM k2").fetchone()
    print(f"answer key lines: {n[0]} (base {n[1]})")
    for row in con.execute("SELECT delivery, count(DISTINCT file_rel) FROM k2 GROUP BY 1 ORDER BY 1").fetchall():
        print(f"  {row[0]:<16} {row[1]} files")


if __name__ == "__main__":
    main()
