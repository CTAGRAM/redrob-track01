#!/usr/bin/env python3
"""Redrob Track-01 — Intelligent Candidate Ranking.

Reads the candidate pool, scores every candidate against the released job
description, and writes the top-100 ranking CSV.

    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Constraints honored: CPU-only, no network, no hosted-LLM calls, standard library
only, well under 5 minutes / 16 GB for the 100K pool. Output is deterministic.
"""

import argparse
import csv
import sys
import time

from src import reasoning
from src.config import SCORE_HI, SCORE_LO, TOP_N
from src.io_load import stream_candidates
from src.scorer import score_candidate


def rank(candidates_path):
    results = []
    n = 0
    honeypots = 0
    for c in stream_candidates(candidates_path):
        n += 1
        r = score_candidate(c)
        if r["is_honeypot"]:
            honeypots += 1
            continue  # hard gate: honeypots can never enter the ranking
        results.append(r)

    # sort by relevance; deterministic tie-break by candidate_id ascending
    results.sort(key=lambda r: (-r["final"], r["candidate_id"]))
    top = results[:TOP_N]

    # calibrate to a strictly-decreasing display score in [SCORE_LO, SCORE_HI]
    # (guarantees the validator's monotonicity rule and avoids score-tie ambiguity)
    rows = []
    step = (SCORE_HI - SCORE_LO) / max(TOP_N - 1, 1)
    for i, r in enumerate(top):
        rank_pos = i + 1
        display = round(SCORE_HI - i * step, 4)
        rows.append({
            "candidate_id": r["candidate_id"],
            "rank": rank_pos,
            "score": display,
            "reasoning": reasoning.build(r, rank_pos),
        })
    return rows, n, honeypots, top


def write_csv(rows, out_path):
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["candidate_id", "rank", "score", "reasoning"])
        w.writeheader()
        for row in rows:
            w.writerow(row)


def main():
    ap = argparse.ArgumentParser(description="Rank the top-100 candidates for the Redrob JD.")
    ap.add_argument("--candidates", required=True, help="path to candidates.jsonl(.gz)")
    ap.add_argument("--out", default="submission.csv", help="output CSV path")
    args = ap.parse_args()

    t0 = time.time()
    rows, n, honeypots, top = rank(args.candidates)
    write_csv(rows, args.out)
    dt = time.time() - t0

    hp_in_top = sum(1 for r in top if r["is_honeypot"])  # must be 0
    print(f"Scanned {n} candidates in {dt:.1f}s", file=sys.stderr)
    print(f"Excluded {honeypots} honeypot/impossible profiles before ranking", file=sys.stderr)
    print(f"Wrote {len(rows)} rows to {args.out}", file=sys.stderr)
    print(f"Honeypots in top-100: {hp_in_top} (must be 0)", file=sys.stderr)
    if hp_in_top != 0:
        print("FATAL: honeypot leaked into top-100", file=sys.stderr)
        sys.exit(2)
    if len(rows) != TOP_N:
        print(f"FATAL: expected {TOP_N} rows, got {len(rows)}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
