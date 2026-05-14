#!/usr/bin/env python3
"""Rebalance Correcta (A/B/C/D) by permuting options.

This script ONLY reorders columns A/B/C/D per row and updates Correcta.
It does not change the text content.

Usage:
  python balance_correcta.py IN.xlsx OUT.xlsx

The goal is an approximately uniform distribution across A/B/C/D globally.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REQUIRED_COLS = ["Tema", "Pregunta", "A", "B", "C", "D", "Correcta"]
LETTERS = ["A", "B", "C", "D"]


@dataclass
class Move:
    src: str
    dst: str


def _safe_str(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _validate_schema(df: pd.DataFrame) -> list[str]:
    return [c for c in REQUIRED_COLS if c not in df.columns]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Rebalance Correcta by permuting A-D")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(argv)

    random.seed(args.seed)

    if not args.input.exists():
        print(f"ERROR: file not found: {args.input}", file=sys.stderr)
        return 2

    df = pd.read_excel(args.input)
    missing = _validate_schema(df)
    if missing:
        print(f"ERROR: missing required columns: {missing}", file=sys.stderr)
        return 2

    correcta = df["Correcta"].apply(_safe_str).str.upper()
    total = len(df)

    # Desired counts: as uniform as possible
    base = total // 4
    remainder = total % 4
    desired = {l: base for l in LETTERS}
    for l in LETTERS[:remainder]:
        desired[l] += 1

    current = {l: int((correcta == l).sum()) for l in LETTERS}

    deficit_count = {l: max(0, desired[l] - current[l]) for l in LETTERS}
    surplus_count = {l: max(0, current[l] - desired[l]) for l in LETTERS}

    def _pick_deficit_target() -> str | None:
        # Pick the letter with highest remaining deficit (tie-break randomly)
        available = [(l, deficit_count[l]) for l in LETTERS if deficit_count[l] > 0]
        if not available:
            return None
        max_def = max(c for _, c in available)
        candidates = [l for l, c in available if c == max_def]
        return random.choice(candidates)

    swaps = 0
    new_rows = []

    for _, row in df.iterrows():
        row_correcta = _safe_str(row["Correcta"]).upper()
        if row_correcta not in LETTERS:
            new_rows.append(row)
            continue

        target = _pick_deficit_target()
        if target is None:
            new_rows.append(row)
            continue

        # Only move from surplus letters to deficit letters
        if surplus_count.get(row_correcta, 0) <= 0:
            new_rows.append(row)
            continue

        if target == row_correcta:
            # Should be rare (would mean both surplus and deficit at same letter)
            new_rows.append(row)
            continue

        opts = {l: row[l] for l in LETTERS}
        correct_text = opts[row_correcta]

        # Create a permutation that puts correct_text in target.
        remaining_letters = [l for l in LETTERS if l != target]
        remaining_texts = [opts[l] for l in LETTERS if l != row_correcta]

        # Deterministic-ish shuffle for variety
        random.shuffle(remaining_texts)

        new_opts = {target: correct_text}
        for l, text in zip(remaining_letters, remaining_texts, strict=False):
            new_opts[l] = text

        # Write back
        new_row = row.copy()
        for l in LETTERS:
            new_row[l] = new_opts[l]
        new_row["Correcta"] = target
        swaps += 1
        surplus_count[row_correcta] -= 1
        deficit_count[target] -= 1
        new_rows.append(new_row)

    out = pd.DataFrame(new_rows)

    # Ensure column order stable
    out = out[REQUIRED_COLS]
    out.to_excel(args.output, index=False)

    # Report
    out_correcta = out["Correcta"].apply(_safe_str).str.upper()
    out_dist = {l: int((out_correcta == l).sum()) for l in LETTERS}

    print("== Balance Correcta ==")
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print(f"Rows:   {total}")
    print(f"Swaps:  {swaps}")
    print("Objetivo (aprox):")
    for l in LETTERS:
        print(f"- {l}: {desired[l]}")
    print("Distribución final:")
    for l in LETTERS:
        pct = (out_dist[l] / total * 100) if total else 0.0
        print(f"- {l}: {out_dist[l]} ({pct:.1f}%)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
