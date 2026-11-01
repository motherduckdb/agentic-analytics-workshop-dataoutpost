#!/usr/bin/env python3
"""Simulate new file deliveries landing in data/raw.

  uv run tools/deliver.py --list          show deliveries and which ones already landed
  uv run tools/deliver.py next            land the next delivery in order
  uv run tools/deliver.py 03-silent-units land a specific delivery
  uv run tools/deliver.py --reset         remove every delivery, back to the base drop

The human runs this, not the agent. The agent finds out the way it would in real life:
new files show up and the numbers move (or not).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
BREAKS = ROOT / "facilitator" / "breaks"
MANIFEST = ROOT / "facilitator" / "answer_key" / "manifest.json"

# What the participant sees. Deliberately vague: the details are for the agent to find.
TEASERS = {
    "01-resend": "November 1 exports. Ops says the Amsterdam upload 'hiccuped' and they sent it again.",
    "02-schema-drift": "November 2 exports. SquareDuck pushed a POS update overnight.",
    "03-silent-units": "November 3 exports. Nothing special, according to Ops.",
    "04-new-product": "November 4 exports. Marketing launched the autumn menu.",
    "05-late-file": "A file Ops found in their outbox. 'Oops, forgot this one.'",
    "06-truncated": "November 5 exports. The Berlin upload timed out but 'the file is there'.",
}


def deliveries() -> dict:
    m = json.loads(MANIFEST.read_text())
    return {k: v for k, v in m.items() if k != "base"}


def landed(files: list[str]) -> bool:
    return all((RAW / f).exists() for f in files)


def land(name: str, files: list[str]) -> None:
    for f in files:
        src = BREAKS / name / f
        dst = RAW / f
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    print(f"Delivered {name}: {len(files)} new file(s) in data/raw")
    print(f"  {TEASERS.get(name, '')}")
    for f in files:
        print(f"  + data/raw/{f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", nargs="?", help="delivery name, or 'next'")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()
    ds = deliveries()

    if args.reset:
        n = 0
        for d in ds.values():
            for f in d["files"]:
                p = RAW / f
                if p.exists():
                    p.unlink()
                    n += 1
        print(f"Removed {n} delivered file(s). data/raw is back to the base drop.")
        return

    if args.list or not args.name:
        for name, d in ds.items():
            mark = "x" if landed(d["files"]) else " "
            print(f"[{mark}] {name:<16} {TEASERS.get(name, '')}")
        return

    if args.name == "next":
        pending = [n for n, d in ds.items() if not landed(d["files"])]
        if not pending:
            print("Every delivery has landed.")
            return
        name = pending[0]
    else:
        matches = [n for n in ds if n == args.name or n.split("-", 1)[0] == args.name or n.endswith(args.name)]
        if len(matches) != 1:
            sys.exit(f"Unknown delivery '{args.name}'. Try --list.")
        name = matches[0]
    land(name, ds[name]["files"])


if __name__ == "__main__":
    main()
