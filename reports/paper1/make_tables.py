#!/usr/bin/env python
"""Render Paper 1 Tables 1-3 (markdown) from committed report artifacts.

Reads only committed artifacts in ``reports/`` (semi-synthetic validation
run -- a documented stand-in built from published summary statistics, NOT
real participant data; see ``docs/DATA_ACCESS.md``) and writes
``reports/paper1/tables_1_to_3_semisynthetic.md``. Rendering is
deterministic: same artifacts -> byte-identical output.

Integrity rule: the script refuses to write anything if the artifacts
disagree with each other (cohort sets, subject/feature totals, per-cohort
counts). No number is typed by hand; every cell is derived from the
committed artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
MINUS = "−"  # U+2212, matching docs/RESULTS.md typography


def load_artifacts(reports: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Load the three committed semi-synthetic artifacts.

    Args:
        reports: Path to the ``reports/`` directory.

    Returns:
        Tuple of (QC report frame, subtype-counts frame, summary dict).

    Raises:
        SystemExit: If any artifact is missing.
    """
    qc_path = reports / "qc_report_semisynthetic.csv"
    counts_path = reports / "subtype_counts_by_cohort.csv"
    summary_path = reports / "subtyping_summary.json"
    for path in (qc_path, counts_path, summary_path):
        if not path.exists():
            raise SystemExit(f"Missing committed artifact: {path}")
    qc = pd.read_csv(qc_path)
    counts = pd.read_csv(counts_path)
    with open(summary_path) as fh:
        summary = json.load(fh)
    return qc, counts, summary


def check_consistency(qc: pd.DataFrame, counts: pd.DataFrame, summary: dict) -> list[str]:
    """Verify the artifacts agree with each other before rendering.

    Args:
        qc: QC report frame (one row per cohort x view block).
        counts: Per-cohort subtype-counts frame.
        summary: Subtyping summary dict.

    Returns:
        A list of inconsistency descriptions (empty if consistent).
    """
    problems = []
    cohorts_qc = sorted(qc["cohort"].unique())
    train = summary["train_cohort"]
    cohorts_summary = sorted([train, *summary["cross_cohort"].keys()])
    if cohorts_qc != cohorts_summary:
        problems.append(f"cohort mismatch: qc={cohorts_qc} summary={cohorts_summary}")
    if sorted(counts["cohort"]) != cohorts_summary:
        problems.append("subtype-counts cohorts do not match the summary")
    if int(qc.groupby("cohort")["n_subjects"].first().sum()) != summary["n_subjects"]:
        problems.append("QC subject total != summary n_subjects")
    feats_per_cohort = qc.groupby("cohort")["n_features"].sum()
    if not feats_per_cohort.eq(summary["n_features"]).all():
        problems.append("QC per-cohort feature total != summary n_features")
    subtype_cols = [c for c in counts.columns if c.startswith("subtype_")]
    if len(subtype_cols) != summary["n_subtypes"]:
        problems.append("subtype-count columns != summary n_subtypes")
    per_cohort_n = counts.set_index("cohort")[subtype_cols].sum(axis=1)
    qc_n = qc.groupby("cohort")["n_subjects"].first()
    for cohort in cohorts_summary:
        if int(per_cohort_n.get(cohort, -1)) != int(qc_n.get(cohort, -2)):
            problems.append(f"{cohort}: subtype counts do not sum to QC n_subjects")
    return problems


def _fmt(value: float, decimals: int) -> str:
    """Format a float with a true minus sign (U+2212).

    Args:
        value: Number to format.
        decimals: Decimal places.

    Returns:
        Formatted string, e.g. ``−4097.82``.
    """
    return f"{value:.{decimals}f}".replace("-", MINUS)


