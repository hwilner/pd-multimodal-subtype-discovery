#!/usr/bin/env python
"""One-command subtype discovery on staged AMP-PD feature matrices.

    python scripts/prepare_amppd.py --semi-synthetic --out data/prepared
    python scripts/run_subtyping.py --prepared data/prepared

Runs: cross-cohort harmonization -> SuStaIn subtype/stage inference ->
multi-view consensus clustering comparator -> train-in-PPMI /
assign-in-other-cohorts reproducibility. Writes derived results to
``reports/`` (subtype assignments, summary metrics).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from pd_subtypes import harmonize, multiview, reproducibility
from pd_subtypes.sustain import SuStaInModel


def main() -> None:
    """Main."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--prepared", type=Path, default=Path("data/prepared"),
                   help="Directory written by scripts/prepare_amppd.py.")
    p.add_argument("--n-subtypes", type=int, default=2)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--reports", type=Path, default=Path("reports"))
    args = p.parse_args()

    cohort = pd.read_csv(args.prepared / "cohort.csv", index_col=0).iloc[:, 0]
    views = {}
    for view in ("clinical", "imaging", "datscan", "csf"):
        f = args.prepared / f"{view}.csv"
        if f.exists():
            views[view] = pd.read_csv(f, index_col=0)
    if not views:
        raise SystemExit(
            f"No staged views under {args.prepared}. Run "
            "scripts/prepare_amppd.py first (see docs/DATA_ACCESS.md for "
            "real AMP-PD access; --semi-synthetic for a stand-in)."
        )

    # 1. Harmonize each view across cohorts.
    harmonized = {name: harmonize.harmonize(X, cohort) for name, X in views.items()}
    X = pd.concat(harmonized.values(), axis=1)
    print(f"Harmonized {X.shape[1]} features for {X.shape[0]} subjects.")

    # 2. SuStaIn subtype/stage inference.
    model = SuStaInModel(n_subtypes=args.n_subtypes, n_init=6,
                         random_state=args.seed).fit(X)
    assignments = pd.DataFrame(
        {"subtype": model.subtype_labels_, "stage": model.stages_},
        index=X.index,
    )
    print("Subtype counts:", assignments["subtype"].value_counts().to_dict())

    # 3. Multi-view consensus clustering comparator.
    consensus = multiview.consensus_clustering(harmonized, n_clusters=args.n_subtypes)
    agree = multiview.multiview_agreement(model.subtype_labels_, consensus)

    # 4. Cross-cohort reproducibility: train in the first cohort, assign
    #    the others, compare signature replication.
    cohorts = list(cohort.unique())
    train_c = cohorts[0]
    train_mask = cohort == train_c
    assigner = reproducibility.SubtypeAssignmentModel().fit(
        X[train_mask], model.subtype_labels_[train_mask.to_numpy()]
    )
    rep = {}
    for c in cohorts[1:]:
        mask = cohort == c
        pred = assigner.predict(X[mask])
        ari = reproducibility.assignment_agreement(
            model.subtype_labels_[mask.to_numpy()], pred
        )
        corr = reproducibility.subtype_signature_correlation(
            assigner, X[mask], model.subtype_labels_[mask.to_numpy()]
        ).mean()
        rep[c] = {"assignment_ari": float(ari), "signature_correlation": float(corr)}

    args.reports.mkdir(parents=True, exist_ok=True)
    assignments.to_csv(args.reports / "subtype_assignments.csv")
    summary = {
        "n_subjects": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "n_subtypes": args.n_subtypes,
        "sustain_log_likelihood": float(model.log_likelihood_),
        "sustain_vs_consensus_ari": float(agree),
        "train_cohort": train_c,
        "cross_cohort": rep,
    }
    with open(args.reports / "subtyping_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    print(f"Wrote {args.reports / 'subtype_assignments.csv'} and subtyping_summary.json")


if __name__ == "__main__":
    main()
