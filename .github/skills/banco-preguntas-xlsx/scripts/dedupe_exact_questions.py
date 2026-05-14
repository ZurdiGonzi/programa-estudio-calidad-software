#!/usr/bin/env python3
"""Remove exact duplicate questions (after normalization).

Keeps the first occurrence of each normalized Pregunta (non-empty), preserves
row order otherwise.

Usage:
  python dedupe_exact_questions.py IN.xlsx OUT.xlsx
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

REQUIRED_COLS = ["Tema", "Pregunta", "A", "B", "C", "D", "Correcta"]


def _normalize_text(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value)
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Dedupe exact Pregunta duplicates")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"ERROR: file not found: {args.input}", file=sys.stderr)
        return 2

    df = pd.read_excel(args.input)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        print(f"ERROR: missing required columns: {missing}", file=sys.stderr)
        return 2

    norm_q = df["Pregunta"].apply(_normalize_text)
    # Only dedupe non-empty; keep empty as unique (so issues remain visible)
    mask_nonempty = norm_q != ""
    dedupe_mask = ~(mask_nonempty & norm_q.duplicated(keep="first"))

    before = len(df)
    out = df.loc[dedupe_mask].copy()
    after = len(out)

    out = out[REQUIRED_COLS]
    out.to_excel(args.output, index=False)

    removed = before - after
    print("== Dedupe exact questions ==")
    print(f"Input:   {args.input}")
    print(f"Output:  {args.output}")
    print(f"Before:  {before}")
    print(f"After:   {after}")
    print(f"Removed: {removed}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