def render_tables(qc: pd.DataFrame, counts: pd.DataFrame, summary: dict) -> str:
    """Render the markdown for Tables 1-3.

    Args:
        qc: QC report frame.
        counts: Per-cohort subtype-counts frame.
        summary: Subtyping summary dict.

    Returns:
        Markdown text for the three captioned tables.
    """
    train = summary["train_cohort"]
    cohort_order = [train, *summary["cross_cohort"].keys()]

    lines = [
        "# Paper 1 Tables 1-3 (semi-synthetic validation run)",
        "",
        "Rendered by `reports/paper1/make_tables.py` from committed artifacts",
        "(`reports/qc_report_semisynthetic.csv`,",
        "`reports/subtype_counts_by_cohort.csv`,",
        "`reports/subtyping_summary.json`). Semi-synthetic stand-in from",
        "published summary statistics - **not real participant data** (see",
        "`docs/DATA_ACCESS.md`). Do not edit by hand; regenerate.",
        "",
        "**Table 1. Semi-synthetic cohort × view inventory and QC.**",
        "",
        "| Cohort | View | Subjects | Features | Frac. missing | Constant features |",
        "|---|---|---|---|---|---|",
    ]
    for _, row in qc.iterrows():
        lines.append(
            f"| {row['cohort']} | {row['view']} | {int(row['n_subjects'])} "
            f"| {int(row['n_features'])} | {row['frac_missing']} "
            f"| {int(row['n_constant_features'])} |"
        )
    lines.append(
        f"| **Total** | **{qc['view'].nunique()} views** "
        f"| **{int(qc.groupby('cohort')['n_subjects'].first().sum())}** "
        f"| **{int(qc.groupby('cohort')['n_features'].sum().iloc[0])}** "
        f"| **{qc['frac_missing'].max()}** "
        f"| **{int(qc['n_constant_features'].sum())}** |"
    )

    subtype_cols = [c for c in counts.columns if c.startswith("subtype_")]
    counts_ix = counts.set_index("cohort")
    lines += [
        "",
        "**Table 2. Recovered subtype counts by cohort (semi-synthetic).**",
        "",
        "| Cohort | "
        + " | ".join(f"Subtype {c.removeprefix('subtype_')}" for c in subtype_cols)
        + " | Median stage |",
        "|---|---|---|---|",
    ]
    for cohort in cohort_order:
        row = counts_ix.loc[cohort]
        cells = " | ".join(str(int(row[c])) for c in subtype_cols)
        lines.append(f"| {cohort} | {cells} | {row['median_stage']} |")

    lines += [
        "",
        "**Table 3. Subtyping run summary and cross-cohort transfer (semi-synthetic).**",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Subjects / features | {summary['n_subjects']} / {summary['n_features']} |",
        f"| Subtypes recovered (k) | {summary['n_subtypes']} |",
        f"| SuStaIn log-likelihood | {_fmt(summary['sustain_log_likelihood'], 2)} |",
        f"| SuStaIn vs. multi-view consensus ARI "
        f"| {_fmt(summary['sustain_vs_consensus_ari'], 3)} |",
    ]
    for cohort, metrics in summary["cross_cohort"].items():
        lines.append(
            f"| {train} → {cohort} assignment ARI "
            f"| {_fmt(metrics['assignment_ari'], 3)} |"
        )
        lines.append(
            f"| {train} → {cohort} subtype-signature correlation "
            f"| {_fmt(metrics['signature_correlation'], 3)} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Entry point: load artifacts, check consistency, write tables."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reports", type=Path, default=REPO_ROOT / "reports",
                        help="Directory holding the committed artifacts.")
    parser.add_argument("--out", type=Path,
                        default=REPO_ROOT / "reports" / "paper1"
                        / "tables_1_to_3_semisynthetic.md",
                        help="Output markdown path.")
    args = parser.parse_args()

    qc, counts, summary = load_artifacts(args.reports)
    problems = check_consistency(qc, counts, summary)
    if problems:
        for problem in problems:
            print(f"REFUSING to render: {problem}", file=sys.stderr)
        raise SystemExit(1)

    text = render_tables(qc, counts, summary)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text)
    print(f"Wrote {args.out} ({len(text)} bytes)")


if __name__ == "__main__":
    main()
