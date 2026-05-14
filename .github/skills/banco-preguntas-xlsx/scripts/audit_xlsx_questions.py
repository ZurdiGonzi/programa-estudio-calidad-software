#!/usr/bin/env python3
"""Audit a multiple-choice question bank stored in an .xlsx.

Expected columns:
- Tema, Pregunta, A, B, C, D, Correcta

This script prints a concise report that helps detect:
- Missing/invalid columns or Correcta values
- Bias in Correcta (A/B/C/D distribution)
- Length outliers (questions/options too long)
- Within-row duplicated options
- Exact duplicated questions (after normalization)

Usage:
  python audit_xlsx_questions.py preguntas.xlsx
  python audit_xlsx_questions.py preguntas.xlsx --max-rows 15

Exit codes:
  0 = ok
  2 = schema/validation problem (missing cols, invalid Correcta, etc.)
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

REQUIRED_COLS = ["Tema", "Pregunta", "A", "B", "C", "D", "Correcta"]
VALID_CORRECTA = {"A", "B", "C", "D"}


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


def _safe_str(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


@dataclass(frozen=True)
class RowFlag:
    idx: int
    tema: str
    pregunta: str
    reasons: tuple[str, ...]


def _len_stats(options: Iterable[str]) -> tuple[int, int, float]:
    lengths = [len(o) for o in options if o is not None]
    if not lengths:
        return 0, 0, 0.0
    min_len = min(lengths)
    max_len = max(lengths)
    ratio = (max_len / min_len) if min_len > 0 else float("inf")
    return min_len, max_len, ratio


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit an .xlsx question bank")
    parser.add_argument("xlsx", type=Path, help="Path to .xlsx")
    parser.add_argument(
        "--max-rows",
        type=int,
        default=20,
        help="Max flagged rows to display in detail",
    )
    parser.add_argument(
        "--ratio-threshold",
        type=float,
        default=1.8,
        help="Flag if max_len/min_len >= this value",
    )
    parser.add_argument(
        "--correcta-longest-mediana",
        type=float,
        default=0.35,
        help="Flag if correct option is longest and >= (1+X) * median length",
    )
    parser.add_argument(
        "--question-max",
        type=int,
        default=240,
        help="Hard max length for Pregunta (flag if exceeded)",
    )
    parser.add_argument(
        "--option-max",
        type=int,
        default=160,
        help="Hard max length for A/B/C/D (flag if exceeded)",
    )
    parser.add_argument(
        "--export-flags",
        type=Path,
        default=None,
        help="Optional path to export flagged rows as CSV",
    )

    args = parser.parse_args(argv)

    if not args.xlsx.exists():
        print(f"ERROR: file not found: {args.xlsx}", file=sys.stderr)
        return 2

    try:
        df = pd.read_excel(args.xlsx)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot read xlsx: {exc}", file=sys.stderr)
        return 2

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        print("ERROR: missing required columns:")
        for c in missing:
            print(f"- {c}")
        return 2

    total = len(df)
    print("== Audit: Question Bank ==")
    print(f"File: {args.xlsx}")
    print(f"Rows: {total}")

    # Basic topic stats
    temas = df["Tema"].astype(str).fillna("")
    tema_counts = temas.value_counts(dropna=False)
    print(f"Temas únicos: {tema_counts.shape[0]}")
    if tema_counts.shape[0] > 0:
        top = tema_counts.head(10)
        print("Top temas:")
        for tema, count in top.items():
            tema_label = tema if tema else "(vacío)"
            print(f"- {tema_label}: {count}")

    # Correcta distribution
    correcta_series = df["Correcta"].apply(_safe_str).str.upper()
    invalid_correcta_mask = ~correcta_series.isin(list(VALID_CORRECTA))
    invalid_correcta = int(invalid_correcta_mask.sum())

    dist = correcta_series.value_counts().reindex(list("ABCD"), fill_value=0)
    print("Distribución Correcta:")
    for k in "ABCD":
        count = int(dist.get(k, 0))
        pct = (count / total * 100) if total else 0.0
        print(f"- {k}: {count} ({pct:.1f}%)")
    if invalid_correcta:
        print(f"Correcta inválida/vacía: {invalid_correcta}")

    # Flags
    flags: list[RowFlag] = []
    export_rows: list[dict[str, object]] = []
    within_row_dupe = 0
    empty_cells = 0

    # Exact duplicate questions (normalized)
    norm_q = df["Pregunta"].apply(_normalize_text)
    dupe_q_mask = norm_q.duplicated(keep=False) & (norm_q != "")
    exact_dupes = int(dupe_q_mask.sum())

    for idx, row in df.iterrows():
        pregunta = _safe_str(row["Pregunta"])
        tema = _safe_str(row["Tema"])

        a = _safe_str(row["A"])
        b = _safe_str(row["B"])
        c = _safe_str(row["C"])
        d = _safe_str(row["D"])
        correcta = _safe_str(row["Correcta"]).upper()

        reasons: list[str] = []

        # empties
        if not tema or not pregunta or not a or not b or not c or not d or not correcta:
            empty_cells += 1
            reasons.append("celdas vacías")

        if len(pregunta) > args.question_max:
            reasons.append(f"Pregunta>{args.question_max}")

        opts = [a, b, c, d]
        if any(len(o) > args.option_max for o in opts):
            reasons.append(f"opción>{args.option_max}")

        # duplicates within row
        norm_opts = [_normalize_text(o) for o in opts]
        norm_opts_nonempty = [o for o in norm_opts if o]
        if len(set(norm_opts_nonempty)) != len(norm_opts_nonempty):
            within_row_dupe += 1
            reasons.append("opciones duplicadas")

        # length ratio
        min_len, max_len, ratio = _len_stats(opts)
        if min_len > 0 and ratio >= args.ratio_threshold:
            reasons.append(f"ratio_len>={args.ratio_threshold}")

        # correct option is longest by margin
        if correcta in VALID_CORRECTA:
            correct_text = {"A": a, "B": b, "C": c, "D": d}[correcta]
            lengths = [len(o) for o in opts]
            if lengths:
                lengths_sorted = sorted(lengths)
                median = lengths_sorted[len(lengths_sorted) // 2]
                if len(correct_text) == max(lengths) and median > 0:
                    if (len(correct_text) - median) / median >= args.correcta_longest_mediana:
                        reasons.append("correcta_delata_por_longitud")

        if correcta and correcta not in VALID_CORRECTA:
            reasons.append("Correcta inválida")

        if reasons:
            flags.append(
                RowFlag(
                    idx=int(idx),
                    tema=tema,
                    pregunta=(pregunta[:120] + "…") if len(pregunta) > 120 else pregunta,
                    reasons=tuple(reasons),
                )
            )
            export_rows.append(
                {
                    "idx": int(idx),
                    "Tema": tema,
                    "Pregunta": pregunta,
                    "A": a,
                    "B": b,
                    "C": c,
                    "D": d,
                    "Correcta": correcta,
                    "reasons": " | ".join(reasons),
                }
            )

    print("Resumen flags:")
    print(f"- Filas con algún flag: {len(flags)}")
    print(f"- Filas con celdas vacías: {empty_cells}")
    print(f"- Filas con opciones duplicadas: {within_row_dupe}")
    print(f"- Duplicados exactos de Pregunta (normalizada): {exact_dupes}")

    if flags:
        print("\nEjemplos de filas a revisar:")
        for rf in flags[: args.max_rows]:
            tema_label = rf.tema if rf.tema else "(vacío)"
            reasons = ", ".join(rf.reasons)
            print(f"- idx={rf.idx} | {tema_label} | {reasons} | {rf.pregunta}")

    if args.export_flags is not None:
        try:
            out_path = args.export_flags
            out_path.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(export_rows).to_csv(out_path, index=False)
            print(f"\nCSV de flags exportado a: {out_path}")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: no se pudo exportar CSV de flags: {exc}", file=sys.stderr)
            return 2

    # Exit code suggests if there are schema-critical issues
    if missing or invalid_correcta:
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
