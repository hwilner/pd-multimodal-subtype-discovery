#!/usr/bin/env python
"""Stage AMP-PD Terra exports into harmonization-ready feature matrices.

Usage
-----
Real AMP-PD Tier 2 data (requires approved DUA + Terra workspace — see
docs/DATA_ACCESS.md). Export one TSV per cohort/view from Terra, e.g.
``PPMI_clinical.tsv``, each with a ``subject_id`` column:

    python scripts/prepare_amppd.py --terra-export /path/to/export --out data/prepared

Semi-synthetic stand-in (published summary statistics; NOT real data),
for validating the pipeline while access is pending:

    python scripts/prepare_amppd.py --semi-synthetic --out data/prepared

Outputs per-view CSVs (``<view>.csv``), ``cohort.csv`` and
``qc_report.csv`` in the output directory.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pd_subtypes import amppd


def main() -> None:
    """Main."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--terra-export", type=Path,
                     help="Directory of Terra-exported AMP-PD TSVs.")
    src.add_argument("--semi-synthetic", action="store_true",
                     help="Generate the documented semi-synthetic stand-in "
                          "from published summary statistics (no real data).")
    p.add_argument("--out", type=Path, default=Path("data/prepared"))
    p.add_argument("--n-per-cohort", type=int, default=80,
                   help="Subjects per cohort (semi-synthetic mode only).")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    if args.semi_synthetic:
        ds = amppd.simulate_semi_synthetic(
            n_per_cohort=args.n_per_cohort, random_state=args.seed
        )
        views = dict(ds.views)
        views["cohort"] = ds.cohort
        print("Generated SEMI-SYNTHETIC dataset from published summary "
              "statistics (not real participant data).")
    else:
        views = amppd.load_terra_export(args.terra_export)

    qc = amppd.integrity_check(views)
    matrices, cohort = amppd.build_feature_matrices(views)

    args.out.mkdir(parents=True, exist_ok=True)
    for name, X in matrices.items():
        X.to_csv(args.out / f"{name}.csv")
    cohort.to_csv(args.out / "cohort.csv")
    qc.to_csv(args.out / "qc_report.csv", index=False)
    print(qc.to_string(index=False))
    print(f"Staged {len(cohort)} subjects x {sum(X.shape[1] for X in matrices.values())} "
          f"features across {len(matrices)} views -> {args.out}")


if __name__ == "__main__":
    main()
